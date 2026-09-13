"""One bounded pass of the review: the files whose verdict is missing or no longer current, reviewed by the agent one
batch at a time in a worktree on branch scalability-crawler. An amendment is kept only when its scope, its syntax and the
ratchet of the invariants hold; the amendments, the review record and the snapshot are committed on that branch, and the
checkout is never touched. It gates nothing.

    python3 -B -m module_skills.sub_module_scalability_crawler.crawl            (make skills-crawl)
    python3 -B -m module_skills.sub_module_scalability_crawler.crawl --queue    the queue, and nothing run
    python3 -B -m module_skills.sub_module_scalability_crawler.crawl --brief    the brief of the first batch
"""

from __future__ import annotations

import json
import os
import posixpath
import re
import shutil
import string
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path

from . import config, status

QUEUE_CLASSES = ("unreviewed", "changed", "stale")
FAILURE_RULE = "module_skills/skill_scalability_crawler.md § The pass"
AMENDMENT_RULE = (
    "Amend what the grammar derives without a decision — a verb outside the closed list, a quantity without its unit, "
    "a debt marker, a commented-out line, a missing row of {orientation} § Design rationale, the glossary row a rename in "
    "scope requires, a spelling — editing only the files of this batch, {orientation} and `module_skills/glossary.md`. "
    "Create no file; touch no `AGENTS.md`, skill, methodology, `Makefile`, `docker-compose.yml`, `Dockerfile`, "
    "`requirements.txt` or store; rename no serialised name — an artifact key, a column, a feature, a store path, a make "
    "target, a compose service: write that rename as a finding and give the file the verdict `deferred`. A file you "
    "edited is `amended`.")
REVIEW_ONLY_RULE = (
    "These files are review-only: edit nothing. Write what the grammar would change as findings, and give a file whose "
    "finding the owner must decide the verdict `deferred`.")


def to_checkout_relative(path: Path) -> str:
    return str(path.relative_to(config.REPO_ROOT))


def build_queue() -> list[dict]:
    """The files CRAWL_PATHSPECS names that want a review — unreviewed, changed since their verdict, stale under a newer
    canon — in order: amendable
    files first, by class, then by module in the chain's order, the orientation and config.py first inside a module;
    the review-only files — the crawler's own, the canon, the root's — last."""
    rows = {row["path"]: row for row in status.load_review_record()["files"]}
    blobs, canon = status.blob_ids(), status.canon_id()
    canon_paths = set(status.tracked_paths(*config.CANON_PATHSPECS))
    modules = status.module_order()
    queue = []
    for path in status.crawl_paths():
        row = rows.get(path)
        queue_class = ("unreviewed" if row is None else "changed" if row["blob_id"] != blobs.get(path)
                       else "stale" if row["canon_id"] != canon else None)
        if queue_class:
            module = path.split("/")[0] if "/" in path else "the root"
            review_only = path.startswith(config.CRAWLER_DIR + "/") or path in canon_paths or "/" not in path
            queue.append({"path": path, "class": queue_class, "module": module, "review_only": review_only,
                          "blob_id": row["blob_id"] if row else None})
    return sorted(queue, key=lambda item: (
        item["review_only"], QUEUE_CLASSES.index(item["class"]),
        modules.index(item["module"]) if item["module"] in modules else len(modules),
        item["path"] != (status.design_rationale_source(item["path"]) or ("", ""))[1],
        posixpath.basename(item["path"]) != "config.py", item["path"]))


def queue_batches(queue: list[dict]) -> list[list[dict]]:
    """The queue cut into batches of one module and one mode, at most CRAWL_BATCH_FILE_COUNT files each, and the first
    CRAWL_PASS_BATCH_COUNT of them — the bound of one pass."""
    batches = []
    for item in queue:
        batch = batches[-1] if batches else None
        if (batch and len(batch) < config.CRAWL_BATCH_FILE_COUNT and batch[0]["module"] == item["module"]
                and batch[0]["review_only"] == item["review_only"]):
            batch.append(item)
        else:
            batches.append([item])
    return batches[:config.CRAWL_PASS_BATCH_COUNT]


def orientation_path(batch: list[dict]) -> str:
    source = status.design_rationale_source(batch[0]["path"])
    return source[1] if source else config.CONTRACT_PATH


def build_brief(batch: list[dict], prior_failure: str | None) -> str:
    orientation = f"`{orientation_path(batch)}`"
    files = "\n".join(
        f"- `{item['path']}` — never reviewed" if item["class"] == "unreviewed"
        else f"- `{item['path']}` — changed since its review: `git diff {item['blob_id']} HEAD:{item['path']}`"
        if item["class"] == "changed" else f"- `{item['path']}` — unchanged since its review, under an earlier canon"
        for item in batch)
    template = string.Template(status.load_file_text(config.BRIEF_TEMPLATE_PATH))
    return template.substitute(
        module=f"`{batch[0]['module']}`" if "/" in batch[0]["path"] else batch[0]["module"],
        orientation=orientation, files=files,
        review_mode="review-only" if batch[0]["review_only"] else "amendable",
        prior_failure=f"\nThe previous attempt at this batch failed: {prior_failure}. The files are back as committed.\n"
        if prior_failure else "",
        amendment_rule=REVIEW_ONLY_RULE if batch[0]["review_only"] else AMENDMENT_RULE.format(orientation=orientation))


def fetch_agent_answer(brief: str, worktree: Path) -> tuple[str | None, str | None]:
    """The agent's result text, or the failure of the attempt. A launch that returns no result is a configuration
    error and ends the pass."""
    try:
        completed = subprocess.run(config.AGENT_COMMAND, input=brief, cwd=worktree, capture_output=True, text=True,
                                   timeout=config.AGENT_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        return None, f"the agent ran past {config.AGENT_TIMEOUT_SECONDS} seconds"
    try:
        envelope = json.loads(completed.stdout)
    except json.JSONDecodeError:
        envelope = {}
    envelope = envelope if isinstance(envelope, dict) else {}
    if completed.returncode != 0 and "result" not in envelope:
        raise SystemExit(f"the agent did not run (exit {completed.returncode}): {completed.stderr.strip()}")
    if envelope.get("is_error"):
        return None, f"the agent reported an error: {envelope.get('result')}"
    return envelope.get("result", ""), None


def is_answer_row(row) -> bool:
    return (isinstance(row, dict) and row.get("verdict") in config.VERDICTS
            and row.get("self_explaining_level") in config.SELF_EXPLAINING_LEVELS and isinstance(row.get("evidence"), str)
            and isinstance(row.get("findings"), list)
            and all(isinstance(finding, dict) and all(isinstance(finding.get(key), str) for key in ("rule", "finding", "example"))
                    for finding in row["findings"]))


def is_proposal(proposal) -> bool:
    return (isinstance(proposal, dict) and all(isinstance(proposal.get(key), str) for key in ("pattern", "forbids", "scope"))
            and isinstance(proposal.get("occurrences"), list) and proposal["occurrences"]
            and all(isinstance(occurrence, str) for occurrence in proposal["occurrences"]))


def parse_answer(result: str, batch: list[dict]) -> tuple[dict | None, str | None]:
    """The answer the brief asks for — a row per file of the batch, and the proposals — or why it is not one."""
    text = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", result or "")
    try:
        answer = json.loads(text)
    except json.JSONDecodeError as error:
        return None, f"the answer is not JSON ({error.msg})"
    files = answer.get("files") if isinstance(answer, dict) else None
    missing = [item["path"] for item in batch if not isinstance(files, dict) or item["path"] not in files]
    if missing:
        return None, "the answer holds no verdict for " + ", ".join(missing)
    malformed = [item["path"] for item in batch if not is_answer_row(files[item["path"]])]
    if malformed or not isinstance(answer.get("proposals", []), list) or not all(map(is_proposal, answer.get("proposals", []))):
        return None, "the answer is not in the form the brief asks" + (" for " + ", ".join(malformed) if malformed else "")
    return answer, None


def changed_paths(worktree: Path) -> set[str]:
    entries = status.git("status", "--porcelain", "-z", "--untracked-files=all", root=worktree).split("\0")
    return {entry[3:] for entry in entries if entry}


def scope_failure(batch: list[dict], changed: set[str]) -> str | None:
    """An edit to a file the brief does not name: in a review-only batch, any edit."""
    allowed = set() if batch[0]["review_only"] else {item["path"] for item in batch} | {orientation_path(batch), config.GLOSSARY_PATH}
    outside = sorted(changed - allowed)
    return f"an edit outside the batch: {', '.join(outside)}" if outside else None


def syntax_failure(worktree: Path, changed: set[str]) -> str | None:
    for path in sorted(changed):
        if path.endswith(".py"):
            try:
                compile((worktree / path).read_text(encoding="utf-8"), path, "exec")
            except SyntaxError as error:
                return f"{path} no longer compiles: {error.msg}, line {error.lineno}"
    return None


def load_worktree_invariants(worktree: Path) -> dict[str, int]:
    """The invariants of the worktree, measured by the checkout's own code — PYTHONPATH and -P, so the worktree's copy
    of the crawler is never the one that counts."""
    snapshot = worktree / to_checkout_relative(config.SKILLS_STATUS_JSON_PATH)
    environment = {**os.environ, "PYTHONPATH": str(config.REPO_ROOT), "STORE_STATUS_DIR": str(snapshot.parent)}
    subprocess.run((sys.executable, "-B", "-P", "-m", f"{__package__}.status"), cwd=worktree, env=environment,
                   capture_output=True, check=True)
    return {row["metric"]: row["value"] for row in json.loads(snapshot.read_text(encoding="utf-8"))["metrics"]
            if row["kind"] == "invariant"}


def index_blob_ids(worktree: Path) -> dict[str, str]:
    entries = status.git("ls-files", "-s", "-z", root=worktree).split("\0")
    return {entry.split("\t", 1)[1]: entry.split()[1] for entry in entries if entry}


def build_review_rows(batch: list[dict], answer: dict | None, edited: set[str], failure: str | None, blobs: dict[str, str],
                canon: str) -> list[dict]:
    """A row per file of the batch. A file the agent edited in a failed batch, or any file of a batch no attempt
    answered, is deferred with the failure as its finding; every other file keeps the agent's verdict."""
    rows = []
    for item in batch:
        answer_row = answer["files"][item["path"]] if answer else None
        if failure and (item["path"] in edited or answer_row is None):
            verdict = {"verdict": "deferred", "self_explaining_level": None, "evidence": None,
                       "findings": [{"rule": FAILURE_RULE, "finding": failure, "example": item["path"]}]}
        else:
            verdict = {"verdict": "amended" if item["path"] in edited
                       else "conformant" if answer_row["verdict"] == "amended" else answer_row["verdict"],
                       "self_explaining_level": answer_row["self_explaining_level"], "evidence": answer_row["evidence"],
                       "findings": answer_row["findings"]}
        rows.append({"path": item["path"], "blob_id": blobs[item["path"]], "canon_id": canon, **verdict})
    return rows


def write_review_record(path: Path, record: dict, scope: set[str], canon: str) -> None:
    """The one writer of the review record: rows sorted by path, proposals by pattern; a row whose file left the scope
    and a proposal of another canon dropped; the file rewritten only when its content changes."""
    files = sorted((row for row in record["files"] if row["path"] in scope), key=lambda row: row["path"])
    proposals = sorted((proposal for proposal in record["proposals"] if proposal["canon_id"] == canon),
                       key=lambda proposal: proposal["pattern"])
    text = json.dumps({"files": files, "proposals": proposals}, sort_keys=True, indent=1) + "\n"
    if path.read_text(encoding="utf-8") != text:
        path.write_text(text, encoding="utf-8")


def build_worktree() -> Path:
    worktree = config.CRAWL_WORKTREE_DIR
    if f"worktree {worktree}" in status.git("worktree", "list", "--porcelain").splitlines():
        status.git("worktree", "remove", "--force", "--force", str(worktree))
    shutil.rmtree(worktree, ignore_errors=True)
    status.git("worktree", "prune")
    status.git("worktree", "add", "-q", "-B", config.CRAWL_BRANCH, str(worktree), "HEAD")
    return worktree


def newest_activity() -> tuple[float, str]:
    """The newest modification under the checkout, and where — the files of PROBE_EXCLUDE aside."""
    newest, where = 0.0, ""
    for directory, subdirectories, files in os.walk(config.REPO_ROOT):
        relative = posixpath.normpath(os.path.relpath(directory, config.REPO_ROOT))
        subdirectories[:] = [name for name in subdirectories
                             if posixpath.normpath(posixpath.join(relative, name)) not in config.PROBE_EXCLUDE]
        for path in [relative] + [posixpath.normpath(posixpath.join(relative, name)) for name in files]:
            if path in config.PROBE_EXCLUDE:
                continue
            try:
                modified = os.lstat(config.REPO_ROOT / path).st_mtime
            except OSError:
                continue
            if modified > newest:
                newest, where = modified, path
    return newest, where


def write_batch_review(worktree: Path, batch: list[dict], base: dict[str, int]) -> tuple[str | None, dict[str, int]]:
    """One batch: at most CRAWL_ATTEMPT_COUNT_PER_BATCH attempts, then one commit of the kept amendments and the rows."""
    answer, failure, changed = None, None, set()
    for attempt in range(1, config.CRAWL_ATTEMPT_COUNT_PER_BATCH + 1):
        status.git("checkout", "--", ".", root=worktree)
        status.git("clean", "-fdq", root=worktree)
        result, failure = fetch_agent_answer(build_brief(batch, failure), worktree)
        if failure is None:
            parsed, failure = parse_answer(result, batch)
            answer = parsed or answer
        changed = changed_paths(worktree)
        failure = failure or scope_failure(batch, changed) or syntax_failure(worktree, changed)
        if failure is None:
            measured = load_worktree_invariants(worktree)
            raised = sorted(metric for metric, value in measured.items() if value > base.get(metric, 0))
            failure = f"the amendment raised {', '.join(raised)}" if raised else None
        print(f"  attempt {attempt}: {failure or 'kept'}", flush=True)
        if failure is None:
            base = measured
            break
    edited = changed & {item["path"] for item in batch}
    snapshot = to_checkout_relative(config.SKILLS_STATUS_JSON_PATH)
    record_path = worktree / to_checkout_relative(config.SKILLS_REVIEW_JSON_PATH)
    status.git("checkout", "--", "." if failure else snapshot, root=worktree)
    status.git("clean", "-fdq", root=worktree)
    kept = sorted(changed - {snapshot}) if failure is None else []
    if kept:
        status.git("add", "--", *kept, root=worktree)
    blobs = index_blob_ids(worktree)
    canon = status.canon_id(blobs)
    record = json.loads(record_path.read_text(encoding="utf-8"))
    rows = {row["path"]: row for row in record["files"]}
    rows.update((row["path"], row) for row in build_review_rows(batch, answer, edited, failure, blobs, canon))
    proposals = {proposal["pattern"]: proposal for proposal in record["proposals"]}
    if answer and failure is None:
        proposals.update((proposal["pattern"], {**proposal, "canon_id": canon, "occurrence_count": len(proposal["occurrences"])})
                         for proposal in answer.get("proposals", []))
    write_review_record(record_path, {"files": list(rows.values()), "proposals": list(proposals.values())},
                        set(status.crawl_paths()), canon)
    status.git("add", "--", to_checkout_relative(config.SKILLS_REVIEW_JSON_PATH), root=worktree)
    module = batch[0]["module"]
    status.git("commit", "-q", "-m", f"{'Defer' if failure else 'Review'} {module}: {len(batch)} file(s)", root=worktree)
    return failure, base


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else None
    if status.git("status", "--porcelain"):
        print("the checkout is not clean: a file git does not track is work in progress, and scratch belongs in a gitignored path")
        return 1
    unmerged = int(status.git("rev-list", "--count", f"HEAD..{config.CRAWL_BRANCH}").strip()) \
        if status.git("branch", "--list", config.CRAWL_BRANCH).strip() else 0
    if unmerged:
        print(f"{config.CRAWL_BRANCH} holds {unmerged} unmerged commit(s) — "
              f"git merge --no-ff --no-edit {config.CRAWL_BRANCH} | git branch -D {config.CRAWL_BRANCH}")
        return 1
    queue = build_queue()
    batches = queue_batches(queue)
    if mode == "--queue":
        for item in queue:
            print(f"{item['class']:<10}  {'review-only' if item['review_only'] else 'amendable':<11}  {item['path']}")
        print(f"{len(queue)} file(s) queued; this pass reviews {sum(map(len, batches))} in {len(batches)} batch(es)")
        return 0
    if not batches:
        print("nothing to review: every file in scope carries a current verdict")
        return 0
    if mode == "--brief":
        print(build_brief(batches[0], None))
        return 0
    if shutil.which(config.AGENT_COMMAND[0]) is None:
        print(f"{config.AGENT_COMMAND[0]} is not on PATH")
        return 1
    newest, where = newest_activity()
    if config.QUIET_PROBE_SECONDS and time.time() - newest < config.QUIET_PROBE_SECONDS:
        print(f"skipped: activity at {where}")
        return 0
    worktree = build_worktree()
    outcomes = Counter()
    try:
        base = load_worktree_invariants(worktree)
        status.git("checkout", "--", ".", root=worktree)
        for number, batch in enumerate(batches, start=1):
            print(f"batch {number}/{len(batches)} — {batch[0]['module']}: "
                  f"{', '.join(item['path'] for item in batch)}", flush=True)
            failure, base = write_batch_review(worktree, batch, base)
            outcomes["deferred batches" if failure else "kept batches"] += 1
            outcomes["files"] += len(batch)
            if status.git("status", "--porcelain"):
                raise SystemExit("the checkout changed during the pass; the pass stops")
        load_worktree_invariants(worktree)
        if status.git("status", "--porcelain", root=worktree):
            status.git("add", "--", to_checkout_relative(config.SKILLS_STATUS_JSON_PATH), root=worktree)
            short = status.git("rev-parse", "--short", "HEAD", root=worktree).strip()
            status.git("commit", "-q", "-m", f"Record the tree's counts at {short}", root=worktree)
    finally:
        status.git("worktree", "remove", "--force", str(worktree))
    print(f"reviewed {outcomes['files']} file(s) in {outcomes['kept batches']} kept and {outcomes['deferred batches']} "
          f"deferred batch(es) — git merge --no-ff --no-edit {config.CRAWL_BRANCH} | git branch -D {config.CRAWL_BRANCH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

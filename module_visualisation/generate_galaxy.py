"""Render the tracked git tree into module_monitoring/repo_galaxy.html.

The picture is not a drawing of the repository; it is the repository. Nodes are
the files and folders `git ls-files` reports, edges are parent -> child and
nothing else, and the whole structure is spliced into the one marked region of
Files_and_Folders_Visualisation.html. Everything outside that region is
hand-written rendering code this module never touches.

    git ls-files
      -> exclude globs
      -> tree, folders inferred from the paths
      -> aggregate rules collapse a matching folder into a single node
      -> stories by longest prefix (unmapped is an error, not a default)
      -> NODES / EDGES + the header block
      -> splice -> module_monitoring/repo_galaxy.html

Two properties are load-bearing. The first is that galaxy_config.json is the
whole configuration surface: shape, colour, wording, camera and placement all
come from there, an unknown key is reported by name rather than ignored, and
changing the picture never means editing this file. The second is determinism:
the same commit must produce the same bytes, so paths are sorted by byte,
children by folders-then-name, JSON by key, and the only date in the output is
the committer date of a commit — never the moment the generator ran.

Standard library only, plus the git binary. The generator has to run on a CI
runner with no virtual environment, which is also why it imports nothing from
module_data or module_ml.
"""

from __future__ import annotations

import argparse
import functools
import json
import re
import subprocess
from pathlib import Path

from . import config

PROVENANCE_WALK_LIMIT = 64          # a chain of output-only commits longer than this is not a real history


class GalaxyError(Exception):
    """A configuration or repository state that cannot produce a picture.

    Raised with the offending name and the fix in the message, because the
    whole point of the strict mode is that a change in the files forces a
    conscious one-line decision in the JSON.
    """


def _git(*args: str) -> str:
    done = subprocess.run(("git", *args), cwd=config.REPO_ROOT,
                          capture_output=True, text=True, check=False)
    if done.returncode != 0:
        raise GalaxyError(f"git {' '.join(args)} failed: {done.stderr.strip()}")
    return done.stdout


def load_tracked_paths() -> list[str]:
    """Every tracked path, in git's own byte order.

    -z rather than plain output: git quotes and escapes unusual names otherwise,
    and a quoted path would enter the tree as a different file.
    """
    raw = _git("ls-files", "-z")
    paths = [p for p in raw.split("\0") if p]
    return sorted(paths, key=lambda p: p.encode("utf-8"))


def load_provenance_stamp(output_relative: str) -> tuple[str, str]:
    """The commit the tree was read from: HEAD, walked back past commits that
    changed nothing except the generated page.

    Walking is what lets --check survive the workflow's own commit. A stamp that
    simply named HEAD would change the moment the bot committed the regenerated
    page, so the next run would produce different bytes for an identical tree
    and the freshness check would fail on the commit the workflow had just made.
    """
    if _git("rev-parse", "--is-shallow-repository").strip() == "true":
        raise GalaxyError(
            "the repository is a shallow clone, so the stamp cannot be trusted: at a graft every\n"
            "  file looks new, the walk stops on the first commit it sees, and a page-only commit\n"
            "  would be stamped as though it were the tree's own.\n"
            "  fix: fetch the history — the workflow pins `fetch-depth: 0` for exactly this reason."
        )
    commit = _git("rev-parse", "HEAD").strip()
    for _ in range(PROVENANCE_WALK_LIMIT):
        changed = [line.strip() for line in
                   _git("show", "--first-parent", "--name-only", "--format=", commit).split("\n")]
        changed = [line for line in changed if line]
        if not changed or set(changed) - {output_relative}:
            break
        parents = _git("rev-list", "--parents", "-n", "1", commit).split()
        if len(parents) < 2:
            break
        commit = parents[1]
    return (_git("rev-parse", "--short", commit).strip(),
            _git("show", "-s", "--format=%cI", commit).strip())


def load_repository_name() -> tuple[str, str]:
    """Owner and repository from the origin URL — the one place the project's own
    name is allowed to appear in this module."""
    url = _git("config", "--get", "remote.origin.url").strip()
    tail = url.rsplit(":", 1)[-1].rsplit("/", 2)[-2:]
    if len(tail) != 2:
        return ("", Path(config.REPO_ROOT).name)
    owner, name = tail
    return (owner, name[:-4] if name.endswith(".git") else name)


@functools.lru_cache(maxsize=None)
def _glob_regex(pattern: str, subtree: bool) -> re.Pattern:
    """One glob translated to a regex over a POSIX repository path.

    fnmatch is not usable: it has no `**`, and its `*` crosses `/`, so
    `module_*/config.py` would match paths it should not. pathlib grew
    full_match() only in 3.13 and the image is 3.12, so the translation lives
    here. `*` and `?` never cross a separator, `**/` stands for zero or more
    leading segments, and a trailing `/` means the directory and everything
    beneath it.
    """
    body = pattern.rstrip("/")
    out = []
    i = 0
    while i < len(body):
        if body.startswith("**/", i):
            out.append("(?:[^/]+/)*")
            i += 3
        elif body[i] == "*":
            out.append("[^/]*")
            i += 1
        elif body[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(body[i]))
            i += 1
    tail = "(?:/.*)?" if subtree else ""
    return re.compile("^" + "".join(out) + tail + "$")


def path_matches(pattern: str, path: str) -> bool:
    return _glob_regex(pattern, pattern.endswith("/")).match(path) is not None


def parent_id(node_id: str) -> str:
    head, separator, _ = node_id.rstrip("/").rpartition("/")
    return head + "/" if separator else "root"


def story_of(path: str, story_map: dict) -> str | None:
    """Longest prefix wins; a directory key covers itself and its subtree."""
    best_key = None
    best_story = None
    for key, story_id in story_map.items():
        hit = path == key or (key.endswith("/") and path.startswith(key))
        if hit and (best_key is None or len(key) > len(best_key)):
            best_key, best_story = key, story_id
    return best_story


def role_of(node_id: str, is_folder: bool) -> str:
    if node_id == "root":
        return config.ROLE_FOR_ROOT
    if is_folder:
        return config.ROLE_FOR_FOLDER
    name = node_id.rsplit("/", 1)[-1]
    if name in config.ROLE_BY_EXACT_NAME:
        return config.ROLE_BY_EXACT_NAME[name]
    suffix = name[name.rfind("."):] if "." in name[1:] else ""
    return config.ROLE_BY_SUFFIX.get(suffix, config.ROLE_FALLBACK)


def _validate_keys(where: str, given, allowed) -> None:
    unknown = sorted(set(given) - set(allowed))
    if unknown:
        raise GalaxyError(
            f"galaxy_config.json: unknown key {unknown[0]!r} in {where}.\n"
            f"  known keys here: {', '.join(sorted(allowed))}\n"
            f"  fix: correct the spelling, or drop the key — the generator never ignores one silently."
        )


def load_config(path: Path) -> dict:
    given = json.loads(path.read_text(encoding="utf-8"))
    _validate_keys("the top level", given, config.CONFIG_DEFAULTS)
    settings = dict(config.CONFIG_DEFAULTS)
    settings.update(given)
    _validate_keys('"camera"', settings["camera"], config.CAMERA_KEYS)
    _validate_keys('"header"', settings["header"], config.HEADER_KEYS)
    _validate_keys('"core"', settings["core"], config.CORE_KEYS)
    for story_id, story in settings["stories"].items():
        _validate_keys(f'"stories"."{story_id}"', story, config.STORY_KEYS)
    for place_key, place in settings["place"].items():
        _validate_keys(f'"place"."{place_key}"', place, config.PLACE_KEYS)
    return settings


def build_tree(paths: list[str], aggregate: dict) -> tuple[dict, list]:
    """Leaves and folders of the picture, with aggregate folders already collapsed.

    Returns the node table keyed by id and the ordered child lists.
    """
    collapsed = {}
    for pattern, role in aggregate.items():
        stem = pattern.rstrip("/")
        for path in paths:
            head = path.rsplit("/", 1)[0] if "/" in path else ""
            while head:
                if _glob_regex(stem, False).match(head):
                    collapsed[head + "/"] = role
                    break
                head = head.rsplit("/", 1)[0] if "/" in head else ""

    leaves = {}
    for path in paths:
        folded = next((node_id for node_id in collapsed if path.startswith(node_id)), None)
        if folded:
            leaves[folded] = collapsed[folded]
        else:
            leaves[path] = None

    nodes = {"root": {"id": "root", "path": "repo/", "type": "core"}}
    for leaf_id, aggregate_role in leaves.items():
        nodes[leaf_id] = {"id": leaf_id, "path": leaf_id, "type": "file",
                          "aggregate_role": aggregate_role}
        walker = parent_id(leaf_id)
        while walker != "root":
            nodes.setdefault(walker, {"id": walker, "path": walker, "type": "folder"})
            walker = parent_id(walker)

    children = {node_id: [] for node_id in nodes}
    for node_id in nodes:
        if node_id != "root":
            children[parent_id(node_id)].append(node_id)
    for node_id in children:
        children[node_id].sort(key=lambda c: (nodes[c]["type"] == "file", c.encode("utf-8")))
    return nodes, children


def ordered_ids(children: dict) -> list[str]:
    """Depth-first from the root in child order — a stable, readable emission order."""
    out = []
    stack = ["root"]
    while stack:
        node_id = stack.pop()
        out.append(node_id)
        stack.extend(reversed(children[node_id]))
    return out


def resolve_key(raw: str, nodes: dict, where: str) -> str:
    for candidate in (raw, raw.rstrip("/") + "/", raw.rstrip("/")):
        if candidate in nodes:
            return candidate
    raise GalaxyError(
        f"galaxy_config.json: {where} points at {raw!r}, which is not in the picture.\n"
        f"  fix: use a path that `git ls-files` reports and that `exclude` does not remove."
    )


def annotations_for(raw: dict, nodes: dict) -> dict:
    """Path-keyed annotations resolved to node ids.

    A key that matches nothing is dropped rather than reported: a description
    left behind by a deleted file is stale, not broken, and the WO asks for a
    missing description to be an empty panel line and never an error. The keys
    that DO change geometry — "place" and a story's "hub" — go through
    resolve_key instead, where a typo is a hard error.
    """
    resolved = {}
    for key, value in raw.items():
        for candidate in (key, key.rstrip("/") + "/", key.rstrip("/")):
            if candidate in nodes:
                resolved[candidate] = value
                break
    return resolved


def hub_of(story_id: str, story: dict, members: list, nodes: dict) -> str:
    if story.get("hub"):
        return resolve_key(story["hub"], nodes, f'"stories"."{story_id}"."hub"')
    if not members:
        raise GalaxyError(
            f'galaxy_config.json: story "{story_id}" has no files, so it cannot be drawn.\n'
            f"  fix: map at least one path to it in \"story_map\", or remove the story."
        )
    folders = [m for m in members if nodes[m]["type"] == "folder"]
    pool = folders or members
    return min(pool, key=lambda m: (m.count("/"), m.encode("utf-8")))


def build_structure(settings: dict) -> tuple[list, list, dict, dict]:
    paths = load_tracked_paths()
    kept = [p for p in paths
            if not any(path_matches(pattern, p) for pattern in settings["exclude"])]
    nodes, children = build_tree(kept, settings["aggregate"])

    stories = settings["stories"]
    unmapped = []
    for node_id, node in nodes.items():
        if node_id == "root":
            node["island"] = "core"
            continue
        story_id = story_of(node_id, settings["story_map"]) or settings["default_story"]
        if story_id is None:
            unmapped.append(node_id)
        elif story_id not in stories:
            raise GalaxyError(
                f"galaxy_config.json: \"story_map\" sends {node_id!r} to story {story_id!r}, "
                f"which \"stories\" does not define.\n"
                f"  fix: add {story_id!r} to \"stories\", or point the path at an existing story."
            )
        node["island"] = story_id
    if unmapped:
        listed = "\n".join(f"    {p}" for p in sorted(unmapped)[:40])
        more = "" if len(unmapped) <= 40 else f"\n    ... and {len(unmapped) - 40} more"
        raise GalaxyError(
            f"galaxy_config.json: {len(unmapped)} path(s) belong to no story:\n{listed}{more}\n"
            f'  fix: add a "story_map" entry for each — the shortest prefix that covers them is\n'
            f"       usually the right one — or set \"default_story\" to a story id to stop\n"
            f"       classifying new things consciously."
        )

    descriptions = annotations_for(settings["descriptions"], nodes)
    roles = annotations_for(settings["roles"], nodes)

    order = ordered_ids(children)
    hubs = {}
    for story_id, story in stories.items():
        members = [n for n in order if nodes[n].get("island") == story_id]
        hubs[story_id] = hub_of(story_id, story, members, nodes)

    emitted = []
    for node_id in order:
        node = nodes[node_id]
        is_folder = node["type"] in ("folder", "core")
        record = {
            "id": node_id,
            "path": node["path"],
            "island": node["island"],
            "type": node["type"],
            "role": roles.get(node_id) or node.get("aggregate_role")
                    or role_of(node_id, is_folder),
            "desc": descriptions.get(node_id, ""),
        }
        if node_id in hubs.values():
            record["hub"] = True
        emitted.append(record)

    edges = []
    for node_id in order:
        for child in children[node_id]:
            edges.append({
                "from": node_id,
                "to": child,
                "kind": "tree",
                "thick": nodes[node_id]["type"] != "file" and nodes[child]["type"] != "file",
            })

    counts = {
        "files": len(kept),
        "modules": sum(1 for c in children["root"] if nodes[c]["type"] == "folder"),
        "assets": sum(1 for n in nodes.values() if n.get("aggregate_role")),
        "nodes": len(emitted),
        "edges": len(edges),
    }
    place = {resolve_key(k, nodes, '"place"'): v for k, v in settings["place"].items()}
    return emitted, edges, place, counts


def build_meta(settings: dict, counts: dict) -> dict:
    header = settings["header"]
    owner, repository = load_repository_name()
    short, committed_at = load_provenance_stamp(
        str(config.MODULE_MONITORING_REPO_GALAXY_HTML_PATH.relative_to(config.REPO_ROOT)))
    template = header.get("subtitle") or "{files} tracked files"
    try:
        subtitle = template.format(**counts)
    except KeyError as unknown:
        raise GalaxyError(
            f'galaxy_config.json: "header"."subtitle" uses {{{unknown.args[0]}}}, which is not a count.\n'
            f"  fix: use one of {', '.join('{' + k + '}' for k in sorted(counts))}."
        ) from None
    title = header.get("title") or "Repo Silk Galaxy"
    eyebrow = f"{owner} / {repository}" if header.get("eyebrow_from_git", True) else ""
    return {
        "title": title,
        "documentTitle": f"{title} · {repository}",
        "eyebrow": eyebrow,
        "subtitle": f"{subtitle} · tree as of {short} · {committed_at}",
        "config": {config.CAMERA_KEYS[k]: v for k, v in settings["camera"].items()},
    }


def _literal(name: str, value) -> str:
    body = json.dumps(value, sort_keys=True, ensure_ascii=True, indent=1)
    return f"const {name} = {body};"


def build_structure_block(meta: dict, islands: dict, order: list,
                          place: dict, nodes: list, edges: list) -> str:
    lines = [
        f"{config.STRUCTURE_BEGIN_MARKER} - written by "
        f"module_visualisation/generate_galaxy.py, do not edit by hand */",
        _literal("META", meta),
        _literal("ISLANDS", islands),
        _literal("ISLAND_ORDER", order),
        _literal("PLACE", place),
        _literal("NODES", nodes),
        _literal("EDGES", edges),
        config.STRUCTURE_END_MARKER,
    ]
    # a description carrying "</script>" would end the block early; escaping the
    # angle bracket is the one transformation applied to the emitted literals
    return "\n".join(lines).replace("<", "\\u003c")


def render_html(template_text: str, block: str) -> str:
    begin = template_text.find(config.STRUCTURE_BEGIN_MARKER)
    end = template_text.find(config.STRUCTURE_END_MARKER)
    if begin < 0 or end < 0 or end < begin:
        raise GalaxyError(
            f"{config.GALAXY_TEMPLATE_HTML_PATH.name}: the structure markers are missing or out of "
            f"order.\n  fix: the template must contain {config.STRUCTURE_BEGIN_MARKER!r} once, then "
            f"{config.STRUCTURE_END_MARKER!r} once."
        )
    if template_text.count(config.STRUCTURE_BEGIN_MARKER) != 1 or \
            template_text.count(config.STRUCTURE_END_MARKER) != 1:
        raise GalaxyError(
            f"{config.GALAXY_TEMPLATE_HTML_PATH.name}: the structure markers appear more than once, "
            f"so the generator cannot tell which region it owns.\n  fix: leave exactly one pair."
        )
    return template_text[:begin] + block + template_text[end + len(config.STRUCTURE_END_MARKER):]


def galaxy_html() -> str:
    settings = load_config(config.GALAXY_CONFIG_JSON_PATH)
    nodes, edges, place, counts = build_structure(settings)
    meta = build_meta(settings, counts)
    islands = {"core": settings["core"]}
    for story_id, story in settings["stories"].items():
        islands[story_id] = {"name": story["name"], "color": story["color"]}
    order = settings["story_order"] or list(settings["stories"])
    unknown = [s for s in order if s not in settings["stories"]]
    if unknown:
        raise GalaxyError(
            f'galaxy_config.json: "story_order" names {unknown[0]!r}, which "stories" does not define.\n'
            f"  fix: list only defined story ids, or drop the key to use the order of \"stories\"."
        )
    block = build_structure_block(meta, islands, order, place, nodes, edges)
    template_text = config.GALAXY_TEMPLATE_HTML_PATH.read_text(encoding="utf-8")
    return render_html(template_text, block), counts


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Render the tracked git tree into module_monitoring/repo_galaxy.html.")
    parser.add_argument("--check", action="store_true",
                        help="regenerate in memory and compare with the committed page; "
                             "exit 1 on drift, say nothing when fresh")
    arguments = parser.parse_args()

    try:
        html, counts = galaxy_html()
    except GalaxyError as failure:
        print(str(failure))
        return 1

    out = config.MODULE_MONITORING_REPO_GALAXY_HTML_PATH
    if arguments.check:
        committed = out.read_text(encoding="utf-8") if out.exists() else ""
        if committed == html:
            return 0
        print(f"{out.relative_to(config.REPO_ROOT)} is stale: the tree has moved since it was written.\n"
              f"  committed {len(committed)} bytes, regenerated {len(html)} bytes\n"
              f"  fix: run `make visualisation-galaxy` and commit the result.")
        return 1

    out.write_text(html, encoding="utf-8", newline="\n")
    print(f"wrote {out.relative_to(config.REPO_ROOT)} "
          f"({len(html) / 1024:.1f} KB) — {counts['nodes']} nodes, {counts['edges']} edges, "
          f"{counts['files']} tracked files, {counts['assets']} aggregated")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

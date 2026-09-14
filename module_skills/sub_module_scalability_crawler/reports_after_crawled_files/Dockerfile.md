
## crawled 2026-09-14 04:59 UTC · claude-sonnet-5 · d2fc592
## Departures

None found. The file matches the written rules for the root `Dockerfile`: base `python:3.12-slim` (`AGENTS.md` § Minimum requirements), no code copied and only `requirements.txt` installed (`module_skills/skill_asset_containers.md` § The topology: "the `Dockerfile` installs the pins of `requirements.txt` onto `python:3.12-slim` and copies no code — the code arrives through `.:/app`, the state through the `/store/<content>` mounts beside it"), and the comment's vocabulary matches the canon's own terms for the tree mount and the store mounts (`module_skills/glossary.md` § Stores; `module_skills/skill_asset_containers.md`).

## Unexplained

- `Dockerfile:7` — `WORKDIR /app` is declared after `COPY requirements.txt .` (line 3) and `RUN pip install …` (line 4). `python:3.12-slim` sets no working directory, so the copy and the install both land at `/`, and `WORKDIR /app` takes effect only after both have already run. Nothing in the file or the rules says why the working directory is set last rather than first — a reader cannot tell whether this placement is deliberate (e.g. to keep `/app` free for the tree mount during build) or incidental.

## Unruled pattern

None — a single six-line file offers no internal repetition to generalise from.

conformant


## crawled 2026-09-14 07:44 UTC · claude-sonnet-5 · 20ac2db
Reviewing `Dockerfile` against the cited canon (`AGENTS.md`, `module_skills/skill_asset_containers.md`, `module_skills/skill_pre_aws_solution.md`, `module_skills/glossary.md`, naming/sorting skills).

1. Departures from a rule:
None found. `FROM python:3.12-slim` matches `AGENTS.md` § Minimum requirements and the images row of § Canonical vocabulary. `COPY requirements.txt .` + `RUN pip install --no-cache-dir -r requirements.txt` with no other `COPY` matches `module_skills/skill_asset_containers.md` § The topology ("the `Dockerfile` installs the pins of `requirements.txt` onto `python:3.12-slim` and copies no code") and `module_skills/skill_pre_aws_solution.md` § What stays as it is, and why (the Dockerfile row, marked "yes — done"). The trailing comment restates § Docker is compute, not storage correctly (image carries pins, `.:/app` carries code, `/store/<content>` mounts carry state) without inventing vocabulary outside the register.

2. What the file leaves unexplained:
`WORKDIR /app` is placed after `COPY`/`RUN` rather than before them, so `COPY requirements.txt .` and the `pip install` both land at the image's default root, not at `/app`. Nothing in the file or the cited rules says why the working directory is set only at the end rather than before the copy/install — a reader cannot decode from the file and rules alone whether this ordering is deliberate or incidental.

3. Pattern governed by no rule:
Not applicable — only one file reviewed, no repeated pattern to observe within it.

4. conformant


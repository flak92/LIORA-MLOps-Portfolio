
## crawled 2026-09-14 04:59 UTC · claude-sonnet-5 · d2fc592
## Departures

None found. The file matches the written rules for the root `Dockerfile`: base `python:3.12-slim` (`AGENTS.md` § Minimum requirements), no code copied and only `requirements.txt` installed (`module_skills/skill_asset_containers.md` § The topology: "the `Dockerfile` installs the pins of `requirements.txt` onto `python:3.12-slim` and copies no code — the code arrives through `.:/app`, the state through the `/store/<content>` mounts beside it"), and the comment's vocabulary matches the canon's own terms for the tree mount and the store mounts (`module_skills/glossary.md` § Stores; `module_skills/skill_asset_containers.md`).

## Unexplained

- `Dockerfile:7` — `WORKDIR /app` is declared after `COPY requirements.txt .` (line 3) and `RUN pip install …` (line 4). `python:3.12-slim` sets no working directory, so the copy and the install both land at `/`, and `WORKDIR /app` takes effect only after both have already run. Nothing in the file or the rules says why the working directory is set last rather than first — a reader cannot tell whether this placement is deliberate (e.g. to keep `/app` free for the tree mount during build) or incidental.

## Unruled pattern

None — a single six-line file offers no internal repetition to generalise from.

conformant


# module_visualisation

The tracked git tree, rendered as a self-contained 3D page.

`module_monitoring/files_and_folders_visualisation.html` is generated, never hand-edited. Nodes are the files and
folders `git ls-files` reports; edges are parent → child and nothing else. A push to `main`
regenerates it, so the picture always equals the tree.

```
make visualisation-generate         regenerate the page
make visualisation-check   fail if the committed page no longer matches the tree
```

Both run `python3 -m module_visualisation.generate` — standard library only, plus the `git`
binary. There is nothing to install, which is why the workflow can call the same target on a bare
runner.

The page is served by the dashboard that already exists: `make monitoring-dashboard`, then
<http://127.0.0.1:8900/files_and_folders_visualisation.html>, or the link in the dashboard footer.

## The one rule

**`visualisation_config.json` is the whole configuration surface.** Shape, colour, wording, camera and
placement all live there. Changing the picture never means editing Python. An unknown key is a hard
error naming the key, so a typo cannot be silently ignored.

## Every key

| key | what it does |
|---|---|
| `default_story` | Story id for paths no `story_map` entry covers. `null` (the default) makes an unmapped path a **hard error** instead — a new top-level thing has to be classified consciously. Set it to a story id to switch that friction off. |
| `exclude` | Glob patterns removed before anything else. `*` and `?` never cross `/`; `**/` stands for zero or more leading segments; a trailing `/` means the directory and everything beneath it. |
| `story_map` | Path → story id. **Longest prefix wins.** A key ending in `/` covers that directory and its subtree; any other key is an exact path. |
| `stories` | The stories themselves, each with `name` (shown in the legend and side panel), `color` (hex) and optional `hub`. |
| `stories.<id>.hub` | The path drawn at the centre of that story's island. Optional: by default the shallowest folder in the story wins, or its first file if it has no folder. A `hub` pointing at a path that is not in the picture is an error. |
| `story_order` | The order the islands are laid out in, clockwise. Defaults to the order of `stories`. The island count comes from this list, so adding a sixth story needs no code change. |
| `core` | `name` and `color` of the repository-root node. |
| `aggregate` | Directory glob → role. Each matching folder collapses into **one** node carrying the folder's name, and its contents vanish from the picture. Used for the per-asset artifact folders. |
| `place` | Path → hand-tuned position for one node, as `r` (fraction of the island radius), `da` (angle offset in radians from the island centre), `y` (vertical offset) and optional `jit` (the vertical jitter of that folder's own child ring). A path that is not in the picture is an error. |
| `roles` | Path → role, overriding the extension-based default. A role picks the glyph and the word the side panel shows: `artifact` draws the halo-and-diamond, everything else draws a plain file or folder. |
| `descriptions` | Path → the sentence the side panel shows. Optional everywhere: a node without one gets an empty line, never an error, and a description left behind by a deleted file is dropped rather than reported. |
| `camera` | `start_rot_y`, `start_rot_x` (radians) and `fit_width` (the viewport width at which the picture fits at zoom 1). |
| `header.eyebrow_from_git` | When true, the small line above the title is `<owner> / <repo>` read from `remote.origin.url`. |
| `header.title` | The heading, and the first half of the browser tab title. The repository name is appended to the tab title from git. |
| `header.subtitle` | The line under the heading. May use `{files}`, `{modules}`, `{assets}`, `{nodes}`, `{edges}` — respectively tracked files that survived `exclude`, top-level folders, aggregated folders, and the totals actually drawn. Any other placeholder is an error naming it. |

## The provenance stamp

The subtitle always ends with `tree as of <short-hash> · <committer date>`. That is the commit the
**tree was read from**, not the moment the file was built — the same commit twice produces the same
bytes.

The stamp walks back from `HEAD` past any commit that changed nothing but `files_and_folders_visualisation.html`. That
walk is what makes the workflow's own commit harmless: without it, the bot's regeneration commit
would become the newest commit, the next run would stamp a different hash for an identical tree, and
`visualisation-check` would fail on the commit the workflow had just made.

A shallow clone is refused rather than stamped. At a graft every file looks new, so the walk stops on
the first commit it sees and a page-only commit would be stamped as if it were the tree's own — the
page comes out byte-for-byte the same length with a different hash inside it, which is the worst kind
of wrong. `fetch-depth: 0` in the workflow is load-bearing, not decoration.

## The template

`files_and_folders_visualisation_template.html` is the rendering shell. The generator owns exactly one region
of it:

```js
/* VISUALISATION:STRUCTURE:BEGIN ... */
const META, ISLANDS, ISLAND_ORDER, PLACE, NODES, EDGES
/* VISUALISATION:STRUCTURE:END */
```

Everything outside those two markers is hand-written canvas code and is never touched. If the
markers are missing, out of order, or appear more than once, the generator refuses rather than
guessing which region is its own.

Edge weight is not a knob: an edge between two folders is drawn at 2.2 px in `#5F79B8`, an edge to a
file at 1 px in `#3A4C74`. The generator emits the flag; the renderer only obeys it.

## Determinism

Same commit, same bytes. Paths come from `git ls-files -z` in git's byte order; children sort folders
first, then by byte; every emitted literal is JSON with sorted keys and ASCII escapes; the file is
written with `\n` endings; and the only date in the output is a committer date. `--check` regenerates
in memory and compares — silent when fresh, and on drift it says which file is stale and what to run.

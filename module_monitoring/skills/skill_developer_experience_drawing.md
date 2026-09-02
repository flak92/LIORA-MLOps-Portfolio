# Skill: the developer-experience drawing

The repository's own tracked tree, drawn as one self-contained page. *The repository shows the
destination, not the road*: the page is redrawn by hand and by nothing else, and what tells a reader
how old it is, is the provenance stamp in its subtitle.

```
make monitoring-dx-update      redraw the page from the tree as it is now
```

That is the whole idea. There is no automation of any kind behind it.

Open it from the dashboard: the **DX** control in the top right corner of the status page, or
directly at `/sub_module_dx/files_and_folders_visualisation.html`. The dashboard already serves this
directory, so nothing in `serve.py` changes.

Nodes are the files and folders `git ls-files` reports; edges are parent → child and nothing else.
Standard library plus the `git` binary — there is nothing to install.

## The one rule

**`visualisation_config.json` is the whole configuration surface.** Shape, colour, wording, camera
and placement all live there. An unknown key is an error naming the key, so a typo in a key cannot
pass unnoticed — a typo in a *path*, under `roles` or `descriptions`, is dropped in silence, because
a path left behind by a deleted file is stale rather than broken. The one thing the JSON overrides
rather than owns is the default role of an extension: `roles` retypes a path at a time, and the
`.md` → doc, `.py` → code, `.json` → artifact defaults live in `config.py`, the way edge weight
does — not a knob.

## Every key

| key | what it does |
|---|---|
| `default_story` | Group for paths no `story_map` entry covers. It is **set**, so a newly added file simply joins that group and the drawing still builds. Setting it to `null` would instead make an unmapped path a hard error — deliberate friction this repository does not ask for. |
| `exclude` | Glob patterns removed before anything else. `*` and `?` never cross `/`; `**/` stands for zero or more leading segments; a trailing `/` means the directory and everything beneath it. The drawn page excludes itself here. |
| `story_map` | Path → group id. **Longest prefix wins.** A key ending in `/` covers that directory and its subtree; any other key is an exact path. |
| `stories` | The groups, one island each, with `name` (legend and side panel), `color` (hex) and optional `hub`. Ids must be `S1`…`S9`: the page reads a digit key as `S` plus that digit, and offers only the digits its stories answer to. |
| `stories.<id>.hub` | The path drawn at the centre of that group's island. Optional — by default the shallowest folder in the group wins. A `hub` naming a path that is not in the drawing is an error, and so is one that `story_map` puts on another story: that island would be drawn with no centre and the other with two. |
| `story_order` | The order the islands are laid out in, clockwise. The island count comes from this list. |
| `core` | `name` and `color` of the repository-root node. |
| `aggregate` | Directory glob → role. Each matching folder collapses into **one** node carrying the folder's name, and its contents leave the drawing. Used for the per-asset artifact folder. |
| `place` | Path → hand-tuned position: `r` (fraction of the island radius — the one the tree needs, `ISLAND_RADIUS` or more, so a placed node moves out with the picture), `da` (angle offset in radians), `y` (vertical offset), optional `jit` (vertical jitter of that folder's child ring). A path that is not in the drawing is an error. |
| `roles` | Path → role, overriding the extension default. A role picks the glyph and the word the side panel shows; `artifact` draws the halo and diamond. |
| `descriptions` | Path → the sentence the side panel shows. Optional everywhere: a node without one gets an empty line, and a description left behind by a deleted file is dropped rather than reported. |
| `camera` | `start_rot_y`, `start_rot_x` (radians) and `fit_width` (viewport width at which the drawing fits at zoom 1). |
| `header.eyebrow_from_git` | When true, the small line above the title is `<owner> / <repo>`, read from `remote.origin.url`. |
| `header.title` | The heading, and the first half of the browser tab title. |
| `header.subtitle` | The line under the heading. May use `{files}`, `{modules}`, `{assets}`, `{nodes}`, `{edges}` — tracked files that survived `exclude`, top-level folders, aggregated folders, and the totals actually drawn. Any other placeholder is an error naming it. |

## The provenance stamp

The subtitle always ends with `tree as of <short-hash> · <committer date>` — the commit the **tree
was read from**, not the moment the file was written. The same commit twice produces the same bytes.

The stamp walks back from `HEAD` past any commit that changed nothing but the page itself, so a
commit carrying only the page does not move it. A depth-limited clone is refused rather than
stamped: at a graft every file looks new, and the page would come out the same length with a
different hash inside — the worst shape a wrong artifact can take.

## The template

`files_and_folders_visualisation_template.html` is the rendering shell. This sub-module writes
exactly one region of it:

```js
/* VISUALISATION:STRUCTURE:BEGIN ... */
const META, ISLANDS, ISLAND_ORDER, PLACE, NODES, EDGES
/* VISUALISATION:STRUCTURE:END */
```

Everything outside those two markers is hand-written canvas code and is never touched. If the
markers are missing, out of order, or appear more than once, the run refuses rather than guessing
which region is its own.

Edge weight is not a knob: an edge between two folders is drawn at 2.2 px, an edge to a file at 1 px.

Spacing is not a knob either. Every node owns a disc — a file's is its glyph plus a share of its
name, a folder's is its children's ring plus the widest disc on it — and a ring is as wide as the
discs on it side by side, a loose member sits outside the hub's disc, and the islands stand where
neighbouring discs do not meet. The floors (`ISLAND_RADIUS`, the 72-unit ring, the 80-unit loose
ring), the gaps and the camera factor live in the template's `CONFIG` block; the tree does the rest,
so a folder that grows pushes its neighbours away by itself.

A node's shade is its island's colour turned a fixed step per nesting level below the hub
(`LEVEL_HUE_STEP`, `LEVEL_LIGHT_STEP`, also in `CONFIG`): a sub-module resembles its module and is
told apart from it, and the sidebar dot carries the same shade. The side panel's story dot stays the
island colour, because it names the story. Two levels down the amber family turns yellow and leans
toward the green; nothing in the tree nests that deep.

## Determinism

Same commit, same bytes. Paths come from `git ls-files -z` in git's byte order; children sort folders
first, then by byte; every emitted literal is JSON with sorted keys and ASCII escapes; the file is
written with `\n` endings; and the only date in the output is a committer date.

`--check` regenerates in memory and compares against the committed page — silent when fresh, and on
drift it says which file is stale and what to run. There is no make target for it: refreshing is a
deliberate act here, and the check exists for the moment you want to ask.

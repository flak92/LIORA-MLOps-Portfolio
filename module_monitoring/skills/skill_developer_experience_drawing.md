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
Standard library plus the `git` binary — there is nothing to install. The page holds two views of
that one tree, flipped by one control: the nodes and edges are the same in both, only the placement
and the wording change (§ Two views of one tree).

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
| `stories.<id>.hub` | The path that group's island is built around: first on the island's arc, with the halo and the label that never fades. Optional — by default the shallowest folder in the group wins. A `hub` naming a path that is not in the drawing is an error, and so is one that `story_map` puts on another story: that island would be drawn with no centre and the other with two. |
| `story_order` | The order the islands are laid out in, clockwise. The island count comes from this list. |
| `core` | `name` and `color` of the repository-root node. |
| `aggregate` | Directory glob → role. Each matching folder collapses into **one** node carrying the folder's name, and its contents leave the drawing. Used for the per-asset artifact folder. |
| `place` | Path → hand-tuned position: `r` (fraction of the island radius — the one the tree needs, `ISLAND_RADIUS` or more, so a placed node moves out with the picture), `da` (angle offset in radians), `y` (vertical offset), optional `jit` (vertical jitter of that folder's child fan). A path that is not in the drawing is an error. |
| `roles` | Path → role, overriding the extension default. A role picks the glyph and the word the side panel shows; `artifact` draws the halo and diamond. |
| `descriptions` | Path → the sentence the side panel shows. Optional everywhere: a node without one gets an empty line, and a description left behind by a deleted file is dropped rather than reported. |
| `camera` | `start_rot_y`, `start_rot_x` (radians) and `fit_width` (viewport width at which the drawing fits at zoom 1). |
| `deployment` | Optional. The deployment view: a second placement of the same tree, seated on the primitives `../../module_skills/skill_pre_aws_solution.md` § The mapping table names. It holds only the keys that place and word — `default_story`, `story_map`, `stories`, `story_order`, `core`, `place`, `descriptions`, `camera` — each meaning what it means above and checked by the same key sets, the error naming the block; any other key here is an error. `exclude`, `aggregate`, `roles` and `header` define the tree and are shared. Absent, the page has one view and no view control. |
| `deployment.<key>` | The same key, for the deployment view. A key the block leaves out is the top level's; `descriptions` and `camera` layer over the top level's entry by entry, so the block says only the sentences and the start angle that change, and every other key it names replaces the top level's whole. Its `camera` is scanned for its own layout. |
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
const META, VIEWS, VIEW_ORDER, NODES, EDGES
/* VISUALISATION:STRUCTURE:END */
```

Everything outside those two markers is hand-written canvas code and is never touched. If the
markers are missing, out of order, or appear more than once, the run refuses rather than guessing
which region is its own. `NODES` and `EDGES` carry the tree alone. `VIEWS` holds, per view, the
islands and their order, the hand places, each node's island, each island's hub, each node's
sentence and the camera, so the page can seat one tree twice; `VIEW_ORDER` names the development
view first, and a page built without a `deployment` block lists one view and hides the control.

Edge weight is not a knob: an edge between two folders is drawn at 2.2 px, an edge to a file at 1 px.

Spacing is not a knob either. Every node owns a disc — a file's is its glyph plus a share of its
name, a folder's is its children's fan plus the widest disc on it. A folder's children fan out on an
arc that faces away from the folder's own parent, only as wide as their discs side by side and never
wider than `FAN_SPAN`, so the edge that arrives at a folder never runs through the fan it holds and
no folder's edges cross another's. An island's root-level members — the hub, and any member whose
parent lives on another island — stand side by side at the island radius, and the islands share the
circle in proportion to what they hold. The floors (`ISLAND_RADIUS`, the 72-unit fan), the gaps, the
fan width and the camera factor live in the template's `CONFIG` block; the tree does the rest, so a
folder that grows pushes its neighbours away by itself. The picture turns, and two edges apart in the
plane may still cross on the screen for a moment; the plane is what the layout answers for.

A node's shade is its island's colour turned a fixed step per nesting level below the hub
(`LEVEL_HUE_STEP`, `LEVEL_LIGHT_STEP`, also in `CONFIG`): a sub-module resembles its module and is
told apart from it, and the sidebar dot carries the same shade. The side panel's story dot stays the
island colour, because it names the story. Two levels down the amber family turns yellow and leans
toward the green; nothing in the tree nests that deep.

## Two views of one tree

The top level of `visualisation_config.json` is the **development view** — the tree as tracked, its
islands the stories. The `deployment` block is the **deployment view** — the same files and folders
seated on the primitives the mapping table names, so a reader can see that the folder structure
already has that shape. The names are the 4+1 model's: the development view is the code's
organisation, the deployment view its mapping onto infrastructure; neither is a deployment, and
nothing is built by either. One control flips the page — ☁ goes to the deployment view, ⌂ returns,
the key is `v` — and the legend in the bottom right names the view that is showing and its islands;
a legend row isolates its island as the digit does. What changes on a flip is the island a node sits
on, the hub, the palette, the sentence in the side panel, the digit keys and the camera; the
selection, the highlighted subtree and the sidebar are the tree's and stay, which is the point —
click a file, press `v`, and watch where it lives. ⟲ — the `0` of the hint's `0 all` — returns the
camera of the view that is showing to its start and clears the selection, the subtree and the
isolated island.

The deployment view is the one picture of the mapping table's right column, and the fifth place a
cloud proper noun may be spoken (`AGENTS.md` § Pre-AWS architectural direction): an island is a row
of that column a tracked path answers to, its name carries the primitive in words with the proper
noun in parentheses as the table spells it, its sentences say what each object *is* there and never
how to move it, and no island names a primitive the table does not. One island is no row: the
repository's own documents — the contract, the overview, the skills — answer to no primitive, and
their island says so in its name.

**A view seats each top-level subtree whole.** The layout answers for crossings inside an island,
where every parent → child edge is radial. A member whose parent is a folder on another island is
seated as a second root at the island radius and its edge becomes a chord across the picture — a
chord that can cross the parent's fan or graze the roots beside it. A path whose parent is the root
is always free; a deeper path costs a chord, so a view splits a subtree only knowingly, and the
deployment view splits none: the two snapshots stay beside the page they are served with, the two
sub-modules with the module that serves them, and their sentences say what each is there.

## Determinism

Same commit, same bytes. Paths come from `git ls-files -z` in git's byte order; children sort folders
first, then by byte; every emitted literal is JSON with sorted keys and ASCII escapes; the file is
written with `\n` endings; and the only date in the output is a committer date.

`--check` regenerates in memory and compares against the committed page — silent when fresh, and on
drift it says which file is stale and what to run. There is no make target for it: refreshing is a
deliberate act here, and the check exists for the moment you want to ask.

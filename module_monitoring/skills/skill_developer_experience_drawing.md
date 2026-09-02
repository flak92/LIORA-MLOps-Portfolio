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

Nodes are the files and folders `git ls-files` reports and, in the deployment view, the primitives
the mapping table names; edges are parent → child and, between primitives, the flows the view
declares — nothing else. Standard library plus the `git` binary — there is nothing to install. The
page holds two views of that one tree, flipped by one control: the tree's nodes and edges are the
same in both; a view adds its own primitives and flows, and the placement and the wording change
(§ Two views of one tree).

## The one rule

**`visualisation_config.json` is the whole configuration surface.** Shape, colour, wording, camera
and placement all live there. An unknown key is an error naming the key, so a typo in a key cannot
pass unnoticed — a typo in a *path*, under `roles` or `descriptions`, is dropped in silence, because
a path left behind by a deleted file is stale rather than broken. The one thing the JSON overrides
rather than owns is the default role of an extension: `roles` retypes a path at a time — the
deployment block may layer its own, so a path can be one role as tracked and another on the
primitives — and the `.md` → doc, `.py` → code, `.json` → artifact defaults live in `config.py`, the
way edge weight does — not a knob.

## Every key

| key | what it does |
|---|---|
| `default_story` | Group for paths no `story_map` entry covers. It is **set**, so a newly added file simply joins that group and the drawing still builds. Setting it to `null` would instead make an unmapped path a hard error — deliberate friction this repository does not ask for. |
| `exclude` | Glob patterns removed before anything else. `*` and `?` never cross `/`; `**/` stands for zero or more leading segments; a trailing `/` means the directory and everything beneath it. The drawn page excludes itself here. |
| `story_map` | Path → group id. **Longest prefix wins.** A key ending in `/` covers that directory and its subtree; any other key is an exact path. |
| `stories` | The groups, one island each, with `name` (legend and side panel), `color` (hex) and optional `hub`. Ids must be `S1`…`S9`: the page reads a digit key as `S` plus that digit, and offers only the digits its stories answer to. |
| `stories.<id>.hub` | The node — a path, or a primitive id — that group's island is built around: first on the island's arc, with the halo and the label that never fades. Optional — by default the shallowest folder in the group wins. A `hub` naming a path that is not in the drawing is an error, and so is one that `story_map` puts on another story: that island would be drawn with no centre and the other with two. |
| `story_order` | The order the islands are laid out in, clockwise. The island count comes from this list. |
| `core` | `name` and `color` of the repository-root node. |
| `aggregate` | Directory glob → role. Each matching folder collapses into **one** node carrying the folder's name, and its contents leave the drawing. Used for the per-asset artifact folder. |
| `place` | Path → hand-tuned position: `r` (fraction of the island radius — the one the tree needs, `ISLAND_RADIUS` or more, so a placed node moves out with the picture), `da` (angle offset in radians), `y` (vertical offset), optional `jit` (vertical jitter of that folder's child fan). A path that is not in the drawing is an error. |
| `roles` | Path → role, overriding the extension default. A role picks the glyph and the word the side panel shows; `artifact` draws the halo and diamond, `database` the cylinder. A view may layer its own `roles` over the top level's, entry by entry: `database` is the deployment view's role for the aggregate folder. |
| `descriptions` | Path → the sentence the side panel shows. Optional everywhere: a node without one gets an empty line, and a description left behind by a deleted file is dropped rather than reported. |
| `camera` | `start_rot_y`, `start_rot_x` (radians), `fit_width` (viewport width at which the drawing fits) and `fit_zoom` (the zoom it is fitted at — a view with a wider ring asks for more). |
| `deployment` | Optional. The deployment view: a second placement of the same tree, seated beside the primitives `../../module_skills/skill_pre_aws_solution.md` § The mapping table names. It holds only the keys that place and word — `default_story`, `story_map`, `stories`, `story_order`, `core`, `place`, `roles`, `descriptions`, `camera`, `primitives`, `flows`, `notice` — each meaning what it means in this table and checked by the same key sets, the error naming the block; any other key here is an error. `exclude`, `aggregate` and `header` define the tree and are shared. Absent, the page has one view and no view control. |
| `deployment.<key>` | The same key, for the deployment view. A key the block leaves out is the top level's; `roles`, `descriptions` and `camera` layer over the top level's entry by entry, so the block says only the roles, the sentences and the camera that change, and every other key it names replaces the top level's whole. Its `camera` is scanned for its own layout. |
| `primitives` | Id → `role`, `name`, optional `absent`. A primitive is a node a view declares for a row of the mapping table no tracked path is. It joins the view's nodes beside the tree, so `story_map` may name its id (exact match), a story may make it its `hub`, `place` may seat it and `descriptions` may give it a sentence; an unmapped id joins `default_story` like a path. `role` picks the icon from one closed set — registry, instance, container, store, database, state_machine, event_rule, log_streams, front, secret — and an unknown role is an error naming it. `absent: true` draws a dashed outline for a primitive nothing local answers to. An island seats its hub first, then its primitives in the order listed, then its tracked roots. The name's head — before the dash or the parenthesis — is the canvas label, so it is short; the rest is the panel's. The development view declares none. |
| `notice` | The words a view shows in the top right, in red capitals, one line per newline — what the picture is, in the presenter's words; empty shows nothing. The development view has none; the deployment view says its mapping is in progress. |
| `flows` | List of `{from, to}` over primitive ids of the same view. Each is one dashed edge with an arrowhead at `to`, coloured by the island it leaves, rising with its length (§ Two views of one tree). An endpoint that is not a node of the view is an error. |
| `header.eyebrow_from_git` | When true, the small line above the title is `<owner> / <repo>`, read from `remote.origin.url`. |
| `header.title` | The heading, and the first half of the browser tab title. |
| `header.subtitle` | The line under the heading. May use `{files}`, `{modules}`, `{assets}`, `{nodes}`, `{edges}` — tracked files that survived `exclude`, top-level folders, aggregated folders, and the tree's totals (a view's primitives and flows are not counted). Any other placeholder is an error naming it. |

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
const META, VIEWS, VIEW_ORDER, TREE_NODES, TREE_EDGES
/* VISUALISATION:STRUCTURE:END */
```

Everything outside those two markers is hand-written canvas code and is never touched. If the
markers are missing, out of order, or appear more than once, the run refuses rather than guessing
which region is its own. `TREE_NODES` and `TREE_EDGES` carry the tree alone — id, path, type and the
role a name gives. `VIEWS` holds, per view, the islands and their order, the hand places, each node's
island, role and sentence, each island's hub, the camera, and the view's own primitives as node
records and its flows as edge records, which the page adds to the tree on a flip; `VIEW_ORDER` names
the development view first, and a page built without a `deployment` block lists one view and hides
the control.

Edge weight is not a knob: an edge between two folders is drawn at 2.2 px, an edge to a file at 1 px;
a flow is dashed, arrowed at its target and coloured by the island it leaves — the third row of the
edge key, shown only when the view draws one.

Spacing is not a knob either. Every node owns a disc — a file's is its glyph plus a share of its
name, a folder's is its children's fan plus the widest disc on it. A folder's children fan out on an
arc that faces away from the folder's own parent, only as wide as their discs side by side and never
wider than `FAN_SPAN`, so the edge that arrives at a folder never runs through the fan it holds and
no folder's edges cross another's. An island's root-level members — the hub, and any member whose
parent lives on another island — stand side by side at the island radius, and the islands share the
circle in proportion to what they hold. The floors (`ISLAND_RADIUS`, the 72-unit fan), the gaps, the
fan width and the camera factor live in the template's `CONFIG` block; the tree does the rest, so a
folder that grows pushes its neighbours away by itself. A primitive owns a disc of its own floor,
`PRIMITIVE_EXTENT`, plus the share of its name a file gets, and stands as an island root — first when
it is the hub, else beside the hub before the island's tracked roots. The picture turns, and two edges apart in the plane may still cross on
the screen for a moment; the plane is what the layout answers for.

A node's shade is its island's colour turned a fixed step per nesting level (`LEVEL_HUE_STEP`,
`LEVEL_LIGHT_STEP`, also in `CONFIG`), counted from the island root the node fans from, so a module
seated beside a primitive hub keeps level 0 and its own shade: a sub-module resembles its module and
is told apart from it, and the sidebar dot carries the same shade. The side panel's story dot stays
the island colour, because it names the story. Two levels down the amber family turns yellow and
leans toward the green; nothing in the tree nests that deep.

## Two views of one tree

The top level of `visualisation_config.json` is the **development view** — the tree as tracked, its
islands the stories. The `deployment` block is the **deployment view** — the same files and folders
seated beside the primitives the mapping table names, so a reader can see that the folder structure
already has that shape. The names are the 4+1 model's: the development view is the code's
organisation, the deployment view its mapping onto infrastructure; neither is a deployment, and
nothing is built by either. One control flips the page — ☁ goes to the deployment view, ⌂ returns,
the key is `v` — and the legend in the bottom right names the view that is showing and its islands;
a legend row isolates its island as the digit does. What changes on a flip is the island a node sits
on, the hub, the palette, the role and the sentence in the side panel, the digit keys and the camera
— and the primitives and flows, which are the view's own; the selection, the highlighted subtree and
the sidebar are the tree's and stay, which is the point — click a file, press `v`, and watch where it
lives. A flip that leaves the selected primitive behind closes the panel. ⟲ — the `0` of the hint's
`0 all` — returns the camera of the view that is showing to its start and clears the selection, the
subtree and the isolated island. Nine islands exhaust the digit keys; a tenth row can never be an
island.

The deployment view is the one picture of the mapping table's right column, and the fifth place a
cloud proper noun may be spoken (`AGENTS.md` § Pre-AWS architectural direction). Every primitive
drawn is a row of that column, drawn as the icon of its role — a registry, a Linux instance, a
container, a store with the asset's database inside it, a state machine, an event rule, log streams,
a content-delivery front, a secret — with the tracked paths that answer to a row seated beside its
primitive; a row whose primitive is an object inside another row's — the task definition, the
artifact objects, the console — is a tracked path seated beside that primitive, not a primitive of
its own. A primitive's name carries the primitive in words with the proper noun in parentheses as the
table spells it, its sentence says what the object *is* there and never how to move it, and no
primitive names a row the table does not have. A row whose primitive has no local counterpart — the
event rule, whose condition is code and a table today; the log streams, whose logs are files of the
run record today; the strategy host and its brokerage secret, which have none at all — is drawn
absent: dashed, paler, its sentence ending *absent here — described*. A row that exists on disk but
untracked — the raw objects, the run records — is drawn solid and says so. One island is no row: the repository's own
documents — the contract, the overview, the skills — answer to no primitive, and their island says
so in its name.

**A view seats each top-level subtree whole.** The layout answers for crossings inside an island,
where every parent → child edge is radial. A member whose parent is a folder on another island is
seated as a second root at the island radius and its edge becomes a chord across the picture — a
chord that can cross the parent's fan or graze the roots beside it. A path whose parent is the root
is always free; a deeper path costs a chord, so a view splits a subtree only knowingly, and the
deployment view splits none: the two snapshots stay beside the page they are served with, the two
sub-modules with the module that serves them, and their sentences say what each is there.

**A flow rises with its length.** A flow is not a tree edge: it splits no subtree, and the crossing
guarantee neither covers nor needs it. Its arc rises in proportion to its length
(`FLOW_LIFT_PER_LENGTH`), so a flow between neighbouring islands is a low arch and a flow between
islands that are not neighbours in `story_order` is a high one, drawn over the fans it passes — an
arc, not a chord. `story_order` is chosen so most flows join neighbours; the deployment view has six
that do not: the state machine's arc to the task host, which sits above every stage by design; the
raw store's arc to the event rule, whose input it is; the task host's arc to the ml-research task,
because the host runs both tasks and both touch the store, and a circle gives an island two
neighbours; the reader's read of the run objects; and the store's two arcs to the absent strategy
host. A flow stops short of its target by `FLOW_TIP_GAP`, a hub's halo radius, so the arrowhead is
seen.

## Determinism

Same commit, same bytes. Paths come from `git ls-files -z` in git's byte order; children sort folders
first, then by byte; every emitted literal is JSON with sorted keys and ASCII escapes; the file is
written with `\n` endings; and the only date in the output is a committer date.

`--check` regenerates in memory and compares against the committed page — silent when fresh, and on
drift it says which file is stale and what to run. There is no make target for it: refreshing is a
deliberate act here, and the check exists for the moment you want to ask.

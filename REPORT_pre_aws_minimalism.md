# Report: the seats reviewed for excess

The Pre-AWS mapping of `module_skills/skill_pre_aws_solution.md` names, for
every local boundary, the standard primitive it would become on Amazon Web
Services (AWS). This report reads that mapping against one question: for a
repository that is one host, one asset, one image and four services, is each
seat the cheapest that keeps its boundary — no service that names nothing, no
two things doing one job, nothing described without the one condition under
which it would stand? *The repository shows the destination, not the road*:
nothing here is a plan, a price or an instance class; the measure is
boundaries, not money. A seat is kept only if removing it would lose a boundary
the mapping exists to name; a seat is excess if it names nothing a rename could
not; and where a seat is kept on a reason the demonstration never has, the
report says so.

## The measure, and where it comes from

The rule is `AGENTS.md` § Values, *Minimalism*, applied to infrastructure by
`module_skills/skill_pre_aws_solution.md` § Infrastructure seats: *the seat of
each thing is the cheapest that keeps its boundary*. A boundary is a row of the
mapping table (§ The mapping table); what each row costs is its fourth column,
*the move* (`module_skills/glossary.md` § Pre-AWS direction). The forms the
repository refused, each with its reason, are § Rejected forms. This report
adds no rule: it counts the seats, asks of each what could be less, and records
whether it is. A bare § below is a section of
`module_skills/skill_pre_aws_solution.md`.

## The count

What elsewhere holds, phase by phase of § The retrain runtime is a ladder, and
what the mapping names that the demonstration never runs.

| phase | services elsewhere | what runs there as here |
|---|---|---|
| the lift | one Linux instance (Amazon EC2) with one durable volume (Amazon EBS) | `docker compose`, the Makefile, a hand typing `make docker-all`, the page behind the tunnel — the same stack, moved |
| the idiom | the two above, and one each for one boundary: the service that runs the tasks (Amazon ECS on Amazon EC2) for the one-off and the residents, the state machine (AWS Step Functions) for the order, the schedule (Amazon EventBridge Scheduler) for the when, object storage (Amazon S3) for the copy after the run, log streams and metrics (Amazon CloudWatch) for a task's output and its samples | every stage, every store, every descriptor, every address |
| the image carries the code | the image registry (Amazon ECR) for the image; the mount narrows to the `store_*` roots | the same |

Beyond the idiom the mapping names three seats that stand only when their
condition holds, never for the demonstration: the strategy host (Amazon EC2)
with its brokerage secret (AWS Secrets Manager), which stand with
`module_trading/`; a static front (Amazon S3 with Amazon CloudFront), which
stands with a reader outside the host; a managed database (Amazon RDS), which
stands past the promotion threshold of § The databases. Nine forms are refused
in § Rejected forms. So the idiom adds five services to the lift's two, and the
phase in which the image carries the code one more — each for one boundary,
and no service the table cannot point at; the lift alone runs the whole chain
with none of the six.

## Seat by seat: what could be less, and whether it is

| seat | could be less | is it, and why | where the tree says so |
|---|---|---|---|
| the instance and the volume | nothing — a host with a disk is the floor of the lift | no: the `store_*` roots need a disk that outlives a container, and the database file needs a block device for its whole-file lock | § Rejected forms, the shared network filesystem row; `module_data/skills/skill_candle_canonicalisation.md` § 15 |
| the whole idiom | the lift, kept for good: `docker compose` and a hand on the instance run the chain end to end with two services | no: the lift names no boundary in the provider's own words — a compose service is not a task definition until something reads it as one; the idiom is described so that the move stays a rename, the ladder says a phase skipped is a redesign, and nothing is built for it | § The retrain runtime is a ladder; § Infrastructure seats |
| the image registry | none until the image carries the code — the host builds the image itself, as a bare clone does here | no: once the image carries the code the service that runs the tasks pulls it by address; one image for every role is one address, and the registry is the one place the role-deciding command and `ASSET` are not | § Infrastructure seats, the question *where does the image live?*; `module_skills/skill_asset_containers.md` § The topology |
| the state machine | a shell script calling the service's task API in the Makefile's order — the order already exists | no: a script would hold the order a second time in words the provider does not read; the state machine is the provider's form of the visible list in `all:` and `ml-all:` — the order moves as a rename, a second asset is one more iteration of the Map, and the Makefile stays the developer interface | § The Makefile is the developer interface; § Infrastructure seats; § Rejected forms, the batch service row |
| the schedule | a cron line on the instance, one line past the lift's hand | no: a cron line is a scheduler inside the compute host, the form the register refuses and the *inside none* of the contract; in the idiom the machine is started by something above it, and a one-rule schedule that starts one execution per `download_cadence_minutes` is that something with nothing else in it — the day closes on a clock | § One day, told forward, *The day closes* and *The schedule*; `module_skills/glossary.md` § Pre-AWS direction; `AGENTS.md` § Pre-AWS architectural direction, *The Makefile is the local developer interface* |
| the copy after the run | no copy: the volume alone, its durability the provider's copies of the disk | no, on one reason: a copy of the disk versions the disk, not the asset — the raw day object written once and never restated, the asset folder under its execution name, the run record under its id are objects, and only object storage gives them a key a reader off the host can read; the copy is one orchestration state and no stage's write; but its one reader, the strategy host, is absent here — see below | § The volume is the home, the store is the copy; § Correlatable artifacts, without a version scheme |
| the copy's four prefixes | one prefix, the whole working tree copied as it is | no: the four prefixes are the three `store_*` roots and the two snapshots the tree already keeps apart — raw, artifacts, runs, status — copied whole with their keys the descriptors' own paths; one prefix would blur the one family written once and never keyed by a run, the raw tree, with the two keyed by the run and the one, `status/`, rewritten by it | § The asset folder is a prefix, read forward |
| log streams and metrics | stdout left in the instance's own log, read through the tunnel; no metrics at all | half: a task that exits leaves no terminal, so the streams are where a container's output goes when nobody is watching, keyed as the recorder keys its files today; the metrics the row names beside them are the recorder's 1 s samples read forward, and they are the half of this seat that § Non-goals, and the one rule behind them, *no full observability platform*, would let go first — no alarm, no history past the run record's own | § The mapping table, the logs row; `module_skills/glossary.md` § Run record |
| the resident asset service | none elsewhere — the task run per asset needs no resident, the panel already reads the Engine for every container, and the dashboard already serves the two snapshots the `data` and `artifacts` blocks are read from | **yes, it could**: `/status` is the asset reporting itself, the contract of `module_skills/skill_asset_containers.md` § The endpoint contract, seated by the compose services row; elsewhere the resident computes nothing, so its footprint is an idle server's, and the reason the skill gives it — the tab measuring the container doing the work — does not travel; what travels is the `data` and `artifacts` blocks, which the dashboard could serve from the snapshots it already reads | § The resident container is a local mechanism; § The mapping table, the compose services row; `module_skills/skill_asset_containers.md` § The topology |
| the DevOps panel beside the provider's console | the console alone — it lists the same containers | no: the panel is a rename of a container that exists, holds the one socket under the guard the repository already wrote, and shows the asset's `data` and `artifacts` blocks the console cannot; the console is named as its equivalent, not replaced, and nothing is built for either | `module_monitoring/skills/skill_devops_panel.md` § The one socket, and what containment means, and its seat paragraph |
| the tunnel | an open port on the instance | no: a port is a security layer to describe and a reader to refuse; loopback is the page's one address here, the tunnel a remote reader's reach to it and a port-forward the same reach elsewhere, and it keeps the front absent until a reader outside the host exists | `README.md` § Quickstart; § Rejected forms, the managed web service row |
| the strategy host and its secret | nothing — they are absent | no: they enter with `module_trading/`, its own container beside `module_ml`, and the secret enters with the first credential; neither has a local counterpart, and the mapping says so rather than pretending a seat | § Module boundaries are extraction boundaries; `AGENTS.md` § Skills absent here, described |
| the managed database | nothing — it is a threshold | no: one file under one lock serves one writer and no query across assets; a database process before its threshold is § The chief antipattern in its purest form | § The databases |
| the description itself | a shorter skill, no rationale tables, and a table of absent skills that holds only the owner and the condition | **in one column, yes**: the description is the deliverable of a repository that builds nothing for the cloud, and each rationale row is one object's argument for its row; but the eleven rows of `AGENTS.md` § Skills absent here, described are the one description that says a thing twice — each *governs* cell says in one line what its last column's section says at length — and what the table alone holds is the owner and the condition, the shorter form a sceptic would keep; it stays as it is because a row read in the contract must say what the skill would govern without opening the skill | `AGENTS.md` § Skills absent here, described; each `README_module_<name>.md` § Design rationale |

## What a stranger would still ask, and the answer

Two seats stand on something other than a boundary the demonstration runs, and
the report names them so nobody mistakes them for what elsewhere needs: the
resident carries a local mechanism forward; the copy describes one that has no
local form.

- The resident asset service exists elsewhere for `/status` alone; every stage
  runs as a task, and the one line of `dockerfanout` is
  the one edit the mapping table names. If the panel ever took the asset's
  `data` and `artifacts` blocks from the snapshots the dashboard serves and its
  footprint from the Engine it already reads, the resident is the first seat to
  go, and no stage notices.
- The copy after the run has one reader, the strategy host, which reads an
  artifact by its execution name, and it is absent here. The copy stands because
  it is the cheapest form in which the raw tree is written once and the
  artifacts are versioned by the name the run already has. It is the one seat of
  the idiom whose condition the demonstration never meets, and § The retrain
  runtime is a ladder seats it at the idiom all the same: the one row of the
  count this report cannot call the cheapest that keeps its boundary.

Everything else names exactly one boundary, costs one service, and moves as a
rename or one edit; the forms that would have added a layer without a boundary
— a cluster, a queue, a host the provider holds, a task without a host, a
public front, a function on an event — are refused where they are named.

## Verdict

The mapping is minimal against its own rule and, at three cells, less than it:
one service per boundary at the idiom, two at the lift, nothing built for any
of them, and every refused form refused where its reason stands. Three cells
find less — the resident's footprint elsewhere, the metrics half of the log
row, and the *governs* column of the absent skills — and one seat, the copy
after the run, is kept for a reader that is absent here. All four are named in
the skill as what they are; that each stands on one reason and would go with
it is this report's finding, not the skill's.

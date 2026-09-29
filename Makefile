# the host side of the dashboard's mapping, measured at invocation: the port the dashboard already publishes,
# else the first free port from 8900 upward — another project on this host, or a checkout of LIORA run under
# COMPOSE_PROJECT_NAME=, may hold 8900
PORT ?= $(shell p=$$(docker compose port dashboard 8900 2>/dev/null | cut -d: -f2); \
                if [ -z "$$p" ]; then p=8900; while python3 -c "import socket, sys; sys.exit(0 if socket.socket().connect_ex(('127.0.0.1', $$p)) == 0 else 1)"; do p=$$((p+1)); done; fi; \
                echo $$p)
# measured once per make: the mapping and the page ask one port
PORT := $(PORT)
COMPOSE_ENV := UID=$(shell id -u) GID=$(shell id -g) PORT=$(PORT)
COMPOSE     := $(COMPOSE_ENV) docker compose
# the five stores of this checkout, one folder each under store/, one variable per store — the store contract every
# config.py reads; facts, not settings: docker-compose.yml mounts ./store/<content> at /store/<content>, the same
# <content> on both sides, record.py lists the four pipeline stores among them by these host paths, and every container
# sees /store/<content> in its own environment
export STORE_RAW_1M_DIR := $(CURDIR)/store/raw_1m
export STORE_ASSETS_ARTIFACTS_DIR := $(CURDIR)/store/assets_artifacts
export STORE_TRIALS_DIR := $(CURDIR)/store/trials
export STORE_RUN_RECORDS_DIR := $(CURDIR)/store/run_records
export STORE_STATUS_DIR := $(CURDIR)/store/status
STORES := store/raw_1m store/assets_artifacts store/trials store/run_records store/status
# the basket — the one definition. ASSET=<TICKER> on the make line narrows every per-asset stage to one asset; make
# exports ASSET into every recipe's environment, which is harmless: no service reads it, and a runner is told its assets
# by --tickers
TICKERS     := BTC
TICKER_LIST := $(if $(ASSET),$(ASSET),$(TICKERS))
# the basket as one argument — --tickers takes a comma-separated value, printf/xargs take one ticker per line. It goes to
# the basket-wide stages, which ASSET never narrows: a snapshot of one asset would silently drop the rest of the basket
# from the page, and the download is one process per venue for the whole basket
TICKERS_CSV := $(shell echo $(TICKERS) | tr ' ' ,)
# the fan-out's width — how many assets one stage runs at once, one process per asset with its threads pinned to 1: one
# unless the make line says otherwise, `JOBS=n`
JOBS ?= 1
# the stages of each module's chain, in the order the data moves through them — the one definition data-all,
# features-all, ml-all and all-record read
DATA_STAGES     := data-download data-ingest data-status
FEATURES_STAGES := features-bars features-catalogue features-status
ML_STAGES       := ml-labels ml-hpo ml-train ml-strategy ml-status
# the proposal a promotion copies, by its rank in the serpentine search result
PROPOSAL ?= 1
# the tmux session the detached serpentine search runs in: one per asset, named for its target
SERPENTINE_SEARCH_SESSION = features-serpentine-search-$(shell echo $(ASSET) | tr A-Z a-z)
RUN_ID = $(shell date -u +%Y%m%dT%H%M%SZ)_$(shell git rev-parse --short HEAD)
# a stage runs in a one-off container of its module's runner service — a role, not an image; nothing resident is assumed
# for compute. `env $(COMPOSE_ENV) docker compose`, because $(COMPOSE) cannot cross xargs
run    = env $(COMPOSE_ENV) docker compose run --rm -T
# $(1) runner service, $(2) python module, $(3) width: the same stage for every ticker of the list, one one-off container each
fanout = printf '%s\n' $(TICKER_LIST) | xargs -P $(3) -I{} $(run) $(1) python -m $(2) --tickers {}
# $(1) runner service, $(2) python module: a basket-wide stage, once, the whole basket
basket = $(run) $(1) python -m $(2) --tickers $(TICKERS_CSV)

.DEFAULT_GOAL := help
# the stages run in the order the chain names them, whatever -j or MAKEFLAGS say: the one parallelism is JOBS, the assets
# of one stage side by side
.NOTPARALLEL:

# every target that carries a `##`, with its one-line purpose; it carries none itself, and neither does a module's
# terminal: an interface is not an option of the menu it opens
help:
	@grep -E '^[a-zA-Z][a-zA-Z0-9_-]*:[^#]*##' $(MAKEFILE_LIST) | sed -E 's/:[^#]*## / — /'

all:             ## the whole chain from a fresh clone: the image, raw data, canonical, features, ML, snapshots
	$(MAKE) build data-all features-all ml-all
build: | $(STORES) ## the image every service runs
	$(COMPOSE) build

# a bind-mounted store must exist before compose mounts it: Docker would create a missing source directory as root, and the
# ${UID}:${GID} container could not write it — order-only, so a store's contents never make a target stale; every new
# compose target joins the line below
$(STORES):
	@mkdir -p $@
$(DATA_STAGES) $(FEATURES_STAGES) $(ML_STAGES) features-serpentine-turn ml-score features-serpentine-search features-serpentine-search-promote on all-record: | $(STORES)

data-download:   ## raw 1m candles of both venues into store/raw_1m — one process per venue, a venue's rate limit being per process
	$(call basket,data,module_data.download_binance)
	$(call basket,data,module_data.download_bybit)
data-ingest:     ## ZIPs -> the two venue families and the canonical family, each asset's partition of each, one asset at a time
	$(call fanout,data,module_data.ingest,1)
data-status:     ## data_status.json -> store/status
	$(call basket,data,module_data.status)
data-all:        ## the data chain in order
	$(MAKE) $(DATA_STAGES)
# a module's own terminal, on the host: python3 and gum, no runner and no dependency — it computes nothing, shows what
# that module's stores hold and starts one of this Makefile's targets, the ones its name gives the module. It gates
# nothing and no target of the chain depends on it; it does not resume, so it has no tmux twin; run it in a terminal
data-terminal:
	python3 -B -m module_data.sub_module_terminal.terminal --tickers $(if $(ASSET),$(ASSET),$(TICKERS_CSV))

features-bars:   ## canonical 1m -> the bars family, one partition per asset and timeframe of the register
	$(call fanout,features,module_features.bars,$(JOBS))
features-catalogue: ## every catalogued column on the decision grid — the catalogue family, one partition per asset and timeframe — and <TICKER>_catalogue.json, the contract the ML layer reads
	$(call fanout,features,module_features.catalogue,$(JOBS))
features-status: ## features_status.json -> store/status: the catalogue's facts, each asset's row counts and its serpentine search
	$(call basket,features,module_features.status)
features-all:    ## the feature chain in order
	$(MAKE) $(FEATURES_STAGES)
features-terminal:
	python3 -B -m module_features.sub_module_terminal.terminal --tickers $(if $(ASSET),$(ASSET),$(TICKERS_CSV))

ml-labels:       ## triple-barrier labels on the canonical 1m path
	$(call fanout,ml,module_ml.labels,$(JOBS))
ml-hpo:          ## Optuna TPE per asset (one process per asset, nthread=1)
	$(call fanout,ml,module_ml.hpo,$(JOBS))
ml-train:        ## out-of-fold predictions + final-holdout report per asset
	$(call fanout,ml,module_ml.train,$(JOBS))
ml-strategy:     ## entry edge threshold on the validation folds, final-holdout PnL
	$(call fanout,ml,module_ml.strategy,$(JOBS))
ml-status:       ## ml_status.json -> store/status, and <TICKER>_README.md
	$(call basket,ml,module_ml.status)
ml-all:          ## the ML chain in order
	$(MAKE) $(ML_STAGES)
ml-terminal:
	python3 -B -m module_ml.sub_module_terminal.terminal --tickers $(if $(ASSET),$(ASSET),$(TICKERS_CSV))

# the serpentine search, a hand's research outside the chain: its two steps, one turn of the feature layer's search and
# the ML layer's scoring of the question the turn left, each a stage of its own module
features-serpentine-turn: ## one turn of the serpentine search per asset: carry it as far as the answers on disk allow, then leave the next question or a finished search
	$(call fanout,features,module_features.sub_module_serpentine_search.serpentine_search,$(JOBS))
ml-score:        ## score the states of <TICKER>_score_request.json -> <TICKER>_score_response.json, one process per asset
	$(call fanout,ml,module_ml.score,$(JOBS))
# the loop over them, per asset: a turn, then — while the turn has left a question — ml-score and a turn again, each step
# a one-off container of its module's runner; the question is the one file the loop tests. Never inside all or all-record
features-serpentine-search: ## the serpentine search per asset: a turn, then ml-score and a turn while the turn leaves a question; resumes where the files stand
	printf '%s\n' $(TICKER_LIST) | xargs -P $(JOBS) -I{} sh -c '$(run) features python -m module_features.sub_module_serpentine_search.serpentine_search --tickers {} && while [ -e "$(STORE_ASSETS_ARTIFACTS_DIR)/ticker={}/{}_score_request.json" ]; do $(run) ml python -m module_ml.score --tickers {} && $(run) features python -m module_features.sub_module_serpentine_search.serpentine_search --tickers {} || exit $$?; done'
# the detached twin: the same search in a tmux session that outlives the terminal, started in this checkout, one asset per
# session; the session ends with the search — `<TICKER>_serpentine_search.json` and the page are the record.
# A plain make, not $(MAKE): the session is a new process of the tmux server, and a recipe line carrying $(MAKE) runs
# even under -n
tmux-features-serpentine-search: ## the serpentine search of one asset detached in tmux session features-serpentine-search-<ticker>, alive after the terminal closes and gone with the search; tmux attach -t features-serpentine-search-<ticker> to watch, Ctrl-C stops, a rerun resumes; ASSET= is required
	$(if $(ASSET),,$(error ASSET=<TICKER> is required))
	@tmux has-session -t $(SERPENTINE_SEARCH_SESSION) 2>/dev/null && echo '$(SERPENTINE_SEARCH_SESSION) is already running — tmux attach -t $(SERPENTINE_SEARCH_SESSION)' || tmux new-session -d -s $(SERPENTINE_SEARCH_SESSION) -c $(CURDIR) 'make features-serpentine-search ASSET=$(ASSET)'
# a hand's decision for one asset, never fanned out: the proposal's columns and barrier geometry become the asset's own,
# and its ML chain runs again, tuning it anew — the search's evaluated point is not what is kept. ASSET= is required
features-serpentine-search-promote: ## copy proposal PROPOSAL=<n> (default 1) of one asset's serpentine search into <TICKER>_feature_set.json and <TICKER>_barriers.json, then rerun its ML chain, which tunes it again; ASSET= is required
	$(if $(ASSET),,$(error ASSET=<TICKER> is required))
	$(run) features python -m module_features.sub_module_serpentine_search.promote --tickers $(ASSET) --proposal $(PROPOSAL)
	$(MAKE) ml-all ASSET=$(ASSET)
# a new experiment for one asset: every file the turn or ml-score writes for it is removed, on the host, over the stores'
# host paths — the state, the loop's ledger, the question, the answer and the asset's partition of score_trials; its
# inputs, the chain's files, the promoted state, hpo_trials and the profile stay. It runs no stage. ASSET= is required
features-serpentine-search-reset: ## remove one asset's serpentine search — its state, ledger, question, answer and score_trials partition — keeping its inputs and its profile; ASSET= is required
	$(if $(ASSET),,$(error ASSET=<TICKER> is required))
	rm -f $(STORE_ASSETS_ARTIFACTS_DIR)/ticker=$(ASSET)/$(ASSET)_serpentine_search.json $(STORE_ASSETS_ARTIFACTS_DIR)/ticker=$(ASSET)/$(ASSET)_serpentine_search_trials.jsonl $(STORE_ASSETS_ARTIFACTS_DIR)/ticker=$(ASSET)/$(ASSET)_score_request.json $(STORE_ASSETS_ARTIFACTS_DIR)/ticker=$(ASSET)/$(ASSET)_score_response.json
	rm -rf $(STORE_TRIALS_DIR)/score_trials/ticker=$(ASSET)

# the canon, on the host: python3 and the standard library alone, no runner and no dependency — the sheet rendered into
# every Skill and the glossary, the CONFIGURABLES records tabled, and the controlled files read against their Skills; it
# gates nothing, and no target of the chain depends on it
skills-sync:     ## render every Skill and module_skills/glossary.md from module_skills/skills_sheet.xlsx
	python3 -B -m module_skills.sync
skills-configurables: ## the table of every CONFIGURABLES record in the controlled config.py files, on stdout
	python3 -B -m module_skills.configurables
skills-crawl: skills-sync ## after the sync, read every controlled file of the files matrix against the Skills marked for it with the active vendor — up to 30 min per file; Ctrl-C ends it, the reports already written stay
	python3 -B -m module_skills.sub_module_scalability_crawler.crawl
skills-terminal:
	python3 -B -m module_skills.sub_module_terminal.terminal

# the presentation switch — the one switch pair the target grammar admits (AGENTS.md § Canonical vocabulary): two words to
# type in front of an audience; the rest is a click in the page
on: build        ## the presentation switch: the dashboard up, the page's address printed and opened
	$(COMPOSE) up -d dashboard
	@python3 -c "import webbrowser; url = 'http://127.0.0.1:$(PORT)/'; print('dashboard at', url); webbrowser.open(url)"
off:             ## the presentation switch: stop and remove every container of this project
	$(COMPOSE) down
monitoring-terminal:
	python3 -B -m module_monitoring.sub_module_terminal.terminal
btc-all: all     ## the single-asset chain by its ticker name; the alias goes when the basket grows
# the stages of all, one make target each, measured from outside by record.py: the four pipeline stores before and after
RECORDED_STAGES := $(DATA_STAGES) $(FEATURES_STAGES) $(ML_STAGES)
all-record: build ## one recorded run of the whole chain, every stage measured from outside by record.py -> store/run_records/<run_id>/<stage>.json
	@run_id=$(RUN_ID); for stage in $(RECORDED_STAGES); do RUN_ID=$$run_id python3 record.py $$stage $(MAKE) $$stage || exit $$?; done
btc-lifecycle: all-record ## the recorded lifecycle by its ticker name; the alias goes when the basket grows

# the host side of the dashboard's mapping, measured at invocation: the port the dashboard already publishes,
# else the first free port from 8900 upward — another project on this host, or a checkout of LIORA run under
# COMPOSE_PROJECT_NAME=, may hold 8900
PORT ?= $(shell p=$$(docker compose port dashboard 8900 2>/dev/null | cut -d: -f2); \
                if [ -z "$$p" ]; then p=8900; while ss -Hltn "sport = :$$p" | grep -q .; do p=$$((p+1)); done; fi; \
                echo $$p)
# measured once per make: the mapping and the page ask one port
PORT := $(PORT)
# the docker group of this host, so the one container that holds the socket can read it without being root
DOCKER_GID  := $(shell getent group docker | cut -d: -f3)
COMPOSE_ENV := UID=$(shell id -u) GID=$(shell id -g) PORT=$(PORT) DOCKER_GID=$(DOCKER_GID)
COMPOSE     := $(COMPOSE_ENV) docker compose
# the four stores of this checkout, one variable per store — the store contract every config.py reads; facts, not settings:
# docker-compose.yml mounts ./store_<content> by the same names, record.py lists them by these host paths, and every
# container sees /store/<content> in its own environment
export STORE_RAW_1M_DIR := $(CURDIR)/store_raw_1m
export STORE_ASSETS_ARTIFACTS_DIR := $(CURDIR)/store_assets_artifacts
export STORE_RUN_RECORDS_DIR := $(CURDIR)/store_run_records
export STORE_STATUS_DIR := $(CURDIR)/store_status
STORES := store_raw_1m store_assets_artifacts store_run_records store_status
# the basket — the one definition; the asset-<ticker> residents of docker-compose.yml follow it, one block per ticker.
# ASSET=<TICKER> on the make line narrows every per-asset stage to one asset; make exports ASSET into every recipe's
# environment, which is harmless: the residents carry their own ASSET and a runner is told its assets by --tickers
TICKERS     := BTC
TICKER_LIST := $(if $(ASSET),$(ASSET),$(TICKERS))
# the basket as one argument — --tickers takes a comma-separated value, printf/xargs take one ticker per line. It goes to
# the basket-wide stages, which ASSET never narrows: a snapshot of one asset would silently drop the rest of the basket
# from the page, and the download is one process per venue for the whole basket
TICKERS_CSV := $(shell echo $(TICKERS) | tr ' ' ,)
ASSET_SERVICE_LIST := $(addprefix asset-,$(shell echo $(TICKER_LIST) | tr A-Z a-z))
# one process per asset with its threads pinned to 1; the width is min(cores, available GiB), at least 1
JOBS ?= $(shell c=$$(nproc 2>/dev/null || echo 1); \
                g=$$(awk '/MemAvailable/ {printf "%d", $$2 / 1048576}' /proc/meminfo 2>/dev/null); \
                if [ -n "$$g" ] && [ "$$g" -lt "$$c" ]; then c=$$g; fi; \
                if [ "$$c" -lt 1 ]; then echo 1; else echo $$c; fi)
# the proposal a promotion copies, by its rank in the feature-set search result
PROPOSAL ?= 1
# the tmux session the detached feature-set search runs in: one per asset, named for it
FEATURE_SET_SEARCH_SESSION = feature-set-$(shell echo $(ASSET) | tr A-Z a-z)
RUN_ID = $(shell date -u +%Y%m%dT%H%M%SZ)_$(shell git rev-parse --short HEAD)
# a stage runs in a one-off container of its module's runner service — a role, not an image; nothing resident is assumed
# for compute. `env $(COMPOSE_ENV) docker compose`, because $(COMPOSE) cannot cross xargs
run    = env $(COMPOSE_ENV) docker compose run --rm -T
# $(1) runner service, $(2) python module, $(3) width: the same stage for every ticker of the list, one one-off container each
fanout = printf '%s\n' $(TICKER_LIST) | xargs -P $(3) -I{} $(run) $(1) python -m $(2) --tickers {}
# $(1) runner service, $(2) python module: a basket-wide stage, once, the whole basket
basket = $(run) $(1) python -m $(2) --tickers $(TICKERS_CSV)

.DEFAULT_GOAL := help

help:            ## list targets
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
data-download data-ingest data-status features-bars features-catalogue features-status ml-labels ml-hpo ml-train ml-strategy ml-status ml-feature-set-search ml-feature-set-promote on all-record: | $(STORES)

data-download:   ## raw 1m candles of both venues into store_raw_1m — one process per venue, a venue's rate limit being per process
	$(call basket,data,module_data.download_binance)
	$(call basket,data,module_data.download_bybit)
data-ingest:     ## ZIPs -> one canonical series per asset, one asset at a time
	$(call fanout,data,module_data.ingest,1)
data-status:     ## data_status.json -> store_status
	$(call basket,data,module_data.status)
data-all:        ## the data chain in order
	$(MAKE) data-download data-ingest data-status

features-bars:   ## canonical 1m -> every timeframe of the register, in each asset's own database
	$(call fanout,features,module_features.bars,$(JOBS))
features-catalogue: ## every catalogued column on the decision grid, one parquet per timeframe per asset, and <TICKER>_catalogue.json — the contract the ML layer reads
	$(call fanout,features,module_features.catalogue,$(JOBS))
features-status: ## features_status.json -> store_status: the catalogue's facts and each asset's row counts
	$(call basket,features,module_features.status)
features-all:    ## the feature chain in order
	$(MAKE) features-bars features-catalogue features-status

ml-labels:       ## triple-barrier labels on the canonical 1m path
	$(call fanout,ml,module_ml.labels,$(JOBS))
ml-hpo:          ## Optuna TPE per asset (one process per asset, nthread=1)
	$(call fanout,ml,module_ml.hpo,$(JOBS))
ml-train:        ## out-of-fold predictions + final-holdout report per asset
	$(call fanout,ml,module_ml.train,$(JOBS))
ml-strategy:     ## entry edge threshold on the validation folds, final-holdout PnL
	$(call fanout,ml,module_ml.strategy,$(JOBS))
ml-status:       ## ml_status.json -> store_status, and <TICKER>_README.md
	$(call basket,ml,module_ml.status)
ml-all:          ## the ML chain in order
	$(MAKE) ml-labels ml-hpo ml-train ml-strategy ml-status
ml-feature-set-search: ## stepwise feature-set search on the validation folds under the asset's frozen parameters; resumes; promotes nothing
	$(call fanout,ml,module_ml.feature_set_search,$(JOBS))
# a hand's decision for one asset, never fanned out: ASSET= is required
ml-feature-set-promote: ## copy proposal PROPOSAL=<n> (default 1) of one asset into <TICKER>_feature_set.json, then rerun its ML chain either way; ASSET= is required
	$(if $(ASSET),,$(error ASSET=<TICKER> is required))
	$(run) ml python -m module_ml.feature_set_promote --tickers $(ASSET) --proposal $(PROPOSAL)
	$(MAKE) ml-all ASSET=$(ASSET)
# the detached twin: the same search in a tmux session that outlives the terminal, started in this checkout, one asset per
# session; the session ends with the search — the ledger and the page are the record. A plain make, not $(MAKE): the
# session is a new process of the tmux server, and a recipe line carrying $(MAKE) runs even under -n
tmux-ml-feature-set-search: ## the search detached in tmux session feature-set-<ticker>, alive after the terminal closes and gone with the search; tmux attach -t feature-set-<ticker> to watch, Ctrl-C stops, a rerun resumes; ASSET= is required
	$(if $(ASSET),,$(error ASSET=<TICKER> is required))
	tmux new-session -d -s $(FEATURE_SET_SEARCH_SESSION) -c $(CURDIR) 'make ml-feature-set-search ASSET=$(ASSET)'

# the presentation switch — the one alias pair the target grammar admits (AGENTS.md § Canonical vocabulary): two words to
# type in front of an audience; the rest is a click in the page
on: build        ## the presentation switch: the dashboard, the DevOps panel and the asset residents up, the page's address printed and opened
	$(COMPOSE) up -d dashboard devops $(ASSET_SERVICE_LIST)
	@python3 -c "import webbrowser; url = 'http://127.0.0.1:$(PORT)/'; print('dashboard at', url); webbrowser.open(url)"
off:             ## the presentation switch: stop and remove every container of this project
	$(COMPOSE) down
btc-all: all     ## the single-asset chain by its ticker name; the alias goes when the basket grows
# the stages of all, one make target each, measured from outside by record.py: the four stores before and after
RECORDED_STAGES := data-download data-ingest data-status features-bars features-catalogue features-status ml-labels ml-hpo ml-train ml-strategy ml-status
all-record: build ## one recorded run of the whole chain, every stage measured from outside by record.py -> store_run_records/<run_id>/<stage>.json
	@run_id=$(RUN_ID); for stage in $(RECORDED_STAGES); do RUN_ID=$$run_id python3 record.py $$stage $(MAKE) $$stage || exit $$?; done
btc-lifecycle: all-record ## the recorded lifecycle by its ticker name; the alias goes when the basket grows

# python3, standard library only: runs on a fresh clone that has never built an image. Refreshed by hand — nothing
# refreshes it for you.
monitoring-dx-update: ## redraw the developer-experience drawing of the tracked tree
	python3 -m module_monitoring.sub_module_dx.visualise

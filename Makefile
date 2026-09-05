PY          := .venv/bin/python
# the host side of the dashboard's mapping, measured at invocation: the port the dashboard already publishes,
# else the first free port from 8900 upward — another checkout of LIORA on this host may hold 8900
PORT ?= $(shell p=$$(docker compose port dashboard 8900 2>/dev/null | cut -d: -f2); \
                if [ -z "$$p" ]; then p=8900; while ss -Hltn "sport = :$$p" | grep -q .; do p=$$((p+1)); done; fi; \
                echo $$p)
# measured once per make: the mapping, the page and the finalise line ask one port
PORT := $(PORT)
# the docker group of this host, so the one container that holds the socket can read it without being root
DOCKER_GID  := $(shell getent group docker | cut -d: -f3)
COMPOSE_ENV := UID=$(shell id -u) GID=$(shell id -g) PORT=$(PORT) DOCKER_GID=$(DOCKER_GID)
COMPOSE     := $(COMPOSE_ENV) docker compose
# the basket, or the one asset ASSET=<TICKER> names on the make line — the contract's own spelling of the namespace
# parameter; make exports it into every recipe's environment, which is harmless: RECORD is empty on host recipes and
# the docker twins run inside containers that carry their own ASSET
TICKER_LIST := $(if $(ASSET),$(ASSET),$(shell python3 -c "from module_data.config import TICKERS; print(' '.join(TICKERS))"))
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
# a run wraps every stage command with the recorder; empty by default, so the recipes are unchanged
RECORD ?=
RUN_ID = $(shell date -u +%Y%m%dT%H%M%SZ)_$(shell git rev-parse --short HEAD)
# $(1) = python command, $(2) = module
fanout = printf '%s\n' $(TICKER_LIST) | OMP_NUM_THREADS=1 xargs -P $(JOBS) -I{} $(1) -m $(2) --tickers {}
# $(1) = module, $(2) = width: each asset's stage runs inside its own resident container, which carries ASSET — the one line that assumes a resident; the quoted command is the whole one-off form
dockerfanout = $(COMPOSE) up -d $(ASSET_SERVICE_LIST) && printf '%s\n' $(ASSET_SERVICE_LIST) | xargs -P $(2) -I{} env $(COMPOSE_ENV) docker compose exec -T {} sh -c '$(RECORD) python -m $(1) --tickers $$ASSET'

.DEFAULT_GOAL := help

help:            ## list targets
	@grep -E '^[a-zA-Z][a-zA-Z0-9_-]*:[^#]*##' $(MAKEFILE_LIST) | sed -E 's/:[^#]*## / — /'

all:             ## full pipeline from a fresh clone: venv, data, canonical, features, ML, snapshots
	$(MAKE) setup data-download data-ingest data-status features-all ml-all

setup:           ## create .venv and install the pinned direct dependencies
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

data-download:   ## fetch Binance + Bybit 1m klines (UTC calendar-day files, idempotent)
	$(PY) -m module_data.download_binance
	$(PY) -m module_data.download_bybit
data-ingest:     ## load both ZIP trees into each asset's <TICKER>_research_ohlcv.duckdb and rebuild its canonical series, one asset at a time
	$(PY) -m module_data.ingest
data-status:     ## data & database monitoring -> stdout + module_monitoring/data_status.json
	$(PY) -m module_data.status

features-bars:   ## canonical 1m -> every timeframe of the register, in each asset's own database
	$(call fanout,$(PY),module_features.bars)
features-catalogue: ## every catalogued column on the decision grid, one parquet per timeframe per asset
	$(call fanout,$(PY),module_features.catalogue)
features-all:    ## the feature chain in order
	$(MAKE) features-bars features-catalogue

ml-labels:       ## triple-barrier labels on the canonical 1m path
	$(call fanout,$(PY),module_ml.labels)
ml-hpo:          ## Optuna TPE per asset (one process per asset, nthread=1)
	$(call fanout,$(PY),module_ml.hpo)
ml-train:        ## out-of-fold predictions + final-holdout report per asset
	$(call fanout,$(PY),module_ml.train)
ml-strategy:     ## entry edge threshold on the validation folds, final-holdout PnL
	$(call fanout,$(PY),module_ml.strategy)
ml-status:       ## aggregate ML artifacts -> module_monitoring/ml_status.json + <TICKER>_README.md
	$(PY) -m module_ml.status
ml-all:          ## the ML chain in order
	$(MAKE) ml-labels ml-hpo ml-train ml-strategy ml-status
ml-feature-set-search: ## stepwise feature-set search on the validation folds under the asset's frozen parameters; resumes; promotes nothing
	$(call fanout,$(PY),module_ml.feature_set_search)
# a hand's decision for one asset, never fanned out: ASSET= is required, and an empty one fails in the parser
ml-feature-set-promote: ## copy proposal PROPOSAL=<n> (default 1) of one asset into <TICKER>_feature_set.json, then rerun its ML chain either way; ASSET= is required
	$(PY) -m module_ml.feature_set_promote --tickers $(ASSET) --proposal $(PROPOSAL)
	$(MAKE) ml-all ASSET=$(ASSET)

# python3, not $(PY): standard library only, so it runs on a fresh clone that has
# never seen `make setup`. Refreshed by hand — nothing refreshes it for you.
monitoring-dx-update: ## redraw the developer-experience drawing of the tracked tree
	python3 -m module_monitoring.sub_module_dx.visualise

docker-build:    ## build the one image every service runs
	$(COMPOSE) build pipeline
docker-up: docker-build ## start the dashboard, the DevOps panel and the asset containers, print the page's address and open it
	$(COMPOSE) up -d dashboard devops $(ASSET_SERVICE_LIST)
	@python3 -c "import webbrowser; url = 'http://127.0.0.1:$(PORT)/'; print('dashboard at', url); webbrowser.open(url)"
docker-down:     ## stop and remove every container
	$(COMPOSE) down
# the presentation switch — the one alias pair the target grammar admits (AGENTS.md § Canonical vocabulary):
# two words to type in front of an audience; the rest is a click in the page, and the targets they name stay the convention
on: docker-up    ## the presentation switch: the same as docker-up
off: docker-down ## the presentation switch: the same as docker-down
docker-data-download: ## both download stages inside the container (basket-wide, sequential)
	$(COMPOSE) run --rm -T pipeline $(RECORD) python -m module_data.download_binance
	$(COMPOSE) run --rm -T pipeline $(RECORD) python -m module_data.download_bybit
docker-data-ingest: ## the ingest stage, one asset at a time, each inside its own container
	$(call dockerfanout,module_data.ingest,1)
docker-data-status: ## the data status stage inside the container -> module_monitoring/data_status.json
	$(COMPOSE) run --rm -T pipeline $(RECORD) python -m module_data.status

docker-features-bars: ## module_features.bars, inside each asset's container
	$(call dockerfanout,module_features.bars,$(JOBS))
docker-features-catalogue: ## module_features.catalogue, inside each asset's container
	$(call dockerfanout,module_features.catalogue,$(JOBS))
docker-features-all: ## the feature chain inside the containers
	$(MAKE) docker-features-bars docker-features-catalogue

docker-ml-labels:    ## module_ml.labels, inside each asset's container
	$(call dockerfanout,module_ml.labels,$(JOBS))
docker-ml-hpo:       ## module_ml.hpo, inside each asset's container
	$(call dockerfanout,module_ml.hpo,$(JOBS))
docker-ml-train:     ## module_ml.train, inside each asset's container
	$(call dockerfanout,module_ml.train,$(JOBS))
docker-ml-strategy:  ## module_ml.strategy, inside each asset's container
	$(call dockerfanout,module_ml.strategy,$(JOBS))
docker-ml-status:    ## module_ml.status inside the container
	$(COMPOSE) run --rm -T pipeline $(RECORD) python -m module_ml.status
docker-ml-all:       ## the ML chain inside the containers
	$(MAKE) docker-ml-labels docker-ml-hpo docker-ml-train docker-ml-strategy docker-ml-status
docker-ml-feature-set-search: ## module_ml.feature_set_search, inside each asset's container
	$(call dockerfanout,module_ml.feature_set_search,$(JOBS))
docker-ml-feature-set-promote: ## module_ml.feature_set_promote for one asset inside the container, then its ML chain inside the containers; ASSET= is required
	$(COMPOSE) run --rm -T pipeline $(RECORD) python -m module_ml.feature_set_promote --tickers $(ASSET) --proposal $(PROPOSAL)
	$(MAKE) docker-ml-all ASSET=$(ASSET)
# the detached twin: the same docker twin in a tmux session that outlives the terminal, started in this checkout,
# one asset per session; the session ends with the search — the ledger and the page are the record. A plain make,
# not $(MAKE): the session is a new process of the tmux server, and a recipe line carrying $(MAKE) runs even under -n
tmux-ml-feature-set-search: ## the search detached in tmux session feature-set-<ticker>, alive after the terminal closes and gone with the search; tmux attach -t feature-set-<ticker> to watch, Ctrl-C stops, a rerun resumes; ASSET= is required
	$(if $(ASSET),,$(error ASSET=<TICKER> is required))
	tmux new-session -d -s $(FEATURE_SET_SEARCH_SESSION) -c $(CURDIR) 'make docker-ml-feature-set-search ASSET=$(ASSET)'
docker-all:          ## the whole chain inside the containers: download -> ingest -> status -> features -> ML -> snapshots
	$(MAKE) docker-data-download docker-data-ingest docker-data-status docker-features-all docker-ml-all
docker-btc-all: docker-all ## the single-asset chain by its ticker name; the alias goes when the basket grows
docker-all-record: docker-build ## one recorded run of the whole chain, the whole basket in one record -> store_run_records/<run_id>/
	$(COMPOSE) up -d dashboard
	@run_id=$(RUN_ID); \
	 $(MAKE) docker-all RECORD="python -m module_monitoring.record $$run_id" && \
	 PORT=$(PORT) python3 -m module_monitoring.record --finalise $$run_id
docker-btc-lifecycle: docker-all-record ## the recorded lifecycle by its ticker name; the alias goes when the basket grows

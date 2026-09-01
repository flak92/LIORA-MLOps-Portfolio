PY          := .venv/bin/python
PORT        ?= 8900
# the docker group of this host, so the one container that holds the socket can read it without being root
DOCKER_GID  := $(shell getent group docker | cut -d: -f3)
COMPOSE_ENV := UID=$(shell id -u) GID=$(shell id -g) PORT=$(PORT) DOCKER_GID=$(DOCKER_GID)
COMPOSE     := $(COMPOSE_ENV) docker compose
TICKER_LIST := $(shell python3 -c "from module_data.config import TICKERS; print(' '.join(TICKERS))")
ASSET_SERVICE_LIST := $(addprefix asset-,$(shell echo $(TICKER_LIST) | tr A-Z a-z))
# one process per asset with its threads pinned to 1; the width is min(cores, available GiB), at least 1
JOBS ?= $(shell c=$$(nproc 2>/dev/null || echo 1); \
                g=$$(awk '/MemAvailable/ {printf "%d", $$2 / 1048576}' /proc/meminfo 2>/dev/null); \
                if [ -n "$$g" ] && [ "$$g" -lt "$$c" ]; then c=$$g; fi; \
                if [ "$$c" -lt 1 ]; then echo 1; else echo $$c; fi)
# a run wraps every stage command with the recorder; empty by default, so the recipes are unchanged
RECORD ?=
RUN_ID = $(shell date -u +%Y%m%dT%H%M%SZ)_$(shell git rev-parse --short HEAD)
# $(1) = python command, $(2) = module
fanout = printf '%s\n' $(TICKER_LIST) | OMP_NUM_THREADS=1 xargs -P $(JOBS) -I{} $(1) -m $(2) --tickers {}
# $(1) = module, $(2) = width: each asset's stage runs inside its own resident container, which carries ASSET
dockerfanout = $(COMPOSE) up -d $(ASSET_SERVICE_LIST) && printf '%s\n' $(ASSET_SERVICE_LIST) | xargs -P $(2) -I{} env $(COMPOSE_ENV) docker compose exec -T {} sh -c '$(RECORD) python -m $(1) --tickers $$ASSET'

.DEFAULT_GOAL := help

help:            ## list targets
	@grep -E '^[a-zA-Z][a-zA-Z0-9_-]*:[^#]*##' $(MAKEFILE_LIST) | sed -E 's/:[^#]*## / — /'

all:             ## full pipeline from a fresh clone: venv, data, canonical, ML, snapshots
	$(MAKE) setup data-download data-ingest data-status ml-all

setup:           ## create .venv and install the pinned direct dependencies
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

data-download:   ## fetch Binance + Bybit 1m klines (UTC calendar-day files, idempotent)
	$(PY) -m module_data.download_binance
	$(PY) -m module_data.download_bybit
data-ingest:     ## load both ZIP trees into each asset's <TICKER>_research_ohlcv.duckdb and rebuild its canonical series, one asset at a time
	$(PY) -m module_data.ingest
data-status:     ## data & DB monitoring -> stdout + module_monitoring/data_status.json
	$(PY) -m module_data.status

ml-bars:         ## canonical 1m -> 15m/1h/4h bars, in each asset's own database
	$(call fanout,$(PY),module_ml.bars)
ml-features:     ## fixed hierarchical 15-column feature matrix per asset
	$(call fanout,$(PY),module_ml.features)
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
ml-all:          ## the whole ML chain in order
	$(MAKE) ml-bars ml-features ml-labels ml-hpo ml-train ml-strategy ml-status

# python3, not $(PY): standard library only, so it runs on a fresh clone that has
# never seen `make setup`. Refreshed by hand — nothing refreshes it for you.
monitoring-dx-update: ## redraw the developer-experience picture of the tracked tree
	python3 -m module_monitoring.sub_module_dx.visualise

docker-build:    ## build the one image every service runs
	$(COMPOSE) build pipeline
docker-up: docker-build ## start the dashboard, the DevOps panel and the asset containers at http://127.0.0.1:$(PORT)/, then open the page
	$(COMPOSE) up -d dashboard devops $(ASSET_SERVICE_LIST)
	@python3 -c "import webbrowser; webbrowser.open('http://127.0.0.1:$(PORT)/')"
docker-down:     ## stop and remove every container
	$(COMPOSE) down
docker-data-download: ## both download stages inside the container (basket-wide, sequential)
	$(COMPOSE) run --rm -T pipeline $(RECORD) python -m module_data.download_binance
	$(COMPOSE) run --rm -T pipeline $(RECORD) python -m module_data.download_bybit
docker-data-ingest: ## the ingest stage, one asset at a time, each inside its own container
	$(call dockerfanout,module_data.ingest,1)
docker-data-status: ## the data status stage inside the container -> module_monitoring/data_status.json
	$(COMPOSE) run --rm -T pipeline $(RECORD) python -m module_data.status

docker-ml-bars:      ## module_ml.bars, inside each asset's container
	$(call dockerfanout,module_ml.bars,$(JOBS))
docker-ml-features:  ## module_ml.features, inside each asset's container
	$(call dockerfanout,module_ml.features,$(JOBS))
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
docker-ml-all:       ## the whole ML chain inside the containers
	$(MAKE) docker-ml-bars docker-ml-features docker-ml-labels docker-ml-hpo docker-ml-train docker-ml-strategy docker-ml-status
docker-all:          ## the whole chain inside the containers: download -> ingest -> status -> ML -> snapshots
	$(MAKE) docker-data-download docker-data-ingest docker-data-status docker-ml-all
docker-btc-all: docker-all ## the single-asset chain by its ticker name; the alias goes when the basket grows
docker-all-record: docker-build ## one recorded run of the whole chain, the whole basket in one record -> store_run_records/<run_id>/
	$(COMPOSE) up -d dashboard
	@run_id=$(RUN_ID); \
	 $(MAKE) docker-all RECORD="python -m module_monitoring.record $$run_id" && \
	 python3 -m module_monitoring.record --finalise $$run_id
docker-btc-lifecycle: docker-all-record ## the recorded lifecycle by its ticker name; the alias goes when the basket grows

PY         := .venv/bin/python
PORT       ?= 8900
COMPOSE    := UID=$(shell id -u) GID=$(shell id -g) docker compose
TICKER_LIST = $(shell python3 -c "from module_data.config import TICKERS; print(' '.join(TICKERS))")

# ML stages are one independent process per asset. The only speed-up allowed
# here is that external parallelism: OMP_NUM_THREADS and nthread stay at 1,
# because multi-threaded float summation reorders and two runs of the same
# experiment stop being comparable. The width is measured, never hardcoded —
# max(1, min(cores, available GiB)) so a bigger machine is used, a loaded one is
# not oversubscribed, and a nearly full one still runs — `xargs -P 0` means no
# limit at all, the exact opposite of the intent. Override with `JOBS=2`.
JOBS ?= $(shell c=$$(nproc 2>/dev/null || echo 1); \
                g=$$(awk '/MemAvailable/ {printf "%d", $$2 / 1048576}' /proc/meminfo 2>/dev/null); \
                if [ -n "$$g" ] && [ "$$g" -lt "$$c" ]; then c=$$g; fi; \
                if [ "$$c" -lt 1 ]; then echo 1; else echo $$c; fi)

# $(1) = python command, $(2) = ml module
fanout = printf '%s\n' $(TICKER_LIST) | OMP_NUM_THREADS=1 xargs -P $(JOBS) -I{} $(1) -m $(2) --tickers {}

.DEFAULT_GOAL := help

# every target is a command, not a file — without this `make dashboard` would
# be "up to date" because the module_monitoring/ directory exists
.PHONY: help all setup download download-binance download-bybit ingest export status \
        dashboard ml-bars ml-features ml-labels ml-hpo ml-train \
        ml-strategy ml-status ml-all docker-build docker-download \
        docker-ingest docker-export docker-status docker-ml-bars \
        docker-ml-features docker-ml-labels docker-ml-hpo docker-ml-train \
        docker-ml-strategy docker-ml-status docker-ml-all docker-up docker-down

help:            ## list targets
	@grep -E '^[a-zA-Z][a-zA-Z0-9_-]*: *##' $(MAKEFILE_LIST) | sed 's/: *## / — /'

all:             ## full pipeline from a fresh clone: venv, data, canonical, ML, snapshots
	$(MAKE) setup download ingest export status ml-all

setup:           ## create .venv and install the pinned direct dependencies
	python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

download:        ## fetch Binance + Bybit 1m klines (UTC calendar-day files, idempotent)
	$(PY) -m module_data.download_binance
	$(PY) -m module_data.download_bybit

download-binance: ## Binance USDS-M only
	$(PY) -m module_data.download_binance

download-bybit:  ## Bybit Linear only
	$(PY) -m module_data.download_bybit

ingest:          ## load both ZIP trees into store_db/research_ohlcv.duckdb and rebuild the canonical series (basket-wide)
	$(PY) -m module_data.ingest

export:          ## write store_Assets_artifacts/<T>/<T>_canonical_ohlcv_ss-01-hh-dd-MM.parquet from the canonical series
	$(PY) -m module_data.export

status:          ## data & DB monitoring -> stdout + module_monitoring/status.json
	$(PY) -m module_data.status

dashboard:       ## serve the dashboard at http://127.0.0.1:$(PORT)/ and open it in the browser
	@(sleep 0.7 && $(PY) -c "import webbrowser; webbrowser.open('http://127.0.0.1:$(PORT)/')") >/dev/null 2>&1 &
	$(PY) -m http.server $(PORT) --bind 127.0.0.1 --directory module_monitoring

ml-bars:         ## canonical 1m -> 15m/1h/4h bars (single DB writer)
	$(PY) -m module_ml.bars

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

ml-status:       ## aggregate ML artifacts -> module_monitoring/ml_status.json
	$(PY) -m module_ml.status

ml-all:          ## the whole ML chain in order
	$(MAKE) ml-bars ml-features ml-labels ml-hpo ml-train ml-strategy ml-status

docker-build:    ## build the pipeline image
	$(COMPOSE) build

docker-download: ## run both download stages inside the container
	$(COMPOSE) run --rm pipeline python -m module_data.download_binance
	$(COMPOSE) run --rm pipeline python -m module_data.download_bybit

docker-ingest:   ## run the ingest stage inside the container
	$(COMPOSE) run --rm pipeline python -m module_data.ingest

docker-export:   ## run the export stage inside the container
	$(COMPOSE) run --rm pipeline python -m module_data.export

docker-status:   ## run the status stage inside the container
	$(COMPOSE) run --rm pipeline python -m module_data.status

docker-ml-bars:      ## module_ml.bars inside the container
	$(COMPOSE) run --rm pipeline python -m module_ml.bars

docker-ml-features:  ## module_ml.features inside the container
	$(COMPOSE) run --rm pipeline sh -c "$(call fanout,python,module_ml.features)"

docker-ml-labels:    ## module_ml.labels inside the container
	$(COMPOSE) run --rm pipeline sh -c "$(call fanout,python,module_ml.labels)"

docker-ml-hpo:       ## module_ml.hpo inside the container
	$(COMPOSE) run --rm pipeline sh -c "$(call fanout,python,module_ml.hpo)"

docker-ml-train:     ## module_ml.train inside the container
	$(COMPOSE) run --rm pipeline sh -c "$(call fanout,python,module_ml.train)"

docker-ml-strategy:  ## module_ml.strategy inside the container
	$(COMPOSE) run --rm pipeline sh -c "$(call fanout,python,module_ml.strategy)"

docker-ml-status:    ## module_ml.status inside the container
	$(COMPOSE) run --rm pipeline python -m module_ml.status

docker-ml-all:       ## the whole ML chain inside the container
	$(MAKE) docker-ml-bars docker-ml-features docker-ml-labels docker-ml-hpo \
	        docker-ml-train docker-ml-strategy docker-ml-status

docker-up:       ## start the dashboard container at http://127.0.0.1:8900/
	$(COMPOSE) up -d dashboard

docker-down:     ## stop and remove the containers
	$(COMPOSE) down

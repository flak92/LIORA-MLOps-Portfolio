PY         := .venv/bin/python
PORT       ?= 8900
COMPOSE    := UID=$(shell id -u) GID=$(shell id -g) docker compose
TICKER_LIST = $(shell python3 -c "from data_module.config import TICKERS; print(' '.join(TICKERS))")

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
# be "up to date" because the monitoring_module/ directory exists
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

setup:           ## create .venv and install the locked dependency set
	python3 -m venv .venv && .venv/bin/pip install -r requirements.lock

download:        ## fetch Binance + Bybit 1m klines (full UTC days, idempotent)
	$(PY) -m data_module.download_binance
	$(PY) -m data_module.download_bybit

download-binance: ## Binance USDS-M only
	$(PY) -m data_module.download_binance

download-bybit:  ## Bybit Linear only
	$(PY) -m data_module.download_bybit

ingest:          ## load both ZIP trees into db/1m_raw_data_db.duckdb and rebuild the canonical series
	$(PY) -m data_module.ingest

export:          ## write assets/Asset_<T>/1m_<T>_data.parquet from the canonical series
	$(PY) -m data_module.export

status:          ## data & DB monitoring -> stdout + monitoring_module/status.json
	$(PY) -m data_module.status

dashboard:       ## serve the dashboard at http://127.0.0.1:$(PORT)/ and open it in the browser
	@(sleep 0.7 && $(PY) -c "import webbrowser; webbrowser.open('http://127.0.0.1:$(PORT)/')") >/dev/null 2>&1 &
	$(PY) -m http.server $(PORT) --bind 127.0.0.1 --directory monitoring_module

ml-bars:         ## canonical 1m -> 15m/1h/4h bars (single DB writer)
	$(PY) -m ml_module.bars

ml-features:     ## fixed hierarchical 15-column feature matrix per asset
	$(call fanout,$(PY),ml_module.features)

ml-labels:       ## triple-barrier labels on the canonical 1m path + uniqueness weights
	$(call fanout,$(PY),ml_module.labels)

ml-hpo:          ## Optuna TPE per asset (one process per asset, nthread=1)
	$(call fanout,$(PY),ml_module.hpo)

ml-train:        ## OOF predictions + final-OOS report per asset
	$(call fanout,$(PY),ml_module.train)

ml-strategy:     ## tau selection on the validation folds, final-OOS PnL
	$(call fanout,$(PY),ml_module.strategy)

ml-status:       ## aggregate ML artifacts -> monitoring_module/ml_status.json
	$(PY) -m ml_module.status

ml-all:          ## the whole ML chain in order
	$(MAKE) ml-bars ml-features ml-labels ml-hpo ml-train ml-strategy ml-status

docker-build:    ## build the pipeline image
	$(COMPOSE) build

docker-download: ## run both download stages inside the container
	$(COMPOSE) run --rm pipeline python -m data_module.download_binance
	$(COMPOSE) run --rm pipeline python -m data_module.download_bybit

docker-ingest:   ## run the ingest stage inside the container
	$(COMPOSE) run --rm pipeline python -m data_module.ingest

docker-export:   ## run the export stage inside the container
	$(COMPOSE) run --rm pipeline python -m data_module.export

docker-status:   ## run the status stage inside the container
	$(COMPOSE) run --rm pipeline python -m data_module.status

docker-ml-bars:      ## ml.bars inside the container
	$(COMPOSE) run --rm pipeline python -m ml_module.bars

docker-ml-features:  ## ml.features inside the container
	$(COMPOSE) run --rm pipeline sh -c "$(call fanout,python,ml_module.features)"

docker-ml-labels:    ## ml.labels inside the container
	$(COMPOSE) run --rm pipeline sh -c "$(call fanout,python,ml_module.labels)"

docker-ml-hpo:       ## ml.hpo inside the container
	$(COMPOSE) run --rm pipeline sh -c "$(call fanout,python,ml_module.hpo)"

docker-ml-train:     ## ml.train inside the container
	$(COMPOSE) run --rm pipeline sh -c "$(call fanout,python,ml_module.train)"

docker-ml-strategy:  ## ml.strategy inside the container
	$(COMPOSE) run --rm pipeline sh -c "$(call fanout,python,ml_module.strategy)"

docker-ml-status:    ## ml.status inside the container
	$(COMPOSE) run --rm pipeline python -m ml_module.status

docker-ml-all:       ## the whole ML chain inside the container
	$(MAKE) docker-ml-bars docker-ml-features docker-ml-labels docker-ml-hpo \
	        docker-ml-train docker-ml-strategy docker-ml-status

docker-up:       ## start the dashboard container at http://127.0.0.1:8900/
	$(COMPOSE) up -d dashboard

docker-down:     ## stop and remove the containers
	$(COMPOSE) down

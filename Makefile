PY         := .venv/bin/python
PORT       ?= 8900
DUCKDB_PIN := duckdb==1.5.4
ML_PINS    := numpy==2.5.2 xgboost==3.4.1 optuna==4.9.0
COMPOSE    := UID=$(shell id -u) GID=$(shell id -g) docker compose
TICKER_LIST = $(shell python3 -c "from pipeline.config import TICKERS; print(' '.join(TICKERS))")

.DEFAULT_GOAL := help

# every target is a command, not a file — without this `make dashboard` would
# be "up to date" because the dashboard/ directory exists
.PHONY: help setup download download-binance download-bybit ingest export status \
        dashboard ml-bars ml-features ml-labels ml-hpo ml-hpo-par ml-train \
        ml-strategy ml-finalize ml-status ml-all docker-build docker-download \
        docker-ingest docker-export docker-status docker-ml-bars \
        docker-ml-features docker-ml-labels docker-ml-hpo docker-ml-train \
        docker-ml-strategy docker-ml-finalize docker-ml-status docker-up docker-down

help:            ## list targets
	@grep -E '^[a-zA-Z][a-zA-Z0-9_-]*: *##' $(MAKEFILE_LIST) | sed 's/: *## / — /'

setup:           ## create .venv and install the locked dependency set
	python3 -m venv .venv && .venv/bin/pip install -r requirements.lock

download:        ## fetch Binance + Bybit 1m klines (full UTC days, idempotent)
	$(PY) -m pipeline.download
	$(PY) -m pipeline.download_bybit

download-binance: ## Binance USDS-M only
	$(PY) -m pipeline.download

download-bybit:  ## Bybit Linear only
	$(PY) -m pipeline.download_bybit

ingest:          ## load both ZIP trees into db/1m_raw_data_db.duckdb and rebuild the canonical series
	$(PY) -m pipeline.ingest

export:          ## write assets/Asset_<T>/1m_<T>_data.parquet from the canonical series
	$(PY) -m pipeline.export

status:          ## data & DB monitoring -> stdout + dashboard/status.json
	$(PY) -m pipeline.status

dashboard:       ## serve the dashboard at http://127.0.0.1:$(PORT)/ and open it in the browser
	@(sleep 0.7 && $(PY) -c "import webbrowser; webbrowser.open('http://127.0.0.1:$(PORT)/')") >/dev/null 2>&1 &
	$(PY) -m http.server $(PORT) --bind 127.0.0.1 --directory dashboard

ml-bars:         ## canonical 1m -> 15m/1h/4h bars + research data hash (single DB writer)
	$(PY) -m ml.bars

ml-features:     ## fixed hierarchical 16-column feature matrix per asset
	OMP_NUM_THREADS=1 $(PY) -m ml.features

ml-labels:       ## triple-barrier labels on the 1m path + uniqueness weights
	OMP_NUM_THREADS=1 $(PY) -m ml.labels

ml-hpo:          ## Optuna TPE per asset (sequential)
	OMP_NUM_THREADS=1 $(PY) -m ml.hpo

ml-hpo-par:      ## Optuna HPO, 4 assets in parallel x nthread=1
	printf '%s\n' $(TICKER_LIST) | OMP_NUM_THREADS=1 xargs -P 4 -I{} $(PY) -m ml.hpo --tickers {}

ml-train:        ## OOF predictions + locked test report per asset
	OMP_NUM_THREADS=1 $(PY) -m ml.train

ml-strategy:     ## tau selection on OOF splits, locked-test PnL
	OMP_NUM_THREADS=1 $(PY) -m ml.strategy

ml-finalize:     ## deployment model fitted on the full research window
	OMP_NUM_THREADS=1 $(PY) -m ml.train --finalize

ml-status:       ## aggregate ML artifacts -> dashboard/ml_status.json
	$(PY) -m ml.status

ml-all:          ## the whole ML chain in order
	$(MAKE) ml-bars ml-features ml-labels ml-hpo ml-train ml-strategy ml-finalize ml-status

docker-build:    ## build the pipeline image
	$(COMPOSE) build

docker-download: ## run both download stages inside the container
	$(COMPOSE) run --rm pipeline python -m pipeline.download
	$(COMPOSE) run --rm pipeline python -m pipeline.download_bybit

docker-ingest:   ## run the ingest stage inside the container
	$(COMPOSE) run --rm pipeline python -m pipeline.ingest

docker-export:   ## run the export stage inside the container
	$(COMPOSE) run --rm pipeline python -m pipeline.export

docker-status:   ## run the status stage inside the container
	$(COMPOSE) run --rm pipeline python -m pipeline.status

docker-ml-bars:      ## ml.bars inside the container
	$(COMPOSE) run --rm pipeline python -m ml.bars

docker-ml-features:  ## ml.features inside the container
	$(COMPOSE) run --rm pipeline python -m ml.features

docker-ml-labels:    ## ml.labels inside the container
	$(COMPOSE) run --rm pipeline python -m ml.labels

docker-ml-hpo:       ## ml.hpo inside the container
	$(COMPOSE) run --rm pipeline python -m ml.hpo

docker-ml-train:     ## ml.train inside the container
	$(COMPOSE) run --rm pipeline python -m ml.train

docker-ml-strategy:  ## ml.strategy inside the container
	$(COMPOSE) run --rm pipeline python -m ml.strategy

docker-ml-finalize:  ## ml.train --finalize inside the container
	$(COMPOSE) run --rm pipeline python -m ml.train --finalize

docker-ml-status:    ## ml.status inside the container
	$(COMPOSE) run --rm pipeline python -m ml.status

docker-up:       ## start the dashboard container at http://127.0.0.1:8900/
	$(COMPOSE) up -d dashboard

docker-down:     ## stop and remove the containers
	$(COMPOSE) down

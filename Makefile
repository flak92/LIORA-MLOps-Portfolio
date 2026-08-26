PY         := .venv/bin/python
PORT       ?= 8900
DUCKDB_PIN := duckdb==1.5.4

.DEFAULT_GOAL := help

help:            ## list targets
	@grep -E '^[a-zA-Z][a-zA-Z0-9_-]*: *##' $(MAKEFILE_LIST) | sed 's/: *## / — /'

setup:           ## create .venv and install pinned DuckDB
	python3 -m venv .venv && .venv/bin/pip install $(DUCKDB_PIN)

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

docker-build:    ## build the pipeline image
	docker compose build

docker-download: ## run both download stages inside the container
	docker compose run --rm pipeline python -m pipeline.download
	docker compose run --rm pipeline python -m pipeline.download_bybit

docker-ingest:   ## run the ingest stage inside the container
	docker compose run --rm pipeline python -m pipeline.ingest

docker-export:   ## run the export stage inside the container
	docker compose run --rm pipeline python -m pipeline.export

docker-status:   ## run the status stage inside the container
	docker compose run --rm pipeline python -m pipeline.status

docker-up:       ## start the dashboard container at http://127.0.0.1:8900/
	docker compose up -d dashboard

docker-down:     ## stop and remove the containers
	docker compose down

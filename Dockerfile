FROM python:3.12-slim

RUN pip install --no-cache-dir duckdb==1.5.4

# code and data come from the compose bind mount (.:/app)
WORKDIR /app

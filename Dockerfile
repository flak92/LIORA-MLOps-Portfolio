FROM python:3.12-slim

RUN pip install --no-cache-dir duckdb==1.5.4 numpy==2.5.2 xgboost==3.4.1 optuna==4.9.0

# code and data come from the compose bind mount (.:/app)
WORKDIR /app

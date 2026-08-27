FROM python:3.12-slim

COPY requirements.lock .
RUN pip install --no-cache-dir -r requirements.lock

# code and data come from the compose bind mount (.:/app)
WORKDIR /app

FROM python:3.12-slim

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# code and data come from the compose bind mount (.:/app)
WORKDIR /app

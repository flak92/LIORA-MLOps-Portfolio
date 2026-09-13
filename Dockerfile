FROM python:3.12-slim

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# the code comes from the compose tree mount (.:/app), the state from the ./store/<content> mounts at /store/<content>, so the image holds the pins alone
WORKDIR /app

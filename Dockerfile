FROM python:3.12-slim

WORKDIR /app

COPY src/main.py /app/main.py
COPY src/announce.py /app/announce.py
COPY src/v11.py /app/v11.py
COPY manifest.json /app/manifest.json

RUN mkdir -p /logs

ENV PYTHONUNBUFFERED=1
# IMPORTANT: process reads from stdin (no CLI args except --version)
ENTRYPOINT ["python3", "/app/main.py"]

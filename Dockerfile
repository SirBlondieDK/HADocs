FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV HADOCS_CONFIG_FILE=/config/config.json
ENV HADOCS_OUTPUT_DIR=/output
ENV HADOCS_CACHE_DIR=/cache

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY src ./src
COPY main.py ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

RUN mkdir -p /config /output /cache

VOLUME ["/config", "/output", "/cache"]

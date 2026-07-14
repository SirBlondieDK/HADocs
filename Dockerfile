@'
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml requirements.txt ./
COPY src ./src
COPY main.py ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

RUN mkdir -p /config /output /cache

VOLUME ["/config", "/output", "/cache"]

ENTRYPOINT ["python", "-m", "src.hadocs.cli.main"]
CMD ["generate"]
'@ | Set-Content -Encoding utf8NoBOM Dockerfile
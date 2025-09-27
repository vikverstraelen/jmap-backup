FROM python:3.12-bookworm

WORKDIR /app


RUN apt-get update && apt-get install -y \
    cron \
    && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir uv
COPY src/ ./src/
COPY pyproject.toml .
COPY backup.sh .
COPY run.sh .
RUN chmod +x run.sh

RUN uv sync

CMD ["./run.sh"]
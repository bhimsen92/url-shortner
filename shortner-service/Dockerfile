# Build stage
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1
WORKDIR /app

# Install build dependencies
RUN apt-get update && \
    apt-get install -y build-essential libpq-dev --no-install-recommends && \
    pip install --upgrade pip

# Copy and install only requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source
COPY . /app

EXPOSE 8000
ENTRYPOINT ["/app/scripts/entrypoint.sh"]

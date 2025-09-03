# syntax=docker/dockerfile:1

# ----------------------------
# Base image for FastAPI app
# ----------------------------
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /app
# System packages (build tools and curl for healthcheck)
RUN apt-get update \ 
    && apt-get install -y --no-install-recommends build-essential curl \ 
    && rm -rf /var/lib/apt/lists/*

# ----------------------------
# Development image with reload
# ----------------------------
FROM base AS dev
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt
COPY ./app ./app
COPY ./main.py ./main.py
EXPOSE 8000
CMD ["uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]

# ----------------------------
# Production image
# ----------------------------
FROM base AS prod
COPY requirements.txt ./
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt
COPY ./app ./app
COPY ./main.py ./main.py
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
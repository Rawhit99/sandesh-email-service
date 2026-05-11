# syntax=docker/dockerfile:1.7

############################
# Backend image build
############################
FROM --platform=$TARGETPLATFORM python:3.12-slim AS backend-builder

WORKDIR /build/backend

RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt


FROM --platform=$TARGETPLATFORM python:3.12-slim AS backend-runtime

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash app

COPY --from=backend-builder /install /usr/local
COPY backend/ /app/
COPY tools/sandesh-cli/cli /app/cli

RUN chown -R app:app /app

USER app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


############################
# Frontend image build
############################
FROM --platform=$BUILDPLATFORM node:20-alpine AS frontend-builder

WORKDIR /build/frontend

ARG REACT_APP_API_URL=http://localhost:8000
ENV REACT_APP_API_URL=$REACT_APP_API_URL

COPY frontend/package*.json ./
RUN npm ci --silent

COPY frontend/ ./
RUN npm run build


FROM --platform=$TARGETPLATFORM nginx:1.27-alpine AS frontend-runtime

COPY --from=frontend-builder /build/frontend/build /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["/bin/sh", "-c", "REACT_APP_API_URL=${REACT_APP_API_URL:-http://localhost:8000} envsubst '$REACT_APP_API_URL' < /usr/share/nginx/html/env.template.js > /usr/share/nginx/html/env.js && nginx -g 'daemon off;'"]

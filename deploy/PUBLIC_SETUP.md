# Sandesh — Public Deployment

Run the **Sandesh** notification platform using prebuilt Docker images from GitHub Container Registry (GHCR).

Includes:
- Subscriber management
- Templates
- Event trigger API
- Queue-based processing (Redis worker)
- Web UI + REST API
- Channel integrations (SES, SMTP, Slack, etc.) configured in the dashboard — not in `.env`

This repository is **deployment-only**. You do not need the source code to run it.

**Source & contributions:** https://github.com/Rawhit99/sandesh-email-service

---

## Quick start

### Prerequisites

- Docker
- Docker Compose
- **PostgreSQL** and **Redis** reachable from the containers (managed cloud, or your own hosts)
- GHCR access if images are private (`docker login ghcr.io`)

### Setup

1. Create `docker-compose.yml` and `.env` from the sections below (or copy this repo’s files).

2. Copy env values into `.env` (see **`.env.example`** section).

3. Edit `.env`:
   - Image names (GHCR defaults below)
   - `DATABASE_URL` and `REDIS_URL` (your external instances)
   - `JWT_SECRET_KEY` (long random secret)
   - `PLATFORM_ADMIN_USERNAME`, `PLATFORM_ADMIN_PASSWORD`, `DEFAULT_ORGANIZATION`
   - `REACT_APP_API_URL` and `CORS_ALLOW_ORIGINS` (must match how users reach the app)

4. Start:

   ```bash
   docker compose up -d
   ```

5. Open:

   | Service | URL |
   |---------|-----|
   | Frontend | http://localhost:3000 |
   | Backend health | http://localhost:8000/health |
   | API docs | http://localhost:8000/docs |

6. Log in with the platform admin credentials from `.env` (created on first startup when bootstrap vars are set).

---

## Required files in deployment repo

- `docker-compose.yml` — copy from section below
- `.env` — copy from `.env.example` section below
- `README.md` — optional; this file can serve as the README

---

## Prebuilt images (GHCR)

Published from https://github.com/Rawhit99/sandesh-email-service on merge to `main`:

| Role | Image |
|------|--------|
| Backend + worker | `ghcr.io/rawhit99/sandesh-email-service-backend:latest` |
| Frontend | `ghcr.io/rawhit99/sandesh-email-service-frontend:latest` |

If packages are private:

```bash
docker login ghcr.io
# GitHub username + PAT with read:packages
```

---

## File: `.env.example`

Copy everything below into `.env` and edit values.

```env
# =========================
# Images (pull from GHCR)
# =========================
SANDESH_BACKEND_IMAGE=ghcr.io/rawhit99/sandesh-email-service-backend:latest
SANDESH_FRONTEND_IMAGE=ghcr.io/rawhit99/sandesh-email-service-frontend:latest

# =========================
# Database & Redis (external — not in this compose file)
# =========================
DATABASE_URL=postgresql://user:password@your-postgres-host:5432/emails
REDIS_URL=redis://your-redis-host:6379/0

# =========================
# API / App
# =========================
API_HOST=0.0.0.0
API_PORT=8000
API_EXPOSED_PORT=8000
PYTHONPATH=/app
PYTHONUNBUFFERED=1

# =========================
# Auth
# =========================
JWT_SECRET_KEY=change-this-to-a-long-random-secret
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
API_KEYS=

# =========================
# Platform bootstrap (first admin + default org)
# =========================
PLATFORM_ADMIN_USERNAME=admin
PLATFORM_ADMIN_PASSWORD=change-me-strong-password
DEFAULT_ORGANIZATION=Default Organization

# =========================
# Queue worker tuning
# =========================
QUEUE_WORKER_CONCURRENCY=8
QUEUE_POLL_TIMEOUT_SECONDS=3
QUEUE_MAX_RETRIES=5
QUEUE_RETRY_BACKOFF_SECONDS=2

# =========================
# Frontend / CORS
# =========================
FRONTEND_EXPOSED_PORT=3000
REACT_APP_API_URL=http://localhost:8000
CORS_ALLOW_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# =========================
# Compose
# =========================
COMPOSE_PROJECT_NAME=sandesh-email-service
```

> **Note:** Email/SMS/Slack and other provider credentials are set in the **web UI** (Integrations), not in `.env`.

---

## File: `docker-compose.yml`

Copy everything below into `docker-compose.yml`.

```yaml
services:
  backend:
    image: ${SANDESH_BACKEND_IMAGE}
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      API_HOST: ${API_HOST}
      API_PORT: ${API_PORT}
      PYTHONPATH: ${PYTHONPATH}
      PYTHONUNBUFFERED: ${PYTHONUNBUFFERED}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY}
      JWT_ALGORITHM: ${JWT_ALGORITHM}
      JWT_ACCESS_TOKEN_EXPIRE_MINUTES: ${JWT_ACCESS_TOKEN_EXPIRE_MINUTES}
      API_KEYS: ${API_KEYS}
      PLATFORM_ADMIN_USERNAME: ${PLATFORM_ADMIN_USERNAME}
      PLATFORM_ADMIN_PASSWORD: ${PLATFORM_ADMIN_PASSWORD}
      DEFAULT_ORGANIZATION: ${DEFAULT_ORGANIZATION}
      CORS_ALLOW_ORIGINS: ${CORS_ALLOW_ORIGINS}
    ports:
      - "${API_EXPOSED_PORT:-8000}:${API_PORT}"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:${API_PORT}/health"]
      interval: 20s
      timeout: 5s
      retries: 8
      start_period: 30s
    restart: unless-stopped

  worker:
    image: ${SANDESH_BACKEND_IMAGE}
    command: ["python", "worker.py"]
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      PYTHONPATH: ${PYTHONPATH}
      PYTHONUNBUFFERED: ${PYTHONUNBUFFERED}
      QUEUE_WORKER_CONCURRENCY: ${QUEUE_WORKER_CONCURRENCY}
      QUEUE_POLL_TIMEOUT_SECONDS: ${QUEUE_POLL_TIMEOUT_SECONDS}
      QUEUE_MAX_RETRIES: ${QUEUE_MAX_RETRIES}
      QUEUE_RETRY_BACKOFF_SECONDS: ${QUEUE_RETRY_BACKOFF_SECONDS}
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    image: ${SANDESH_FRONTEND_IMAGE}
    environment:
      REACT_APP_API_URL: ${REACT_APP_API_URL}
    ports:
      - "${FRONTEND_EXPOSED_PORT:-3000}:80"
    depends_on:
      backend:
        condition: service_healthy
    restart: unless-stopped
```

---

## First-time platform setup

After containers are healthy:

1. Open the UI and sign in with `PLATFORM_ADMIN_USERNAME` / `PLATFORM_ADMIN_PASSWORD`.
2. In **Integrations**, add email (SES/SMTP) or other channel credentials.
3. Create templates and subscribers.
4. Trigger events via the API or sandesh-sdk.

---

## Python SDK

Install:

```bash
pip install sandesh-sdk
```

Usage:

```python
from sandesh.sdk import Sandesh

client = Sandesh(
    base_url="http://localhost:8000",
    bearer_token="YOUR_API_KEY_OR_JWT",
)

response = client.events_trigger(
    {
        "name": "welcome-template",
        "to": {"subscriberId": "user-123"},
        "payload": {"name": "Rohit"},
    }
)

print(response)
```

---

## API example

```bash
curl --location 'http://localhost:8000/v1/events/trigger' \
  --header 'Authorization: ApiKey YOUR_API_KEY' \
  --header 'Content-Type: application/json' \
  --data '{
    "name": "welcome-template",
    "to": { "subscriberId": "user-123" },
    "payload": {
      "name": "Rohit"
    }
  }'
```

---

## Operations

Start:

```bash
docker compose up -d
```

Logs:

```bash
docker compose logs -f
docker compose logs -f backend worker frontend
```

Restart:

```bash
docker compose restart
```

Stop:

```bash
docker compose down
```

Pull latest images:

```bash
docker compose pull
docker compose up -d
```

---

## Troubleshooting

| Issue | What to check |
|-------|----------------|
| Backend unhealthy | `docker compose logs backend` — `DATABASE_URL`, `JWT_SECRET_KEY`, DB reachable from container |
| Worker not processing | `docker compose logs worker` — `REDIS_URL`, Redis reachable, backend healthy |
| Frontend cannot call API | `REACT_APP_API_URL` must be the URL **the browser** uses (not `http://backend:8000`). Match `CORS_ALLOW_ORIGINS` to the frontend origin |
| Cannot pull images | `docker login ghcr.io`; confirm publish workflow ran on sandesh-email-service |
| Login fails | Bootstrap vars set before first start |

---

## Security

- Never commit a real `.env`
- Use a strong `JWT_SECRET_KEY` and platform admin password
- Put HTTPS and a reverse proxy in front for internet-facing deployments
- Restrict network access to Postgres and Redis

---

## License

MIT License

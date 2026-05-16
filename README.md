<p align="center">
  <img
    src="./docs/assets/sandesh-logo-readme.png"
    alt="Sandesh logo"
    width="280"
  />
</p>

# Sandesh

**Open-source, multi-channel notification infrastructure for product teams.**  
*Sandesh* (संदेश) means *message* in Hindi — built for reliable delivery at scale.

---

## What is Sandesh?

Sandesh is a self-hostable notification platform inspired by modern event-driven systems, focused on:

- **Multi-channel delivery** — email (AWS SES / SMTP), Slack, Microsoft Teams, FCM push, SNS, WhatsApp (Twilio)
- **Template engine** — reusable templates with variables, previews, and validation
- **Subscribers & events** — trigger workflows by event name with subscriber context
- **Enterprise controls** — organizations, API keys, JWT auth, audit logs, rate limits
- **Python SDK** — [`sandesh-sdk` on PyPI](https://pypi.org/project/sandesh-sdk/) for programmatic integration
- **Operator UI** — React dashboard for templates, subscribers, integrations, and delivery logs

Define notifications as code or API calls, version templates, and observe delivery in production from a single control plane.

---

## Host Sandesh (run the platform)

**You do not need this source repository to run Sandesh.**

Use the deployment repository — it contains `docker-compose.yaml`, `.env.example`, and a full hosting guide:

### [**github.com/Rawhit99/test-sandesh**](https://github.com/Rawhit99/test-sandesh)

That repo is **deployment-only**: pull prebuilt images, configure `.env`, and start the stack.

### Quick start (from the deployment repo)

```bash
git clone https://github.com/Rawhit99/test-sandesh.git
cd test-sandesh
cp .env.example .env
# Edit .env — JWT_SECRET_KEY, image names, DATABASE_URL, etc.
docker compose up -d
```

| Service      | URL |
| ------------ | --- |
| Dashboard    | http://localhost:3000 |
| API          | http://localhost:8000 |
| OpenAPI docs | http://localhost:8000/docs |

### After containers are up

1. Open the UI and **register** the first user.
2. Configure email integration in the UI (SES/SMTP) — credentials are set in the app, not only in `.env`.
3. Create templates and subscribers.
4. Trigger events via the API or Python SDK.

Default images (override in `.env` if you publish your own):

- `rohithakur0208/sandesh-email-backend:latest`
- `rohithakur0208/sandesh-email-frontend:latest`

Operations, troubleshooting, and security notes: see the [test-sandesh README](https://github.com/Rawhit99/test-sandesh/blob/main/README.md).

---

## Python SDK

Install from PyPI:

```bash
pip install sandesh-sdk
```

```python
from sandesh.sdk import Sandesh

client = Sandesh(
    base_url="http://localhost:8000",
    bearer_token="your_api_key_or_jwt",
)

result = client.events_trigger(
    {
        "name": "welcome-email",
        "to": {"subscriberId": "user-123"},
        "payload": {"name": "Asha", "company": "Sandesh Labs"},
    }
)
print(result)
```

See [backend/README.md](./backend/README.md) for the full SDK surface.

---

## API example (curl)

```bash
curl -X POST "http://localhost:8000/api/v1/events/trigger" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "welcome-email",
    "to": { "subscriberId": "user-123" },
    "payload": { "name": "Asha" }
  }'
```

---

## Contribute to Sandesh (this repository)

**Want to fix bugs, add features, or improve docs?** Work in **this** repo (`sandesh-email-service`), not the deployment repo.

| Goal | Repository |
| ---- | ---------- |
| **Run / host** the platform | [Rawhit99/test-sandesh](https://github.com/Rawhit99/test-sandesh) |
| **Develop / contribute** | [sandesh-email-service](https://github.com/Rawhit99/sandesh-email-service) (here) |

### Source layout

```text
sandesh-email-service/
├── backend/           # FastAPI API, services, Alembic migrations
│   └── sandesh/       # Python SDK (published as sandesh-sdk)
├── frontend/          # React operator dashboard
├── tools/sandesh-cli/ # Template sync CLI utilities
├── docs/              # Brand assets and documentation
└── docker-compose.yml # Full-stack build from source (contributors)
```

Architecture and layering: [backend/ARCHITECTURE.md](./backend/ARCHITECTURE.md).

### Requirements (development)

| Component  | Version |
| ---------- | ------- |
| Python     | 3.12+   |
| Node.js    | 18+     |
| PostgreSQL | 15+     |
| Redis      | 7+ (recommended for the worker) |
| Docker     | 24+ (optional) |

### Develop from source

```bash
git clone https://github.com/Rawhit99/sandesh-email-service.git
cd sandesh-email-service
cp .env.example .env
docker compose up -d --build
```

Or run services individually — see [CONTRIBUTING.md](./CONTRIBUTING.md).

### Governance

| Document | Description |
| -------- | ----------- |
| [CONTRIBUTING.md](./CONTRIBUTING.md) | How to contribute (read before opening a PR) |
| [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) | Community standards |
| [SECURITY.md](./SECURITY.md) | Responsible disclosure |
| [SUPPORT.md](./SUPPORT.md) | Getting help |
| [GOVERNANCE.md](./GOVERNANCE.md) | Project roles and decisions |
| [RELEASE_POLICY.md](./RELEASE_POLICY.md) | Merge rules; SDK/CLI publish (maintainer-only) |
| [BRANCH_PROTECTION.md](./BRANCH_PROTECTION.md) | GitHub settings so only you approve merges |
| [OPEN_SOURCE.md](./OPEN_SOURCE.md) | Maintainer release checklist |

Before opening a PR, read [CONTRIBUTING.md](./CONTRIBUTING.md) and use the pull request template.

---

## Prebuilt images (maintainers)

This repo publishes images via [.github/workflows/publish-images.yml](./.github/workflows/publish-images.yml):

- `ghcr.io/<owner>/<repo>-backend:<tag>`
- `ghcr.io/<owner>/<repo>-frontend:<tag>`

Tags: `latest`, short commit SHA, and git tags (`v*.*.*`).

Point the [deployment repo](https://github.com/Rawhit99/test-sandesh) `.env` at these images when you release new versions.

---

## License

Licensed under the [MIT License](./LICENSE).

Copyright (c) 2026 Rohit Thakur and contributors.

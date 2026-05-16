# Contributing to Sandesh

Thank you for your interest in contributing to Sandesh. Every contribution —
code, documentation, bug reports, and design feedback — helps make reliable
notifications accessible to more teams.

## Which repository?

| Goal | Repository |
| ---- | ---------- |
| **Host** Sandesh with prebuilt images | [Rawhit99/test-sandesh](https://github.com/Rawhit99/test-sandesh) |
| **Contribute** (code, docs, issues, PRs) | **This repo** — `sandesh-email-service` |

Do not open feature PRs on the deployment repo; it is for `docker compose` and `.env` only.

## Reviews and merging

- You **cannot merge** your own PR into `main` without **maintainer (code owner) approval**.
- [@Rawhit99](https://github.com/Rawhit99) owns all paths in [CODEOWNERS](./.github/CODEOWNERS) when branch protection is enabled.
- **Do not publish** `sandesh-sdk` to PyPI or release the CLI — that is [maintainer-only](./RELEASE_POLICY.md).

## Before you start

1. Read the [README](./README.md) and [backend/ARCHITECTURE.md](./backend/ARCHITECTURE.md).
2. Search [existing issues](https://github.com/RohitThakur/sandesh-email-service/issues)
   to avoid duplicate work.
3. For large changes, open an issue first to discuss approach and scope.

## License

By contributing, you agree that your contributions are licensed under the
same license as the project: [MIT](./LICENSE).

## Development setup

### Prerequisites

- Docker and Docker Compose (recommended)
- Python 3.12+
- Node.js 18+ (for frontend work)
- PostgreSQL 15+ and Redis 7+ (or use Compose services)

### Local environment

```bash
git clone https://github.com/<your-fork>/sandesh-email-service.git
cd sandesh-email-service
cp .env.example .env
# Fill required values (see README)
docker compose up -d --build
```

### Backend only

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn main:app --reload
```

### Frontend only

```bash
cd frontend
npm install
npm start
```

### SDK package (backend/sandesh)

```bash
cd backend
pip install -e .
# Or build wheel:
python -m pip install build
python -m build
```

## Submitting issues

### Bug reports

Please include:

- Sandesh version or commit SHA
- Steps to reproduce (minimal example preferred)
- Expected vs actual behavior
- Logs, stack traces, or screenshots
- Environment (OS, Docker, browser)

Use the [bug report template](.github/ISSUE_TEMPLATE/bug_report.yml).

Without a reproducible scenario, we may not be able to investigate every report.

### Feature requests

Describe the problem, proposed solution, and alternatives considered.
Use the [feature request template](.github/ISSUE_TEMPLATE/feature_request.yml).

## Pull request process

1. Fork the repository and create a branch from `main`.
2. Keep PRs focused — one logical change per PR when possible.
3. Update documentation when behavior or configuration changes.
4. Add or update tests when fixing bugs or adding features.
5. Ensure no secrets, credentials, or `.env` files are committed.
6. Fill out the [pull request template](.github/pull_request_template.md).

### Commit messages

Use clear, imperative messages:

- `fix: handle missing subscriber on event trigger`
- `docs: add Redis configuration to README`
- `feat: expose template preview in public API`

### Code style

- Follow existing patterns in `routers/`, `services/`, and `api/contracts/`.
- Business logic belongs in `services/`; HTTP wiring stays in `routers/`.
- Prefer typed exceptions and explicit HTTP status codes.
- Run linters on changed Python files before submitting.

## Project structure (where to change what)

| Path | Purpose |
|------|---------|
| `backend/routers/` | HTTP routes only |
| `backend/services/` | Business logic |
| `backend/api/contracts/` | Public API request/response models |
| `backend/api/mappers/` | Contract ↔ service mapping |
| `backend/models/` | ORM and internal schemas |
| `backend/sandesh/` | Published Python SDK |
| `frontend/src/` | React dashboard |

## Security

Do **not** open public issues for security vulnerabilities.
Follow [SECURITY.md](./SECURITY.md).

## Ways to contribute

- Reproduce and triage issues
- Improve documentation and examples
- Add provider integrations or channel adapters
- Enhance the operator UI
- Write tests and improve CI
- Share Sandesh with teams who need self-hosted notifications

## Getting help

- [GitHub Issues](https://github.com/RohitThakur/sandesh-email-service/issues)
- [SUPPORT.md](./SUPPORT.md)

We appreciate your time and effort. धन्यवाद — thank you for helping Sandesh grow.

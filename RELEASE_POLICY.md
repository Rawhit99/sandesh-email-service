# Release & Publish Policy

## Merge policy

- All changes to `main` go through a **pull request**.
- **@Rawhit99** is the code owner ([CODEOWNERS](./.github/CODEOWNERS)).
- Merges require **code owner approval** when branch protection is enabled ([BRANCH_PROTECTION.md](./BRANCH_PROTECTION.md)).
- Contributors cannot merge their own PRs without maintainer review unless explicitly granted admin access.

## What contributors can do

- Fork, branch, open PRs, discuss issues
- Change application code **with** maintainer review
- **Cannot** merge to `main` without approval
- **Cannot** publish `sandesh-sdk` to PyPI
- **Cannot** publish or republish the Sandesh CLI package on your behalf

## Maintainer-only releases

| Artifact | How it is published | Automation |
| -------- | ------------------- | ---------- |
| **Docker images** (backend/frontend) | GitHub Actions on merge/tag | [publish-images.yml](./.github/workflows/publish-images.yml) — runs only after **you** merge to `main` |
| **`sandesh-sdk` (PyPI)** | **Manual** `twine upload` from maintainer machine | **No** PyPI workflow in this repo |
| **Sandesh CLI** (`tools/sandesh-cli`) | **Not** on PyPI by default; source in repo only | **No** publish workflow |

### PyPI (`sandesh-sdk`)

Only the maintainer should:

1. Hold the PyPI API token (local password manager — **never** commit to GitHub).
2. Bump version in `backend/pyproject.toml` and `backend/sandesh/__init__.py`.
3. Build and upload per [OPEN_SOURCE.md](./OPEN_SOURCE.md) / [backend/README.md](./backend/README.md).

Do **not** add `PYPI_API_TOKEN` to GitHub repository secrets unless you also lock Actions behind an environment with **required reviewer = you**.

### CLI

The CLI under `tools/sandesh-cli/` is developed in-tree. Publishing to PyPI (if ever) is **maintainer-only** and requires an explicit decision and version bump — not contributor-driven.

## Docker images vs SDK

- **Merging to `main`** triggers (or can trigger) **container** builds — protect `main` so only you control merges.
- **PyPI SDK** is **independent** — protect by keeping tokens off CI and off shared secrets.

## Adding a co-maintainer later

1. Add their GitHub handle to [CODEOWNERS](./.github/CODEOWNERS).
2. Add them as required reviewer only if you trust them with merges and releases.
3. Never share PyPI tokens in chat or in the repository.

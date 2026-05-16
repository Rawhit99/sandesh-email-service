# Open Source Release Checklist

This guide is for maintainers preparing Sandesh for public release and ongoing
community stewardship.

## Pre-release

- [ ] Remove secrets from git history if any were ever committed
- [ ] Verify `.env` is gitignored and `.env.example` documents all required vars
- [ ] Confirm [LICENSE](./LICENSE) year and copyright holders
- [ ] Review [CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md) contact email
- [ ] Review [SECURITY.md](./SECURITY.md) disclosure process
- [ ] Enable branch protection per [BRANCH_PROTECTION.md](./BRANCH_PROTECTION.md)
- [ ] Add repository description, topics (`notifications`, `email`, `python`, `fastapi`, `novu-alternative`)
- [ ] Upload social preview image (use `docs/assets/sandesh-icon.png`)

## Access control (before going public)

- [ ] Apply [BRANCH_PROTECTION.md](./BRANCH_PROTECTION.md) on `main` (require **Code Owner** review).
- [ ] Confirm [CODEOWNERS](./.github/CODEOWNERS) lists `@Rawhit99`.
- [ ] Read [RELEASE_POLICY.md](./RELEASE_POLICY.md) — PyPI/CLI are maintainer-only.

## PyPI (`sandesh-sdk`) — maintainer only

**Contributors cannot publish.** Only you run `twine upload` (no PyPI token in GitHub Actions).

1. Bump version in `backend/pyproject.toml` and `backend/sandesh/__init__.py`.
2. Update `backend/README.md` changelog/examples if the public API changed.
3. Build and verify:

```bash
cd backend
python -m pip install --upgrade build twine
python -m build
python -m twine check dist/*
```

4. Upload to TestPyPI first, then production PyPI.
5. Tag the release: `git tag v0.x.y && git push origin v0.x.y`

## Container images (GHCR)

Publishing is automated on push to `main` and version tags via
`.github/workflows/publish-images.yml`.

Verify images after release:

- `ghcr.io/<owner>/<repo>-backend:latest`
- `ghcr.io/<owner>/<repo>-frontend:latest`

## Community hygiene

- Respond to new issues within a reasonable SLA
- Label issues: `bug`, `enhancement`, `good first issue`, `help wanted`
- Welcome first-time contributors
- Keep `main` deployable

## Optional next steps

- Add CI workflow for lint/test on pull requests
- Publish documentation site (MkDocs or Docusaurus)
- Create a public roadmap (GitHub Projects)
- Register on [libraries.io](https://libraries.io/) and package indexes

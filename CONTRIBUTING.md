# Contributing

Thanks for your interest in contributing.

## License and Usage Terms

By contributing, you agree your contribution is licensed under the same
repository license (MIT).

## Development Setup

1. Fork the repository and create a feature branch.
2. Copy `.env.example` to `.env` and fill required values.
3. Run locally:
   - `docker compose build`
   - `docker compose up -d`
4. Ensure code quality checks pass for changed files.

## Pull Request Guidelines

- Keep PRs focused and small.
- Add/update tests for behavior changes.
- Update docs when changing public behavior.
- Do not include secrets or credentials.
- Use clear commit messages.

## Code Style

- Follow existing architecture and file organization.
- Prefer typed exceptions and service-layer business logic.
- Keep line length and lint rules compliant with repo standards.

## Security

Do not open public issues for sensitive vulnerabilities.
Use the private process in `SECURITY.md`.

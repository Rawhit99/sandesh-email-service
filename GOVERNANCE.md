# Project Governance

Sandesh is an open-source project under the [MIT License](./LICENSE).

## Maintainer

**@Rawhit99** is the primary maintainer and code owner. See [.github/CODEOWNERS](./.github/CODEOWNERS).

## Roles

| Role | Can merge to `main`? | Can publish SDK/CLI? |
| ---- | -------------------- | -------------------- |
| **Maintainer** (`@Rawhit99`) | Yes (after self-review / policy) | Yes (manual PyPI; you control tokens) |
| **Contributor** | No — PR only | No |
| **User** | No | No |

## Decision making

- Changes merge via pull request with **code owner review** ([BRANCH_PROTECTION.md](./BRANCH_PROTECTION.md)).
- Breaking API changes should be discussed in an issue first.
- Security issues: [SECURITY.md](./SECURITY.md) (private report).

## Releases

Full rules: [RELEASE_POLICY.md](./RELEASE_POLICY.md).

- **`sandesh-sdk` on PyPI** — maintainer-only manual publish; no automated PyPI workflow in this repo.
- **CLI** — source in `tools/sandesh-cli/`; not published by contributors.
- **Docker images** — GitHub Actions after merge to `main`; controlled by who can merge.

## Code of Conduct

[CODE_OF_CONDUCT.md](./CODE_OF_CONDUCT.md)

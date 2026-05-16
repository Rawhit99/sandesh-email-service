# Branch & Release Protection (GitHub Settings)

Apply these on **`main`** (and optionally `new_integration_features`) so **no one can merge without maintainer review** and **releases stay under your control**.

Repository: [github.com/Rawhit99/sandesh-email-service](https://github.com/Rawhit99/sandesh-email-service)

## 1. Branch protection rule (`main`)

**Settings → Branches → Add branch protection rule → Branch name: `main`**

Enable:

| Setting | Value |
| -------- | ----- |
| Require a pull request before merging | On |
| Required approvals | **1** (or more) |
| **Require review from Code Owners** | **On** (uses [.github/CODEOWNERS](./.github/CODEOWNERS)) |
| Dismiss stale pull request approvals when new commits are pushed | On |
| Require conversation resolution before merging | On |
| Require branches to be up to date before merging | On (when CI exists) |
| Do not allow bypassing the above settings | **On** (even for admins, if you want strictest mode) |
| Restrict who can push to matching branches | **On** — allow only **your** GitHub user |
| Allow force pushes | Off |
| Allow deletions | Off |

Result: every PR needs **your CODEOWNERS approval** before merge.

## 2. Tag protection (`v*` releases)

**Settings → Tags → Add rule → Tag name pattern: `v*`**

- Restrict who can create matching tags → **only you** (or Maintainers group you control)
- This limits who can trigger versioned Docker publishes tied to git tags

## 3. Actions permissions

**Settings → Actions → General**

- **Workflow permissions:** Read repository contents (minimum needed)
- **Fork pull request workflows:** Require approval for first-time contributors (recommended)

**Settings → Actions → General → Approval for running fork PR workflows:** Enabled

## 4. Environments (optional, recommended)

Create environment **`release`**:

- Required reviewers: **you only**
- Deployment branches: `main` or tags only

Use this if you later add a manual `workflow_dispatch` release workflow.

## 5. Who can merge?

| Role | Suggested access |
| ---- | ---------------- |
| **You (`Rawhit99`)** | Admin — merge after review, publish SDK/CLI, manage settings |
| **Contributors** | Read or Triage — open PRs only |
| **Others** | No Write on `main` if you use “Restrict who can push” |

Do **not** give broad **Write** or **Maintain** on the repo unless you trust them to merge.

## 6. PyPI & CLI (not controlled by branch rules alone)

Branch protection does **not** block PyPI uploads. See [RELEASE_POLICY.md](./RELEASE_POLICY.md):

- **`sandesh-sdk`** — manual publish by maintainer only; **no** PyPI token in GitHub Actions
- **CLI** — not published to PyPI from this repo unless you add it; maintainer-only

## Checklist

- [ ] Branch protection on `main` with **Require review from Code Owners**
- [ ] Restrict pushes to `main` to maintainer only
- [ ] Tag protection on `v*`
- [ ] CODEOWNERS points to `@Rawhit99`
- [ ] No shared PyPI API token in repository secrets
- [ ] Docker publish ([publish-images.yml](./.github/workflows/publish-images.yml)) only runs after **you** merge to `main`

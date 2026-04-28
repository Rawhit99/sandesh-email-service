# Recommended Branch Protection (GitHub)

Apply these settings to your default branch (usually `main`):

1. Require a pull request before merging.
2. Require at least 1 approval.
3. Dismiss stale approvals when new commits are pushed.
4. Require status checks to pass before merging.
5. Require branches to be up to date before merging.
6. Require conversation resolution before merging.
7. Restrict who can push to matching branches (optional for teams).
8. Do not allow force pushes.
9. Do not allow deletions.

## Suggested roles

- `Admin`/`Maintain`: can manage settings and merge when checks pass.
- `Write`: can open PRs and merge if branch rules permit.
- `Triage`/`Read`: cannot merge.

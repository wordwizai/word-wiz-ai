---
name: deploy-backend
description: Use when asked to deploy, ship, or roll back the backend on the production EC2 box (api.wordwizai.com)
disable-model-invocation: true
---

# Deploy backend

Run from the repo root with the Bash tool, `timeout: 600000` (builds are slow on this box):

```bash
scripts/deploy-backend.sh            # latest origin/main
scripts/deploy-backend.sh <sha>      # a specific commit, i.e. a rollback
```

If it fails with `WWAI_HOST` unset, ask the user to fill in `.env.deploy` at the main checkout's root (see the script header). Never ask for or use a password.

## Rules

- **Only origin/main ships.** If the change isn't pushed or merged, say so. Don't push without asking.
- **`STOP: ... alembic migrations`**: ask the user. Prod migrations are theirs to run. Re-run with `MIGRATIONS_OK=1` only after they confirm.
- **A `ROLLBACK:` line means prod is broken.** Run that command right away, then report what failed.
- **Git error on the server, nothing changed**: report it. Don't stash, reset, or edit files on the server. Its `docker-compose.yml` differs from git on purpose (resource limits removed).
- **Never hit `/health/model-optimization` or `/health/performance-test`.** Each one loads a second model and can OOM the box.
- On an ONNX failure, roll back. Don't "fix" it with `USE_ONNX_BACKEND=false` (see the fast-model trap in CLAUDE.md).

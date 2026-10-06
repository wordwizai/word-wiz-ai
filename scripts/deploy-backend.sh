#!/usr/bin/env bash
# Deploy the backend to the EC2 box: check out a commit, rebuild the backend
# container, and check it came back up serving the right model.
#
#   scripts/deploy-backend.sh          # deploy latest origin/main
#   scripts/deploy-backend.sh <sha>    # deploy (or roll back to) a specific commit
#   scripts/deploy-backend.sh --check  # read-only: test the connection, show what's live
#
# Connection settings come from the environment or a .env.deploy file at the
# repo root (gitignored):
#   WWAI_HOST=<ec2-public-ip>
#   WWAI_KEY=C:/path/to/key.pem    # or the key itself, in double quotes
#   WWAI_USER=ubuntu               # optional, default ubuntu
#
# Set MIGRATIONS_OK=1 to deploy a range that adds alembic migrations (they are
# not applied automatically; main.py's create_all() never adds columns).
set -euo pipefail

root=$(git -C "$(dirname "$0")" rev-parse --show-toplevel)
main_root=$(cd "$(git -C "$root" rev-parse --git-common-dir)/.." && pwd)  # worktrees share the main checkout's .env.deploy
for f in "$root/.env.deploy" "$main_root/.env.deploy"; do
  if [[ -s $f ]]; then set -a; . <(tr -d '\r' < "$f"); set +a; break; fi
done
: "${WWAI_HOST:?set WWAI_HOST in the environment or .env.deploy}"

# WWAI_KEY may be a path or the pasted key itself; ssh -i needs a file.
if [[ ${WWAI_KEY:-} == *"PRIVATE KEY"* ]]; then
  keyfile=$(mktemp)
  trap 'rm -f "$keyfile"' EXIT
  chmod 600 "$keyfile"
  printf '%b\n' "$WWAI_KEY" > "$keyfile"   # %b also turns literal \n into newlines
  WWAI_KEY=$keyfile
fi

ref=${1:-origin/main}
ssh_opts=(-o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=20 -o StrictHostKeyChecking=accept-new)
[[ -n ${WWAI_KEY:-} ]] && ssh_opts+=(-i "$WWAI_KEY")

if [[ $ref == --check ]]; then  # read-only: what's live and what's running
  ssh "${ssh_opts[@]}" "${WWAI_USER:-ubuntu}@$WWAI_HOST" \
    'cd ~/word-wiz-ai && git log -1 --format="checkout: %h %s (%cr)" && cd backend && docker compose ps --format "{{.Service}}: {{.Status}}" &&
     df -h / | awk "NR==2 {print \"disk: \" \$4 \" free of \" \$2 \" (\" \$5 \" used)\"}" && docker system df'
  exit
fi

ssh "${ssh_opts[@]}" "${WWAI_USER:-ubuntu}@$WWAI_HOST" bash -s -- "$ref" "${MIGRATIONS_OK:-}" <<'REMOTE'
set -euo pipefail
ref=$1 migrations_ok=${2:-}
cd ~/word-wiz-ai

prev=$(git rev-parse --short HEAD)
git fetch -q origin
target=$(git rev-parse --short "$ref^{commit}")
echo "==> $prev -> $target"
git log --format='    %h %s' "$prev..$target" -- backend | head -20

if [[ -z $migrations_ok ]] && git diff --name-only "$prev" "$target" | grep -q '^backend/alembic/versions/'; then
  echo "STOP: this range adds alembic migrations, which nothing applies automatically."
  echo "      Run them against prod first, then re-run with MIGRATIONS_OK=1. Nothing was changed."
  exit 1
fi

# A failed checkout (e.g. upstream touched the server's locally edited
# docker-compose.yml) stops here with nothing changed.
if [[ $ref == origin/main ]]; then
  git checkout -q main && git merge -q --ff-only origin/main
else
  git checkout -q "$target"
fi
now=$target

cd backend
echo "==> building and swapping the backend container (old one serves until the swap)"
if ! docker compose up -d --build backend < /dev/null 2>&1 | tail -n 15; then
  echo "FAIL: build/up failed. If it was the build, the old container is still serving."
  echo "ROLLBACK (puts the checkout back too): scripts/deploy-backend.sh $prev"
  exit 1
fi

echo "==> waiting for /docs"
code=000
for _ in $(seq 60); do
  code=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 5 https://localhost:8443/docs || true)
  [[ $code == 200 ]] && break
  sleep 5
done
logs=$(docker compose logs --no-log-prefix backend 2>&1 || true)
if [[ $code != 200 ]]; then
  echo "FAIL: /docs returned $code after 5 minutes"
  tail -n 30 <<<"$logs"
  echo "ROLLBACK: scripts/deploy-backend.sh $prev"
  exit 1
fi
echo "    /docs 200"

# The PyTorch fallback loads a character model scored against IPA, so every
# word reads as wrong. A 200 from /docs doesn't catch that; the log does.
if grep -q 'ONNX loading failed' <<<"$logs"; then
  grep 'ONNX loading failed' <<<"$logs" | head -1
  echo "FAIL: ONNX fell back to PyTorch (the fast-model trap in CLAUDE.md)"
  echo "ROLLBACK: scripts/deploy-backend.sh $prev"
  exit 1
fi
if grep -qF '[OK] ONNX Runtime backend loaded successfully' <<<"$logs"; then
  echo "    ONNX model loaded"
else
  echo "    WARN: ONNX status line not in the logs yet, so the model backend is unconfirmed"
fi

# nginx resolves backend:8443 once at startup; a recreated container can get
# a new IP, and nginx keeps proxying to the old one (502).
nginx=$(curl -sk -o /dev/null -w '%{http_code}' --max-time 10 \
  --resolve api.wordwizai.com:443:127.0.0.1 https://api.wordwizai.com/docs || true)
if [[ $nginx != 200 ]]; then
  echo "    nginx returned $nginx, restarting it"
  docker compose restart nginx < /dev/null > /dev/null 2>&1
fi
echo "==> deployed $now (previous: $prev)"
REMOTE

sleep 3
public=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 https://api.wordwizai.com/docs || true)
echo "==> https://api.wordwizai.com/docs from here: $public"
[[ $public == 200 ]]

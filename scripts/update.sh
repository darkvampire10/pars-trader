#!/usr/bin/env bash
# Explicit version/commit only; never automatically changes a running trading system.
set -euo pipefail
cd "$(dirname "$0")/.."
ref="${1:?Usage: bash scripts/update.sh VERSION_TAG_OR_COMMIT}"
[[ "$ref" != -* ]] || { echo 'Invalid ref'; exit 1; }
[[ -z "$(git status --porcelain)" ]] || { echo 'Commit or stash local source changes first.'; exit 1; }
git fetch origin --tags
target="$(git rev-parse --verify "${ref}^{commit}")"
previous="$(git rev-parse HEAD)"
python3 -m unittest discover -s tests -q
# Build and test in a detached worktree BEFORE stopping the service.
work="$(mktemp -d)"
git worktree add --detach "$work" "$target"
cleanup() { git worktree remove --force "$work" >/dev/null 2>&1 || true; }
trap cleanup EXIT
(cd "$work"; python3 -m unittest discover -s tests -q)
docker build -t pars-trader-candidate "$work"
mkdir -p backups
stamp="$(date -u +%Y%m%dT%H%M%SZ)"
docker compose stop
# Service is stopped, so DB + WAL can be backed up consistently.
tar -czf "backups/data-${stamp}.tar.gz" data
printf '%s\n' "$previous" > "backups/previous-${stamp}.txt"
git switch --detach "$target"
if ! docker compose up -d --build; then
  git switch --detach "$previous"
  docker compose up -d --build
  echo 'Deployment command failed; returned to previous code. Inspect logs.'
  exit 1
fi
echo "Updated to $target. Previous code: $previous"
echo 'Check docker compose ps and /status. Rollback requires stopping, selecting previous commit, then starting.'

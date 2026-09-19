#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
command -v docker >/dev/null || { echo 'Install Docker Engine + Compose from docs.docker.com first.'; exit 1; }
docker compose version >/dev/null
if [[ ! -f .env ]]; then
  (umask 077; cp .env.example .env)
  echo 'Created .env. Set Telegram token and owner ID locally, then run this script again.'
  exit 0
fi
if ! grep -Eq '^TELEGRAM_BOT_TOKEN=.+$' .env || ! grep -Eq '^TELEGRAM_OWNER_ID=[1-9][0-9]*$' .env; then
  echo 'Set TELEGRAM_BOT_TOKEN and TELEGRAM_OWNER_ID in .env before starting.'
  exit 1
fi
chmod 600 .env
mkdir -p data backups
if [[ "$(stat -c %u data)" != 10001 ]]; then
  echo 'Data directory must be writable by container UID 10001. Run: sudo chown -R 10001:10001 data'
  exit 1
fi
docker compose build
docker compose run --rm bot python -m pars_trader demo
docker compose up -d
docker compose ps

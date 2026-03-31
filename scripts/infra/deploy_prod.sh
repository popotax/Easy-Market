#!/usr/bin/env bash
set -euo pipefail

if [[ ! -f .env.production ]]; then
  echo "Missing .env.production (copy .env.production.example and set values)"
  exit 1
fi

if [[ ! -f deploy/Caddyfile ]]; then
  echo "Missing deploy/Caddyfile"
  exit 1
fi

docker compose -f deploy/docker-compose.prod.yml up -d --build

echo "Deployment started."
echo "Check status: docker compose -f deploy/docker-compose.prod.yml ps"
echo "Check logs: docker compose -f deploy/docker-compose.prod.yml logs -f"

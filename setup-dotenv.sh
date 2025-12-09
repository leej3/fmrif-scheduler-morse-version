#!/bin/bash
set -euo pipefail

# Ensure .env.docker is a file (needed for volume mount to /app/.env)
if [ -d ".env.docker" ]; then
  if [ "$(ls -A .env.docker)" ]; then
    echo "ERROR: .env.docker is a directory and not empty; replace it with a file." >&2
    exit 1
  fi
  rmdir .env.docker
fi

# Copy all .env.sample files to .env.docker
while IFS= read -r f; do
  cp "$f" "${f%.sample}.docker"
  echo "Copied $f to ${f%.sample}.docker"
done < <(find . -name .env.sample -print)

# Copy all .env.sample.local files to .env
while IFS= read -r f; do
  cp "$f" "${f%.sample.local}"
  echo "Copied $f to ${f%.sample.local}"
done < <(find . -name .env.sample.local -print)

# If no .env.docker was created (e.g. missing .env.sample), fall back to using .env
if [ ! -f .env.docker ] && [ -f .env ]; then
  cp .env .env.docker
  echo "Copied .env to .env.docker"
fi

# Fail fast if required files are still missing
[ -f .env ] || { echo "ERROR: .env was not created. Add one or create from .env.sample.local." >&2; exit 1; }
[ -f .env.docker ] || { echo "ERROR: .env.docker was not created. Add one or create from .env.sample/.env." >&2; exit 1; }

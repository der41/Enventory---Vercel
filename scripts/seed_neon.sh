#!/usr/bin/env bash
# Apply db/create.sql and db/load.sql to a Neon (or any) Postgres URL.
#
# Usage:
#   ./scripts/seed_neon.sh "postgresql://user:pass@host/db?sslmode=require"
#
# The CSVs in db/data/ are loaded via psql's \copy so no server-side filesystem
# access is needed.

set -euo pipefail

if [ $# -lt 1 ]; then
  echo "Usage: $0 <DATABASE_URL>" >&2
  exit 1
fi

DATABASE_URL="$1"
REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"

cd "$REPO_ROOT"

echo "==> Applying schema (db/create.sql)"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$REPO_ROOT/db/create.sql"

echo "==> Loading seed data (db/load.sql — \\COPY resolves CSVs relative to CWD)"
cd "$REPO_ROOT/db/data"
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f "$REPO_ROOT/db/load.sql"

echo "==> Done."

#!/usr/bin/env bash
# Postgres official image runs this as ./script if executable, otherwise sources it.
# Be source-safe: avoid `set -u` and use `die` instead of bare `exit` when possible.
set -eo pipefail
DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
DIM="${EMBEDDING_DIMENSIONS:-768}"
if ! [[ "${DIM}" =~ ^[0-9]+$ ]]; then
  echo "Invalid EMBEDDING_DIMENSIONS: ${DIM}" >&2
  return 1 2>/dev/null || exit 1
fi
sed "s/__EMBEDDING_DIM__/${DIM}/g" "${DIR}/01_schema.tpl" | psql -v ON_ERROR_STOP=1 -U "${POSTGRES_USER}" -d "${POSTGRES_DB}"

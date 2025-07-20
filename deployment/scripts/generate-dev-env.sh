#!/usr/bin/env bash
# Generate a .env file with unique development credentials for TraderTerminal
# Usage: ./generate-dev-env.sh (run from any directory)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
COMPOSE_DIR="${SCRIPT_DIR}/../compose"
ENV_FILE="${COMPOSE_DIR}/.env"

if [[ -f "${ENV_FILE}" ]]; then
  echo "[INFO] ${ENV_FILE} already exists. Delete it if you want to regenerate."
  exit 0
fi

rand() { openssl rand -base64 32 | tr -dc 'A-Za-z0-9' | head -c 24; }

MONGO_INITDB_ROOT_USERNAME="tradenote"
MONGO_INITDB_ROOT_PASSWORD="$(rand)"
MONGO_INITDB_DATABASE="tradenote"
APP_ID="traderterminal_$(rand | head -c 8)"
MASTER_KEY="$(rand)"
TRADENOTE_MONGO_URI="mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@tradenote-mongo:27017/${MONGO_INITDB_DATABASE}?authSource=admin"

cat > "${ENV_FILE}" <<EOF
MONGO_INITDB_ROOT_USERNAME=${MONGO_INITDB_ROOT_USERNAME}
MONGO_INITDB_ROOT_PASSWORD=${MONGO_INITDB_ROOT_PASSWORD}
MONGO_INITDB_DATABASE=${MONGO_INITDB_DATABASE}
TRADENOTE_MONGO_URI=${TRADENOTE_MONGO_URI}
APP_ID=${APP_ID}
MASTER_KEY=${MASTER_KEY}
EOF

echo "[SUCCESS] Generated ${ENV_FILE} with the following values:"
cat "${ENV_FILE}" 
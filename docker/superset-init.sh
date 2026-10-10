#!/usr/bin/env bash
set -euo pipefail

echo "[init] Running metadata database migrations..."
superset db upgrade

echo "[init] Ensuring administrator user '${ADMIN_USERNAME}' exists..."
if ! superset fab create-admin \
  --username "${ADMIN_USERNAME}" \
  --firstname "${ADMIN_FIRSTNAME}" \
  --lastname "${ADMIN_LASTNAME}" \
  --email "${ADMIN_EMAIL}" \
  --password "${ADMIN_PASSWORD}"; then
    if superset fab list-users 2>/dev/null | grep -qE "username:${ADMIN_USERNAME}( |\$)"; then
        echo "[init] Admin already exists. Synchronizing password..."
        superset fab reset-password --username "${ADMIN_USERNAME}" --password "${ADMIN_PASSWORD}"
    else
        echo "[init] ERROR: Failed to create or verify administrator user." >&2
        exit 1
    fi
fi

echo "[init] Synchronizing standard roles and permissions..."
superset init

echo "[init] Bootstrap completed successfully."

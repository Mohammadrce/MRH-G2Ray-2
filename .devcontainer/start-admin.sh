#!/bin/bash
set -euo pipefail

ADMIN_SCRIPT="/usr/local/bin/mrh-admin-server.py"

# Start admin server if not running
if ! pgrep -f "python3 ${ADMIN_SCRIPT}" >/dev/null; then
    nohup python3 "$ADMIN_SCRIPT" >/tmp/mrh-admin.log 2>&1 &
    sleep 1
    if ! pgrep -f "python3 ${ADMIN_SCRIPT}" >/dev/null; then
        echo "ERROR: Failed to start admin server" >&2
        cat /tmp/mrh-admin.log >&2
        exit 1
    fi
fi

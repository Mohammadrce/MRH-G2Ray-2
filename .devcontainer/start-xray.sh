#!/bin/bash
set -euo pipefail

UUID_FILE="${HOME}/.xray-uuid"

# Generate UUID if not exists
if [[ ! -f "$UUID_FILE" ]]; then
    cat /proc/sys/kernel/random/uuid > "$UUID_FILE"
fi
XRAY_UUID="$(cat "$UUID_FILE")"
export XRAY_UUID

XRAY_BIN="/usr/local/bin/xray"
XRAY_CONFIG="/tmp/config.runtime.json"
XRAY_PROCESS_PATTERN="${XRAY_BIN} -c ${XRAY_CONFIG}"

# Generate runtime config with UUID
python3 - <<'PY'
import json
import os
from pathlib import Path

config_path = Path("/etc/config.json")
runtime_path = Path("/tmp/config.runtime.json")
uuid_value = os.environ["XRAY_UUID"].strip()

try:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    data["inbounds"][0]["settings"]["clients"][0]["id"] = uuid_value
    runtime_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
except (json.JSONDecodeError, IOError) as e:
    print(f"Error generating config: {e}", file=sys.stderr)
    sys.exit(1)
PY

# Fetch public IP and generate xray-info.json
python3 - <<'PY'
import json
import os
import sys
import urllib.request
from pathlib import Path

def fetch_public_ip():
    """Fetch public IP from multiple sources with fallback."""
    urls = [
        "https://api.ipify.org",
        "https://ifconfig.me/ip",
        "https://icanhazip.com"
    ]
    for url in urls:
        try:
            with urllib.request.urlopen(url, timeout=5) as resp:
                return resp.read().decode().strip()
        except (OSError, ValueError):
            continue
    return ""

try:
    info_path = Path("/opt/mrh-admin/xray-info.json")
    info_data = {
        "uuid": os.environ["XRAY_UUID"],
        "path": "/",
        "remark": "ghtun",
        "server_ip": fetch_public_ip()
    }
    info_path.write_text(json.dumps(info_data, indent=2) + "\n", encoding="utf-8")
except IOError as e:
    print(f"Error writing xray-info.json: {e}", file=sys.stderr)
    sys.exit(1)
PY

# Start Xray if not running
if ! pgrep -f "$XRAY_PROCESS_PATTERN" >/dev/null; then
    if sudo -n true >/dev/null 2>&1; then
        sudo nohup "$XRAY_BIN" -c "$XRAY_CONFIG" >/tmp/xray.log 2>&1 &
    else
        nohup "$XRAY_BIN" -c "$XRAY_CONFIG" >/tmp/xray.log 2>&1 &
    fi
    sleep 1
    if ! pgrep -f "$XRAY_PROCESS_PATTERN" >/dev/null; then
        echo "ERROR: Failed to start Xray" >&2
        exit 1
    fi
fi

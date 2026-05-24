#!/bin/bash
set -euo pipefail

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

XRAY_VERSION="26.3.27"
XRAY_URL="https://github.com/XTLS/Xray-core/releases/download/v${XRAY_VERSION}/Xray-linux-64.zip"

echo "Downloading Xray v${XRAY_VERSION}..."
if ! wget -q --show-progress -O "${TMP_DIR}/xray.zip" "$XRAY_URL"; then
    echo "ERROR: Failed to download Xray" >&2
    exit 1
fi

echo "Installing Xray..."
if ! unzip -q "${TMP_DIR}/xray.zip" -d "${TMP_DIR}"; then
    echo "ERROR: Failed to extract Xray" >&2
    exit 1
fi

chmod +x "${TMP_DIR}/xray"
if ! mv "${TMP_DIR}/xray" /usr/local/bin/xray; then
    echo "ERROR: Failed to move Xray to /usr/local/bin" >&2
    exit 1
fi

echo "Xray v${XRAY_VERSION} installed successfully!"

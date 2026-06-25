#!/bin/bash
set -e

# NEXUS lives in a separate checkout. Override with NEXUS_DIR if it is
# somewhere else; the default assumes it sits next to the EVA repo.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${NEXUS_DIR:-$(cd "$SCRIPT_DIR/../../.." && pwd)/NEXUS}"

if [ ! -d "$APP_DIR" ]; then
    echo "NEXUS directory not found: $APP_DIR" >&2
    echo "Set NEXUS_DIR to the path of your NEXUS checkout." >&2
    exit 1
fi

cd "$APP_DIR"

# Check if virtual environment exists
if [ ! -d "$APP_DIR/venv" ]; then
    echo 'Virtual environment not found. Creating one...'
    python3.10 -m venv "$APP_DIR/venv"
    source "$APP_DIR/venv/bin/activate"
    echo 'Installing dependencies...'
    pip install --upgrade pip
    pip install -r "$APP_DIR/requirements.txt"
else
    source "$APP_DIR/venv/bin/activate"
fi

echo 'Starting NEXUS...'
# Use prime-run (Optimus/NVIDIA offload) only if available; fall back otherwise.
if command -v prime-run >/dev/null 2>&1; then
    exec prime-run make nexus
else
    exec make nexus
fi

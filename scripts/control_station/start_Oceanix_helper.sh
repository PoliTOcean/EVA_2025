#!/bin/bash
set -e

# Resolve the helper dir relative to this script (repo_root/helper),
# so it works regardless of username or where the repo is cloned.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="${HELPER_DIR:-$(cd "$SCRIPT_DIR/../../helper" && pwd)}"

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

echo 'Starting Python application...'
exec python main.py

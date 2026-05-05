#!/bin/bash

# Get absolute path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Run each script in background
"$SCRIPT_DIR/start_NEXUS.sh" &
"$SCRIPT_DIR/start_janus.sh" &
"$SCRIPT_DIR/start_Oceanix_helper.sh" &


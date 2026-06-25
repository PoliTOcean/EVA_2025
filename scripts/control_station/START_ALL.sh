#!/bin/bash

# Get absolute path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

LOG_DIR="$SCRIPT_DIR/logs"
mkdir -p "$LOG_DIR"

# Run each script in background, logging output to a file
"$SCRIPT_DIR/start_NEXUS.sh"          >"$LOG_DIR/nexus.log"   2>&1 &
NEXUS_PID=$!
"$SCRIPT_DIR/start_janus.sh"          >"$LOG_DIR/janus.log"   2>&1 &
JANUS_PID=$!
"$SCRIPT_DIR/start_Oceanix_helper.sh" >"$LOG_DIR/helper.log"  2>&1 &
HELPER_PID=$!

echo "Started:"
echo "  NEXUS  (pid $NEXUS_PID)  -> $LOG_DIR/nexus.log"
echo "  Janus  (pid $JANUS_PID)  -> $LOG_DIR/janus.log"
echo "  Helper (pid $HELPER_PID) -> $LOG_DIR/helper.log"
echo
echo "Tail logs with:  tail -f $LOG_DIR/*.log"
echo "Stop all with:   kill $NEXUS_PID $JANUS_PID $HELPER_PID"

# Wait so Ctrl-C here kills the children too
trap 'kill $NEXUS_PID $JANUS_PID $HELPER_PID 2>/dev/null' INT TERM
wait

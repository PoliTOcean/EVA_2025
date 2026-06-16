#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# main, right and bottom (exploreHD) share USB controller xhci-hcd.0. Opening
# them at the same instant causes USB contention and one fails to start, so the
# three are staggered. main goes first (no extra delay).
"$SCRIPT_DIR/wait_for_camera.sh" /dev/camera-main

# Pipeline ottimizzata per Janus (PC Base 10.0.0.69)
gst-launch-1.0 v4l2src device=/dev/camera-main ! \
  video/x-h264,width=1280,height=720,framerate=25/1 ! \
  h264parse ! \
  rtph264pay config-interval=1 pt=96 ! \
  udpsink host=10.0.0.69 port=5001 sync=false async=false

#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Staggered behind main to avoid USB contention on controller xhci-hcd.0.
sleep 2
"$SCRIPT_DIR/wait_for_camera.sh" /dev/camera-right

# Pipeline ottimizzata per Janus (PC Base 10.0.0.69)
gst-launch-1.0 v4l2src device=/dev/camera-right ! \
  video/x-h264,width=1280,height=720,framerate=25/1 ! \
  h264parse ! \
  rtph264pay config-interval=1 pt=96 ! \
  udpsink host=10.0.0.69 port=5002 sync=false async=false

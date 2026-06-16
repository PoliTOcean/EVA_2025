#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Staggered behind main and right to avoid USB contention on controller xhci-hcd.0.
sleep 4
"$SCRIPT_DIR/wait_for_camera.sh" /dev/camera-bottom

# Pipeline ottimizzata per Janus (PC Base 10.0.0.69)
# main, right and bottom share one USB 2.0 hub (480 Mbit/s). At 720p all three
# together saturate the bus ("Not enough bandwidth for altsetting" in dmesg),
# which makes the more-used main camera lag. bottom is the least used, so it
# runs at a lower resolution/framerate to free USB bandwidth for the others.
gst-launch-1.0 v4l2src device=/dev/camera-bottom ! \
  video/x-h264,width=640,height=480,framerate=20/1 ! \
  h264parse ! \
  rtph264pay config-interval=1 pt=96 ! \
  udpsink host=10.0.0.69 port=5003 sync=false async=false

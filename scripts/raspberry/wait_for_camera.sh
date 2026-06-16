#!/bin/bash
# Wait until a camera device is actually openable, not just present as a symlink.
#
# The udev symlink (/dev/camera-*) appears as soon as the kernel enumerates the
# USB device, but the camera may not yet answer to VIDIOC_* ioctls. Launching
# gst-launch too early - or launching the three exploreHD cameras on the same
# USB controller at the same instant - causes one of them to fail to open
# (USB resource contention). This helper probes the device with a real one-frame
# capture and retries until it succeeds.
#
# Usage: wait_for_camera.sh <device> [retries] [delay_s]

DEV="$1"
RETRIES="${2:-30}"
DELAY="${3:-1}"

# First wait for the symlink/node to exist at all.
until [ -e "$DEV" ]; do sleep "$DELAY"; done

# Then confirm the camera actually delivers a frame before we hand it to the
# real streaming pipeline.
for i in $(seq 1 "$RETRIES"); do
    if gst-launch-1.0 -q v4l2src device="$DEV" num-buffers=1 ! fakesink >/dev/null 2>&1; then
        exit 0
    fi
    sleep "$DELAY"
done

echo "wait_for_camera: $DEV did not become ready after $RETRIES attempts" >&2
exit 1

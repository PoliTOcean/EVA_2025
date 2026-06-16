#!/bin/bash

# Aspetta il device
until [ -e /dev/camera-bottom ]; do sleep 1; done

# Pipeline ottimizzata per Janus (PC Base 10.0.0.69)
gst-launch-1.0 v4l2src device=/dev/camera-bottom ! \
  video/x-h264,width=1280,height=720,framerate=25/1 ! \
  h264parse ! \
  rtph264pay config-interval=1 pt=96 ! \
  udpsink host=10.0.0.69 port=5003 sync=false async=false

#!/bin/bash

gst-launch-1.0 v4l2src device=/dev/camera-right ! \
  video/x-h264,width=1280,height=720,framerate=20/1 ! \
  h264parse ! queue ! rtph264pay config-interval=10 pt=96 ! \
  udpsink host=10.0.0.192 port=5002
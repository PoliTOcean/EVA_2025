#!/bin/bash

gst-launch-1.0 v4l2src device=/dev/camera-bottom ! \
  video/x-h264,width=1280,height=720,framerate=25/1 ! \
  h264parse ! queue ! rtph264pay config-interval=10 pt=100 ! \
  udpsink host=10.0.0.69 port=5003

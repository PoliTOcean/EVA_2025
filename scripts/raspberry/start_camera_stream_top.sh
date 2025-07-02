#!/bin/bash

gst-launch-1.0 v4l2src device=/dev/camera-top ! \
  image/jpeg,width=1600,height=1200,framerate=15/1 ! \
  jpegdec ! videoconvert ! x264enc \
  tune=zerolatency bitrate=3000 speed-preset=superfast ! \
  h264parse ! rtph264pay config-interval=1 pt=96 ! \
  udpsink host=10.0.0.192 port=5004

#!/bin/bash

gst-launch-1.0 v4l2src device=/dev/camera-arm ! \
  image/jpeg,width=800,height=600,framerate=30/1 ! \
  jpegdec  ! videoconvert ! x264enc \
  tune=zerolatency bitrate=3000 speed-preset=superfast ! \
  h264parse ! rtph264pay config-interval=1 pt=96 ! \
  udpsink host=10.0.0.192 port=5005

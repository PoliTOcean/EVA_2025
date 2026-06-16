#!/bin/bash

# Aspetta il device
until [ -e /dev/camera-arm ]; do sleep 1; done

# Pipeline specifica per Pi 5 (800x600 MJPEG -> H264)
gst-launch-1.0 v4l2src device=/dev/camera-arm do-timestamp=true ! \
  image/jpeg,width=800,height=600,framerate=30/1 ! \
  jpegdec ! \
  videoconvert ! \
  video/x-raw,format=I420 ! \
  x264enc tune=zerolatency bitrate=2000 speed-preset=ultrafast threads=4 ! \
  h264parse ! \
  rtph264pay config-interval=1 pt=96 ! \
  udpsink host=10.0.0.69 port=5004 sync=false async=false

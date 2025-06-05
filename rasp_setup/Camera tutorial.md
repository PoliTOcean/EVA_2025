# Linux Camera Systems

Cameras in Linux are seen as `/dev/video*`. They have different output formats and resolutions. To check the available formats, use the following command:

```bash
v4l2-ctl -d /dev/video0 --list-formats-ext
```

after the camera static link setup is best to use:

```bash
v4l2-ctl -d /dev/camera-main --list-formats-ext
```
also to check that the ATTR{index} is set up correctly.

## Camera Formats Explained

The formats can be MJPG or H264:

- **MJPG (Motion JPEG)**: A series of JPEG images sent in sequence. 
  - Pros: Higher quality, widely supported
  - Cons: Higher bandwidth usage, must be transcoded for efficient streaming
  - Must be encoded to H264 for efficient network streaming
  - May introduce lag on the client side due to decoding overhead
  - To stream in MJPG use ustreamer, easy to set up and easy to work with, also with the snapshots

- **H264**: A compressed video format
  - Pros: Already compressed, lower bandwidth, ready for Real-Time Communication (RTC)
  - Cons: May have slightly lower quality than MJPG at the same bitrate
  - DWE cameras can output compressed H264 natively and are streamed directly with DWE OS 2

## Camera Identification

To understand which camera is associated with a specific `/dev/video*`, use the following command:

```bash
v4l2-ctl --list-devices
```

This script will list all video devices and their corresponding camera models/types.


## Port Configuration and Janus Integration

Both DWE_OS_2 and GStreamer streams should target `127.0.0.1` (localhost), which is where Janus is running. The port selected for each camera stream must match the corresponding port defined in the Janus streaming configuration file (`janus.plugin.streaming.cfg`). In NEXUS, the different camera streams are then identified and displayed using their respective IDs configured in Janus.
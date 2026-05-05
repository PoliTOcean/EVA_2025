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

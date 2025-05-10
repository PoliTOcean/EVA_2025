# Setting up Camera Streaming with GStreamer and Janus WebRTC

This tutorial outlines the steps to set up camera streaming using GStreamer and Janus.

## Step 1: Install GStreamer

Install GStreamer and the necessary plugins on your Raspberry Pi:

```bash
sudo apt update
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly
```

## Step 2: Install Janus

Install GStreamer and the necessary plugins on your Raspberry Pi:

```bash
sudo apt update
sudo apt install -y janus
```

## Step 3: Create a GStreamer Pipeline

Create a GStreamer pipeline to capture video from the camera and stream it to Janus. Change the device and the port number.

```bash
gst-launch-1.0 -v v4l2src device=/dev/video0 ! \
image/jpeg,width=1600,height=1200,framerate=30/1 ! \
jpegdec !  videoconvert !   x264enc \
tune=zerolatency bitrate=5000 speed-preset=superfast ! \
h264parse !  rtph264pay config-interval=1 pt=96 ! \
udpsink host=127.0.0.1 port=5001

```

**Explanation:**

*   `v4l2src`: Captures video from the camera device `/dev/video0`.
*   `image/jpeg,width=640,height=480,framerate=30/1`: Specifies the video format.
*   `jpegdec`: Decodes the JPEG stream.
*   `videoconvert`: Converts the video format.
*   `x264enc`: Encodes the video using H.264.
*   `rtph264pay`: Packages the H.264 stream into RTP packets.
*   `udpsink`: Sends the RTP packets to the specified host and port.

## Step 4: Install and Configure DWE OS

DWE OS provides an alternative method for streaming H.264 encoded video directly from compatible cameras.

First, install DWE OS using the following commands:

```bash
curl -s https://raw.githubusercontent.com/DeepwaterExploration/DWE_OS_2/main/install.sh | sudo bash -s
```

After installation, access the DWE OS interface by navigating to the Raspberry Pi's IP address in a web browser (e.g., `http://<rasp_ip>`). You should see the connected camera(s) listed.

For each camera:

1.  Select `127.0.0.1` (localhost) as the endpoint.
2.  Enter the corresponding port number that you've configured in the Janus streaming configuration file (`janus.plugin.streaming.cfg`).
3.  Choose a suitable quality setting; "HD" is generally a good balance.

## Step 5: Configure Janus

Configure Janus to receive the video stream.

**Example `janus.plugin.streaming.cfg` configuration:**

```json
[gst-rpipeline]
type = rtp
id = 1
description = H264 USB Camera
audio = no
video = yes
videoport = 5004
videopt = 96
videortpmap = H264/90000
videofmtp = profile-level-id=42e01f;packetization-mode=1

[gst-camera-2]
type = rtp
id = 2
description = USB Camera 2 (H264)
audio = no
video = yes
videoport = 5006
videopt = 96
videortpmap = H264/90000
videofmtp = profile-level-id=42e01f;packetization-mode=1

[gst-camera-180]
type = rtp
id = 3
description = USB Camera 3 (MJPEG)
audio = no
video = yes
videoport = 5002
videopt = 96
videortpmap = H264/90000
videofmtp = profile-level-id=42e01f;packetization-mode=1


[gst-camera-4]
type = rtp
id = 4
description = USB Camera 4 (MJPEG)
audio = no
video = yes
videoport = 5001
videopt = 96
videortpmap = H264/90000
videofmtp = profile-level-id=42e01f;packetization-mode=1
```

## Step 6: Start Janus

Start the Janus server:

```bash
sudo systemctl restart janus
```
# Setting up Camera Streaming with GStreamer and Janus WebRTC

This tutorial outlines the steps to set up camera streaming using GStreamer and Janus.
Gstreamer is used to stream the camera using RTP protocol in H.264 encoding to the control station. On the control station the Janus server create the WebRTC access point for all apps.
Janus server is installed on the control station and not on the Raspberry Pi to avoid overloading it, while the latency remains the same.

## Step 1: Install GStreamer on Raspberry Pi

Install GStreamer and the necessary plugins on your Raspberry Pi:

```bash
sudo apt update
sudo apt install -y gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly
```

## Step 2: Install Janus on Control station

Use the installation script you can find in scripts/ to install Janus from source. Download the install_janus.sh and the janus.plugin.streaming.jcfg file which contain the streaming configuration

```bash
cd scripts/
chmod +x ./install_janus.sh && ./install_janus.sh
```

Good luck with the configuration of Janus, at beginning may not be easy, the most important file to modify is "${JANUS_CONFIG_DIR}/janus.jcfg", if nothing is working probably the problem is here.

## Step 3: Install and Configure DWE OS 2

DWE OS 2 provides an alternative method for streaming H.264 encoded video directly from compatible cameras. Streaming directly with DWE OS often caused unexpected lag, install it only for controlling camera parameters such as brighness ecc.

First, install DWE OS using the following commands:

```bash
curl -s https://raw.githubusercontent.com/DeepwaterExploration/DWE_OS_2/main/install.sh | sudo bash -s
```

After installation, access the DWE OS interface by navigating to the Raspberry Pi's IP address in a web browser (e.g., `http://<rasp_ip>`). You should see the connected camera(s) listed.
This is only used for changing camera parameters, all camera are streamed using custom pipelines to ensure the best latency.

## Step 4: Configure the streaming pipeline

Copy all the start_camera_stream_'camera'.sh scripts (and the shared `wait_for_camera.sh` helper) in a folder on the Raspberry Pi. If you execute manually and Janus is already configured you shoud see from janus that the camera stream are found. Remember to change the IP in the scripts to the Control Station LAN IP.
There are four cameras: main, right, bottom and arm. The resolution, bitrate and framerate ensure that the streaming does not overload the Raspberry Pi nor the shared USB bus. However they can be changed with other supported resolutions, you can see the list with v4l2-ctl -d "camera" --list-formats-ext (Camera tutorial).

The scripts use `wait_for_camera.sh` to wait until each device is actually openable (not just present as a udev symlink), and main/right/bottom are started staggered (right +2s, bottom +4s) because they share one USB controller and opening them simultaneously causes USB contention.

To launch directly the script:
```bash
chmod +x ./start_camera_stream_main.sh && ./start_camera_stream_main.sh
```

If the test is passed now configura automatic stream at startup with systemctl service.

*   Create the `camera_stream_main.service` file in `/etc/systemd/system/`:

    ```bash
    sudo nano /etc/systemd/system/camera_stream_main.service
    ```

*   Add the following content to the `camera_stream_main.service` file:

    ```
    [Unit]
    Description=Camera Stream Service
    After=network.target
    StartLimitIntervalSec=60
    StartLimitBurst=3

    [Service]
    Type=simple
    ExecStart=/home/politocean/firmware/start_camera_stream_main.sh

    Restart=on-failure
    RestartSec=5

    StartLimitAction=none
    TimeoutStartSec=20

    User=root
    Environment=DISPLAY=:0
    Environment=XAUTHORITY=/home/politocean/.Xauthority

    [Install]
    WantedBy=multi-user.target
    ```

*   **Important:** Verify that the `ExecStart` path is correct: you must put the script absolute path.

*   Enable the service:

    ```bash
    sudo systemctl enable camera_stream_main.service
    ```

*   restart (or start) the service:

    ```bash
    sudo systemctl restart camera_stream_main.service
    ```

    Repeat all the steps for each camera

## Troubleshooting

### A camera lags or never starts at power-on (until you unplug/replug)
main, right and bottom (the exploreHD cameras) are on the same USB controller. If their pipelines open at the exact same instant, one fails to open due to USB resource contention. The fix is already in the scripts: `wait_for_camera.sh` probes the device with a real one-frame capture before streaming, and right/bottom are staggered behind main. If it still happens, increase the `sleep` values in `start_camera_stream_right.sh` (+2s) and `start_camera_stream_bottom.sh` (+4s).

### The main feed lags intermittently during use
The three exploreHD cameras share a single USB 2.0 hub (480 Mbit/s). At 720p all three together saturate the bus; check with:

```bash
sudo dmesg | grep -iE "bandwidth|altsetting"
```

If you see `Not enough bandwidth for altsetting`, the bus is saturated. Lower the resolution/framerate of the least-used camera (bottom is already at 640x480@20 for this reason), or move one camera to a different USB controller (and update its udev rule, see [Camera static link](./Camera%20static%20link.md)).

### Frozen / laggy frames on the control station side
Bursty RTP can overflow the UDP receive buffer on the control station, dropping packets. Check the `RcvbufErrors` counter (5th number) — if it keeps growing while streaming, the buffer is too small:

```bash
grep Udp: /proc/net/snmp
```

The fix is shipped as `scripts/control_station/99-janus-udp.conf` and applied automatically by `install_janus.sh`. To apply it manually:

```bash
sudo cp scripts/control_station/99-janus-udp.conf /etc/sysctl.d/
sudo sysctl --system
```

Then restart Janus so it reopens its sockets with the larger buffer.

### Wrong video in the browser / WebRTC won't connect
Janus must advertise the control station LAN IP, not WiFi. `install_janus.sh` sets `nat_1_1_mapping` to the LAN IP (`CONTROL_STATION_LAN_IP`) in `janus.jcfg`. Verify the running log shows the correct IP; if Janus picks a WiFi/other address, check that setting.

### `start_janus.sh` errors with a gnome-terminal symbol lookup
`start_janus.sh` runs Janus directly in the current terminal (no gnome-terminal), which avoids the snap library conflict. Stop it with `Ctrl+C`.

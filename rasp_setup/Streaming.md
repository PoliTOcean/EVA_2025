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

## Step 3: Install and Configure DWE OS 2

DWE OS 2 provides an alternative method for streaming H.264 encoded video directly from compatible cameras. Streaming directly with DWE OS often caused unexpected lag, install it only for controlling camera parameters such as brighness ecc.

First, install DWE OS using the following commands:

```bash
curl -s https://raw.githubusercontent.com/DeepwaterExploration/DWE_OS_2/main/install.sh | sudo bash -s
```

After installation, access the DWE OS interface by navigating to the Raspberry Pi's IP address in a web browser (e.g., `http://<rasp_ip>`). You should see the connected camera(s) listed.

## Step 4: Configure the streaming pipeline

Copy all the start_camera_stream_'camera'.sh scripts in a folder on the Raspberry Pi. If you execute manually and Janus is already configured you shoud see from janus that the camera stream are found. Remember to change the IP in the scripts to the Control Station LAN IP.
The resolution, bitrate and framerate ensure that the streaing of the 5 cameras does not overload the Raspberry Pi. However can be changed with other supported resolution, you can see the list with v4l2-ctl -d "camera" --list-formats-ext (Camera tutorial).

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

    [Service]
    ExecStart=/home/politocean/firmware/start_camera_stream_main.sh
    Restart=always
    RestartSec=5
    User=root
    Environment=DISPLAY=:0
    Environment=XAUTHORITY=/home/pi/.Xauthority

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

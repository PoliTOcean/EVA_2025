# Raspberry Pi Setup - EVA 2025

This directory contains guides and instructions for setting up the Raspberry Pi for the EVA 2025 project.

## Installation Overview

1.  **Camera Setup**:
    *   Configure the four cameras (main, right, bottom, arm) in Linux.
    *   Understand camera formats (MJPG, H264).
    *   Set static device symlinks per USB port (udev).
    *   Stream video using GStreamer or DWE OS.
    *   Integrate with Janus WebRTC server.

2.  **Janus WebRTC Server**:
    *   Install and configure Janus for video streaming (`install_janus.sh`
        also sets `nat_1_1_mapping` to the control station LAN IP and installs
        the UDP buffer tuning).
    *   Set up streaming plugins.
    *   See the Troubleshooting section in [Streaming](./Streaming.md) if feeds lag.

3.  **Oceanix**:
    *   Install the Oceanix software.
    *   Enable I2C.
    *   Configure automatic execution using systemd.

## Guides

*   [Camera tutorial](./Camera%20tutorial.md): Explains how cameras work in Linux.
*   [Camera_stati_link](./Camera%20static%20link.md): Explains how to set static devices for cameras (IMPORTANT!).
*   [Streaming](./Streaming.md): Details how to set up camera streaming with GStreamer and Janus.
*   [Snapshots](./Camera%20snapshot.md): How snapshots from cameras cam be taken.
*   [Static_IP](./Set%20static%20IP.md): Provides instructions for setting a static IP on the raspberry.
*   [Install Oceanix](./Install%20Oceanix.md): Provides instructions for installing Oceanix.

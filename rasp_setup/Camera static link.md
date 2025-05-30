## 🎯 **Goal**

Instead of dealing with changing `/dev/video4`, `/dev/video6`, etc., we want:

```bash
/dev/camera-bottom
/dev/camera-top
/dev/camera-main
/dev/camera-right
/dev/camera-arm
```

that always point to the correct camera, based on which USB port it’s plugged into.

---

## 🧰 Prerequisites

Make sure you have:

* `v4l-utils` installed (for `v4l2-ctl`)
* root access (`sudo`)

If not already installed:

```bash
sudo apt update
sudo apt install v4l-utils
```

---

## 📝 Step 1: List Video Devices

List your connected cameras and the video devices they expose:

```bash
v4l2-ctl --list-devices
```

You'll see output like:

```
HD USB CAMERA: HD USB CAMERA (usb-xhci-hcd.0-2.2):
    /dev/video4
    /dev/video5

exploreHD USB Camera: exploreHD (usb-xhci-hcd.0-2.4):
    /dev/video8
    /dev/video9
```

exploreHD USB Cameras are managed by DWE OS that already uses static path, so ignore these cameras in this tutorial

---

## 🔍 Step 2: Find the `ID_PATH` for the Correct Device

Pick the device that corresponds to the **stream you want to use** (e.g. `/dev/video4`), then run:

```bash
udevadm info /dev/video4 | grep ID_PATH
```

You'll get something like:

```
E: ID_PATH=platform-xhci-hcd.0-usb-0:2.2:1.0
```

Write that down — that's the stable ID of that USB port.

Repeat this for all cameras you want to assign.

---

## 🧩 Step 3: Create a udev Rule File

Create a new udev rules file:

```bash
sudo nano /etc/udev/rules.d/99-usb-cameras.rules
```

Add one line per camera, like this:

```udev
# Bottom camera
SUBSYSTEM=="video4linux", ENV{ID_PATH}=="platform-xhci-hcd.0-usb-0:2.2:1.0", ATTR{index}=="0", SYMLINK+="camera-bottom"

# Top camera
SUBSYSTEM=="video4linux", ENV{ID_PATH}=="platform-xhci-hcd.0-usb-0:2.3:1.0", ATTR{index}=="0", SYMLINK+="camera-top"
```

📌 **Make sure you adjust the `ID_PATH` values** to the correct ones from your own system.
the ATTR{index}=="0" is to make sure we are selecting the right interface of the camera, for the DWE camera the index is 2 to use H.264

---

## 🔄 Step 4: Reload udev and Trigger

```bash
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Then check:

```bash
ls -l /dev/camera-*
```

You should see:

```
/dev/camera-bottom -> video4
/dev/camera-top -> video6
...
```

🎉 Done!
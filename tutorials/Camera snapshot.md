# Camera Snapshot Tutorial

This tutorial explains how to capture snapshots from cameras in the EVA system. There are two main approaches, each with different advantages and use cases.

## Overview

The EVA system supports two methods for taking camera snapshots:

1. **WebRTC Stream Snapshots** - Fast, simultaneous capture from compressed streams
2. **Direct Camera Snapshots** - Higher quality capture directly from camera hardware

## Method 1: WebRTC Stream Snapshots

### Description
This method captures snapshots from the WebRTC streaming feed. While the image quality is lower due to compression, it allows for instantaneous capture from multiple cameras simultaneously.

### Use Cases
- **Stereo camera operations** where simultaneity of both photos is essential
- Real-time applications requiring immediate capture
- When network bandwidth is limited

### How it Works
- Connects to Janus WebRTC gateway
- Receives compressed video streams
- Captures frames directly from the stream
- Processes multiple streams simultaneously

### Implementation
A Flask server runs locally on the computer and:
- Connects to the Janus WebRTC server
- Receives all camera streaming feeds
- Provides API endpoints for snapshot capture

**Repository:** [[WebRTC snapshot repo](https://github.com/PoliTOcean/snapshot-WebRTC)]

### Advantages
- ✅ Instantaneous capture
- ✅ Simultaneous multi-camera snapshots
- ✅ No interruption to streaming

### Disadvantages
- ❌ Lower image quality (compressed stream)
- ❌ Limited by streaming resolution

## Method 2: Direct Camera Snapshots

### Description
This method captures photos directly from the camera hardware, providing higher quality images at the cost of sequential processing and potential streaming interruption.

### Use Cases
- High-quality image capture requirements
- Documentation and detailed analysis
- When image quality is more important than speed

### How it Works
The snapshot server (Flask-based) runs on each Raspberry Pi and directly accesses the camera hardware.

#### DWE Cameras
- Expose a secondary MJPEG device for snapshots
- H.264 video streaming continues uninterrupted
- Multiple photos are taken sequentially due to Raspberry Pi limitations

#### Other MJPEG Cameras
- Streaming process is temporarily stopped
- High-quality photo is captured
- Streaming resumes after capture
- Causes brief lag in NEXUS during photo capture

### Implementation
**Repository:** [[snapshot server repo](https://github.com/PoliTOcean/Snapshot-server)]

### Advantages
- ✅ Higher image quality
- ✅ Direct hardware access
- ✅ Full camera resolution available

### Disadvantages
- ❌ Sequential capture only (Raspberry Pi limitation)
- ❌ Potential streaming interruption (MJPEG cameras)
- ❌ Brief lag in NEXUS interface

## Choosing the Right Method

| Requirement | WebRTC Snapshots | Direct Snapshots |
|-------------|------------------|------------------|
| High image quality | ❌ | ✅ |
| Simultaneous capture | ✅ | ❌ |
| No streaming interruption | ✅ | Depends on camera |
| Real-time applications | ✅ | ❌ |
| Stereo vision | ✅ | ❌ |

## Technical Architecture

### WebRTC Method
```
Computer → Janus Gateway → Camera Streams → Flask Server → Snapshot API
```

### Direct Method
```
Raspberry Pi → Camera Hardware → Flask Server → Snapshot API
```

## Getting Started

1. **For WebRTC snapshots:** Set up the local Flask server and connect to Janus
2. **For direct snapshots:** Deploy the snapshot server to each Raspberry Pi
3. Choose the appropriate method based on your quality vs. speed requirements

## Repository Links

- **WebRTC Snapshot Server:** [[repo](https://github.com/PoliTOcean/snapshot-WebRTC)]
- **Direct Snapshot Server:** [[repo](https://github.com/PoliTOcean/Snapshot-server)]

---

*Note: The choice between methods depends on your specific use case. For stereo vision applications, WebRTC snapshots are essential due to the simultaneity requirement. For single high-quality captures, direct camera snapshots provide superior image quality.*

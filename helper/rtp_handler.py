import cv2
import os
from datetime import datetime

class RTPStreamHandler:
    def __init__(self):
        self.stream_ports = [5000, 5001, 5002, 5003, 5004]
        self.streams = {port: None for port in self.stream_ports}

    def start_stream(self, port):
        """Start capturing from an RTP stream on the given port using GStreamer pipeline."""
        if port not in self.stream_ports:
            raise ValueError(f"Invalid port: {port}. Valid ports are {self.stream_ports}.")
        gst_pipeline = (
            f'udpsrc port={port} caps="application/x-rtp, media=video, encoding-name=H264, payload=96" '
            '! rtph264depay ! avdec_h264 ! videoconvert ! appsink'
        )
        self.streams[port] = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)

    def stop_stream(self, port):
        """Stop capturing from an RTP stream on the given port."""
        if port in self.streams and self.streams[port]:
            self.streams[port].release()
            self.streams[port] = None

    def take_snapshot(self, port, timestamp=None):
        """Take a snapshot from the RTP stream on the given port."""
        if port not in self.stream_ports:
            raise ValueError(f"Invalid port: {port}. Valid ports are {self.stream_ports}.")
        if not self.streams[port]:
            self.start_stream(port)

        ret, frame = self.streams[port].read()
        if not ret:
            raise RuntimeError(f"Failed to capture frame from port {port}.")

        # Save the snapshot
        folder_path = os.path.join("photos", f"camera_{port}")
        os.makedirs(folder_path, exist_ok=True)
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(folder_path, f"{timestamp}.jpg")
        cv2.imwrite(file_path, frame)
        print(f"Snapshot saved to {file_path}")
        return file_path

    def stop_all_streams(self):
        """Stop all active RTP streams."""
        for port in self.stream_ports:
            self.stop_stream(port)

import cv2
import os
import subprocess
import numpy as np
import platform
from datetime import datetime

class RTPStreamHandler:
    def __init__(self):
        self.stream_ports = [5001, 5002, 5003, 5004, 5005]
        self.streams = {port: None for port in self.stream_ports}
        # Check GStreamer support
        self.has_gstreamer = self._check_gstreamer_support()
        if not self.has_gstreamer:
            print("WARNING: OpenCV not built with GStreamer support. RTP capture may not work.")
        
        # Create directory for SDP files if it doesn't exist
        self.sdp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sdp_files")
        os.makedirs(self.sdp_dir, exist_ok=True)
        
        # Known working stream info
        self.stream_info = {
            # Default values based on test
            'width': 1920,
            'height': 1080,
            'framerate': 30
        }

    def _check_gstreamer_support(self):
        """Check if OpenCV is built with GStreamer support"""
        # Check if OpenCV has GStreamer support
        build_info = cv2.getBuildInformation()
        has_gstreamer = "GStreamer" in build_info and "YES" in build_info.split("GStreamer:")[1].split("\n")[0]
        
        # Also check if gst-launch is available
        gst_available = False
        try:
            if platform.system() == "Windows":
                # Check for Windows gst-launch
                result = subprocess.run(["where", "gst-launch-1.0"], capture_output=True, text=True)
                gst_available = result.returncode == 0
            else:
                # Check for Unix-like gst-launch
                result = subprocess.run(["which", "gst-launch-1.0"], capture_output=True, text=True)
                gst_available = result.returncode == 0
        except Exception:
            gst_available = False
            
        print(f"OpenCV GStreamer support: {has_gstreamer}")
        print(f"GStreamer command line tools: {gst_available}")
        
        return has_gstreamer

    def _create_sdp_file(self, port, ip_address="0.0.0.0"):
        """Create an SDP file for the specified port with known video parameters"""
        sdp_content = f"""v=0
o=- 0 0 IN IP4 {ip_address}
s=RTP Stream on port {port}
c=IN IP4 {ip_address}
t=0 0
a=tool:libavformat 61.7.100
m=video {port} RTP/AVP 96
a=rtpmap:96 H264/90000
a=fmtp:96 packetization-mode=1; profile-level-id=42e01f
a=framerate:{self.stream_info['framerate']}
"""
        sdp_path = os.path.join(self.sdp_dir, f"stream_{port}.sdp")
        with open(sdp_path, "w") as f:
            f.write(sdp_content)
        print(f"Created SDP file: {sdp_path}")
        return sdp_path

    def start_stream(self, port):
        """Start capturing from an RTP stream on the given port using ffmpeg as fallback."""
        if port not in self.stream_ports:
            raise ValueError(f"Invalid port: {port}. Valid ports are {self.stream_ports}.")
        
        # Try GStreamer method first if available
        if self.has_gstreamer:
            gst_pipeline = (
                f'udpsrc port={port} caps="application/x-rtp, media=video, encoding-name=H264, payload=96" '
                '! rtph264depay ! avdec_h264 ! videoconvert ! appsink'
            )
            
            print(f"Opening stream with GStreamer pipeline: {gst_pipeline}")
            cap = cv2.VideoCapture(gst_pipeline, cv2.CAP_GSTREAMER)
            
            if cap.isOpened():
                self.streams[port] = cap
                return True
        
        # Fallback to ffmpeg (check if installed)
        try:
            subprocess.run(["which", "ffmpeg"], check=True, capture_output=True)
            print(f"GStreamer not available. Using ffmpeg fallback for RTP stream on port {port}")
            # We'll use ffmpeg when taking the snapshot, not keeping a continuous stream open
            self.streams[port] = f"ffmpeg_rtp_{port}"  # Just a marker that we're using ffmpeg
            return True
        except subprocess.CalledProcessError:
            raise RuntimeError(
                "Neither GStreamer nor ffmpeg are available. Cannot capture RTP streams.\n"
                "Please install either GStreamer or ffmpeg to continue."
            )

    def stop_stream(self, port):
        """Stop capturing from an RTP stream on the given port."""
        if port in self.streams and self.streams[port]:
            self.streams[port].release()
            self.streams[port] = None

    def preview_stream(self, port):
        """Open an ffplay window to preview the stream"""
        if port not in self.stream_ports:
            raise ValueError(f"Invalid port: {port}. Valid ports are {self.stream_ports}.")
        
        # Create SDP file
        sdp_path = self._create_sdp_file(port)
        
        # Construct ffplay command
        preview_cmd = [
            "ffplay",
            "-protocol_whitelist", "file,rtp,udp",
            "-fflags", "nobuffer",   # Reduce latency
            "-flags", "low_delay",   # Reduce latency
            "-framedrop",           # Allow frame dropping if needed
            "-i", sdp_path
        ]
        
        # Launch ffplay in a separate process (non-blocking)
        print(f"Launching preview with command: {' '.join(preview_cmd)}")
        try:
            subprocess.Popen(preview_cmd)
            return True
        except Exception as e:
            raise RuntimeError(f"Failed to start preview: {str(e)}")

    def take_snapshot(self, port, timestamp=None):
        """Take a snapshot from the RTP stream on the given port."""
        if port not in self.stream_ports:
            raise ValueError(f"Invalid port: {port}. Valid ports are {self.stream_ports}.")
        
        # Create folder for saving snapshots
        folder_path = os.path.join("photos", f"camera_{port}")
        os.makedirs(folder_path, exist_ok=True)
        
        if not timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(folder_path, f"{timestamp}.jpg")
        
        # Start the stream if not already started
        if not self.streams.get(port):
            self.start_stream(port)
        
        # If using GStreamer backend (regular OpenCV)
        if isinstance(self.streams[port], cv2.VideoCapture):
            # Try to grab a frame first (this is more immediate than read())
            grab_success = self.streams[port].grab()
            if not grab_success:
                raise RuntimeError(f"Failed to grab frame from port {port}.")
            
            ret, frame = self.streams[port].retrieve()
            if not ret or frame is None:
                raise RuntimeError(f"Retrieved frame is invalid from port {port}.")
                
            if frame.size == 0:
                raise RuntimeError("Captured frame is empty (zero size).")
                
            save_success = cv2.imwrite(file_path, frame)
            if not save_success:
                raise RuntimeError(f"Failed to save image to {file_path}")
        
        # If using ffmpeg fallback
        elif str(self.streams[port]).startswith("ffmpeg_rtp_"):
            try:
                # Create SDP file for this port
                sdp_path = self._create_sdp_file(port)
                
                # First, try to verify stream is active (similar to preview)
                print(f"Testing if RTP stream is active on port {port}...")
                probe_cmd = [
                    "ffprobe",
                    "-v", "error",
                    "-show_entries", "stream=width,height,codec_name",
                    "-protocol_whitelist", "file,rtp,udp",
                    "-i", sdp_path,
                    "-max_probe_time", "3",  # 3 seconds max
                    "-probesize", "5000000"  # 5MB probe size
                ]
                
                try:
                    # Just check if stream is decodable
                    probe_result = subprocess.run(
                        probe_cmd,
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    print(f"ffprobe result: {probe_result.returncode}")
                    print(f"ffprobe output: {probe_result.stdout}")
                    print(f"ffprobe stderr: {probe_result.stderr}")
                except subprocess.TimeoutExpired:
                    # Timeout is actually OK - means stream is flowing
                    print("ffprobe timed out - stream is likely active")
                    pass

                # Create a temporary ts file first (TS container has better error recovery)
                temp_ts_file = os.path.join(folder_path, f"temp_{timestamp}.ts")
                
                # Use ffmpeg with SDP file to capture a short segment of video
                # This method is more reliable than trying to grab just one frame
                capture_cmd = [
                    "ffmpeg", 
                    "-protocol_whitelist", "file,rtp,udp",
                    "-i", sdp_path,
                    "-t", "2",  # Capture 2 seconds of video
                    "-vsync", "2",  # Passthrough vsync mode
                    "-c:v", "copy",  # Don't re-encode, just copy
                    "-y",  # Overwrite output without asking
                    temp_ts_file
                ]
                
                print(f"Running ffmpeg capture command: {' '.join(capture_cmd)}")
                
                # Run ffmpeg with a timeout - this captures a segment of the stream
                result = subprocess.run(
                    capture_cmd, 
                    capture_output=True, 
                    text=True, 
                    timeout=10  # 10 second timeout
                )
                
                if result.returncode != 0:
                    detailed_error = f"ffmpeg capture failed with error code {result.returncode}:\n" 
                    detailed_error += f"STDOUT: {result.stdout}\n"
                    detailed_error += f"STDERR: {result.stderr}\n\n"
                    detailed_error += "Possible solutions:\n"
                    detailed_error += "1. Ensure the camera is actually streaming H.264 to this port\n"
                    detailed_error += f"2. Try previewing the stream with: ffplay -protocol_whitelist file,rtp,udp -i {sdp_path}\n"
                    detailed_error += "3. Check for network issues or firewall restrictions"
                    
                    raise RuntimeError(detailed_error)
                
                # Now extract the first good frame from the captured segment
                extract_cmd = [
                    "ffmpeg",
                    "-i", temp_ts_file,
                    "-vframes", "1",  # Extract one frame
                    "-q:v", "1",  # Highest quality
                    "-y",
                    file_path
                ]
                
                print(f"Extracting frame with command: {' '.join(extract_cmd)}")
                
                extract_result = subprocess.run(
                    extract_cmd,
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                # Clean up temporary file
                try:
                    os.remove(temp_ts_file)
                except OSError:
                    pass
                
                if extract_result.returncode != 0:
                    raise RuntimeError(f"Failed to extract frame: {extract_result.stderr}")
                
                # Verify the final image was created successfully
                if not os.path.exists(file_path) or os.path.getsize(file_path) < 1000:  # Minimum size check
                    raise RuntimeError("Extracted image is too small or not created")
                
            except subprocess.TimeoutExpired as e:
                raise RuntimeError(
                    f"ffmpeg timed out: {str(e)}.\n"
                    "This usually means no video data is being received on port " + str(port) + ".\n"
                    f"Try previewing the stream first with: ffplay -protocol_whitelist file,rtp,udp -i {sdp_path}"
                )
            except Exception as e:
                raise RuntimeError(f"Snapshot error: {str(e)}")
        
        print(f"Snapshot saved to {file_path}")
        return file_path

    def stop_all_streams(self):
        """Stop all active RTP streams."""
        for port in self.stream_ports:
            self.stop_stream(port)

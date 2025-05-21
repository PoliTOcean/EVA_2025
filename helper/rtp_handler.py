import os
import subprocess
import platform # Keep platform for _check_ffmpeg_availability
from datetime import datetime
# Removed cv2 and numpy imports as they are not used if GStreamer path is removed
import time # Added for retry delay

class RTPStreamHandler:
    def __init__(self):
        self.stream_ports = [5001, 5002, 5003, 5004, 5005]
        self.streams = {port: None for port in self.stream_ports} # Will mark if ffmpeg is to be used
        
        # Check ffmpeg availability
        self.has_ffmpeg = self._check_ffmpeg_availability()
        if not self.has_ffmpeg:
            raise RuntimeError("ffmpeg is not installed or not found in PATH. Cannot capture RTP streams.")

        # Create directory for SDP files if it doesn't exist
        self.sdp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sdp_files")
        os.makedirs(self.sdp_dir, exist_ok=True)
        
        # Known working stream info
        self.stream_info = {
            'width': 1080,
            'height': 720,
            'framerate': 30
        }

    def _check_ffmpeg_availability(self):
        """Check if ffmpeg is installed and accessible."""
        try:
            # Use 'where' on Windows and 'which' on Unix-like systems
            command = "where" if platform.system() == "Windows" else "which"
            subprocess.run([command, "ffmpeg"], check=True, capture_output=True)
            print("ffmpeg found.")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("ffmpeg not found.")
            return False

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
        """Mark that ffmpeg will be used for this port."""
        if port not in self.stream_ports:
            raise ValueError(f"Invalid port: {port}. Valid ports are {self.stream_ports}.")
        
        if not self.has_ffmpeg:
             raise RuntimeError("ffmpeg is not installed. Cannot capture RTP streams.")
        
        # Mark that ffmpeg will be used for this port. No actual stream is started here.
        self.streams[port] = f"ffmpeg_rtp_{port}" 
        print(f"ffmpeg will be used for snapshots on port {port}")
        return True

    def stop_stream(self, port):
        """Placeholder as ffmpeg calls are per-snapshot."""
        if port in self.streams:
            self.streams[port] = None # Reset the marker

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

    def take_snapshot(self, port, timestamp=None, silent=False): # Added silent parameter
        """Take a snapshot from the RTP stream on the given port using ffmpeg directly to JPG."""
        if port not in self.stream_ports:
            raise ValueError(f"Invalid port: {port}. Valid ports are {self.stream_ports}.")
        
        if not self.has_ffmpeg:
            raise RuntimeError("ffmpeg is not installed. Cannot capture RTP streams.")

        # Create folder for saving snapshots
        folder_path = os.path.join("photos", f"camera_{port}")
        os.makedirs(folder_path, exist_ok=True)
        
        current_time = datetime.now()
        if not timestamp:
            timestamp_str = current_time.strftime("%Y%m%d_%H%M%S_%f") # Add microseconds for uniqueness
        else:
            timestamp_str = f"{timestamp}_p{port}_{current_time.strftime('%f')}"

        file_path = os.path.join(folder_path, f"{timestamp_str}.jpg")
        
        if not self.streams.get(port) or not str(self.streams[port]).startswith("ffmpeg_rtp_"):
            self.start_stream(port)

        sdp_path_for_cleanup = None

        try:
            sdp_filename = f"stream_{port}_{current_time.strftime('%Y%m%d%H%M%S%f')}.sdp"
            sdp_path = os.path.join(self.sdp_dir, sdp_filename)
            sdp_path_for_cleanup = sdp_path
            
            sdp_content = f"""v=0
o=- 0 0 IN IP4 0.0.0.0
s=RTP Stream on port {port}
c=IN IP4 0.0.0.0
t=0 0
a=tool:libavformat 61.7.100
m=video {port} RTP/AVP 96
a=rtpmap:96 H264/90000
a=fmtp:96 packetization-mode=1; profile-level-id=42e01f
a=framerate:{self.stream_info['framerate']}
"""
            with open(sdp_path, "w") as f:
                f.write(sdp_content)
            print(f"Created unique SDP file for snapshot: {sdp_path}")

            # Direct capture to JPG
            capture_cmd = [
                "ffmpeg",
                "-protocol_whitelist", "file,rtp,udp",
                "-i", sdp_path,
                "-frames:v", "1",  # Capture a single video frame
                "-q:v", "2",       # Output quality for JPG (1-31, lower is better)
                "-y",              # Overwrite output file if it exists
                file_path
            ]
            
            max_retries = 100 
            initial_retry_delay = 0.5 
            retry_delay_increment = 0.1 
            
            capture_success = False
            last_capture_result = None

            for attempt in range(max_retries):
                print(f"Running ffmpeg direct snapshot command for port {port} (attempt {attempt + 1}/{max_retries}): {' '.join(capture_cmd)}")
                # Increased timeout as establishing connection and capturing one frame might take a moment
                last_capture_result = subprocess.run(capture_cmd, capture_output=True, text=True, timeout=15) 
                
                if last_capture_result.returncode == 0:
                    # Check if the file was created and has a reasonable size
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 1000: # Check for >1KB size
                        capture_success = True
                        break # Success
                    else:
                        # ffmpeg might return 0 but fail to produce a valid file in some edge cases
                        print(f"ffmpeg command succeeded (port {port}, attempt {attempt + 1}) but output file '{file_path}' is invalid or too small.")
                        # Continue to retry if attempts are left
                
                if "bind failed: Address already in use" in last_capture_result.stderr:
                    if attempt < max_retries - 1:
                        current_delay = initial_retry_delay + (attempt * retry_delay_increment)
                        print(f"Port {port} in use (ffmpeg stderr: {last_capture_result.stderr.strip()}), retrying in {current_delay:.2f}s...")
                        time.sleep(current_delay)
                        continue
                    else:
                        break 
                else: # Different error, fail immediately (no retry for other errors)
                    break 
            
            if not capture_success:
                if last_capture_result is None:
                    raise RuntimeError(f"ffmpeg direct snapshot command for port {port} did not produce a result.")

                error_description = "ffmpeg error"
                if "bind failed: Address already in last_capture_result.stderr":
                    error_description = "Address already in use"
                
                attempts_info = ""
                if error_description == "Address already in use" and attempt == max_retries - 1 and max_retries > 1:
                    attempts_info = f" after {max_retries} attempts"
                
                # Add info if file was not created or too small even if ffmpeg returned 0
                file_issue_info = ""
                if last_capture_result.returncode == 0 and (not os.path.exists(file_path) or os.path.getsize(file_path) <= 1000):
                    file_issue_info = " Output file was not created or is too small."


                detailed_error = (f"ffmpeg direct snapshot for port {port} failed{attempts_info} due to '{error_description}' "
                                  f"(code {last_capture_result.returncode}):{file_issue_info}\n"
                                  f"STDOUT: {last_capture_result.stdout}\nSTDERR: {last_capture_result.stderr}")
                raise RuntimeError(detailed_error)
                
        except subprocess.TimeoutExpired as e:
            raise RuntimeError(f"ffmpeg timed out for port {port}: {str(e)}.")
        except Exception as e:
            if isinstance(e, RuntimeError): # Re-raise our specific RuntimeErrors
                 raise
            else:
                 raise RuntimeError(f"Unexpected snapshot error for port {port}: {str(e)}")
        finally:
            if sdp_path_for_cleanup and os.path.exists(sdp_path_for_cleanup):
                try: 
                    os.remove(sdp_path_for_cleanup)
                except OSError as e_remove: 
                    print(f"Warning: Could not remove sdp file {sdp_path_for_cleanup}: {e_remove}")
        
        if not silent:
            print(f"Snapshot saved to {file_path}")
        return file_path

    def stop_all_streams(self):
        """Stop all active RTP streams."""
        for port in self.stream_ports:
            self.stop_stream(port)

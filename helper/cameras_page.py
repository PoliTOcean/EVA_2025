import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
from rtp_handler import RTPStreamHandler

class CamerasPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Initialize RTP stream handler
        self.rtp_handler = RTPStreamHandler()
        self.stream_ip = "10.0.0.192"  # Default IP for RTP streams

        # Main frame for camera controls
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # IP label
        ip_frame = ttk.Frame(main_frame)
        ip_frame.pack(fill=tk.X, pady=5)
        ttk.Label(ip_frame, text="RTP Stream IP:").pack(side=tk.LEFT, padx=5)
        self.ip_var = tk.StringVar(value=self.stream_ip)
        ttk.Label(ip_frame, textvariable=self.ip_var).pack(side=tk.LEFT, padx=5)

        # Cameras frame
        self.cameras_frame = ttk.LabelFrame(main_frame, text="Available Cameras", padding=10)
        self.cameras_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        # Add camera buttons - now with both snapshot and preview
        for port in self.rtp_handler.stream_ports:
            port_frame = ttk.Frame(self.cameras_frame)
            port_frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(port_frame, text=f"Camera on Port {port}:", width=20).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                port_frame,
                text="Take Photo",
                command=lambda p=port: self.take_photo(p)
            ).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(
                port_frame,
                text="Preview Stream",
                command=lambda p=port: self.preview_stream(p)
            ).pack(side=tk.LEFT, padx=5)

        # Group action buttons
        group_frame = ttk.LabelFrame(main_frame, text="Group Actions", padding=10)
        group_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            group_frame,
            text="Take Photos from Cameras 5001 and 5002 Simultaneously",
            command=self.take_photo_0_1
        ).pack(fill=tk.X, pady=5)

        ttk.Button(
            group_frame,
            text="Take Photos from All Cameras Simultaneously",
            command=self.take_photo_all
        ).pack(fill=tk.X, pady=5)

        # Status variable and label
        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(main_frame, textvariable=self.status_var, foreground="green").pack(pady=5)

    def take_photo(self, port):
        """Take a photo from a specific RTP stream."""
        try:
            self.status_var.set(f"Taking photo from port {port}...")
            file_path = self.rtp_handler.take_snapshot(port)
            messagebox.showinfo("Success", f"Snapshot saved to {file_path}")
            self.status_var.set("Ready")
        except Exception as e:
            error_msg = str(e)
            print(f"Error taking snapshot: {error_msg}")
            
            # Create an informative error message with debugging help
            detail_msg = (
                f"Failed to take snapshot from port {port}.\n\n"
                f"Error: {error_msg}\n\n"
                f"Debugging steps:\n"
                f"1. Verify camera is streaming to {self.stream_ip}:{port}\n"
                f"2. Try using the 'Preview Stream' button first\n"
                f"3. Check network connectivity\n"
                f"4. Ensure no firewall is blocking UDP on port {port}"
            )
            
            messagebox.showerror("Snapshot Error", detail_msg)
            self.status_var.set("Error taking snapshot")
    
    def preview_stream(self, port):
        """Preview the RTP stream using ffplay."""
        try:
            self.status_var.set(f"Starting preview for port {port}...")
            self.rtp_handler.preview_stream(port)
            self.status_var.set("Preview started. Close ffplay window when done.")
        except Exception as e:
            error_msg = str(e)
            print(f"Error starting preview: {error_msg}")
            messagebox.showerror("Preview Error", f"Failed to start preview: {error_msg}")
            self.status_var.set("Error starting preview")

    def take_photo_0_1(self):
        self._take_photos_simultaneous([5001, 5002])

    def take_photo_all(self):
        self._take_photos_simultaneous(self.rtp_handler.stream_ports)

    def _take_photos_simultaneous(self, ports):
        """Take snapshots from multiple cameras at the exact same time."""
        results = {}
        errors = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.status_var.set(f"Taking photos from ports {ports}...")

        def capture(port):
            try:
                file_path = self.rtp_handler.take_snapshot(port, timestamp=timestamp)
                results[port] = file_path
            except Exception as e:
                error_msg = str(e)
                print(f"Thread error taking snapshot from port {port}: {error_msg}")
                errors[port] = error_msg

        threads = []
        for port in ports:
            t = threading.Thread(target=capture, args=(port,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        # Update status based on results
        if results and not errors:
            self.status_var.set("All snapshots successful")
        elif results and errors:
            self.status_var.set(f"Some snapshots failed ({len(errors)} errors)")
        else:
            self.status_var.set("All snapshots failed")

        if results:
            msg = "Snapshots saved:\n" + "\n".join([f"Camera {p}: {f}" for p, f in results.items()])
            messagebox.showinfo("Success", msg)
        if errors:
            # Create a detailed error report
            error_report = "Errors occurred while taking snapshots:\n\n"
            for port, error in errors.items():
                error_report += f"Port {port}: {error}\n\n"
            
            error_report += (
                "Possible solutions:\n"
                "1. Verify all cameras are streaming correctly\n"
                "2. Check if GStreamer is installed and configured\n"
                "3. Make sure ports are not blocked by firewall\n"
                "4. Try restarting the application or the camera streams"
            )
            
            messagebox.showerror("Snapshot Errors", error_report)
            

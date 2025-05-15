import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
from rtp_handler import RTPStreamHandler  # Updated import

class CamerasPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Initialize RTP stream handler
        self.rtp_handler = RTPStreamHandler()
        self.stream_ip = "127.0.0.1"  # Default IP for RTP streams

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

        # Add camera buttons
        for port in self.rtp_handler.stream_ports:
            camera_btn = ttk.Button(
                self.cameras_frame,
                text=f"Take Photo: Camera on Port {port}",
                command=lambda p=port: self.take_photo(p)
            )
            camera_btn.pack(fill=tk.X, pady=5)

        # Group action buttons
        group_frame = ttk.LabelFrame(main_frame, text="Group Actions", padding=10)
        group_frame.pack(fill=tk.X, pady=10)

        ttk.Button(
            group_frame,
            text="Take Photos from Cameras 0 and 1 Simultaneously",
            command=self.take_photo_0_1
        ).pack(fill=tk.X, pady=5)

        ttk.Button(
            group_frame,
            text="Take Photos from All Cameras Simultaneously",
            command=self.take_photo_all
        ).pack(fill=tk.X, pady=5)

    def take_photo(self, port):
        """Take a photo from a specific RTP stream."""
        try:
            file_path = self.rtp_handler.take_snapshot(port)
            messagebox.showinfo("Success", f"Snapshot saved to {file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to take snapshot: {str(e)}")

    def take_photo_0_1(self):
        self._take_photos_simultaneous([5000, 5001])

    def take_photo_all(self):
        self._take_photos_simultaneous(self.rtp_handler.stream_ports)

    def _take_photos_simultaneous(self, ports):
        """Take snapshots from multiple cameras at the exact same time."""
        results = {}
        errors = {}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        def capture(port):
            try:
                file_path = self.rtp_handler.take_snapshot(port, timestamp=timestamp)
                results[port] = file_path
            except Exception as e:
                errors[port] = str(e)

        threads = []
        for port in ports:
            t = threading.Thread(target=capture, args=(port,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        if results:
            msg = "Snapshots saved:\n" + "\n".join([f"Camera {p}: {f}" for p, f in results.items()])
            messagebox.showinfo("Success", msg)
        if errors:
            msg = "Errors:\n" + "\n".join([f"Camera {p}: {e}" for p, e in errors.items()])
            messagebox.showerror("Error", msg)

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from datetime import datetime
from rtp_handler import RTPStreamHandler
import time # Import time for delay
from PIL import Image, ImageTk # Import Pillow for image handling

class CamerasPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Initialize RTP stream handler
        self.rtp_handler = RTPStreamHandler()
        self.stream_ip = "10.0.0.192"  # Default IP for RTP streams

        # To store thumbnail labels and their PhotoImage objects
        self.thumbnail_labels = {}
        self.thumbnail_images = {} # To prevent garbage collection

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

            # Add Label for thumbnail display
            thumb_label = ttk.Label(port_frame)
            thumb_label.pack(side=tk.LEFT, padx=10)
            self.thumbnail_labels[port] = thumb_label

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
            # Call with silent=True to suppress rtp_handler's print
            file_path = self.rtp_handler.take_snapshot(port, silent=True) 
            
            # Display thumbnail
            if file_path:
                self._display_thumbnail(port, file_path)
            
            # No success pop-up: messagebox.showinfo("Success", f"Snapshot saved to {file_path}")
            self.status_var.set(f"Snapshot from port {port} taken.") # Update status
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
            self._clear_thumbnail(port) # Clear thumbnail on error
    
    def _display_thumbnail(self, port, file_path):
        """Loads an image, resizes it, and displays it in the thumbnail label."""
        try:
            img = Image.open(file_path)
            img.thumbnail((100, 75))  # Resize to 100x75 or your preferred size
            photo_img = ImageTk.PhotoImage(img)
            
            if port in self.thumbnail_labels:
                self.thumbnail_labels[port].config(image=photo_img)
                # Keep a reference to the image to prevent it from being garbage collected
                self.thumbnail_labels[port].image = photo_img 
                self.thumbnail_images[port] = photo_img # Also store in dict
        except Exception as e:
            print(f"Error displaying thumbnail for port {port}: {e}")
            self._clear_thumbnail(port)

    def _clear_thumbnail(self, port):
        """Clears the thumbnail for a given port."""
        if port in self.thumbnail_labels:
            self.thumbnail_labels[port].config(image='')
            self.thumbnail_labels[port].image = None
            if port in self.thumbnail_images:
                del self.thumbnail_images[port]

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
        # Use a common base timestamp string for the group, ffmpeg_rtp_handler will add port and microsecond for uniqueness
        base_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") 
        self.status_var.set(f"Taking photos from ports {ports}...")

        def capture(port):
            try:
                # Pass the base_timestamp, rtp_handler will make it unique per port/call
                # Call with silent=True
                file_path = self.rtp_handler.take_snapshot(port, timestamp=base_timestamp, silent=True)
                results[port] = file_path
            except Exception as e:
                error_msg = str(e)
                print(f"Thread error taking snapshot from port {port}: {error_msg}")
                errors[port] = error_msg

        threads = []
        # Launch threads as concurrently as possible.
        # rtp_handler.py uses unique SDP files for each call, which should mitigate port conflicts for SDP.
        # Underlying UDP port binding by ffmpeg for RTP data (5001, 5002 etc.) is the main concern for "Address already in use".
        
        for port in ports:
            t = threading.Thread(target=capture, args=(port,))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()

        # Update thumbnails for successful captures
        for port, file_path in results.items():
            self._display_thumbnail(port, file_path)
        
        # Clear thumbnails for failed captures
        for port in errors.keys():
            if port not in results: # Only clear if it wasn't successful despite an error log (shouldn't happen with current logic)
                self._clear_thumbnail(port)

        # Update status based on results
        if results and not errors:
            self.status_var.set("All snapshots successful")
        elif results and errors:
            self.status_var.set(f"Some snapshots failed ({len(errors)} errors)")
        else:
            self.status_var.set("All snapshots failed")

        # No general success pop-up for group action
        # if results:
        #     msg = "Snapshots saved:\n" + "\n".join([f"Camera {p}: {f}" for p, f in results.items()])
        #     messagebox.showinfo("Success", msg)
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


import tkinter as tk
from tkinter import ttk, messagebox
import os
from datetime import datetime
import threading

import mqtt_handler
from webrtc_handler import JanusWebRTCHandler

class CamerasPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Initialize WebRTC handler
        self.webrtc_handler = JanusWebRTCHandler()
        self.webrtc_handler.set_status_callback(self.update_connection_status)
        
        # Register the camera-related MQTT callback
        mqtt_handler.register_callback(self.mqtt_camera_callback)

        # Default Janus server settings
        self.default_server = "10.0.0.254"
        self.default_port = 8188
        
        # Main frame for camera controls
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Connection section
        connection_frame = ttk.LabelFrame(main_frame, text="Janus WebRTC Connection", padding=10)
        connection_frame.pack(fill=tk.X, pady=10)
        
        # Server settings input
        server_frame = ttk.Frame(connection_frame)
        server_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(server_frame, text="Server IP:").pack(side=tk.LEFT, padx=5)
        self.server_ip_var = tk.StringVar(value=self.default_server)
        self.server_ip_entry = ttk.Entry(server_frame, textvariable=self.server_ip_var, width=15)
        self.server_ip_entry.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(server_frame, text="Port:").pack(side=tk.LEFT, padx=5)
        self.port_var = tk.StringVar(value=str(self.default_port))
        self.port_entry = ttk.Entry(server_frame, textvariable=self.port_var, width=6)
        self.port_entry.pack(side=tk.LEFT, padx=5)
        
        # SSL checkbox
        self.use_ssl_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(server_frame, text="Use SSL", variable=self.use_ssl_var).pack(side=tk.LEFT, padx=10)
        
        self.connect_button = ttk.Button(server_frame, text="Connect", command=self.connect_to_janus)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        # Status display
        status_frame = ttk.Frame(connection_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="Disconnected")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        # Cameras frame - will be populated after connection
        self.cameras_frame = ttk.LabelFrame(main_frame, text="Available Cameras", padding=10)
        self.cameras_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        ttk.Label(self.cameras_frame, text="Connect to Janus server to discover cameras").pack(pady=20)
        
        # Group actions section will be added after connection
        self.group_frame = ttk.LabelFrame(main_frame, text="Group Actions", padding=10)
        self.group_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(self.group_frame, text="Connect to see group camera options").pack(pady=10)

    def connect_to_janus(self):
        """Connect to Janus WebRTC Gateway"""
        server_ip = self.server_ip_var.get()
        if not server_ip:
            messagebox.showerror("Error", "Please enter a server IP address")
            return
            
        # Get port number
        try:
            port = int(self.port_var.get())
        except ValueError:
            messagebox.showerror("Error", "Port must be a number")
            return
            
        use_ssl = self.use_ssl_var.get()
        
        # Disable the connect button during connection
        self.connect_button.config(state="disabled")
        self.status_var.set("Connecting...")
        
        # Initiate connection with the new parameters
        self.webrtc_handler.connect(
            server_ip=server_ip,
            port=port,
            use_ssl=use_ssl,
            on_success=self.on_connection_success,
            on_error=self.on_connection_error
        )
    
    def update_connection_status(self, status):
        """Update the connection status display"""
        self.status_var.set(status)
        
    def on_connection_success(self, streams_info):
        """Handle successful connection"""
        # Re-enable the connect button and update UI
        self.connect_button.config(state="normal", text="Disconnect")
        
        # Clear and update the cameras frame
        for widget in self.cameras_frame.winfo_children():
            widget.destroy()
            
        # Add camera buttons
        if not streams_info:
            ttk.Label(self.cameras_frame, text="No cameras found").pack(pady=20)
        else:
            # Add buttons for individual cameras
            for stream_id, stream_info in streams_info.items():
                camera_btn = ttk.Button(
                    self.cameras_frame,
                    text=f"Take Photo: {stream_info['name']} (ID: {stream_id})",
                    command=lambda id=stream_id: self.take_photo(id)
                )
                camera_btn.pack(fill=tk.X, pady=5)
            
            # Update group actions frame
            for widget in self.group_frame.winfo_children():
                widget.destroy()
                
            # Add group action buttons
            ttk.Button(
                self.group_frame, 
                text="Take Photos from Cameras 0,1", 
                command=lambda: self.take_group_photo([0, 1])
            ).pack(fill=tk.X, pady=5)
            
            ttk.Button(
                self.group_frame, 
                text="Take Photos from All Cameras", 
                command=self.take_photo_all_cameras
            ).pack(fill=tk.X, pady=5)
    
    def on_connection_error(self, error_message):
        """Handle connection error"""
        self.connect_button.config(state="normal")
        messagebox.showerror("Connection Error", f"Failed to connect: {error_message}")
    
    def take_photo(self, stream_id):
        """Take a photo from a specific camera"""
        self.webrtc_handler.take_snapshot(
            [stream_id],
            on_success=lambda result: self.on_snapshot_success(result),
            on_error=lambda error: self.on_snapshot_error(error)
        )
    
    def take_group_photo(self, stream_ids):
        """Take photos from a group of cameras"""
        self.webrtc_handler.take_snapshot(
            stream_ids,
            on_success=lambda result: self.on_snapshot_success(result),
            on_error=lambda error: self.on_snapshot_error(error)
        )
    
    def take_photo_all_cameras(self):
        """Take photos from all available cameras"""
        all_stream_ids = list(self.webrtc_handler.streams_info.keys())
        self.take_group_photo(all_stream_ids)
    
    def on_snapshot_success(self, results):
        """Handle successful snapshot capture"""
        if results:
            cameras_str = ", ".join([f"{info['name']} (ID: {stream_id})" 
                                    for stream_id, info in results.items()])
            messagebox.showinfo("Success", f"Snapshots taken from: {cameras_str}")
        else:
            messagebox.showinfo("Info", "No snapshots were taken")
    
    def on_snapshot_error(self, error_message):
        """Handle snapshot error"""
        messagebox.showerror("Snapshot Error", f"Failed to take snapshot: {error_message}")
    
    def mqtt_camera_callback(self, message, topic):
        """Handles incoming MQTT messages for camera commands"""
        if topic != mqtt_handler.MQTT_TOPIC_COMMANDS:
            return
            
        # Process camera photo commands
        if isinstance(message, dict):
            for command, value in message.items():
                if command and command.startswith("PHOTO_CAMERA_"):
                    try:
                        camera_ids = [int(id) for id in command.split("_")[2:]]
                        if camera_ids:
                            self.take_group_photo(camera_ids)
                    except ValueError:
                        print(f"Invalid camera ID in command: {command}")
                    break
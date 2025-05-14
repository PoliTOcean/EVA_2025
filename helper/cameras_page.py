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

        # Default Janus server IP
        self.default_server = "10.0.0.254"
        
        # Main frame for camera controls
        main_frame = ttk.Frame(self, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Connection section
        connection_frame = ttk.LabelFrame(main_frame, text="Janus WebRTC Connection", padding=10)
        connection_frame.pack(fill=tk.X, pady=10)
        
        # Server IP input
        server_frame = ttk.Frame(connection_frame)
        server_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(server_frame, text="Janus Server IP:").pack(side=tk.LEFT, padx=5)
        self.server_ip_var = tk.StringVar(value=self.default_server)
        self.server_ip_entry = ttk.Entry(server_frame, textvariable=self.server_ip_var, width=15)
        self.server_ip_entry.pack(side=tk.LEFT, padx=5)
        
        self.connect_button = ttk.Button(server_frame, text="Connect", command=self.connect_to_janus)
        self.connect_button.pack(side=tk.LEFT, padx=5)
        
        # Status display
        status_frame = ttk.Frame(connection_frame)
        status_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=5)
        self.status_var = tk.StringVar(value="Disconnected")
        ttk.Label(status_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=5)
        
        # Individual cameras section
        self.cameras_frame = ttk.LabelFrame(main_frame, text="Available Cameras", padding=10)
        self.cameras_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Initial message
        self.cameras_message = ttk.Label(self.cameras_frame, text="Connect to Janus server to discover cameras")
        self.cameras_message.pack(pady=20)
        
        # Camera buttons will be added here dynamically
        self.camera_buttons = {}
        
        # Group actions section
        group_frame = ttk.LabelFrame(main_frame, text="Group Actions", padding=10)
        group_frame.pack(fill=tk.X, pady=10)
        
        self.group_buttons_frame = ttk.Frame(group_frame)
        self.group_buttons_frame.pack(fill=tk.X, pady=5)
        
        # Group buttons will be enabled after connection
        self.group_button_01 = ttk.Button(
            self.group_buttons_frame, 
            text="Take Photo from Cameras 0,1", 
            command=lambda: self.take_group_photo([0, 1]),
            state="disabled"
        )
        self.group_button_01.pack(fill=tk.X, pady=5)
        
        self.group_button_all = ttk.Button(
            self.group_buttons_frame, 
            text="Take Photo from All Cameras", 
            command=self.take_photo_all_cameras,
            state="disabled"
        )
        self.group_button_all.pack(fill=tk.X, pady=5)

    def connect_to_janus(self):
        """Connect to Janus WebRTC Gateway"""
        server_ip = self.server_ip_var.get()
        if not server_ip:
            messagebox.showerror("Error", "Please enter a server IP address")
            return
            
        # Disable the connect button during connection
        self.connect_button.config(state="disabled")
        self.status_var.set("Connecting...")
        
        # Initiate connection
        self.webrtc_handler.connect(
            server_ip,
            on_success=self.on_connection_success,
            on_error=self.on_connection_error
        )
    
    def on_connection_success(self, streams_info):
        """Handle successful connection to Janus"""
        # Re-enable the connect button
        self.connect_button.config(state="normal", text="Disconnect")
        
        # Clear the cameras frame
        for widget in self.cameras_frame.winfo_children():
            widget.destroy()
            
        # Create a frame for the camera buttons
        buttons_frame = ttk.Frame(self.cameras_frame)
        buttons_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Add buttons for each camera
        if not streams_info:
            ttk.Label(buttons_frame, text="No cameras found").pack(pady=20)
        else:
            for stream_id, stream_info in streams_info.items():
                camera_frame = ttk.Frame(buttons_frame)
                camera_frame.pack(fill=tk.X, pady=5)
                
                button = ttk.Button(
                    camera_frame,
                    text=f"Take Photo from {stream_info['name']} (ID: {stream_id})",
                    command=lambda id=stream_id: self.take_photo(id)
                )
                button.pack(fill=tk.X)
                self.camera_buttons[stream_id] = button
            
            # Enable group buttons
            self.group_button_01.config(state="normal")
            self.group_button_all.config(state="normal")
    
    def on_connection_error(self, error_message):
        """Handle connection error"""
        self.connect_button.config(state="normal")
        messagebox.showerror("Connection Error", f"Failed to connect: {error_message}")
    
    def update_connection_status(self, status):
        """Update the connection status display"""
        self.status_var.set(status)
    
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
            
        # Check if it's a photo command
        if not isinstance(message, dict):
            return
            
        for command, value in message.items():
            if command and command.startswith("PHOTO_CAMERA_"):
                # Extract camera IDs from the command
                try:
                    camera_ids = [int(id) for id in command.split("_")[2:]]
                    if camera_ids:
                        self.take_group_photo(camera_ids)
                except ValueError:
                    print(f"Invalid camera ID in command: {command}")
                break
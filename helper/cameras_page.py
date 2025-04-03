import tkinter as tk
from tkinter import messagebox
import requests
import os
from datetime import datetime
import threading

import mqtt_handler

class CamerasPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Register the camera-related MQTT callback
        mqtt_handler.register_callback(self.mqtt_camera_callback)

        self.camera_ports = {
            "CAMERA_1": 8080,
            "CAMERA_2": 8079,
            "CAMERA_3": 8078,
            "CAMERA_4": 8077
        }

        tk.Label(self, text="Cameras Page", font=("Arial", 16)).pack(pady=10)

        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        for camera in self.camera_ports.keys():
            tk.Button(button_frame, 
                      text=f"Take Photo {camera}",
                      command=lambda c=camera: self.take_photo(c)
                     ).pack(pady=5, fill='x')

        tk.Button(button_frame, 
                  text="Take Photo CAMERA_1 and CAMERA_2",
                  command=self.take_photo_camera_1_2
                 ).pack(pady=5, fill='x')

    def mqtt_camera_callback(self, message, topic):
        """
        Handles incoming MQTT messages for camera commands.
        """
        if topic != mqtt_handler.MQTT_TOPIC_COMMANDS:
            return
        command = message.get("command")
        if command and command.startswith("PHOTO_CAMERA_"):
            cameras = command.split("_")[2:]
            threads = []
            for camera in cameras:
                t = threading.Thread(target=self.take_photo, args=(camera,))
                threads.append(t)
                t.start()
            for t in threads:
                t.join()

    def take_photo(self, camera):
        port = self.camera_ports.get(camera, 8080)
        url = f"http://10.0.0.254:{port}/snapshot"
        try:
            response = requests.get(url)
            if response.status_code == 200:
                self.save_photo(camera, response.content)
                messagebox.showinfo("Success", f"Photo taken from {camera} and saved successfully.")
            else:
                messagebox.showerror("Error", f"Failed to take photo from {camera} (status code: {response.status_code})")
        except requests.RequestException as e:
            messagebox.showerror("Error", f"Error taking photo from {camera}: {e}")

    def take_photo_camera_1_2(self):
        thread1 = threading.Thread(target=self.take_photo, args=("CAMERA_1",))
        thread2 = threading.Thread(target=self.take_photo, args=("CAMERA_2",))
        thread1.start()
        thread2.start()

    def save_photo(self, camera, photo_data):
        folder_path = os.path.join("photos", camera)
        os.makedirs(folder_path, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_path = os.path.join(folder_path, f"{timestamp}.jpg")
        with open(file_path, "wb") as file:
            file.write(photo_data)
        print(f"Photo saved to {file_path}")
# main_app.py
import tkinter as tk
from tkinter import ttk

# Import pages
from debug_mqtt_viewer_page import DebugMQTTViewerPage
from send_test_mqtt_page import SendTestMQTTPage
from update_configuration_page import UpdateConfigurationPage
from logger_page import LoggerPage
from plotting_page import PlottingPage  # New plotting page

# Import MQTT handler with additional functions
from mqtt_handler import initialize_mqtt, register_connection_callback, MQTT_BROKER, MQTT_TOPIC_CONFIG, MQTT_TOPIC_COMMANDS, MQTT_TOPIC_AXES, MQTT_TOPIC_STATUS, MQTT_TOPIC_ARM

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Modular GUI with MQTT")
        self.geometry("800x900")
        self.mqtt_connected = False
        self.reconnect_scheduled = False
        self.reconnect_delay = 5000  # 5 seconds

        # Create a navigation bar
        nav_bar = tk.Frame(self, bg="lightgrey")
        nav_bar.pack(side="top", fill="x")

        # Create connection status indicator
        self.status_frame = tk.Frame(nav_bar, width=15, height=15, bg="white", relief="raised", borderwidth=1)
        self.status_frame.pack(side="left", padx=2, pady=5)

        # Add connect button without background color
        self.connect_button = tk.Button(
            nav_bar, 
            text="Connect to ROV", 
            command=self.toggle_mqtt_connection
        )
        self.connect_button.pack(side="left", padx=5, pady=5)
        
        # Other navigation buttons (without MQTT Config)
        tk.Button(nav_bar, text="Status", command=lambda: self.show_frame("DebugMQTTViewerPage")).pack(side="left", padx=5, pady=5)
        tk.Button(nav_bar, text="Commands", command=lambda: self.show_frame("SendTestMQTTPage")).pack(side="left", padx=5, pady=5)
        tk.Button(nav_bar, text="Config", command=lambda: self.show_frame("UpdateConfigurationPage")).pack(side="left", padx=5, pady=5)
        tk.Button(nav_bar, text="Plots", command=lambda: self.show_frame("PlottingPage")).pack(side="left", padx=5, pady=5)
        tk.Button(nav_bar, text="Logger", command=lambda: self.show_frame("LoggerPage")).pack(side="left", padx=5, pady=5)

        # Create a container for the frames
        container = ttk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # Include the new PlottingPage
        for F in (DebugMQTTViewerPage, SendTestMQTTPage, UpdateConfigurationPage, PlottingPage, LoggerPage): 
            page_name = F.__name__
            frame = F(parent=container, controller=self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Register callback for MQTT connection status changes
        register_connection_callback(self.update_connection_status)
        
        # Start with DebugMQTTViewerPage instead of MQTTConfigPage
        self.show_frame("DebugMQTTViewerPage")
        
        # Automatically try to connect to MQTT at startup
        self.after(500, self.connect_to_mqtt)  # Short delay to let the UI initialize first

    def update_connection_status(self, connected):
        """Update connection status indicator based on MQTT connection status"""
        self.mqtt_connected = connected
        if connected:
            self.status_frame.config(bg="green")
            self.connect_button.config(text="ROV Connected")
            self.reconnect_scheduled = False  # Connection successful, cancel any pending reconnect
        else:
            self.status_frame.config(bg="red")
            self.connect_button.config(text="Connect to ROV")
            if not self.reconnect_scheduled:
                print(f"MQTT disconnected. Scheduling reconnection in {self.reconnect_delay / 1000} seconds.")
                self.reconnect_scheduled = True
                self.after(self.reconnect_delay, self.attempt_reconnection)

    def attempt_reconnection(self):
        """Attempt to reconnect to MQTT if not already connected."""
        if not self.mqtt_connected:
            print("Attempting to reconnect to MQTT...")
            self.connect_to_mqtt() 
        # Regardless of outcome, allow update_connection_status to reschedule if needed
        self.reconnect_scheduled = False


    def connect_to_mqtt(self):
        """Connect to MQTT using default values"""
        try:
            # Use default MQTT settings
            broker = MQTT_BROKER
            result = initialize_mqtt(
                broker, 
                MQTT_TOPIC_CONFIG, 
                MQTT_TOPIC_COMMANDS, 
                MQTT_TOPIC_AXES,
                MQTT_TOPIC_STATUS, 
                MQTT_TOPIC_ARM
            )
            # Status will be updated by the callback
        except Exception as e:
            print(f"Error connecting to MQTT: {e}")
            self.update_connection_status(False)

    def toggle_mqtt_connection(self):
        """Handles connect/reconnect button click"""
        if not self.mqtt_connected:
            self.connect_to_mqtt()
        # If already connected, button doesn't need to do anything

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()


if __name__ == "__main__":
    app = MainApp()
    app.mainloop()

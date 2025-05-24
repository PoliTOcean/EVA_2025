# send_test_mqtt_page.py
import tkinter as tk
from tkinter import ttk
from mqtt_handler import mqtt_send_message, MQTT_TOPIC_COMMANDS, MQTT_TOPIC_AXES, MQTT_TOPIC_ARM

class SendTestMQTTPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.slider_labels = {}
        
        # Main container with some padding
        main_frame = tk.Frame(self, padx=15, pady=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a row of control panels
        control_row = tk.Frame(main_frame)
        control_row.pack(fill=tk.X, pady=10)
        
        # ROV Control Panel
        rov_frame = ttk.LabelFrame(control_row, text="ROV Control", padding=10)
        rov_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Button(rov_frame, text="ARM ROV", command=self.send_arm_rov, width=20).pack(pady=5)
        ttk.Button(rov_frame, text="Change Controller Status", command=self.change_controller_status, width=20).pack(pady=5)
        ttk.Button(rov_frame, text="Activate PITCH", command=self.send_activate_pitch_profile, width=20).pack(pady=5)
        ttk.Button(rov_frame, text="Deactivate PITCH", command=self.send_deactivate_pitch_profile, width=20).pack(pady=5)
        ttk.Button(rov_frame, text="WORK MODE", command=self.send_work_mode, width=20).pack(pady=5)
        
        # Quick Movement Panel
        movement_frame = ttk.LabelFrame(control_row, text="Quick Movement", padding=10)
        movement_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        ttk.Button(movement_frame, text="Stop Motors", command=self.send_axes_zero, width=20).pack(pady=5)
        ttk.Button(movement_frame, text="Forward", command=self.send_axes_x, width=20).pack(pady=5)
        ttk.Button(movement_frame, text="Up", command=self.send_axes_z, width=20).pack(pady=5)
        
        # Depth Control Panel
        depth_frame = ttk.LabelFrame(control_row, text="Depth Control", padding=10)
        depth_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        depth_input_frame = tk.Frame(depth_frame)
        depth_input_frame.pack(pady=10)
        
        ttk.Label(depth_input_frame, text="Depth Reference:").pack(pady=(0, 5))
        self.depth_entry = ttk.Entry(depth_input_frame, width=10)
        self.depth_entry.pack(pady=(0, 5))
        self.depth_entry.insert(0, "0.0")
        ttk.Button(depth_input_frame, text="Update", command=self.update_depth_reference).pack(pady=(0, 5))
        
        # Sliders Panel
        slider_frame = ttk.LabelFrame(main_frame, text="Movement Controls", padding=10)
        slider_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create a grid layout for sliders
        slider_grid = tk.Frame(slider_frame)
        slider_grid.pack(fill=tk.BOTH, expand=True)
        
        # Create sliders with better layout and styling - now in two columns
        # First column: X, Y, Z
        self.slider_x = self.create_styled_slider(slider_grid, "X", 0, 0)
        self.slider_y = self.create_styled_slider(slider_grid, "Y", 1, 0)
        self.slider_z = self.create_styled_slider(slider_grid, "Z", 2, 0)
        
        # Second column: PITCH, ROLL, YAW
        self.slider_pitch = self.create_styled_slider(slider_grid, "PITCH", 0, 1)
        self.slider_roll = self.create_styled_slider(slider_grid, "ROLL", 1, 1)
        self.slider_yaw = self.create_styled_slider(slider_grid, "YAW", 2, 1)
        
        # Arm Controls Panel
        arm_frame = ttk.LabelFrame(main_frame, text="Arm Controls", padding=10)
        arm_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create two frames for wrist and nipper controls
        wrist_frame = tk.Frame(arm_frame)
        wrist_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        nipper_frame = tk.Frame(arm_frame)
        nipper_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        # Wrist Controls
        ttk.Label(wrist_frame, text="Wrist Control", font=("TkDefaultFont", 10, "bold")).pack(pady=5)
        ttk.Button(wrist_frame, text="Rotate CCW", command=self.rotate_wrist_ccw).pack(fill=tk.X, pady=2)
        ttk.Button(wrist_frame, text="Rotate CW", command=self.rotate_wrist_cw).pack(fill=tk.X, pady=2)
        ttk.Button(wrist_frame, text="Stop Wrist", command=self.stop_wrist).pack(fill=tk.X, pady=2)
        ttk.Button(wrist_frame, text="Torque ON", command=self.torque_wrist_on).pack(fill=tk.X, pady=2)
        ttk.Button(wrist_frame, text="Torque OFF", command=self.torque_wrist_off).pack(fill=tk.X, pady=2)
        
        # Nipper Controls
        ttk.Label(nipper_frame, text="Nipper Control", font=("TkDefaultFont", 10, "bold")).pack(pady=5)
        ttk.Button(nipper_frame, text="Open Nipper", command=self.open_nipper).pack(fill=tk.X, pady=2)
        ttk.Button(nipper_frame, text="Close Nipper", command=self.close_nipper).pack(fill=tk.X, pady=2)
        ttk.Button(nipper_frame, text="Stop Nipper", command=self.stop_nipper).pack(fill=tk.X, pady=2)

    def create_styled_slider(self, parent, label, row, col):
        slider_container = tk.Frame(parent, padx=10, pady=5)
        slider_container.grid(row=row, column=col, sticky="ew")
        
        ttk.Label(slider_container, text=label, width=8).pack(side=tk.LEFT)
        
        slider = ttk.Scale(slider_container, from_=-32000, to=32000, orient=tk.HORIZONTAL, 
                          length=200, command=self.send_custom_axes)
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        
        # Add a value display label
        value_label = ttk.Label(slider_container, text="0", width=8)
        value_label.pack(side=tk.RIGHT)
        
        # Store the label for later access
        self.slider_labels[label] = value_label
        
        # Bind to update the label when slider changes
        slider.bind("<Motion>", lambda e, s=slider, l=value_label: l.config(text=str(int(s.get()))))
        
        return slider

    def send_message(self, topic, payload):
        mqtt_send_message(topic, payload)

    def send_arm_rov(self):
        self.send_message(MQTT_TOPIC_COMMANDS, {"ARM_ROV": 1})

    def send_axes_zero(self):
        self.send_message(MQTT_TOPIC_AXES, {"X": 0, "Y": 0, "Z": 0, "PITCH": 0, "ROLL": 0, "YAW": 0})
        # Reset sliders to 0
        self.slider_x.set(0)
        self.slider_y.set(0)
        self.slider_z.set(0)
        self.slider_pitch.set(0)
        self.slider_roll.set(0)
        self.slider_yaw.set(0)
        # Update slider labels to 0
        for label_widget in self.slider_labels.values():
            label_widget.config(text="0")

    def send_axes_x(self):
        self.send_message(MQTT_TOPIC_AXES, {"X": 10000, "Y": 0, "Z": 0, "PITCH": 0, "ROLL": 0, "YAW": 0})

    def send_axes_z(self):
        self.send_message(MQTT_TOPIC_AXES, {"X": 0, "Y": 0, "Z": 10000, "PITCH": 0, "ROLL": 0, "YAW": 0})

    def change_controller_status(self):
        self.send_message(MQTT_TOPIC_COMMANDS, {"CHANGE_CONTROLLER_STATUS": 0})
        
    def send_activate_pitch_profile(self):
        self.send_message(MQTT_TOPIC_COMMANDS, {"CHANGE_CONTROLLER_PROFILE": 7})

    def send_deactivate_pitch_profile(self):
        self.send_message(MQTT_TOPIC_COMMANDS, {"CHANGE_CONTROLLER_PROFILE": 3})
        
    def send_work_mode(self):
        self.send_message(MQTT_TOPIC_COMMANDS, {"WORK_MODE": 1})
        
    def update_depth_reference(self):
        try:
            depth_value = float(self.depth_entry.get())
            self.send_message(MQTT_TOPIC_COMMANDS, {"DEPTH_REFERENCE_UPDATE": depth_value})
        except ValueError:
            print("Invalid depth value. Please enter a number.")

    # Add a dummy argument `_` to handle the value passed by the Scale command
    def send_custom_axes(self, _=None): 
        x_value = self.slider_x.get()
        y_value = self.slider_y.get()
        z_value = self.slider_z.get()
        pitch_value = self.slider_pitch.get()
        roll_value = self.slider_roll.get()
        yaw_value = self.slider_yaw.get()
        self.send_message(MQTT_TOPIC_AXES, {
            "X": x_value, 
            "Y": y_value, 
            "Z": z_value, 
            "PITCH": pitch_value, 
            "ROLL": roll_value, 
            "YAW": yaw_value
        })
    
    def rotate_wrist_ccw(self):
        self.send_message(MQTT_TOPIC_ARM, {"ROTATE_WRIST_CCW": 0})

    def rotate_wrist_cw(self):
        self.send_message(MQTT_TOPIC_ARM, {"ROTATE_WRIST_CW": 0})

    def stop_wrist(self):
        self.send_message(MQTT_TOPIC_ARM, {"STOP_WRIST": 0})

    def open_nipper(self):
        self.send_message(MQTT_TOPIC_ARM, {"OPEN_NIPPER": 0})

    def close_nipper(self):
        self.send_message(MQTT_TOPIC_ARM, {"CLOSE_NIPPER": 0})

    def stop_nipper(self):
        self.send_message(MQTT_TOPIC_ARM, {"STOP_NIPPER": 0})

    def torque_wrist_on(self):
        self.send_message(MQTT_TOPIC_ARM, {"TORQUE_WRIST_ON": 0})

    def torque_wrist_off(self):
        self.send_message(MQTT_TOPIC_ARM, {"TORQUE_WRIST_OFF": 0})
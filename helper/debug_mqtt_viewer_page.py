# debug_mqtt_viewer_page.py
import tkinter as tk
from tkinter import ttk
from mqtt_handler import register_callback, unregister_callback, MQTT_TOPIC_STATUS

class DebugMQTTViewerPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        # Create a main canvas and a scrollbar
        main_canvas = tk.Canvas(self)
        scrollbar = tk.Scrollbar(self, orient="vertical", command=main_canvas.yview)
        scrollable_frame = tk.Frame(main_canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: main_canvas.configure(
                scrollregion=main_canvas.bbox("all")
            )
        )

        main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        main_canvas.configure(yscrollcommand=scrollbar.set)

        # Variables to store data
        self.bar_state_var = tk.StringVar()
        self.imu_state_var = tk.StringVar()
        self.rov_armed_var = tk.StringVar()
        self.controller_state_vars = {key: tk.StringVar() for key in ["DEPTH", "PITCH", "ROLL"]}
        self.motor_thrust_vars = {key: tk.DoubleVar() for key in ["FDX", "FSX", "RDX", "RSX", "UPFDX", "UPFSX", "UPRDX", "UPRSX"]}
        self.pwm_vars = {key: tk.StringVar() for key in ["FDX", "FSX", "RDX", "RSX", "UPFDX", "UPFSX", "UPRDX", "UPRSX"]}
        self.depth_var = tk.StringVar()
        self.Zspeed_var = tk.StringVar()
        self.pitch_var = tk.StringVar()
        self.angular_y_var = tk.StringVar()
        self.roll_var = tk.StringVar()
        self.angular_x_var = tk.StringVar() 
        self.yaw_var = tk.StringVar()
        self.force_pitch_var = tk.StringVar()
        self.force_roll_var = tk.StringVar()
        self.force_z_var = tk.StringVar()
        self.motor_thrust_max_xy_var = tk.StringVar()
        self.motor_thrust_max_z_var = tk.StringVar()
        self.reference_pitch_var = tk.StringVar()
        self.reference_roll_var = tk.StringVar()
        self.reference_z_var = tk.StringVar()
        self.cpu_temp_var = tk.StringVar()
        self.cpu_usage_var = tk.StringVar()
        self.ram_total_mb_var = tk.StringVar()
        self.ram_used_mb_var = tk.StringVar()
        self.internal_temperature_var = tk.StringVar()
        self.external_temperature_var = tk.StringVar()
        self.error_integral_z_var = tk.StringVar()
        self.error_integral_pitch_var = tk.StringVar()
        self.error_integral_roll_var = tk.StringVar()
        self.work_mode_var = tk.StringVar()


        # Create a structured layout with frames for different groups of information
        # Top row: ROV Status and System Status
        top_row = tk.Frame(scrollable_frame)
        top_row.grid(row=0, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        
        # ROV Status Box without temperatures
        status_frame = ttk.LabelFrame(top_row, text="ROV Status")
        status_frame.grid(row=0, column=0, padx=10, pady=5, sticky="nw")
        
        status_vars = [
            ("ROV Armed", self.rov_armed_var),
            ("Work Mode", self.work_mode_var),
            ("Bar State", self.bar_state_var),
            ("IMU State", self.imu_state_var)
        ]
        
        for i, (label, var) in enumerate(status_vars):
            tk.Label(status_frame, text=label, width=12, anchor="w").grid(row=i, column=0, padx=5, pady=2, sticky="w")
            tk.Label(status_frame, textvariable=var, width=8, anchor="e", font='TkFixedFont').grid(row=i, column=1, padx=5, pady=2)
        
        # System Status Box next to ROV Status
        system_frame = ttk.LabelFrame(top_row, text="System Status")
        system_frame.grid(row=0, column=1, padx=10, pady=5, sticky="nw")
        
        system_vars = [
            ("CPU Temp", self.cpu_temp_var),
            ("CPU Usage", self.cpu_usage_var),
            ("RAM Total", self.ram_total_mb_var),
            ("RAM Used", self.ram_used_mb_var)
        ]
        
        for i, (label, var) in enumerate(system_vars):
            tk.Label(system_frame, text=label, width=12, anchor="w").grid(row=i, column=0, padx=5, pady=2, sticky="w")
            tk.Label(system_frame, textvariable=var, width=8, anchor="e", font='TkFixedFont').grid(row=i, column=1, padx=5, pady=2)
            
        # New Sensors Box
        sensors_frame = ttk.LabelFrame(top_row, text="Sensors")
        sensors_frame.grid(row=0, column=2, padx=10, pady=5, sticky="nw")
        
        sensors_vars = [
            ("Int Temp", self.internal_temperature_var),
            ("Ext Temp", self.external_temperature_var),
            ("Yaw", self.yaw_var)
        ]
        
        for i, (label, var) in enumerate(sensors_vars):
            tk.Label(sensors_frame, text=label, width=12, anchor="w").grid(row=i, column=0, padx=5, pady=2, sticky="w")
            tk.Label(sensors_frame, textvariable=var, width=8, anchor="e", font='TkFixedFont').grid(row=i, column=1, padx=5, pady=2)
        
        # Middle row: Control Values (merged with Position & Motion)
        control_frame = ttk.LabelFrame(scrollable_frame, text="Control Values")
        control_frame.grid(row=1, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        
        # Group control values into 3 columns: Depth, Roll, Pitch
        # Reordered to put reference values in second position
        depth_vars = [
            ("Depth", self.depth_var),
            ("Ref Z", self.reference_z_var),
            ("Z Speed", self.Zspeed_var),
            ("Force Z", self.force_z_var),
            ("Err Int Z", self.error_integral_z_var),
            ("Ctrl DEPTH", self.controller_state_vars["DEPTH"])
        ]
        
        roll_vars = [
            ("Roll", self.roll_var),
            ("Ref Roll", self.reference_roll_var),
            ("Angular X", self.angular_x_var),
            ("Force Roll", self.force_roll_var),
            ("Err Int Roll", self.error_integral_roll_var),
            ("Ctrl ROLL", self.controller_state_vars["ROLL"])
        ]
        
        pitch_vars = [
            ("Pitch", self.pitch_var),
            ("Ref Pitch", self.reference_pitch_var),
            ("Angular Y", self.angular_y_var),
            ("Force Pitch", self.force_pitch_var),
            ("Err Int Pitch", self.error_integral_pitch_var),
            ("Ctrl PITCH", self.controller_state_vars["PITCH"])
        ]
        
        # Create the 3-column layout
        for i, (label, var) in enumerate(depth_vars):
            tk.Label(control_frame, text=label, width=12, anchor="w").grid(row=i, column=0, padx=5, pady=2, sticky="w")
            tk.Label(control_frame, textvariable=var, width=8, anchor="e", font='TkFixedFont').grid(row=i, column=1, padx=5, pady=2)
            
        for i, (label, var) in enumerate(roll_vars):
            tk.Label(control_frame, text=label, width=12, anchor="w").grid(row=i, column=2, padx=5, pady=2, sticky="w")
            tk.Label(control_frame, textvariable=var, width=8, anchor="e", font='TkFixedFont').grid(row=i, column=3, padx=5, pady=2)
            
        for i, (label, var) in enumerate(pitch_vars):
            tk.Label(control_frame, text=label, width=12, anchor="w").grid(row=i, column=4, padx=5, pady=2, sticky="w")
            tk.Label(control_frame, textvariable=var, width=8, anchor="e", font='TkFixedFont').grid(row=i, column=5, padx=5, pady=2)
        
        # Bottom row: Motor Thrust Visualization (more compact)
        motor_frame = ttk.LabelFrame(scrollable_frame, text="Motor Thrust Visualization")
        motor_frame.grid(row=2, column=0, columnspan=3, padx=10, pady=5, sticky="ew")
        
        self.canvas = tk.Canvas(motor_frame, width=700, height=300)  # Reduced height
        self.canvas.pack(padx=5, pady=5)
        
        # Create labels for motor thrust and PWM values
        self.motor_labels = {}
        self.pwm_labels = {}
        self.thrust_text_labels = {}
        
        motor_keys = ["FDX", "FSX", "RDX", "RSX", "UPFDX", "UPFSX", "UPRDX", "UPRSX"]
        for i, key in enumerate(motor_keys):
            x = i * 65 + 75  # Increased padding to the right (from 45 to 75)
            self.motor_labels[key] = self.canvas.create_rectangle(x-15, 150, x+15, 150, fill="blue")  # Centered at 150
            self.pwm_labels[key] = self.canvas.create_text(x, 250, text="N/A", font=("Arial", 10))  # Adjusted y position
            self.canvas.create_text(x, 270, text=key, font=("Arial", 10))  # Adjusted y position
            self.thrust_text_labels[key] = self.canvas.create_text(x, 290, text="N/A", font=("Arial", 10))  # Adjusted y position
        
        # Add a horizontal reference line at zero thrust
        self.canvas.create_line(0, 150, 700, 150, fill="gray", dash=(4, 2))  # Zero line at 150
        self.canvas.create_text(40, 150, text="0", anchor="e", fill="gray")  # Increased x from 20 to 40
        
        # Add scale markers for +/- 2.5
        self.canvas.create_line(45, 25, 55, 25, fill="gray")  # Line at +2.5 (x increased from 25 to 45)
        self.canvas.create_text(40, 25, text="+2.5", anchor="e", fill="gray")  # Increased x from 20 to 40
        self.canvas.create_line(45, 275, 55, 275, fill="gray")  # Line at -2.5 (x increased from 25 to 45)
        self.canvas.create_text(40, 275, text="-2.5", anchor="e", fill="gray")  # Increased x from 20 to 40
        
        # Pack the canvas and scrollbar
        main_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        register_callback(self.update_data)

    def update_data(self, message, topic):
        if topic != MQTT_TOPIC_STATUS:
            return

        # Update the variables with the received message data
        self.bar_state_var.set(message.get("bar_state", "N/A"))
        self.imu_state_var.set(message.get("imu_state", "N/A"))
        self.rov_armed_var.set(message.get("rov_armed", "N/A"))

        controller_state = message.get("controller_state", {})
        for key, var in self.controller_state_vars.items():
            var.set(controller_state.get(key, "N/A"))

        motor_thrust = message.get("motor_thrust", {})
        for key, var in self.motor_thrust_vars.items():
            thrust = motor_thrust.get(key, "0.0")
            thrust = float(thrust)  # Ensure thrust is a float
            var.set(thrust)
            self.update_motor_thrust_bar(key, thrust)

        pwm_values = message.get("pwm", {})
        for key, var in self.pwm_vars.items():
            pwm = pwm_values.get(key, "N/A")
            var.set(pwm)
            self.canvas.itemconfig(self.pwm_labels[key], text=f"{pwm}")

        self.depth_var.set(message.get("depth", "N/A"))
        self.Zspeed_var.set(message.get("Zspeed", "N/A"))
        self.pitch_var.set(message.get("pitch", "N/A"))
        self.angular_y_var.set(message.get("angular_y", "N/A")) 
        self.roll_var.set(message.get("roll", "N/A"))
        self.angular_x_var.set(message.get("angular_x", "N/A"))
        self.yaw_var.set(message.get("yaw", "N/A"))
        self.force_pitch_var.set(message.get("force_pitch", "N/A"))
        self.force_roll_var.set(message.get("force_roll", "N/A"))
        self.force_z_var.set(message.get("force_z", "N/A"))
        self.motor_thrust_max_xy_var.set(message.get("motor_thrust_max_xy", "N/A"))
        self.motor_thrust_max_z_var.set(message.get("motor_thrust_max_z", "N/A"))
        self.reference_pitch_var.set(message.get("reference_pitch", "N/A"))
        self.reference_roll_var.set(message.get("reference_roll", "N/A"))
        self.reference_z_var.set(message.get("reference_z", "N/A"))
        self.cpu_temp_var.set(message.get("cpu_temp", "N/A"))
        self.cpu_usage_var.set(message.get("cpu_usage", "N/A"))
        self.ram_total_mb_var.set(message.get("ram_total_mb", "N/A"))
        self.ram_used_mb_var.set(message.get("ram_used_mb", "N/A"))
        self.internal_temperature_var.set(message.get("internal_temperature", "N/A"))
        self.external_temperature_var.set(message.get("external_temperature", "N/A"))
        
        error_integral = message.get("error_integral", {})
        self.error_integral_z_var.set(error_integral.get("Z", "N/A"))
        self.error_integral_pitch_var.set(error_integral.get("PITCH", "N/A"))
        self.error_integral_roll_var.set(error_integral.get("ROLL", "N/A"))
        
        self.work_mode_var.set(message.get("work_mode", "N/A"))

    def update_motor_thrust_bar(self, motor, thrust):
        # Convert thrust value to a height for the bar (max value +/- 2.5)
        # New scale: 50 pixels per 2.5 units, centered at 150
        height = 150 - (thrust * 50)  # 50 pixels per 2.5 units of thrust
        x = self.canvas.coords(self.motor_labels[motor])[0] + 15
        self.canvas.coords(self.motor_labels[motor], x-15, height, x+15, 150)
        self.canvas.itemconfig(self.thrust_text_labels[motor], text=f"{thrust:.2f}")

    def __del__(self):
        unregister_callback(self.update_data)
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import numpy as np
import time
import collections
import threading
import queue
from mqtt_handler import register_callback, unregister_callback, MQTT_TOPIC_STATUS

class PlottingPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        
        # Configuration parameters
        self.time_window = 30  # 30 seconds window
        self.update_freq = 10  # Expected 10Hz update frequency
        self.plot_refresh_rate = 200  # Refresh plots every 200ms (5Hz)
        self.buffer_size = self.time_window * self.update_freq  # Buffer size for 30 seconds at 10Hz
        
        # Queue for thread-safe data transfer
        self.data_queue = queue.Queue()
        self.processing_active = False
        self.worker_thread = None
        
        # Initialize data buffers with deques for efficient appending/popping
        self.timestamps = collections.deque(maxlen=self.buffer_size)
        
        # Data buffers for each plot
        # Depth plot and reference
        self.depth_data = collections.deque(maxlen=self.buffer_size)
        self.depth_ref_data = collections.deque(maxlen=self.buffer_size)
        
        # Pitch plot and reference
        self.pitch_data = collections.deque(maxlen=self.buffer_size)
        self.pitch_ref_data = collections.deque(maxlen=self.buffer_size)
        
        # Roll plot and reference
        self.roll_data = collections.deque(maxlen=self.buffer_size)
        self.roll_ref_data = collections.deque(maxlen=self.buffer_size)
        
        # Error integrals
        self.depth_error_integral = collections.deque(maxlen=self.buffer_size)
        self.depth_force = collections.deque(maxlen=self.buffer_size)
        self.pitch_error_integral = collections.deque(maxlen=self.buffer_size)
        self.pitch_force = collections.deque(maxlen=self.buffer_size)
        self.roll_error_integral = collections.deque(maxlen=self.buffer_size)
        self.roll_force = collections.deque(maxlen=self.buffer_size)
        
        # Controller status variables
        self.depth_controller_status = tk.StringVar(value="DEPTH Controller: Unknown")
        self.pitch_controller_status = tk.StringVar(value="PITCH Controller: Unknown")
        self.roll_controller_status = tk.StringVar(value="ROLL Controller: Unknown")
        
        # Plot state
        self.plotting_active = False
        self.start_time = None
        
        # Thread lock for data access
        self.data_lock = threading.Lock()
        
        # Create main layout
        self.create_layout()
        
        # Register MQTT callback
        register_callback(self.process_mqtt_data)
        
    def create_layout(self):
        # Create top control frame
        control_frame = ttk.Frame(self, padding=10)
        control_frame.pack(fill=tk.X)
        
        # Create plotting controls
        self.start_button = ttk.Button(control_frame, text="Start Plotting", command=self.toggle_plotting)
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Time window selector
        ttk.Label(control_frame, text="Time Window (seconds):").pack(side=tk.LEFT, padx=10)
        window_values = [10, 20, 30, 60, 120]
        self.window_selector = ttk.Combobox(control_frame, values=window_values, width=5)
        self.window_selector.current(2)  # Default to 30 seconds
        self.window_selector.pack(side=tk.LEFT, padx=5)
        self.window_selector.bind("<<ComboboxSelected>>", self.update_time_window)
        
        # Create plot frame
        plot_frame = ttk.Frame(self, padding=10)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create a figure with 2 rows and 3 columns
        self.fig = Figure(figsize=(12, 8), dpi=100)
        self.fig.subplots_adjust(hspace=0.4, wspace=0.3)
        
        # Create subplots
        self.ax_depth = self.fig.add_subplot(2, 3, 1)
        self.ax_pitch = self.fig.add_subplot(2, 3, 2)
        self.ax_roll = self.fig.add_subplot(2, 3, 3)
        self.ax_depth_error = self.fig.add_subplot(2, 3, 4)
        self.ax_pitch_error = self.fig.add_subplot(2, 3, 5)
        self.ax_roll_error = self.fig.add_subplot(2, 3, 6)
        
        # Initialize plots
        self.initialize_plots()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=plot_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        
        # Add toolbar
        toolbar_frame = ttk.Frame(plot_frame)
        toolbar_frame.pack(side=tk.BOTTOM, fill=tk.X)
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()
        
        # Status labels
        status_frame = ttk.Frame(self, padding=10)
        status_frame.pack(fill=tk.X)
        
        # Create controller status labels in 3 columns
        ttk.Label(status_frame, textvariable=self.depth_controller_status).grid(row=0, column=0, padx=10)
        ttk.Label(status_frame, textvariable=self.pitch_controller_status).grid(row=0, column=1, padx=10)
        ttk.Label(status_frame, textvariable=self.roll_controller_status).grid(row=0, column=2, padx=10)
        
    def initialize_plots(self):
        # Initialize empty plots
        # Depth plot
        self.depth_line, = self.ax_depth.plot([], [], 'b-', label='Depth')
        self.depth_ref_line, = self.ax_depth.plot([], [], 'r-', label='Reference')
        self.ax_depth.set_title('Depth vs Reference')
        self.ax_depth.set_xlabel('Time (s)')
        self.ax_depth.set_ylabel('Depth (m)')
        self.ax_depth.grid(True)
        self.ax_depth.legend()
        
        # Pitch plot
        self.pitch_line, = self.ax_pitch.plot([], [], 'b-', label='Pitch')
        self.pitch_ref_line, = self.ax_pitch.plot([], [], 'r-', label='Reference')
        self.ax_pitch.set_title('Pitch vs Reference')
        self.ax_pitch.set_xlabel('Time (s)')
        self.ax_pitch.set_ylabel('Pitch (deg)')
        self.ax_pitch.grid(True)
        self.ax_pitch.legend()
        
        # Roll plot
        self.roll_line, = self.ax_roll.plot([], [], 'b-', label='Roll')
        self.roll_ref_line, = self.ax_roll.plot([], [], 'r-', label='Reference')
        self.ax_roll.set_title('Roll vs Reference')
        self.ax_roll.set_xlabel('Time (s)')
        self.ax_roll.set_ylabel('Roll (deg)')
        self.ax_roll.grid(True)
        self.ax_roll.legend()
        
        # Depth error integral plot
        self.depth_error_line, = self.ax_depth_error.plot([], [], 'g-', label='Error Integral')
        self.depth_force_line, = self.ax_depth_error.plot([], [], 'm-', label='Force', alpha=0.7)
        self.ax_depth_error.set_title('Depth Error Integral & Force')
        self.ax_depth_error.set_xlabel('Time (s)')
        self.ax_depth_error.set_ylabel('Value')
        self.ax_depth_error.grid(True)
        self.ax_depth_error.legend()
        
        # Pitch error integral plot
        self.pitch_error_line, = self.ax_pitch_error.plot([], [], 'g-', label='Error Integral')
        self.pitch_force_line, = self.ax_pitch_error.plot([], [], 'm-', label='Force', alpha=0.7)
        self.ax_pitch_error.set_title('Pitch Error Integral & Force')
        self.ax_pitch_error.set_xlabel('Time (s)')
        self.ax_pitch_error.set_ylabel('Value')
        self.ax_pitch_error.grid(True)
        self.ax_pitch_error.legend()
        
        # Roll error integral plot
        self.roll_error_line, = self.ax_roll_error.plot([], [], 'g-', label='Error Integral')
        self.roll_force_line, = self.ax_roll_error.plot([], [], 'm-', label='Force', alpha=0.7)
        self.ax_roll_error.set_title('Roll Error Integral & Force')
        self.ax_roll_error.set_xlabel('Time (s)')
        self.ax_roll_error.set_ylabel('Value')
        self.ax_roll_error.grid(True)
        self.ax_roll_error.legend()
        
    def toggle_plotting(self):
        self.plotting_active = not self.plotting_active
        
        if self.plotting_active:
            # Start plotting
            self.start_button.config(text="Stop Plotting")
            self.start_time = time.time()
            
            # Clear existing data
            self.clear_data()
            
            # Start the data processing thread
            self.processing_active = True
            self.worker_thread = threading.Thread(target=self.data_processing_thread)
            self.worker_thread.daemon = True
            self.worker_thread.start()
            
            # Schedule first update in the main thread
            self.after(self.plot_refresh_rate, self.update_plots)
        else:
            # Stop plotting
            self.start_button.config(text="Start Plotting")
            
            # Stop the data processing thread
            self.processing_active = False
            if self.worker_thread:
                self.worker_thread.join(timeout=1.0)
    
    def clear_data(self):
        """Clear all data buffers"""
        self.timestamps.clear()
        self.depth_data.clear()
        self.depth_ref_data.clear()
        self.pitch_data.clear()
        self.pitch_ref_data.clear()
        self.roll_data.clear()
        self.roll_ref_data.clear()
        self.depth_error_integral.clear()
        self.depth_force.clear()
        self.pitch_error_integral.clear()
        self.pitch_force.clear()
        self.roll_error_integral.clear()
        self.roll_force.clear()
        
    def update_time_window(self, event=None):
        """Update the time window for the plots"""
        try:
            self.time_window = int(self.window_selector.get())
            self.buffer_size = self.time_window * self.update_freq
            
            # Update buffer sizes
            self.timestamps = collections.deque(list(self.timestamps)[-self.buffer_size:], maxlen=self.buffer_size)
            self.depth_data = collections.deque(list(self.depth_data)[-self.buffer_size:], maxlen=self.buffer_size)
            self.depth_ref_data = collections.deque(list(self.depth_ref_data)[-self.buffer_size:], maxlen=self.buffer_size)
            self.pitch_data = collections.deque(list(self.pitch_data)[-self.buffer_size:], maxlen=self.buffer_size)
            self.pitch_ref_data = collections.deque(list(self.pitch_ref_data)[-self.buffer_size:], maxlen=self.buffer_size)
            self.roll_data = collections.deque(list(self.roll_data)[-self.buffer_size:], maxlen=self.buffer_size)
            self.roll_ref_data = collections.deque(list(self.roll_ref_data)[-self.buffer_size:], maxlen=self.buffer_size)
            self.depth_error_integral = collections.deque(list(self.depth_error_integral)[-self.buffer_size:], maxlen=self.buffer_size)
            self.depth_force = collections.deque(list(self.depth_force)[-self.buffer_size:], maxlen=self.buffer_size)
            self.pitch_error_integral = collections.deque(list(self.pitch_error_integral)[-self.buffer_size:], maxlen=self.buffer_size)
            self.pitch_force = collections.deque(list(self.pitch_force)[-self.buffer_size:], maxlen=self.buffer_size)
            self.roll_error_integral = collections.deque(list(self.roll_error_integral)[-self.buffer_size:], maxlen=self.buffer_size)
            self.roll_force = collections.deque(list(self.roll_force)[-self.buffer_size:], maxlen=self.buffer_size)
            
        except ValueError:
            print("Invalid time window value")
            
    def data_processing_thread(self):
        """Worker thread that processes data from the queue"""
        while self.processing_active:
            try:
                # Get message data from the queue with a timeout
                message = self.data_queue.get(timeout=0.1)
                
                # Get current timestamp relative to start time
                current_time = time.time() - self.start_time
                
                # Process message data
                with self.data_lock:
                    self.timestamps.append(current_time)
                    
                    # Extract data from MQTT message
                    try:
                        self.depth_data.append(float(message.get("depth", 0)))
                        self.depth_ref_data.append(float(message.get("reference_z", 0)))
                        
                        self.pitch_data.append(float(message.get("pitch", 0)))
                        self.pitch_ref_data.append(float(message.get("reference_pitch", 0)))
                        
                        self.roll_data.append(float(message.get("roll", 0)))
                        self.roll_ref_data.append(float(message.get("reference_roll", 0)))
                        
                        # Error integrals and forces
                        error_integral = message.get("error_integral", {})
                        self.depth_error_integral.append(float(error_integral.get("Z", 0)))
                        self.depth_force.append(float(message.get("force_z", 0)))
                        
                        self.pitch_error_integral.append(float(error_integral.get("PITCH", 0)))
                        self.pitch_force.append(float(message.get("force_pitch", 0)))
                        
                        self.roll_error_integral.append(float(error_integral.get("ROLL", 0)))
                        self.roll_force.append(float(message.get("force_roll", 0)))
                    except (ValueError, TypeError) as e:
                        print(f"Error processing data: {e}")
                
                # Update controller status (GUI update must be done in main thread)
                controller_state = message.get("controller_state", {})
                self.after_idle(self.update_controller_status, controller_state)
                
                # Mark the task as done
                self.data_queue.task_done()
            except queue.Empty:
                # No data in queue, just continue
                pass
            except Exception as e:
                print(f"Error in data processing thread: {e}")
    
    def update_controller_status(self, controller_state):
        """Update controller status in the main thread"""
        self.depth_controller_status.set(f"DEPTH Controller: {controller_state.get('DEPTH', 'Unknown')}")
        self.pitch_controller_status.set(f"PITCH Controller: {controller_state.get('PITCH', 'Unknown')}")
        self.roll_controller_status.set(f"ROLL Controller: {controller_state.get('ROLL', 'Unknown')}")
    
    def process_mqtt_data(self, message, topic):
        """Process incoming MQTT data - runs in MQTT thread"""
        if topic != MQTT_TOPIC_STATUS or not self.plotting_active:
            return
        
        # Initialize start time if not set
        if self.start_time is None:
            self.start_time = time.time()
        
        # Put the message in the queue for processing
        self.data_queue.put(message)
        
    def update_plots(self):
        """Update all plot lines with current data - runs in main thread"""
        if not self.plotting_active:
            return
        
        with self.data_lock:
            if len(self.timestamps) > 0:
                # Convert deques to numpy arrays for plotting
                timestamps = np.array(self.timestamps)
                
                # Create local copies of data for plotting to minimize lock time
                depth_data = np.array(self.depth_data)
                depth_ref_data = np.array(self.depth_ref_data)
                pitch_data = np.array(self.pitch_data)
                pitch_ref_data = np.array(self.pitch_ref_data)
                roll_data = np.array(self.roll_data)
                roll_ref_data = np.array(self.roll_ref_data)
                depth_error_integral = np.array(self.depth_error_integral)
                depth_force = np.array(self.depth_force)
                pitch_error_integral = np.array(self.pitch_error_integral)
                pitch_force = np.array(self.pitch_force)
                roll_error_integral = np.array(self.roll_error_integral)
                roll_force = np.array(self.roll_force)
                
                # Calculate x-axis limits outside the lock
                if len(timestamps) > 1:
                    x_min = max(0, timestamps[-1] - self.time_window)
                    x_max = timestamps[-1] + 0.1  # Add a small margin
        
        # Update the plots with the local data copies (no lock needed)
        if len(self.timestamps) > 0:
            # Update depth plot
            self.depth_line.set_data(timestamps, depth_data)
            self.depth_ref_line.set_data(timestamps, depth_ref_data)
            
            # Update pitch plot
            self.pitch_line.set_data(timestamps, pitch_data)
            self.pitch_ref_line.set_data(timestamps, pitch_ref_data)
            
            # Update roll plot
            self.roll_line.set_data(timestamps, roll_data)
            self.roll_ref_line.set_data(timestamps, roll_ref_data)
            
            # Update error integral plots
            self.depth_error_line.set_data(timestamps, depth_error_integral)
            self.depth_force_line.set_data(timestamps, depth_force)
            
            self.pitch_error_line.set_data(timestamps, pitch_error_integral)
            self.pitch_force_line.set_data(timestamps, pitch_force)
            
            self.roll_error_line.set_data(timestamps, roll_error_integral)
            self.roll_force_line.set_data(timestamps, roll_force)
            
            # Adjust x-axis limits
            if len(timestamps) > 1:
                self.ax_depth.set_xlim(x_min, x_max)
                self.ax_pitch.set_xlim(x_min, x_max)
                self.ax_roll.set_xlim(x_min, x_max)
                self.ax_depth_error.set_xlim(x_min, x_max)
                self.ax_pitch_error.set_xlim(x_min, x_max)
                self.ax_roll_error.set_xlim(x_min, x_max)
            
            # Auto-adjust y-axis limits if we have data
            if len(depth_data) > 0:
                for ax in [self.ax_depth, self.ax_pitch, self.ax_roll, 
                           self.ax_depth_error, self.ax_pitch_error, self.ax_roll_error]:
                    ax.relim()
                    ax.autoscale_view()
            
            # Draw updated plots
            self.canvas.draw_idle()
        
        # Schedule next update
        if self.plotting_active:
            self.after(self.plot_refresh_rate, self.update_plots)
    
    def __del__(self):
        """Clean up when the page is destroyed"""
        self.processing_active = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.worker_thread.join(timeout=1.0)
        unregister_callback(self.process_mqtt_data)

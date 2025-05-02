# update_configuration_page.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import copy
import numpy as np
import scipy.io
from mqtt_handler import register_callback, mqtt_send_message, MQTT_TOPIC_COMMANDS, MQTT_TOPIC_CONFIG

class UpdateConfigurationPage(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller
        self.current_config = {}
        self.entry_widgets = {}
        self.labels = {}
        self.key_paths = {}  # Stores the full path [section, subsection, ..., key] for each parameter key

        # Create a canvas and scrollbar for scrollable interface
        self.canvas = tk.Canvas(self, borderwidth=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas)

        # Configure the canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(
                scrollregion=self.canvas.bbox("all")
            )
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Layout the canvas and scrollbar
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self.scrollbar.grid(row=0, column=1, sticky="ns")

        # Configure grid weights to make the canvas expand
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Create button frame inside the scrollable frame
        self.button_frame = tk.Frame(self.scrollable_frame)
        self.button_frame.grid(row=0, column=0, columnspan=2, pady=10, sticky="ew")

        load_button = tk.Button(self.button_frame, text="Load Config", command=self.request_configuration)
        load_button.pack(side='left', padx=5)

        send_button = tk.Button(self.button_frame, text="Send Configuration", command=self.send_updated_configuration)
        send_button.pack(side='left', padx=5)

        # Add Save Config button
        save_button = tk.Button(self.button_frame, text="Save Config to File", command=self.save_configuration_to_file)
        save_button.pack(side='left', padx=5)

        # Add Load .mat File button (conditionally enabled)
        self.load_mat_button = tk.Button(self.button_frame, text="Load .mat File", command=self.load_mat_file)
        self.load_mat_button.pack(side='left', padx=5)


        # Register the callback to handle incoming MQTT messages
        register_callback(self.load_config_into_gui)

    def _populate_gui_recursive(self, parent_frame, config_level, current_path, row_index):
        """Recursively populates the GUI based on nested configuration."""
        indent_level = len(current_path)
        indent_px = indent_level * 20 # Pixels of indentation per level

        for key, value in config_level.items():
            full_path = current_path + [key]

            if isinstance(value, dict):
                # Add a section/subsection label
                section_label_text = f"{' ' * indent_level * 2}--- {key} ---" # Text indentation
                section_label = tk.Label(parent_frame, text=section_label_text, font=("Arial", 10, "bold"))
                # Grid indentation using padx
                section_label.grid(row=row_index, column=0, columnspan=2, pady=(10, 5), sticky="w", padx=(10 + indent_px, 10))
                self.labels["_section_" + "_".join(full_path)] = section_label # Store section labels if needed
                row_index += 1
                # Recursively process the nested dictionary
                row_index = self._populate_gui_recursive(parent_frame, value, full_path, row_index)
            else:
                # Check if the value is a list (vector) and skip if it is
                if isinstance(value, list):
                    print(f"Skipping list parameter: {key}") # Optional: for debugging
                    continue # Skip this parameter

                # It's a parameter (and not a list)
                param_key_str = str(key) # Ensure key is string for dict keys
                self.key_paths[param_key_str] = full_path # Store the full path for this parameter key

                # Create label
                label_text = f"{' ' * indent_level * 2}{param_key_str}" # Text indentation
                self.labels[param_key_str] = tk.Label(parent_frame, text=label_text)
                # Grid indentation using padx
                self.labels[param_key_str].grid(row=row_index, column=0, sticky='w', padx=(10 + indent_px, 10))

                # Create entry
                entry = tk.Entry(parent_frame)
                entry.grid(row=row_index, column=1, padx=5, pady=2, sticky='ew')
                self.entry_widgets[param_key_str] = entry

                # Update entry value
                entry.delete(0, tk.END)
                entry.insert(0, str(value))

                row_index += 1
        return row_index


    def load_config_into_gui(self, config, topic):
        if topic != MQTT_TOPIC_CONFIG:
            return

        self.current_config = config.copy() # Store the received config
        self.key_paths.clear() # Clear previous paths

        # Destroy existing widgets before creating new ones
        for widget in self.scrollable_frame.winfo_children():
             # Keep the button frame
            if widget != self.button_frame:
                widget.destroy()

        # Clear references
        self.labels.clear()
        self.entry_widgets.clear()

        # Start populating the GUI recursively from row 1 (below button frame)
        self._populate_gui_recursive(self.scrollable_frame, self.current_config, [], 1)

        # Update the scroll region after adding all widgets
        self.scrollable_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))


    def _find_and_update_key(self, config_level, target_key, new_value):
        """Recursively searches for target_key in config_level and updates its value."""
        if not isinstance(config_level, dict):
            return False

        for key, value in config_level.items():
            if key == target_key:
                # Found the key, update its value directly
                config_level[key] = new_value
                print(f"Updated key '{target_key}' with new value.")
                return True
            elif isinstance(value, dict):
                # Recurse into nested dictionary
                if self._find_and_update_key(value, target_key, new_value):
                    return True # Key was found and updated in nested dict
        return False # Key not found at this level or its descendants


    def load_mat_file(self):
        """Loads data from a .mat file, flattens matrices, and updates corresponding keys in current_config."""

        if not self.current_config:
            messagebox.showwarning("No Configuration", "Load a configuration first before loading .mat data.")
            return

        file_path = filedialog.askopenfilename(
            filetypes=[("MATLAB files", "*.mat"), ("All files", "*.*")],
            title="Select .mat File"
        )

        if not file_path:
            return # User cancelled

        try:
            mat_data = scipy.io.loadmat(file_path)
            updated_keys = []
            not_found_keys = []

            for mat_key, mat_value in mat_data.items():
                # Skip MATLAB's internal variables
                if mat_key.startswith('__'):
                    continue

                # Process the value: flatten numpy arrays, convert numpy scalars
                value_to_update = None
                if isinstance(mat_value, np.ndarray):
                    # Flatten multi-dimensional arrays into a 1D list
                    value_to_update = mat_value.flatten().tolist()
                    #print(f"Flattened matrix for key '{mat_key}'.")
                elif isinstance(mat_value, np.generic):
                     # Convert numpy scalar types (like np.float64) to Python native types
                     value_to_update = mat_value.item()
                     #print(f"Converted numpy scalar for key '{mat_key}'.")
                else:
                    # Use other types as is (e.g., strings, standard Python numbers if loadmat returns them)
                    value_to_update = mat_value

                # Attempt to find and update the key in the current config
                if self._find_and_update_key(self.current_config, mat_key, value_to_update):
                     updated_keys.append(mat_key)
                else:
                     not_found_keys.append(mat_key)


            # --- Feedback Messages ---
            if updated_keys:
                 msg = f"Successfully processed and updated data for keys: {', '.join(updated_keys)}.\n"
                 if not_found_keys:
                     msg += f"Keys not found in the current configuration: {', '.join(not_found_keys)}."
                 messagebox.showinfo("MAT File Loaded", msg)
            elif not_found_keys:
                 messagebox.showwarning("MAT File Processed", f"No matching keys found in the current configuration for variables in the .mat file.\nChecked for: {', '.join(not_found_keys)}")
            else:
                 messagebox.showinfo("MAT File Loaded", "No variables found in the .mat file (excluding internal ones) to process.")


        except Exception as e:
            messagebox.showerror("Error Loading .mat File", f"Failed to load or process .mat file: {e}")


    def _convert_numpy_to_list(self, data):
        """Recursively converts numpy arrays within a nested structure to Python lists."""
        if isinstance(data, dict):
            return {k: self._convert_numpy_to_list(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._convert_numpy_to_list(item) for item in data]
        elif isinstance(data, np.ndarray):
            return data.tolist()
        else:
            return data

    def send_updated_configuration(self):
        # Start with the current config, potentially containing loaded .mat data (numpy arrays)
        updated_config = copy.deepcopy(self.current_config)

        # Merge changes from GUI entries into the updated_config
        for param_key, entry in self.entry_widgets.items():
            value_str = entry.get()
            path = self.key_paths.get(str(param_key))

            if not path:
                print(f"Warning: Path not found for GUI parameter '{param_key}' during send.")
                continue

            # Convert value from GUI string to appropriate type
            try:
                if value_str.lower() in ['true', 'false']:
                    converted_value = value_str.lower() == 'true'
                elif '.' in value_str:
                    converted_value = float(value_str)
                else:
                    converted_value = int(value_str)
            except ValueError:
                converted_value = value_str # Keep as string if conversion fails

            # Navigate the nested structure and update the value
            current_level = updated_config
            try:
                for key in path[:-1]:
                    key_str = str(key)
                    # Ensure intermediate dictionaries exist if somehow missing (shouldn't happen with deepcopy)
                    if key_str not in current_level or not isinstance(current_level[key_str], dict):
                         print(f"Warning: Structure inconsistency for path {path}. Creating intermediate dict.")
                         current_level[key_str] = {}
                    current_level = current_level[key_str]

                final_key = str(path[-1])
                current_level[final_key] = converted_value
            except KeyError as e:
                 messagebox.showerror("Configuration Error", f"Error updating structure for key '{param_key}' at path '{path}'. Missing key: {e}")
                 return
            except TypeError as e:
                 messagebox.showerror("Configuration Error", f"Structure conflict for key '{param_key}' at path '{path}'. Expected a dictionary level. Error: {e}")
                 return


        # Update the internal state to reflect the merged configuration
        self.current_config = updated_config # Keep numpy arrays here if they exist

        # Prepare a version for sending (convert numpy arrays to lists)
        config_to_send = self._convert_numpy_to_list(copy.deepcopy(self.current_config))

        print(f"Sending updated configuration: {config_to_send}")
        mqtt_send_message(MQTT_TOPIC_CONFIG, config_to_send)

    def request_configuration(self):
        request_message = {"REQUEST_CONFIG": 0}
        print(f"Requesting configuration: {request_message}")
        mqtt_send_message(MQTT_TOPIC_COMMANDS, request_message)

    def save_configuration_to_file(self):
        """Saves the current configuration (self.current_config) to a JSON file, converting numpy arrays."""
        if not self.current_config:
            messagebox.showwarning("No Configuration", "No configuration loaded to save.")
            return

        # Ask user for file path
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
            title="Save Configuration As"
        )

        if not file_path:  # User cancelled the dialog
            return

        try:
            # Create a deep copy and convert numpy arrays to lists for JSON compatibility
            config_to_save = self._convert_numpy_to_list(copy.deepcopy(self.current_config))

            with open(file_path, 'w') as f:
                json.dump(config_to_save, f, indent=4)
            messagebox.showinfo("Success", f"Configuration saved successfully to {file_path}")
        except Exception as e:
            messagebox.showerror("Error Saving File", f"Failed to save configuration: {e}")
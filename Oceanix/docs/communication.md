# Communication Protocol

## Overview

This document describes the MQTT-based communication protocol between the **GUI** and **Oceanix**. All messages exchanged MUST follow a JSON-like structure, adhering to the specified topics and key-value conventions.

---

## MQTT Topics and Message Format

Each topic below defines the permissible keys and values, as well as the direction of communication (GUI -> Oceanix or Oceanix -> GUI). Message structures are detailed to ensure consistency.

### Topics and Message Structure

1. ### **axes/**
   - **Direction**: GUI → Oceanix
   - **Description**: Sends position and orientation values from the GUI to Oceanix.
   - **Keys**:
     - `X`: Integer from -32678 to 32678
     - `Y`: Integer from -32678 to 32678
     - `Z`: Integer from -32678 to 32678
     - `YAW`: Integer from -32678 to 32678
   - **Example Message**:
     ```json
     {
       "X": 0,
       "Y": 0,
       "Z": 0,
       "YAW": 0
     }
     ```

2. ### **state_commands/**
   - **Direction**: GUI → Oceanix
   - **Description**: Sends state commands to Oceanix, typically in response to user actions in the GUI.
   - **Keys**:
     - `command_name`: The name of the command, which may correspond to a button pressed in the GUI.
     - `value`: Boolean `0` or `1`
   - **Example Message**:
     ```json
     {
       "command_name": 1
     }
     ```

3. ### **arm_commands/**
   - **Direction**: GUI → Oceanix
   - **Description**: Sends commands for the arm control to Oceanix, typically in response to button presses in the GUI.
   - **Keys**:
     - `command`: command
     - `command_name`: The name of the command, indicating the arm action.
   - **Example Message**:
     ```json
     {
       "command": "command_name"
     }
     ```

4. ### **debug/**
   - **Direction**: GUI ← Oceanix
   - **Description**: Sends debug information from Oceanix to the GUI at a configurable interval.
   - **Keys**:
     - `variable_name`: The name of the variable being monitored.
     - `value`: Current value of the variable
   - **Information Types**:
     - **Heartbeat**: Essential information required for GUI functionality.
     - **Optional Debug**: Additional data useful for debugging purposes.
   - **Example Message**:
     ```json
     {
       "cpu_usage": 34,
       "temperature": 28
     }
     ```

5. ### **config/**
   - **Direction**: GUI ⇔ Oceanix
   - **Description**: Used to synchronize configuration data between GUI and Oceanix.
   - **Keys**:
     - `config_variable`: The name of the configuration variable.
     - `value`: The current or updated value of the configuration variable.
   - **Behavior**:
     - At startup, Oceanix sends the current configuration to the GUI.
     - The GUI can send updates to modify the configuration.
   - **Example Message**:
     ```json
     {
       "controller_profile" : 1 
     }
     ```
---

## Future Extensions

This structure is designed for future modifications, including additional keys and topics that may be required as the protocol evolves.

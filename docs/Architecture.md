# EVA ROV System Architecture

## System Overview

EVA is a Remotely Operated Vehicle (ROV) controlled through a multi-component system that communicates via established protocols:

```
NEXUS (Base Station) <==MQTT==> OCEANIX (Onboard Computer) <==CHIMPANZEE==> NUCLEO (Motor Controller)
```

## Component Breakdown

### NEXUS (Base Station)
**Platform:** MacOS/Linux
**Purpose:** Command and control interface

- Receives and displays video feed from ROV cameras via HTTP
- Processes input from Xbox joystick or X52 flight controller 
- Converts control inputs to MQTT commands
- Displays sensor data from the ROV in real-time
- Acts as the base station for FLOAT (flotation system)

### OCEANIX (ROV Brain)
**Platform:** Raspberry Pi 4/5
**Purpose:** Central processing and control system

- Functions as the primary ROV control system
- Receives operator commands via MQTT
- Transmits sensor data, debug information, and state updates via MQTT
- Implements automatic depth, roll, and pitch control
- Calculates and sends motor PWM values to NUCLEO via CHIMPANZEE protocol
- Processes data from onboard IMU and barometer sensors
- Features configurable parameters via config.json

### NUCLEO (Motor Interface)
**Platform:** STM32 microcontroller
**Purpose:** Direct hardware control

- Implements the CHIMPANZEE serial protocol for communication with OCEANIX
- Receives PWM and arm commands from OCEANIX
- Directly controls motor hardware via multiple PWM output pins

### Oceanix_helper (Development Tool)
**Platform:** GUI application
**Purpose:** Testing and configuration interface

- Connects to OCEANIX via MQTT
- Provides customizable MQTT topic configuration
- Displays sensor and system data in real-time
- Allows manual control of motors and robotic arm for testing
- Shows real-time motor PWM and thrust data
- Enables real-time configuration updates for OCEANIX
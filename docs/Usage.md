# EVA ROV - Operating Instructions

## Startup Procedure

1. **Connect Hardware**
   - Connect EVA to power supply
   - Connect EVA to PC using ethernet cable
   - Wait approximately 10 seconds for system initialization

2. **Launch Control Software**
    - open a new terminal window
   - **Start NEXUS** (primary control interface)
     ```bash
     cd NEXUS
     source venv/bin/activate
     make test
     ```
   - **Start Oceanix_helper** (in a separate terminal)
     ```bash
     cd Oceanix/helper
     source venv/bin/activate
     python main_helper.py
     ```

3. **Arm the ROV** and begin operation

## Troubleshooting Guide

If you encounter issues:

1. **Connect to onboard computer**
   ```bash
   ssh politocean@10.0.0.254
   ```

2. **Verify Oceanix status**
   ```bash
   sudo systemctl status Oceanix
   ```

3. **Restart Oceanix service** if needed
   ```bash
   sudo systemctl restart Oceanix
   ```

4. **Check error logs**
   ```bash
   cd firmware/Oceanix/log
   cat "last_created_file"
   ```

## Oceanix_helper Guide

### Connection Setup
- Use default MQTT values
- Click "Save and Connect" button

### Main Features
- **State Viewer Tab**: Monitor sensors and motors in real-time
- **Commands Tab**:
  - ARM_ROV (required first step)
  - Test motors with predefined commands
  - Use sliders to adjust direction values
  - Click "Send Custom Axes" to apply changes
  - Enable/disable automatic depth, roll, and pitch control

### Advanced Settings
- **Config Tab**: Load, modify and update Oceanix configuration
- **Log Tab**: View real-time console output
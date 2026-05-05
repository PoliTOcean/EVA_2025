# EVA ROV - Operating Instructions

## Startup Procedure

1. **Connect Hardware**
   - Connect EVA to power supply
   - Connect EVA to PC using ethernet cable (can be direct connection or through switch/router)
   - Wait approximately 10 seconds for system initialization

2. **Network Configuration**
   - **With Router**: If router is configured correctly with static IPs, it can automatically assign them
   - **Direct Connection/Switch**: Raspberry Pi and control station must be in same subnet
   - **Default IP Addresses**:
     - Control Station: `10.0.0.192`
     - Raspberry Pi: `10.0.0.254`
   - Check these IP settings if connection issues occur

3. **Launch Control Software**
   
   **Option A: Using Scripts (Recommended)**
   - Scripts are located in `scripts/control_station`
   - **ATTENTION**: Update paths in scripts depending on repository location (default: `Documents/GitHub/repos`)
   - Individual scripts:
     ```bash
     # NEXUS (GUI)
     ./scripts/control_station/nexus_script.sh
     
     # Janus (camera streaming - required for NEXUS)
     ./scripts/control_station/janus_script.sh
     
     # Oceanix Helper (debugging and parameter changes)
     ./scripts/control_station/oceanix_helper_script.sh
     
     # Start all three together
     ./scripts/control_station/start_all.sh
     ```

   Run using the right-click -> Run as a program.
   
   **Option B: Manual Commands**
   - Open a new terminal window
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

4. **Arm the ROV** and begin operation

## Troubleshooting Guide

If you encounter issues:

1. **Connection Loss from NEXUS or Helper**
   - If connection is lost, first close and reopen NEXUS and the helper when connection is restored
   - You may encounter bugs when MQTT connection is lost - restart the application to resolve

2. **Connect to onboard computer**
   ```bash
   ssh politocean@10.0.0.254
   ```

3. **Verify Oceanix status**
   ```bash
   sudo systemctl status Oceanix
   ```

4. **Restart Oceanix service** if needed
   ```bash
   sudo systemctl restart Oceanix
   ```

5. **Check error logs**
   ```bash
   cd firmware/Oceanix/log
   cat "last_created_file"
   ```

## Oceanix_helper Guide

### Connection Setup
- Click "CONNECT" button

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
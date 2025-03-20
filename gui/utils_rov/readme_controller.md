# ROV Controller

This repository contains `controller.py`, a Python script that manages the operation of an ROV (Remotely Operated Vehicle) using a joystick and MQTT communication.

## Button Change Handler (`__on_buttonChanged`)

This function processes button presses and releases, handling different commands based on the button state and shift mode.

### Behavior:
1. If a button is pressed and **shift mode is off**, it retrieves the `onPress` command and its associated value.
2. If a button is pressed and **shift mode is on**, it retrieves the `onShiftPress` command and value.
3. If a button is released and **shift mode is off**, it retrieves the `onRelease` command.
4. If a button is released and **shift mode is on**, it retrieves the `onShiftRelease` command.
5. If the button corresponds to `SHIFT`, it toggles shift mode on (`SHIFT`) or off (`noSHIFT`).
6. If the command is `Z_UP` or `Z_DOWN`, it modifies the `Z` axis movement accordingly.
7. If the command is a known joystick axis state, it updates `axesStates`.
8. If the command is not related to an axis, it publishes an MQTT message to the corresponding topic.

### Debugging:
- Prints button ID, state, command, and value for debugging.
- If no MQTT topic is found for a command, it logs a warning.

## Axis Change Handler (`__on_axisChanged`)

This function processes joystick axis movements, applies deadzones, and maps them to movement commands.

### Behavior:
1. If the axis is `LSB-Y` or `RSB-Y`, it inverts the value.
2. If the absolute value is smaller than the defined deadzone, it sets the value to `0` to prevent small unintended movements.
3. If the axis is `LT` or `RT` (triggers), it normalizes the value to a range between `-32767` and `32767`, then scales it between `0` and `32767`.
4. If the axis is `throttle`, it inverts and normalizes its value.
5. If `Z_UP` or `Z_DOWN` is active, the `Z` axis state is updated accordingly.
6. Finally, the processed axis value is assigned to the corresponding movement command in `axesStates`.

### Debugging:
- Prints axis ID and its processed value for debugging.

## Usage

1. Ensure `config.yaml` is properly set up.
2. Run the script:
3. The joystick will control the ROV, sending commands over MQTT.

## Customization

- Modify `config.yaml` to adjust joystick and MQTT settings.
- Adjust `AXES_DEADZONE` or `INTERVAL` for sensitivity tuning.
- Implement additional command handling in `__on_axisChanged` or `__on_buttonChanged` as needed.

## Controller choice

- The mapping is available in the json file for the xbox one x controller and the x52 flight simulator, if you change the controller you have to add or modify that script with the button mappings of the new controller, there is a different version for linux and MacOS (darwin on the file) because the buttons mapping can be different and the order can change.
-SUGGESTION to understand the buttons order use the debug mode with the script, it will print the position of that buttons in the array so you can modify correctly the json file
-SUGGESTION the buttons mapping can change with wireless controller and with the same controller used with cable



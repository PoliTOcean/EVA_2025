# Joystick Move Configuration

This repository contains the `joystick_Move.yaml` configuration file, which defines the mapping of joystick buttons and axes to specific commands for controlling an arm mechanism. The file is structured in YAML format and consists of two main sections:

- **Buttons**: Defines actions triggered by button presses and releases.
- **Axes**: Maps joystick axes to movement commands with deadzones.

## Buttons Mapping
Each button has a set of properties:
- `onPress`: Command sent when the button is pressed.
- `onRelease`: Command sent when the button is released.
- `topic`: The topic under which the command is published.
- `value`: Numeric value associated with the button press (if applicable).
- `onShiftPress`, `onShiftRelease`, `onShiftValue`: Additional shift-based commands.

### Button Actions:
- **B**: Rotates the wrist clockwise (`ROTATE_WRIST_CW`), stops on release.
- **Y**: Closes the nipper (`CLOSE_NIPPER`), stops on release.
- **X**: Rotates the wrist counterclockwise (`ROTATE_WRIST_CCW`), stops on release.
- **A**: Opens the nipper (`OPEN_NIPPER`), stops on release.
- **Back**: Enables/disables torque (`TORQUE`/`TORQUE_OFF`), with values of `10000` and `0`.
- **Guide & Start**: No assigned actions.
- **LS, RS, LB**: Controls yaw movement (`YAW`).
- **D-Pad-Up**: Enables a function (`ABLE`) with a value of `10000`.
- **D-Pad-Down**: Disables a function (`DISABLE`).
- **D-Pad-Left**: Toggles shift mode (`SHIFT`/`noSHIFT`).
- **D-Pad-Right**: Triggers `DPAD_RIGHT` command.
- **UPLOAD**: Arms the system (`ARM`).

!!You can modify this commands as you want, this is just a base.

## Axes Mapping
Each axis is assigned a movement command and a `deadzone` value to prevent small, unintended movements.

### Axis Actions:
- **LSB-X**: Moves along the Y-axis (`Y`), deadzone: `2000`.
- **LSB-Y**: Moves along the X-axis (`X`), deadzone: `2000`.
- **RSB-X**: Controls roll (`ROLL`), deadzone: `2000`.
- **RSB-Y**: Controls pitch (`PITCH`), deadzone: `2000`.
- **LT, RT**: Controls Z-axis (`Z`), deadzone: `3000`.

## Usage
This configuration is designed for a joystick-based control system where commands are mapped to specific buttons and axes for controlling an arm mechanism.

The shift button is like the shift on the keyboard, when it is pressed each other button can chenge the command or the value to send, for the axis commands during the shift it is possible to have faster or more precise movements based on the value sent.

The command Able/Disable allows the pilot to use or not pitch and roll commands, to use them just when he needs, when disable the ROV become stable and horizontal again.

It is also possible to send fixed value through buttons, and change this value with the shift button, as explained before. (ex value= 10000, onShiftValue=3000, so when shift it pressed the movement will be slower and more precise)

 ```
  LB:
    onPress: "YAW"
    onRelease: "YAW"
    topic: "state_commands"
    onShiftRelease:  "YAW"
    onShiftPress: "YAW"
    value: 10000
    onShiftValue: 3000
```
    
-Code Example with LB button that change the value when shift is pressed

## Customization
To modify the configuration:
- Adjust button commands based on specific robotic system needs.
- Modify deadzones in the axes section to fine-tune sensitivity.
- Add new button mappings or reassign existing ones as necessary.

Ensure that the corresponding system software is configured to handle the assigned commands appropriately.



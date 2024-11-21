import serial
import threading
import sys
import termios
import tty

# Open serial port
ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)  # Adjust port and baudrate as needed

# Messages to send
message1 = [0xFF, 0x00, 0x01, 0x00, 0x01, 0x55, 0xEE]  # Customize the message
message2 = [0xAA, 0x00, 0x00, 0x06, 0x40, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0xEE]  # Customize the message

# Function to read input without blocking
def getch():
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch

def read_serial():
    buffer = bytearray()  # Buffer to store incoming bytes
    while True:
        if ser.in_waiting > 0:
            # Read incoming bytes
            data = ser.read(ser.in_waiting)
            for byte in data:
                buffer.append(byte)
                if byte == 0xEE:  # Trigger condition
                    print(f"Received buffer: {[hex(b) for b in buffer]}\r")
                    buffer.clear()  # Clear buffer after processing

# Function to read serial data continuously
# def read_serial():
#     while True:
#         if ser.in_waiting > 0:
#             data = ser.read(ser.in_waiting) #.decode('utf-8', errors='ignore')
#             print(f"Received: {data}")

# Start the serial reading thread
reader_thread = threading.Thread(target=read_serial, daemon=True)
reader_thread.start()

# Main loop to send messages based on key presses
print("Press '1' to send Message 1, '2' to send Message 2. Press 'q' to quit.")
try:
    while True:
        key = getch()
        if key == '1':
            for byte in message1:
                ser.write(byte.to_bytes(1, 'big'))  # Convert integer to single byte
                print(f"Sent byte: {hex(byte)}")
        elif key == '2':
            for byte in message2:
                ser.write(byte.to_bytes(1, 'big'))  # Convert integer to single byte
                print(f"Sent byte: {hex(byte)}")
        elif key == 'q':  # Quit
            print("Exiting...")
            break
except KeyboardInterrupt:
    print("\nExiting...")

# Close the serial port
ser.close()

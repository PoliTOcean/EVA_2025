#!/bin/bash

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for CMake
if ! command_exists cmake; then
    echo "CMake is not installed. Installing CMake..."
    sudo apt-get update
    sudo apt-get install -y cmake
else
    echo "CMake is already installed."
fi

# Check for GCC
if ! command_exists gcc; then
    echo "GCC is not installed. Installing GCC..."
    sudo apt-get update
    sudo apt-get install -y gcc g++
else
    echo "GCC is already installed."
fi

# Check for OpenSSL
if ! dpkg -s libssl-dev >/dev/null 2>&1; then
    echo "OpenSSL is not installed. Installing OpenSSL..."
    sudo apt-get update
    sudo apt-get install -y libssl-dev
else
    echo "OpenSSL is already installed."
fi

# Check for libuv
if ! dpkg -s libuv1-dev >/dev/null 2>&1; then
    echo "libuv is not installed. Installing libuv..."
    sudo apt-get update
    sudo apt-get install -y libuv1-dev
else
    echo "libuv is already installed."
fi

# Check for wiringPi
if ! dpkg -s wiringpi >/dev/null 2>&1; then
    echo "wiringPi is not installed. Installing wiringPi..."
    sudo apt-get update
    sudo apt-get install -y wiringpi
else
    echo "wiringPi is already installed."
fi

# Check for Eclipse Paho MQTT C and C++ libraries
if ! dpkg -s libpaho-mqtt-dev libpaho-mqttpp-dev >/dev/null 2>&1; then
    echo "Eclipse Paho MQTT libraries are not installed. Installing Eclipse Paho MQTT libraries..."
    sudo apt-get update
    sudo apt-get install -y libpaho-mqtt-dev libpaho-mqttpp-dev
else
    echo "Eclipse Paho MQTT libraries are already installed."
fi

# Clone the repository (if not already cloned)
# if [ ! -d "Oceanix" ]; then
#     echo "Cloning the repository..."
#     git clone https://github.com/your-repo/Oceanix.git
# fi

# Navigate to the project directory
cd Oceanix

# Create a build directory
mkdir -p build
cd build

# Run CMake
echo "Running CMake..."
cmake ..

# Run Make
echo "Running Make..."
make

echo "Installation and build process completed."
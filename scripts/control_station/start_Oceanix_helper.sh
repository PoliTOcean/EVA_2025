#!/bin/bash

APP_DIR="/home/politocean/Documents/GitHub/EVA_2025/helper"

gnome-terminal -- bash -c "
cd $APP_DIR

# Check if virtual environment exists
if [ ! -d \"$APP_DIR/venv\" ]; then
echo 'Virtual environment not found. Creating one...'
python3.10 -m venv $APP_DIR/venv
source $APP_DIR/venv/bin/activate
echo 'Installing dependencies...'
pip install --upgrade pip
pip install -r $APP_DIR/requirements.txt
else
source $APP_DIR/venv/bin/activate
fi

echo 'Starting Python application...'

source $APP_DIR/venv/bin/activate
python main.py
exec bash
"

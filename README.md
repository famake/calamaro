# calamaro

A small controller for RGB LEDs on the local network using Art-Net.

## Features
- Add devices with IP address and number of pixels
- Create groups of devices
- Set colors for a group via HTTP or MQTT

## Usage
Install requirements with `pip install -r requirements.txt`.
Run the server:
```bash
python controller.py
```
Send REST commands to http://localhost:8000.

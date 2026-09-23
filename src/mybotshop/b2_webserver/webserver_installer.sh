#!/usr/bin/env bash

# @author    Salman Omar Sohail <support@mybotshop.de>
# @copyright (c) 2025, MYBOTSHOP GmbH, Inc., All rights reserved.

# Define color codes
ORANGE='\033[38;5;208m'
YELLOW='\033[93m'
WHITE='\033[0m'
NC='\033[0m' 

log() { echo -e "${1}${2}${NC}"; }

# Update package lists and install necessary packages
log "${ORANGE}" "Installing VNC server and XFCE desktop environment..."
sudo apt update -y && sudo apt install -y tigervnc-standalone-server xfce4 xfce4-goodies dbus-x11

# Create the ~/.vnc directory if it doesn't exist
mkdir -p ~/.vnc
echo "mybotshop" | vncpasswd -f > ~/.vnc/passwd
chmod 600 ~/.vnc/passwd

# Setup the VNC server configuration
cat > ~/.vnc/xstartup << 'EOF'
#!/bin/bash
unset SESSION_MANAGER
unset DBUS_SESSION_BUS_ADDRESS
export XKL_XMODMAP_DISABLE=1

# Start basic X services
xsetroot -solid grey
vncconfig -iconic &

# Start XFCE (keep running in background)
startxfce4 &

# Requires Superuser privileges to run
# sudo chmod +x .vnc/xstartup
# Wait a bit for XFCE to load before setting the wallpaper
source /opt/mybotshop/install/setup.bash
(sleep 5 && \
 WALLPAPER_PATH="$(ros2 pkg prefix b2_webserver)/share/b2_webserver/b2_webserver/static/media/wallpaper/vnc_wallpaper.jpg" && \
 for i in {0..3}; do
   xfconf-query -c xfce4-desktop \
     -p /backdrop/screen0/monitorVNC-0/workspace$i/last-image \
     -n -t string -s "$WALLPAPER_PATH"
   xfconf-query -c xfce4-desktop \
     -p /backdrop/screen0/monitorVNC-0/workspace$i/image-style \
     -n -t int -s 3
 done && xfdesktop --reload) &

# Keep the session alive
while true; do
    sleep 3600
done
EOF

# Make the xstartup script executable
sudo chmod +x ~/.vnc/xstartup

log "${ORANGE}" "Installing Websocket..."
sudo apt install -y websockify

log "${ORANGE}" "Installing Webserver dependencies..."
python3.10 -m pip install playsound Flask waitress

log "${ORANGE}" "Updating ufw policies..."
sudo ufw allow 5901/tcp && sudo ufw allow 6080/tcp && sudo ufw allow 9000

# Final instructions
log "${ORANGE}" "VNC server setup complete."
log "${YELLOW}" "To start the VNC server:"
log "${WHITE}" "vncserver :1 -geometry 1920x1080 -depth 24 -localhost no"

log "${YELLOW}" "To check VNC server status:"
log "${WHITE}" "vncserver -list"

log "${YELLOW}" "To stop the VNC server:"
log "${WHITE}" "vncserver -kill :1 && rm -rf /tmp/.X1-lock /tmp/.X11-unix/X1"

log "${ORANGE}" "VNC Client Setup"
log "${YELLOW}" "For first-time setup, run:"
log "${WHITE}" "sudo apt install tigervnc-viewer && sudo ufw allow 5901/tcp"

log "${YELLOW}" "To connect to the VNC server:"
log "${WHITE}" "vncviewer 192.168.131.1:1"
# MYBOTSHOP Web Interface
![maintainer](https://img.shields.io/badge/Maintainer-Salman-blue)

## Operation

- Add password to configuration file and service names

- Run WebServer

```bash
ros2 launch b2_webserver webserver.launch.py
```

## Dependency

Core dependency

- ROS2
- `pip3 install Flask`

For Audio

- `pip3 install playsound`
- `pip3 install TTS`

For Audio CLI

- `sudo apt-get install espeak-ng`
    
## Configuration

- Update the ``robot_webserver.yaml``
- Update `.gltf` & name in `index.html` and `system.html`

## Parameters

This file contains the configuration parameters for the b2_webserver node. 
The parameters are used to configure the web server, including the IP address and port, 
as well as the robot's GPS coordinates, password, and other settings.

- `str` robot_rosbag_dir -- Directory where the rosbag files are stored
- `int` robot_rosbag_storage -- Split rosbag is file size in more that 1 Gb (in bytes)
- `int` robot_rosbag_duration -- Split rosbag if duration is more than 30 minutes (in seconds)
- `lis` robot_services -- List of services to be used by the webserver
- `str` robot_webserver -- Name of the webserver node
- `str` robot_map_topic -- Name of the map topic
- `str` robot_cmd_vel -- Name of the cmd_vel topic
- `str` robot_e_stop -- Name of the e_stop topic
- `flo` robot_gps_lat -- Latitude of the robot
- `flo` robot_gps_lon -- Longitude of the robot
- `str` robot_password -- Password for the robot
- `str` robot_gps_topic -- Name of the gps topic
- `str` robot_battery_topic -- Name of the battery topic

### Access to Robot PC


#### First Time Setup

- Install
  
```bash
sudo apt update && sudo apt install tigervnc-standalone-server xfce4 xfce4-goodies dbus-x11 -y
```

- Password

```bash
vncpasswd
```

- Setup server

```bash
mkdir -p ~/.vnc
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

# Keep the session alive
while true; do
    sleep 3600
done
EOF
```

- Super user

```bash
sudo chmod +x ~/.vnc/xstartup
```

#### VNC Robot Startup

- Start Server

```bash
vncserver :1 -geometry 1920x1080 -depth 24 -localhost no
```

- Check VNC

```bash
vncserver -list
```

- Stop VNC
  
```bash
vncserver -kill :1 && rm -rf /tmp/.X1-lock /tmp/.X11-unix/X1
```

#### VNC Remote Startup

- In remote PC 

```bash
sudo apt install tigervnc-viewer
sudo ufw allow 5901/tcp && sudo ufw allow 6080/tcp
vncviewer 10.42.0.50:1
```
# B2 Robot Quick Reference

## Connect to Robot

```bash
ssh b2
```
Password: `Unitree0408`

## Share Internet (Host -> Robot)

> **Note:** Your laptop must be connected to WiFi with an IPv4 address (not IPv6-only).

### 1. On your laptop (run once per session):
```bash
sudo ~/Documents/NEW_b2_REPO/qre_b2/utils/share_internet.sh
```

### 2. On the robot (after SSH):
```bash
sudo ~/Documents/roberto/enable_internet.sh
```

## Launch Webserver (on robot)

```bash
ros2 launch b2_webserver webserver.launch.py
```

> Environment and `ROS_DOMAIN_ID=10` are auto-sourced in `.bashrc` on the robot.

**First-time setup (if ROS_DOMAIN_ID not set):**
```bash
echo 'export ROS_DOMAIN_ID=10' >> ~/.bashrc && source ~/.bashrc
```

Access at: **http://192.168.123.164:9000**
- Username: `admin`
- Password: `mybotshop`

## ROS2 Topics from Host

```bash
source ~/Documents/NEW_b2_REPO/qre_b2/src/mybotshop/b2_bringup/config/host_setup.bash
ros2 topic list
```

> `host_setup.bash` sets `ROS_DOMAIN_ID=10` and CycloneDDS config automatically.

## Network Info

| Device               | IP Address           | Notes                |
|---------------------|----------------------|----------------------|
| B2 MCU              | 192.168.123.161      | -                    |
| B2 PC               | 192.168.123.164      | User: unitree        |
| B2 Webserver        | 192.168.123.164:9000 | admin / mybotshop    |
| Livox MID360 Lidar  | 192.168.123.162      | -                    |
| Host PC (USB LAN)   | 192.168.123.51       | enx00e04c6804d9      |

## Systemd Services (on robot)

The robot uses systemd services for auto-starting ROS nodes on boot.

**Check service status:**
```bash
systemctl list-units --all | grep b2
```

**Manage services:**
```bash
sudo systemctl start b2-hardware      # Start a service
sudo systemctl stop b2-hardware       # Stop a service
sudo systemctl restart b2-hardware    # Restart a service
sudo systemctl enable b2-hardware     # Enable auto-start on boot
sudo systemctl disable b2-hardware    # Disable auto-start
systemctl status b2-hardware          # Check status/logs
journalctl -u b2-hardware -n 50       # View recent logs
```

**Core services (should be enabled):**
- `b2-hardware` - Robot hardware interface (Unitree SDK)
- `b2-domain-bridge` - Bridges ROS topics between domains
- `b2-statepublisher` - Publishes robot state/TF
- `b2-twistmux` - Velocity command multiplexer
- `b2-webserver` - Web interface

**Optional services (enable if hardware connected):**
- `b2-front-video` / `b2-rear-video` - Camera streams
- `b2-livox-mid360` - Livox LiDAR
- `b2-realsense-d405` - Intel RealSense depth camera
- `b2-nano` - Serial communication
- `b2-pcd-scan` - Point cloud to laser scan

**First-time service installation:**
```bash
cd /opt/mybotshop
python3 src/mybotshop/b2_bringup/scripts/startup_installer.py
sudo systemctl daemon-reload
sudo systemctl enable --now b2-hardware b2-domain-bridge b2-statepublisher b2-twistmux b2-webserver
```

---

## Common Commands (on robot)

```bash
# Teleoperation
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# SLAM Navigation
ros2 launch b2_nav2 slam.launch.py

# Map Navigation
ros2 launch b2_nav2 map_navi.launch.py

# Visualization
ros2 launch b2_viz view_robot.launch.py

# Update system date (if robot has no internet)
setdate
```

## Troubleshooting

**Service fails with "eth0: does not match an available interface":**
The C++ source files have hardcoded `eth0`. The robot uses `eno2`. See INSTALLATION_NOTES.md Issue 12 for the fix.

**"ros2 topic list" shows no topics from robot:**
1. Check `ROS_DOMAIN_ID=10` is set on both robot and host
2. Check CycloneDDS config has correct network interface
3. Verify services are running: `systemctl list-units --all | grep b2`

---

## Documentation

https://www.docs.quadruped.de/projects/b2/html/index.html

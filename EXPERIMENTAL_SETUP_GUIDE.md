# B2_W - (Experimental) Setup Guide

> Local documentation for testing the QRE B2 MyBotShop Software
> Started: 2025-12-08

## Environment Setup

| Location | Details |
|----------|---------|
| Laptop | Ubuntu 20.04 |
| B2 Onboard PC | Ubuntu 22.04, `ssh -X unitree@192.168.123.164` (password: `Unitree0408`) |
| Network | Connected via LAN, static IP on 192.168.123.x subnet |

### Network Interfaces (Laptop)

> **Note:** These are example values. Your interface names and IPs will differ. Run `ip addr` to find yours.

| Interface | IP Address | Purpose |
|-----------|------------|---------|
| `<wifi_interface>` (e.g., `wlp3s0`, `wlan0`) | `<your_wifi_ip>` | WiFi (internet access) |
| `<lan_interface>` (e.g., `enx...`, `eth0`) | 192.168.123.X | LAN to robot (must be on 192.168.123.x subnet) |

**Finding your network interfaces:**

```bash
ip addr
```

Look for:
- **WiFi interface**: Usually starts with `wl` (e.g., `wlp3s0`, `wlan0`)
- **LAN interface**: Usually starts with `en` or `eth` (e.g., `enx00e04c6804d9`, `eth0`)

### Network Interfaces (B2_W Robot)

| Interface | IP Address | Purpose |
|-----------|------------|---------|
| eno2 | 192.168.123.164 | LAN to Laptop |
| wlo1 | - | WiFi (available but not used) |

---

## SSH Setup (Optional)

To simplify connecting to the robot, you can set up an SSH alias and key-based authentication.

### SSH Alias

Add this to `~/.ssh/config` on your laptop:

```
Host b2
       HostName 192.168.123.164
       User unitree
       ForwardX11 yes
```

Now you can connect with just `ssh b2` instead of `ssh -X unitree@192.168.123.164`.

### SSH Key Authentication (Optional)

To avoid typing the password every time:

```bash
# Generate SSH key (if you don't have one)
ssh-keygen -t ed25519

# Copy key to robot (will ask for password once)
ssh-copy-id unitree@192.168.123.164
```

---

## Sharing Internet with the Robot

The robot does not have direct internet access. To install packages, we share internet from the Laptop via the LAN connection.

> **Note:** These changes are **temporary** and will be lost on reboot of either machine.

### Step 1: On the Laptop

Enable IP forwarding and set up NAT to route robot traffic through WiFi.

**Option A: Use the script (recommended)**

```bash
sudo ./utils/share_internet.sh
```

> **Note:** Before running, edit the script to match your network interfaces (see "Finding your network interfaces" below).

**Option B: Run commands manually**

```bash
# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# Set up NAT (masquerade) - route traffic from robot through WiFi
# Replace wlp3s0 with your WiFi interface
# Replace enx00e04c6804d9 with your LAN interface to the robot
sudo iptables -t nat -A POSTROUTING -o wlp3s0 -j MASQUERADE
sudo iptables -A FORWARD -i enx00e04c6804d9 -o wlp3s0 -j ACCEPT
sudo iptables -A FORWARD -i wlp3s0 -o enx00e04c6804d9 -m state --state RELATED,ESTABLISHED -j ACCEPT
```


### Step 2: On the Robot (via SSH)

Set the laptop as the default gateway and configure DNS.

**Option A: Use the script (recommended)**

```bash
ssh unitree@192.168.123.164
sudo ~/Documents/<user>/enable_internet.sh
```

**Option B: Run commands manually**

```bash
# Add default route through laptop (replace with your laptop's LAN IP)
sudo ip route add default via <your_laptop_lan_ip>  # e.g., 192.168.123.51

# Set DNS server (Google's public DNS)
echo "nameserver 8.8.8.8" | sudo tee /etc/resolv.conf

# Verify internet access
ping -c 3 google.com
```

---

## Installing ROS2 Humble on the Robot

> **Prerequisite:** Internet access on the robot (see "Sharing Internet with the Robot" above)

### Step 1: Set Locale

```bash
sudo apt update && sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

### Step 2: Add ROS2 Repository

```bash
sudo apt install software-properties-common curl -y
sudo add-apt-repository universe -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

### Step 3: Install ROS2 Humble Desktop

```bash
sudo apt update
sudo apt install ros-humble-desktop -y
```

### Step 4: Verify Installation

```bash
source /opt/ros/humble/setup.bash
ros2 --version
```

### Optional: Add to .bashrc

To automatically source ROS2 on every terminal session:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

---

## Copying the Workspace to the Robot

The workspace (repository content) needs to be at `/opt/mybotshop` on the robot.

### Step 1: Create Directory on Robot (via SSH)

```bash
sudo mkdir /opt/mybotshop
sudo chown unitree:unitree /opt/mybotshop
```

### Step 2: Copy from Laptop

From your laptop, copy the workspace contents:

```bash
scp -r /path/to/mybotshop/* unitree@192.168.123.164:/opt/mybotshop/
```

> **Note:** Replace `/path/to/mybotshop` with your local repo path.


> **Note:** The trailing `/` on the source path copies the contents, not the folder itself.

---

## Running the Install Script

The install script installs additional ROS2 packages and system dependencies.

> **Prerequisite:** Internet access on the robot and ROS2 Humble installed.

### On the Robot

```bash
cd /opt/mybotshop/src/mybotshop
./b2_install.bash
```

This script will:
- Install system dependencies (cmake, PCL, GStreamer, etc.)
- Install Python packages (Flask, colcon, etc.)
- Install ROS2 Humble packages (navigation2, ros2_control, realsense, teleop, etc.)
- Copy udev rules for USB devices
- Set up MOTD banner

---

## Building the Workspace

### On the Robot

```bash
cd /opt/mybotshop
source /opt/ros/humble/setup.bash
colcon build --symlink-install
```

### Build Fixes Required

The initial build will fail due to missing dependencies and files. Apply these fixes:

#### 1. Missing `config` folder in b2_depth_camera

```bash
mkdir -p /opt/mybotshop/src/mybotshop/b2_depth_camera/config
touch /opt/mybotshop/src/mybotshop/b2_depth_camera/config/.gitkeep
```

#### 2. Missing `rtcm_msgs` package (for ntrip_client)

```bash
sudo apt install ros-humble-rtcm-msgs -y
```

#### 3. Missing Livox SDK (for livox_ros_driver2)

```bash
cd /opt/mybotshop/src/third_party/lidar/8May2025_livox_sdk
mkdir -p build && cd build
cmake ..
make -j4
sudo make install
```

#### 4. Missing Unitree SDK2 libraries (for b2_platform)

The repository includes Unitree SDK2 but is missing the prebuilt libraries (`lib/`), complete include files, and thirdparty dependencies. Download from official repo and copy missing parts:

```bash
cd /opt/mybotshop/src/third_party/unitree

# Clone the official Unitree SDK2 repo
git clone https://github.com/unitreerobotics/unitree_sdk2.git unitree_sdk2_official

# Copy missing folders to the existing SDK directory
cp -r unitree_sdk2_official/lib /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2/
cp -r unitree_sdk2_official/include /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2/
cp -r unitree_sdk2_official/thirdparty /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2/
```

Build and install the SDK (without examples to avoid version mismatch errors):

```bash
cd /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2
mkdir -p build && cd build
cmake .. -DBUILD_EXAMPLES=OFF
sudo make install
```

> **Note:** If you get permission errors when removing the build folder, use `sudo rm -rf build` first.

#### 5. Missing `asio` library (for ublox_gps)

```bash
sudo apt install libasio-dev -y
```

After applying all fixes, rebuild:

```bash
cd /opt/mybotshop
colcon build --symlink-install
```

### Sourcing the Workspace

After building, source the workspace:

```bash
source /opt/ros/humble/setup.bash
source /opt/mybotshop/install/setup.bash
```

To make this permanent, add to `~/.bashrc`:

```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
echo "source /opt/mybotshop/install/setup.bash" >> ~/.bashrc
```

---

## Known Issues

### b2_platform Build Failure - Wrong SportClient Namespace

**Status:** RESOLVED (?)

**Problem:** The `b2_platform` package fails to build with linker errors:

```
undefined reference to `unitree::robot::go2::SportClient::SwitchGait(int)'
undefined reference to `unitree::robot::go2::SportClient::BodyHeight(float)'
```

**Root Cause Analysis:**

After investigation, we found that:

1. The file `b2_lowlevel_example.cpp` uses `unitree::robot::go2::SportClient` (Go2 robot client)
2. The official Unitree SDK2's Go2 SportClient does **NOT** have `SwitchGait()` or `BodyHeight()` methods
3. However, the official SDK's **B2 SportClient** (`unitree::robot::b2::SportClient`) **DOES** have these methods
4. The other files (`b2_highroscontrol.cpp`, `b2w_test.cpp`) correctly use `unitree::robot::b2::SportClient`

**File Analysis:**

| File | Uses Namespace | Has SwitchGait/BodyHeight |
|------|----------------|---------------------------|
| `b2_highroscontrol.cpp` | `unitree::robot::b2` | Yes (correct) |
| `b2w_test.cpp` | `unitree::robot::b2` | Yes (correct) |
| `b2_lowlevel_example.cpp` | `unitree::robot::go2` | No (WRONG - causes build failure) |

**Official SDK Comparison:**

| Client | `SwitchGait()` | `BodyHeight()` |
|--------|----------------|----------------|
| `go2::SportClient` (official) | NO | NO |
| `b2::SportClient` (official) | YES | YES |

**Impact:** Without `b2_platform`, the following functionality is unavailable:
- Robot hardware control (stand up, stand down, gaits)
- Joint state publishing
- Odometry publishing
- IMU data publishing
- Velocity command interface

**Workaround:** Build all other packages while skipping `b2_platform`:

```bash
cd /opt/mybotshop
colcon build --symlink-install --packages-skip b2_platform
```

This allows testing of:
- Gazebo simulation
- RViz visualization
- Navigation stack (in simulation)
- Sensor drivers (if hardware available)

**Applied Fix - Option A: Modify b2_lowlevel_example.cpp**

Changed `b2_lowlevel_example.cpp` to use the B2 SportClient instead of Go2:

1. Changed include from:
   ```cpp
   #include <unitree/robot/go2/sport/sport_client.hpp>
   ```
   to:
   ```cpp
   #include <unitree/robot/b2/sport/sport_client.hpp>
   ```

2. Changed all `unitree::robot::go2::SportClient` references to `unitree::robot::b2::SportClient`:
   - Line 17: Constructor parameter
   - Line 283: Class member variable
   - Line 291: main() instantiation

**Result:** All 26 packages now build successfully.

**Alternative Fix - Option B (not used):**

Copy the official SDK's B2 headers to replace the MyBotShop ones:

```bash
cp -r /opt/mybotshop/src/third_party/unitree/unitree_sdk2_official/include/unitree/robot/b2 \
      /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2/include/unitree/robot/
```

---

## Repository Structure Overview

### Main Packages (src/mybotshop/)

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| b2_platform | 1.0.0 | High-level robot driver (joints, odom, IMU, gaits) | Not tested |
| b2_bringup | 0.0.8 | System startup orchestration | Not tested |
| b2_control | 1.2.0 | Motion control, EKF localization | Not tested |
| b2_description | 1.0.0 | URDF/Xacro robot model | Not tested |
| b2_lidars | 1.2.0 | Livox MID360 LiDAR integration | Not tested |
| b2_gps | 1.2.0 | GPS/GNSS (FixPosition, Drotek, Emlid) | Not tested |
| b2_depth_camera | 1.2.0 | RealSense D435i/D405 | Not tested |
| b2_usbcam | 1.2.0 | USB camera interface | Not tested |
| b2_vision_action | 1.0.0 | YOLOv8 object detection, autonomous tasks | Not tested |
| b2_nav2 | 1.0.0 | Navigation2 (SLAM, odom nav, map nav, GPS nav) | Not tested |
| b2_viz | 0.0.1 | RViz2 visualization | Not tested |
| b2_webserver | 5.0.0 | Flask web control interface | Not tested |
| b2_srvs | 0.1.0 | Custom ROS2 services/messages | Not tested |
| b2_nano | 1.0.0 | Jetson Nano integration | Not tested |
| b2_gazebo | 1.0.0 | Gazebo Fortress simulation | Not tested |

### Third-Party Packages (src/third_party/)

| Category | Package | Purpose | Status |
|----------|---------|---------|--------|
| GPS | ublox-ros2 | u-blox GPS/RTK driver | Not tested |
| GPS | fixposition_driver | FixPosition GNSS/INS | Not tested |
| GPS | reach_rs_ros2_humble | Emlid Reach RS driver | Not tested |
| GPS | ntrip_client | NTRIP for RTK corrections | Not tested |
| LiDAR | livox_ros_driver2 | Livox MID360/HAP driver | Not tested |
| LiDAR | livox_sdk | Livox SDK library | Not tested |
| Unitree | unitree_sdk2 | Low-level robot SDK | Not tested |
| Unitree | unitree_ros2 | ROS2 wrapper for Unitree | Not tested |

---

## Key Launch Files

### System Startup
- `b2_bringup/launch/system.launch.py` - Master launch (description + platform + control)

### Visualization
- `b2_viz/launch/view_robot.launch.py` - RViz2 visualization

### Navigation
- `b2_nav2/launch/odom_navi.launch.py` - Odometry-based navigation
- `b2_nav2/launch/map_navi.launch.py` - Pre-mapped navigation
- `b2_nav2/launch/slam.launch.py` - SLAM mapping
- `b2_nav2/launch/gps_navi.launch.py` - GPS navigation

### Sensors
- `b2_lidars/launch/livox_mid360.launch.py` - LiDAR
- `b2_depth_camera/launch/realsense_d435i.launch.py` - Depth camera
- `b2_gps/launch/fixposition.launch.py` - GPS

### Simulation
- `b2_gazebo/launch/b2_fortress_simulation.launch.py` - B2 simulation
- `b2_gazebo/launch/b2w_fortress_simulation.launch.py` - B2W (wheeled) simulation

---

## Testing Log

### [Date: 2025-12-08]

#### Initial Observations
- Repository cloned and README reviewed
- Network connection to robot confirmed
- Documentation structure created

#### Setup Completed
- Internet sharing from laptop to robot configured
- ROS2 Humble installed on robot
- Workspace copied and built (26 packages)
- Fixed b2_platform SDK namespace issue

#### ROS2 Topics from Robot Internal Systems

After sourcing the workspace, `ros2 topic list` shows topics from the robot's internal Unitree DDS system.

**Note:** `ros2 node list` returns empty because no custom nodes from our workspace are running yet. The topics are published by the robot's internal DDS middleware.

#### Tests Performed

**Date: 2025-12-09** - Complete topic verification (63 topics scanned)

**Robot State Topics:**

| Topic | Type | Status | Notes |
|-------|------|--------|-------|
| `/sportmodestate` | `unitree_go/msg/SportModeState` | Working (500 Hz) | Mode 7, IMU, position |
| `/odommodestate` | `unitree_go/msg/SportModeState` | Working (500 Hz) | Odometry data |
| `/lowstate` | `unitree_go/msg/LowState` | Working (~500 Hz) | 12 leg + 4 arm motors, IMU, battery (69% SOC) |
| `/lowcmd` | `unitree_go/msg/LowCmd` | Working | Motor commands (damping mode active) |
| `/lf/sportmodestate` | `unitree_go/msg/SportModeState` | Working | Duplicate stream |
| `/lf/odommodestate` | `unitree_go/msg/SportModeState` | Working | Duplicate stream |
| `/lf/lowstate` | `unitree_go/msg/LowState` | Working | Duplicate stream |
| `/multiplestate` | `std_msgs/msg/String` | Empty `{}` | |

**Camera Topics:**

| Topic | Type | Status | Notes |
|-------|------|--------|-------|
| `/front_videohub/videostream` | `unitree_go/msg/Go2FrontVideoData` | Working (43 Hz) | 720p video data |
| `/back_videohub/videostream` | `unitree_go/msg/Go2FrontVideoData` | Working (43 Hz) | 720p video data |
| `/panorama_videohub/videostream` | `unitree_go/msg/Go2FrontVideoData` | No publisher | Camera not installed |

**API Topics:**

| Topic | Type | Status | Notes |
|-------|------|--------|-------|
| `/api/sport/request` | `unitree_api/msg/Request` | Working | Queries bodyHeight, footRaiseHeight, speedLevel |
| `/api/sport/response` | `unitree_api/msg/Response` | Working | Returns gait=0, mode=7 |
| `/api/motion_switcher/*` | `unitree_api/msg/*` | No data | Mode switching API |
| `/api/robot_state/*` | `unitree_api/msg/*` | No data | Robot state API |
| `/api/slam_*` | `unitree_api/msg/*` | No data | SLAM operations API |
| `/api/obstacles_avoid/*` | `unitree_api/msg/*` | No data | Obstacle avoidance API |
| `/api/*_videohub/*` | `unitree_api/msg/*` | No data | Video control API |

**Input Topics:**

| Topic | Type | Status | Notes |
|-------|------|--------|-------|
| `/wirelesscontroller` | `unitree_go/msg/WirelessController` | Working | Controller buttons/joysticks |

**LiDAR/SLAM Topics (No LiDAR installed):**

| Topic | Type | Status |
|-------|------|--------|
| `/lio_sam_ros2/mapping/cloud_registered` | `sensor_msgs/msg/PointCloud2` | No publisher |
| `/lio_sam_ros2/mapping/odometry` | `nav_msgs/msg/Odometry` | No publisher |
| `/unitree/slam_mapping/points` | `sensor_msgs/msg/PointCloud2` | No publisher |
| `/unitree/slam_relocation/points` | `sensor_msgs/msg/PointCloud2` | No publisher |
| `/slam_info` | `std_msgs/msg/String` | No publisher |

**GPS Topics (Tested indoors - no signal):**

| Topic | Type | Status |
|-------|------|--------|
| `/gps` | `std_msgs/msg/String` | No publisher |
| `/gnss` | `std_msgs/msg/String` | No publisher |

**Topics with Invalid/Missing Message Types:**

| Topic | Type | Issue |
|-------|------|-------|
| `/EstimatorData` | `unitree_go/msg/EstimatorData` | Message definition not available |
| `/SymState` | `unitree_go/msg/SymState` | Message definition not available |
| `/SymState_back` | `unitree_go/msg/SymState` | Message definition not available |
| `/config_change_status` | `unitree_go/msg/ConfigChangeStatus` | Message definition not available |
| `/pctoimage_local` | `unitree_interfaces/msg/PcToImage` | `unitree_interfaces` package missing |
| `/qt_add_edge` | `unitree_interfaces/msg/QtEdge` | `unitree_interfaces` package missing |
| `/qt_add_node` | `unitree_interfaces/msg/QtNode` | `unitree_interfaces` package missing |
| `/qt_command` | `unitree_interfaces/msg/QtCommand` | `unitree_interfaces` package missing |

**System/WebRTC Topics (No data during scan):**

| Topic | Type | Notes |
|-------|------|-------|
| `/public_network_status` | `std_msgs/msg/String` | Network status |
| `/selftest` | `std_msgs/msg/String` | Self-test results |
| `/servicestate` | `std_msgs/msg/String` | Service state |
| `/rtc_status` | `std_msgs/msg/String` | WebRTC status |
| `/webrtcreq`, `/webrtcres` | `std_msgs/msg/String` | WebRTC signaling |

**Summary:**
- **13 topics actively publishing data**
- **8 topics with missing message definitions** (need `unitree_interfaces` package)
- **LiDAR/SLAM topics** waiting for hardware installation
- **GPS topics** need outdoor testing
- **API topics** use request/response pattern - only `/api/sport/*` showed activity

**Available Unitree message interfaces:**
- `unitree_go/msg/*` - Robot state, commands, sensors
- `unitree_api/msg/*` - API request/response messages
- `unitree_hg/msg/*` - Hand/gripper messages (if equipped)

**Missing interfaces (causes "invalid type" errors):**
- `unitree_interfaces/msg/*` - Qt interface messages, PcToImage

---

## Commands Reference

### SSH to Robot
```bash
ssh -X unitree@192.168.123.164
# Password: Unitree0408
```

### Check ROS2 Topics (from robot or properly configured host)
```bash
ros2 topic list
```

### Echo a Topic (safe, read-only)
```bash
ros2 topic echo /sportmodestate --once
ros2 topic echo /lowstate --once
```

### Launch Hardware Node

> **WARNING:** This will activate sport_mode on the robot. Ensure:
> - Robot is in a safe area with space around it
> - Emergency stop / controller is ready
> - No one is near the robot's legs

```bash
ros2 launch b2_platform hardware.launch.py
```

### Robot Mode Control (requires hardware node running)
```bash
# Stand up
ros2 service call /b2_unit_001/hardware/modes b2_srvs/srv/B2Modes "{request_data: 'stand_up'}"

# Stand down
ros2 service call /b2_unit_001/hardware/modes b2_srvs/srv/B2Modes "{request_data: 'stand_down'}"

# Damp (disable motors - robot will collapse!)
ros2 service call /b2_unit_001/hardware/modes b2_srvs/srv/B2Modes "{request_data: 'damp'}"

# Recovery stand (if robot fell)
ros2 service call /b2_unit_001/hardware/modes b2_srvs/srv/B2Modes "{request_data: 'recovery'}"
```

### Teleop (requires hardware node running)
```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard cmd_vel:=/b2_unit_001/hardware/cmd_vel
```

---

## Issues Found

_(To be documented as we discover issues)_

| Issue | Package | Description | Resolution |
|-------|---------|-------------|------------|
| | | | |

---

## Working Features

| Feature | Package | Notes |
|---------|---------|-------|
| ROS2 topic discovery | ros2cli | `ros2 topic list` shows robot's internal DDS topics |
| ROS2 topic echo | ros2cli | Works with CycloneDDS, displays real-time robot state |
| ROS2 topic hz | ros2cli | Confirmed /sportmodestate at 500Hz |
| Controller input | Internal | Wireless controller commands visible via /wirelesscontroller |
| Robot state | Internal | `/sportmodestate`, `/lowstate`, `/odommodestate` all working |
| Front camera | Internal | `/front_videohub/videostream` at 43Hz |
| Back camera | Internal | `/back_videohub/videostream` at 43Hz |
| Motor telemetry | Internal | 12 leg motors + 4 arm motors reporting via `/lowstate` |
| Battery status | Internal | SOC, voltage, cell voltages via `/lowstate` |
| RViz visualization | b2_description | Robot model displays correctly (see instructions below) |
| Camera streaming | GStreamer | Front and rear cameras via multicast UDP (see below) |

---

## Camera Streaming

The B2 robot streams front and rear cameras via UDP multicast. You can view these streams from any computer connected to the robot's network (192.168.123.x subnet).

### Prerequisites

Install GStreamer on your laptop:

```bash
sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-libav
```

### Viewing Camera Streams

> **Note:** Replace `<lan_interface>` with your laptop's ethernet interface connected to the robot (e.g., `enx607d09a9a14e`, `eth0`). Run `ip addr` to find yours.

**Front Camera (port 1720):**

```bash
gst-launch-1.0 udpsrc address=230.1.1.1 port=1720 multicast-iface=<lan_interface> ! application/x-rtp, media=video, encoding-name=H264 ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! autovideosink
```

**Rear Camera (port 1721):**

```bash
gst-launch-1.0 udpsrc address=230.1.1.1 port=1721 multicast-iface=<lan_interface> ! application/x-rtp, media=video, encoding-name=H264 ! rtph264depay ! h264parse ! avdec_h264 ! videoconvert ! autovideosink
```

### Technical Details

| Camera | Multicast Address | Port | Encoding |
|--------|-------------------|------|----------|
| Front  | 230.1.1.1         | 1720 | H.264    |
| Rear   | 230.1.1.1         | 1721 | H.264    |

---

## Arduino SBUS Receiver

The robot has an Arduino Nano Every connected via USB that reads SBUS signals from an RC receiver. This can be used for manual RC control of the robot.

### Serial Port Access

The Arduino is accessible at `/dev/arduino_sbus` (persistent symlink created via udev rule).

**Read serial data:**

```bash
cat /dev/arduino_sbus
# Or with screen (115200 baud):
screen /dev/arduino_sbus 115200
# Exit screen: Ctrl+A, then K, then Y
```

**Example output (16 SBUS channels, tab-separated):**

```
172	990	988	992	172	172	172	1811	992	992	0	0	0	0	0	0
```

### Udev Rule

The persistent symlink is created by `/etc/udev/rules.d/99-arduino-sbus.rules`:

```
SUBSYSTEM=="tty", ATTRS{idVendor}=="2341", ATTRS{idProduct}=="0058", ATTRS{serial}=="C428CA9B51544E5450202020FF093F1C", SYMLINK+="arduino_sbus", MODE="0666"
```

### Technical Details

| Property | Value |
|----------|-------|
| Device | Arduino Nano Every |
| Vendor ID | 2341 |
| Product ID | 0058 |
| Serial | C428CA9B51544E5450202020FF093F1C |
| Baud Rate | 115200 |
| Symlink | `/dev/arduino_sbus` |

---

## WiFi and Remote Access (ZeroTier)

The robot can connect to WiFi for remote access via ZeroTier, allowing SSH from anywhere with internet.

### USB WiFi Dongle

The robot's built-in Intel WiFi antenna may not be connected. A USB WiFi dongle (Edimax AC600) is used instead.

**Driver Installation (RTL8812AU):**

```bash
sudo apt update
sudo apt install -y dkms git build-essential
git clone https://github.com/aircrack-ng/rtl8812au.git
cd rtl8812au
sudo make dkms_install
sudo modprobe 88XXau
```

**Verify interface:**

```bash
ip link | grep wlx
```

The dongle creates interface `wlx08beac1d4bb0`.

### Connecting to eduroam (Enterprise WiFi)

A script at `~/Documents/roberto/connect_eduroam.sh` handles eduroam connection:

```bash
./connect_eduroam.sh
# Prompts for username and password
```

The connection is saved and will auto-connect on boot.

**Manual connection:**

```bash
nmcli connection add type wifi ifname wlx08beac1d4bb0 con-name "eduroam-IPv6only" ssid "eduroam-IPv6only" \
  wifi-sec.key-mgmt wpa-eap \
  802-1x.eap peap \
  802-1x.phase2-auth mschapv2 \
  802-1x.identity "YOUR_USERNAME" \
  802-1x.password "YOUR_PASSWORD"

nmcli connection modify "eduroam-IPv6only" connection.autoconnect yes
nmcli connection up "eduroam-IPv6only"
```

### ZeroTier Setup

ZeroTier provides a stable IP for remote access regardless of network.

**Install ZeroTier:**

```bash
curl -s https://install.zerotier.com | sudo bash
```

**Join network:**

```bash
sudo zerotier-cli join <network-id>
```

**Check status:**

```bash
sudo zerotier-cli listnetworks
```

### SSH Access Methods

| Method | Command | Address | When to use |
|--------|---------|---------|-------------|
| Ethernet | `ssh b2` | 192.168.123.164 | Direct cable connection |
| WiFi (IPv6) | `ssh b2wifi` | 2001:4ca0:... | Same WiFi network |
| ZeroTier | `ssh b2zerotier` | 172.22.206.213 | **Anywhere with internet** |

**SSH config (`~/.ssh/config` on laptop):**

```
Host b2
    HostName 192.168.123.164
    User unitree
    ForwardX11 yes

Host b2wifi
    HostName 2001:4ca0:0:f29f:7248:65d3:52e4:a122
    User unitree
    ForwardX11 yes

Host b2zerotier
    HostName 172.22.206.213
    User unitree
    ForwardX11 yes
```

### Technical Details

| Component | Details |
|-----------|---------|
| USB WiFi Dongle | Edimax AC600 (7392:a812) |
| WiFi Driver | RTL8812AU (aircrack-ng) |
| WiFi Interface | wlx08beac1d4bb0 |
| ZeroTier IP | 172.22.206.213 |
| ZeroTier Network | test_net (8286ac0e4758019e) |

---

## Teleop (Keyboard Control)

Control the robot's movement using keyboard commands.

> **Note:** Due to DDS/CycloneDDS network issues, teleop must be run **on the robot** (via SSH), not from the host PC.

### Running Teleop

SSH into the robot and run:

```bash
ssh b2zerotier  # or ssh b2 if using ethernet
source /opt/ros/humble/setup.bash
source /opt/mybotshop/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ROS_DOMAIN_ID=10 ros2 run teleop_twist_keyboard teleop_twist_keyboard cmd_vel:=/b2_366/hardware/cmd_vel
```

### Keyboard Controls

| Key | Action |
|-----|--------|
| `i` | Forward |
| `,` | Backward |
| `j` | Turn left |
| `l` | Turn right |
| `k` | Stop |
| `q`/`z` | Increase/decrease speed |

### Important Notes

- **Robot namespace:** `b2_366` (not `b2_unit_001` as in default README)
- **Working topic:** `/b2_366/hardware/cmd_vel`
- **Not working:** `/b2_366/controls/cmd_vel`
- Make sure the robot is standing before sending movement commands
- Have the physical controller ready for emergency stop

---

## RViz Robot Visualization

Visualizing the robot model in RViz requires multiple components running together. The launch files use `ROS_DOMAIN_ID=10` and a namespace, which requires special setup.

![B2 Robot in RViz](utils/assets/Screenshot%20from%202025-12-09%2018-18-40.png)

### Quick Start

**Terminal 1 - Robot State Publisher:**
```bash
source /opt/ros/humble/setup.bash
source /opt/mybotshop/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 launch b2_description b2_description.launch.py
```

**Terminal 2 - Joint State Publisher** (required for limbs to display):
```bash
source /opt/ros/humble/setup.bash
source /opt/mybotshop/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_DOMAIN_ID=10
ros2 run joint_state_publisher joint_state_publisher --ros-args -r robot_description:=/b2_366/robot_description -r joint_states:=/b2_366/joint_states
```

**Terminal 3 - RViz:**
```bash
source /opt/ros/humble/setup.bash
source /opt/mybotshop/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 launch b2_description view_robot.launch.py
```

### RViz Configuration

After RViz opens, you may need to fix the Fixed Frame:
1. In the left panel, under **Global Options**
2. Change **Fixed Frame** from `odom` to `base_link`
3. The robot model should now display correctly with all limbs

### Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| Limbs at origin (white bars) | No joint states being published | Run joint_state_publisher with correct namespace remapping |
| "Frame [odom] does not exist" | Wrong fixed frame | Change Fixed Frame to `base_link` |
| Body visible but no limbs | Missing TF transforms | Ensure joint_state_publisher is running |
| No robot visible | Namespace mismatch | Check that ROS_DOMAIN_ID=10 is set |
| joint_state_publisher_gui shows no sliders | Namespace mismatch | Use `--ros-args -r` to remap topics to `/b2_366/` namespace |

### Technical Notes

- The launch file sets `ROS_DOMAIN_ID=10` to isolate from other ROS2 traffic
- Namespace is `b2_366` (from environment variable, not `b2_unit_001` as in code)
- `robot_state_publisher` publishes TF transforms but needs `joint_states` input
- `joint_state_publisher` reads the URDF and publishes default joint positions
- The URDF has 12 revolute joints (3 per leg: hip, thigh, calf)

---

## Notes

- **CRITICAL:** Must use CycloneDDS instead of FastDDS - the default FastDDS causes "Illegal instruction" crashes
- Workspace expected at `/opt/mybotshop` on the robot
- Robot internal systems publish DDS topics automatically (no node launch needed to see them)
- The `b2_platform` hardware node is needed to send commands to the robot

---

## CycloneDDS Requirement (IMPORTANT)

The robot's onboard PC crashes with "Illegal instruction (core dumped)" when using the default FastDDS middleware. This affects `ros2 topic echo`, `ros2 topic hz`, and other ROS2 commands.

**Symptoms:**
```
ros2 topic echo /sportmodestate
Illegal instruction (core dumped)

ros2 topic hz /sportmodestate
Illegal instruction (core dumped)
```

**Solution:** Use CycloneDDS middleware instead:

```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

**Make it permanent** by adding to `~/.bashrc`:

```bash
echo 'export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp' >> ~/.bashrc
```

**Full environment setup for robot:**

```bash
source /opt/ros/humble/setup.bash
source /opt/mybotshop/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Or add all three lines to `~/.bashrc` for automatic setup on login.

**Verified working with CycloneDDS:**
- `ros2 topic list` - Lists all topics
- `ros2 topic hz /sportmodestate` - Shows 500Hz update rate
- `ros2 topic echo /sportmodestate` - Displays robot state data in real-time

---

## Known Issues / Future Work

### Hardware Issues to Investigate

| Issue | Status | Notes |
|-------|--------|-------|
| Built-in WiFi antenna | Not working | Intel Wi-Fi 6E AX211 detected but no networks found. Antenna cables inside robot may be disconnected. Need to check hardware. |
| RealSense D435i depth camera | Not detected | Camera physically installed but not showing in `lsusb`. USB cable may be disconnected or connected to different PC. Need to check hardware. |

### Future Integration Tasks

| Task | Description | Priority |
|------|-------------|----------|
| Z1 Robotic Arm Integration | The B2W robot has a Unitree Z1 robotic arm mounted on top. Need to integrate arm control with the robot's ROS2 system. | High |
| Teleop from Host PC | DDS/CycloneDDS communication between laptop and robot on ROS_DOMAIN_ID=10 not working. Need to debug network/multicast configuration. | Medium |
| Gazebo Simulation | gz_ros2_control YAML loading issue on Ubuntu 20.04. Controllers fail to load properly. | Low |

### Hardware Checklist

**WiFi Antenna:**
- [ ] Open robot PC compartment
- [ ] Locate Intel WiFi card
- [ ] Check if antenna cables (usually 2) are connected
- [ ] Verify antenna wires route to external antennas

**RealSense D435i:**
- [ ] Locate camera USB cable inside robot
- [ ] Verify USB cable is connected to PC4 (192.168.123.164)
- [ ] Check if camera needs external power
- [ ] Test with `rs-enumerate-devices` after connecting

**Z1 Robotic Arm:**
- [ ] Document arm's current connection method
- [ ] Identify ROS2 packages for Z1 control
- [ ] Test arm movement independently
- [ ] Integrate arm control with B2W locomotion

---

## Session Summary - 2025-12-08

### Accomplished
1. Established network connection to robot via LAN
2. Set up internet sharing from laptop to robot (NAT/IP forwarding)
3. Installed ROS2 Humble on robot's onboard PC (Ubuntu 22.04)
4. Copied workspace to `/opt/mybotshop` on robot
5. Ran `b2_install.bash` to install dependencies
6. Fixed multiple build issues:
   - Missing `config` folder in b2_depth_camera
   - Missing `rtcm_msgs` package
   - Missing Livox SDK
   - Missing Unitree SDK2 libraries (cloned from official repo)
   - Missing `libasio-dev`
   - Fixed `b2_lowlevel_example.cpp` namespace issue (go2 → b2)
7. Successfully built all 26 packages
8. Verified ROS2 topics from robot's internal systems are visible
9. Discovered CycloneDDS requirement (FastDDS causes "Illegal instruction" crashes)
10. Confirmed ROS2 communication works - can echo topics and see real-time robot data at 500Hz

### Not Yet Tested
- Launching `b2_platform` hardware node
- Robot control via ROS2 services (stand up, stand down, etc.)
- Teleop control
- External sensor drivers (LiDAR - not installed, GPS - needs outdoor test)
- Navigation stack
- Gazebo simulation

---

## Session Summary - 2025-12-09

### Accomplished
1. Created utility scripts:
   - `utils/share_internet.sh` - Share laptop internet with robot
   - `utils/check_all_topics.sh` - Scan all ROS2 topics and save results
2. Set up SSH alias (`ssh b2`) for easier robot access
3. Complete ROS2 topic verification (63 topics scanned):
   - 13 topics actively publishing data
   - 8 topics with missing message definitions (`unitree_interfaces` package)
   - Documented all topic statuses in detail
4. RViz robot visualization working:
   - Debugged namespace issues (`b2_366` vs `b2_unit_001`)
   - Debugged ROS_DOMAIN_ID isolation (domain 10)
   - Fixed joint_state_publisher remapping for correct namespace
   - Fixed RViz Fixed Frame (`base_link` instead of `odom`)
   - Robot model now displays correctly with all 4 limbs
5. Updated documentation with:
   - Complete topic verification results
   - RViz setup instructions and troubleshooting guide
   - Screenshot of working RViz visualization

---

## Session Summary - 2026-01-14

### Accomplished: SBUS RC Teleop Integration

Created a new ROS2 package `b2_rc_teleop` that reads SBUS RC receiver data from Arduino and controls the robot.

#### Package Details

| Component | Location |
|-----------|----------|
| Package | `/opt/mybotshop/src/mybotshop/b2_rc_teleop/` |
| Config | `config/sbus_teleop.yaml` |
| Launch | `launch/sbus_teleop.launch.py` |
| Topic | `/b2_366/rc_teleop/cmd_vel` |
| Priority | 18 in twist_mux |

#### Channel Mapping

| Channel | Function | Notes |
|---------|----------|-------|
| CH3 | Forward/backward (`linear.x`) | |
| CH4 | Strafe left/right (`linear.y`) | Inverted in config |
| CH5 | Yaw rotation (`angular.z`) | Inverted in config |
| CH14 | Dead-man switch | Must be > 900 to enable |

**Note:** CH1, CH2, CH6 (body pitch/roll/height) are not supported via cmd_vel on B2.

#### Issues Fixed During Implementation

| Issue | Solution |
|-------|----------|
| Executable in wrong path | Symlink from `bin/` to `lib/b2_rc_teleop/` |
| pyserial missing | `pip3 install pyserial` |
| CH4/CH5 inverted | Negative max values in config |
| Arduino not ready on startup | DTR reset added to node |
| twist_mux not forwarding | Restart twist_mux to load new config |
| b2-hardware crashed | Restart b2-hardware service |

#### Systemd Service

The RC teleop runs as a systemd service that starts automatically after `b2-hardware` and `b2-twistmux`.

**Service files:**
- `/lib/systemd/system/b2-rc-teleop.service`
- `/usr/sbin/b2-rc-teleop-start`

**Service commands:**
```bash
# Start/stop/restart
sudo systemctl start b2-rc-teleop
sudo systemctl stop b2-rc-teleop
sudo systemctl restart b2-rc-teleop

# Check status
sudo systemctl status b2-rc-teleop

# Enable/disable on boot
sudo systemctl enable b2-rc-teleop
sudo systemctl disable b2-rc-teleop
```

#### Manual Startup (if needed)

If services don't start automatically after reboot:

```bash
# 1. Restart required services
sudo systemctl restart b2-hardware
sudo systemctl restart b2-twistmux
sudo systemctl restart b2-rc-teleop

# 2. Verify all services are running
sudo systemctl status b2-hardware --no-pager
sudo systemctl status b2-twistmux --no-pager
sudo systemctl status b2-rc-teleop --no-pager
```

#### Manual Launch (for development/debugging)

```bash
source /opt/ros/humble/setup.bash
source /opt/mybotshop/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 launch b2_rc_teleop sbus_teleop.launch.py
```

#### Monitoring

```bash
# Watch RC teleop output
ROS_DOMAIN_ID=10 ros2 topic echo /b2_366/rc_teleop/cmd_vel

# Watch final command to robot
ROS_DOMAIN_ID=10 ros2 topic echo /b2_366/hardware/cmd_vel
```

### Working Features Updated

| Feature | Package | Notes |
|---------|---------|-------|
| RC Teleop | b2_rc_teleop | SBUS via Arduino, dead-man switch on CH14 |
| Robot movement | b2_platform | Forward, strafe, yaw via cmd_vel |
| Keyboard teleop | teleop_twist_keyboard | Works via `/b2_366/hardware/cmd_vel` |

### Not Yet Tested
- External sensor drivers (LiDAR - not installed, GPS - needs outdoor test)
- Navigation stack
- Gazebo simulation

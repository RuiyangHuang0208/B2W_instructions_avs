# Livox MID-360 LiDAR Setup Guide

This guide documents the installation process for the Livox MID-360 LiDAR with ROS2 Humble (built from source).

## Hardware Setup

### Network Configuration

The MID-360 uses ethernet for communication. Default network settings:
- **LiDAR default IP range:** `192.168.1.1xx` (where xx = last 2 digits of serial number)
- **Required host IP:** Must be in the same subnet (e.g., `192.168.1.50`)

### Physical Connection

1. Connect the MID-360 via the M12 aviation connector breakout cable:
   - **Power cable** (red/black) → 9-27V DC power supply
   - **Ethernet cable** (RJ45) → Host PC (direct or via USB-C ethernet adapter)

2. Add a static IP to the ethernet interface:
   ```bash
   # Find your ethernet interface name
   ip link show

   # Add IP address (replace enxXXXXXX with your interface)
   sudo ip addr add 192.168.1.50/24 dev enxXXXXXXXXXXXX
   ```

3. Verify connection:
   ```bash
   # Scan for LiDAR (common IPs: 192.168.1.100-130)
   for ip in 192.168.1.{100..130}; do
       ping -c 1 -W 0.2 $ip &>/dev/null && echo "FOUND: $ip"
   done
   ```

## Software Installation

### Prerequisites

```bash
# Install PCL (Point Cloud Library)
sudo apt install libpcl-dev

# Install APR (Apache Portable Runtime) - required by Livox SDK
sudo apt install libapr1-dev
```

### Step 1: Build and Install Livox SDK2

```bash
cd /opt/mybotshop/src/third_party/lidar/8May2025_livox_sdk

# Fix CMake version if needed (change 3.0 to 3.5 in all CMakeLists.txt)
find . -name "CMakeLists.txt" -exec sed -i 's/cmake_minimum_required(VERSION 3.0)/cmake_minimum_required(VERSION 3.5)/g' {} \;

# Build
mkdir -p build && cd build
cmake .. && make -j$(nproc)

# Install (installs to /usr/local/lib and /usr/local/include)
sudo make install
```

### Step 2: Build pcl_msgs and pcl_conversions (if not already installed)

If you built ROS2 from source and don't have pcl_conversions:

```bash
cd /home/avs_robotdog/ros2_humble/src

# Clone pcl_msgs
git clone https://github.com/ros-perception/pcl_msgs.git -b ros2

# Clone perception_pcl (contains pcl_conversions)
git clone https://github.com/ros-perception/perception_pcl.git -b humble

# Build
cd /home/avs_robotdog/ros2_humble
source install/setup.bash
colcon build --packages-select pcl_msgs
source install/setup.bash
colcon build --packages-select pcl_conversions
```

### Step 3: Setup Livox ROS2 Driver

```bash
cd /opt/mybotshop/src/third_party/lidar/8May2025_livox_ros_driver2

# Copy required files from official repo (if missing)
# Clone official repo to get missing files
cd /tmp && git clone --depth 1 https://github.com/Livox-SDK/livox_ros_driver2.git
cp /tmp/livox_ros_driver2/package_ROS2.xml /opt/mybotshop/src/third_party/lidar/8May2025_livox_ros_driver2/
cp -r /tmp/livox_ros_driver2/launch_ROS2 /opt/mybotshop/src/third_party/lidar/8May2025_livox_ros_driver2/

# Copy launch_ROS2 to launch (required by CMakeLists.txt)
cd /opt/mybotshop/src/third_party/lidar/8May2025_livox_ros_driver2
cp -r launch_ROS2 launch

# Ensure package.xml exists (copy from package_ROS2.xml if missing)
cp package_ROS2.xml package.xml
```

### Step 4: Configure LiDAR IP Addresses

Edit the config file to match your network setup:

```bash
nano /opt/mybotshop/src/third_party/lidar/8May2025_livox_ros_driver2/config/MID360_config.json
```

Update these fields:
```json
{
  "MID360": {
    "host_net_info" : {
      "cmd_data_ip" : "192.168.1.50",      // Your host PC IP
      "push_msg_ip": "192.168.1.50",
      "point_data_ip": "192.168.1.50",
      "imu_data_ip" : "192.168.1.50"
    }
  },
  "lidar_configs" : [
    {
      "ip" : "192.168.1.103"               // Your LiDAR IP (found in step above)
    }
  ]
}
```

### Step 5: Build the ROS2 Driver

```bash
cd /opt/mybotshop/src/third_party/lidar/8May2025_livox_ros_driver2

# Source ROS2
source /home/avs_robotdog/ros2_humble/install/setup.bash

# Build
colcon build --packages-select livox_ros_driver2 --cmake-args -Wno-dev
```

## Running the Driver

### Terminal 1: Launch the driver
```bash
source /home/avs_robotdog/ros2_humble/install/setup.bash
source /opt/mybotshop/src/third_party/lidar/8May2025_livox_ros_driver2/install/setup.bash
ros2 launch livox_ros_driver2 msg_MID360_launch.py
```

### Terminal 2: Visualize with RViz2
```bash
source /home/avs_robotdog/ros2_humble/install/setup.bash
source /opt/mybotshop/src/third_party/lidar/8May2025_livox_ros_driver2/install/setup.bash
ros2 launch livox_ros_driver2 rviz_MID360_launch.py
```

Or launch RViz2 manually:
```bash
rviz2
```
Then:
1. Set **Fixed Frame** to `livox_frame`
2. Click **Add** → **By topic** → select `/livox/lidar` → **PointCloud2**

## Troubleshooting

### LiDAR not found on network
- Verify power is connected (LEDs should be active on the LiDAR)
- Check ethernet link: `ip link show` (should show state UP)
- Verify IP is assigned: `ip addr show <interface>`
- Try pinging the LiDAR directly

### Build errors
- **CMake version error:** Update `cmake_minimum_required(VERSION 3.0)` to `VERSION 3.5`
- **pcl_conversions not found:** Build pcl_msgs and pcl_conversions as shown above
- **launch folder missing:** Copy `launch_ROS2` to `launch`

### No point cloud data
- Verify LiDAR IP in config matches actual LiDAR IP
- Verify host IP in config matches your PC's IP on that interface
- Check firewall isn't blocking UDP ports 56100-56500

## MID-360 Specifications

| Parameter | Value |
|-----------|-------|
| Detection Range | 0.1m - 100m |
| FOV | 360° horizontal, 59° vertical |
| Point Rate | 200,000 pts/s |
| IMU | 3-axis accelerometer + 3-axis gyroscope (200 Hz) |
| Power | 9-27V DC, ~10W typical |
| IP Rating | IP67 |
| Weight | 265g |

## File Locations

- **Livox SDK2:** `/opt/mybotshop/src/third_party/lidar/8May2025_livox_sdk`
- **ROS2 Driver:** `/opt/mybotshop/src/third_party/lidar/8May2025_livox_ros_driver2`
- **Config files:** `/opt/mybotshop/src/third_party/lidar/8May2025_livox_ros_driver2/config/`
- **Launch files:** `/opt/mybotshop/src/third_party/lidar/8May2025_livox_ros_driver2/launch/`

---
*Document created: 2026-02-10*
*Tested on: Ubuntu 22.04, ROS2 Humble (built from source)*

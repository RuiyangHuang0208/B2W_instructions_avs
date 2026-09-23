# B2 Installation Notes

This document tracks deviations from the official README and additional steps required during installation.

## Installation Date: 2025-12-10

---

## Summary for Support

We encountered **14 issues** while following the README instructions for "Installation (B2 Nvidia)". The installation eventually succeeded, but required significant manual intervention. Below is a quick summary:

| Issue | Step | Category | Description |
|-------|------|----------|-------------|
| 1 | Step 3: `b2_install.bash` | Missing Files | `99-super-usb.rules` and `90-logitech.rules` not in repo |
| 2 | Step 4: `colcon build` | Missing SDK | Livox SDK not built/installed by `b2_install.bash` |
| 3 | Step 4: `colcon build` | Missing Directory | `b2_depth_camera/config` directory missing from repo |
| 4 | Step 4: `colcon build` | Incomplete SDK | Unitree SDK2 missing `lib/`, `include/`, `thirdparty/` |
| 5 | Step 4: `colcon build` | Code Bug | `b2_lowlevel_example.cpp` uses wrong namespace (go2 vs b2) |
| 6 | Step 4: `colcon build` | Missing Dependency | `libasio-dev` not installed by `b2_install.bash` |
| 7 | Step 6: Testing | Config Mismatch | CycloneDDS config hardcodes `eth0`, robot uses `eno2` |
| 8 | Webserver | Missing Dependencies | `waitress`, `playsound`, `vncserver`, `websockify` not installed |
| 9 | Webserver | Config Mismatch | CycloneDDS config has wrong WiFi interface (`wlxe4fac44c84d6`) |
| 10 | Webserver | Config Error | CycloneDDS duplicate interface error after fix attempt |
| 11 | Webserver | Environment | `RMW_IMPLEMENTATION` not set to CycloneDDS |
| 12 | Services | Not Installed | Systemd services not installed, webserver shows all "Inactive" |
| 13 | Services | Code Bug | C++ source files hardcode `eth0` instead of `eno2` |
| 14 | Services | Environment | `ROS_DOMAIN_ID=10` not set in robot's `.bashrc` |

**Key Recommendations:**
1. `b2_install.bash` should build/install the Livox SDK from `src/third_party/lidar/8May2025_livox_sdk`
2. `b2_install.bash` should download complete Unitree SDK2 or include all required files
3. Fix the namespace bug in `b2_lowlevel_example.cpp` (go2 → b2)
4. Add `libasio-dev` to apt dependencies
5. Include `b2_depth_camera/config` directory in repo (even if empty)
6. Document/auto-detect network interface for CycloneDDS config
7. Provide the missing udev rules files or remove them from install script
8. Add `waitress`, `playsound`, `tigervnc-standalone-server`, and `websockify` to dependencies
9. CycloneDDS config should use a single Domain with auto-detected or configurable interface
10. Ensure `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` is set in setup scripts

---

## Detailed Issues

---

## Issue 1: Missing udev Rules Files

**Occurred during:** Step 3 - Running `b2_install.bash`

**Problem:** Install script fails to copy udev rules:
```
cp: cannot stat 'b2_bringup/debian/99-super-usb.rules': No such file or directory
cp: cannot stat 'b2_bringup/debian/90-logitech.rules': No such file or directory
```

**Cause:** These files don't exist in the repository.

**Impact:** Unknown - possibly affects USB device permissions or Logitech controller support.

**Status:** TODO - Ask MyBotShop if these files are needed and where to get them.

---

## Issue 2: Missing Livox LiDAR SDK

**Occurred during:** Step 4 - Running `colcon build`

**Problem:** Build fails with:
```
CMake Error at CMakeLists.txt:61 (find_library):
  Could not find LIVOX_LIDAR_SDK_LIBRARY using the following names:
  liblivox_lidar_sdk_shared.so, /usr/local/lib
Failed   <<< livox_ros_driver2 [12.1s, exited with code 1]
```

**Cause:** The `b2_install.bash` script does not install the Livox LiDAR SDK, but the `livox_ros_driver2` package requires it.

**Note:** The Livox LiDAR (MID360) is optional hardware that may not be installed on all B2 robots. However, since the package is included in the repository and the build attempts to compile it, the SDK must be installed for the build to succeed.

**Solution:** The SDK source is included in the repo at `src/third_party/lidar/8May2025_livox_sdk` but `b2_install.bash` does not build/install it. Install manually:
```bash
cd /opt/mybotshop/src/third_party/lidar/8May2025_livox_sdk
mkdir -p build && cd build
cmake ..
make -j4
sudo make install
```

**Recommendation:** The `b2_install.bash` script should either:
1. Include the SDK build/install steps, OR
2. Provide a clear option to skip optional hardware packages

---

## Issue 3: Missing `b2_depth_camera/config` Directory

**Occurred during:** Step 4 - Running `colcon build`

**Problem:** Build fails with:
```
CMake Error at ament_cmake_symlink_install/ament_cmake_symlink_install.cmake:100 (message):
  ament_cmake_symlink_install_directory() can't find
  '/opt/mybotshop/src/mybotshop/b2_depth_camera/config'
```

**Cause:** `CMakeLists.txt` (line 29) references a `config` directory that doesn't exist in the repository.

**Note:** The Intel RealSense depth camera is optional hardware that may not be installed on all B2 robots. However, the package is included in the repo with an incomplete directory structure, causing build failures.

**Solution:** Create empty config directory:
```bash
mkdir -p /opt/mybotshop/src/mybotshop/b2_depth_camera/config
```

**Recommendation:** Either:
1. Include the missing `config` directory in the repo (even if empty), OR
2. Fix `CMakeLists.txt` to not require a non-existent directory, OR
3. Provide a way to skip optional hardware packages during build

---

## Issue 4: Missing Unitree SDK2 Libraries (for b2_platform)

**Occurred during:** Step 4 - Running `colcon build`

**Problem:** Build fails with multiple errors:
```
fatal error: unitree/common/log/log.hpp: No such file or directory
/usr/bin/ld: cannot find -lunitree_sdk2: No such file or directory
Failed   <<< b2_platform [18.9s, exited with code 2]
```

**Cause:** The repository includes a partial Unitree SDK2 at `src/third_party/unitree/17Mar2025_unitree_sdk2/` but is missing:
- `lib/` directory (prebuilt libraries)
- Complete `include/` files
- `thirdparty/` dependencies

**Solution:** Clone the official SDK and copy missing parts:
```bash
cd /opt/mybotshop/src/third_party/unitree

# Clone the official Unitree SDK2 repo
git clone https://github.com/unitreerobotics/unitree_sdk2.git unitree_sdk2_official

# Copy missing folders to the existing SDK directory
cp -r unitree_sdk2_official/lib /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2/
cp -r unitree_sdk2_official/include /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2/
cp -r unitree_sdk2_official/thirdparty /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2/
```

Then build and install:
```bash
cd /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2
mkdir -p build && cd build
cmake .. -DBUILD_EXAMPLES=OFF
sudo make install
```

> **Note:** The `-DBUILD_EXAMPLES=OFF` flag is required because the official SDK examples have API mismatches (e.g., `go2_trajectory_follow.cpp` uses `TrajectoryFollow()` which doesn't exist in the Go2 SportClient). Skipping examples avoids these build errors.

**Recommendation:** The `b2_install.bash` script should either include complete SDK files or automate this download/install process.

---

## Issue 5: Wrong SportClient Namespace in b2_lowlevel_example.cpp

**Occurred during:** Step 4 - Running `colcon build`

**Problem:** Build fails with linker errors:
```
undefined reference to `unitree::robot::go2::SportClient::SwitchGait(int)'
undefined reference to `unitree::robot::go2::SportClient::BodyHeight(float)'
Failed   <<< b2_platform [22.2s, exited with code 2]
```

**Cause:** The file `b2_platform/src/b2_lowlevel_example.cpp` incorrectly uses `unitree::robot::go2::SportClient` (Go2 robot), but:
- Go2 SportClient does NOT have `SwitchGait()` or `BodyHeight()` methods
- B2 SportClient (`unitree::robot::b2::SportClient`) DOES have these methods
- Other files in the same package (`b2_highroscontrol.cpp`, `b2w_test.cpp`) correctly use `b2::SportClient`

**Solution:** Change from Go2 to B2 namespace:
```bash
sed -i 's|unitree/robot/go2/sport/sport_client.hpp|unitree/robot/b2/sport/sport_client.hpp|g' /opt/mybotshop/src/mybotshop/b2_platform/src/b2_lowlevel_example.cpp
sed -i 's|unitree::robot::go2::SportClient|unitree::robot::b2::SportClient|g' /opt/mybotshop/src/mybotshop/b2_platform/src/b2_lowlevel_example.cpp
```

**Recommendation:** This is a bug in the repository that should be fixed upstream.

---

## Issue 6: Missing `asio` Library (for ublox_gps)

**Occurred during:** Step 4 - Running `colcon build`

**Problem:** Build of `ublox_gps` fails due to missing asio library.

**Solution:**
```bash
sudo apt install libasio-dev -y
```

**Recommendation:** Add `libasio-dev` to the apt packages installed by `b2_install.bash`.

---

## Issue 7: CycloneDDS Network Interface Mismatch

**Occurred during:** Step 6 - Testing the installation

**Problem:** After installation, `ros2 topic list` fails with:
```
eth0: does not match an available interface.
[ERROR] [rmw_cyclonedds_cpp]: rmw_create_node: failed to create domain, error Error
```

**Cause:** The CycloneDDS config file `b2_bringup/config/multi_robot_cyclone.xml` hardcodes `eth0` as the network interface, but the B2's onboard PC uses `eno2`.

**Solution:** Update the interface name in the config file:
```bash
sed -i 's/name="eth0"/name="eno2"/g' /opt/mybotshop/src/mybotshop/b2_bringup/config/multi_robot_cyclone.xml
```

**Recommendation:** The config file should either:
1. Use a more generic interface name, OR
2. Auto-detect the active interface, OR
3. Document that users need to update this setting for their specific hardware

---

## Issue 8: Missing Webserver Dependencies

**Occurred during:** Launching `b2_webserver`

**Problem:** Webserver launch fails with multiple errors:
```
FileNotFoundError: [Errno 2] No such file or directory: 'vncserver'
FileNotFoundError: [Errno 2] No such file or directory: 'websockify'
ModuleNotFoundError: No module named 'waitress'
ModuleNotFoundError: No module named 'playsound'
```

**Cause:** The `b2_install.bash` script does not install:
- `waitress` - Python WSGI server used by the webserver
- `playsound` - Python module for audio playback
- `tigervnc-standalone-server` - VNC server for remote desktop
- `websockify` - WebSocket to TCP proxy for noVNC

**Solution:** Install missing dependencies:
```bash
# Install Python modules
pip3 install waitress playsound

# Install system packages
sudo apt update
sudo apt install -y tigervnc-standalone-server websockify
```

**Recommendation:** Add these dependencies to `b2_install.bash`:
- Add `waitress playsound` to the pip install section
- Add `tigervnc-standalone-server websockify` to the apt install section

---

## Issue 9: CycloneDDS Config - Wrong WiFi Interface Name

**Occurred during:** Launching `b2_webserver` (after fixing Issue 8)

**Problem:** Webserver fails with:
```
wlxe4fac44c84d6: does not match an available interface.
[ERROR] [rmw_cyclonedds_cpp]: rmw_create_node: failed to create domain, error Error
```

**Cause:** The CycloneDDS config file `b2_bringup/config/multi_robot_cyclone.xml` hardcodes a WiFi interface name (`wlxe4fac44c84d6`) that doesn't exist on this robot. The robot's actual WiFi interface is `wlo1`.

**Analysis:** The config file had two Domain sections, each with an `<Interfaces>` block:
- `Domain Id="any"` with `eno2` (LAN - correct)
- `Domain Id="10"` with `wlxe4fac44c84d6` (WiFi - wrong interface name)

**Solution:** The config needed to be simplified to use only the LAN interface (`eno2`) since WiFi (`wlo1`) was DOWN anyway.

---

## Issue 10: CycloneDDS Config - Duplicate Interface Error

**Occurred during:** Launching `b2_webserver` (after attempting to fix Issue 9)

**Problem:** After changing the WiFi interface to `eno2`, CycloneDDS fails with:
```
eno2: the same interface may not be selected twice
```

**Cause:** Both Domain sections (`Id="any"` and `Id="10"`) were now using `eno2`, which CycloneDDS doesn't allow.

**Solution:** Simplify the CycloneDDS config to have only ONE Domain section:

```bash
cat > /opt/mybotshop/src/mybotshop/b2_bringup/config/multi_robot_cyclone.xml << 'EOF'
<?xml version="1.0" encoding="UTF-8" ?>
<CycloneDDS xmlns="https://cdds.io/config"
    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="https://cdds.io/config https://raw.githubusercontent.com/eclipse-cyclonedds/cyclonedds/master/etc/cyclonedds.xsd">
    <Domain Id="any">
        <General>
            <Interfaces>
                <NetworkInterface name="eno2" priority="default" multicast="default" />
            </Interfaces>
            <AllowMulticast>true</AllowMulticast>
            <EnableMulticastLoopback>true</EnableMulticastLoopback>
        </General>
        <Discovery>
            <ParticipantIndex>auto</ParticipantIndex>
            <MaxAutoParticipantIndex>100</MaxAutoParticipantIndex>
        </Discovery>
    </Domain>
</CycloneDDS>
EOF
```

**Important:** Make sure the `EOF` marker is typed on its own line to complete the heredoc, and verify the file doesn't contain the literal text "EOF" at the end.

---

## Issue 11: RMW Implementation Not Set

**Occurred during:** Launching `b2_webserver` (after fixing CycloneDDS config)

**Problem:** CycloneDDS config is correct but webserver still fails to create ROS2 node.

**Cause:** The `RMW_IMPLEMENTATION` environment variable was not set (or commented out in `.bashrc`), so ROS2 wasn't using CycloneDDS.

**Solution:** Export the RMW implementation before launching:
```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 launch b2_webserver webserver.launch.py
```

**Recommendation:** Ensure this is set in the robot's `.bashrc` or in the `b2_bringup/config/setup.bash`:
```bash
echo 'export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp' >> ~/.bashrc
```

---

## Webserver - Complete Setup Summary

After resolving Issues 8-11, the webserver can be started successfully. Here's the complete setup:

### Prerequisites (on robot)

```bash
# Install missing dependencies
pip3 install waitress playsound
sudo apt update
sudo apt install -y tigervnc-standalone-server websockify

# Ensure CycloneDDS is properly configured (single Domain, correct interface)
# See Issue 10 for the correct config content

# Set RMW implementation
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

### Starting the Webserver

```bash
ros2 launch b2_webserver webserver.launch.py
```

### Accessing the Webserver

- **URL:** http://192.168.123.164:9000
- **Username:** admin
- **Password:** mybotshop

### Webserver Features

The webserver provides:
- Service management (start/stop robot services)
- Console access
- Teleoperation controls
- Map visualization
- Battery status
- ROS bag recording

---

## Installation Progress

- [x] Step 0: Create `/opt/mybotshop` directory
- [x] Step 1: Copy repository to robot
- [x] Step 2: Set hostname and timezone
- [x] Step 3: Run `b2_install.bash` (completed with warnings - see issues above)
- [x] Step 4: Build workspace with colcon (required manual fixes for Issues 2-6)
- [x] Step 5: Add sourcing to `.bashrc`
- [x] Step 6: Test the installation - `ros2 topic list` shows 65 topics ✓

---

## Issue 12: Systemd Services Not Installed

**Occurred during:** Testing webserver service management (2026-01-05)

**Problem:** The webserver shows all services as "Inactive". Clicking "Re-activate Srvs." does nothing because the systemd services were never installed.

```bash
systemctl list-units --all | grep b2
# Returns nothing (no b2 services found)

ls /etc/systemd/system/ | grep b2
# Returns nothing
```

**Cause:** The `startup_installer.py` script was never run to install the systemd services.

**Solution:** Run the startup installer on the robot:
```bash
cd /opt/mybotshop
python3 src/mybotshop/b2_bringup/scripts/startup_installer.py
sudo systemctl daemon-reload
```

Then enable the core services:
```bash
sudo systemctl enable --now b2-hardware
sudo systemctl enable --now b2-domain-bridge
sudo systemctl enable --now b2-statepublisher
sudo systemctl enable --now b2-twistmux
sudo systemctl enable --now b2-webserver
sudo systemctl enable --now b2-front-video
sudo systemctl enable --now b2-rear-video
```

**Recommendation:** The README should include running `startup_installer.py` as a post-installation step.

---

## Issue 13: Network Interface Hardcoded as eth0 in C++ Source Files

**Occurred during:** Starting b2-hardware service (2026-01-05)

**Problem:** After installing systemd services, `b2-hardware` fails immediately with:
```
eth0: does not match an available interface.
[ERROR] [b2_highroscontrol-1]: process has died [pid 22158, exit code -6]
```

**Cause:** Multiple C++ source files have `eth0` hardcoded for Unitree SDK communication, but the B2 robot uses `eno2`:
- `b2_platform/src/b2_highroscontrol.cpp:309` - `ChannelFactory::Instance()->Init(0, "eth0")`
- `b2_platform/src/b2_lowlevel_example.cpp:289` - `ChannelFactory::Instance()->Init(0, "eth0")`
- `b2_platform/src/b2_video.cpp:10` - `declare_parameter<std::string>("lan_port", "eth0")`
- `b2_platform/config/b2_platform.yaml` - `lan_port: "eth0"`

**Solution:** Change `eth0` to `eno2` in all affected files:

```bash
# On the robot, edit the source files:
sed -i 's/"eth0"/"eno2"/g' /opt/mybotshop/src/mybotshop/b2_platform/src/b2_highroscontrol.cpp
sed -i 's/"eth0"/"eno2"/g' /opt/mybotshop/src/mybotshop/b2_platform/src/b2_lowlevel_example.cpp
sed -i 's/"eth0"/"eno2"/g' /opt/mybotshop/src/mybotshop/b2_platform/src/b2_video.cpp
sed -i 's/lan_port: "eth0"/lan_port: "eno2"/g' /opt/mybotshop/src/mybotshop/b2_platform/config/b2_platform.yaml

# Rebuild the package:
cd /opt/mybotshop
colcon build --packages-select b2_platform --symlink-install

# Restart affected services:
sudo systemctl restart b2-hardware b2-front-video b2-rear-video
```

**Recommendation:** The network interface should be configurable via parameter or environment variable, not hardcoded.

---

## Issue 14: ROS_DOMAIN_ID Not Set on Robot

**Occurred during:** Testing ROS topic communication (2026-01-05)

**Problem:** Host PC cannot see robot topics even with correct CycloneDDS configuration. The robot's `ROS_DOMAIN_ID` was empty/unset.

```bash
# On robot:
echo $ROS_DOMAIN_ID
# Returns empty
```

**Cause:** The robot's `.bashrc` did not have `ROS_DOMAIN_ID=10` set. The host was using domain 10, but the robot was using the default domain 0.

**Solution:** Add to robot's `.bashrc`:
```bash
echo 'export ROS_DOMAIN_ID=10' >> ~/.bashrc
source ~/.bashrc
```

**Recommendation:** The `b2_bringup/config/setup.bash` should export `ROS_DOMAIN_ID=10` explicitly.

---

## Services Setup - Complete Summary (2026-01-05)

After resolving Issues 12-14, all core services are running. Here's the complete working setup:

### Prerequisites

1. Run startup installer:
```bash
cd /opt/mybotshop
python3 src/mybotshop/b2_bringup/scripts/startup_installer.py
```

2. Fix network interface (eth0 → eno2) in source files and rebuild.

3. Set ROS_DOMAIN_ID:
```bash
echo 'export ROS_DOMAIN_ID=10' >> ~/.bashrc
source ~/.bashrc
```

### Enable Services

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now b2-hardware b2-domain-bridge b2-statepublisher b2-twistmux b2-webserver b2-front-video b2-rear-video
```

### Verify

```bash
# Check services
systemctl list-units --all | grep b2

# Check topics (should show 26+ topics)
ros2 topic list
```

### Working Services

After setup, these services should be `active (running)`:
- b2-hardware
- b2-domain-bridge
- b2-statepublisher
- b2-twistmux
- b2-webserver
- b2-front-video
- b2-rear-video

### Available Topics

With all services running, `ros2 topic list` shows:
```
/b2_366/autonomous_high_priority/cmd_vel
/b2_366/autonomous_low_priority/cmd_vel
/b2_366/autonomous_mid_priority/cmd_vel
/b2_366/base/odom
/b2_366/cmd_vel
/b2_366/diagnostics
/b2_366/drotek/ublox_gps_node/fix
/b2_366/e_stop
/b2_366/hardware/cmd_vel
/b2_366/joint_states
/b2_366/joy_teleop/cmd_vel
/b2_366/lf/lowstate
/b2_366/map
/b2_366/odommodestate
/b2_366/sensor/battery/state
/b2_366/sensor/camera_info
/b2_366/sensor/front/camera_raw
/b2_366/sensor/imu/data
/b2_366/sensor/rear/camera_raw
/b2_366/steamdeck_joy_teleop/cmd_vel
/b2_366/tf
/b2_366/tf_static
/b2_366/twist_marker_server/cmd_vel
/b2_366/webserver/cmd_vel
/parameter_events
/rosout
```

---

## Notes

- Robot PC: Ubuntu 22.04 (Jammy)
- ROS2: Humble
- Repository branch: humble-nvidia
- Session date for Issues 12-14: 2026-01-05

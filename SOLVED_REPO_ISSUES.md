# GitHub Issues for qre_b2 Repository

These are ready-to-submit GitHub issues based on the installation problems encountered on 2025-12-10.

**Environment:**
- Robot PC: Ubuntu 22.04 (Jammy)
- ROS2: Humble
- Repository branch: humble-nvidia

---

## Issue 1: Missing udev rules files (99-super-usb.rules, 90-logitech.rules)

**Title:** `b2_install.bash fails: missing udev rules files 99-super-usb.rules and 90-logitech.rules`

**Body:**

I was following the "Installation (B2 Nvidia)" instructions in the README. When I ran Step 3 (`b2_install.bash`), the script failed to copy the udev rules:

```
cp: cannot stat 'b2_bringup/debian/99-super-usb.rules': No such file or directory
cp: cannot stat 'b2_bringup/debian/90-logitech.rules': No such file or directory
```

These files are referenced in the install script but don't exist in the repository.

**Questions:**
1. Are these files needed for the B2 to function properly?
2. If yes, can they be added to the repository?
3. If no, can the install script be updated to remove these references?

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia

---

## Issue 2: Livox SDK not built/installed by b2_install.bash

**Title:** `colcon build fails: Livox SDK not installed (livox_ros_driver2 cannot find liblivox_lidar_sdk_shared.so)`

**Body:**

I was following the "Installation (B2 Nvidia)" instructions in the README. After completing Step 3 (`b2_install.bash`), I ran Step 4 (`colcon build`). The build failed with:

```
CMake Error at CMakeLists.txt:61 (find_library):
  Could not find LIVOX_LIDAR_SDK_LIBRARY using the following names:
  liblivox_lidar_sdk_shared.so, /usr/local/lib
Failed   <<< livox_ros_driver2 [12.1s, exited with code 1]
```

The Livox SDK source code is included in the repository at `src/third_party/lidar/8May2025_livox_sdk`, but `b2_install.bash` does not build or install it.

**Workaround:**
I had to manually build and install the SDK:
```bash
cd /opt/mybotshop/src/third_party/lidar/8May2025_livox_sdk
mkdir -p build && cd build
cmake ..
make -j4
sudo make install
```

**Suggestion:**
The `b2_install.bash` script should include the Livox SDK build/install steps, since the SDK source is already in the repo and `livox_ros_driver2` requires it.

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia

---

## Issue 3: Missing b2_depth_camera/config directory

**Title:** `colcon build fails: b2_depth_camera/config directory missing from repository`

**Body:**

I was following the "Installation (B2 Nvidia)" instructions in the README. When I ran Step 4 (`colcon build`), the build failed with:

```
CMake Error at ament_cmake_symlink_install/ament_cmake_symlink_install.cmake:100 (message):
  ament_cmake_symlink_install_directory() can't find
  '/opt/mybotshop/src/mybotshop/b2_depth_camera/config'
```

The `CMakeLists.txt` in `b2_depth_camera` (line 29) references a `config` directory that doesn't exist in the repository:
```cmake
install(DIRECTORY config launch
  DESTINATION share/${PROJECT_NAME}
)
```

**Workaround:**
I had to manually create the directory:
```bash
mkdir -p /opt/mybotshop/src/mybotshop/b2_depth_camera/config
```

**Suggestion:**
Either:
1. Include the `config` directory in the repo (even if empty with a `.gitkeep`), OR
2. Update `CMakeLists.txt` to handle the case when `config` doesn't exist

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia

---

## Issue 4: Incomplete Unitree SDK2 (missing lib/, include/, thirdparty/)

**Title:** `colcon build fails: Unitree SDK2 missing lib/, include/, and thirdparty/ directories`

**Body:**

I was following the "Installation (B2 Nvidia)" instructions in the README. When I ran Step 4 (`colcon build`), the build failed with:

```
fatal error: unitree/common/log/log.hpp: No such file or directory
/usr/bin/ld: cannot find -lunitree_sdk2: No such file or directory
Failed   <<< b2_platform [18.9s, exited with code 2]
```

The repository includes a partial Unitree SDK2 at `src/third_party/unitree/17Mar2025_unitree_sdk2/` but it's missing:
- `lib/` directory (prebuilt libraries)
- Complete `include/` files
- `thirdparty/` dependencies

**Workaround:**
I had to clone the official Unitree SDK2 and copy the missing parts:
```bash
cd /opt/mybotshop/src/third_party/unitree
git clone https://github.com/unitreerobotics/unitree_sdk2.git unitree_sdk2_official

cp -r unitree_sdk2_official/lib /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2/
cp -r unitree_sdk2_official/include /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2/
cp -r unitree_sdk2_official/thirdparty /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2/

cd /opt/mybotshop/src/third_party/unitree/17Mar2025_unitree_sdk2
mkdir -p build && cd build
cmake .. -DBUILD_EXAMPLES=OFF
sudo make install
```

Note: `-DBUILD_EXAMPLES=OFF` is required because the official SDK examples have API mismatches.

**Suggestion:**
Either:
1. Include the complete SDK files in the repository, OR
2. Have `b2_install.bash` automate the download and installation

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia

---

## Issue 5: Bug in b2_lowlevel_example.cpp - wrong namespace (go2 instead of b2)

**Title:** `Bug: b2_lowlevel_example.cpp uses go2::SportClient instead of b2::SportClient`

**Body:**

I was following the "Installation (B2 Nvidia)" instructions in the README. When I ran Step 4 (`colcon build`), the build failed with linker errors:

```
undefined reference to `unitree::robot::go2::SportClient::SwitchGait(int)'
undefined reference to `unitree::robot::go2::SportClient::BodyHeight(float)'
Failed   <<< b2_platform [22.2s, exited with code 2]
```

The file `b2_platform/src/b2_lowlevel_example.cpp` incorrectly uses the Go2 namespace:
- Uses: `unitree::robot::go2::SportClient`
- Should use: `unitree::robot::b2::SportClient`

The Go2 SportClient does NOT have `SwitchGait()` or `BodyHeight()` methods, but the B2 SportClient does.

Other files in the same package (`b2_highroscontrol.cpp`, `b2w_test.cpp`) correctly use `b2::SportClient`.

**Workaround:**
```bash
sed -i 's|unitree/robot/go2/sport/sport_client.hpp|unitree/robot/b2/sport/sport_client.hpp|g' /opt/mybotshop/src/mybotshop/b2_platform/src/b2_lowlevel_example.cpp
sed -i 's|unitree::robot::go2::SportClient|unitree::robot::b2::SportClient|g' /opt/mybotshop/src/mybotshop/b2_platform/src/b2_lowlevel_example.cpp
```

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia

---

## Issue 6: Missing dependency libasio-dev

**Title:** `colcon build fails: missing libasio-dev dependency for ublox_gps`

**Body:**

I was following the "Installation (B2 Nvidia)" instructions in the README. When I ran Step 4 (`colcon build`), the build of `ublox_gps` failed due to missing asio library.

**Workaround:**
```bash
sudo apt install libasio-dev -y
```

**Suggestion:**
Add `libasio-dev` to the apt packages installed by `b2_install.bash`.

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia

---

## Issue 7: CycloneDDS config hardcodes eth0 interface

**Title:** `CycloneDDS config hardcodes eth0 - fails on B2 which uses eno2`

**Body:**

I was following the "Installation (B2 Nvidia)" instructions in the README. After completing all installation steps, I tried to test with `ros2 topic list` (Step 6) and got:

```
eth0: does not match an available interface.
[ERROR] [rmw_cyclonedds_cpp]: rmw_create_node: failed to create domain, error Error
```

The CycloneDDS config file `b2_bringup/config/multi_robot_cyclone.xml` hardcodes `eth0` as the network interface, but the B2's onboard PC uses `eno2`.

**Workaround:**
```bash
sed -i 's/name="eth0"/name="eno2"/g' /opt/mybotshop/src/mybotshop/b2_bringup/config/multi_robot_cyclone.xml
```

**Suggestion:**
Either:
1. Use a wildcard or auto-detect the active interface, OR
2. Document in the README that users need to update this setting for their specific hardware, OR
3. Add a configuration option in the install script to set the interface name

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia
- Network interface on B2: `eno2`

---

## Issue 8: Missing webserver dependencies (waitress, vncserver, websockify)

**Title:** `b2_webserver launch fails: missing waitress, tigervnc-standalone-server, and websockify`

**Body:**

After completing the installation, I tried to launch the webserver with `ros2 launch b2_webserver webserver.launch.py` and got multiple errors:

```
FileNotFoundError: [Errno 2] No such file or directory: 'vncserver'
FileNotFoundError: [Errno 2] No such file or directory: 'websockify'
ModuleNotFoundError: No module named 'waitress'
```

The `b2_install.bash` script does not install the required dependencies for the webserver:
- `waitress` - Python WSGI server
- `playsound` - Python module for audio playback
- `tigervnc-standalone-server` - VNC server
- `websockify` - WebSocket to TCP proxy

**Workaround:**
```bash
# Install Python modules
pip3 install waitress playsound

# Install system packages
sudo apt update
sudo apt install -y tigervnc-standalone-server websockify
```

**Suggestion:**
Add these dependencies to `b2_install.bash`:
- Add `waitress playsound` to the pip install section
- Add `tigervnc-standalone-server websockify` to the apt install section

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia

---

## Issue 9: CycloneDDS config hardcodes wrong WiFi interface

**Title:** `CycloneDDS config hardcodes non-existent WiFi interface wlxe4fac44c84d6`

**Body:**

After installing the webserver dependencies (Issue 8), I tried to launch the webserver with `ros2 launch b2_webserver webserver.launch.py` and got:

```
wlxe4fac44c84d6: does not match an available interface.
[ERROR] [rmw_cyclonedds_cpp]: rmw_create_node: failed to create domain, error Error
```

The CycloneDDS config file `b2_bringup/config/multi_robot_cyclone.xml` hardcodes a WiFi interface name (`wlxe4fac44c84d6`) that doesn't exist on our B2 robot. The robot's actual WiFi interface is `wlo1`.

**Root Cause:**
The config file has two Domain sections with different interface names:
- `Domain Id="any"` uses `eno2` (LAN)
- `Domain Id="10"` uses `wlxe4fac44c84d6` (wrong WiFi interface)

**Suggestion:**
The CycloneDDS config should either:
1. Use only the LAN interface (`eno2`) since WiFi may not always be connected
2. Auto-detect available interfaces
3. Use a configurable interface name set during installation

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia
- Robot LAN interface: `eno2`
- Robot WiFi interface: `wlo1`

---

## Issue 10: CycloneDDS config causes duplicate interface error

**Title:** `CycloneDDS config with multiple Domain sections causes "same interface selected twice" error`

**Body:**

Related to Issue 9. When attempting to fix the wrong WiFi interface by using the same LAN interface (`eno2`) in both Domain sections, CycloneDDS fails with:

```
eno2: the same interface may not be selected twice
```

**Root Cause:**
The config file has two Domain sections (`Id="any"` and `Id="10"`), and CycloneDDS does not allow the same interface to be specified in multiple domains.

**Workaround:**
Simplify the config to use only ONE Domain section:

```xml
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
```

**Suggestion:**
The default CycloneDDS config should use a simpler single-Domain structure that works across different network configurations.

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia

---

## Issue 11: RMW_IMPLEMENTATION not set for CycloneDDS

**Title:** `Webserver fails because RMW_IMPLEMENTATION=rmw_cyclonedds_cpp is not set`

**Body:**

After fixing the CycloneDDS config (Issues 9-10), the webserver still failed to create a ROS2 node. The issue was that `RMW_IMPLEMENTATION` was not set or was commented out in `.bashrc`.

**Root Cause:**
The robot's `.bashrc` had the CycloneDDS export commented out:
```bash
#export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

Without this, ROS2 uses the default FastDDS middleware, which doesn't use the CycloneDDS config file.

**Workaround:**
```bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

**Suggestion:**
The `b2_bringup/config/setup.bash` should ensure `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` is exported, or the `.bashrc` setup instructions should make this clear.

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia

---

## Issue 12: Systemd services not installed by default

**Title:** `Webserver shows all services as "Inactive" - startup_installer.py never mentioned in README`

**Body:**

After completing the installation per the README, I opened the webserver and noticed all services show as "Inactive". Clicking "Re-activate Srvs." has no effect.

Investigation revealed that no systemd services exist:
```bash
systemctl list-units --all | grep b2
# Returns nothing

ls /etc/systemd/system/ | grep b2
# Returns nothing
```

The `startup_installer.py` script exists in the repository at `src/mybotshop/b2_bringup/scripts/startup_installer.py` but is never mentioned in the README installation instructions.

**Workaround:**
```bash
cd /opt/mybotshop
python3 src/mybotshop/b2_bringup/scripts/startup_installer.py
sudo systemctl daemon-reload
sudo systemctl enable --now b2-hardware b2-domain-bridge b2-statepublisher b2-twistmux b2-webserver
```

**Suggestion:**
Add running `startup_installer.py` as a post-installation step in the README.

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia

---

## Issue 13: Network interface eth0 hardcoded in C++ source files

**Title:** `Bug: b2_platform C++ files hardcode eth0 - should be configurable or use eno2`

**Body:**

After installing systemd services, the `b2-hardware` service fails immediately with:
```
eth0: does not match an available interface.
[ERROR] [b2_highroscontrol-1]: process has died [pid 22158, exit code -6]
```

The B2 robot's onboard PC uses `eno2` for its LAN interface, but multiple source files have `eth0` hardcoded:

1. `b2_platform/src/b2_highroscontrol.cpp:309`:
   ```cpp
   unitree::robot::ChannelFactory::Instance()->Init(0, "eth0");
   ```

2. `b2_platform/src/b2_lowlevel_example.cpp:289`:
   ```cpp
   unitree::robot::ChannelFactory::Instance()->Init(0, "eth0");
   ```

3. `b2_platform/src/b2_video.cpp:10`:
   ```cpp
   this->declare_parameter<std::string>("lan_port", "eth0");
   ```

4. `b2_platform/config/b2_platform.yaml`:
   ```yaml
   lan_port: "eth0"
   ```

**Workaround:**
```bash
sed -i 's/"eth0"/"eno2"/g' /opt/mybotshop/src/mybotshop/b2_platform/src/b2_highroscontrol.cpp
sed -i 's/"eth0"/"eno2"/g' /opt/mybotshop/src/mybotshop/b2_platform/src/b2_lowlevel_example.cpp
sed -i 's/"eth0"/"eno2"/g' /opt/mybotshop/src/mybotshop/b2_platform/src/b2_video.cpp
sed -i 's/lan_port: "eth0"/lan_port: "eno2"/g' /opt/mybotshop/src/mybotshop/b2_platform/config/b2_platform.yaml

cd /opt/mybotshop
colcon build --packages-select b2_platform --symlink-install
```

**Suggestion:**
Either:
1. Change the default from `eth0` to `eno2` (correct for B2 robot)
2. Make it configurable via ROS parameter or environment variable
3. Auto-detect the active interface

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia
- Robot LAN interface: `eno2`

---

## Issue 14: ROS_DOMAIN_ID=10 not set in setup scripts

**Title:** `ROS_DOMAIN_ID=10 not exported in setup.bash - host/robot communication fails`

**Body:**

After installation, the host PC cannot see robot topics even with correct CycloneDDS configuration. Investigation revealed that `ROS_DOMAIN_ID` was not set on the robot:

```bash
# On robot:
echo $ROS_DOMAIN_ID
# Returns empty (using default domain 0)
```

The `b2_bringup/config/host_setup.bash` correctly sets `ROS_DOMAIN_ID=10`, but the robot's `b2_bringup/config/setup.bash` does not set it at all.

**Workaround:**
```bash
echo 'export ROS_DOMAIN_ID=10' >> ~/.bashrc
source ~/.bashrc
```

**Suggestion:**
Add `export ROS_DOMAIN_ID=10` to `b2_bringup/config/setup.bash` so the robot and host use the same domain by default.

**Environment:**
- Ubuntu 22.04 (Jammy)
- ROS2 Humble
- Branch: humble-nvidia

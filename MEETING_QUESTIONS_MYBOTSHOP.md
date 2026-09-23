# Questions for MyBotShop - B2 Software Setup

> Prepared for meeting on 2025-12-09
> Based on issues encountered during ROS2 setup and testing

---

## 1. Installation Process - Missing Packages and Build Failures

We followed the installation instructions but encountered several issues that prevented the workspace from building. Here's what we had to fix:

### 1.1 Missing `config` folder in b2_depth_camera

The build failed because `b2_depth_camera/config/` folder was missing (referenced in CMakeLists.txt).

**Our fix:** Created empty folder with `.gitkeep`

**Questions:**
- What configuration files should be in this folder?
- Is this an oversight in the repository?

### 1.2 Missing `rtcm_msgs` package

Build failed for `ntrip_client` package.

**Our fix:** `sudo apt install ros-humble-rtcm-msgs`

**Questions:**
- Should this be added to the `b2_install.bash` script?

### 1.3 Missing Livox SDK

Build failed for `livox_ros_driver2`.

**Our fix:** Built and installed from `src/third_party/lidar/8May2025_livox_sdk`

**Questions:**
- Should the install script build this automatically?
- Is there documentation for this step?

### 1.4 Missing Unitree SDK2 libraries

The repository's `17Mar2025_unitree_sdk2` folder was missing:
- `lib/` folder (prebuilt libraries)
- Complete `include/` files
- `thirdparty/` dependencies

**Our fix:** Cloned official Unitree SDK2 from GitHub and copied these folders manually.

**Questions:**
- Should these files be included in the repository?
- Is there a specific version of the SDK we should use?
- Are there licensing issues preventing inclusion in the repo?

### 1.5 Missing `asio` library

Build failed for `ublox_gps`.

**Our fix:** `sudo apt install libasio-dev`

**Questions:**
- Should this be added to the `b2_install.bash` script?

### 1.6 Wrong namespace in `b2_lowlevel_example.cpp`

**File:** `src/mybotshop/b2_platform/src/b2_lowlevel_example.cpp`

The file used `unitree::robot::go2::SportClient` instead of `unitree::robot::b2::SportClient`, causing linker errors:

```
undefined reference to `unitree::robot::go2::SportClient::SwitchGait(int)'
undefined reference to `unitree::robot::go2::SportClient::BodyHeight(float)'
```

**Our fix:** Changed include and namespace from `go2` to `b2`:
```cpp
// From:
#include <unitree/robot/go2/sport/sport_client.hpp>
// To:
#include <unitree/robot/b2/sport/sport_client.hpp>
```

**Questions:**
- Is this a known issue?
- Was this file meant for the Go2 robot and accidentally included?
- Should we submit this fix back to you?

---

## 2. Missing Message Definitions

### 2.1 Missing `unitree_interfaces` package

During topic verification, we found 8 topics with invalid message types that require the `unitree_interfaces` package:

| Topic | Missing Type |
|-------|--------------|
| `/pctoimage_local` | `unitree_interfaces/msg/PcToImage` |
| `/qt_add_edge` | `unitree_interfaces/msg/QtEdge` |
| `/qt_add_node` | `unitree_interfaces/msg/QtNode` |
| `/qt_command` | `unitree_interfaces/msg/QtCommand` |

**Questions:**
- Is the `unitree_interfaces` package supposed to be included in the repository?
- Where can we obtain this package?
- Are these topics essential for normal operation?

### 2.2 Missing `unitree_go` message definitions

These `unitree_go` message types exist as topics but cannot be echoed:
- `unitree_go/msg/EstimatorData`
- `unitree_go/msg/SymState`
- `unitree_go/msg/ConfigChangeStatus`

**Questions:**
- Are these message definitions missing from the workspace?
- Are they published by Unitree's internal system and not meant to be accessed?

---

## 3. Launch File Configuration

### 3.1 Namespace discrepancy

The launch file `b2_description.launch.py` sets:
- `B2_NS` environment variable defaults to `b2_unit_001`
- But actual namespace used is `b2_366`

**Questions:**
- Where does `b2_366` come from?
- How should we configure the correct namespace for our robot?
- Is this robot-specific (serial number based)?

### 3.2 ROS_DOMAIN_ID isolation

The description launch file sets `ROS_DOMAIN_ID=10`, which isolates it from:
- The robot's internal DDS topics (on default domain)
- Other ROS2 nodes we might run

**Questions:**
- Is this intentional?
- What is the recommended domain ID setup?
- Should the robot's internal topics also be on domain 10?

### 3.3 Missing joint_state_publisher in launch

The `b2_description.launch.py` only launches `robot_state_publisher` but not `joint_state_publisher`, causing RViz to show disconnected limbs.

**Questions:**
- Should `joint_state_publisher` be added to the launch file?
- Or is there another node that should publish joint states?
- When running on the real robot, what publishes joint states?

---

## 4. Hardware and Sensors

### 4.1 Current hardware configuration

Our robot currently has:
- Front camera (working, 43Hz)
- Back camera (working, 43Hz)
- No LiDAR installed
- No panorama camera
- GPS (untested - indoors)

**Questions:**
- What is the full hardware specification we purchased?
- Is a LiDAR supposed to be installed?
- What GPS module is installed?

### 4.2 CycloneDDS requirement

The robot's onboard PC crashes with "Illegal instruction" when using FastDDS. We must use CycloneDDS.

**Questions:**
- Is this a known issue with the B2's onboard PC?
- Is there a specific CPU architecture limitation?
- Should CycloneDDS be set as default in the install script?

---

## 5. Testing and Operation

### 5.1 Safe testing procedure

We want to test the `b2_platform` hardware node but are concerned about safety.

**Questions:**
- What is the recommended procedure for first-time testing?
- What safety measures should be in place?
- Is there a simulation mode we can use first?
- What does `mode: 7` mean in `/sportmodestate`?

### 5.2 Robot modes

From `/api/sport/response` we see `gait=0, mode=7`.

**Questions:**
- What are all the possible modes and their meanings?
- What are the gait types available?
- How do we safely switch between modes?

---

## 6. Documentation

### 6.1 Missing documentation

**Questions:**
- Is there additional documentation beyond the README?
- Is there an API reference for the `b2_platform` services?
- Are there example scripts for common operations?
- Is there a hardware manual for the B2?

---

## 7. Support and Updates

**Questions:**
- How do we receive software updates?
- Is there a support channel for technical issues?
- Can we get access to the source repository for updates?
- How should we report bugs or issues we find?

---

## Summary of Changes We Made

For reference, here are all the modifications we made to get the system working:

1. Created `b2_depth_camera/config/.gitkeep` (missing folder)
2. Installed `ros-humble-rtcm-msgs`
3. Built and installed Livox SDK from `src/third_party/lidar/8May2025_livox_sdk`
4. Cloned official Unitree SDK2 and copied `lib/`, `include/`, `thirdparty/` to `17Mar2025_unitree_sdk2`
5. Installed `libasio-dev`
6. Changed `b2_lowlevel_example.cpp` from `go2::SportClient` to `b2::SportClient`
7. Set `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp` as required middleware

---

## Notes During Meeting

_(Space for notes)_


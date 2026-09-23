# Z1 Robotic Arm ROS2 Setup

> Documentation of Z1 arm integration with B2 robot using ROS2 Humble.
> Date: 2026-02-03

## Overview

The Unitree Z1 robotic arm is mounted on the B2 robot and connected via ethernet to the B2's onboard PC. We use the community-driven `z1_ros2` package for ROS2 control.

---

## Network Configuration

| Device | IP Address |
|--------|------------|
| Z1 Arm | `192.168.123.110` |
| B2 PC (eno2) | `192.168.123.164` |
| B2 Robot | `192.168.123.161` |

The Z1 communicates on the same network as the B2 robot (192.168.123.x subnet via `eno2` interface).

---

## Software Setup

### Package Location

- **Host PC:** `/home/avs_robotdog/Documents/z1_ros2`
- **B2 Robot:** `~/ros2_ws/src/z1_ros2`

### Repository

Community-driven ROS2 package: [idra-lab/z1_ros2](https://github.com/idra-lab/z1_ros2)

Supports: ROS2 Humble, Jazzy, Rolling

### Installation on B2

```bash
# Create workspace
mkdir -p ~/ros2_ws/src
cd ~/ros2_ws/src

# Clone repository (already done)
git clone https://github.com/idra-lab/z1_ros2.git

# Install dependencies
source /opt/ros/humble/setup.bash
rosdep update
rosdep install --from-paths ~/ros2_ws/src --ignore-src -y

# Build
cd ~/ros2_ws
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release

# Source workspace
source ~/ros2_ws/install/setup.bash
```

---

## Usage

### Launch Z1 Controller

```bash
source /opt/ros/humble/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch z1_bringup z1.launch.py starting_controller:=joint_trajectory_controller sim_ignition:=false
```

This launches:
- Robot state publisher
- ROS2 control node with Z1 hardware interface
- Joint trajectory controller
- RViz visualization

### Check Joint States

```bash
ros2 topic echo /joint_states --once
```

### Move Individual Joints

**Joint 1 (base rotation):**
```bash
ros2 action send_goal /joint_trajectory_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "{trajectory: {joint_names: [joint1, joint2, joint3, joint4, joint5, joint6], points: [{positions: [0.3, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 2}}, {positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 4}}]}}"
```

**Joint 2 (shoulder):**
```bash
ros2 action send_goal /joint_trajectory_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "{trajectory: {joint_names: [joint1, joint2, joint3, joint4, joint5, joint6], points: [{positions: [0.0, 0.5, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 2}}, {positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 4}}]}}"
```

**Joint 3 (elbow):**
```bash
ros2 action send_goal /joint_trajectory_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "{trajectory: {joint_names: [joint1, joint2, joint3, joint4, joint5, joint6], points: [{positions: [0.0, 0.0, 0.5, 0.0, 0.0, 0.0], time_from_start: {sec: 2}}, {positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 4}}]}}"
```

**Joint 4 (wrist pitch):**
```bash
ros2 action send_goal /joint_trajectory_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "{trajectory: {joint_names: [joint1, joint2, joint3, joint4, joint5, joint6], points: [{positions: [0.0, 0.0, 0.0, 0.5, 0.0, 0.0], time_from_start: {sec: 2}}, {positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 4}}]}}"
```

**Joint 5 (wrist roll):**
```bash
ros2 action send_goal /joint_trajectory_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "{trajectory: {joint_names: [joint1, joint2, joint3, joint4, joint5, joint6], points: [{positions: [0.0, 0.0, 0.0, 0.0, 0.5, 0.0], time_from_start: {sec: 2}}, {positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 4}}]}}"
```

**Joint 6 (wrist yaw):**
```bash
ros2 action send_goal /joint_trajectory_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "{trajectory: {joint_names: [joint1, joint2, joint3, joint4, joint5, joint6], points: [{positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.5], time_from_start: {sec: 2}}, {positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 4}}]}}"
```

### Gripper Control

Include `jointGripper` in the trajectory:
```bash
ros2 action send_goal /joint_trajectory_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "{trajectory: {joint_names: [joint1, joint2, joint3, joint4, joint5, joint6, jointGripper], points: [{positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, -0.5], time_from_start: {sec: 2}}, {positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 4}}]}}"
```

---

## Known Issues

### Serial Port Conflict with B2 RC Teleop

The Z1 and B2 RC teleop nodes both use `/dev/arduino_sbus`. Running both simultaneously causes laggy, unresponsive control.

**Solution:** Stop B2 RC teleop before using Z1 RC teleop:
```bash
sudo systemctl stop b2-rc-teleop.service
```

### Motor 3 (Elbow) Overheat Warning

**Symptom:** `[ERROR] Motor 3 windings overheat` appears during or after movement.

**Findings:**
- Motor 3 is not physically hot when error occurs
- Joint 3 has mechanical resistance (same when powered on/off)
- Error is likely overcurrent protection, not thermal
- Starting from different positions can avoid the error
- The default waypoint test (`ros2 run z1_examples waypoint_test.py`) triggers this issue

**Workarounds:**
1. Power cycle the Z1 arm if error persists on startup
2. Avoid returning to exact `[0,0,0,0,0,0]` position
3. Use gentle, single-joint movements
4. Start from a slightly offset position

**Recommendation:** Contact MyBotShop/Unitree support if issue persists frequently.

---

## ROS2 Topics & Actions

| Type | Name | Description |
|------|------|-------------|
| Topic | `/joint_states` | Current joint positions, velocities, efforts |
| Topic | `/robot_description` | URDF for visualization |
| Action | `/joint_trajectory_controller/follow_joint_trajectory` | Send trajectories |

---

## Configuration Files

| File | Location | Purpose |
|------|----------|---------|
| `config.xml` | `z1_hardware_interface/config/` | Z1 IP, port, collision settings |
| `z1_controllers.yaml` | `z1_bringup/config/` | Controller parameters |
| `z1.rviz` | `z1_bringup/rviz/` | RViz configuration |

---

## Joint Mapping

| Joint | Name | Description |
|-------|------|-------------|
| 1 | joint1 | Base rotation |
| 2 | joint2 | Shoulder |
| 3 | joint3 | Elbow |
| 4 | joint4 | Wrist pitch |
| 5 | joint5 | Wrist roll |
| 6 | joint6 | Wrist yaw |
| 7 | jointGripper | Gripper (0=open, -1.57=closed) |

---

## RC Teleop Package

### Package Location
- **Source:** `~/ros2_ws/src/z1_rc_teleop`
- **Config:** `z1_rc_teleop/config/sbus_teleop.yaml`

### Channel Mapping

| Channel | Joint | Notes |
|---------|-------|-------|
| CH1 | Joint 2 (Shoulder) | |
| CH2 | Joint 1 (Base) | Inverted |
| CH3 | Joint 3 (Elbow) | |
| CH4 | Joint 4 (Wrist pitch) | |
| CH5 | Joint 5 (Wrist roll) | Inverted |
| CH6 | Joint 6 (Wrist yaw) | |
| CH7 | Gripper | |
| CH14 | Dead-man switch | |

### Configuration

```yaml
velocity_scale: 1.5   # rad/s at full stick
deadzone: 0.01
control_mode: velocity
```

To invert a channel, use negative max_joint value in config.

---

## References

- [z1_ros2 GitHub](https://github.com/idra-lab/z1_ros2)
- [Unitree Z1 Documentation](https://support.unitree.com/home/en/Z1_developer)
- [ROS2 Control Documentation](https://control.ros.org/rolling/index.html)

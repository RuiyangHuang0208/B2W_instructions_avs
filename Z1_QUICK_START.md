# Z1 Arm Quick Start

## Prerequisites

- Z1 arm powered on and connected via ethernet
- Z1 reachable at `192.168.123.110`

## Important: Stop B2 RC Teleop First

The Z1 and B2 RC teleop nodes share the same serial port (`/dev/arduino_sbus`). **You must stop the B2 RC teleop before launching Z1 RC teleop:**

```bash
sudo systemctl stop b2-rc-teleop.service
```

Or stop all B2 services:
```bash
~/Documents/roberto/utils/b2_services.sh stop
```

## Launch Z1 Controller

**Terminal 1:**
```bash
source ~/ros2_ws/install/setup.bash
ros2 launch z1_bringup z1.launch.py starting_controller:=position_controller sim_ignition:=false
```

## Launch RC Teleop

**Terminal 2:**
```bash
source ~/ros2_ws/install/setup.bash
ros2 launch z1_rc_teleop sbus_teleop.launch.py
```

## RC Channel Mapping

| Channel | Joint | Description |
|---------|-------|-------------|
| CH1 | Joint 2 | Shoulder |
| CH2 | Joint 1 | Base rotation (inverted) |
| CH3 | Joint 3 | Elbow |
| CH4 | Joint 4 | Wrist pitch |
| CH5 | Joint 5 | Wrist roll (inverted) |
| CH6 | Joint 6 | Wrist yaw |
| CH7 | Gripper | Open/close |
| CH14 | Enable | Dead-man switch |

**Control Mode:** Velocity (stick = joint speed, center = stop)

**Settings:**
- Velocity scale: 1.5 rad/s
- Deadzone: 0.01
- Gripper range: 0 (open) to -1.57 (closed)

---

## Alternative: Trajectory Controller

For action-based control (MoveIt, scripts):

```bash
source ~/ros2_ws/install/setup.bash
ros2 launch z1_bringup z1.launch.py starting_controller:=joint_trajectory_controller sim_ignition:=false
```

## Manual Joint Commands

Check joint states:
```bash
ros2 topic echo /joint_states --once
```

Move single joint (example - joint1):
```bash
ros2 action send_goal /joint_trajectory_controller/follow_joint_trajectory control_msgs/action/FollowJointTrajectory "{trajectory: {joint_names: [joint1, joint2, joint3, joint4, joint5, joint6], points: [{positions: [0.3, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 2}}, {positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: {sec: 4}}]}}"
```

---

## Troubleshooting

### Motor Overheat Error
```
[ERROR] Motor 3 windings overheat
```
- Power cycle the Z1 arm (unplug/replug power)
- Wait a few minutes for motor to cool
- Avoid holding extended positions for long periods

### Connection Failed
- Verify Z1 is powered on
- Check ping: `ping 192.168.123.110`
- Ensure on correct network interface (eno2)

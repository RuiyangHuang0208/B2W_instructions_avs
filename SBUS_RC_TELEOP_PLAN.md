# SBUS RC Teleop ROS2 Node Implementation Plan

## Overview
Create a ROS2 Python node that reads SBUS RC receiver data from Arduino serial port and publishes `geometry_msgs/Twist` messages to control the B2 robot.

## Channel Mapping (User-specified)

### Locomotion (linear velocities)
- **CH3** (index 2): Forward/backward → `linear.x`
- **CH4** (index 3): Strafe left/right → `linear.y`
- **CH6** (index 5): Up/down → `linear.z`

### Body Orientation (angular velocities)
- **CH1** (index 0): Body pitch → `angular.x`
- **CH2** (index 1): Body roll → `angular.y`
- **CH5** (index 4): Yaw rotation → `angular.z`

### Safety
- **CH14** (index 13): Dead-man switch (>900 = enabled)

## SBUS Data Format
- Serial port: `/dev/arduino_sbus` at 115200 baud
- Output: 16 tab-separated integer values per line
- Value range: 172-1811, center ~992
- Header lines to skip: "SBUS Reader Started", "Waiting for SBUS signal..."

## Implementation

### 1. Create new package: `b2_rc_teleop`
Location: `/opt/mybotshop/src/mybotshop/b2_rc_teleop/`

```
b2_rc_teleop/
├── package.xml
├── setup.py
├── b2_rc_teleop/
│   ├── __init__.py
│   └── sbus_teleop_node.py
├── config/
│   └── sbus_teleop.yaml
└── launch/
    └── sbus_teleop.launch.py
```

### 2. Configuration file: `config/sbus_teleop.yaml`
```yaml
/**:
  ros__parameters:
    # Serial settings
    serial_port: '/dev/arduino_sbus'
    baud_rate: 115200

    # Channel mapping (1-indexed as user specifies)
    channel_linear_x: 3      # Forward/backward
    channel_linear_y: 4      # Strafe
    channel_linear_z: 6      # Up/down
    channel_angular_x: 1     # Body pitch
    channel_angular_y: 2     # Body roll
    channel_angular_z: 5     # Yaw rotation
    channel_enable: 14       # Dead-man switch

    # Enable switch threshold
    enable_threshold: 900    # Values above this = enabled

    # SBUS value range
    sbus_min: 172
    sbus_max: 1811
    sbus_center: 992

    # Velocity scaling (m/s for linear, rad/s for angular)
    max_linear_x: 0.5
    max_linear_y: 0.3
    max_linear_z: 0.2
    max_angular_x: 0.5       # Body pitch rate
    max_angular_y: 0.5       # Body roll rate
    max_angular_z: 0.8       # Yaw rate

    # Deadzone (% of full range)
    deadzone: 0.05

    # Publishing rate (Hz)
    publish_rate: 20.0
```

### 3. Node implementation: `sbus_teleop_node.py`

Key functionality:
1. Open serial port with configurable baud rate
2. Read lines and parse tab-separated values
3. Skip header lines ("SBUS Reader Started", etc.)
4. Check dead-man switch (CH14 > 900)
5. Map SBUS values (172-1811) to velocity range with deadzone
6. Publish Twist message at configured rate
7. Publish zero velocity when disabled or on error

### 4. Launch file: `sbus_teleop.launch.py`
- Set ROS_DOMAIN_ID=10
- Load config from sbus_teleop.yaml
- Namespace: use B2_NS environment variable (default: b2_366)
- Remap output to `rc_teleop/cmd_vel` for twist_mux integration

### 5. Update twist_mux config (optional)
Add RC teleop input to `/opt/mybotshop/src/mybotshop/b2_control/config/twist_mux.yaml`:
```yaml
rc_teleop:
  topic: rc_teleop/cmd_vel
  timeout: 0.5
  priority: 18  # Between joy_teleop (15) and steamdeck (20)
```

## Files to Create/Modify

| File | Action |
|------|--------|
| `/opt/mybotshop/src/mybotshop/b2_rc_teleop/package.xml` | Create |
| `/opt/mybotshop/src/mybotshop/b2_rc_teleop/setup.py` | Create |
| `/opt/mybotshop/src/mybotshop/b2_rc_teleop/b2_rc_teleop/__init__.py` | Create |
| `/opt/mybotshop/src/mybotshop/b2_rc_teleop/b2_rc_teleop/sbus_teleop_node.py` | Create |
| `/opt/mybotshop/src/mybotshop/b2_rc_teleop/config/sbus_teleop.yaml` | Create |
| `/opt/mybotshop/src/mybotshop/b2_rc_teleop/launch/sbus_teleop.launch.py` | Create |
| `/opt/mybotshop/src/mybotshop/b2_control/config/twist_mux.yaml` | Modify (add rc_teleop topic) |

## Verification Steps

1. **Build the package:**
   ```bash
   cd /opt/mybotshop
   source install/setup.bash
   colcon build --packages-select b2_rc_teleop
   ```

2. **Test on robot (SSH to b2zerotier):**
   ```bash
   # Terminal 1: Run the SBUS teleop node
   source /opt/mybotshop/install/setup.bash
   ROS_DOMAIN_ID=10 ros2 launch b2_rc_teleop sbus_teleop.launch.py

   # Terminal 2: Monitor published messages
   ROS_DOMAIN_ID=10 ros2 topic echo /b2_366/rc_teleop/cmd_vel
   ```

3. **Test with robot (hardware webserver must be running):**
   - Activate dead-man switch (CH14 > 900)
   - Move sticks and verify robot responds
   - Release dead-man switch and verify robot stops

## Dependencies
- rclpy
- geometry_msgs
- pyserial (may need: `pip install pyserial`)

## Safety Considerations
- Dead-man switch must be held for robot to move
- Zero velocity published when:
  - Dead-man switch inactive
  - Serial read error
  - Node shutdown
- Configurable max velocities prevent accidental high-speed commands

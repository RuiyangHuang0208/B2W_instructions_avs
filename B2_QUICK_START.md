# B2 Quick Start

## Connect to Robot

```bash
ssh b2zerotier
```
Password: `Unitree0408`

## Start All Services

```bash
~/Documents/roberto/utils/b2_services.sh start
```

## Check Service Status

```bash
~/Documents/roberto/utils/b2_services.sh status
```

## Stop All Services

```bash
~/Documents/roberto/utils/b2_services.sh stop
```

## RC Teleop (SBUS)

Service starts automatically with `b2_services.sh start`.

**Manual launch (if needed):**
```bash
source /opt/ros/humble/setup.bash
source /opt/mybotshop/install/setup.bash
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
ros2 launch b2_rc_teleop sbus_teleop.launch.py
```

**Monitor RC commands:**
```bash
ROS_DOMAIN_ID=10 ros2 topic echo /b2_366/rc_teleop/cmd_vel
```

**Channel mapping:**
- CH3: Forward/backward
- CH4: Strafe (inverted)
- CH5: Yaw (inverted)
- CH14: Dead-man switch (>900 to enable)

## Webserver

- **URL:** http://172.22.206.213:9000
- **User:** admin
- **Pass:** mybotshop

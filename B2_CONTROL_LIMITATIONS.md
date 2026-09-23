# B2 Control Limitations & SDK Analysis

> Documentation of findings regarding simultaneous locomotion and body pose control on the Unitree B2 robot.
> Date: 2026-02-03

## Summary

**The Unitree B2 SDK does not support simultaneous locomotion and body pose control.** The `Move()` and `BodyHeight()`/`Euler()` commands conflict when called together, causing shaky/unstable behavior. This is a fundamental design limitation, not a bug.

---

## Findings

### 1. SDK Command Conflicts

When testing RC teleop with body pose control, we discovered:

| Test | Result |
|------|--------|
| `BodyHeight()` alone at 20Hz | Shaky |
| `BodyHeight()` alone at 2Hz | Smooth |
| `BodyHeight()` with constant value at 20Hz | Smooth |
| `Move()` alone at 20Hz | Smooth |
| `Move()` + `BodyHeight()` at 2Hz each | **Shaky** |
| Set height once, then `Move()` | Height resets to default |

**Conclusion:** `Move()` and `BodyHeight()`/`Euler()` are mutually exclusive commands that reset each other's state.

### 2. Sport Mode Architecture

The B2 has distinct operating modes (from `/sportmodestate`):

```
0. idle, default stand
1. balanceStand      <- Body pose control (Euler, BodyHeight)
2. pose
3. locomotion        <- Movement control (Move)
4. reserve
5. lieDown
6. jointLock
7. damping
8. recoveryStand
...
```

- **Mode 1 (balanceStand):** Uses `Euler()` + `BodyHeight()` + `BalanceStand()`
- **Mode 3 (locomotion):** Uses `Move()`

These modes are separate - the robot switches between them, not combines them.

### 3. Physical Controller Behavior

The Unitree physical controller also requires mode switching:
- Cannot control movement and body pose simultaneously
- Uses buttons to switch between modes
- This is the intended design, not a limitation of the SDK wrapper

### 4. Available SDK Functions (B2 SportClient)

```cpp
// Locomotion
int32_t Move(float vx, float vy, float vyaw);
int32_t StopMove();

// Body Pose (only works in balanceStand mode)
int32_t Euler(float roll, float pitch, float yaw);
int32_t BodyHeight(float height);
int32_t BalanceStand();

// Mode Switching
int32_t SwitchGait(int d);
int32_t SwitchEulerMode(bool flag);  // Declared but not linked in library
int32_t SwitchMoveMode(bool flag);   // Declared but not linked in library

// Other
int32_t StandUp();
int32_t StandDown();
int32_t Damp();
int32_t RecoveryStand();
int32_t SpeedLevel(int level);
int32_t FootRaiseHeight(float height);
```

**Note:** `SwitchEulerMode()` and `SwitchMoveMode()` are declared in the header but cause linker errors - the implementations are not provided in the library.

---

## Alternative: Low-Level Control

### What's Available

The SDK provides low-level motor control via `/lowcmd` topic:

```cpp
// Per-motor control (12 leg motors + optional arm)
motor_cmd[i].mode  // 0x01 for servo mode
motor_cmd[i].q     // Target position (rad)
motor_cmd[i].dq    // Target velocity (rad/s)
motor_cmd[i].kp    // Position gain
motor_cmd[i].kd    // Velocity gain
motor_cmd[i].tau   // Feedforward torque (N.m)
```

### Framework for Custom Controllers

The SDK includes `RobotController` template class with:
- State machine (DAMPING, STAND, CTRL)
- Gamepad input handling
- Low-level command publishing at 500Hz
- Thread management

### What's NOT Provided

To create a custom combined locomotion + body pose mode, you would need to implement:

1. **Balance Controller**
   - Model Predictive Control (MPC) or
   - Quadratic Programming (QP) based Whole-Body Control (WBC)
   - Requires dynamics model of the robot

2. **Gait Generator**
   - Foot trajectory planning
   - Stance/swing phase timing
   - Ground contact detection

3. **Inverse Kinematics**
   - Convert body pose + foot positions to joint angles

4. **State Estimation**
   - Fuse IMU, joint encoders, contact sensors

**Effort Estimate:** This is typically a multi-month project for experienced robotics engineers/researchers.

---

## Recommended Solutions

### Option 1: Mode Switch (Recommended)

Implement a mode switch on the RC controller:
- **Mode A (Locomotion):** CH3, CH4, CH5 → `Move()`
- **Mode B (Body Pose):** CH1, CH2, CH6 → `Euler()`, `BodyHeight()`
- Use a toggle switch (e.g., CH7) to switch between modes

This matches the physical controller behavior and requires minimal code changes.

### Option 2: Sequential Control

Only send body pose commands when not moving:
- If `cmd_vel` is zero, allow body pose adjustments
- If moving, ignore body pose inputs

### Option 3: Low-Level Control (Advanced)

Write a custom controller that:
- Takes over from sport mode using `/lowcmd`
- Implements combined balance + locomotion
- Handles all stability and safety

**Warning:** This disables all built-in safety features and requires extensive testing.

---

## Code Locations

| Component | Path |
|-----------|------|
| B2 SportClient Header | `src/third_party/unitree/17Mar2025_unitree_sdk2/include/unitree/robot/b2/sport/sport_client.hpp` |
| Low-Level Example | `src/third_party/unitree/17Mar2025_unitree_sdk2/example/go2/go2_low_level.cpp` |
| Controller Framework | `src/third_party/unitree/17Mar2025_unitree_sdk2/example/state_machine/robot_controller.hpp` |
| ROS2 Sport Client | `src/third_party/unitree/18Mar2025_unitree_ros2/example/src/src/common/ros2_sport_client.cpp` |
| API IDs | `src/third_party/unitree/18Mar2025_unitree_ros2/example/src/include/common/ros2_sport_client.h` |

---

## References

- Unitree SDK2: https://github.com/unitreerobotics/unitree_sdk2
- Unitree ROS2: https://github.com/unitreerobotics/unitree_ros2
- Sport Services Docs: https://support.unitree.com/home/en/developer/sports_services

---

## Appendix: Test Commands

```bash
# Test body height alone (smooth at 2Hz)
ros2 topic pub -r 2 /b2_366/hardware/body_pose geometry_msgs/msg/Vector3 "{x: 0.0, y: 0.0, z: 0.05}"

# Test movement alone
ros2 topic pub -r 2 /b2_366/hardware/cmd_vel geometry_msgs/msg/Twist "{linear: {x: 0.2, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"

# Test combined (causes shaking)
# Run both commands above simultaneously in separate terminals
```

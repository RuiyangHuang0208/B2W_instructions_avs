#!/usr/bin/env python3
"""
SBUS RC Teleop Node for Z1 Robotic Arm

Reads SBUS RC receiver data from Arduino serial port and publishes
joint position commands to control the Z1 arm.

Channel mapping (must match config/sbus_teleop.yaml, which is what gets loaded):
  CH1 -> Joint 2 (shoulder)
  CH2 -> Joint 1 (base rotation)
  CH3 -> Joint 3 (elbow)
  CH4 -> Joint 4 (wrist pitch)
  CH5 -> Joint 5 (wrist roll)
  CH6 -> Joint 6 (wrist yaw)
  CH7 -> Gripper (open/close)
  CH14 -> Dead-man (enable)
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import JointState
import serial
import threading


class Z1SbusTeleopNode(Node):
    def __init__(self):
        super().__init__('z1_sbus_teleop_node')

        # Declare parameters
        self.declare_parameter('serial_port', '/dev/arduino_sbus')
        self.declare_parameter('baud_rate', 115200)

        # Channel mapping (1-indexed in config, convert to 0-indexed)
        self.declare_parameter('channel_joint1', 2)
        self.declare_parameter('channel_joint2', 1)
        self.declare_parameter('channel_joint3', 3)
        self.declare_parameter('channel_joint4', 4)
        self.declare_parameter('channel_joint5', 5)
        self.declare_parameter('channel_joint6', 6)
        self.declare_parameter('channel_gripper', 7)
        self.declare_parameter('channel_enable', 14)

        self.declare_parameter('enable_threshold', 900)

        # SBUS value range
        self.declare_parameter('sbus_min', 172)
        self.declare_parameter('sbus_max', 1811)
        self.declare_parameter('sbus_center', 992)

        # Joint position limits (radians)
        self.declare_parameter('max_joint1', 2.6)   # Base rotation ~±150 deg
        self.declare_parameter('max_joint2', 2.6)   # Shoulder ~±150 deg
        self.declare_parameter('max_joint3', 2.6)   # Elbow ~±150 deg
        self.declare_parameter('max_joint4', 2.6)   # Wrist pitch ~±150 deg
        self.declare_parameter('max_joint5', 2.6)   # Wrist roll ~±150 deg
        self.declare_parameter('max_joint6', 2.6)   # Wrist yaw ~±150 deg
        self.declare_parameter('max_gripper', 1.0)  # Gripper range

        self.declare_parameter('deadzone', 0.05)
        self.declare_parameter('publish_rate', 20.0)

        # Control mode: 'position' for absolute position, 'velocity' for incremental
        self.declare_parameter('control_mode', 'position')

        # Velocity mode settings (radians per second when stick is full deflection)
        self.declare_parameter('velocity_scale', 0.5)

        # Safe fixed gripper target (rad). z1_ctrl runs its OWN internal position
        # loop for the gripper that ignores the kp/kd we set, so neutralizing gains
        # does not neutralize the gripper. The only way to stop it ratcheting into
        # its hard stop (where it stalls and overheats Motor 7) is to pin the
        # COMMAND to a value safely inside both stops. -0.8 is mid-range
        # (open = 0, closed = -1.57).
        self.declare_parameter('gripper_safe_position', -0.8)

        # Gripper stick control is ABSOLUTE and clamped to a safe band centered on
        # gripper_safe_position with this half-width. With safe=-0.8 and half_range=0.5
        # the gripper command can only ever sit in [-1.3, -0.2], strictly inside both
        # hard stops (open=0, closed=-1.57) so it can never stall/overheat. Set
        # half_range to 0.0 to fully pin the gripper (no stick control).
        self.declare_parameter('gripper_half_range', 0.5)

        # Get parameters
        self.serial_port = self.get_parameter('serial_port').value
        self.baud_rate = self.get_parameter('baud_rate').value

        # Channel indices (convert 1-indexed to 0-indexed)
        self.ch_joints = [
            self.get_parameter('channel_joint1').value - 1,
            self.get_parameter('channel_joint2').value - 1,
            self.get_parameter('channel_joint3').value - 1,
            self.get_parameter('channel_joint4').value - 1,
            self.get_parameter('channel_joint5').value - 1,
            self.get_parameter('channel_joint6').value - 1,
        ]
        self.ch_gripper = self.get_parameter('channel_gripper').value - 1
        self.ch_enable = self.get_parameter('channel_enable').value - 1

        self.enable_threshold = self.get_parameter('enable_threshold').value

        self.sbus_min = self.get_parameter('sbus_min').value
        self.sbus_max = self.get_parameter('sbus_max').value
        self.sbus_center = self.get_parameter('sbus_center').value

        self.max_joints = [
            self.get_parameter('max_joint1').value,
            self.get_parameter('max_joint2').value,
            self.get_parameter('max_joint3').value,
            self.get_parameter('max_joint4').value,
            self.get_parameter('max_joint5').value,
            self.get_parameter('max_joint6').value,
        ]
        self.max_gripper = self.get_parameter('max_gripper').value

        self.deadzone = self.get_parameter('deadzone').value
        self.publish_rate = self.get_parameter('publish_rate').value
        self.control_mode = self.get_parameter('control_mode').value
        self.velocity_scale = self.get_parameter('velocity_scale').value
        self.gripper_safe = self.get_parameter('gripper_safe_position').value
        self.gripper_half_range = self.get_parameter('gripper_half_range').value

        # Publisher for position controller
        self.position_pub = self.create_publisher(
            Float64MultiArray,
            '/position_controller/commands',
            10
        )

        # Subscribe to joint states to get current position (for velocity mode)
        self.current_positions = [0.0] * 7  # 6 joints + gripper
        self.joint_state_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )

        # Serial connection
        self.serial_conn = None
        self.serial_lock = threading.Lock()
        self.latest_channels = [self.sbus_center] * 16
        self.enabled = False
        self.connected = False

        # Connect to serial port
        self.connect_serial()

        # Start serial reading thread
        self.running = True
        self.serial_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
        self.serial_thread.start()

        # Timer for publishing
        self.timer = self.create_timer(1.0 / self.publish_rate, self.publish_commands)

        self.get_logger().info(f'Z1 SBUS Teleop Node started')
        self.get_logger().info(f'Serial port: {self.serial_port} @ {self.baud_rate} baud')
        self.get_logger().info(f'Control mode: {self.control_mode}')
        self.get_logger().info(f'Dead-man switch: CH{self.ch_enable + 1} > {self.enable_threshold}')

    def connect_serial(self):
        """Connect to the serial port with DTR reset to ensure Arduino is ready."""
        try:
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=0.1,
                dsrdtr=False
            )
            # Reset Arduino via DTR toggle
            self.serial_conn.dtr = False
            import time
            time.sleep(0.1)
            self.serial_conn.dtr = True
            time.sleep(0.5)
            self.serial_conn.reset_input_buffer()

            self.connected = True
            self.get_logger().info(f'Connected to {self.serial_port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to connect to {self.serial_port}: {e}')
            self.connected = False

    def serial_read_loop(self):
        """Background thread to read serial data."""
        while self.running:
            if not self.connected:
                self.connect_serial()
                if not self.connected:
                    import time
                    time.sleep(1.0)
                    continue

            try:
                line = self.serial_conn.readline().decode('utf-8').strip()
                if not line:
                    continue

                if line.startswith('SBUS') or line.startswith('Waiting'):
                    self.get_logger().info(f'Arduino: {line}')
                    continue

                values = line.split('\t')
                if len(values) >= 16:
                    channels = [int(v) for v in values[:16]]
                    with self.serial_lock:
                        self.latest_channels = channels

            except (serial.SerialException, OSError) as e:
                self.get_logger().warn(f'Serial error: {e}')
                self.connected = False
                if self.serial_conn:
                    try:
                        self.serial_conn.close()
                    except:
                        pass
            except (ValueError, UnicodeDecodeError):
                pass

    def joint_state_callback(self, msg: JointState):
        """Update current joint positions from joint states."""
        # Map joint names to indices
        joint_map = {
            'joint1': 0, 'joint2': 1, 'joint3': 2,
            'joint4': 3, 'joint5': 4, 'joint6': 5,
            'jointGripper': 6
        }
        for i, name in enumerate(msg.name):
            if name in joint_map:
                idx = joint_map[name]
                if i < len(msg.position):
                    self.current_positions[idx] = msg.position[i]

    def map_sbus_to_value(self, sbus_value: int, max_value: float) -> float:
        """
        Map SBUS value (172-1811, center 992) to value (-max to +max).
        Applies deadzone around center.
        """
        half_range = (self.sbus_max - self.sbus_min) / 2.0
        normalized = (sbus_value - self.sbus_center) / half_range
        normalized = max(-1.0, min(1.0, normalized))

        if abs(normalized) < self.deadzone:
            return 0.0

        if normalized > 0:
            normalized = (normalized - self.deadzone) / (1.0 - self.deadzone)
        else:
            normalized = (normalized + self.deadzone) / (1.0 - self.deadzone)

        return normalized * max_value

    def compute_gripper_cmd(self, channels):
        """Absolute, clamped gripper command (see gripper_half_range note in __init__).

        Maps the gripper stick to an absolute position in a safe band centered on
        gripper_safe, so the command can never reach a hard stop (no stall/overheat).
        No velocity integration -> passive-revert hiccups cannot ratchet it open.
        """
        offset = self.map_sbus_to_value(channels[self.ch_gripper], self.gripper_half_range)
        lo = self.gripper_safe - self.gripper_half_range
        hi = self.gripper_safe + self.gripper_half_range
        return max(lo, min(hi, self.gripper_safe + offset))

    def publish_commands(self):
        """Publish joint position commands based on current SBUS values."""
        with self.serial_lock:
            channels = self.latest_channels.copy()

        # Check dead-man switch
        if self.ch_enable < len(channels):
            self.enabled = channels[self.ch_enable] > self.enable_threshold
        else:
            self.enabled = False

        if not self.enabled or not self.connected:
            return

        # Calculate joint positions
        positions = []

        if self.control_mode == 'position':
            # Direct position control: stick position = joint position
            for i in range(6):
                # Use sign of max_joints for inversion, abs for limits
                limit = abs(self.max_joints[i])
                pos = self.map_sbus_to_value(channels[self.ch_joints[i]], self.max_joints[i])
                pos = max(-limit, min(limit, pos))
                positions.append(pos)
            # Gripper: absolute, clamped stick control (cannot reach a hard stop).
            positions.append(self.compute_gripper_cmd(channels))
        else:
            # Velocity mode: stick position = joint velocity
            dt = 1.0 / self.publish_rate
            for i in range(6):
                # Use sign of max_joints for inversion, abs for limits
                sign = 1.0 if self.max_joints[i] >= 0 else -1.0
                limit = abs(self.max_joints[i])
                velocity = self.map_sbus_to_value(channels[self.ch_joints[i]], self.velocity_scale) * sign
                new_pos = self.current_positions[i] + velocity * dt
                # Clamp to joint limits
                new_pos = max(-limit, min(limit, new_pos))
                positions.append(new_pos)
                self.current_positions[i] = new_pos
            # Gripper: absolute, clamped stick control (cannot reach a hard stop).
            # NOT velocity-integrated — integrating from the measured position let the
            # gripper ratchet to its open stop on every passive-revert hiccup, where it
            # stalled and overheated.
            g = self.compute_gripper_cmd(channels)
            positions.append(g)
            self.current_positions[6] = g

        # Publish position command
        msg = Float64MultiArray()
        msg.data = positions
        self.position_pub.publish(msg)

    def destroy_node(self):
        """Clean up on shutdown."""
        self.running = False
        if self.serial_conn:
            try:
                self.serial_conn.close()
            except:
                pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = Z1SbusTeleopNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

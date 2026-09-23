#!/usr/bin/env python3
"""
SBUS RC Teleop Node for B2 Robot

Reads SBUS RC receiver data from Arduino serial port and publishes
geometry_msgs/Twist messages to control the robot.
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist, Vector3
import serial
import threading


class SbusTeleopNode(Node):
    def __init__(self):
        super().__init__('sbus_teleop_node')

        # Declare parameters
        self.declare_parameter('serial_port', '/dev/arduino_sbus')
        self.declare_parameter('baud_rate', 115200)

        # Channel mapping (1-indexed in config, convert to 0-indexed)
        self.declare_parameter('channel_linear_x', 3)
        self.declare_parameter('channel_linear_y', 4)
        self.declare_parameter('channel_linear_z', 6)
        self.declare_parameter('channel_angular_x', 1)
        self.declare_parameter('channel_angular_y', 2)
        self.declare_parameter('channel_angular_z', 5)
        self.declare_parameter('channel_enable', 14)

        self.declare_parameter('enable_threshold', 900)

        # SBUS value range
        self.declare_parameter('sbus_min', 172)
        self.declare_parameter('sbus_max', 1811)
        self.declare_parameter('sbus_center', 992)

        # Velocity limits
        self.declare_parameter('max_linear_x', 0.5)
        self.declare_parameter('max_linear_y', 0.3)
        self.declare_parameter('max_linear_z', 0.2)
        self.declare_parameter('max_angular_x', 0.5)
        self.declare_parameter('max_angular_y', 0.5)
        self.declare_parameter('max_angular_z', 0.8)

        # Body pose limits (for body_pose topic)
        self.declare_parameter('max_body_roll', 0.4)    # radians (~23 degrees)
        self.declare_parameter('max_body_pitch', 0.4)   # radians (~23 degrees)
        self.declare_parameter('max_body_height', 0.1)  # meters

        self.declare_parameter('deadzone', 0.05)
        self.declare_parameter('publish_rate', 20.0)

        # Get parameters
        self.serial_port = self.get_parameter('serial_port').value
        self.baud_rate = self.get_parameter('baud_rate').value

        # Channel indices (convert 1-indexed to 0-indexed)
        self.ch_linear_x = self.get_parameter('channel_linear_x').value - 1
        self.ch_linear_y = self.get_parameter('channel_linear_y').value - 1
        self.ch_linear_z = self.get_parameter('channel_linear_z').value - 1
        self.ch_angular_x = self.get_parameter('channel_angular_x').value - 1
        self.ch_angular_y = self.get_parameter('channel_angular_y').value - 1
        self.ch_angular_z = self.get_parameter('channel_angular_z').value - 1
        self.ch_enable = self.get_parameter('channel_enable').value - 1

        self.enable_threshold = self.get_parameter('enable_threshold').value

        self.sbus_min = self.get_parameter('sbus_min').value
        self.sbus_max = self.get_parameter('sbus_max').value
        self.sbus_center = self.get_parameter('sbus_center').value

        self.max_linear_x = self.get_parameter('max_linear_x').value
        self.max_linear_y = self.get_parameter('max_linear_y').value
        self.max_linear_z = self.get_parameter('max_linear_z').value
        self.max_angular_x = self.get_parameter('max_angular_x').value
        self.max_angular_y = self.get_parameter('max_angular_y').value
        self.max_angular_z = self.get_parameter('max_angular_z').value

        self.max_body_roll = self.get_parameter('max_body_roll').value
        self.max_body_pitch = self.get_parameter('max_body_pitch').value
        self.max_body_height = self.get_parameter('max_body_height').value

        self.deadzone = self.get_parameter('deadzone').value
        publish_rate = self.get_parameter('publish_rate').value

        # Publishers
        self.twist_pub = self.create_publisher(Twist, 'cmd_vel', 10)
        self.body_pose_pub = self.create_publisher(Vector3, 'body_pose', 10)

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
        self.timer = self.create_timer(1.0 / publish_rate, self.publish_commands)

        self.get_logger().info(f'SBUS Teleop Node started')
        self.get_logger().info(f'Serial port: {self.serial_port} @ {self.baud_rate} baud')
        self.get_logger().info(f'Dead-man switch: CH{self.ch_enable + 1} > {self.enable_threshold}')

    def connect_serial(self):
        """Connect to the serial port with DTR reset to ensure Arduino is ready."""
        try:
            self.serial_conn = serial.Serial(
                port=self.serial_port,
                baudrate=self.baud_rate,
                timeout=0.1,
                dsrdtr=False  # Allow manual DTR control
            )
            # Reset Arduino via DTR toggle
            self.serial_conn.dtr = False
            import time
            time.sleep(0.1)
            self.serial_conn.dtr = True
            time.sleep(0.5)  # Wait for Arduino to boot
            self.serial_conn.reset_input_buffer()  # Clear any startup garbage

            self.connected = True
            self.get_logger().info(f'Connected to {self.serial_port} (Arduino reset via DTR)')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to connect to {self.serial_port}: {e}')
            self.connected = False

    def serial_read_loop(self):
        """Background thread to read serial data."""
        while self.running:
            if not self.connected:
                # Try to reconnect
                self.connect_serial()
                if not self.connected:
                    import time
                    time.sleep(1.0)
                    continue

            try:
                line = self.serial_conn.readline().decode('utf-8').strip()
                if not line:
                    continue

                # Skip header lines from Arduino
                if line.startswith('SBUS') or line.startswith('Waiting'):
                    self.get_logger().info(f'Arduino: {line}')
                    continue

                # Parse tab-separated values
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
            except (ValueError, UnicodeDecodeError) as e:
                # Invalid data, skip
                pass

    def map_sbus_to_velocity(self, sbus_value: int, max_velocity: float) -> float:
        """
        Map SBUS value (172-1811, center 992) to velocity (-max to +max).
        Applies deadzone around center.
        """
        # Calculate half range
        half_range = (self.sbus_max - self.sbus_min) / 2.0

        # Normalize to -1.0 to 1.0
        normalized = (sbus_value - self.sbus_center) / half_range

        # Clamp to valid range
        normalized = max(-1.0, min(1.0, normalized))

        # Apply deadzone
        if abs(normalized) < self.deadzone:
            return 0.0

        # Scale deadzone out
        if normalized > 0:
            normalized = (normalized - self.deadzone) / (1.0 - self.deadzone)
        else:
            normalized = (normalized + self.deadzone) / (1.0 - self.deadzone)

        return normalized * max_velocity

    def publish_commands(self):
        """Publish Twist and body pose messages based on current SBUS values."""
        twist = Twist()
        body_pose = Vector3()

        with self.serial_lock:
            channels = self.latest_channels.copy()

        # Check dead-man switch
        if self.ch_enable < len(channels):
            self.enabled = channels[self.ch_enable] > self.enable_threshold
        else:
            self.enabled = False

        if not self.enabled or not self.connected:
            # Publish zero velocity and neutral body pose
            self.twist_pub.publish(twist)
            self.body_pose_pub.publish(body_pose)
            return

        # Map channels to velocities (for cmd_vel)
        twist.linear.x = self.map_sbus_to_velocity(channels[self.ch_linear_x], self.max_linear_x)
        twist.linear.y = self.map_sbus_to_velocity(channels[self.ch_linear_y], self.max_linear_y)
        twist.angular.z = self.map_sbus_to_velocity(channels[self.ch_angular_z], self.max_angular_z)

        # Map channels to body pose (for body_pose topic)
        # x = roll (CH2), y = pitch (CH1), z = height (CH6)
        body_pose.x = self.map_sbus_to_velocity(channels[self.ch_angular_y], self.max_body_roll)   # Roll from CH2
        body_pose.y = self.map_sbus_to_velocity(channels[self.ch_angular_x], self.max_body_pitch)  # Pitch from CH1
        body_pose.z = self.map_sbus_to_velocity(channels[self.ch_linear_z], self.max_body_height)  # Height from CH6

        self.twist_pub.publish(twist)
        self.body_pose_pub.publish(body_pose)

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
    node = SbusTeleopNode()

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

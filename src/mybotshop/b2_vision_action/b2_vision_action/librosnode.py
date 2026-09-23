#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Software License Agreement (BSD)
#
# @author    Salman Omar Sohail <support@mybotshop.de>
# @copyright (c) 2025, MYBOTSHOP GmbH, Inc., All rights reserved.

import cv2
import tf2_ros
import math
import numpy as np
import time as pytime_custom

from ultralytics import YOLO
from cv_bridge import CvBridge

from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy

from b2_srvs.srv import B2Modes
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import TransformStamped, Twist

from tf2_ros import TransformBroadcaster
from ament_index_python.packages import get_package_share_directory


class Ros2Vision(Node):
    def __init__(self):
        super().__init__('b2_vision_action')
        self.get_logger().info(self.colorize("Starting ROS2 Computer Vision Node", "orange"))

        # Parameters Declaration
        self.declare_parameters(namespace='', parameters=[
            ('yolo_model', 'none.pt'),
            ('sub_image', '/image_raw'),
            ('depth_image', '/depth/image_raw'),
            ('pub_image', 'yolo/image_raw'),
            ('base_frame', 'base_link'),
            ('camera_info_topic', '/camera_info'),
            ('camera_frame', 'camera_frame'),
            ('detection_list', ['person'])
        ])

        # Parameters Initialization
        self.param_yolo_model = self.get_parameter('yolo_model').value
        self.param_sub_image = self.get_parameter('sub_image').value
        self.param_depth_image = self.get_parameter('depth_image').value
        self.param_pub_image = self.get_parameter('pub_image').value
        self.base_frame = self.get_parameter('base_frame').value
        self.param_camera_frame = self.get_parameter('camera_frame').value
        self.param_detection_list = self.get_parameter(
            'detection_list').value
        self.param_camera_info_topic = self.get_parameter(
            'camera_info_topic').value

        # Print Parameters
        self.get_logger().info(
            f'{self.colorize(f"yolo_model: {self.param_yolo_model}","blue")}')
        self.get_logger().info(
            f'{self.colorize(f"sub_image: {self.param_sub_image}","blue")}')
        self.get_logger().info(
            f'{self.colorize(f"depth_image: {self.param_depth_image}","blue")}')
        self.get_logger().info(
            f'{self.colorize(f"pub_image: {self.param_pub_image}","blue")}')
        self.get_logger().info(
            f'{self.colorize(f"base_frame: {self.base_frame}","blue")}')
        self.get_logger().info(
            f'{self.colorize(f"detection_list: {self.param_detection_list}","blue")}')
        self.get_logger().info(
            f'{self.colorize(f"camera_frame: {self.param_camera_frame}","blue")}')
        self.get_logger().info(
            f'{self.colorize(f"camera_info_topic: {self.param_camera_info_topic}","blue")}')

        # Parameters
        self.smoke_region = None
        self.center_threshold_x = 20
        self.center_threshold_y = 20
        self.b2_vacuum_left = False
        self.b2_vacuum_right = False
        self.vacuum_active = False

        self.param_goal_region_offset_x_left = 200
        self.param_goal_region_offset_x_right = 250
        self.param_goal_region_offset_y = 10
        self.param_vertical_shift = 40

        self.last_detection_time = self.get_clock().now()

        self.systematic_error_x = 0.0
        self.systematic_error_y = 0.0
        self.systematic_error_z = -0.05
        self.latest_depth_image = None
        self.latest_smoke_position = None

        # Initialize OpenCV & TF2
        self.bridge = CvBridge()
        self.tf_broadcaster = TransformBroadcaster(self)
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # Camera
        self.camera_intrinsics = {
            'fx': 500.0,  # focal length x
            'fy': 500.0,  # focal length y
            'cx': 320.0,  # optical center x
            'cy': 240.0,  # optical center y
        }
        self.camera_info_received = False
        self.epsilon = 1e-6

        # Initialize YOLO model
        self.initalize_yolo()

        # Subcribers
        self.sub_image = self.create_subscription(
            Image,
            self.param_sub_image,
            self.image_callback,
            10
        )
        self.sub_camera_info = self.create_subscription(
            CameraInfo,
            self.param_camera_info_topic,
            self.camera_info_callback,
            10
        )

        self.dep_image = self.create_subscription(
            Image,
            self.param_depth_image,
            self.depth_image_callback,
            10
        )

        # Publisher
        qos_profile = QoSProfile(
            depth=10,
            reliability=QoSReliabilityPolicy.RELIABLE,  # RELIABLE is better for images
            durability=QoSDurabilityPolicy.VOLATILE
        )
        self.image_publisher = self.create_publisher(
            Image,
            self.param_pub_image,
            qos_profile
        )

        self.velocity_publisher = self.create_publisher(
            Twist, 'autonomous_mid_priority/cmd_vel', qos_profile)

        self.create_timer(0.1, self.motion_control_callback)

        # Service Clients
        self.b2_robot_service_client = self.create_client(
            B2Modes, 'hardware/modes')
        self.b2_vacuum_service_client = self.create_client(
            B2Modes, 'rig/control')

        self.get_logger().info(self.colorize(
            "ROS2 Computer Vision Node initialized successfully.", "green"))

    def motion_control_callback(self):
        try:

            # Timeout check
            time_since_last_detection = self.get_clock().now() - self.last_detection_time
            if time_since_last_detection.nanoseconds > 3 * 1e9:
                self.get_logger().warn(self.colorize(
                    "No detection in the last 3 seconds. Stopping motion control.", "orange"), throttle_duration_sec=1.0)
                # Deactivate vacuum when reaching target
                if self.vacuum_active:
                    self.vacuum_sequence("close")
                    self.vacuum_active = False
                return

            if self.latest_smoke_position is None or not hasattr(self, 'latest_smoke_center_x'):
                self.get_logger().warn(self.colorize(
                    "No valid smoke position detected yet. Waiting for detection.", "yellow"), throttle_duration_sec=1.0)
                # Deactivate vacuum when reaching target
                if self.vacuum_active:
                    self.vacuum_sequence("close")
                    self.vacuum_active = False
                return

            x, y, z = self.latest_smoke_position
            center_x = self.latest_smoke_center_x
            fx = self.camera_intrinsics['fx']
            fy = self.camera_intrinsics['fy']
            cx = self.camera_intrinsics['cx']
            cy = self.camera_intrinsics['cy']

            center_y = ((y * fy) / z) + cy if z != 0 else cy

            image_width = cx * 2
            image_height = cy * 2

            mid_x = image_width / 2
            mid_y = image_height / 2

            adjusted_mid_y = mid_y - self.param_vertical_shift

            # === Define region centers ===
            left_region_center_x = mid_x - self.param_goal_region_offset_x_left
            right_region_center_x = mid_x + self.param_goal_region_offset_x_right

            # === Decide which region it's in ===
            if center_x < mid_x:
                # Camera Left Region
                target_x = left_region_center_x
                region = "LEFT"
                # Check if we need to switch valves
                if self.b2_vacuum_left:
                    # Switching from left to right valve
                    self.b2_vacuum_left = False
                    self.b2_vacuum_right = True
                    if self.vacuum_active:
                        self.vacuum_sequence("open")  # Reconfigure valves
                else:
                    self.b2_vacuum_right = True
            else:
                # Camera Right Region
                target_x = right_region_center_x
                region = "RIGHT"
                # Check if we need to switch valves
                if self.b2_vacuum_right:
                    # Switching from right to left valve
                    self.b2_vacuum_right = False
                    self.b2_vacuum_left = True
                    if self.vacuum_active:
                        self.vacuum_sequence("open")  # Reconfigure valves
                else:
                    self.b2_vacuum_left = True

            # === Compute offset to region center ===
            offset_x = center_x - target_x
            offset_y = center_y - adjusted_mid_y

            linear_y = 0.0  # side movement
            linear_x = 0.0  # vertical/front-back if needed

            if offset_x < -self.center_threshold_x:
                self.get_logger().info(self.colorize(
                    f"Object is LEFT of {region} region center. Moving RIGHT.", "blue"), throttle_duration_sec=1.0)
                linear_y = -0.1
            elif offset_x > self.center_threshold_x:
                self.get_logger().info(self.colorize(
                    f"Object is RIGHT of {region} region center. Moving LEFT.", "blue"), throttle_duration_sec=1.0)
                linear_y = 0.1

            if offset_y < -self.center_threshold_y:
                self.get_logger().info(self.colorize(
                    "Object is ABOVE center. Moving DOWN.", "blue"), throttle_duration_sec=1.0)
                linear_x = -0.1
            elif offset_y > self.center_threshold_y:
                self.get_logger().info(self.colorize(
                    "Object is BELOW center. Moving UP.", "blue"), throttle_duration_sec=1.0)
                linear_x = 0.1

            if abs(offset_x) <= self.center_threshold_x and abs(offset_y) <= self.center_threshold_y:
                self.get_logger().info(self.colorize(
                    f"Object is centered in {region} region. Stopping motion control.", "green"))
                # Deactivate vacuum when reaching target
                if self.vacuum_active:
                    self.vacuum_sequence("close")
                    self.vacuum_active = False
            else:
                # Activate vacuum when moving (if not already active)
                if not self.vacuum_active:
                    if self.b2_vacuum_left or self.b2_vacuum_right:
                        self.vacuum_sequence("open")
                        self.vacuum_active = True
                self.pub_velocity(linear_x=linear_x, linear_y=linear_y)

        except Exception as e:
            self.get_logger().error(f"Error in motion control: {e}")

    def pub_velocity(self, linear_x=0.0, linear_y=0.0, angular_z=0.0):
        """
        Publishes a velocity command to the robot.
        """
        try:

            twist_msg = Twist()
            twist_msg.linear.x = float(linear_x)
            twist_msg.linear.y = float(linear_y)
            twist_msg.angular.z = float(angular_z)

            # Normalize and limit speed
            norm = math.hypot(twist_msg.linear.x, twist_msg.linear.y)
            max_speed = 0.03
            if norm > max_speed:
                scale = max_speed / norm
                twist_msg.linear.x *= scale
                twist_msg.linear.y *= scale

            self.velocity_publisher.publish(twist_msg)

        except Exception as e:
            self.get_logger().error(f"Error publishing velocity: {e}")

    def vacuum_sequence(self, action):
        if action == "open":
            if self.b2_vacuum_right:
                self.get_logger().info(self.colorize(
                    "Activating right vacuum and closing left valve.", "purple"))
                self.b2_vacuum_service_client.call_async(
                    B2Modes.Request(request_data='right_valve_open'))
                self.b2_vacuum_service_client.call_async(
                    B2Modes.Request(request_data='left_valve_close'))
                self.b2_vacuum_service_client.call_async(
                    B2Modes.Request(request_data='vacuum_on'))

            elif self.b2_vacuum_left:
                self.get_logger().info(self.colorize(
                    "Activating left vacuum and closing right valve.", "purple"))
                self.b2_vacuum_service_client.call_async(
                    B2Modes.Request(request_data='left_valve_open'))
                self.b2_vacuum_service_client.call_async(
                    B2Modes.Request(request_data='right_valve_close'))
                self.b2_vacuum_service_client.call_async(
                    B2Modes.Request(request_data='vacuum_on'))

        elif action == "close":
            self.get_logger().info(self.colorize(
                "Deactivating vacuum. Closing Valves", "purple"))
            self.b2_vacuum_left = False
            self.b2_vacuum_right = False
            self.b2_vacuum_service_client.call_async(
                B2Modes.Request(request_data='left_valve_close'))
            self.b2_vacuum_service_client.call_async(
                B2Modes.Request(request_data='right_valve_close'))
            self.b2_vacuum_service_client.call_async(
                B2Modes.Request(request_data='vacuum_off'))

    def depth_image_callback(self, msg):
        try:
            depth_image = self.bridge.imgmsg_to_cv2(
                msg, desired_encoding='passthrough')
            self.latest_depth_image = depth_image
        except Exception as e:
            self.get_logger().error(f"Failed to convert depth image: {e}")

    def get_depth_at_pixel(self, x, y):
        try:
            if self.latest_depth_image is None:
                self.get_logger().warn("No depth image received yet.")
                return None
            # Get average z as sometimes the depth parts are missing

            height, width = self.latest_depth_image.shape
            x = int(round(x))
            y = int(round(y))

            if 0 <= x < width and 0 <= y < height:
                depth = self.latest_depth_image[y, x]
                # Handle NaN or invalid data
                if np.isnan(depth) or depth <= 0.0:
                    self.get_logger().warn(
                        f"Invalid depth value at ({x}, {y}): {depth}")
                    return None
                return float(depth)*0.001*-1.0
            else:
                self.get_logger().warn(
                    f"Pixel coordinates ({x}, {y}) out of bounds.")
                return None
        except Exception as e:
            self.get_logger().error(
                f"Error getting depth at pixel ({x}, {y}): {e}")
            return None

    def calculate_3d_position(self, center_x, center_y, depth):
        fx = self.camera_intrinsics['fx']
        fy = self.camera_intrinsics['fy']
        cx = self.camera_intrinsics['cx']
        cy = self.camera_intrinsics['cy']

        z = depth
        x = (center_x - cx) * z / fx
        y = (center_y - cy) * z / fy
        return x, y, z

    def initalize_yolo(self):

        self.get_logger().info(self.colorize("Initializing YOLO model", "yellow"))
        b2_cv_dir = get_package_share_directory('b2_vision_action')
        model_path = b2_cv_dir+f"/config/{self.param_yolo_model}"

        try:
            self.yolo_model = YOLO(model_path)
            self.yolo_model.conf = 0.75  # Confidence threshold
            self.yolo_model.iou = 0.5  # Overlapping Objects threshold
            self.yolo_model.agnostic = False  # Multiple Classification of the same object
            self.yolo_model.multi_label = False  # Multiple labels
            self.yolo_model.max_det = 5  # maximum number of detections per image
        except Exception as e:
            self.get_logger().fatal(
                f"Failed to load YOLO model from {model_path}. Please check the model path and file. Error: {e}")
            self.destroy_node()
            return

    def camera_info_callback(self, msg):
        """
        Callback function for the camera info subscriber.
        Updates camera intrinsics.
        """
        if len(msg.k) >= 9:
            fx = float(msg.k[0])
            fy = float(msg.k[4])
            cx = float(msg.k[2])
            cy = float(msg.k[5])

            if abs(fx) > self.epsilon and abs(fy) > self.epsilon:
                self.camera_intrinsics['fx'] = fx
                self.camera_intrinsics['fy'] = fy
                self.camera_intrinsics['cx'] = cx
                self.camera_intrinsics['cy'] = cy
                self.camera_info_received = True
                # self.get_logger().info(self.colorize(
                #     f"Received and updated CameraInfo: fx={self.camera_intrinsics['fx']:.2f}, fy={self.camera_intrinsics['fy']:.2f}, cx={self.camera_intrinsics['cx']:.2f}, cy={self.camera_intrinsics['cy']:.2f}", "green"))
            else:
                self.get_logger().warning(self.colorize(
                    "Received CameraInfo with zero or near-zero focal lengths. Cannot use for 3D estimation.", "red"), once=True)
                self.camera_info_received = False
        else:
            self.get_logger().warning(self.colorize(
                "Received CameraInfo with insufficient K matrix data.", "red"), once=True)
            self.camera_info_received = False

    def image_callback(self, msg):
        """
        Callback function for the image subscriber.
        Converts the ROS2 image message to OpenCV format and processes it.
        """
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            results = self.yolo_model([cv_image], verbose=False)
            annotated_frame = cv_image
            self.smoke_region = None
            self.image_width = annotated_frame.shape[1]
            self.image_height = annotated_frame.shape[0]
            if results and len(results) > 0:
                result = results[0]
                # Process each detected object
                if len(result.boxes) > 0:
                    # for i, box in enumerate(result.boxes): # Multi object detection
                    box = result.boxes[0]
                    i = 0
                    # Get the box coordinates
                    # xyxy is [x1, y1, x2, y2] in pixel coordinates
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    # Calculate center of the bounding box
                    center_x = (x1 + x2) / 2.0
                    center_y = (y1 + y2) / 2.0

                    # Get confidence and class
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    cls_name = result.names.get(cls, f"unknown_{cls}")

                    if conf > self.yolo_model.conf:
                        if cls_name in self.param_detection_list:
                            depth_value = self.get_depth_at_pixel(
                                center_x, center_y)
                            if depth_value is not None:
                                x, y, z = self.calculate_3d_position(
                                    center_x, center_y, depth_value)
                                self.latest_smoke_position = (x, y, z)
                                self.last_detection_time = self.get_clock().now()

                                # Draw goal region box centered in the image
                                # Green for goals
                                goal_box_color = (0, 255, 0)
                                goal_box_thickness = 2

                                mid_x = self.image_width // 2
                                mid_y = self.image_height // 2

                                offset_y = self.param_goal_region_offset_y

                                # Adjust vertical center up
                                adjusted_mid_y = mid_y - self.param_vertical_shift

                                # Left goal region box
                                left_top_left = (
                                    mid_x - self.param_goal_region_offset_x_left - self.center_threshold_x, adjusted_mid_y - offset_y)
                                left_bottom_right = (
                                    mid_x - self.param_goal_region_offset_x_left + self.center_threshold_x, adjusted_mid_y + offset_y)

                                # Right goal region box
                                right_top_left = (
                                    mid_x + self.param_goal_region_offset_x_right - self.center_threshold_x, adjusted_mid_y - offset_y)
                                right_bottom_right = (
                                    mid_x + self.param_goal_region_offset_x_right + self.center_threshold_x, adjusted_mid_y + offset_y)

                                cv2.rectangle(
                                    annotated_frame, left_top_left, left_bottom_right, goal_box_color, goal_box_thickness)
                                cv2.rectangle(
                                    annotated_frame, right_top_left, right_bottom_right, goal_box_color, goal_box_thickness)

                                # Draw circle on the detected object
                                cv2.circle(annotated_frame, (int(center_x), int(
                                    center_y)), 5, (255, 0, 0), -1)
                                cv2.putText(annotated_frame, "Detected", (int(center_x) + 10, int(center_y) - 10),
                                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

                                self.latest_smoke_center_x = center_x
                                self.latest_smoke_center_y = center_y

                                self.publish_object_tf(center_x, center_y, depth_value,
                                                        f"detected_{cls_name}_{i}", msg.header.stamp)

            height, width, _ = annotated_frame.shape
            mid_x = width // 2

            # Create tinted overlays
            left_region = annotated_frame[:, :mid_x].copy()
            right_region = annotated_frame[:, mid_x:].copy()

            left_color = np.full_like(
                left_region, (0, 255, 255))  # Yellow tint (BGR)
            right_color = np.full_like(
                right_region, (0, 165, 255))  # Orange tint (BGR)

            left_region = cv2.addWeighted(left_region, 0.7, left_color, 0.3, 0)
            right_region = cv2.addWeighted(
                right_region, 0.7, right_color, 0.3, 0)

            # Put tinted regions back
            annotated_frame[:, :mid_x] = left_region
            annotated_frame[:, mid_x:] = right_region

            # Publish the annotated image
            self.publish_image(annotated_frame, "bgr8", msg.header.stamp)

        except Exception as e:
            self.get_logger().error(f"Error in image callback: {e}")

    def publish_image(self, img_array, encoding, timestamp):
        """
        Helper function to convert and publish an OpenCV image (NumPy array).
        """
        try:
            ros2_image_msg = self.bridge.cv2_to_imgmsg(
                img_array, encoding=encoding)
            ros2_image_msg.header.stamp = self.get_clock().now().to_msg()
            ros2_image_msg.header.frame_id = self.param_camera_frame
            self.image_publisher.publish(ros2_image_msg)
        except Exception as e:
            self.get_logger().error(
                f"Error converting or publishing image: {e}")

    def publish_object_tf(self, center_x, center_y, object_distance, object_name, timestamp):
        """
        Publishes a TF transform for an object detected in the image.
        Uses camera intrinsics (received or default) and assumed object distance for 3D estimation.
        Assumes camera frame has +X right, +Y down, +Z forward.
        """
        # Get camera intrinsics - prefer received if available and valid, otherwise use defaults
        fx = self.camera_intrinsics['fx']
        fy = self.camera_intrinsics['fy']
        cx = self.camera_intrinsics['cx']
        cy = self.camera_intrinsics['cy']

        try:

            object_z_cam = object_distance
            object_x_cam = (center_x - cx) * object_z_cam / fx
            object_y_cam = (center_y - cy) * object_z_cam / fy

            # Create transform message
            t = TransformStamped()
            t.header.stamp = timestamp
            t.header.frame_id = self.param_camera_frame
            t.child_frame_id = object_name

            # Set translation in the camera frame (+X right, +Y down, +Z forward)
            # Note: The ROS convention for a camera frame is often +X right, +Y down, +Z forward.
            t.transform.translation.x = -1*object_y_cam + \
                self.systematic_error_x  # Right/Left in camera image plane
            t.transform.translation.y = -1*object_x_cam + \
                self.systematic_error_y  # Down/Up in camera image plane
            # Forward/Backward in camera image plane
            t.transform.translation.z = object_z_cam + self.systematic_error_z

            # Set rotation (identity - no rotation of the object frame relative to the camera frame)
            t.transform.rotation.x = 0.0
            t.transform.rotation.y = 0.0
            t.transform.rotation.z = 0.0
            t.transform.rotation.w = 1.0

            # Broadcast transform
            self.tf_broadcaster.sendTransform(t)
        except Exception as e:
            self.get_logger().error(
                f"Error in publish_object_tf for {object_name}: {e}")

    def colorize(self, text, color):
        color_codes = {
            'green': '\033[92m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'yellow': '\033[93m',
            'orange': '\033[38;5;208m',
            'blue': '\033[94m',
            'red': '\033[91m'
        }
        return color_codes[color] + text + '\033[0m'

    def destroy_node(self):
        self.get_logger().info(self.colorize("Shutting down ROS2 Computer Vision Node", "red"))
        self.vacuum_sequence("close")
        self.vacuum_active = False
        super().destroy_node()

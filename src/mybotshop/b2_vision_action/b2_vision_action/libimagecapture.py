#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import os
import threading
import sys
import termios
import tty

class ImageSaver(Node):
    def __init__(self):
        super().__init__('image_saver')
        self.subscription = self.create_subscription(
            Image,
            '/b2_366/b2_366/color/image_rect_raw', 
            self.listener_callback,
            10)
        self.bridge = CvBridge()
        self.image_count = 0
        self.latest_image = None
        self.save_next_image = False

        os.makedirs('images', exist_ok=True)

        # Start keyboard listener thread
        threading.Thread(target=self.key_listener, daemon=True).start()

    def listener_callback(self, msg):
        self.latest_image = msg
        if self.save_next_image:
            try:
                cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
                filename = f"/home/unitree/images/image_{self.image_count:04d}.jpg"
                cv2.imwrite(filename, cv_image)
                self.get_logger().info(f"✅ Saved {filename}")
                self.image_count += 1
                self.save_next_image = False
            except Exception as e:
                self.get_logger().error(f"❌ Failed to save image: {e}")

    def key_listener(self):
        self.get_logger().info("🔘 Press 's' to save image, 'q' to quit.")
        while True:
            key = self.get_key()
            if key == 's':
                self.get_logger().info("📸 Save command received.")
                self.save_next_image = True
            elif key == 'q':
                self.get_logger().info("👋 Exiting on user request.")
                rclpy.shutdown()
                break

    def get_key(self):
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return key

def main(args=None):
    rclpy.init(args=args)
    image_saver = ImageSaver()
    try:
        rclpy.spin(image_saver)
    except KeyboardInterrupt:
        pass
    image_saver.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()

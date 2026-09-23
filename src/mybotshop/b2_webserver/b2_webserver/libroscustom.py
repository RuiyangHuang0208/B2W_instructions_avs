#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Software License Agreement (BSD)
#
# @author    Salman Omar Sohail <support@mybotshop.de>
# @copyright (c) 2025, MYBOTSHOP GmbH, Inc., All rights reserved.

import subprocess

from b2_srvs.srv import B2Modes

from std_srvs.srv import Trigger, SetBool
from std_msgs.msg import Bool, Empty, String, Float64
# from ros2_interfaces.srv import CustomString

class ROS2CustomWebInterface():
    
    def __init__(self, web_node):
        self.web_node = web_node
        
        self.web_node.create_timer(1, self.ros2_webserver_control_buttons_callback)
        
        self.b2_robot_service_client = self.web_node.create_client(B2Modes, 'hardware/modes')
        self.b2_vacuum_service_client = self.web_node.create_client(B2Modes, 'rig/control')
        
    
    def ros2_webserver_control_buttons_callback(self):
        
        try:
            if self.web_node.control_block_11: # Stand Up
                self.web_node.get_logger().info("Control Block 11 is active")
                self.b2_robot_service_client.call_async(B2Modes.Request(request_data='stand_up'))
                self.web_node.control_block_11 = False
            elif self.web_node.control_block_12: 
                self.web_node.get_logger().info("Control Block 12 is active")
                self.web_node.control_block_12 = False
            elif self.web_node.control_block_13:
                self.web_node.get_logger().info("Control Block 13 is active")
                self.web_node.control_block_13 = False
            elif self.web_node.control_block_14:
                self.web_node.get_logger().info("Control Block 14 is active")
                self.web_node.control_block_14 = False
            elif self.web_node.control_block_15: # Stand Down
                self.web_node.get_logger().info("Control Block 15 is active")
                self.b2_robot_service_client.call_async(B2Modes.Request(request_data='stand_down'))
                self.web_node.control_block_15 = False
            elif self.web_node.control_block_16:
                self.web_node.get_logger().info("Control Block 16 is active")
                self.web_node.control_block_16 = False
            elif self.web_node.control_block_17:
                self.web_node.get_logger().info("Control Block 17 is active")
                self.web_node.control_block_17 = False
            elif self.web_node.control_block_18:
                self.web_node.get_logger().info("Control Block 18 is active")
                self.web_node.control_block_18 = False

            elif self.web_node.control_block_21: # Vacuum On
                self.web_node.get_logger().info("Control Block 21 is active")
                self.b2_vacuum_service_client.call_async(B2Modes.Request(request_data='vacuum_on'))
                self.web_node.control_block_21 = False
            elif self.web_node.control_block_22: # Vacuum Left Valve Open
                self.web_node.get_logger().info("Control Block 22 is active")
                self.b2_vacuum_service_client.call_async(B2Modes.Request(request_data='left_valve_open'))
                self.web_node.control_block_22 = False
            elif self.web_node.control_block_23: # Vacuum Right Valve Open
                self.web_node.get_logger().info("Control Block 23 is active")
                self.b2_vacuum_service_client.call_async(B2Modes.Request(request_data='right_valve_open'))
                self.web_node.control_block_23 = False
            elif self.web_node.control_block_24:
                self.web_node.get_logger().info("Control Block 24 is active")
                self.web_node.control_block_24 = False
            elif self.web_node.control_block_25: # Vacuum Off
                self.web_node.get_logger().info("Control Block 25 is active")
                self.b2_vacuum_service_client.call_async(B2Modes.Request(request_data='vacuum_off'))
                self.web_node.control_block_25 = False
            elif self.web_node.control_block_26: # Vacuum Left Valve Close
                self.web_node.get_logger().info("Control Block 26 is active")
                self.b2_vacuum_service_client.call_async(B2Modes.Request(request_data='left_valve_close'))
                self.web_node.control_block_26 = False
            elif self.web_node.control_block_27: # Vacuum Right Valve Close
                self.web_node.get_logger().info("Control Block 27 is active")
                self.b2_vacuum_service_client.call_async(B2Modes.Request(request_data='right_valve_close'))
                self.web_node.control_block_27 = False
            elif self.web_node.control_block_28:
                self.web_node.get_logger().info("Control Block 28 is active")
                self.web_node.control_block_28 = False
                
            elif self.web_node.control_block_31:
                self.web_node.get_logger().info("Control Block 31 is active")
                self.web_node.control_block_31 = False
            elif self.web_node.control_block_32:
                self.web_node.get_logger().info("Control Block 32 is active")
                self.web_node.control_block_32 = False
            elif self.web_node.control_block_33:
                self.web_node.get_logger().info("Control Block 33 is active")
                self.web_node.control_block_33 = False
            elif self.web_node.control_block_34:
                self.web_node.get_logger().info("Control Block 34 is active")
                self.web_node.control_block_34 = False
            elif self.web_node.control_block_35:
                self.web_node.get_logger().info("Control Block 35 is active")
                self.web_node.control_block_35 = False
            elif self.web_node.control_block_36:
                self.web_node.get_logger().info("Control Block 36 is active")
                self.web_node.control_block_36 = False
            elif self.web_node.control_block_37:
                self.web_node.get_logger().info("Control Block 37 is active")
                self.web_node.control_block_37 = False
            elif self.web_node.control_block_38:
                self.web_node.get_logger().info("Control Block 38 is active")
                self.web_node.control_block_38 = False
                
                
            # Robot Computer Control Blocks          
            elif self.web_node.control_block_41: # Reboot
                self.web_node.get_logger().info("Control Block 41 is active")
                self.web_node.sudo_command_line("sudo -S shutdown -r now")
                self.web_node.control_block_41 = False
                
            elif self.web_node.control_block_42: # Update system
                self.web_node.get_logger().info("Control Block 42 is active")
                # self.web_node.sudo_command_line("sudo -S apt-get update")
                self.web_node.control_block_42 = False
                
            elif self.web_node.control_block_43: # Clear Journal and History
                self.web_node.get_logger().info("Control Block 43 is active")
                # self.web_node.sudo_command_line("sudo -S journalctl --vacuum-time=7d; history -c")
                self.web_node.control_block_43 = False
                
            elif self.web_node.control_block_44: # Reload Udev Rules
                self.web_node.get_logger().info("Control Block 44 is active")
                self.web_node.sudo_command_line("sudo -S udevadm control --reload && sudo udevadm trigger")
                self.web_node.control_block_44 = False
                
            elif self.web_node.control_block_45: # Shutdown
                self.web_node.get_logger().info("Control Block 45 is active")
                self.web_node.sudo_command_line("sudo -S shutdown -h now")
                self.web_node.control_block_45 = False
                
            elif self.web_node.control_block_46: # Upgrade System
                self.web_node.get_logger().info("Control Block 46 is active")
                # self.web_node.sudo_command_line("sudo -S apt upgrade -y")
                self.web_node.control_block_46 = False
                
            elif self.web_node.control_block_47: # Restart NetworkManager
                self.web_node.get_logger().info("Control Block 47 is active")
                self.web_node.sudo_command_line("sudo -S systemctl restart NetworkManager")
                self.web_node.control_block_47 = False
                
            elif self.web_node.control_block_48: # Clear Memory Cache
                self.web_node.get_logger().info("Control Block 48 is active")
                self.web_node.sudo_command_line("sudo -S sync; sudo -S sysctl -w vm.drop_caches=3")
                self.web_node.control_block_48 = False
        
        except Exception as e:
            self.web_node.get_logger().error(f"Error in ros2_webserver_control_buttons_callback: {e}")
        
    def __del__(self):
        pass
        

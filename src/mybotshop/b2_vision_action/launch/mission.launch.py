#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Software License Agreement (BSD)
#
# @author    Salman Omar Sohail <support@mybotshop.de>
# @copyright (c) 2025, MYBOTSHOP GmbH, Inc., All rights reserved.

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare
from launch.actions import SetEnvironmentVariable

def generate_launch_description():

    b2_control_domain_id = SetEnvironmentVariable('ROS_DOMAIN_ID', '10')
    
    nsp = os.environ.get('B2_NS', 'b2_unit_001')
    rmp = [
        ('/tf', 'tf'),
        ('/tf_static', 'tf_static'),
    ]

    filepath_config_ros2_utils = PathJoinSubstitution(
        [FindPackageShare('b2_vision_action'),
         'config', ('robot_vision.yaml')]
    )

    node_vision = Node(
        namespace=nsp,
        remappings=rmp,
        name='b2_vision_action',
        package='b2_vision_action',
        executable='detection_server',
        output='screen',
        parameters=[filepath_config_ros2_utils]
    )

    ld = LaunchDescription()
    
    ld.add_action(b2_control_domain_id)
    ld.add_action(node_vision)

    return ld

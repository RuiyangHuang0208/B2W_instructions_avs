#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Software License Agreement (BSD)
#
# @author    Salman Omar Sohail <support@mybotshop.de>
# @copyright (c) 2024, MYBOTSHOP GmbH, Inc., All rights reserved.

import os
import launch
import launch_ros.actions
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

    serial_ros_params = PathJoinSubstitution(
        [FindPackageShare('b2_nano'), 'config', 'nano.yaml'])

    node_embedded_sys = launch_ros.actions.Node(
        namespace=nsp,
        remappings=rmp,
        respawn=True,
        name='b2_nano',
        package='b2_nano',
        executable='serial_driver',
        output='screen',
        parameters=[serial_ros_params]
    )

    ld = launch.LaunchDescription()

    ld.add_action(b2_control_domain_id)
    ld.add_action(node_embedded_sys)

    return ld

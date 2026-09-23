#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import launch_ros.actions

from launch import LaunchDescription
from launch.actions import SetEnvironmentVariable

def generate_launch_description():
    b2_control_domain_id = SetEnvironmentVariable('ROS_DOMAIN_ID', '10')

    nsp = os.environ.get('B2_NS', 'b2_unit_001')
    rmp = [
        ('/tf', 'tf'),
        ('/tf_static', 'tf_static'),
        ('/diagnostics', 'diagnostics'),
        ('cloud_in', 'livox/lidar'),
        ('scan', 'scan')
    ]

    launch_scan = launch_ros.actions.Node(namespace=nsp,
                                              remappings=rmp,
                                              name='pointcloud_to_laserscan',
                                              package='pointcloud_to_laserscan',
                                              executable='pointcloud_to_laserscan_node',
                                              parameters=[{'target_frame': 'lidar_link',
                                                           'transform_tolerance': 0.01,
                                                           'min_height': 0.05,
                                                           'max_height': 0.7,
                                                           'angle_min': -3.14,
                                                           'angle_max': 3.14,
                                                           'angle_increment': 0.033,
                                                           'scan_time': 0.005,
                                                           'range_min': 0.3,
                                                           'range_max': 80.0,
                                                           'use_inf': True,
                                                           'inf_epsilon': 1.0}],
                                              )

    ld = LaunchDescription()
    
    ld.add_action(b2_control_domain_id)
    ld.add_action(launch_scan)

    return ld

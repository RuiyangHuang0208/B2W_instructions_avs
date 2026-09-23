#!/usr/bin/env python3
"""Launch file for Z1 SBUS RC Teleop node."""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get package share directory
    pkg_share = get_package_share_directory('z1_rc_teleop')

    # Get namespace from environment variable (default: z1)
    namespace = os.environ.get('Z1_NS', 'z1')

    # Config file path
    config_file = os.path.join(pkg_share, 'config', 'sbus_teleop.yaml')

    return LaunchDescription([
        # Set ROS_DOMAIN_ID
        SetEnvironmentVariable('ROS_DOMAIN_ID', '10'),

        # Z1 SBUS Teleop Node
        Node(
            package='z1_rc_teleop',
            executable='sbus_teleop_node',
            name='z1_sbus_teleop_node',
            namespace=namespace,
            output='screen',
            parameters=[config_file],
        ),
    ])

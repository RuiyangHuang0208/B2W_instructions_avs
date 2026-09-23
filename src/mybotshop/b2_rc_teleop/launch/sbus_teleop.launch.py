#!/usr/bin/env python3
"""Launch file for SBUS RC Teleop node."""

import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, SetEnvironmentVariable
from launch.substitutions import LaunchConfiguration, EnvironmentVariable
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():
    # Get package share directory
    pkg_share = get_package_share_directory('b2_rc_teleop')

    # Get namespace from environment variable (default: b2_366)
    namespace = os.environ.get('B2_NS', 'b2_366')

    # Config file path
    config_file = os.path.join(pkg_share, 'config', 'sbus_teleop.yaml')

    return LaunchDescription([
        # Set ROS_DOMAIN_ID
        SetEnvironmentVariable('ROS_DOMAIN_ID', '10'),

        # SBUS Teleop Node
        Node(
            package='b2_rc_teleop',
            executable='sbus_teleop_node',
            name='sbus_teleop_node',
            namespace=namespace,
            output='screen',
            parameters=[config_file],
            remappings=[
                ('cmd_vel', 'rc_teleop/cmd_vel'),
                ('body_pose', 'hardware/body_pose'),
            ],
        ),
    ])

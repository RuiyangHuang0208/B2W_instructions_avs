#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import SetEnvironmentVariable
from ament_index_python.packages import get_package_share_directory


xfer_format = 0      # Set pointcloud format
                     # 0 -- Livox pointcloud2(PointXYZRTLT) pointcloud format
                     # 1 -- Livox customized pointcloud format
multi_topic = 0      # 0-All LiDARs share the same topic, 1-One LiDAR one topic
data_src = 0         # 0-lidar, others-Invalid data src
publish_freq = 20.0  # freqency of publish, 5.0, 10.0, 20.0, 50.0, etc.
output_type = 0
frame_id = 'lidar_link'
lvx_file_path = '/opt/mybotshop/livox_test.lvx'
cmdline_bd_code = 'livox0000000001'

user_config_path = os.path.join(get_package_share_directory('b2_lidars'), 'config', 'livox_mid360.json')

livox_ros2_params = [
    {"xfer_format": xfer_format},
    {"multi_topic": multi_topic},
    {"data_src": data_src},
    {"publish_freq": publish_freq},
    {"output_data_type": output_type},
    {"frame_id": frame_id},
    {"lvx_file_path": lvx_file_path},
    {"user_config_path": user_config_path},
    {"cmdline_input_bd_code": cmdline_bd_code}
]


def generate_launch_description():
    b2_control_domain_id = SetEnvironmentVariable('ROS_DOMAIN_ID', '10')

    nsp = os.environ.get('B2_NS', 'b2_unit_001')
    rmp = [('/tf', 'tf'),
           ('/tf_static', 'tf_static'),
           ]

    livox_driver = Node(
        namespace=nsp,
        remappings=rmp,
        name='livox_mid360',
        package='livox_ros_driver2',
        executable='livox_ros_driver2_node',
        output='screen',
        parameters=livox_ros2_params,
    )

    ld = LaunchDescription()

    ld.add_action(b2_control_domain_id)
    ld.add_action(livox_driver)

    return ld

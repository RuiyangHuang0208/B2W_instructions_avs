#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Software License Agreement (BSD)
#
# @author    Salman Omar Sohail <support@mybotshop.de>
# @copyright (c) 2025, MYBOTSHOP GmbH, Inc., All rights reserved.

import os
from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.actions import SetEnvironmentVariable


def generate_launch_description():

    b2_control_domain_id = SetEnvironmentVariable('ROS_DOMAIN_ID', '10')

    nsp = os.environ.get('B2_NS', 'b2_unit_001')
    rmp = [
        ('/tf', 'tf'),
        ('/tf_static', 'tf_static'),
        ('/goal_pose', 'goal_pose'),
        ('/clicked_point', 'clicked_point'),
        ('/initialpose', 'initialpose'),
        ('/robot_description', 'robot_description'),
        ('/global_costmap/costmap', 'global_costmap/costmap'),
        ('/global_costmap/costmap_updates', 'global_costmap/costmap_updates'),
        ('/global_costmap/published_footprint',
         'global_costmap/published_footprint'),
        ('/local_costmap/published_footprint',
         'local_costmap/published_footprint'),
        ('/local_costmap/costmap', 'local_costmap/costmap'),
        ('/local_costmap/costmap_updates', 'local_costmap/costmap_updates'),
        ('/map', 'map'),
        ('/map_updates', 'map_updates'),
        ('/marker', 'marker'),
        ('/local_plan', 'local_plan'),
        ('/plan', 'plan'),
        ('/assisted_teleop', 'assisted_teleop'),
        ('/backup', 'backup'),
        ('/compute_path_through_poses', 'compute_path_through_poses'),
        ('/compute_path_to_pose', 'compute_path_to_pose'),
        ('/drive_on_heading', 'drive_on_heading'),
        ('/follow_path', 'follow_path'),
        ('/follow_waypoints', 'follow_waypoints'),
        ('/navigate_through_poses', 'navigate_through_poses'),
        ('/navigate_to_pose', 'navigate_to_pose'),
        ('/smooth_path', 'smooth_path'),
        ('/spin', 'spin'),
        ('/wait', 'wait')

    ]
    rviz_config_file = PathJoinSubstitution(
        [FindPackageShare("b2_viz"), "rviz", "robot.rviz"]
    )

    node_rviz = Node(
        namespace=nsp,
        remappings=rmp,
        package='rviz2',
        executable='rviz2',
        name='rviz',
        arguments=['-d', rviz_config_file],
        output='screen'
    )

    ld = LaunchDescription()

    ld.add_action(b2_control_domain_id)
    ld.add_action(node_rviz)

    return ld

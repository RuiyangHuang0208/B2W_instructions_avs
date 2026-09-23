#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Software License Agreement (BSD)
#
# @author    Salman Omar Sohail <support@mybotshop.de>
# @copyright (c) 2025, MYBOTSHOP GmbH, Inc., All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, is not permitted without the express permission
# of MYBOTSHOP GmbH.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

import os
from launch import LaunchDescription
from launch.actions import ExecuteProcess
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
        [FindPackageShare('b2_webserver'), 'config', ('robot_webserver.yaml')]
    )

    node_webserver = Node(
        namespace=nsp,
        remappings=rmp,
        name='b2_webserver',
        package='b2_webserver',
        executable='webserver',
        output='screen',
        parameters=[filepath_config_ros2_utils]
    )
    
    # Start VNC server
    vncserver_process = ExecuteProcess(
        cmd=['vncserver', ':1', '-geometry', '1920x1080',
             '-depth', '24', '-localhost', 'no'],
        output='screen',
        additional_env={'HOME': '/home/unitree'}
    )

    # Start Websockify to forward VNC to browser
    websockify_process = ExecuteProcess(
        cmd=['websockify', '6080', '127.0.0.1:5901'],
        output='screen'
    )

    ld = LaunchDescription()
    
    ld.add_action(b2_control_domain_id)
    ld.add_action(vncserver_process)
    ld.add_action(websockify_process)
    
    ld.add_action(node_webserver)

    return ld

#!/usr/bin/env python3

# Software License Agreement (BSD)
#
# @author    Salman Omar Sohail <support@mybotshop.de>
# @copyright (c) 2024, MYBOTSHOP GmbH, Inc., All rights reserved.
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
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch.actions import RegisterEventHandler, EmitEvent
from launch.events import Shutdown
from launch.event_handlers import OnProcessExit
from launch.actions import SetEnvironmentVariable

def generate_launch_description():

    b2_control_domain_id = SetEnvironmentVariable('ROS_DOMAIN_ID', '10')

    nap = os.environ.get('B2_NS', 'b2_unit_001')
    nsp = nap + "/drotek"
    rmp = [
        ('/diagnostics', 'diagnostics'),
        ('/tf', 'tf'),
        ('/tf_static', 'tf_static'),
    ]

    config_drotek = PathJoinSubstitution(
        [FindPackageShare('b2_gps'),
         'config',
         'drotek.yaml'],
    )

    ublox_gps_node = Node(
        namespace=nsp,
        remappings=rmp,
        package='ublox_gps',
        executable='ublox_gps_node',
        output='both',
        parameters=[config_drotek])

    ld = LaunchDescription()
    
    ld.add_action(b2_control_domain_id)
    ld.add_action(ublox_gps_node)

    ld.add_action(RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=ublox_gps_node,
            on_exit=[EmitEvent(
                event=Shutdown())],
        )))

    return ld

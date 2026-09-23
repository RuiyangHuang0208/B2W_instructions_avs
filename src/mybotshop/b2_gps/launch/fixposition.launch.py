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

def generate_launch_description():
    
    nsp = os.environ.get('B2_NS', 'b2_unit_001')
    rmp = [
        ('/diagnostics', 'diagnostics'),
        ('/tf', 'tf'),
        ('/tf_static', 'tf_static'),
    ]
    
    # Fixposition
    config_fixposition = PathJoinSubstitution(
        [FindPackageShare('b2_gps'),
        'config',
        'fixposition.yaml'],
    )
    
    node_fixposition = Node(
            package='fixposition_driver_ros2',
            executable='fixposition_driver_ros2_exec',
            name='fixposition_driver_ros2',
            namespace=nsp,
            output='screen',
            parameters=[config_fixposition],
            remappings=[
              ('/diagnostics', 'diagnostics'),
              ('/tf', 'tf'),
              ('/tf_static', 'tf_static'),
            ]
        )
    
    ld = LaunchDescription()
    
    ld.add_action(node_fixposition)

    return ld
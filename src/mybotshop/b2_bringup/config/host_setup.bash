#!/bin/bash

# Software License Agreement (BSD)
#
# @author    Salman Omar Sohail <support@mybotshop.de>
# @copyright (c) 2025, MYBOTSHOP GmbH, Inc., All rights reserved.

echo "Setup Local unitree ros2 environment"
source /opt/ros/humble/setup.bash

# Examine the following line and make sure the path is correct for your pc
# source /home/administrator/projects/quadruped/qre_b2/install/setup.bash

export ROS_DOMAIN_ID=10
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=/home/administrator/projects/quadruped/qre_b2/src/b2_bringup/config/multi_robot_cyclone_host.xml

# Single - Robot
# Examine the following line and make sure the interface is correct use command: ifconfig to check

# export CYCLONEDDS_URI='<CycloneDDS><Domain Id="10"><General><Interfaces>
#                             <NetworkInterface name="enx9cebe86d0a5d" priority="default" multicast="default" />
#                         </Interfaces>
#                         <AllowMulticast>true</AllowMulticast>
#                       </General></Domain></CycloneDDS>'

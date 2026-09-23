#!/bin/bash

# Software License Agreement (BSD)
#
# @author    Salman Omar Sohail <support@mybotshop.de>
# @copyright (c) 2025, MYBOTSHOP GmbH, Inc., All rights reserved.

echo "Setup Local unitree ros2 environment"

# For from-source ROS2 Humble build:
source ~/ros2_humble/install/local_setup.bash

# For standard ROS2 installation (uncomment if using apt-installed ROS2):
# source /opt/ros/humble/setup.bash

# For this workspace (uncomment if built):
# source /home/brusnicki/Documents/NEW_b2_REPO/qre_b2/install/setup.bash

export ROS_DOMAIN_ID=10
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export CYCLONEDDS_URI=/home/brusnicki/Documents/NEW_b2_REPO/qre_b2/src/mybotshop/b2_bringup/config/multi_robot_cyclone_host.xml

# Single - Robot
# Examine the following line and make sure the interface is correct use command: ifconfig to check

# export CYCLONEDDS_URI='<CycloneDDS><Domain Id="10"><General><Interfaces>
#                             <NetworkInterface name="enx9cebe86d0a5d" priority="default" multicast="default" />
#                         </Interfaces>
#                         <AllowMulticast>true</AllowMulticast>
#                       </General></Domain></CycloneDDS>'

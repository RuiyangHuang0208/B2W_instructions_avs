#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Software License Agreement (BSD)
#
# @author    Salman Omar Sohail <support@mybotshop.de>
# @copyright (c) 2025, MYBOTSHOP GmbH, Inc., All rights reserved.

import os
import robot_upstart
from ament_index_python.packages import get_package_share_directory


def install_job(job_name, package_name, launch_filename, domain_id=10,
                e_user=None, rmw_type='rmw_cyclonedds_cpp', disable_srvs=False):
    
    # 0. Print Configuration 
    print(color_string(34, "Installing job: {}".format(job_name)))
    print(color_string(34, "Package: {}".format(package_name)))
    print(color_string(34, "Launch File: {}".format(launch_filename)))
    print(color_string(34, "Domain ID: {}".format(domain_id)))
    print(color_string(34, "RMW Type: {}".format(rmw_type)))
    print(color_string(34, "User: {}".format(e_user)))
    print(color_string(34, "Disable Services: {}".format(disable_srvs)))
    print(color_string(34, "----------------------------------------"))

    # 1. Uninstall existing service
    print(color_string(33, "Uninstalling existing service: {}".format(job_name)))
    os.system("sudo service {} stop".format(job_name))
    uninstall_job = robot_upstart.Job(
        name=job_name, rosdistro=os.environ['ROS_DISTRO'])
    uninstall_job.uninstall()

    # 2. Configure new service
    print(color_string(32, "Installing new service: {}".format(job_name)))
    linux_service = robot_upstart.Job(name=job_name,
                                      user=e_user,
                                      ros_domain_id=domain_id,
                                      rmw=rmw_type,
                                      workspace_setup=os.path.join(
                                          get_package_share_directory('b2_bringup'), 'config/setup.bash')
                                      )

    linux_service.add(package=package_name, filename=launch_filename)
    linux_service.install()

    # 3. Set service state
    if disable_srvs:
        os.system("sudo systemctl disable {}".format(job_name))
        return

    # 4. Refresh for activation
    os.system(
        "sudo systemctl daemon-reload && sudo systemctl start {}".format(job_name))


def color_string(color, string):
    return "\033[{}m{}\033[0m".format(color, string)


if __name__ == "__main__":

    jobs = [
        {"name": "b2-nano",
         "package": "b2_nano",
         "launch_filename": "launch/serial_driver.launch.py",
         "user": "unitree",
         "disable": True,
         },
        
        {"name": "b2-hardware",
         "package": "b2_platform",
         "launch_filename": "launch/hardware.launch.py",
         "disable": True,         
         "user": "unitree",},
        
        {"name": "b2-twistmux",
         "package": "b2_control",
         "launch_filename": "launch/twistmux.launch.py",
         "disable": True,         
         "user": "unitree",},

        {"name": "b2-webserver",
         "package": "b2_webserver",
         "launch_filename": "launch/webserver.launch.py"},

        {"name": "b2-statepublisher",
         "package": "b2_platform",
         "disable": True,         
         "launch_filename": "launch/state_publisher.launch.py"},
        
        {"name": "b2-domain-bridge",
         "package": "b2_platform",
         "disable": True,         
         "launch_filename": "launch/bridge.launch.py"},

        # {"name": "b2-control",
        #  "package": "b2_control",
        #  "launch_filename": "launch/control.launch.py",
        #  "disable": False},

        {"name": "b2-description",
         "package": "b2_description",
         "disable": True,         
         "launch_filename": "launch/b2_description.launch.py"},
        
        # {"name": "b2w-description",
        #  "package": "b2_description",
        #  "launch_filename": "launch/b2w_description.launch.py"},

        {"name": "b2-front-video",
         "package": "b2_platform",
         "disable": True,         
         "launch_filename": "launch/front_video.launch.py"},
        
        {"name": "b2-rear-video",
         "package": "b2_platform",
         "disable": True,         
         "launch_filename": "launch/rear_video.launch.py"},
        
        {"name": "b2-livox-mid360",
         "package": "b2_lidars",
         "disable": True,         
         "launch_filename": "launch/livox_mid360.launch.py"},
        
        # {"name": "b2-drotek",
        #  "package": "b2_gps",
        #  "disable": True,         
        #  "launch_filename": "launch/drotek.launch.py"},
        
        {"name": "b2-realsense-d405",
         "package": "b2_depth_camera",
         "disable": True,         
         "launch_filename": "launch/realsense_d435i.launch.py"},
        
        {"name": "b2-pcd-scan",
         "package": "b2_lidars",
         "disable": True,         
         "launch_filename": "launch/pcd_to_laserscan.launch.py"},
    ]

    for job in jobs:
        install_job(job_name=job["name"],
                    package_name=job["package"],
                    launch_filename=job["launch_filename"],
                    disable_srvs=job.get("disable", False),
                    rmw_type=job.get("rmw_type", "rmw_cyclonedds_cpp"),
                    e_user=job.get("user", None),
                    )

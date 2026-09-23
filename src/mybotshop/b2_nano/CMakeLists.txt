cmake_minimum_required(VERSION 3.5)
project(b2_nano)
add_compile_options(-std=c++17)

set(AMENT_DEPENDENCIES rclcpp 
                       rclpy
                       geometry_msgs
                       sensor_msgs
                       nav_msgs
                       tf2
                       tf2_ros
                       std_srvs 
                       std_msgs
                       rosbag2_cpp)

set (DEPENDENCY_LIST rclcpp
                     std_msgs
                     std_srvs)

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)
find_package(geometry_msgs REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(tf2 REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)

install(PROGRAMS  b2_nano/serial_driver
                  DESTINATION lib/${PROJECT_NAME}
)
# Install Python modules
ament_python_install_package(${PROJECT_NAME})

install(DIRECTORY launch config
                  DESTINATION share/${PROJECT_NAME}
)

ament_package()
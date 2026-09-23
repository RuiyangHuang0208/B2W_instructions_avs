cmake_minimum_required(VERSION 3.5)
project(b2_vision_action)

set(AMENT_DEPENDENCIES rclpy tf2 tf2_ros)

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)

# Install Python modules
ament_python_install_package(${PROJECT_NAME})

# Install executables
install(DIRECTORY config launch b2_vision_action
  DESTINATION share/${PROJECT_NAME}
)

# Install Python executables
install(PROGRAMS scripts/detection_server
  ${PROJECT_NAME}/libimagecapture.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()

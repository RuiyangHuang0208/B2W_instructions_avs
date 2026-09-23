cmake_minimum_required(VERSION 3.5)
project(b2_bringup)

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclpy REQUIRED)

# Install Python modules
ament_python_install_package(${PROJECT_NAME})

# Install Python executables
install(PROGRAMS
  scripts/startup_installer.py
  config/setup.bash
  DESTINATION lib/${PROJECT_NAME}
)

# Add Launch File
install(DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

# Auto source bash
install(
  DIRECTORY hooks/
  DESTINATION share/${PROJECT_NAME}/hooks
)
ament_environment_hooks("${CMAKE_CURRENT_SOURCE_DIR}/hooks/robot_bringup.bash")

ament_package()
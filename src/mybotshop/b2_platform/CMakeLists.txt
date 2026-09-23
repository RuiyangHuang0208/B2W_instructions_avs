cmake_minimum_required(VERSION 3.5)
project(b2_platform)
add_compile_options(-std=c++17)

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
find_package(unitree_go REQUIRED)
find_package(unitree_api REQUIRED)
find_package(std_msgs REQUIRED)
find_package(std_srvs REQUIRED)
find_package(rosbag2_cpp REQUIRED)
find_package(b2_srvs REQUIRED)
find_package(camera_info_manager REQUIRED)
find_package(OpenCV REQUIRED)
find_package(cv_bridge REQUIRED)
find_package(PkgConfig REQUIRED)

pkg_check_modules(GSTREAMER_APP REQUIRED gstreamer-app-1.0)

# Set dependencies
set(DEPENDENCY_LIST unitree_go
        unitree_api
        rclcpp
        rclpy
        geometry_msgs
        sensor_msgs
        nav_msgs
        tf2
        tf2_ros
        std_srvs
        std_msgs
        b2_srvs
        rosbag2_cpp
        cv_bridge
        camera_info_manager)

set(CMAKE_CXX_FLAGS "-O3 -fPIC")

################################# Unitree SDK ROS2 Control
include_directories(
        include /usr/include/eigen3
        include /usr/local/include/ddscxx
        include /usr/local/include/iceoryx/v2.0.2
        include/qre
        include/unitree
        ${OpenCV_INCLUDE_DIRS}
        ${cv_bridge_INCLUDE_DIRS}
        ${GSTREAMER_APP_INCLUDE_DIRS})

link_libraries(unitree_sdk2 ddsc ddscxx rt pthread)

# Include Cpp "include" directory
link_directories(src)

# Executable
add_executable(b2_video src/b2_video.cpp)
add_executable(b2w_test src/b2w_test.cpp)
add_executable(b2_highroscontrol src/b2_highroscontrol.cpp)
add_executable(b2_lowroscontrol src/b2_lowlevel_example.cpp)

# Linking
target_link_libraries(b2_video
        ${GSTREAMER_APP_LIBRARIES}
        ${OpenCV_LIBS}
)

ament_target_dependencies(b2w_test ${DEPENDENCY_LIST})
ament_target_dependencies(b2_video ${DEPENDENCY_LIST})
ament_target_dependencies(b2_highroscontrol ${DEPENDENCY_LIST})
ament_target_dependencies(b2_lowroscontrol ${DEPENDENCY_LIST})

install(PROGRAMS b2_platform/b2_statepublisher
        DESTINATION lib/${PROJECT_NAME}
)

install(TARGETS b2_highroscontrol
        b2_lowroscontrol
        b2w_test
        b2_video
        DESTINATION lib/${PROJECT_NAME})

install(DIRECTORY launch config
        DESTINATION share/${PROJECT_NAME}
)

ament_python_install_package(${PROJECT_NAME})
ament_package()

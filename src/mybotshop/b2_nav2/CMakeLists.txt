cmake_minimum_required(VERSION 3.5)
project(b2_nav2)
find_package(ament_cmake REQUIRED)
install(
  DIRECTORY launch maps param behavior_trees
  DESTINATION share/${PROJECT_NAME}
)
ament_package()
#!/usr/bin/env bash

function color_echo () {
    echo -e "${GREEN}$1${NC}"
}

function install_binary_packages () {
    color_echo "Installing Debian pacakges."
    sudo apt-get update
    sudo apt-get install openssh*\
                         build-essential\
                         libpcap-dev \
                         chrony\
                         sshpass\
                         neofetch\
                         libpcl-dev\
                         cmake\
                         libglfw3-dev\
                         libglew-dev\
                         libeigen3-dev\
                         libjsoncpp-dev\
                         libtclap-dev\
                         libeigen3-dev\
                         libboost-all-dev\
                         libgstreamer1.0-dev \
                         libgstreamer-plugins-base1.0-dev \
                         gstreamer1.0-tools \
                         gstreamer1.0-plugins-base \
                         gstreamer1.0-plugins-good \
                         gstreamer1.0-plugins-bad \
                         gstreamer1.0-plugins-ugly \
                         gstreamer1.0-libav \
                         gstreamer1.0-x \
                         gstreamer1.0-alsa \
                         gstreamer1.0-gl \
                         gstreamer1.0-gtk3 \
                         gstreamer1.0-pulseaudio\
                         git\
                         libbullet-dev\
                         python3-pip\
                         python3-colcon-common-extensions\
                         python3-flake8\
                         python3-pytest-cov\
                         python3-rosdep\
                         python3-setuptools\
                         python3-vcstool\
                         wget -y

    color_echo "Installing Python pacakges."
    pip3 install flask
    python3.10 -m pip install flask

    color_echo "Installing ROS2 Humble pacakges."
    sudo apt-get install ros-humble-robot-upstart\
                         ros-humble-teleop-twist-keyboard\
                         ros-humble-teleop-twist-joy\
                         ros-humble-geodesy\
                         ros-humble-pcl-ros\
                         ros-humble-nmea-msgs\
                         ros-humble-robot-localization\
                         ros-humble-interactive-marker-twist-server\
                         ros-humble-pointcloud-to-laserscan\
                         ros-humble-twist-mux\
                         ros-humble-rmw-cyclonedds-cpp\
                         ros-humble-rosidl-generator-dds-idl\
                         ros-humble-navigation2\
                         ros-humble-joint-state-publisher-gui\
                         ros-humble-ros2-control\
                         ros-humble-ros2-controllers\
                         ros-humble-gripper-controllers\
                         ros-humble-xacro\
                         ros-humble-navigation2\
                         ros-humble-realsense2-*\
                         ros-humble-librealsense2*\
                         ros-humble-apriltag\
                         ros-humble-camera-info-manager\
                         ros-humble-image-proc\
                         ros-humble-domain-bridge\
                         ros-humble-ros-gz\
                         ros-humble-gz-ros2-control\
                         ros-humble-nav2-* -y
}

function install_debian () {
    color_echo "Copying over debian packages"
    sudo cp b2_bringup/debian/99-super-usb.rules /etc/udev/rules.d/
    sudo cp b2_bringup/debian/90-logitech.rules /etc/udev/rules.d/
    sudo service udev restart && sudo udevadm trigger
    sudo usermod -aG input $USER
}

function install_motd () {
    color_echo "Copying over motd"
    sudo chmod -x /etc/update-motd.d/*
    sudo cp b2_bringup/config/10-qre-b2 /etc/update-motd.d/
    sudo chmod +x /etc/update-motd.d/10-qre-b2
}

function install_livox () {
    echo -e "${CYAN}Installing Livox${NC}"
    rm -rf ../third_party/8May2025_livox_sdk/build
    mkdir ../third_party/8May2025_livox_sdk/build 
    cd ../third_party/8May2025_livox_sdk/build
    cmake .. 
    make -j4
    sudo make install
}


RED='\033[0;31m'
DGREEN='\033[0;32m'
GREEN='\033[1;32m'
WHITE='\033[0;37m'
BLUE='\033[1;34m'
CYAN='\033[1;36m'
NC='\033[0m' 
                                                                                          
echo -e "${DGREEN}------------------------------------------------------------------------------------------------------"
echo -e " _______           _______  ______   _______           _______  _______  ______     ______   _______  "
echo -e "(  ___  )|\     /|(  ___  )(  __  \ (  ____ )|\     /|(  ____ )(  ____ \(  __  \   (  __  \ (  ____ \ "
echo -e "| (   ) || )   ( || (   ) || (  \  )| (    )|| )   ( || (    )|| (    \/| (  \  )  | (  \  )| (    \/ "
echo -e "| |   | || |   | || (___) || |   ) || (____)|| |   | || (____)|| (__    | |   ) |  | |   ) || (__     "
echo -e "| |   | || |   | ||  ___  || |   | ||     __)| |   | ||  _____)|  __)   | |   | |  | |   | ||  __)    "
echo -e "| | /\| || |   | || (   ) || |   ) || (\ (   | |   | || (      | (      | |   ) |  | |   ) || (       "
echo -e "| (_\ \ || (___) || )   ( || (__/  )| ) \ \__| (___) || )      | (____/\| (__/  )_ | (__/  )| (____/\ "
echo -e "(____\/_)(_______)|/     \|(______/ |/   \__/(_______)|/       (_______/(______/(_)(______/ (_______/ "
echo -e ""                                                                                                                                   
echo -e "------------------------------------------------------------------------------------------------------"
echo -e "Installing Required Libraries and ROS dependencies! "                                                                                                                                         
echo -e "------------------------------------------------------------------------------------------------------${NC}"

# Binary packages installation
install_binary_packages
install_debian
install_motd

# Optional packages
# install_livox
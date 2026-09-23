# Building ROS2 Humble from Source on Ubuntu 20.04

This guide documents the steps to build ROS2 Humble from source on Ubuntu 20.04, which is necessary because official Humble packages are only available for Ubuntu 22.04.

**Source:** [ROS 2 Documentation - Ubuntu Development Setup](https://docs.ros.org/en/humble/Installation/Alternatives/Ubuntu-Development-Setup.html)

**Estimated build time:** 1-2 hours

---

## Step 1: System Setup (Locale)

```bash
sudo apt update && sudo apt install locales
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
```

---

## Step 2: Add ROS2 Repository

```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
export ROS_APT_SOURCE_VERSION=$(curl -s https://api.github.com/repos/ros-infrastructure/ros-apt-source/releases/latest | grep -F "tag_name" | awk -F\" '{print $4}')
curl -L -o /tmp/ros2-apt-source.deb "https://github.com/ros-infrastructure/ros-apt-source/releases/download/${ROS_APT_SOURCE_VERSION}/ros2-apt-source_${ROS_APT_SOURCE_VERSION}.$(. /etc/os-release && echo ${UBUNTU_CODENAME:-${VERSION_CODENAME}})_all.deb"
sudo dpkg -i /tmp/ros2-apt-source.deb
```

---

## Step 3: Install Dependencies

**Common packages:**
```bash
sudo apt update && sudo apt install -y \
  python3-flake8-docstrings \
  python3-pip \
  python3-pytest-cov \
  ros-dev-tools
```

**Ubuntu 20.04 specific (via pip):**
```bash
python3 -m pip install -U \
   flake8-blind-except \
   flake8-builtins \
   flake8-class-newline \
   flake8-comprehensions \
   flake8-deprecated \
   flake8-import-order \
   flake8-quotes \
   "pytest>=5.3" \
   pytest-repeat \
   pytest-rerunfailures \
   empy==3.3.4
```

---

## Step 4: Get Source Code

```bash
mkdir -p ~/ros2_humble/src
cd ~/ros2_humble
vcs import --input https://raw.githubusercontent.com/ros2/ros2/humble/ros2.repos src
```

---

## Step 4.5: Clone Missing Packages (Ubuntu 20.04 specific)

The standard ros2.repos file doesn't include all packages needed for Ubuntu 20.04. Clone these additional repositories:

```bash
cd ~/ros2_humble/src
git clone -b humble https://github.com/ros/class_loader.git
git clone -b humble https://github.com/ros/pluginlib.git
git clone -b humble https://github.com/ros/resource_retriever.git
git clone -b humble https://github.com/ros/robot_state_publisher.git
git clone -b humble https://github.com/ros/ros_environment.git
git clone -b humble https://github.com/ros/kdl_parser.git
git clone -b humble https://github.com/ros-visualization/rqt.git
```

---

## Step 5: Install Build Dependencies

```bash
# Only run 'sudo rosdep init' if not already done
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src -y --rosdistro humble --skip-keys "fastcdr rti-connext-dds-6.0.1 urdfdom_headers pluginlib resource_retriever rqt_plot ros2plugin ros_environment robot_state_publisher class_loader"
```

---

## Step 6: Build

```bash
cd ~/ros2_humble/
colcon build --symlink-install
```

> **Note:** This step takes 1-2 hours depending on your system.

---

## Step 7: Environment Setup

Add to your `.bashrc` for permanent setup:
```bash
echo 'source ~/ros2_humble/install/local_setup.bash' >> ~/.bashrc
```

Or source manually when needed:
```bash
source ~/ros2_humble/install/local_setup.bash
```

---

## Verification

Test in two separate terminals:

**Terminal 1:**
```bash
source ~/ros2_humble/install/local_setup.bash
ros2 run demo_nodes_cpp talker
```

**Terminal 2:**
```bash
source ~/ros2_humble/install/local_setup.bash
ros2 run demo_nodes_py listener
```

You should see the talker publishing messages and the listener receiving them.

---

## Notes

- You can have multiple ROS2 versions installed (e.g., Foxy and Humble)
- Just source the one you need: `source ~/ros2_humble/install/local_setup.bash` for Humble
- The build produces 341 packages when completed successfully
- Some packages will show stderr warnings (libcurl, qt_gui_cpp, rviz packages) - these are harmless warnings, not errors
- If the build fails with "package not found" errors, you may need to clone additional repositories from GitHub (see Step 4.5)

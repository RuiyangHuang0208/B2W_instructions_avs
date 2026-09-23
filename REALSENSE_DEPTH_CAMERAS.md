# RealSense Depth Cameras Setup Guide

This guide documents the Intel RealSense D430I depth cameras on the B2 robot.

## Hardware

Two RealSense D430I cameras are installed:

| Camera | Serial Number | USB Port | Status |
|--------|---------------|----------|--------|
| Front | 243222073012 | 2-1 | Working |
| Rear | 243222074951 | 2-3.3 | Working |

## Prerequisites

### Add user to video group (one-time setup)
```bash
sudo usermod -aG video unitree
# Logout and login again (or reboot) for changes to take effect
```

### Verify cameras are detected
```bash
lsusb | grep -i realsense
```

### Middleware Note (Important!)
The B2 robot's bashrc sets `RMW_IMPLEMENTATION=rmw_cyclonedds_cpp`, but the RealSense camera node uses the default FastDDS middleware. **You must unset this variable** in any terminal where you want to interact with camera topics:
```bash
unset RMW_IMPLEMENTATION
```

## Running the Front Camera

### Terminal 1: Launch camera node
```bash
ros2 launch realsense2_camera rs_launch.py camera_name:=front_camera serial_no:="'243222073012'"
```
Wait for "RealSense Node Is Up!" message.

### Terminal 2: Check topics and data

**Important:** You must unset `RMW_IMPLEMENTATION` to match the camera's middleware (FastDDS):
```bash
unset RMW_IMPLEMENTATION
ros2 topic list | grep camera
```

Expected topics:
- `/camera/front_camera/depth/image_rect_raw` - Depth image
- `/camera/front_camera/depth/camera_info` - Camera calibration

### Check publish rate
```bash
unset RMW_IMPLEMENTATION
ros2 topic hz /camera/front_camera/depth/image_rect_raw
```
Expected: ~30 Hz

### Visualize with rqt
```bash
unset RMW_IMPLEMENTATION
ros2 run rqt_image_view rqt_image_view
```
Select topic: `/camera/front_camera/depth/image_rect_raw`

## Running the Rear Camera

### Terminal 1: Launch camera node
```bash
ros2 launch realsense2_camera rs_launch.py camera_name:=rear_camera serial_no:="'243222074951'"
```
Wait for "RealSense Node Is Up!" message.

### Terminal 2: Check and visualize
```bash
unset RMW_IMPLEMENTATION
ros2 topic hz /camera/rear_camera/depth/image_rect_raw
```

### Visualize with rqt
```bash
unset RMW_IMPLEMENTATION
ros2 run rqt_image_view rqt_image_view
```
Select topic: `/camera/rear_camera/depth/image_rect_raw`

## Camera Specifications

| Parameter | Value |
|-----------|-------|
| Model | Intel RealSense D430I |
| Resolution | 848x480 @ 30fps (default) |
| USB | 3.2 |
| Firmware | 5.13.0.55 |
| IMU | Gyro 200Hz, Accel 100Hz |

## Troubleshooting

### Permission denied errors
```
Cannot open '/dev/video0': Permission denied
```
**Solution:** Add user to video group and reboot:
```bash
sudo usermod -aG video unitree
sudo reboot
```

### Device or resource busy
```
xioctl(VIDIOC_S_FMT) failed, errno=16 Last Error: Device or resource busy
```
**Solution:** Kill any existing RealSense processes:
```bash
pkill -f realsense
```

### Topic not publishing / hz shows nothing
1. Check if node is running: `ros2 node list | grep camera`
2. Check ROS_DOMAIN_ID matches between publisher and subscriber: `echo $ROS_DOMAIN_ID`
3. **Check RMW middleware matches** - this is critical:
   ```bash
   echo $RMW_IMPLEMENTATION
   ```
   The camera node and subscriber must use the same middleware. On B2, the bashrc may set `rmw_cyclonedds_cpp` but the camera uses default FastDDS.

   **Solution:** Unset the middleware in your subscriber terminal:
   ```bash
   unset RMW_IMPLEMENTATION
   ros2 topic hz /camera/front_camera/depth/image_rect_raw
   ```

## Known Issues

### Running both cameras simultaneously
- May cause USB bandwidth conflicts
- Try lower resolution: `depth_module.depth_profile:=424x240x15`
- Or connect cameras to different USB controllers

## ROS2 Package Info

```
ros-humble-librealsense2: 2.56.4
ros-humble-realsense2-camera: 4.56.4
```

---
*Document created: 2026-02-13*
*Tested on: B2 Robot PC4 (Ubuntu 22.04, ROS2 Humble)*

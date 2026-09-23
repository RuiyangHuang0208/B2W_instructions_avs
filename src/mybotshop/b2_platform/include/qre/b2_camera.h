#ifndef B2_CAMERA_H
#define B2_CAMERA_H

#include <mutex>
#include <gst/gst.h>
#include <gst/app/gstappsink.h>
#include <opencv2/opencv.hpp>
#include <cv_bridge/cv_bridge.h>

#include <rclcpp/rclcpp.hpp>
#include <sensor_msgs/msg/image.hpp>
#include "sensor_msgs/msg/camera_info.hpp"
#include "camera_info_manager/camera_info_manager.hpp"
#include "ament_index_cpp/get_package_share_directory.hpp"

class B2Camera : public rclcpp::Node
{
public:
    B2Camera();
    ~B2Camera();

private:
    void update_camera_image();
    static GstFlowReturn on_new_sample_from_sink(GstElement *sink, B2Camera *camera);
    std::string colorize(const std::string &text, const std::string &color) const;

    std::mutex image_mutex;
    std::string robot_camera_link;
    int picture_height;
    int picture_width;
    int picture_step;
    std::string picture_encoding;
    cv::Mat camera_state;

    std::string param_lan_port_;
    std::string param_camera_type_;
    std::string param_camera_port_;
    std::string param_camera_frame_;

    rclcpp::Publisher<sensor_msgs::msg::Image>::SharedPtr publisher_camera;
    sensor_msgs::msg::Image::SharedPtr pub_camera_data_image;
    rclcpp::TimerBase::SharedPtr timer_1_;

    rclcpp::Publisher<sensor_msgs::msg::CameraInfo>::SharedPtr publisher_camera_info;
    std::shared_ptr<camera_info_manager::CameraInfoManager> camera_info_manager_;
    sensor_msgs::msg::CameraInfo::SharedPtr pub_camera_data_info;

    GstElement *pipeline;
    GstElement *appsink;
};

#endif // B2_CAMERA_H
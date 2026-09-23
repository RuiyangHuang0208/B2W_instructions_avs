#include "b2_camera.h"

using std::placeholders::_1;

B2Camera::B2Camera() : Node("b2_camera_publisher")
{
  RCLCPP_INFO(this->get_logger(), "%s", colorize("Initializing B2 Camera Publisher!", "orange").c_str());

  // Declare parameters
  this->declare_parameter<std::string>("lan_port", "eno2");
  this->declare_parameter<std::string>("camera_type", "front");
  this->declare_parameter<std::string>("camera_port", "1720");
  this->declare_parameter<std::string>("camera_frame", "front_camera");

  // Get parameters
  param_lan_port_ = this->get_parameter("lan_port").as_string();
  param_camera_type_ = this->get_parameter("camera_type").as_string();
  param_camera_port_ = this->get_parameter("camera_port").as_string();
  param_camera_frame_ = this->get_parameter("camera_frame").as_string();

  RCLCPP_INFO(this->get_logger(), "%s", colorize("lan_port: " + param_lan_port_, "blue").c_str());
  RCLCPP_INFO(this->get_logger(), "%s", colorize("camera_type: " + param_camera_type_, "blue").c_str());
  RCLCPP_INFO(this->get_logger(), "%s", colorize("camera_port: " + param_camera_port_, "blue").c_str());
  RCLCPP_INFO(this->get_logger(), "%s", colorize("camera_frame: " + param_camera_frame_, "blue").c_str());

  robot_camera_link = param_camera_frame_;
  std::string camera_pub_topic = "sensor/" + param_camera_type_ + "/camera_raw";

  // Camera Data
  picture_height = 720;
  picture_width = 1280;
  picture_step = picture_width * 3; // For RGB
  picture_encoding = "rgb8";

  // Flags
  camera_state = cv::Mat();

  // Publishers
  publisher_camera = this->create_publisher<sensor_msgs::msg::Image>(camera_pub_topic, 1);
  pub_camera_data_image = std::make_shared<sensor_msgs::msg::Image>();

  // Timer to periodically trigger the GStreamer callback
  timer_1_ = this->create_wall_timer(
      std::chrono::milliseconds(10), std::bind(&B2Camera::update_camera_image, this));

  // Camera Capture
  gst_init(nullptr, nullptr);
  std::string gstreamer_str = "udpsrc address=230.1.1.1 "
                              "port=" +
                              param_camera_port_ + " multicast-iface=" +
                              param_lan_port_ + " ! application/x-rtp, media=video,"
                                                " encoding-name=H264 ! rtph264depay ! "
                                                "h264parse ! avdec_h264 ! videoconvert ! "
                                                "video/x-raw,width=1280,height=720,format=RGB "
                                                "! queue ! appsink name=appsink0 drop=1"; 

  GError *error = nullptr;
  pipeline = gst_parse_launch(gstreamer_str.c_str(), &error);

  if (!pipeline)
  {
    RCLCPP_FATAL(this->get_logger(), "%s", colorize("Failed to parse GStreamer pipeline: " + std::string(error ? error->message : "Unknown error"), "red").c_str());
    if (error)
      g_error_free(error);
    // Consider exiting or throwing an exception here as the camera won't work
    rclcpp::shutdown();
    return;
  }

  appsink = gst_bin_get_by_name(GST_BIN(pipeline), "appsink0");
  if (!appsink)
  {
    RCLCPP_FATAL(this->get_logger(), "%s", colorize("Failed to get appsink element from pipeline.", "red").c_str());
    gst_object_unref(pipeline);
    // Consider exiting or throwing an exception here
    rclcpp::shutdown();
    return;
  }

  g_object_set(appsink, "emit-signals", TRUE, "max-buffers", 1, nullptr);
  g_signal_connect(appsink, "new-sample", G_CALLBACK(on_new_sample_from_sink), this);

  GstStateChangeReturn state_change_ret = gst_element_set_state(pipeline, GST_STATE_PLAYING);

  if (state_change_ret == GST_STATE_CHANGE_FAILURE)
  {
    RCLCPP_FATAL(this->get_logger(), "%s", colorize("Failed to set GStreamer pipeline to PLAYING state.", "red").c_str());
    gst_object_unref(pipeline);
    // Consider exiting or throwing an exception here
    rclcpp::shutdown();
    return;
  }

  // Initialize the CameraInfoManager
  std::string camera_name = "b2_" + param_camera_type_ + "_camera";
  std::string package_name = "b2_platform";
  std::string calibration_file = "config/b2_" + param_camera_type_ + "_cam.yaml";
  std::string camera_info_url = "";
  try
  {
    camera_info_url = "file://" + ament_index_cpp::get_package_share_directory(package_name) + "/" + calibration_file;
  }
  catch (const std::exception &e)
  {
    RCLCPP_ERROR(this->get_logger(), "Failed to find package '%s': %s", package_name.c_str(), e.what());
  }

  camera_info_manager_ = std::make_shared<camera_info_manager::CameraInfoManager>(this, camera_name, camera_info_url);

  if (!camera_info_url.empty() && camera_info_manager_->loadCameraInfo(camera_info_url))
  {
    RCLCPP_INFO(this->get_logger(), "Loaded camera calibration from %s", camera_info_url.c_str());
  }
  else
  {
    RCLCPP_WARN(this->get_logger(), "Failed to load camera calibration from %s, using default parameters. Ensure package '%s' and file '%s' exist.", camera_info_url.c_str(), package_name.c_str(), calibration_file.c_str());
  }

  // Create the CameraInfo publisher
  publisher_camera_info = this->create_publisher<sensor_msgs::msg::CameraInfo>("sensor/camera_info", 1);
  pub_camera_data_info = std::make_shared<sensor_msgs::msg::CameraInfo>();

  RCLCPP_INFO(this->get_logger(), "%s", colorize("B2 Camera Publisher Initialized Successfully!", "green").c_str());
}

B2Camera::~B2Camera()
{
  RCLCPP_INFO(this->get_logger(), "B2 Camera Publisher is shutting down");
  if (pipeline)
  {
    gst_element_set_state(pipeline, GST_STATE_NULL);
    gst_object_unref(pipeline);
    pipeline = nullptr; // Prevent double freeing
  }
}

void B2Camera::update_camera_image()
{
  auto now = this->get_clock()->now();

  // Pull sample directly from appsink (non-blocking with 0 timeout)
  GstSample *sample = gst_app_sink_try_pull_sample(GST_APP_SINK(appsink), 0);
  if (sample)
  {
    GstBuffer *buffer = gst_sample_get_buffer(sample);
    if (buffer)
    {
      GstMapInfo map;
      if (gst_buffer_map(buffer, &map, GST_MAP_READ))
      {
        if (map.data != nullptr && map.size >= (size_t)(picture_height * picture_width * 3))
        {
          cv::Mat frame(cv::Size(picture_width, picture_height), CV_8UC3, (char *)map.data);
          camera_state = frame.clone();
        }
        gst_buffer_unmap(buffer, &map);
      }
    }
    gst_sample_unref(sample);
  }

  // Publish image if we have data
  if (!camera_state.empty())
  {
    pub_camera_data_image->header.stamp = now;
    pub_camera_data_image->header.frame_id = robot_camera_link;
    pub_camera_data_image->height = picture_height;
    pub_camera_data_image->width = picture_width;
    pub_camera_data_image->encoding = picture_encoding;
    pub_camera_data_image->is_bigendian = false;
    pub_camera_data_image->step = picture_step;
    pub_camera_data_image->data.assign(camera_state.data, camera_state.data + camera_state.total() * camera_state.elemSize());
    publisher_camera->publish(*pub_camera_data_image);
  }
  else
  {
    RCLCPP_ERROR_THROTTLE(this->get_logger(), *this->get_clock(), 5000, "%s", colorize("No B2 Camera Data Received in update_camera_image. Check GStreamer pipeline status and incoming UDP stream.", "red").c_str());
  }

  // Publish camera info regardless of whether a new image was received
  *pub_camera_data_info = camera_info_manager_->getCameraInfo();
  pub_camera_data_info->header.stamp = now;
  pub_camera_data_info->header.frame_id = robot_camera_link;
  publisher_camera_info->publish(*pub_camera_data_info);
}

GstFlowReturn B2Camera::on_new_sample_from_sink(GstElement *sink, B2Camera *camera)
{
  GstSample *sample = gst_app_sink_pull_sample(GST_APP_SINK(sink));
  if (!sample)
  {
    RCLCPP_WARN(camera->get_logger(), "Camera Warning: gst_app_sink_pull_sample returned NULL. No new sample available or error occurred.");
    return GST_FLOW_OK; // Or GST_FLOW_ERROR depending on desired pipeline behavior
  }

  GstBuffer *buffer = gst_sample_get_buffer(sample);
  if (!buffer)
  {
    RCLCPP_ERROR(camera->get_logger(), "Camera Error: GstSample has no buffer.");
    gst_sample_unref(sample);
    return GST_FLOW_ERROR;
  }

  GstMapInfo map;
  if (!gst_buffer_map(buffer, &map, GST_MAP_READ))
  {
    RCLCPP_ERROR(camera->get_logger(), "Camera Error: Failed to map buffer.");
    gst_sample_unref(sample);
    return GST_FLOW_ERROR;
  }

  // Check if mapped data is valid and expected size (optional but good practice)
  if (map.data == nullptr || map.size < camera->picture_height * camera->picture_width * 3)
  {
    RCLCPP_ERROR(camera->get_logger(), "Camera Error: Mapped buffer has invalid data or size (size: %zu, expected >= %d)", map.size, camera->picture_height * camera->picture_width * 3);
    gst_buffer_unmap(buffer, &map);
    gst_sample_unref(sample);
    return GST_FLOW_ERROR;
  }

  cv::Mat frame(cv::Size(camera->picture_width, camera->picture_height), CV_8UC3, (char *)map.data);

  {
    std::lock_guard<std::mutex> lock(camera->image_mutex);
    camera->camera_state = frame.clone();
  }

  gst_buffer_unmap(buffer, &map);
  gst_sample_unref(sample);

  // Log successful sample reception and processing
  RCLCPP_DEBUG(camera->get_logger(), "Successfully processed new camera sample.");

  return GST_FLOW_OK;
}

std::string B2Camera::colorize(const std::string &text, const std::string &color) const
{
  std::string color_code;
  if (color == "orange")
  {
    color_code = "\033[38;5;214m";
  }
  else if (color == "blue")
  {
    color_code = "\033[34m";
  }
  else if (color == "green")
  {
    color_code = "\033[92m";
  }
  else if (color == "red")
  {
    color_code = "\033[31m";
  }
  else if (color == "purple")
  {
    color_code = "\033[35m";
  }
  else
  {
    color_code = "\033[0m"; // Reset color
  }
  return color_code + text + "\033[0m";
}

int main(int argc, char *argv[])
{
  rclcpp::init(argc, argv);
  rclcpp::spin(std::make_shared<B2Camera>());
  rclcpp::shutdown();
  return 0;
}
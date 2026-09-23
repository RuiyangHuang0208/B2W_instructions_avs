#include <cmath>
#include <unistd.h>
#include "utils/colors.h"

#include "rclcpp/rclcpp.hpp"
#include "b2_srvs/srv/b2_modes.hpp"
#include "geometry_msgs/msg/twist.hpp"
#include "geometry_msgs/msg/vector3.hpp"

#include "unitree_api/msg/request.hpp"
#include "unitree/robot/b2/sport/sport_client.hpp"
#include "unitree/robot/b2/motion_switcher/motion_switcher_client.hpp"

using std::placeholders::_1;

class B2HighLevelRequest : public rclcpp::Node
{
public:
    B2HighLevelRequest(std::shared_ptr<unitree::robot::b2::SportClient> sport_client,
                       std::shared_ptr<unitree::robot::b2::MotionSwitcherClient> switcher_client)
        : Node("B2_highroscontrol"), sport_client_(sport_client), switcher_client_(switcher_client)
    {
        // Initialization
        RCLCPP_INFO(get_logger(), BOLD(FGRN("Initializing B2 ROS Hardware Communication")));

        // Subscribers
        sub_b2_cmd_vel = this->create_subscription<geometry_msgs::msg::Twist>(
            "hardware/cmd_vel", 1, std::bind(&B2HighLevelRequest::callback_b2_cmd, this, _1));

        // Body pose subscriber (x=roll, y=pitch, z=height)
        sub_b2_body_pose = this->create_subscription<geometry_msgs::msg::Vector3>(
            "hardware/body_pose", 1, std::bind(&B2HighLevelRequest::callback_b2_body_pose, this, _1));

        // Service
        srv_b2_modes = this->create_service<b2_srvs::srv::B2Modes>(
            "hardware/modes", std::bind(&B2HighLevelRequest::callback_b2_modes, this, std::placeholders::_1, std::placeholders::_2));

        printAllModes();
        printMotionStatus();
        switchSportsMode();
    }

private:
    int printMotionStatus()
    {
        std::string robotForm, motionName;
        int motionStatus;
        switcher_client_->CheckMode(robotForm, motionName);
        RCLCPP_INFO(get_logger(), FORA("Current robotform: %s"), (robotForm == "0" ? "B2" : "B2-W"));
        if (motionName.empty())
        {
            RCLCPP_INFO(get_logger(), FORA("sport_mode or ai_sport is deactivated"));
            motionStatus = 0;
        }
        else
        {
            RCLCPP_INFO(get_logger(), FORA("%s"), (motionName == "normal" ? "sport_mode is active" : "ai_sport is active"));
            motionStatus = 1;
        }
        return motionStatus;
    }

    void switchWheelSportsMode()
    {
        RCLCPP_INFO(get_logger(), FORA("Switching to wheeled sport mode"));
        switcher_client_->SelectMode("wheeled_sport");
    }

    void switchSportsMode()
    {
        RCLCPP_INFO(get_logger(), FORA("Switching to Sports mode"));
        switcher_client_->SelectMode("sport_mode");
    }

    void switchReleaseMode()
    {
        switcher_client_->ReleaseMode();
    }
    void callback_b2_cmd(geometry_msgs::msg::Twist::SharedPtr msg)
    {

        float linear_x = 0.0;
        float linear_y = 0.0;
        float angular_z = 0.0;

        if (msg->linear.x && msg->linear.y && msg->angular.z)
        {
            linear_x = msg->linear.x;
            linear_y = msg->linear.y;
            angular_z = msg->angular.z;
        }
        else if (msg->linear.x && msg->linear.y)
        {
            linear_x = msg->linear.x;
            linear_y = msg->linear.y;
        }
        else if (msg->linear.x && msg->angular.z)
        {
            linear_x = msg->linear.x;
            angular_z = msg->angular.z;
        }
        else if (msg->linear.y && msg->angular.z)
        {
            linear_y = msg->linear.y;
            angular_z = msg->angular.z;
        }
        else if (msg->linear.x)
        {
            linear_x = msg->linear.x;
        }
        else if (msg->linear.y)
        {
            linear_y = msg->linear.y;
        }
        else if (msg->angular.z)
        {
            angular_z = msg->angular.z;
        }
        else
        {
            return;
        }

        int32_t ret = sport_client_->Move(linear_x, linear_y, angular_z);
        RCLCPP_INFO(get_logger(), "Request status: %d", ret);
    }

    void callback_b2_body_pose(geometry_msgs::msg::Vector3::SharedPtr msg)
    {
        // msg->x = roll (radians)
        // msg->y = pitch (radians)
        // msg->z = height (-0.1 to 0.1 meters relative to default)

        float roll = msg->x;
        float pitch = msg->y;
        float height = msg->z;

        // Clamp values to safe ranges
        roll = std::max(-0.5f, std::min(0.5f, roll));      // ~±28 degrees
        pitch = std::max(-0.5f, std::min(0.5f, pitch));    // ~±28 degrees
        height = std::max(-0.15f, std::min(0.1f, height)); // -15cm to +10cm

        // Only send commands if there's meaningful input (avoid spamming SDK)
        bool has_orientation = (std::abs(roll) > 0.01f || std::abs(pitch) > 0.01f);
        bool has_height = (std::abs(height) > 0.01f);

        // Apply body orientation (roll, pitch, yaw=0)
        if (has_orientation)
        {
            int32_t ret = sport_client_->Euler(roll, pitch, 0.0f);
            if (ret != 0)
            {
                RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 5000, "Euler request failed: %d", ret);
            }
        }

        // Apply body height
        if (has_height)
        {
            int32_t ret = sport_client_->BodyHeight(height);
            if (ret != 0)
            {
                RCLCPP_WARN_THROTTLE(get_logger(), *get_clock(), 5000, "BodyHeight request failed: %d", ret);
            }
        }
    }

    // Callback for Subscribers and Servicesuhni
    void callback_b2_modes(const std::shared_ptr<b2_srvs::srv::B2Modes::Request> request,
                           std::shared_ptr<b2_srvs::srv::B2Modes::Response> response)
    {
        try
        {
            RCLCPP_INFO(get_logger(), BOLD(FORA("Service request received: ")) FBLU("%s"), request->request_data.c_str());

            bool success = b2_mode_selection(request);

            response->success = success;

            if (success)
            {
                response->reason = "B2 mode set successfully";
            }
            else
            {
                response->reason = "Failed to set B2 mode";
            }
        }
        catch (const std::exception &e)
        {
            RCLCPP_ERROR(get_logger(), "Exception in callback_b2_modes: %s", e.what());
        }
    }

    bool b2_mode_selection(const std::shared_ptr<b2_srvs::srv::B2Modes::Request> request)
    {
        int res;
        if (request->request_data == "stand_up")
        {
            res = sport_client_->SwitchGait(0);
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            res = sport_client_->StandUp();
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            res = sport_client_->BalanceStand();
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "recovery_stand")
        {
            res = sport_client_->RecoveryStand();
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "stand_down")
        {
            res = sport_client_->StandDown();
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "gait_idle")
        {
            res = sport_client_->SwitchGait(0);
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "gait_trot")
        {
            res = sport_client_->SwitchGait(1);
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "gait_trot_running")
        {
            res = sport_client_->SwitchGait(2);
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "gait_visualwalk")
        {
            res = sport_client_->SwitchGait(3);
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "gait_flatwalk")
        {
            res = sport_client_->SwitchGait(4);
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "damp")
        {
            res = sport_client_->Damp();
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "recovery")
        {
            res = sport_client_->RecoveryStand();
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "speed_low")
        {
            res = sport_client_->SpeedLevel(-1);
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "speed_high")
        {
            res = sport_client_->SpeedLevel(1);
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "body_height_low")
        {
            res = sport_client_->BodyHeight(-0.1f);
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "body_height_mid")
        {
            res = sport_client_->BodyHeight(0.0f);
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "body_height_high")
        {
            res = sport_client_->BodyHeight(0.1f);
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "stop_move")
        {
            res = sport_client_->StopMove();
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return true;
        }
        else if (request->request_data == "print_modes")
        {
            printAllModes();
            return true;
        }
        else
        {
            RCLCPP_WARN(this->get_logger(), "Unknown mode received: %s", request->request_data.c_str());
            res = sport_client_->StopMove();
            RCLCPP_INFO(get_logger(), "Request status: %d", res);
            return false;
        }
    }

    void printAllModes()
    {
        RCLCPP_INFO(get_logger(), BOLD(FBLU("Available B2 Modes via ROS2 Services:")));

        std::vector<std::string> modes = {
            "damp",
            "stand_up",
            "stand_down",
            "stop_move",
            "gait_idle",
            "gait_trot",
            "gait_trot_running",
            "gait_visualwalk",
            "gait_flatwalk",
            "recovery",
            "speed_low",
            "speed_high",
            "body_height_low",
            "body_height_mid",
            "body_height_high",
        };

        for (const auto &mode : modes)
        {
            RCLCPP_INFO(get_logger(), FCYN("\t- %s"), mode.c_str());
        }
    }

    // Initialize Subscribers
    rclcpp::Subscription<geometry_msgs::msg::Twist>::SharedPtr sub_b2_cmd_vel;
    rclcpp::Subscription<geometry_msgs::msg::Vector3>::SharedPtr sub_b2_body_pose;

    // Initialize Service
    rclcpp::Service<b2_srvs::srv::B2Modes>::SharedPtr srv_b2_modes;

    // Unitree client
    std::shared_ptr<unitree::robot::b2::SportClient> sport_client_;
    std::shared_ptr<unitree::robot::b2::MotionSwitcherClient> switcher_client_;
};

int main(int argc, char *argv[])
{
    // Initialize Unitree Robot
    unitree::robot::ChannelFactory::Instance()->Init(0, "eno2");

    auto sport_client = std::make_shared<unitree::robot::b2::SportClient>();
    sport_client->SetTimeout(5.0f);
    sport_client->Init();

    // Initialize MotionSwitcherClient
    auto switcher_client = std::make_shared<unitree::robot::b2::MotionSwitcherClient>();
    switcher_client->Init();

    // Initialize ROS 2
    rclcpp::init(argc, argv);
    auto node = std::make_shared<B2HighLevelRequest>(sport_client, switcher_client);
    rclcpp::spin(node);
    RCLCPP_INFO(node->get_logger(), "\x1B[1m\x1B[31mTerminating B2 ROS Hardware Communication\x1B[0m");
    return 0;
}
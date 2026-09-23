#include <cmath>
#include <unistd.h>
#include "utils/colors.h"

#include "rclcpp/rclcpp.hpp"
#include "b2_srvs/srv/b2_modes.hpp"
#include "geometry_msgs/msg/twist.hpp"

#include "unitree_api/msg/request.hpp"
#include <unitree/robot/b2/sport/sport_client.hpp>

using std::placeholders::_1;

class B2HighLevelRequest : public rclcpp::Node
{
public:
    B2HighLevelRequest(std::shared_ptr<unitree::robot::b2::SportClient> sport_client)
        : Node("B2_highroscontrol"), sport_client_(sport_client)
    {
        // Initialization
        RCLCPP_INFO(get_logger(), BOLD(FGRN("Initializing B2 ROS Hardware Communication")));

        // Subscribers
        sub_b2_cmd_vel = this->create_subscription<geometry_msgs::msg::Twist>(
            "hardware/cmd_vel", 1, std::bind(&B2HighLevelRequest::callback_b2_cmd, this, _1));

        // Service
        srv_b2_modes = this->create_service<b2_srvs::srv::B2Modes>(
            "hardware/modes", std::bind(&B2HighLevelRequest::callback_b2_modes, this, std::placeholders::_1, std::placeholders::_2));

        printAllModes();
    }

private:
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

        // Limit to speed values
        if (linear_x > 0.6)
        {
            linear_x = 0.6;
        }
        else if (linear_x < -0.6)
        {
            linear_x = -0.6;
        }

        if (linear_y > 0.4)
        {
            linear_y = 0.4;
        }
        else if (linear_y < -0.4)
        {
            linear_y = -0.4;
        }

        if (angular_z > 0.8)
        {
            angular_z = 0.8;
        }
        else if (angular_z < -0.8)
        {
            angular_z = -0.8;
        }

        // Fixed: Using the class member client_ instead of sport_client
        sport_client_->Move(linear_x, linear_y, angular_z);
    }

    // Callback for Subscribers and Services
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

    // Initialize Service
    rclcpp::Service<b2_srvs::srv::B2Modes>::SharedPtr srv_b2_modes;

    // SPorts client
    std::shared_ptr<unitree::robot::b2::SportClient> sport_client_;
};

int main(int argc, char *argv[])
{
    // Initialize Unitree Robot
    unitree::robot::ChannelFactory::Instance()->Init(0, "eno2");

    auto sport_client_ = std::make_shared<unitree::robot::b2::SportClient>();
    sport_client_->SetTimeout(5.0f);
    sport_client_->Init();

    // Initialize ROS 2
    rclcpp::init(argc, argv);
    auto node = std::make_shared<B2HighLevelRequest>(sport_client_);
    rclcpp::spin(node);
    RCLCPP_INFO(node->get_logger(), "\x1B[1m\x1B[31mTerminating B2 ROS Hardware Communication\x1B[0m");
    return 0;
}
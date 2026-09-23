/*
 * Copyright 2025 IDRA, University of Trento
 * Author: Matteo Dalle Vedove (matteodv99tn@gmail.com)
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#ifndef UNITREE_Z1_HW_INTERFACE_HPP__
#define UNITREE_Z1_HW_INTERFACE_HPP__

#include <Eigen/Dense>

#include "hardware_interface/handle.hpp"
#include "hardware_interface/hardware_info.hpp"
#include "hardware_interface/system_interface.hpp"
#include "hardware_interface/types/hardware_interface_return_values.hpp"
#include "rclcpp/logger.hpp"
#include "rclcpp/macros.hpp"
#include "rclcpp_lifecycle/state.hpp"
#include "unitree_arm_sdk/control/unitreeArm.h"

namespace unitree::z1 {

class HardwareInterface : public hardware_interface::SystemInterface {
public:
    using Vec6   = Eigen::Vector<double, 6>;  // NOLINT: magic number
    using ArmPtr = std::unique_ptr<UNITREE_ARM::unitreeArm>;

    RCLCPP_SHARED_PTR_DEFINITIONS(HardwareInterface)

    HardwareInterface()           = default;
    ~HardwareInterface() override = default;

    HardwareInterface(const HardwareInterface&)             = delete;
    HardwareInterface(const HardwareInterface&&)            = delete;
    HardwareInterface& operator=(const HardwareInterface&)  = delete;
    HardwareInterface& operator=(const HardwareInterface&&) = delete;


    hardware_interface::CallbackReturn on_configure(
            const rclcpp_lifecycle::State& prev_state
    ) override;

    hardware_interface::CallbackReturn on_cleanup(
            const rclcpp_lifecycle::State& prev_state
    ) override;

    hardware_interface::CallbackReturn on_shutdown(
            const rclcpp_lifecycle::State& prev_state
    ) override;

    hardware_interface::CallbackReturn on_activate(
            const rclcpp_lifecycle::State& prev_state
    ) override;

    hardware_interface::CallbackReturn on_deactivate(
            const rclcpp_lifecycle::State& prev_state
    ) override;

    hardware_interface::CallbackReturn on_error(
            const rclcpp_lifecycle::State& prev_state
    ) override;

    std::vector<hardware_interface::StateInterface> export_state_interfaces() override;

    std::vector<hardware_interface::CommandInterface>

    export_command_interfaces() override;

    hardware_interface::return_type read(
            const rclcpp::Time& time, const rclcpp::Duration& period
    ) override;

    hardware_interface::return_type write(
            const rclcpp::Time& time, const rclcpp::Duration& period
    ) override;

    hardware_interface::return_type perform_command_mode_switch(
            const std::vector<std::string>& start_interfaces,
            const std::vector<std::string>& stop_interfaces
    ) override;

    // clang-format off
    [[nodiscard]] std::vector<hardware_interface::ComponentInfo>& joints() { return info_.joints; }
    [[nodiscard]] const std::vector<hardware_interface::ComponentInfo>& joints() const { return info_.joints; }

    [[nodiscard]] rclcpp::Logger& get_logger() { return _logger; }
    
    [[nodiscard]] bool with_gripper() const;
    // clang-format on


private:
    rclcpp::Logger _logger = rclcpp::get_logger("z1_hardware_interface");

    ArmPtr _arm = nullptr;

    Vec6   _arm_max_torque     = 20.0 * Vec6::Ones();
    double _gripper_max_torque = 20.0;

    struct GainsData {
        // Gripper (index 6) gains are forced to ZERO because Motor 7 has a HARDWARE
        // FAULT: it trips "windings overheat" the instant it is energized with any
        // real gain -- even commanded to a safe mid-range position and held
        // perfectly still (NOT at a hard stop). Verified 2026-06-29: restoring the
        // upstream gains (kp=20,kd=2000) produced 18000+ "Motor 7 windings overheat"
        // errors in seconds, which cascade onto the shared wrist CAN bus and drop
        // motors 5/6/7 -> PASSIVE reverts -> whole-arm shaking. With kp=kd=0 the
        // gripper draws no torque, never overheats, and the 6 arm axes are rock
        // solid. The gripper is unusable until the motor is serviced/replaced;
        // do NOT re-enable these gains without new gripper hardware.
        std::vector<double> kp = {20.0, 30.0, 30.0, 20.0, 15.0, 10.0, 0.0};
        std::vector<double> kd = {2000, 2000, 2000, 2000, 2000, 2000, 0.0};
    };

    GainsData _default_gains;
    GainsData _current_gains;

    struct {
        Vec6 q   = Vec6::Zero();
        Vec6 qd  = Vec6::Zero();
        Vec6 tau = Vec6::Zero();
    } _arm_state;

    struct {
        double q   = 0;
        double qd  = 0;
        double tau = 0;
    } _gripper_state;

    struct {
        Vec6 q   = Vec6::Zero();
        Vec6 qd  = Vec6::Zero();
        Vec6 tau = Vec6::Zero();
    } _arm_cmd;

    struct {
        double q   = 0;
        double qd  = 0;
        double tau = 0;
    } _gripper_cmd;

    void saturate_torque();

    long get_joint_id(const std::string& joint_name) const;

    // Track the last FSM state reported by z1_ctrl so we can log transitions
    // and detect an unexpected revert to PASSIVE from read().
    int _last_fsm_state = -1;

    // LOWCMD watchdog recovery. z1_ctrl forces PASSIVE if it misses UDP packets
    // for ~100 ms, which happens while the controller_manager stalls the
    // (non-RT) update loop during controller spawning. The FSM transition back
    // to LOWCMD is edge-triggered, so streaming commands does not recover it;
    // we must explicitly re-issue setFsm(LOWCMD). These track when to do so.
    bool          _lowcmd_requested  = false;  // set once on_configure asks for LOWCMD
    unsigned long _read_count        = 0;      // read() cycles since activation
    unsigned long _last_recover_read = 0;      // _read_count at last recovery attempt
};


}  // namespace unitree::z1

#endif  // UNITREE_Z1_HW_INTERFACE_HPP__

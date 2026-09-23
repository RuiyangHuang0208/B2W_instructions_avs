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
#include "z1_hardware_interface/z1_hardware_interface.hpp"

#include <algorithm>
#include <ctime>
#include <fmt/format.h>
#include <memory>
#include <stdexcept>
#include <unitree_arm_sdk/control/unitreeArm.h>
#include <unitree_arm_sdk/message/arm_common.h>

#include <rclcpp/duration.hpp>

#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include "rclcpp/logging.hpp"

//  ____            _                 _   _
// |  _ \  ___  ___| | __ _ _ __ __ _| |_(_) ___  _ __  ___
// | | | |/ _ \/ __| |/ _` | '__/ _` | __| |/ _ \| '_ \/ __|
// | |_| |  __/ (__| | (_| | | | (_| | |_| | (_) | | | \__ \
// |____/ \___|\___|_|\__,_|_|  \__,_|\__|_|\___/|_| |_|___/
//

using unitree::z1::HardwareInterface;

static void to_lower_string(std::string& str);

template <typename Iterable>
static std::string
pretty_vector(const Iterable& vec) {
    return fmt::format("({})", fmt::join(vec, ", "));
}

static std::pair<std::string, std::string> split_interface(const std::string&);

//  ____   ____ _     ____ ____  ____    _     _  __       ____           _
// |  _ \ / ___| |   / ___|  _ \|  _ \  | |   (_)/ _| ___ / ___|   _  ___| | ___
// | |_) | |   | |  | |   | |_) | |_) | | |   | | |_ / _ \ |  | | | |/ __| |/ _ \
// |  _ <| |___| |__| |___|  __/|  __/  | |___| |  _|  __/ |__| |_| | (__| |  __/
// |_| \_\\____|_____\____|_|   |_|     |_____|_|_|  \___|\____\__, |\___|_|\___|
//                                                             |___/
hardware_interface::CallbackReturn
HardwareInterface::on_configure(const rclcpp_lifecycle::State& prev_state) {
    RCLCPP_DEBUG(get_logger(), "calling on_configure()");
    if (hardware_interface::SystemInterface::on_configure(prev_state)
        != hardware_interface::CallbackReturn::SUCCESS) {
        RCLCPP_ERROR(get_logger(), "parent on_configure() failed");
        return hardware_interface::CallbackReturn::ERROR;
    }

#ifdef SHOW_DEBUG_MESSAGES
    rclcpp::Logger logger = get_logger();
    logger.set_level(rclcpp::Logger::Level::Debug);
#endif

    if (with_gripper()) RCLCPP_INFO(get_logger(), "Gripper is enabled");
    else RCLCPP_INFO(get_logger(), "Gripper is disabled");

    // TODO: load torque limits from URDF
    RCLCPP_INFO(
            get_logger(),
            "Joint torque limits: %s",
            pretty_vector(_arm_max_torque).c_str()
    );
    RCLCPP_INFO(get_logger(), "Gripper torque limit: %lf", _gripper_max_torque);

    RCLCPP_INFO(get_logger(), "Establishing connection to the ARM through SDK");
    _arm = std::make_unique<UNITREE_ARM::unitreeArm>(with_gripper());
    RCLCPP_INFO(get_logger(), "Connection established!");
    _arm->sendRecvThread->start();
    _arm->setFsm(UNITREE_ARM::ArmFSMState::PASSIVE);
    read(rclcpp::Time(0), rclcpp::Duration(0, 0));

    // clang-format off
    RCLCPP_INFO(get_logger(), "Current joints configuration: %s", pretty_vector(_arm_state.q).c_str());
    RCLCPP_INFO(get_logger(), "Current joints velocity: %s", pretty_vector(_arm_state.qd).c_str());
    RCLCPP_INFO(get_logger(), "Measured joint torque: %s", pretty_vector(_arm_state.tau).c_str());
    RCLCPP_INFO(get_logger(), "Position-proportional gains: %s", pretty_vector(_default_gains.kp).c_str());
    RCLCPP_INFO(get_logger(), "Velocity-proportional gains: %s", pretty_vector(_default_gains.kd).c_str());
    // clang-format on

    // Set command to current state
    _arm_cmd.q      = _arm_state.q;
    // Command ZERO velocity for a position hold. The position controller never
    // writes the velocity command interface, so whatever we set here stays
    // frozen. Capturing the measured velocity (which may be nonzero at startup)
    // would, with the large kd, produce a constant torque bias (kd*qd_des) that
    // saturates the motor and trips its overcurrent "overheat" protection.
    // With qd_des=0, kd acts as pure damping (zero torque when the joint holds).
    _arm_cmd.qd     = Vec6::Zero();
    _gripper_cmd.q  = _gripper_state.q;
    _gripper_cmd.qd = 0.0;  // zero velocity command (see _arm_cmd.qd note)
    // Stage gains AND commands for BOTH the arm and the gripper BEFORE entering
    // LOWCMD, so z1_ctrl streams OUR values from the very first low-level packet.
    // The gripper matters most: perform_command_mode_switch() (which sets the
    // gripper gain to 0) and write() (which sends the gripper hold command) do
    // NOT run until the controller_manager activates the position_controller --
    // ~4.7 s after this switch. Without staging the gripper here, for those few
    // seconds z1_ctrl streams the SDK's DEFAULT gripper gain toward its DEFAULT
    // target (q=0 == fully OPEN), which actively drives the gripper open on every
    // launch even though our configured gripper gain is 0. (The arm doesn't drift
    // because its command is seeded to the measured position.) Setting the
    // gripper gain to 0 and holding it at the measured position here closes that
    // window.
    _arm->lowcmd->setControlGain(_default_gains.kp, _default_gains.kd);
    _arm->lowcmd->setGripperGain(_default_gains.kp[6], _default_gains.kd[6]);
    _arm->setArmCmd(_arm_state.q, Vec6::Zero());        // hold current arm pos
    _arm->setGripperCmd(_gripper_state.q, 0.0, 0.0);    // hold current gripper pos, zero torque
    _arm->setFsm(UNITREE_ARM::ArmFSMState::LOWCMD);
    RCLCPP_INFO(get_logger(), "SDK switch to low-level control!");

    // IMPORTANT: keep the background sendRecvThread running. It pumps UDP
    // packets to z1_ctrl at a steady 500 Hz INDEPENDENTLY of the
    // controller_manager update loop. The ros2_control read()/write() callbacks
    // therefore must NOT call sendRecv() themselves -- they only copy the latest
    // state and stage the next command, which the thread transmits. This
    // decouples the arm link from the (non-RT, stall-prone) control loop: if the
    // update loop hiccups, the thread still feeds z1_ctrl, so z1_ctrl never
    // starves and drops the arm ("Lose connection with z1_arm" -> PASSIVE).
    RCLCPP_INFO(get_logger(), "SDK sendRecv thread streaming to z1_ctrl at 500 Hz");

    // From now on read() will keep the arm in LOWCMD, re-requesting it if
    // z1_ctrl's watchdog ever drops us back to PASSIVE.
    _lowcmd_requested = true;

    RCLCPP_DEBUG(get_logger(), "on_configure() completed successfully");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn
HardwareInterface::on_cleanup(const rclcpp_lifecycle::State& prev_state) {
    RCLCPP_DEBUG(get_logger(), "calling on_cleanup()");
    if (hardware_interface::SystemInterface::on_cleanup(prev_state)
        != hardware_interface::CallbackReturn::SUCCESS) {
        RCLCPP_ERROR(get_logger(), "parent on_cleanup() failed");
        return hardware_interface::CallbackReturn::ERROR;
    }
    // TODO
    RCLCPP_DEBUG(get_logger(), "on_cleanup() completed successfully");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn
HardwareInterface::on_shutdown(const rclcpp_lifecycle::State& prev_state) {
    RCLCPP_DEBUG(get_logger(), "calling on_shutdown()");
    if (hardware_interface::SystemInterface::on_shutdown(prev_state)
        != hardware_interface::CallbackReturn::SUCCESS) {
        RCLCPP_ERROR(get_logger(), "parent on_shutdown() failed");
    }
    RCLCPP_INFO(get_logger(), "Going back to start");
    _arm->backToStart();
    RCLCPP_INFO(get_logger(), "Setting arm into passive state");
    _arm->setFsm(UNITREE_ARM::ArmFSMState::PASSIVE);
    RCLCPP_INFO(get_logger(), "Closing SDK connection");
    _arm->sendRecvThread->shutdown();
    RCLCPP_DEBUG(get_logger(), "on_shutdown() completed successfully");
    return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn
HardwareInterface::on_activate(const rclcpp_lifecycle::State& prev_state) {
    RCLCPP_DEBUG(get_logger(), "calling on_activate()");
    if (hardware_interface::SystemInterface::on_activate(prev_state)
        != hardware_interface::CallbackReturn::SUCCESS) {
        RCLCPP_ERROR(get_logger(), "parent on_shutdown() failed");
    }
    // TODO
    RCLCPP_DEBUG(get_logger(), "on_activate() completed successfully");
    return hardware_interface::CallbackReturn::SUCCESS;
}

/**
 * This function should deactivate the hardware.
 */
hardware_interface::CallbackReturn
HardwareInterface::on_deactivate(const rclcpp_lifecycle::State& prev_state) {
    RCLCPP_DEBUG(get_logger(), "calling on_deactivate()");
    if (hardware_interface::SystemInterface::on_deactivate(prev_state)
        != hardware_interface::CallbackReturn::SUCCESS) {
        RCLCPP_ERROR(get_logger(), "parent on_deactivate() failed");
        return hardware_interface::CallbackReturn::ERROR;
    }
    // TODO
    RCLCPP_DEBUG(get_logger(), "on_deactivate() completed successfully");
    return hardware_interface::CallbackReturn::SUCCESS;
}

/**
 * This function should handle errors.
 */
hardware_interface::CallbackReturn
HardwareInterface::on_error(const rclcpp_lifecycle::State& prev_state) {
    RCLCPP_DEBUG(get_logger(), "called on_error()");
    if (hardware_interface::SystemInterface::on_error(prev_state)
        != hardware_interface::CallbackReturn::SUCCESS) {
        RCLCPP_ERROR(get_logger(), "parent on_error() failed");
        return hardware_interface::CallbackReturn::ERROR;
    }
    // TODO
    RCLCPP_DEBUG(get_logger(), "on_error() processed correctly");
    return hardware_interface::CallbackReturn::SUCCESS;
}

//  _   ___        __  ___       _             __
// | | | \ \      / / |_ _|_ __ | |_ ___ _ __ / _| __ _  ___ ___
// | |_| |\ \ /\ / /   | || '_ \| __/ _ \ '__| |_ / _` |/ __/ _ \
// |  _  | \ V  V /    | || | | | ||  __/ |  |  _| (_| | (_|  __/
// |_| |_|  \_/\_/    |___|_| |_|\__\___|_|  |_|  \__,_|\___\___|
//

std::vector<hardware_interface::StateInterface>
HardwareInterface::export_state_interfaces() {
    using hardware_interface::HW_IF_EFFORT;
    using hardware_interface::HW_IF_POSITION;
    using hardware_interface::HW_IF_VELOCITY;

    std::vector<hardware_interface::StateInterface> state_interfaces;
    state_interfaces.reserve(21);  // NOLINT: 7 joints * 3 states
    for (long i = 0; i < 6; ++i) {
        const std::string jnt_name = joints()[i].name;
        state_interfaces.emplace_back(jnt_name, HW_IF_POSITION, &_arm_state.q(i));
        state_interfaces.emplace_back(jnt_name, HW_IF_VELOCITY, &_arm_state.qd(i));
        state_interfaces.emplace_back(jnt_name, HW_IF_EFFORT, &_arm_state.tau(i));
    }
    if (with_gripper()) {
        const std::string jnt_name = joints()[6].name;
        state_interfaces.emplace_back(jnt_name, HW_IF_POSITION, &_gripper_state.q);
        state_interfaces.emplace_back(jnt_name, HW_IF_VELOCITY, &_gripper_state.qd);
        state_interfaces.emplace_back(jnt_name, HW_IF_EFFORT, &_gripper_state.tau);
    }
    return state_interfaces;
};

std::vector<hardware_interface::CommandInterface>
HardwareInterface::export_command_interfaces() {
    using hardware_interface::HW_IF_EFFORT;
    using hardware_interface::HW_IF_POSITION;
    using hardware_interface::HW_IF_VELOCITY;

    std::vector<hardware_interface::CommandInterface> cmd_interfaces;
    cmd_interfaces.reserve(21);  // NOLINT: 7 joints * 3 cmd interfaces
    for (long i = 0; i < 6; ++i) {
        const std::string jnt_name = joints()[i].name;
        cmd_interfaces.emplace_back(jnt_name, HW_IF_POSITION, &_arm_cmd.q(i));
        cmd_interfaces.emplace_back(jnt_name, HW_IF_VELOCITY, &_arm_cmd.qd(i));
        cmd_interfaces.emplace_back(jnt_name, HW_IF_EFFORT, &_arm_cmd.tau(i));
    }
    if (with_gripper()) {
        const std::string jnt_name = joints()[6].name;
        cmd_interfaces.emplace_back(jnt_name, HW_IF_POSITION, &_gripper_cmd.q);
        cmd_interfaces.emplace_back(jnt_name, HW_IF_VELOCITY, &_gripper_cmd.qd);
        cmd_interfaces.emplace_back(jnt_name, HW_IF_EFFORT, &_gripper_cmd.tau);
    }
    return cmd_interfaces;
}

hardware_interface::return_type
HardwareInterface::
        read(const rclcpp::Time& /* time */, const rclcpp::Duration& /* period */) {
    // NOTE: do NOT call _arm->sendRecv() here -- the background sendRecvThread
    // owns all UDP I/O with z1_ctrl. We just consume the latest state it cached.

    // Log whenever z1_ctrl's reported FSM state changes.
    const int fsm_now    = static_cast<int>(_arm->_ctrlComp->recvState.state);
    const int fsm_lowcmd = static_cast<int>(UNITREE_ARM::ArmFSMState::LOWCMD);
    const int fsm_passive = static_cast<int>(UNITREE_ARM::ArmFSMState::PASSIVE);
    if (fsm_now != _last_fsm_state) {
        RCLCPP_WARN(
                get_logger(),
                "z1_ctrl FSM state changed: %d -> %d (LOWCMD=%d, PASSIVE=%d)",
                _last_fsm_state,
                fsm_now,
                fsm_lowcmd,
                fsm_passive
        );
        _last_fsm_state = fsm_now;
    }

    // Recover from a watchdog-induced revert to PASSIVE. Wait out the initial
    // startup churn (controllers spawning), then re-request LOWCMD at most once
    // per second so a single attempt sticks once things settle. The background
    // sendRecvThread is already running, so setFsm() can do its handshake
    // directly (no bracketing needed).
    ++_read_count;
    if (_lowcmd_requested && fsm_now == fsm_passive && _read_count > 1000
        && (_read_count - _last_recover_read) > 250) {
        _last_recover_read = _read_count;
        RCLCPP_WARN(get_logger(), "z1 reverted to PASSIVE; re-requesting LOWCMD");
        // Re-stage gains + a hold command before re-entering LOWCMD, for the same
        // reason as on_configure(): a PASSIVE revert can drop the SDK's gripper
        // gain and target back to defaults, so re-entering LOWCMD without
        // re-staging would let z1_ctrl drive the gripper toward its default OPEN
        // target (this is why the gripper also opened during earlier overheat /
        // fault episodes). Hold both arm and gripper at the last measured position
        // with gripper gain 0. (_current_gains is populated by now: recovery only
        // fires after _read_count > 1000, i.e. well after the controller activated.)
        _arm->lowcmd->setControlGain(_current_gains.kp, _current_gains.kd);
        _arm->lowcmd->setGripperGain(_current_gains.kp[6], _current_gains.kd[6]);
        _arm->setArmCmd(_arm_state.q, Vec6::Zero());
        _arm->setGripperCmd(_gripper_state.q, 0.0, 0.0);
        _arm->setFsm(UNITREE_ARM::ArmFSMState::LOWCMD);
    }

    for (long i = 0; i < 6; ++i) {
        _arm_state.q(i)   = _arm->lowstate->q[i];
        _arm_state.qd(i)  = _arm->lowstate->dq[i];
        _arm_state.tau(i) = _arm->lowstate->tau[i];
    }
    if (with_gripper()) {
        _gripper_state.q   = _arm->lowstate->q[6];
        _gripper_state.qd  = _arm->lowstate->dq[6];
        _gripper_state.tau = _arm->lowstate->tau[6];
    }
    return hardware_interface::return_type::OK;
}

hardware_interface::return_type
HardwareInterface::
        write(const rclcpp::Time& /* time */, const rclcpp::Duration& /* period */) {
    saturate_torque();
    // Diagnostics: log commanded q roughly once per second (1000 Hz loop).
    static unsigned long _write_count = 0;
    if ((_write_count++ % 1000) == 0) {
        RCLCPP_INFO(
                get_logger(),
                "write() cmd q=(%.3f %.3f %.3f %.3f %.3f %.3f) grip=%.3f",
                _arm_cmd.q(0), _arm_cmd.q(1), _arm_cmd.q(2),
                _arm_cmd.q(3), _arm_cmd.q(4), _arm_cmd.q(5), _gripper_cmd.q
        );
    }
    // Stage the command; the background sendRecvThread transmits it to z1_ctrl.
    // Do NOT call _arm->sendRecv() here (the thread owns UDP I/O).
    _arm->setArmCmd(_arm_cmd.q, _arm_cmd.qd, _arm_cmd.tau);
    _arm->setGripperCmd(_gripper_cmd.q, _gripper_cmd.qd, _gripper_cmd.tau);
    return hardware_interface::return_type::OK;
}

hardware_interface::return_type
HardwareInterface::perform_command_mode_switch(
        const std::vector<std::string>& start_interfaces,
        const std::vector<std::string>& /* stop_interfaces */
) {
    using hardware_interface::HW_IF_EFFORT;
    using hardware_interface::HW_IF_POSITION;
    using hardware_interface::HW_IF_VELOCITY;

    RCLCPP_INFO(get_logger(), "Switching control mode");
    for (const std::string& interface : start_interfaces) {
        const auto [name, type] = split_interface(interface);
        auto idx                = get_joint_id(name);

        if (type == HW_IF_POSITION) {
            _current_gains.kp[idx] = _default_gains.kp[idx];
            _current_gains.kd[idx] = _default_gains.kd[idx];
        } else if (type == HW_IF_VELOCITY) {
            _current_gains.kp[idx] = 0.0;
            _current_gains.kd[idx] = _default_gains.kd[idx];
        } else if (type == HW_IF_EFFORT) {
            _current_gains.kp[idx] = 0.0;
            _current_gains.kd[idx] = 0.0;
        } else {
            RCLCPP_ERROR(
                    get_logger(),
                    "Don't know how to configure interface '%s'",
                    interface.c_str()
            );
            return hardware_interface::return_type::ERROR;
        }
    }

    // clang-format off
    RCLCPP_INFO(get_logger(), "Updated proportional gains: %s", pretty_vector(_current_gains.kp).c_str());
    RCLCPP_INFO(get_logger(), "Updated derivative gains: %s", pretty_vector(_current_gains.kd).c_str());
    // clang-format on

    _arm->lowcmd->setControlGain(_current_gains.kp, _current_gains.kd);
    _arm->lowcmd->setGripperGain(_current_gains.kp[6], _current_gains.kd[6]);

    // Set command to current state
    _arm_cmd.q      = _arm_state.q;
    // Command ZERO velocity for a position hold. The position controller never
    // writes the velocity command interface, so whatever we set here stays
    // frozen. Capturing the measured velocity (which may be nonzero at startup)
    // would, with the large kd, produce a constant torque bias (kd*qd_des) that
    // saturates the motor and trips its overcurrent "overheat" protection.
    // With qd_des=0, kd acts as pure damping (zero torque when the joint holds).
    _arm_cmd.qd     = Vec6::Zero();
    _gripper_cmd.q  = _gripper_state.q;
    _gripper_cmd.qd = 0.0;  // zero velocity command (see _arm_cmd.qd note)

    return hardware_interface::return_type::OK;
}

//  ____       _            _
// |  _ \ _ __(_)_   ____ _| |_ ___
// | |_) | '__| \ \ / / _` | __/ _ \
// |  __/| |  | |\ V / (_| | ||  __/
// |_|   |_|  |_| \_/ \__,_|\__\___|
//

void
HardwareInterface::saturate_torque() {
    const Vec6 original_tau = _arm_cmd.tau;
    _arm_cmd.tau = original_tau.cwiseMin(_arm_max_torque).cwiseMax(-_arm_max_torque);
    _gripper_cmd.tau =
            std::clamp(_gripper_cmd.tau, -_gripper_max_torque, _gripper_max_torque);

    if (original_tau != _arm_cmd.tau)
        RCLCPP_WARN(get_logger(), "Saturating input torque");
}

bool
HardwareInterface::with_gripper() const {
    std::string gripper_param = info_.hardware_parameters.at("gripper");
    to_lower_string(gripper_param);
    return gripper_param == "true";
}

long
HardwareInterface::get_joint_id(const std::string& joint_name) const {
    for (long i = 0; i < joints().size(); ++i) {
        if (joints()[i].name == joint_name) return i;
    }
    throw std::out_of_range(
            fmt::format("Unable to find joint '{}' with the joints of the robot")
    );
}

//  ____  _        _   _
// / ___|| |_ __ _| |_(_) ___ ___
// \___ \| __/ _` | __| |/ __/ __|
//  ___) | || (_| | |_| | (__\__ \
// |____/ \__\__,_|\__|_|\___|___/
//

/**
 * @bried Convert in-place a string to lower case.
 *
 * @param[in,out] str       The string to be converted.
 */
static void
to_lower_string(std::string& str) {
    std::transform(str.begin(), str.end(), str.begin(), [](unsigned char c) {
        return std::tolower(c);
    });
}

static std::pair<std::string, std::string>
split_interface(const std::string& in) {
    const auto sep_id = in.find('/');
    return std::make_pair(
            in.substr(0, sep_id), in.substr(sep_id + 1, in.size() - sep_id - 1)
    );
}

//  _____                       _
// | ____|_  ___ __   ___  _ __| |_
// |  _| \ \/ / '_ \ / _ \| '__| __|
// | |___ >  <| |_) | (_) | |  | |_
// |_____/_/\_\ .__/ \___/|_|   \__|
//            |_|
#include <pluginlib/class_list_macros.hpp>

PLUGINLIB_EXPORT_CLASS(
        unitree::z1::HardwareInterface, hardware_interface::SystemInterface
);

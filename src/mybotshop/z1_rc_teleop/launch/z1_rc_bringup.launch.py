#!/usr/bin/env python3
"""
Combined launch file: Z1 controller + RC teleop (single command).

Usage:
    ros2 launch z1_rc_teleop z1_rc_bringup.launch.py
"""

import os
import subprocess
import xacro
from launch import LaunchDescription
from launch.actions import ExecuteProcess, RegisterEventHandler, SetEnvironmentVariable
from launch.event_handlers.on_process_exit import OnProcessExit
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory, get_package_prefix
from ament_index_python.packages import get_package_share_path


# Service that also drives the same SBUS RC receiver on the B2 quadruped. If it is
# running it grabs /dev/arduino_sbus and corrupts our frames (stuttery teleop).
_SBUS_CONTENDER_SERVICE = 'b2-rc-teleop.service'


def _run(cmd):
    """Run a command, never raise; return (returncode, stdout, stderr) stripped."""
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        return r.returncode, (r.stdout or '').strip(), (r.stderr or '').strip()
    except Exception as exc:  # noqa: BLE001 - preflight must never crash on tool errors
        return 127, '', str(exc)


def _abort(reason, fix):
    bar = '=' * 70
    print('\n' + bar
          + '\n  Z1 RC TELEOP PRE-FLIGHT CHECK FAILED'
          + '\n' + bar
          + '\n  ' + reason
          + '\n\n  ' + fix
          + '\n' + bar + '\n', flush=True)
    raise RuntimeError('SBUS pre-flight failed: ' + reason)


def _preflight_sbus(serial_port):
    """Verify the SBUS RC receiver is free before bringing up the Z1 stack.

    Runs automatically on every launch so a re-enabled B2 service (or any stray
    port holder) is caught BEFORE z1_ctrl starts -- not discovered as mid-teleop
    stutter. Aborts the launch with actionable instructions if the port is busy.
    """
    dev = os.path.realpath(serial_port)
    print('[z1_rc preflight] checking SBUS port {} is free...'.format(serial_port),
          flush=True)

    # 1) Is the known contender (B2 RC teleop) running right now?
    _, active, _ = _run(['systemctl', 'is-active', _SBUS_CONTENDER_SERVICE])
    if active == 'active':
        print('[z1_rc preflight] {} is ACTIVE; attempting to stop it...'.format(
            _SBUS_CONTENDER_SERVICE), flush=True)
        _run(['sudo', '-n', 'systemctl', 'stop', _SBUS_CONTENDER_SERVICE])
        _, active, _ = _run(['systemctl', 'is-active', _SBUS_CONTENDER_SERVICE])
        if active == 'active':
            _abort(
                '{} is RUNNING and holding {}.'.format(_SBUS_CONTENDER_SERVICE, serial_port),
                'Stop it, then relaunch:\n'
                '      sudo systemctl stop {svc}\n'
                '  And keep it from returning on boot:\n'
                '      sudo systemctl disable {svc}'.format(svc=_SBUS_CONTENDER_SERVICE))
        print('[z1_rc preflight] stopped {}.'.format(_SBUS_CONTENDER_SERVICE), flush=True)

    # 2) Did it get re-enabled (e.g. by a vendor provisioning script)? Warn, don't abort.
    _, enabled, _ = _run(['systemctl', 'is-enabled', _SBUS_CONTENDER_SERVICE])
    if enabled == 'enabled':
        print('\n' + '!' * 70
              + '\n[z1_rc preflight] WARNING: {} is ENABLED -- it will auto-start on the'
              '\n  next B2 boot and fight the Z1 arm for the SBUS port. To stop that:'
              '\n      sudo systemctl disable {svc}'.format(
                  _SBUS_CONTENDER_SERVICE, svc=_SBUS_CONTENDER_SERVICE)
              + '\n' + '!' * 70 + '\n', flush=True)

    # 3) Is anything else already holding the device? (best-effort: as a non-root user
    #    fuser may not see root-owned holders, but the service check above covers the
    #    known contender; this catches stray user-owned processes.)
    _, holders, _ = _run(['fuser', dev])
    if holders.split():
        _abort(
            '{} ({}) is already open by PID(s): {}.'.format(serial_port, dev, holders),
            'Another process is using the SBUS receiver. Identify and stop it:\n'
            '      sudo fuser -v {}'.format(dev))

    print('[z1_rc preflight] OK -- {} ({}) is free.'.format(serial_port, dev), flush=True)


def _serial_port_from_config(teleop_config):
    """Read serial_port from the teleop YAML; fall back to the known default."""
    default = '/dev/arduino_sbus'
    try:
        import yaml
        with open(teleop_config) as fh:
            cfg = yaml.safe_load(fh) or {}
        for node_cfg in cfg.values():
            params = (node_cfg or {}).get('ros__parameters', {}) or {}
            if 'serial_port' in params:
                return params['serial_port']
    except Exception:  # noqa: BLE001 - never let config parsing break the launch
        pass
    return default


def generate_launch_description():
    # Package paths
    z1_bringup_share = get_package_share_directory('z1_bringup')
    z1_description_share = get_package_share_directory('z1_description')
    z1_rc_teleop_share = get_package_share_directory('z1_rc_teleop')

    # Config files
    xacro_file = os.path.join(z1_description_share, 'urdf', 'z1.urdf.xacro')
    controller_config = os.path.join(z1_bringup_share, 'config', 'z1_controllers.yaml')
    teleop_config = os.path.join(z1_rc_teleop_share, 'config', 'sbus_teleop.yaml')

    # Pre-flight: make sure the SBUS RC receiver is free (no B2 service / stray holder)
    # BEFORE we start z1_ctrl. Aborts the launch with instructions if it is contended.
    _preflight_sbus(_serial_port_from_config(teleop_config))

    # Process URDF
    robot_description_content = xacro.process(
        xacro_file,
        mappings={
            'name': 'z1',
            'prefix': '',
            'with_gripper': 'true',
            'controllers': controller_config,
            'sim_ignition': 'false',
        }
    )
    robot_description = {'robot_description': robot_description_content}

    # Ignition resource path (needed by xacro even if not simulating)
    ign_env_var = 'IGN_GAZEBO_RESOURCE_PATH'
    z1_desc_prefix = os.path.join(get_package_prefix('z1_description'), 'share')
    ign_path = z1_desc_prefix
    if ign_env_var in os.environ:
        ign_path = os.environ[ign_env_var] + ':' + z1_desc_prefix

    # --- z1_ctrl SDK bridge process ---
    z1_ctrl_work_dir = os.path.join(
        str(get_package_share_path('z1_hardware_interface')), 'controller'
    )
    z1_ctrl_process = ExecuteProcess(
        cmd=['./z1_ctrl'],
        cwd=z1_ctrl_work_dir,
        output='screen',
    )

    # --- Nodes ---

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='both',
        parameters=[robot_description, {'use_sim_time': False}],
    )

    controller_manager = Node(
        package='controller_manager',
        executable='ros2_control_node',
        parameters=[robot_description, controller_config, {'use_sim_time': False}],
        remappings=[
            ('motion_control_handle/target_frame', 'target_frame'),
            ('cartesian_motion_controller/target_frame', 'target_frame'),
        ],
    )

    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster', '-c', '/controller_manager'],
        parameters=[{'use_sim_time': False, 'set_state': 'active'}],
    )

    position_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['position_controller', '-c', '/controller_manager'],
        parameters=[{'use_sim_time': False, 'set_state': 'active'}],
    )

    # RC teleop namespace
    namespace = os.environ.get('Z1_NS', 'z1')

    teleop_node = Node(
        package='z1_rc_teleop',
        executable='sbus_teleop_node',
        name='z1_sbus_teleop_node',
        namespace=namespace,
        output='screen',
        parameters=[teleop_config],
    )

    # Launch teleop after position controller is ready
    teleop_delayed = RegisterEventHandler(
        event_handler=OnProcessExit(
            target_action=position_controller_spawner,
            on_exit=[teleop_node],
        )
    )

    return LaunchDescription([
        SetEnvironmentVariable('ROS_DOMAIN_ID', '10'),
        SetEnvironmentVariable(ign_env_var, ign_path),
        z1_ctrl_process,
        robot_state_publisher,
        controller_manager,
        joint_state_broadcaster_spawner,
        position_controller_spawner,
        teleop_delayed,
    ])

# Interface With EMB SYS

- Commands


## Vacuum

```bash
ros2 service call /b2_unit_001/rig/control b2_srvs/srv/B2Modes "{request_data: 'vacuum_on'}"
ros2 service call /b2_unit_001/rig/control b2_srvs/srv/B2Modes "{request_data: 'vacuum_off'}"
```

## Left Valve

```bash
ros2 service call /b2_unit_001/rig/control b2_srvs/srv/B2Modes "{request_data: 'left_valve_open'}"
ros2 service call /b2_unit_001/rig/control b2_srvs/srv/B2Modes "{request_data: 'left_valve_close'}"
```

## Right Valve

```bash
ros2 service call /b2_unit_001/rig/control b2_srvs/srv/B2Modes "{request_data: 'right_valve_open'}"
ros2 service call /b2_unit_001/rig/control b2_srvs/srv/B2Modes "{request_data: 'right_valve_close'}"
```
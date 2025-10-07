# Unraid Management Agent - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
[![GitHub Release](https://img.shields.io/github/release/domalab/ha-unraid-management-agent.svg)](https://github.com/domalab/ha-unraid-management-agent/releases)
[![License](https://img.shields.io/github/license/domalab/ha-unraid-management-agent.svg)](LICENSE)

Home Assistant custom integration for monitoring and controlling Unraid servers via the Unraid Management Agent.

## Features

### Monitoring
- **System Metrics**: CPU usage, RAM usage, CPU temperature, uptime
- **Array Status**: Array state, usage, parity check status
- **GPU Metrics**: GPU utilization, temperature, power consumption
- **Network**: Interface status, bandwidth usage
- **UPS**: Battery level, load, runtime
- **Containers**: Docker container status and metrics
- **Virtual Machines**: VM status and metrics

### Control
- **Docker Containers**: Start, stop, restart containers
- **Virtual Machines**: Start, stop, restart VMs
- **Array Management**: Start/stop array, parity checks
- **Real-time Updates**: WebSocket support for instant state changes

## Installation

For detailed installation instructions, see [INSTALLATION.md](../../INSTALLATION.md).

### Quick Start

1. **HACS Installation** (Recommended)
   - Add custom repository: `https://github.com/domalab/ha-unraid-management-agent`
   - Install "Unraid Management Agent"
   - Restart Home Assistant

2. **Manual Installation**
   - Copy `unraid_management_agent` folder to `<config>/custom_components/`
   - Restart Home Assistant

3. **Configure**
   - Go to Settings → Devices & Services
   - Add "Unraid Management Agent"
   - Enter your Unraid server details

## Configuration

### Prerequisites

1. Install and configure the Unraid Management Agent on your Unraid server
2. Ensure the agent is accessible from your Home Assistant instance
3. Note the IP address and port (default: 8043)

### Setup via UI

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration**
3. Search for "Unraid Management Agent"
4. Enter your Unraid server details:
   - **Host**: IP address or hostname of your Unraid server
   - **Port**: Port number (default: 8043)
   - **Update Interval**: How often to poll for updates (default: 30 seconds)
   - **Enable WebSocket**: Enable real-time updates (recommended)
5. Click **Submit**

### Configuration Options

After setup, you can modify options by:
1. Go to **Settings** → **Devices & Services**
2. Find "Unraid Management Agent"
3. Click **Configure**

Available options:
- **Update Interval**: Polling interval when WebSocket is unavailable (seconds)
- **Enable WebSocket**: Toggle real-time updates on/off

## Entities

### Sensors

#### System
- `sensor.unraid_cpu_usage` - CPU usage percentage
- `sensor.unraid_ram_usage` - RAM usage percentage
- `sensor.unraid_cpu_temperature` - CPU temperature (°C)
- `sensor.unraid_uptime` - System uptime (seconds)

#### Array
- `sensor.unraid_array_usage` - Array disk usage percentage
- `sensor.unraid_parity_progress` - Parity check progress percentage

#### GPU
- `sensor.unraid_gpu_name` - GPU model name
- `sensor.unraid_gpu_utilization` - GPU utilization percentage
- `sensor.unraid_gpu_cpu_temperature` - CPU temperature (for iGPUs)
- `sensor.unraid_gpu_power` - GPU power consumption (watts)

#### UPS
- `sensor.unraid_ups_battery` - UPS battery level percentage
- `sensor.unraid_ups_load` - UPS load percentage
- `sensor.unraid_ups_runtime` - Estimated runtime (seconds)

#### Network
- `sensor.unraid_network_{interface}_rx` - Bytes received
- `sensor.unraid_network_{interface}_tx` - Bytes transmitted

### Binary Sensors

#### Array
- `binary_sensor.unraid_array_started` - Array running state
- `binary_sensor.unraid_parity_check_running` - Parity check status
- `binary_sensor.unraid_parity_valid` - Parity validity

#### UPS
- `binary_sensor.unraid_ups_connected` - UPS connection status

#### Containers
- `binary_sensor.unraid_container_{name}` - Container running state

#### Virtual Machines
- `binary_sensor.unraid_vm_{name}` - VM running state

#### Network
- `binary_sensor.unraid_network_{interface}` - Interface up/down state

### Switches

- `switch.unraid_container_{name}` - Start/stop Docker containers
- `switch.unraid_vm_{name}` - Start/stop virtual machines

### Buttons

- `button.unraid_array_start` - Start the Unraid array
- `button.unraid_array_stop` - Stop the Unraid array
- `button.unraid_parity_check_start` - Start parity check
- `button.unraid_parity_check_stop` - Stop parity check

## Services

### Container Control

#### `unraid_management_agent.container_start`
Start a Docker container.

```yaml
service: unraid_management_agent.container_start
data:
  container_id: "nginx"
```

#### `unraid_management_agent.container_stop`
Stop a Docker container.

```yaml
service: unraid_management_agent.container_stop
data:
  container_id: "nginx"
```

#### `unraid_management_agent.container_restart`
Restart a Docker container.

```yaml
service: unraid_management_agent.container_restart
data:
  container_id: "nginx"
```

### VM Control

#### `unraid_management_agent.vm_start`
Start a virtual machine.

```yaml
service: unraid_management_agent.vm_start
data:
  vm_id: "Ubuntu"
```

#### `unraid_management_agent.vm_stop`
Stop a virtual machine.

```yaml
service: unraid_management_agent.vm_stop
data:
  vm_id: "Ubuntu"
```

### Array Control

#### `unraid_management_agent.array_start`
Start the Unraid array.

```yaml
service: unraid_management_agent.array_start
```

#### `unraid_management_agent.array_stop`
Stop the Unraid array.

```yaml
service: unraid_management_agent.array_stop
```

#### `unraid_management_agent.parity_check_start`
Start a parity check.

```yaml
service: unraid_management_agent.parity_check_start
```

## Example Automations

For comprehensive automation examples, dashboard configurations, and scripts, see [EXAMPLES.md](../../EXAMPLES.md).

### Quick Examples

**High CPU Alert**
```yaml
automation:
  - alias: "Unraid High CPU Alert"
    trigger:
      - platform: numeric_state
        entity_id: sensor.unraid_cpu_usage
        above: 80
        for:
          minutes: 5
    action:
      - service: notify.mobile_app
        data:
          title: "Unraid Alert"
          message: "CPU usage is above 80%"
```

**Start Container on Array Start**
```yaml
automation:
  - alias: "Start Plex when Array Starts"
    trigger:
      - platform: state
        entity_id: binary_sensor.unraid_array_started
        to: "on"
    action:
      - service: switch.turn_on
        target:
          entity_id: switch.unraid_container_plex
```

See [EXAMPLES.md](../../EXAMPLES.md) for more examples including:
- System monitoring automations
- Array management automations
- Container control automations
- UPS monitoring and graceful shutdown
- Dashboard card configurations
- Notification examples

## Troubleshooting

### Integration Not Appearing

1. Ensure you've restarted Home Assistant after installation
2. Check the logs for any errors: **Settings** → **System** → **Logs**
3. Verify the `custom_components/unraid_management_agent` folder exists

### Cannot Connect to Server

1. Verify the Unraid Management Agent is running on your server
2. Check the IP address and port are correct
3. Ensure Home Assistant can reach the Unraid server (same network/VLAN)
4. Test connectivity: `curl http://<unraid-ip>:8043/api/v1/health`

### WebSocket Not Working

1. Check if WebSocket is enabled in the integration options
2. Verify no firewall is blocking WebSocket connections
3. Check Home Assistant logs for WebSocket errors
4. The integration will fall back to REST API polling if WebSocket fails

### Entities Not Updating

1. Check the update interval in integration options
2. Verify the Unraid Management Agent is collecting data
3. Check Home Assistant logs for API errors
4. Try reloading the integration

### Missing Entities

Some entities are created dynamically:
- Container entities appear when containers exist
- VM entities appear when VMs are configured
- Network entities appear for each interface

If entities are missing:
1. Ensure the corresponding resources exist on Unraid
2. Reload the integration
3. Check logs for errors during entity creation

## Support

- **Issues**: [GitHub Issues](https://github.com/domalab/ha-unraid-management-agent/issues)
- **Documentation**: [GitHub Wiki](https://github.com/domalab/ha-unraid-management-agent/wiki)
- **Discussions**: [GitHub Discussions](https://github.com/domalab/ha-unraid-management-agent/discussions)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Credits

Developed by [@domalab](https://github.com/domalab)


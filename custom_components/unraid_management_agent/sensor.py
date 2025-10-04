"""Sensor platform for Unraid Management Agent."""

from __future__ import annotations

import logging
import re
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    UnitOfDataRate,
    UnitOfPower,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import UnraidDataUpdateCoordinator
from .const import (
    ATTR_ARRAY_STATE,
    ATTR_CPU_CORES,
    ATTR_CPU_MODEL,
    ATTR_CPU_THREADS,
    ATTR_GPU_DRIVER_VERSION,
    ATTR_HOSTNAME,
    ATTR_NETWORK_IP,
    ATTR_NETWORK_MAC,
    ATTR_NETWORK_SPEED,
    ATTR_NUM_DATA_DISKS,
    ATTR_NUM_DISKS,
    ATTR_NUM_PARITY_DISKS,
    ATTR_RAM_TOTAL,
    ATTR_SERVER_MODEL,
    ATTR_UPS_MODEL,
    ATTR_UPS_STATUS,
    DOMAIN,
    ICON_ARRAY,
    ICON_CPU,
    ICON_GPU,
    ICON_MEMORY,
    ICON_NETWORK,
    ICON_PARITY,
    ICON_POWER,
    ICON_TEMPERATURE,
    ICON_UPS,
    ICON_UPTIME,
    KEY_ARRAY,
    KEY_DISKS,
    KEY_GPU,
    KEY_NETWORK,
    KEY_SYSTEM,
    KEY_UPS,
    MANUFACTURER,
    MODEL,
)

_LOGGER = logging.getLogger(__name__)


def _is_physical_network_interface(interface_name: str) -> bool:
    """
    Check if the network interface is a physical interface.

    Only include physical interfaces like eth0, eth1, wlan0, bond0, etc.
    Exclude virtual interfaces (veth*, br-*, docker*, virbr*) and loopback (lo).
    """
    # Patterns for physical interfaces
    physical_patterns = [
        r"^eth\d+$",  # Ethernet: eth0, eth1, etc.
        r"^wlan\d+$",  # Wireless: wlan0, wlan1, etc.
        r"^bond\d+$",  # Bonded interfaces: bond0, bond1, etc.
        r"^eno\d+$",  # Onboard Ethernet: eno1, eno2, etc.
        r"^enp\d+s\d+$",  # PCI Ethernet: enp2s0, etc.
    ]

    # Check if interface matches any physical pattern
    for pattern in physical_patterns:
        if re.match(pattern, interface_name):
            return True

    return False


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Unraid sensor entities."""
    coordinator: UnraidDataUpdateCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities: list[SensorEntity] = []

    # System sensors
    entities.extend(
        [
            UnraidCPUUsageSensor(coordinator, entry),
            UnraidRAMUsageSensor(coordinator, entry),
            UnraidCPUTemperatureSensor(coordinator, entry),
            UnraidUptimeSensor(coordinator, entry),
        ]
    )

    # Motherboard temperature sensor (if available)
    system_data = coordinator.data.get(KEY_SYSTEM, {})
    if system_data.get("motherboard_temp_celsius"):
        entities.append(UnraidMotherboardTemperatureSensor(coordinator, entry))

    # Fan sensors (dynamic, one per fan)
    fans = system_data.get("fans", [])
    for fan in fans:
        fan_name = fan.get("name", "unknown")
        entities.append(UnraidFanSensor(coordinator, entry, fan_name))

    # Array sensors
    entities.extend(
        [
            UnraidArrayUsageSensor(coordinator, entry),
            UnraidParityProgressSensor(coordinator, entry),
        ]
    )

    # Disk sensors (dynamic, one per disk)
    disks = coordinator.data.get(KEY_DISKS, [])
    for disk in disks:
        disk_id = disk.get("id", disk.get("name", "unknown"))
        disk_name = disk.get("name", disk_id)
        # Create usage sensor for each disk (temperature is now an attribute)
        entities.append(UnraidDiskUsageSensor(coordinator, entry, disk_id, disk_name))

    # GPU sensors (if GPU available)
    if coordinator.data.get(KEY_GPU):
        entities.extend(
            [
                UnraidGPUNameSensor(coordinator, entry),
                UnraidGPUUtilizationSensor(coordinator, entry),
                UnraidGPUCPUTemperatureSensor(coordinator, entry),
                UnraidGPUPowerSensor(coordinator, entry),
            ]
        )

    # UPS sensors (if UPS connected)
    if coordinator.data.get(KEY_UPS, {}).get("connected"):
        entities.extend(
            [
                UnraidUPSBatterySensor(coordinator, entry),
                UnraidUPSLoadSensor(coordinator, entry),
                UnraidUPSRuntimeSensor(coordinator, entry),
                UnraidUPSPowerSensor(coordinator, entry),
            ]
        )

    # Network sensors (only physical interfaces)
    for interface in coordinator.data.get(KEY_NETWORK, []):
        interface_name = interface.get("name", "unknown")
        # Only create sensors for physical network interfaces
        if _is_physical_network_interface(interface_name):
            entities.extend(
                [
                    UnraidNetworkRXSensor(coordinator, entry, interface_name),
                    UnraidNetworkTXSensor(coordinator, entry, interface_name),
                ]
            )

    async_add_entities(entities)


class UnraidSensorBase(CoordinatorEntity, SensorEntity):
    """Base class for Unraid sensors."""

    def __init__(
        self,
        coordinator: UnraidDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_has_entity_name = True
        self._entry = entry

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        system_data = self.coordinator.data.get(KEY_SYSTEM, {})
        hostname = system_data.get("hostname", "Unraid")

        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": f"Unraid ({hostname})",
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "sw_version": system_data.get("version", "Unknown"),
        }


# System Sensors


class UnraidCPUUsageSensor(UnraidSensorBase):
    """CPU usage sensor."""

    _attr_name = "CPU Usage"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_CPU
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_cpu_usage"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        cpu_usage = self.coordinator.data.get(KEY_SYSTEM, {}).get("cpu_usage_percent")
        if cpu_usage is not None:
            return round(cpu_usage, 1)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        system_data = self.coordinator.data.get(KEY_SYSTEM, {})
        return {
            ATTR_CPU_MODEL: system_data.get("cpu_model"),
            ATTR_CPU_CORES: system_data.get("cpu_cores"),
            ATTR_CPU_THREADS: system_data.get("cpu_threads"),
        }


class UnraidRAMUsageSensor(UnraidSensorBase):
    """RAM usage sensor."""

    _attr_name = "RAM Usage"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_MEMORY
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_ram_usage"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        ram_usage = self.coordinator.data.get(KEY_SYSTEM, {}).get("ram_usage_percent")
        if ram_usage is not None:
            return round(ram_usage, 1)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        system_data = self.coordinator.data.get(KEY_SYSTEM, {})
        ram_total = system_data.get("ram_total_bytes", 0)
        return {
            ATTR_RAM_TOTAL: (
                f"{ram_total / (1024**3):.2f} GB" if ram_total else "Unknown"
            ),
            ATTR_SERVER_MODEL: system_data.get("server_model"),
        }


class UnraidCPUTemperatureSensor(UnraidSensorBase):
    """CPU temperature sensor."""

    _attr_name = "CPU Temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_TEMPERATURE
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_cpu_temperature"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        return self.coordinator.data.get(KEY_SYSTEM, {}).get("cpu_temp_celsius")


class UnraidMotherboardTemperatureSensor(UnraidSensorBase):
    """Motherboard temperature sensor."""

    _attr_name = "Motherboard Temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_TEMPERATURE
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_motherboard_temperature"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        return self.coordinator.data.get(KEY_SYSTEM, {}).get("motherboard_temp_celsius")


class UnraidFanSensor(UnraidSensorBase):
    """Fan speed sensor."""

    _attr_native_unit_of_measurement = "RPM"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:fan"
    _attr_suggested_display_precision = 0

    def __init__(
        self,
        coordinator: UnraidDataUpdateCoordinator,
        entry: ConfigEntry,
        fan_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._fan_name = fan_name
        self._attr_name = f"Fan {fan_name}"

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        # Sanitize fan name for unique ID
        safe_name = self._fan_name.replace(" ", "_").replace("/", "_").lower()
        return f"{self._entry.entry_id}_fan_{safe_name}"

    @property
    def native_value(self) -> int | None:
        """Return the state."""
        fans = self.coordinator.data.get(KEY_SYSTEM, {}).get("fans", [])
        for fan in fans:
            if fan.get("name") == self._fan_name:
                return fan.get("rpm")
        return None


class UnraidUptimeSensor(UnraidSensorBase):
    """Uptime sensor."""

    _attr_name = "Uptime"
    _attr_icon = ICON_UPTIME

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_uptime"

    @staticmethod
    def _format_uptime(seconds: int) -> str:
        """
        Format uptime seconds into human-readable string.

        Returns format like: "42 days, 21 hours, 31 minutes, 49 seconds"
        Matches the Unraid web UI display format.
        """
        if seconds is None:
            return "Unknown"

        # Calculate time components
        years, remainder = divmod(seconds, 31536000)  # 365 days
        months, remainder = divmod(remainder, 2592000)  # 30 days
        days, remainder = divmod(remainder, 86400)
        hours, remainder = divmod(remainder, 3600)
        minutes, seconds_remaining = divmod(remainder, 60)

        # Build the formatted string
        parts = []
        if years > 0:
            parts.append(f"{years} year{'s' if years != 1 else ''}")
        if months > 0:
            parts.append(f"{months} month{'s' if months != 1 else ''}")
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds_remaining > 0 or not parts:  # Always show seconds if nothing else
            parts.append(
                f"{seconds_remaining} second{'s' if seconds_remaining != 1 else ''}"
            )

        return ", ".join(parts)

    @property
    def native_value(self) -> str | None:
        """Return the state as human-readable uptime."""
        uptime_seconds = self.coordinator.data.get(KEY_SYSTEM, {}).get("uptime_seconds")
        if uptime_seconds is not None:
            return self._format_uptime(uptime_seconds)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        system_data = self.coordinator.data.get(KEY_SYSTEM, {})
        uptime_seconds = system_data.get("uptime_seconds")

        attributes = {
            ATTR_HOSTNAME: system_data.get("hostname"),
        }

        # Include raw seconds value for use in automations/templates
        if uptime_seconds is not None:
            attributes["uptime_seconds"] = uptime_seconds

        return attributes


# Array Sensors


class UnraidArrayUsageSensor(UnraidSensorBase):
    """Array usage sensor."""

    _attr_name = "Array Usage"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_ARRAY
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_array_usage"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        return self.coordinator.data.get(KEY_ARRAY, {}).get("used_percent")

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        array_data = self.coordinator.data.get(KEY_ARRAY, {})
        return {
            ATTR_ARRAY_STATE: array_data.get("state"),
            ATTR_NUM_DISKS: array_data.get("num_disks"),
            ATTR_NUM_DATA_DISKS: array_data.get("num_data_disks"),
            ATTR_NUM_PARITY_DISKS: array_data.get("num_parity_disks"),
        }


class UnraidParityProgressSensor(UnraidSensorBase):
    """Parity check progress sensor."""

    _attr_name = "Parity Check Progress"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_PARITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_parity_progress"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        return self.coordinator.data.get(KEY_ARRAY, {}).get("parity_check_progress")


# GPU Sensors


class UnraidGPUNameSensor(UnraidSensorBase):
    """GPU name sensor."""

    _attr_name = "GPU Name"
    _attr_icon = ICON_GPU

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_gpu_name"

    @property
    def native_value(self) -> str | None:
        """Return the state."""
        gpu_list = self.coordinator.data.get(KEY_GPU, [])
        if gpu_list and len(gpu_list) > 0:
            return gpu_list[0].get("name")
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        gpu_list = self.coordinator.data.get(KEY_GPU, [])
        if gpu_list and len(gpu_list) > 0:
            return {
                ATTR_GPU_DRIVER_VERSION: gpu_list[0].get("driver_version"),
            }
        return {}


class UnraidGPUUtilizationSensor(UnraidSensorBase):
    """GPU utilization sensor."""

    _attr_name = "GPU Utilization"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_GPU
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_gpu_utilization"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        gpu_list = self.coordinator.data.get(KEY_GPU, [])
        if gpu_list and len(gpu_list) > 0:
            return gpu_list[0].get("utilization_gpu_percent")
        return None


class UnraidGPUCPUTemperatureSensor(UnraidSensorBase):
    """GPU CPU temperature sensor (for iGPUs)."""

    _attr_name = "GPU CPU Temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_TEMPERATURE
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_gpu_cpu_temperature"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        gpu_list = self.coordinator.data.get(KEY_GPU, [])
        if gpu_list and len(gpu_list) > 0:
            return gpu_list[0].get("cpu_temperature_celsius")
        return None


class UnraidGPUPowerSensor(UnraidSensorBase):
    """GPU power consumption sensor."""

    _attr_name = "GPU Power"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_POWER
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_gpu_power"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        gpu_list = self.coordinator.data.get(KEY_GPU, [])
        if gpu_list and len(gpu_list) > 0:
            return gpu_list[0].get("power_draw_watts")
        return None


# UPS Sensors


class UnraidUPSBatterySensor(UnraidSensorBase):
    """UPS battery sensor."""

    _attr_name = "UPS Battery"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_UPS
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_ups_battery"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        return self.coordinator.data.get(KEY_UPS, {}).get("battery_charge_percent")


class UnraidUPSLoadSensor(UnraidSensorBase):
    """UPS load sensor."""

    _attr_name = "UPS Load"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.POWER_FACTOR
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_UPS
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_ups_load"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        return self.coordinator.data.get(KEY_UPS, {}).get("load_percent")


class UnraidUPSRuntimeSensor(UnraidSensorBase):
    """UPS runtime sensor."""

    _attr_name = "UPS Runtime"
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_UPS

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_ups_runtime"

    @property
    def native_value(self) -> int | None:
        """Return the state."""
        return self.coordinator.data.get(KEY_UPS, {}).get("runtime_left_seconds")


class UnraidUPSPowerSensor(UnraidSensorBase):
    """UPS power consumption sensor for Energy Dashboard."""

    _attr_name = "UPS Power"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = ICON_POWER
    _attr_suggested_display_precision = 1

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_ups_power"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        ups_data = self.coordinator.data.get(KEY_UPS, {})
        power_watts = ups_data.get("power_watts")

        # Return power_watts if available
        if power_watts is not None:
            return round(power_watts, 1)

        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        ups_data = self.coordinator.data.get(KEY_UPS, {})

        attributes = {
            ATTR_UPS_STATUS: ups_data.get("status"),
            ATTR_UPS_MODEL: ups_data.get("model"),
        }

        # Add load percentage
        load_percent = ups_data.get("load_percent")
        if load_percent is not None:
            attributes["load_percent"] = load_percent

        # Add input/output voltage if available
        input_voltage = ups_data.get("input_voltage")
        if input_voltage is not None:
            attributes["input_voltage"] = input_voltage

        output_voltage = ups_data.get("output_voltage")
        if output_voltage is not None:
            attributes["output_voltage"] = output_voltage

        return attributes


# Network Sensors


class UnraidNetworkRXSensor(UnraidSensorBase):
    """Network inbound traffic sensor."""

    _attr_native_unit_of_measurement = UnitOfDataRate.BITS_PER_SECOND
    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidDataUpdateCoordinator,
        entry: ConfigEntry,
        interface_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._interface_name = interface_name
        self._attr_name = f"Network {interface_name} Inbound"
        self._attr_icon = ICON_NETWORK

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_network_{self._interface_name}_rx"

    @property
    def native_value(self) -> float | None:
        """Return the state in bits per second."""
        for interface in self.coordinator.data.get(KEY_NETWORK, []):
            if interface.get("name") == self._interface_name:
                bytes_received = interface.get("bytes_received")
                if bytes_received is not None:
                    # Convert bytes to bits per second (multiply by 8)
                    return float(bytes_received * 8)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        for interface in self.coordinator.data.get(KEY_NETWORK, []):
            if interface.get("name") == self._interface_name:
                return {
                    ATTR_NETWORK_MAC: interface.get("mac_address"),
                    ATTR_NETWORK_IP: interface.get("ip_address"),
                    ATTR_NETWORK_SPEED: interface.get("speed"),
                    "status": interface.get("status"),
                    "interface": self._interface_name,
                }
        return {}


class UnraidNetworkTXSensor(UnraidSensorBase):
    """Network outbound traffic sensor."""

    _attr_native_unit_of_measurement = UnitOfDataRate.BITS_PER_SECOND
    _attr_device_class = SensorDeviceClass.DATA_RATE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidDataUpdateCoordinator,
        entry: ConfigEntry,
        interface_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._interface_name = interface_name
        self._attr_name = f"Network {interface_name} Outbound"
        self._attr_icon = ICON_NETWORK

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        return f"{self._entry.entry_id}_network_{self._interface_name}_tx"

    @property
    def native_value(self) -> float | None:
        """Return the state in bits per second."""
        for interface in self.coordinator.data.get(KEY_NETWORK, []):
            if interface.get("name") == self._interface_name:
                bytes_sent = interface.get("bytes_sent")
                if bytes_sent is not None:
                    # Convert bytes to bits per second (multiply by 8)
                    return float(bytes_sent * 8)
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        for interface in self.coordinator.data.get(KEY_NETWORK, []):
            if interface.get("name") == self._interface_name:
                return {
                    ATTR_NETWORK_MAC: interface.get("mac_address"),
                    ATTR_NETWORK_IP: interface.get("ip_address"),
                    ATTR_NETWORK_SPEED: interface.get("speed"),
                    "status": interface.get("status"),
                    "interface": self._interface_name,
                }
        return {}


class UnraidDiskUsageSensor(UnraidSensorBase):
    """Disk usage sensor."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:harddisk"
    _attr_suggested_display_precision = 1

    def __init__(
        self,
        coordinator: UnraidDataUpdateCoordinator,
        entry: ConfigEntry,
        disk_id: str,
        disk_name: str,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator, entry)
        self._disk_id = disk_id
        self._disk_name = disk_name
        self._attr_name = f"Disk {disk_name} Usage"
        self._last_known_value = None

    @property
    def unique_id(self) -> str:
        """Return unique ID."""
        # Sanitize disk ID for unique ID
        safe_id = self._disk_id.replace(" ", "_").replace("/", "_").lower()
        return f"{self._entry.entry_id}_disk_{safe_id}_usage"

    @property
    def native_value(self) -> float | None:
        """Return the state."""
        for disk in self.coordinator.data.get(KEY_DISKS, []):
            disk_id = disk.get("id", disk.get("name"))
            if disk_id == self._disk_id:
                spin_state = disk.get("spin_state", "active")
                usage_percent = disk.get("usage_percent")

                # Calculate usage_percent if not provided by API
                if usage_percent is None:
                    size_bytes = disk.get("size_bytes", 0)
                    used_bytes = disk.get("used_bytes", 0)
                    if size_bytes > 0 and used_bytes > 0:
                        usage_percent = (used_bytes / size_bytes) * 100

                # If disk is in standby/idle, return last known value
                if spin_state in ("standby", "idle"):
                    return self._last_known_value

                # Disk is active, update and return current value
                if usage_percent is not None:
                    self._last_known_value = round(usage_percent, 1)
                    return self._last_known_value

        return self._last_known_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra attributes."""
        for disk in self.coordinator.data.get(KEY_DISKS, []):
            disk_id = disk.get("id", disk.get("name"))
            if disk_id == self._disk_id:
                size_bytes = disk.get("size_bytes", 0)
                used_bytes = disk.get("used_bytes", 0)
                free_bytes = disk.get("free_bytes", 0)
                spin_state = disk.get("spin_state", "active")
                temperature = disk.get("temperature_celsius")

                attrs = {
                    "device": disk.get("device"),
                    "status": disk.get("status"),
                    "filesystem": disk.get("filesystem"),
                    "mount_point": disk.get("mount_point"),
                    "spin_state": spin_state,
                    "size": (
                        f"{size_bytes / (1024**3):.2f} GB"
                        if size_bytes is not None
                        else "Unknown"
                    ),
                    "used": (
                        f"{used_bytes / (1024**3):.2f} GB"
                        if used_bytes is not None
                        else "Unknown"
                    ),
                    "free": (
                        f"{free_bytes / (1024**3):.2f} GB"
                        if free_bytes is not None
                        else "Unknown"
                    ),
                    "smart_status": disk.get("smart_status"),
                    "smart_errors": disk.get("smart_errors", 0),
                }

                # Add temperature if available (will be 0 or None when spun down)
                if temperature is not None and temperature > 0:
                    attrs["temperature_celsius"] = temperature
                elif spin_state in ("standby", "idle"):
                    attrs["temperature_celsius"] = "Disk in standby"

                return attrs
        return {}

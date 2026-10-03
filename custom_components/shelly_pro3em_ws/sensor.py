"""Sensors mapped from em:0 NotifyStatus."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfApparentPower,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfEnergy,
    UnitOfFrequency,
    UnitOfPower,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ShellyWsCoordinator


@dataclass(frozen=True, kw_only=True)
class EmSensorDescription(SensorEntityDescription):
    value_fn: Callable[[dict[str, Any]], float | None] = lambda d: None


def _num(data: dict[str, Any], key: str) -> float | None:
    val = data.get(key)
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


SENSORS: tuple[EmSensorDescription, ...] = (
    EmSensorDescription(
        key="total_act_power",
        translation_key="total_act_power",
        name="Total active power",
        native_unit_of_measurement=UnitOfPower.WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _num(d, "total_act_power"),
    ),
    EmSensorDescription(
        key="total_aprt_power",
        translation_key="total_aprt_power",
        name="Total apparent power",
        native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
        device_class=SensorDeviceClass.APPARENT_POWER,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _num(d, "total_aprt_power"),
    ),
    EmSensorDescription(
        key="total_current",
        name="Total current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: _num(d, "total_current"),
    ),
    EmSensorDescription(
        key="n_current",
        name="Neutral current",
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        device_class=SensorDeviceClass.CURRENT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_registry_enabled_default=False,
        value_fn=lambda d: _num(d, "n_current"),
    ),
)

for _phase, _label in (("a", "A"), ("b", "B"), ("c", "C")):
    SENSORS += (  # type: ignore[assignment]
        EmSensorDescription(
            key=f"{_phase}_act_power",
            name=f"Phase {_label} active power",
            native_unit_of_measurement=UnitOfPower.WATT,
            device_class=SensorDeviceClass.POWER,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda d, k=f"{_phase}_act_power": _num(d, k),
        ),
        EmSensorDescription(
            key=f"{_phase}_aprt_power",
            name=f"Phase {_label} apparent power",
            native_unit_of_measurement=UnitOfApparentPower.VOLT_AMPERE,
            device_class=SensorDeviceClass.APPARENT_POWER,
            state_class=SensorStateClass.MEASUREMENT,
            entity_registry_enabled_default=False,
            value_fn=lambda d, k=f"{_phase}_aprt_power": _num(d, k),
        ),
        EmSensorDescription(
            key=f"{_phase}_voltage",
            name=f"Phase {_label} voltage",
            native_unit_of_measurement=UnitOfElectricPotential.VOLT,
            device_class=SensorDeviceClass.VOLTAGE,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda d, k=f"{_phase}_voltage": _num(d, k),
        ),
        EmSensorDescription(
            key=f"{_phase}_current",
            name=f"Phase {_label} current",
            native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
            device_class=SensorDeviceClass.CURRENT,
            state_class=SensorStateClass.MEASUREMENT,
            value_fn=lambda d, k=f"{_phase}_current": _num(d, k),
        ),
        EmSensorDescription(
            key=f"{_phase}_pf",
            name=f"Phase {_label} power factor",
            device_class=SensorDeviceClass.POWER_FACTOR,
            state_class=SensorStateClass.MEASUREMENT,
            entity_registry_enabled_default=False,
            value_fn=lambda d, k=f"{_phase}_pf": _num(d, k),
        ),
        EmSensorDescription(
            key=f"{_phase}_freq",
            name=f"Phase {_label} frequency",
            native_unit_of_measurement=UnitOfFrequency.HERTZ,
            device_class=SensorDeviceClass.FREQUENCY,
            state_class=SensorStateClass.MEASUREMENT,
            entity_registry_enabled_default=False,
            value_fn=lambda d, k=f"{_phase}_freq": _num(d, k),
        ),
    )


def _energy(key: str, name: str, enabled: bool = True) -> EmSensorDescription:
    return EmSensorDescription(
        key=key,
        name=name,
        native_unit_of_measurement=UnitOfEnergy.WATT_HOUR,
        suggested_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        suggested_display_precision=3,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_registry_enabled_default=enabled,
        value_fn=lambda d, k=key: _num(d, k),
    )


SENSORS += (  # type: ignore[assignment]
    _energy("total_act", "Total energy imported"),
    _energy("total_act_ret", "Total energy exported"),
)
for _phase, _label in (("a", "A"), ("b", "B"), ("c", "C")):
    SENSORS += (  # type: ignore[assignment]
        _energy(f"{_phase}_total_act_energy", f"Phase {_label} energy imported", False),
        _energy(f"{_phase}_total_act_ret_energy", f"Phase {_label} energy exported", False),
    )


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: ShellyWsCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(EmSensor(coordinator, entry, desc) for desc in SENSORS)


class EmSensor(CoordinatorEntity[ShellyWsCoordinator], SensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: ShellyWsCoordinator,
        entry: ConfigEntry,
        description: EmSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._value_fn = description.value_fn
        device_id = entry.data.get("device_id") or coordinator.device_id
        self._attr_unique_id = f"{device_id}_{description.key}"
        mac = entry.data.get("mac")
        connections = {("mac", mac)} if mac else set()
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            connections=connections,
            manufacturer="Shelly",
            model="Pro 3EM",
            name=device_id,
        )

    @property
    def native_value(self) -> float | None:
        return self._value_fn(self.coordinator.data or {})

"""Switch platform for Frigate Camera Control."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import DOMAIN, FrigateCoordinator

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Frigate camera switches."""
    coordinator: FrigateCoordinator = hass.data[DOMAIN][config_entry.entry_id]
    
    entities = []
    
    # Create a switch for each camera
    for camera_name in coordinator.data:
        entities.append(FrigateCameraSwitch(coordinator, camera_name))
    
    async_add_entities(entities)

class FrigateCameraSwitch(CoordinatorEntity, SwitchEntity):
    """Frigate camera switch."""

    def __init__(self, coordinator: FrigateCoordinator, camera_name: str):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._camera_name = camera_name
        self._attr_name = f"Frigate {camera_name.title()}"
        self._attr_unique_id = f"frigate_camera_{camera_name}"
        self._attr_icon = "mdi:camera"

    @property
    def is_on(self) -> bool:
        """Return true if the camera is enabled."""
        camera_data = self.coordinator.data.get(self._camera_name, {})
        return camera_data.get("enabled", True)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._camera_name in self.coordinator.data

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the camera on."""
        _LOGGER.info(f"Turning ON camera {self._camera_name}")
        success = await self.coordinator.set_camera_state(self._camera_name, True)
        if not success:
            _LOGGER.error(f"Failed to enable camera {self._camera_name}")

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the camera off."""
        _LOGGER.info(f"Turning OFF camera {self._camera_name}")
        success = await self.coordinator.set_camera_state(self._camera_name, False)
        if not success:
            _LOGGER.error(f"Failed to disable camera {self._camera_name}")

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, f"frigate_{self.coordinator.host}_{self.coordinator.port}")},
            "name": f"Frigate Server ({self.coordinator.host}:{self.coordinator.port})",
            "manufacturer": "Frigate",
            "model": "NVR",
            "sw_version": "Unknown",
        }

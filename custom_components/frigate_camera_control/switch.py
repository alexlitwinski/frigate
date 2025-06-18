"""Switch platform for Frigate Camera Control."""
import logging
import time

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
        self._is_changing = False  # Prevent concurrent operations
        self._assumed_state = None  # Track what we think the state should be

    @property
    def is_on(self) -> bool:
        """Return true if the camera is enabled."""
        # If we're in the middle of changing, use assumed state
        if self._is_changing and self._assumed_state is not None:
            return self._assumed_state
            
        # Otherwise use coordinator data
        camera_data = self.coordinator.data.get(self._camera_name, {})
        return camera_data.get("enabled", True)

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return self.coordinator.last_update_success and self._camera_name in self.coordinator.data

    async def async_turn_on(self, **kwargs) -> None:
        """Turn the camera on."""
        if self._is_changing:
            _LOGGER.warning(f"Camera {self._camera_name} is already being changed, ignoring")
            return
            
        self._is_changing = True
        self._assumed_state = True
        self.async_write_ha_state()
        
        try:
            success = await self.coordinator.enable_camera(self._camera_name)
            if success:
                _LOGGER.info(f"Successfully enabled camera {self._camera_name}")
            else:
                # Revert on failure
                self._assumed_state = False
                self.async_write_ha_state()
                _LOGGER.error(f"Failed to enable camera {self._camera_name}")
        finally:
            self._is_changing = False
            # Clear assumed state after a delay to let coordinator sync
            self.hass.loop.call_later(5, self._clear_assumed_state)

    async def async_turn_off(self, **kwargs) -> None:
        """Turn the camera off."""
        if self._is_changing:
            _LOGGER.warning(f"Camera {self._camera_name} is already being changed, ignoring")
            return
            
        self._is_changing = True
        self._assumed_state = False
        self.async_write_ha_state()
        
        try:
            success = await self.coordinator.disable_camera(self._camera_name)
            if success:
                _LOGGER.info(f"Successfully disabled camera {self._camera_name}")
            else:
                # Revert on failure
                self._assumed_state = True
                self.async_write_ha_state()
                _LOGGER.error(f"Failed to disable camera {self._camera_name}")
        finally:
            self._is_changing = False
            # Clear assumed state after a delay to let coordinator sync
            self.hass.loop.call_later(5, self._clear_assumed_state)

    def _clear_assumed_state(self):
        """Clear the assumed state and update."""
        self._assumed_state = None
        self.async_write_ha_state()

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

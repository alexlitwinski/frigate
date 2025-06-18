"""Frigate Camera Control integration for Home Assistant."""
import logging
import aiohttp
import asyncio
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

DOMAIN = "frigate_camera_control"
PLATFORMS = ["switch"]

class FrigateCoordinator(DataUpdateCoordinator):
    """Frigate data coordinator."""

    def __init__(self, hass: HomeAssistant, host: str, port: int):
        """Initialize coordinator."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/api"
        self.session = async_get_clientsession(hass)
        self._pending_changes = {}  # Track cameras being changed
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        """Fetch data from Frigate."""
        try:
            # Use config endpoint as it's more reliable for enabled/disabled state
            async with self.session.get(f"{self.base_url}/config") as response:
                if response.status == 200:
                    config = await response.json()
                    cameras = {}
                    
                    if "cameras" in config:
                        for camera_name, camera_config in config["cameras"].items():
                            # Don't override state if camera is being changed
                            if camera_name in self._pending_changes:
                                cameras[camera_name] = {
                                    "name": camera_name,
                                    "enabled": self._pending_changes[camera_name]
                                }
                            else:
                                cameras[camera_name] = {
                                    "name": camera_name,
                                    "enabled": camera_config.get("enabled", True)
                                }
                    
                    return cameras
                else:
                    raise UpdateFailed(f"Error fetching config: {response.status}")
                    
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Frigate: {err}")

    async def enable_camera(self, camera_name: str):
        """Enable a camera with proper state management."""
        try:
            # Mark camera as being changed
            self._pending_changes[camera_name] = True
            
            # Send API command
            async with self.session.put(f"{self.base_url}/{camera_name}/enable") as response:
                if response.status == 200:
                    _LOGGER.info(f"Camera {camera_name} enable command sent successfully")
                    
                    # Wait a bit for Frigate to process the change
                    await asyncio.sleep(3)
                    
                    # Clear pending change and refresh
                    self._pending_changes.pop(camera_name, None)
                    await self.async_request_refresh()
                    
                    return True
                else:
                    # Remove pending change on failure
                    self._pending_changes.pop(camera_name, None)
                    _LOGGER.error(f"Failed to enable camera {camera_name}: HTTP {response.status}")
                    return False
                    
        except Exception as err:
            # Remove pending change on error
            self._pending_changes.pop(camera_name, None)
            _LOGGER.error(f"Error enabling camera {camera_name}: {err}")
            return False

    async def disable_camera(self, camera_name: str):
        """Disable a camera with proper state management."""
        try:
            # Mark camera as being changed
            self._pending_changes[camera_name] = False
            
            # Send API command
            async with self.session.put(f"{self.base_url}/{camera_name}/disable") as response:
                if response.status == 200:
                    _LOGGER.info(f"Camera {camera_name} disable command sent successfully")
                    
                    # Wait a bit for Frigate to process the change
                    await asyncio.sleep(3)
                    
                    # Clear pending change and refresh
                    self._pending_changes.pop(camera_name, None)
                    await self.async_request_refresh()
                    
                    return True
                else:
                    # Remove pending change on failure
                    self._pending_changes.pop(camera_name, None)
                    _LOGGER.error(f"Failed to disable camera {camera_name}: HTTP {response.status}")
                    return False
                    
        except Exception as err:
            # Remove pending change on error
            self._pending_changes.pop(camera_name, None)
            _LOGGER.error(f"Error disabling camera {camera_name}: {err}")
            return False

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Frigate Camera Control from a config entry."""
    host = entry.data["host"]
    port = entry.data["port"]
    
    coordinator = FrigateCoordinator(hass, host, port)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Forward the setup to the switch platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok"""Frigate Camera Control integration for Home Assistant."""
import logging
import aiohttp
import asyncio
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)

DOMAIN = "frigate_camera_control"
PLATFORMS = ["switch"]

class FrigateCoordinator(DataUpdateCoordinator):
    """Frigate data coordinator."""

    def __init__(self, hass: HomeAssistant, host: str, port: int):
        """Initialize coordinator."""
        self.host = host
        self.port = port
        self.base_url = f"http://{host}:{port}/api"
        self.session = async_get_clientsession(hass)
        self._pending_changes = {}  # Track cameras being changed
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        """Fetch data from Frigate."""
        try:
            # Use config endpoint as it's more reliable for enabled/disabled state
            async with self.session.get(f"{self.base_url}/config") as response:
                if response.status == 200:
                    config = await response.json()
                    cameras = {}
                    
                    if "cameras" in config:
                        for camera_name, camera_config in config["cameras"].items():
                            # Don't override state if camera is being changed
                            if camera_name in self._pending_changes:
                                cameras[camera_name] = {
                                    "name": camera_name,
                                    "enabled": self._pending_changes[camera_name]
                                }
                            else:
                                cameras[camera_name] = {
                                    "name": camera_name,
                                    "enabled": camera_config.get("enabled", True)
                                }
                    
                    return cameras
                else:
                    raise UpdateFailed(f"Error fetching config: {response.status}")
                    
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Frigate: {err}")

    async def enable_camera(self, camera_name: str):
        """Enable a camera with proper state management."""
        try:
            # Mark camera as being changed
            self._pending_changes[camera_name] = True
            
            # Send API command
            async with self.session.put(f"{self.base_url}/{camera_name}/enable") as response:
                if response.status == 200:
                    _LOGGER.info(f"Camera {camera_name} enable command sent successfully")
                    
                    # Wait a bit for Frigate to process the change
                    await asyncio.sleep(3)
                    
                    # Clear pending change and refresh
                    self._pending_changes.pop(camera_name, None)
                    await self.async_request_refresh()
                    
                    return True
                else:
                    # Remove pending change on failure
                    self._pending_changes.pop(camera_name, None)
                    _LOGGER.error(f"Failed to enable camera {camera_name}: HTTP {response.status}")
                    return False
                    
        except Exception as err:
            # Remove pending change on error
            self._pending_changes.pop(camera_name, None)
            _LOGGER.error(f"Error enabling camera {camera_name}: {err}")
            return False

    async def disable_camera(self, camera_name: str):
        """Disable a camera with proper state management."""
        try:
            # Mark camera as being changed
            self._pending_changes[camera_name] = False
            
            # Send API command
            async with self.session.put(f"{self.base_url}/{camera_name}/disable") as response:
                if response.status == 200:
                    _LOGGER.info(f"Camera {camera_name} disable command sent successfully")
                    
                    # Wait a bit for Frigate to process the change
                    await asyncio.sleep(3)
                    
                    # Clear pending change and refresh
                    self._pending_changes.pop(camera_name, None)
                    await self.async_request_refresh()
                    
                    return True
                else:
                    # Remove pending change on failure
                    self._pending_changes.pop(camera_name, None)
                    _LOGGER.error(f"Failed to disable camera {camera_name}: HTTP {response.status}")
                    return False
                    
        except Exception as err:
            # Remove pending change on error
            self._pending_changes.pop(camera_name, None)
            _LOGGER.error(f"Error disabling camera {camera_name}: {err}")
            return False

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Frigate Camera Control from a config entry."""
    host = entry.data["host"]
    port = entry.data["port"]
    
    coordinator = FrigateCoordinator(hass, host, port)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Forward the setup to the switch platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

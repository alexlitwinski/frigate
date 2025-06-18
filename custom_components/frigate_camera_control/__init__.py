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
        
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),  # Increased interval to reduce conflicts
        )

    async def _async_update_data(self):
        """Fetch data from Frigate."""
        try:
            # Get current status from stats endpoint (more reliable for enabled/disabled state)
            async with self.session.get(f"{self.base_url}/stats") as response:
                if response.status == 200:
                    stats = await response.json()
                    cameras = {}
                    
                    # Get camera status from stats
                    if "cameras" in stats:
                        for camera_name, camera_stats in stats["cameras"].items():
                            # Check if camera is actually running (detection/ffmpeg processes)
                            detection_enabled = camera_stats.get("detection_enabled", True)
                            cameras[camera_name] = {
                                "name": camera_name,
                                "enabled": detection_enabled
                            }
                    
                    # Fallback to config if stats doesn't have camera info
                    if not cameras:
                        async with self.session.get(f"{self.base_url}/config") as config_response:
                            if config_response.status == 200:
                                config = await config_response.json()
                                if "cameras" in config:
                                    for camera_name, camera_config in config["cameras"].items():
                                        cameras[camera_name] = {
                                            "name": camera_name,
                                            "enabled": camera_config.get("enabled", True)
                                        }
                    
                    return cameras
                else:
                    raise UpdateFailed(f"Error fetching stats: {response.status}")
                    
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Frigate: {err}")

    async def enable_camera(self, camera_name: str):
        """Enable a camera."""
        try:
            async with self.session.put(f"{self.base_url}/{camera_name}/enable") as response:
                if response.status == 200:
                    # Update local state immediately to prevent UI flicker
                    if self.data and camera_name in self.data:
                        self.data[camera_name]["enabled"] = True
                        self.async_update_listeners()
                    
                    # Request refresh after a short delay to get actual state
                    await asyncio.sleep(2)
                    await self.async_request_refresh()
                    return True
                else:
                    _LOGGER.error(f"Failed to enable camera {camera_name}: {response.status}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error enabling camera {camera_name}: {err}")
            return False

    async def disable_camera(self, camera_name: str):
        """Disable a camera."""
        try:
            async with self.session.put(f"{self.base_url}/{camera_name}/disable") as response:
                if response.status == 200:
                    # Update local state immediately to prevent UI flicker
                    if self.data and camera_name in self.data:
                        self.data[camera_name]["enabled"] = False
                        self.async_update_listeners()
                    
                    # Request refresh after a short delay to get actual state
                    await asyncio.sleep(2)
                    await self.async_request_refresh()
                    return True
                else:
                    _LOGGER.error(f"Failed to disable camera {camera_name}: {response.status}")
                    return False
        except Exception as err:
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

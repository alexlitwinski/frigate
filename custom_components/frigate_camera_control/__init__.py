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
            update_interval=timedelta(seconds=30),
        )

    async def _async_update_data(self):
        """Fetch data from Frigate."""
        try:
            async with self.session.get(f"{self.base_url}/config", timeout=10) as response:
                if response.status == 200:
                    config = await response.json()
                    cameras = {}
                    
                    if "cameras" in config and config["cameras"]:
                        for camera_name, camera_config in config["cameras"].items():
                            cameras[camera_name] = {
                                "name": camera_name,
                                "enabled": camera_config.get("enabled", True)
                            }
                    
                    return cameras
                else:
                    raise UpdateFailed(f"Error fetching config: {response.status}")
                    
        except asyncio.TimeoutError:
            raise UpdateFailed("Timeout connecting to Frigate")
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Frigate: {err}")

    async def enable_camera(self, camera_name: str):
        """Enable a camera."""
        try:
            async with self.session.put(f"{self.base_url}/{camera_name}/enable") as response:
                if response.status == 200:
                    _LOGGER.info(f"Camera {camera_name} enabled successfully")
                    # Wait and refresh
                    await asyncio.sleep(2)
                    await self.async_request_refresh()
                    return True
                else:
                    _LOGGER.error(f"Failed to enable camera {camera_name}: HTTP {response.status}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error enabling camera {camera_name}: {err}")
            return False

    async def disable_camera(self, camera_name: str):
        """Disable a camera."""
        try:
            async with self.session.put(f"{self.base_url}/{camera_name}/disable") as response:
                if response.status == 200:
                    _LOGGER.info(f"Camera {camera_name} disabled successfully")
                    # Wait and refresh
                    await asyncio.sleep(2)
                    await self.async_request_refresh()
                    return True
                else:
                    _LOGGER.error(f"Failed to disable camera {camera_name}: HTTP {response.status}")
                    return False
        except Exception as err:
            _LOGGER.error(f"Error disabling camera {camera_name}: {err}")
            return False

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Frigate Camera Control from a config entry."""
    host = entry.data["host"]
    port = entry.data["port"]
    
    coordinator = FrigateCoordinator(hass, host, port)
    
    try:
        await coordinator.async_config_entry_first_refresh()
        
        if not coordinator.data:
            _LOGGER.error("No camera data received from Frigate")
            return False
            
    except Exception as err:
        _LOGGER.error(f"Failed to connect to Frigate at {host}:{port} - {err}")
        return False
    
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok

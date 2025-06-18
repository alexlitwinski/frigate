"""Config flow for Frigate Camera Control integration."""
import logging
import aiohttp
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

_LOGGER = logging.getLogger(__name__)

DOMAIN = "frigate_camera_control"

STEP_USER_DATA_SCHEMA = vol.Schema({
    vol.Required("host", default="localhost"): str,
    vol.Required("port", default=5000): int,
})

async def validate_input(hass: HomeAssistant, data: dict) -> dict:
    """Validate the user input allows us to connect."""
    host = data["host"]
    port = data["port"]
    
    session = async_get_clientsession(hass)
    
    try:
        async with session.get(f"http://{host}:{port}/api/config", timeout=10) as response:
            if response.status == 200:
                config = await response.json()
                if "cameras" in config and len(config["cameras"]) > 0:
                    return {"title": f"Frigate ({host}:{port})"}
                else:
                    raise ValueError("No cameras found in Frigate configuration")
            else:
                raise ValueError(f"HTTP {response.status}")
    except aiohttp.ClientError as err:
        raise ValueError(f"Cannot connect to Frigate: {err}")

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Frigate Camera Control."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step."""
        errors = {}
        
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
                
                # Check if already configured
                await self.async_set_unique_id(f"{user_input['host']}:{user_input['port']}")
                self._abort_if_unique_id_configured()
                
                return self.async_create_entry(title=info["title"], data=user_input)
            
            except ValueError:
                _LOGGER.exception("Cannot connect to Frigate")
                errors["base"] = "cannot_connect"
            except Exception:
                _LOGGER.exception("Unexpected exception during setup")
                errors["base"] = "unknown"

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

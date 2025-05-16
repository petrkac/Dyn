import logging
from datetime import timedelta
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=30)

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Optional("name", default="Dyn PV Forecast"): cv.string,
})

def setup_platform(hass, config, add_entities, discovery_info=None):
    name = config.get("name")
    sensor = DynPVForecastSensor(name, hass)
    add_entities([sensor], True)

class DynPVForecastSensor(Entity):
    def __init__(self, name, hass):
        self._name = name
        self.hass = hass
        self._state = None
        self._attr_extra_state_attributes = {}

    @property
    def name(self):
        return self._name

    @property
    def state(self):
        return self._state

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes

    @Throttle(MIN_TIME_BETWEEN_UPDATES)
def update(self):
    try:
        today_entity = self._hass.states.get("sensor.solcast_pv_forecast_forecast_today")
        tomorrow_entity = self._hass.states.get("sensor.solcast_pv_forecast_forecast_tomorrow")

        if today_entity is None or tomorrow_entity is None:
            _LOGGER.warning("One of the Solcast sensors is not available yet")
            return

        # Předpokládám, že data jsou v today_entity.state a tomorrow_entity.state jako JSON string nebo dict
        today_data = today_entity.state
        tomorrow_data = tomorrow_entity.state

        # Pro jednoduchost přímo uložíme do atributů
        self._state = today_data  # nebo nějaká vhodná hodnota z today_data

        self._attr_extra_state_attributes = {
            "today_forecast": today_data,
            "tomorrow_forecast": tomorrow_data,
            "DataCorrect": True,
        }

    except Exception as e:
        _LOGGER.error(f"Failed to update Dyn PV Forecast sensor: {e}")
        self._attr_extra_state_attributes = {
            "DataCorrect": False,
            "error": str(e),
        }

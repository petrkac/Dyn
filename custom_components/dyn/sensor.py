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
    sensor = DynPVForecastSensor(hass, name)
    add_entities([sensor], True)

class DynPVForecastSensor(Entity):
    def __init__(self, hass, name):
        self._hass = hass
        self._name = name
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
        # Příklad: získat data z jiných sensorů v HA
        today_sensor = self._hass.states.get("sensor.solcast_pv_forecast_forecast_today")
        tomorrow_sensor = self._hass.states.get("sensor.solcast_pv_forecast_forecast_tomorrow")

        if today_sensor is None or today_sensor.state is None:
            _LOGGER.warning("Dnešní Solcast sensor není k dispozici")
            self._state = None
            self._attr_extra_state_attributes = {}
            return

        # Pro jednoduchost použijeme jako stav hodnotu dnešního senzoru
        self._state = today_sensor.state

        # Přidáme atributy - např. data z dnešního a zítřejšího senzoru
        self._attr_extra_state_attributes = {
            "today": today_sensor.state,
            "tomorrow": tomorrow_sensor.state if tomorrow_sensor else "unknown",
            "DataCorrect": True,
        }

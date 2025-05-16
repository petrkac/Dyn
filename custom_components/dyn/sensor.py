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
        solcast_state = self.hass.states.get("sensor.solcast_pv_forecast_forecast_today")
        if solcast_state:
            try:
                self._state = float(solcast_state.state)
            except (ValueError, TypeError):
                self._state = None
                _LOGGER.error("Neplatný stav ze senzoru solcast: %s", solcast_state.state)
            self._attr_extra_state_attributes = solcast_state.attributes or {}
        else:
            self._state = None
            self._attr_extra_state_attributes = {}

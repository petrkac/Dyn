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
    sensor = DynPVForecastSensor(name)
    add_entities([sensor], True)

class DynPVForecastSensor(Entity):
    def __init__(self, name):
        self._name = name
        self._state = None
        self._attr_extra_state_attributes = {}
        self._last_update = None

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
        # Tady bude logika získání dat (API, výpočet apod.)
        # Pro test nastavíme dummy data
        self._state = 42.0
        self._attr_extra_state_attributes = {
            "DetailedForecast": [
                {
                    "period_start": "2025-05-15T00:00:00+02:00",
                    "pv_estimate": 0,
                    "pv_estimate10": 0,
                    "pv_estimate90": 0,
                },
                # přidej další podle potřeby
            ],
            "Dayname": "Thursday",
            "DataCorrect": True
        }

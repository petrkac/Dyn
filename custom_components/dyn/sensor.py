import logging
from datetime import timedelta
from datetime import datetime
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.helpers.entity import Entity
from homeassistant.util import Throttle

_LOGGER = logging.getLogger(__name__)

MIN_TIME_BETWEEN_UPDATES = timedelta(minutes=1)

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
        # Tady bude logika získání dat (API, výpočet apod.)
        today_sensor = self._hass.states.get("sensor.solcast_pv_forecast_forecast_today")
        tomorrow_sensor = self._hass.states.get("sensor.solcast_pv_forecast_forecast_tomorrow")
        now = datetime.now().isoformat()

        # Inicializace pole
        if "bat_new_state" not in self._attr_extra_state_attributes:
            self._attr_extra_state_attributes["bat_new_state"] = [None] * 48

        # Spočítej aktuální index půlhodinového úseku
        now2 = datetime.now()
        index = now2.hour * 2 + (1 if now2.minute >= 30 else 0)

        # Spočítej hodnotu a zapiš
        bat_sensor = self._hass.states.get("sensor.battery_state_of_charge")
        dod_sensor = self._hass.states.get("number.depth_of_discharge_on_grid")

        if bat_sensor and dod_sensor and bat_sensor.state not in (None, "unknown") and dod_sensor.state not in (None, "unknown"):
            try:
                soc = float(bat_sensor.state)
                dod = float(dod_sensor.state)
                new_value = (soc - dod) * 9.6
                self._attr_extra_state_attributes["bat_new_state"][index] = new_value
            except ValueError:
                _LOGGER.warning("Chyba při výpočtu bat_new_state")
                

        
        # Pro test nastavíme dummy stav
        self._state = 42.0

        # Aktualizace atributů místo přepsání celého slovníku
        self._attr_extra_state_attributes["DetailedForecast"] = [
            {
                "period_start": "2025-05-15T00:00:00+02:00",
                "pv_estimate": 0,
                "pv_estimate10": 0,
                "pv_estimate90": 0,
            },
        ]
        self._attr_extra_state_attributes["Dayname"] = "Thursday"
        self._attr_extra_state_attributes["DataCorrect"] = True
        self._attr_extra_state_attributes["Today"] = (
            today_sensor.state if today_sensor else "unknown"
        )
        self._attr_extra_state_attributes["Tomorrow"] = (
            tomorrow_sensor.state if tomorrow_sensor else "unknown"
        )
        self._attr_extra_state_attributes["Ohrev vody"] = [
            0.46 if (10 <= i <= 15 or 30 <= i <= 45) else 0.0
            for i in range(48)
        ]
        self._attr_extra_state_attributes["L1a2"] = [0.27 for _ in range(48)]
        self._attr_extra_state_attributes["Bat_Old_vybiji"] = [
            1 if (0 <= i <= 15 or 44 <= i <= 47) else 0
            for i in range(48)
        ]
        self._attr_extra_state_attributes["Bat_Old_nabiji"] = [
            0 if (0 <= i <= 15 or 44 <= i <= 47) else 1
            for i in range(48)
        ]
        self._attr_extra_state_attributes["Bat_new_nabiji"] = [0 for _ in range(48)]
        self._attr_extra_state_attributes["Bat_Old_state"] = [0 for _ in range(48)]
        self._attr_extra_state_attributes["Cas"] = now 
        


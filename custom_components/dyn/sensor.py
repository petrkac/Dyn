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
    now = datetime.now()
    index = now.hour * 2 + (1 if now.minute >= 30 else 0)
    _LOGGER.debug(f"Aktuální čas: {now}, index: {index}")

    today_sensor = self._hass.states.get("sensor.solcast_pv_forecast_forecast_today")
    tomorrow_sensor = self._hass.states.get("sensor.solcast_pv_forecast_forecast_tomorrow")

    if "bat_new_state" not in self._attr_extra_state_attributes:
        self._attr_extra_state_attributes["bat_new_state"] = [None] * 48

    if "bat_old_state" not in self._attr_extra_state_attributes:
        self._attr_extra_state_attributes["bat_old_state"] = [None] * 48

    # Výpočet aktuálního bat_new_state[index]
    bat_sensor = self._hass.states.get("sensor.battery_state_of_charge")
    dod_sensor = self._hass.states.get("number.depth_of_discharge_on_grid")

    if bat_sensor and dod_sensor:
        try:
            soc = float(bat_sensor.state)
            dod = float(dod_sensor.state)
            new_value = round((soc - dod) / 100 * 9.6, 2)
            self._attr_extra_state_attributes["bat_new_state"][index] = new_value
            _LOGGER.debug(f"bat_new_state[{index}] = {new_value} (SOC: {soc}, DOD: {dod})")
        except ValueError:
            _LOGGER.warning("Chyba při výpočtu bat_new_state")

    # Výpočet bat_old_state[index]
    bat_sensor_old = self._hass.states.get("sensor.battery_state_of_charge_2")
    dod_sensor_old = self._hass.states.get("number.depth_of_discharge_on_grid_2")

    if bat_sensor_old and dod_sensor_old:
        try:
            soc = float(bat_sensor_old.state)
            dod = float(dod_sensor_old.state)
            new_value = round((soc - dod) / 100 * 9.6, 2)
            self._attr_extra_state_attributes["bat_old_state"][index] = new_value
            _LOGGER.debug(f"bat_old_state[{index}] = {new_value} (SOC: {soc}, DOD: {dod})")
        except ValueError:
            _LOGGER.warning("Chyba při výpočtu bat_old_state")

    # Dummy stav senzoru
    self._state = 42.0

    # Atributy (pro jednoduchost zachovány)
    self._attr_extra_state_attributes["Today"] = (
        today_sensor.state if today_sensor else "unknown"
    )
    self._attr_extra_state_attributes["Tomorrow"] = (
        tomorrow_sensor.state if tomorrow_sensor else "unknown"
    )
    self._attr_extra_state_attributes["Cas"] = now.isoformat()
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

    # Forecast připravený jako seznam dictů
    forecast = [
        {"pv_estimate": 0.1 + 0.05 * (i % 5)} for i in range(48)  # náhrada za reálná data
    ]
    self._attr_extra_state_attributes["DetailedForecast"] = forecast

    bat = self._attr_extra_state_attributes["bat_new_state"]
    l1a2 = self._attr_extra_state_attributes["L1a2"]
    ohrev = self._attr_extra_state_attributes["Ohrev vody"]
    nabiji = self._attr_extra_state_attributes["Bat_Old_nabiji"]

    # Výpočet predikce pro další úseky
    for i in range(index + 1, 48):
        if bat[i - 1] is None:
            _LOGGER.debug(f"Přerušeno: bat[{i - 1}] je None")
            break

        try:
            spotreba = l1a2[i]
            ohrev_vody = ohrev[i] if nabiji[i] == 0 else 0
            vyroba = forecast[i].get("pv_estimate", 0.0)

            bat[i] = round(bat[i - 1] - spotreba - ohrev_vody + vyroba, 2)

            _LOGGER.debug(
                f"bat[{i}] = bat[{i - 1}] ({bat[i - 1]}) - spotreba({spotreba}) "
                f"- ohrev({ohrev_vody}) + vyroba({vyroba}) = {bat[i]}"
            )
        except (IndexError, TypeError, ValueError) as e:
            _LOGGER.warning(f"Chyba při výpočtu bat[{i}]: {e}")
            break

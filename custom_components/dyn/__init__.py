# Init file for dyn custom component
def __init__(self, hass, name):
    self._hass = hass
    self._name = name
    self._state = None
    self._attr_extra_state_attributes = {}

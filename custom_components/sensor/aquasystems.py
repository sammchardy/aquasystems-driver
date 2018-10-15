"""
Support for MQTT room presence detection.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.mqtt_room/
"""
import logging

import voluptuous as vol

from custom_components.aquasystems import (
    AquaTimerSensor, ATTR_STATUS, DEVICE_MAP)

import homeassistant.helpers.config_validation as cv
from homeassistant.components.sensor import PLATFORM_SCHEMA
from homeassistant.const import (
    CONF_NAME, CONF_SENSOR_TYPE)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['aquasystems']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_SENSOR_TYPE, default=ATTR_STATUS): vol.In(DEVICE_MAP)
})


async def async_setup_platform(hass, config, async_add_entities,
                               discovery_info=None):
    """Set up MQTT room Sensor."""
    async_add_entities([AquaTimerSensor(
        config.get(CONF_NAME),
        config.get(CONF_SENSOR_TYPE),
    )])


"""
class AquaTimerEntity(AquaTimerSensor):
    ""Representation of an Aqua Systems BlueTooth Timer updated via MQTT.""

    pass
"""
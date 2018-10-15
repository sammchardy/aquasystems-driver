"""
Support for MQTT room presence detection.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.mqtt_room/
"""
import logging
import json

import voluptuous as vol

from homeassistant.components import mqtt
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.dispatcher import (
    async_dispatcher_connect, dispatcher_send)
from homeassistant.components.mqtt import CONF_STATE_TOPIC, CONF_COMMAND_TOPIC
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = ['mqtt']

DATA_AQUASYSTEMS = 'aquasystems'
DOMAIN = 'aquasystems'

DEFAULT_NAME = 'Aqua Timer'
DEFAULT_TOPIC = '$SYS/broker/aquatimer/info'
DEFAULT_COMMAND_TOPIC = '$SYS/broker/aquatimer/command'

SIGNAL_UPDATE_AQUASYSTEMS = 'aquasystems_update'

ATTR_BATTERY = 'battery'
ATTR_ON = 'on'
ATTR_STATUS = 'status'
ATTR_TIME = 'time'
ATTR_CYCLE1_START = 'cycle1_start'
ATTR_CYCLE2_START = 'cycle2_start'
ATTR_CYCLE_DUR = 'cycle_duration'
ATTR_CYCLE_FREQ = 'cycle_frequency'
ATTR_MANUAL_TIME_LEFT = 'manual_time_left'
ATTR_RAIN_DELAY_TIME = 'rain_delay_time'

STATUS_OFF = 1
STATUS_ON = 2
STATUS_MANUAL = 10
STATUS_CHOICES = {
    STATUS_OFF: 'Off',
    STATUS_ON: 'On',
    STATUS_MANUAL: 'Manual'
}

DEVICE_MAP_INDEX = ['KEY_INDEX', 'ICON_INDEX', 'UNIT_OF_MEASURE_INDEX']
DEVICE_MAP = {
    ATTR_BATTERY: ['Battery', 'mdi:battery', '%'],
    ATTR_ON: ['On/Off', 'mdi:power', ''],
    ATTR_STATUS: ['Status', {STATUS_OFF: 'mdi:sync-off', STATUS_ON: 'mdi:autorenew', STATUS_MANUAL: 'mdi:hand'}, ''],
    ATTR_TIME: ['Time', 'mdi:clock-outline', ''],
    ATTR_CYCLE1_START: ['Cycle1 Start', 'mdi:clock-start', ''],
    ATTR_CYCLE2_START: ['Cycle2 Start', 'mdi:clock-start', ''],
    ATTR_CYCLE_DUR: ['Duration', 'mdi:timer', 'mins'],
    ATTR_CYCLE_FREQ: ['Frequency', 'mdi:calendar-clock', 'days'],
    ATTR_MANUAL_TIME_LEFT: ['Manual Time', 'mdi:account', 'mins'],
    ATTR_RAIN_DELAY_TIME: ['Rain Delay', 'mdi:lock-clock', 'days'],
}

UPDATE_PAYLOAD = json.dumps({
    'cmd': 'get',
    'item': 'all'
})

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_STATE_TOPIC, default=DEFAULT_TOPIC): cv.string,
        vol.Required(CONF_COMMAND_TOPIC, default=DEFAULT_COMMAND_TOPIC): cv.string,
    }),
}, extra=vol.ALLOW_EXTRA)


MQTT_PAYLOAD = vol.Schema(vol.All(json.loads, vol.Schema({
    vol.Required(ATTR_BATTERY): cv.positive_int,
    vol.Required(ATTR_ON): vol.Coerce(bool),
    vol.Required(ATTR_STATUS): cv.positive_int,
    vol.Required(ATTR_TIME): vol.All(cv.ensure_list, [cv.positive_int]),
    vol.Required(ATTR_CYCLE1_START): vol.All(cv.ensure_list, [cv.positive_int]),
    vol.Required(ATTR_CYCLE2_START): vol.All(cv.ensure_list, [cv.positive_int]),
    vol.Required(ATTR_CYCLE_DUR): cv.positive_int,
    vol.Required(ATTR_CYCLE_FREQ): cv.positive_int,
    vol.Required(ATTR_MANUAL_TIME_LEFT): cv.positive_int,
    vol.Required(ATTR_RAIN_DELAY_TIME): cv.positive_int,
}, extra=vol.ALLOW_EXTRA)))


async def async_setup(hass, config):

    conf = config[DOMAIN]
    hass.data[DATA_AQUASYSTEMS] = {}

    async def message_received(topic, payload, qos):
        """Handle new MQTT messages."""
        _LOGGER.info("aquasystems payload {}".format(payload))
        try:
            data = MQTT_PAYLOAD(payload)
            hass.data[DATA_AQUASYSTEMS] = data
            dispatcher_send(hass, SIGNAL_UPDATE_AQUASYSTEMS)
        except vol.MultipleInvalid as error:
            _LOGGER.debug(
                "Skipping update because of malformatted data: %s", error)
            return

    await mqtt.async_subscribe(
        hass,
        conf[CONF_STATE_TOPIC],
        message_received,
        1
    )

    return True


class AquaTimerSensor(Entity):
    """Representation of an Aqua Systems BlueTooth Timer updated via MQTT."""

    def __init__(self, name, sensor_type):
        """Initialize the sensor."""
        self._state = None
        self._name = name
        self._sensor_type = sensor_type

    @property
    def name(self):
        """Return the name of the sensor."""
        return self._name

    @property
    def state(self):
        """Return the state of the sensor."""
        if self._state is None:
            return None

        if self._sensor_type in [ATTR_CYCLE1_START, ATTR_CYCLE2_START, ATTR_TIME]:
            if self._state[0] == 255:
                return "Disabled"
            return '{:02d}:{:02d}'.format(self._state[0], self._state[1])
        elif self._sensor_type == ATTR_STATUS:
            return STATUS_CHOICES[self._state]

        return self._state

    async def async_update(self):
        data = self.hass.data[DATA_AQUASYSTEMS]
        _LOGGER.info("data {}".format(data))
        if self._sensor_type in data:
            self._state = data[self._sensor_type]

    async def async_added_to_hass(self):
        """Register callbacks."""
        async_dispatcher_connect(
            self.hass, SIGNAL_UPDATE_AQUASYSTEMS, self._update_callback)

    async def _update_callback(self):
        """Call update method."""
        self.async_schedule_update_ha_state(True)

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        _LOGGER.info("icon for {}".format(self._sensor_type))
        if self._sensor_type == ATTR_STATUS:
            if not self._state:
                return None
            return DEVICE_MAP[self._sensor_type][DEVICE_MAP_INDEX.index('ICON_INDEX')][self._state]
        else:
            return DEVICE_MAP[self._sensor_type][DEVICE_MAP_INDEX.index('ICON_INDEX')]

    @property
    def unit_of_measurement(self):
        """Return the units of measurement."""
        return DEVICE_MAP[self._sensor_type][DEVICE_MAP_INDEX.index('UNIT_OF_MEASURE_INDEX')]

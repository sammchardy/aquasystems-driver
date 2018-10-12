import uuid

from Adafruit_BluefruitLE.services.servicebase import ServiceBase

# Define service and characteristic UUIDs.
TIMER_SERVICE_UUID = uuid.UUID('0000FCC0-0000-1000-8000-00805F9B34FB')
BATTERY_SERVICE_UUID = uuid.UUID('0000180f-0000-1000-8000-00805f9b34fb')
BATTERY_CHAR_UUID = uuid.UUID('00002a19-0000-1000-8000-00805f9b34fb')

TIMER_OFF_CHAR_UUID = uuid.UUID('0000fcc2-0000-1000-8000-00805f9b34fb')

TIME_CHAR_UUID = uuid.UUID('0000fcc4-0000-1000-8000-00805f9b34fb')

STATUS_CHAR_UUID = uuid.UUID('0000fcd1-0000-1000-8000-00805f9b34fb')
CYCLE1_DUR_CHAR_UUID = uuid.UUID('0000fcd2-0000-1000-8000-00805f9b34fb')
DAY_CYCLE_CHAR_UUID = uuid.UUID('0000fcd3-0000-1000-8000-00805f9b34fb')
START_TIME1_CHAR_UUID = uuid.UUID('0000fcd4-0000-1000-8000-00805f9b34fb')
START_TIME2_CHAR_UUID = uuid.UUID('0000fcd5-0000-1000-8000-00805f9b34fb')
RAIN_DELAY_TIME_CHAR_UUID = uuid.UUID('0000fcd6-0000-1000-8000-00805f9b34fb')
MANUAL_TIME_CHAR_UUID = uuid.UUID('0000fcd9-0000-1000-8000-00805f9b34fb')

# Not Implemented
# TIMER1_CHAR_UUID = uuid.UUID('0000fcc1-0000-1000-8000-00805f9b34fb')


class TimerService(ServiceBase):
    """Bluetooth LE Aqua Systems water timer service object."""

    ATTRIBUTES = {
        'battery': {  # NOTIFY, READ
            'service': 'battery',
            'uuid': BATTERY_CHAR_UUID,
            'format': [  # '5'
                'value'
            ],
            'can_set': False,
            'can_notify': True
        },
        'on': {  # READ
            'service': 'timer',
            'uuid': TIMER_ON_CHAR_UUID,
            'format': [  # 'R\x01\x01'
                82,
                1,
                'on'
            ],
            'can_set': False,
            'can_notify': False
        },
        'status': {  # NOTIFY, READ
            # 'a\x01\x01' - off
            # 'a\x01\x02' - auto
            # 'a\x01\t'  - 9 (manual)
            'service': 'timer',
            'uuid': STATUS_CHAR_UUID,
            'format': [
                97,
                1,
                'status'
            ],
            'can_set': False,
            'can_notify': True
        },
        'time': {  # READ, WRITE
            'service': 'timer',
            'uuid': TIME_CHAR_UUID,
            'format': [  # 'T\x04\x15\x17\x04\x04'
                84,
                4,
                'hours',
                'minutes',
                'seconds',
                4
            ],
            'can_set': True,
            'can_notify': False
        },
        'cycle1_start': {  # READ, WRITE
            'service': 'timer',
            'uuid': START_TIME1_CHAR_UUID,
            'format': [  # 'd\x02\x05\x1e'
                100,
                2,
                'hours',
                'mins'
            ],
            'can_set': True,
            'can_notify': False
        },
        'cycle2_start': {  # READ, WRITE
            'service': 'timer',
            'uuid': START_TIME2_CHAR_UUID,
            'format': [  # 'e\x02\x05\x1e'
                101,
                2,
                'hours',
                'mins'
            ],
            'can_set': True,
            'can_notify': False
        },
        'cycle_duration': {  # NOTIFY, READ, WRITE
            'service': 'timer',
            'uuid': CYCLE1_DUR_CHAR_UUID,
            'format': [  # 'b\x02\x00\x1d'
                98,
                2,
                0,
                'duration'
            ],
            'can_set': True,
            'can_notify': True
        },
        'cycle_frequency': {  # READ, WRITE
            'service': 'timer',
            'uuid': DAY_CYCLE_CHAR_UUID,
            'format': [  # 'c\x03\x00\x04\x7f' - 4 days
                99,
                3,
                0,
                'days',
                127
            ],
            'can_set': True,
            'can_notify': False
        },
        'manual_time_left': {  # NOTIFY, READ, WRITE
            # 'i\x03\x00\x00\x05' - off
            # 'i\x03\x01\x00\x05' - on 5 mins
            # 'i\x03\x01\x00\n' - on 10 mins
            # 'i\x03\x01\x00\t' - on 9 min
            'service': 'timer',
            'uuid': MANUAL_TIME_CHAR_UUID,
            'format': [
                105,
                3,
                'status',
                0,
                'duration'
            ],
            'can_set': True,
            'can_notify': True
        },
        'rain_delay_time': {  # NOTIFY, READ, WRITE
            'service': 'timer',
            'uuid': RAIN_DELAY_TIME_CHAR_UUID,
            'format': [  # 'f\x01\x00'
                102,
                1,
                'duration'
            ],
            'can_set': True,
            'can_notify': True
        }
    }

    # Configure expected services and characteristics for the UART service.
    ADVERTISED = [TIMER_SERVICE_UUID]
    SERVICES = [TIMER_SERVICE_UUID, BATTERY_SERVICE_UUID]
    CHARACTERISTICS = [CYCLE1_DUR_CHAR_UUID, TIME_CHAR_UUID]

    def __init__(self, device):
        """Initialize Timer from provided bluez device."""
        self.device = device
        # Find the Timer service and characteristics associated with the device.
        self._timer = self.device.find_service(TIMER_SERVICE_UUID)
        self._battery = self.device.find_service(BATTERY_SERVICE_UUID)
        if self._timer is None:
            raise RuntimeError('Failed to find expected Timer service!')
        if self._battery is None:
            raise RuntimeError('Failed to find expected Battery service!')

    def __getattr__(self, item):
        # lookup attribute in array
        if item not in self.ATTRIBUTES:
            # check if item is set
            if item in self.__dict__:
                return self.__dict__[item]
            else:
                return None

        # get attribute details from array
        attr = self.ATTRIBUTES[item]

        # init service and characteristic
        characteristic = self._get_characteristic(attr['service'], attr['uuid'])
        # read the value
        val = characteristic.read_value()

        results = []
        idx = 0
        for el in attr['format']:
            # save result if it's not a placeholder char
            if type(el) == str:
                results.append(val[idx])
            idx += 1

        # if we only have one result return that, otherwise return list
        if len(results) == 1:
            return results[0]
        return results

    def __setattr__(self, item, value):
        # lookup attribute in array
        if item not in self.ATTRIBUTES:
            # if not found find in class dict
            self.__dict__[item] = value
            return

        # get attribute details from array
        attr = self.ATTRIBUTES[item]

        # ignore if we can't actually set this attribute
        if not attr['can_set']:
            return False

        return self._write_attr(attr, value)

    def _write_attr(self, attr, value):
        """

        :param attr:
        :param value:
        :return:
        """
        # convert to list for ease
        if type(value) != list:
            value = [value]

        # build the required format
        idx = 0
        byte_val = bytearray()
        for el in attr['format']:
            if type(el) == int:
                # add char items as is
                byte_val.append(el)
            else:
                # add properties from the value list passed
                byte_val.append(value[idx])
                idx += 1

        # init service and characteristic
        characteristic = self._get_characteristic(attr['service'], attr['uuid'])
        # write the value
        return characteristic.write_value(byte_val)

    def _get_characteristic(self, service, uuid):
        """Find a characteristic for a service from the uuid

        """
        s = getattr(self, '_{}'.format(service))
        return s.find_characteristic(uuid)

    @property
    def on(self):
        # use getattr helper
        val = self.__getattr__('on')
        if val == 1:
            return True
        return False

    @property
    def manual_time_left(self):
        """
        'i\x03\x00\x00\x05' - off
        'i\x03\x01\x00\x05' - on 5 mins
        'i\x03\x01\x00\n' - on 10 mins
        'i\x03\x01\x00\t' - on 9 min
        :return:
        """
        # use getattr helper
        val = self.__getattr__('manual_time_left')

        # check if manual mode is turned on
        if val[0] == 1:
            return val[1]
        return 0

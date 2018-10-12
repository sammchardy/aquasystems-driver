# Bluetooth LE UART service class.  Provides an easy to use interface to read
# and write data from a bluezle device that implements the UART service.
# Author: Tony DiCola
#
# Copyright (c) 2015 Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import queue
import uuid
import sys

from Adafruit_BluefruitLE.services.servicebase import ServiceBase


# Define service and characteristic UUIDs.
TIMER_SERVICE_UUID = uuid.UUID('0000FCC0-0000-1000-8000-00805F9B34FB')
BATTERY_SERVICE_UUID = uuid.UUID('0000180f-0000-1000-8000-00805f9b34fb')
TX_CHAR_UUID = uuid.UUID('6E400002-B5A3-F393-E0A9-E50E24DCCA9E')
RX_CHAR_UUID = uuid.UUID('6E400003-B5A3-F393-E0A9-E50E24DCCA9E')
BATTERY_CHAR_UUID = uuid.UUID('00002a19-0000-1000-8000-00805f9b34fb')

TIMER1_CHAR_UUID = uuid.UUID('0000fcc1-0000-1000-8000-00805f9b34fb')
TIMER_OFF1_CHAR_UUID = uuid.UUID('0000fcc2-0000-1000-8000-00805f9b34fb')

TIME_CHAR_UUID = uuid.UUID('0000fcc4-0000-1000-8000-00805f9b34fb')

STATUS1_CHAR_UUID = uuid.UUID('0000fcd1-0000-1000-8000-00805f9b34fb')
DUR1_CHAR_UUID = uuid.UUID('0000fcd2-0000-1000-8000-00805f9b34fb')
DAY_CYCLE1_CHAR_UUID = uuid.UUID('0000fcd3-0000-1000-8000-00805f9b34fb')
TIME1_CHAR_UUID = uuid.UUID('0000fcd4-0000-1000-8000-00805f9b34fb')
RAIN_DELAY1_CHAR_UUID = uuid.UUID('0000fcd6-0000-1000-8000-00805f9b34fb')

MANUAL_TIME1_CHAR_UUID = uuid.UUID('0000fcd9-0000-1000-8000-00805f9b34fb')

"""
0000fcd1-0000-1000-8000-00805f9b34fb

b'a\x01\x01' - off
b'a\x01\x02' - auto
b'a\x01\t'  - 9 (manual) ?

 0000fcd6-0000-1000-8000-00805f9b34fb - 
 
 Rain Delay in days
 
 b'f\x01\x03'

b'T\x04\x13/\x1b\x04'

 """


class Timer(ServiceBase):
    """Bluetooth LE UART service object."""

    # Configure expected services and characteristics for the UART service.
    ADVERTISED = [TIMER_SERVICE_UUID]
    SERVICES = [TIMER_SERVICE_UUID, BATTERY_SERVICE_UUID]
    CHARACTERISTICS = [DUR1_CHAR_UUID, TIME1_CHAR_UUID]

    def __init__(self, device):
        """Initialize Timer from provided bluez device."""
        self.device = device
        # Find the Timer service and characteristics associated with the device.
        self._timer = device.find_service(TIMER_SERVICE_UUID)
        self._battery = self.device.find_service(BATTERY_SERVICE_UUID)
        if self._timer is None:
            raise RuntimeError('Failed to find expected Timer service!')
        if self._battery is None:
            raise RuntimeError('Failed to find expected Battery service!')

        """
        self._tx = self._timer.find_characteristic(TX_CHAR_UUID)
        self._rx = self._timer.find_characteristic(RX_CHAR_UUID)
        if self._tx is None or self._rx is None:
            raise RuntimeError('Failed to find expected UART RX and TX characteristics!')
        # Use a queue to pass data received from the RX property change back to
        # the main thread in a thread-safe way.
        self._queue = queue.Queue()
        # Subscribe to RX characteristic changes to receive data.
        self._rx.start_notify(self._rx_received)
        """

    @property
    def battery_level(self):
        """Find the battery level as decimal

        :return:
        """
        battery_char = self._battery.find_characteristic(BATTERY_CHAR_UUID)
        return int.from_bytes(battery_char.read_value(), byteorder=sys.byteorder)

    @property
    def time(self):
        val = self._read_timer_char(TIME_CHAR_UUID)
        return "{:02d}:{:02d}:{:02d}".format(val[2], val[3], val[4])

    @time.setter
    def time(self, hours, mins, secs):
        """
        b'd\x02\x05\x00'
        :param val:
        :return:
        """
        # convert to correct format
        byte_val = bytearray(b'T\x04')
        byte_val.append(hours)
        byte_val.append(mins)
        byte_val.append(secs)
        byte_val = bytearray(b'\x04')

        # write to device
        self._write_timer_char(TIME_CHAR_UUID, byte_val)

    @property
    def timer1(self):
        val = self._read_timer_char(TIMER1_CHAR_UUID)
        return val

    @property
    def is_off1(self):
        val = self._read_timer_char(TIMER_OFF1_CHAR_UUID)
        val = bytes(val)
        val = val.replace(b'R\x01', b'')
        val = int.from_bytes(val, byteorder=sys.byteorder)
        if val == 0:
            return True
        return False

    @property
    def status1(self):
        val = self._read_timer_char(STATUS1_CHAR_UUID)
        val = bytes(val)
        val = val.replace(b'b\x02\x00', b'')
        return int.from_bytes(val, byteorder=sys.byteorder)

    @property
    def manual_time_left1(self):
        """
        b'i\x03\x00\x00\x05' - off
        b'i\x03\x01\x00\x05' - on 5 mins
        b'i\x03\x01\x00\n' - on 10 mins
        b'i\x03\x01\x00\t' - on 9 min
        :return:
        """
        val = self._read_timer_char(MANUAL_TIME1_CHAR_UUID)
        # check if manual mode is turned on
        if val[2] == 1:
            return val[4]
        return 0

    @property
    def duration_timer1(self):
        """
        b'b\x02\x00\x1d'

        :return:
        """
        val = self._read_timer_char(DUR1_CHAR_UUID)
        return val[3]

    @duration_timer1.setter
    def duration_timer1(self, val):
        """
        b'b\x02\x00\x1d'
        :param val:
        :return:
        """
        # convert to correct format
        byte_val = bytearray(b'b\x02\x00')
        byte_val.append(val)

        # write to device
        self._write_timer_char(DUR1_CHAR_UUID, byte_val)

    @property
    def time_timer1(self):
        val = self._read_timer_char(TIME1_CHAR_UUID)
        return "{:02d}:{:02d}".format(val[2], val[3])

    @time_timer1.setter
    def time_timer1(self, hours=None, minutes=None):
        """

        :param hours:
        :param minutes:
        :return:
        """
        # convert to correct format
        byte_val = bytearray(b'd\x02')
        if not hours:
            hours = b'\xff'
            minutes = b'\xff'
        byte_val.append(hours)
        byte_val.append(minutes)

        # write to device
        self._write_timer_char(TIME1_CHAR_UUID, byte_val)

    @property
    def cycle_timer1(self):
        """

        Timer 1 Cycle

        b'c\x03\x00\x01\x7f' - 1 days
        b'c\x03\x00\x04\x7f' - 4 days

        :return:
        """
        val = self._read_timer_char(DAY_CYCLE1_CHAR_UUID)
        val = bytes(val)
        return val[3]

    @cycle_timer1.setter
    def cycle_timer1(self, days):
        """

        :param days:
        :return:
        """
        # convert to correct format
        byte_val = bytearray(b'c\x03\x00')
        byte_val.append(days)
        byte_val.append(b'\x7f')

        # write to device
        self._write_timer_char(DAY_CYCLE1_CHAR_UUID, byte_val)

    @property
    def rain_delay_timer1(self):
        """

         Rain Delay in days

         b'f\x01\x03'

        :return:
        """
        val = self._read_timer_char(RAIN_DELAY1_CHAR_UUID)
        val = bytes(val)
        return val[2]

    @rain_delay_timer1.setter
    def rain_delay_timer1(self, days):
        """

        :param days:
        :return:
        """
        # convert to correct format

        byte_val = bytearray(b'f\x01')
        byte_val.append(days)

        # write to device
        self._write_timer_char(RAIN_DELAY1_CHAR_UUID, byte_val)

    def _read_timer_char(self, uuid):
        """
        Read a specified UUID from the device

        :param uuid:
        :return:
        """
        char = self._timer.find_characteristic(uuid)
        return char.read_value()

    def _write_timer_char(self, uuid, value):
        """
        Write a value to the specified UUID on the device

        :param uuid:
        :param value:
        :return:
        """
        char = self._timer.find_characteristic(uuid)
        return char.write_value(value)

    def _rx_received(self, data):
        # Callback that's called when data is received on the RX characteristic.
        # Just throw the new data in the queue so the read function can access
        # it on the main thread.
        self._queue.put(data)

    def write(self, data):
        """Write a string of data to the UART device."""
        self._tx.write_value(data)

    def read(self, timeout_sec=None):
        """Block until data is available to read from the UART.  Will return a
        string of data that has been received.  Timeout_sec specifies how many
        seconds to wait for data to be available and will block forever if None
        (the default).  If the timeout is exceeded and no data is found then
        None is returned.
        """
        try:
            return self._queue.get(timeout=timeout_sec)
        except queue.Empty:
            # Timeout exceeded, return None to signify no data received.
            return None

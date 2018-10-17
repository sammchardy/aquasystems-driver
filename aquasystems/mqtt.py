import asyncio
import json
import logging
import Adafruit_BluefruitLE

from .timer import TimerService
from hbmqtt.client import MQTTClient
from hbmqtt.mqtt.constants import QOS_1

ble = Adafruit_BluefruitLE.get_provider()  # Get the BLE provider for the current platform.


class TimerMqttService:
    """MQTT Service for Bluetooth LE Aqua Systems water timer

    """

    COMMAND_TOPIC = '$SYS/broker/aquatimer/command'
    INFO_TOPIC = '$SYS/broker/aquatimer/info'
    BATTERY_TOPIC = '$SYS/broker/aquatimer/battery'

    # Dictionary for any attribute specific topics
    ATTR_TOPICS = {
        'battery': BATTERY_TOPIC
    }

    device_connect_timeout = 10  # seconds
    battery_notify_interval = 1  # minutes

    def __init__(self, mqtt_url, device_name):

        self.logger = logging.getLogger(__name__)
        self.running = True
        self.device = None
        self.timer_service = None
        self.mqtt_url = mqtt_url
        self.mqtt_client = MQTTClient()
        self.device_name = device_name
        self.loop = asyncio.get_event_loop()

        self.command_queue = asyncio.Queue(loop=self.loop)

        ble.run_mainloop_with(self.run)

    def run(self):
        # Initialize the BLE system.  MUST be called before other BLE calls!
        ble.initialize()

        try:
            # Clear any cached data because both bluez and CoreBluetooth have issues with
            # caching data and it going stale.
            ble.clear_cached_data()

            # Get the first available BLE network adapter and make sure it's powered on.
            adapter = ble.get_default_adapter()
            adapter.power_on()
            self.logger.debug('Using adapter: {0}'.format(adapter.name))

            # Disconnect any currently connected UART devices.  Good for cleaning up and
            # starting from a fresh state.
            self.logger.debug('Disconnecting any connected Timer devices...')
            TimerService.disconnect_devices()
        except Exception as e:
            self.logger.error("got error: {}".format(e))
            return None

        # Scan for device
        self.logger.debug('Searching for Timer device...')
        try:
            adapter.start_scan()
            # Search for the first UART device found (will time out after 60 seconds
            # but you can specify an optional timeout_sec parameter to change it).
            self.device = ble.find_device(name=self.device_name)
            if self.device is None:
                raise RuntimeError('Failed to find Timer device!')
        finally:
            # Make sure scanning is stopped before exiting.
            adapter.stop_scan()

        self.logger.debug('Connecting to device...')
        self.device.connect()

        try:
            self.logger.debug('Discovering services...')
            TimerService.discover(self.device)

            self.logger.debug('Creating device')
            self.timer_service = TimerService(self.device)
        except Exception as e:
            self.logger.error("got error: {}".format(e))

        # now do things
        self._run_mqtt()

    def stop(self):
        """Stop the service

        """
        self.running = False

    async def process_command(self, command):
        """Process a command

        :param command:
        :return:
        """
        self.logger.debug("processing command: {}".format(command))

        try:
            if not self.timer_service:
                self.logger.debug("No device found")
                return

            if command['cmd'] == 'set':
                setattr(self.timer_service, command['item'], command['value'])
                # make sure we push an update
                data = {'cmd': 'get', 'item': 'all'}
                await self.command_queue.put(data)
            elif command['cmd'] == 'get':
                await self.publish_item(command['item'])
        except Exception as e:
            self.logger.error('publish error: {}'.format(e))

    async def publish_item(self, item):
        """Publish an item to the relevant item topic or info topic as fallback

        :param item:
        :return:
        """

        topic = TimerMqttService.INFO_TOPIC
        if item == 'all':
            # check if we want the all attributes
            payload = self.timer_service.all
        else:
            # otherwise just return one attribute
            payload = {
                item: getattr(self.timer_service, item)
            }
            # check if we need to send to a specific topic
            if item in TimerMqttService.ATTR_TOPICS:
                topic = TimerMqttService.ATTR_TOPICS[item]
        self.logger.debug("publishing payload:{}".format(payload))
        await self.mqtt_client.publish(
            topic,
            json.dumps(payload).encode("utf-8"),
            qos=QOS_1
        )

    async def _producer(self):
        # connect MQTT client
        await self.mqtt_client.connect(self.mqtt_url)
        await self.mqtt_client.subscribe([
            (TimerMqttService.COMMAND_TOPIC, QOS_1),
        ])
        while self.running:
            try:
                # wait for incoming MQTT messages
                msg = await self.mqtt_client.deliver_message()
                self.logger.debug('topic: {} payload: {}'.format(
                    msg.publish_packet.variable_header.topic_name,
                    msg.publish_packet.payload.data
                ))
                if msg.publish_packet.variable_header.topic_name == TimerMqttService.COMMAND_TOPIC:
                    # process if on the command topic
                    await asyncio.sleep(0)
                    data = json.loads(msg.publish_packet.payload.data.decode('utf-8'))
                    self.logger.debug("mqtt packet: {}".format(data))
                    await self.command_queue.put(data)
            except:
                pass

    async def _consumer(self):
        self.logger.debug("start consumer")
        while self.running:
            self.logger.debug("waiting for queue item")
            # wait for incoming queue items
            item = await self.command_queue.get()
            self.logger.debug("got queue item: {}".format(item))

            await self.process_command(item)

            self.command_queue.task_done()

    async def _battery_notify(self):
        """Start the loop to notify MQTT of Battery level

        :return:
        """
        # wait a few seconds before starting
        await asyncio.sleep(5)
        self.logger.debug("start battery notify")
        while self.running:
            await asyncio.sleep(0)
            data = {'cmd': 'get', 'item': 'battery'}
            await self.command_queue.put(data)

            # wait for 10 minutes
            await asyncio.sleep(60 * self.battery_notify_interval)

    async def _all_notify(self):
        """Start the loop to notify MQTT of All details

        :return:
        """
        # wait a few seconds before starting
        await asyncio.sleep(5)
        self.logger.debug("start all notify")
        while self.running:
            await asyncio.sleep(0)
            data = {'cmd': 'get', 'item': 'all'}
            await self.command_queue.put(data)

            # wait for 10 minutes
            await asyncio.sleep(60 * self.battery_notify_interval)

    def _disconnect_timer_service(self):
        if self.device:
            self.device.disconnect()

    def _run_mqtt(self):
        """Start MQTT service and other notify loops

        :return:
        """

        cors = asyncio.wait([
            self._consumer(),
            self._producer(),
            self._all_notify(),
            self._battery_notify()
        ])
        self.loop.run_until_complete(cors)

import asyncio
import json
import logging

from .timer import Timer
from hbmqtt.client import MQTTClient, ClientException
from hbmqtt.mqtt.constants import QOS_1, QOS_2


class TimerMqttService:
    """MQTT Service for

    """

    COMMAND_TOPIC = '$SYS/broker/timer/command'

    def __init__(self, mqtt_url, device_name):

        self.logger = logging.getLogger(__name__)
        self.running = True
        self.mqtt_url = mqtt_url
        self.mqtt_client = MQTTClient()
        self.device_name = device_name
        self.loop = asyncio.get_event_loop()
        self.command_queue = asyncio.Queue(loop=self.loop)

        self.run()

    async def process_command(self, command):
        """Process a command

        :param command:
        :return:
        """
        self.logger.debug("processing command: {}".format(command))

    async def _producer(self, q):
        self.logger.debug("start producer")
        # connect MQTT client
        #TODO: check if mqtt running if not self._mqtt:
        await self.mqtt_client.connect(self.mqtt_url)
        await self.mqtt_client.subscribe([
            (TimerMqttService.COMMAND_TOPIC, QOS_1),
        ])
        while self.running:
            try:
                msg = await self.mqtt_client.deliver_message()
                self.logger.debug('topic: {} payload: {}'.format(
                    msg.publish_packet.variable_header.topic_name,
                    msg.publish_packet.payload.data
                ))
                if msg.publish_packet.variable_header.topic_name == TimerMqttService.COMMAND_TOPIC:
                    await asyncio.sleep(0)
                    data = json.dumps(json.loads(msg.publish_packet.payload.data.decode('utf-8')))
                    self.logger.debug("data: {}".format(data))
                    await self.command_queue.put(data)
                    self.logger.debug("pushing data to the queue size is {}".format(self.command_queue.qsize()))
            except:
                pass

    async def _consumer(self, q):
        self.logger.debug("start consumer")
        while self.running:
            self.logger.debug("waiting for queue item")
            item = await self.command_queue.get()
            self.logger.debug("got queue item: {}".format(item))

            await self.process_command(item)

            self.command_queue.task_done()

    def run(self):

        cors = asyncio.wait([self._consumer(self.command_queue), self._producer(self.command_queue)])
        self.loop.run_until_complete(cors)

    def stop(self):
        self.running = False

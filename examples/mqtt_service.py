import argparse
import logging

from aquasystems.mqtt import TimerMqttService

# setup logging
logging.basicConfig()
log = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.DEBUG)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Run an automated trading bot.')
    parser.add_argument('--device_id', help='ID of Tap Timer device e.g "Spray-Mist A19E"', default="Spray-Mist A19E")
    parser.add_argument('--broker_url', help='URL for MQTT broker', default="mqtt://127.0.0.1")
    args = parser.parse_args()

    # run MQTT service
    tms = TimerMqttService(args.broker_url, args.device_id)

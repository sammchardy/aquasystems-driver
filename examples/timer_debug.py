import Adafruit_BluefruitLE
import argparse
from Adafruit_BluefruitLE.services import DeviceInformation
from aquasystems.timer import TimerService

import logging

# setup logging
logging.basicConfig()
log = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.DEBUG)

device_name = "Spray-Mist A19E"


# Get the BLE provider for the current platform.
ble = Adafruit_BluefruitLE.get_provider()


def bytes_to_str(b):
    """Break bytes apart and output individually

    :param b:
    :return:
    """
    return '-'.join(str(a) for a in b)


def main():
    # Clear any cached data because both bluez and CoreBluetooth have issues with
    # caching data and it going stale.
    ble.clear_cached_data()

    # Get the first available BLE network adapter and make sure it's powered on.
    adapter = ble.get_default_adapter()
    adapter.power_on()
    print('Using adapter: {0}'.format(adapter.name))

    # Disconnect any currently connected UART devices.  Good for cleaning up and
    # starting from a fresh state.
    print('Disconnecting any connected Timer devices...')
    TimerService.disconnect_devices()

    # Scan for UART devices.
    print('Searching for Timer device...')
    try:
        adapter.start_scan()
        # Search for the first UART device found (will time out after 60 seconds
        # but you can specify an optional timeout_sec parameter to change it).
        device = ble.find_device(name=device_name)
        if device is None:
            raise RuntimeError('Failed to find Timer device!')
    finally:
        # Make sure scanning is stopped before exiting.
        adapter.stop_scan()
        pass

    print('Connecting to device...')
    device.connect()  # Will time out after 60 seconds, specify timeout_sec parameter
                      # to change the timeout.

    # Once connected do everything else in a try/finally to make sure the device
    # is disconnected when done.
    # Wait for service discovery to complete for the DIS service.  Will
    # time out after 60 seconds (specify timeout_sec parameter to override).
    try:
        print('Discovering services...')
        DeviceInformation.discover(device)

        # Once service discovery is complete create an instance of the service
        # and start interacting with it.
        dis = DeviceInformation(device)

        # Print out the DIS characteristics.
        print('Manufacturer: {}'.format(dis.manufacturer))
        print('Model: {}'.format(dis.model))
        print('Serial: {}'.format(dis.serial))
        print('Hardware Revision: {}'.format(dis.hw_revision))
        print('Software Revision: {}'.format(dis.sw_revision))
        print('Firmware Revision: {}'.format(dis.fw_revision))
        print('System ID: {}'.format(dis.system_id))
        print('Regulatory Cert: {}'.format(dis.regulatory_cert))
        print('PnP ID: {}'.format(dis.pnp_id))
        print('RSSI: {}'.format(device.rssi))

        # loop through services
        for service in device.list_services():
            print("")
            print("Service: {}".format(service.uuid))
            print("Characteristics:")
            for char in service.list_characteristics():
                val = char.read_value()
                print(" {} - {} - {}".format(char.uuid, val, bytes_to_str(val)))
                """
                print(" Descriptors:")
                for desc in char.list_descriptors():
                    try:
                        print("   {} - {}".format(desc.uuid, desc.read_value()))
                    except AttributeError as e:
                        print("   {} - not readable".format(desc.uuid))
                """
    finally:
        # Make sure device is disconnected on exit.
        device.disconnect()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Debug the device.')
    parser.add_argument('--device_id', help='ID of Tap Timer device e.g "Spray-Mist A19E"', default="Spray-Mist A19E")
    args = parser.parse_args()

    # Initialize the BLE system.  MUST be called before other BLE calls!
    ble.initialize()

    # Start the mainloop to process BLE events, and run the provided function in
    # a background thread.  When the provided main function stops running, returns
    # an integer status code, or throws an error the program will exit.
    ble.run_mainloop_with(main)


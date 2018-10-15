import Adafruit_BluefruitLE
import argparse
from aquasystems.timer import TimerService

device_name = None

# Get the BLE provider for the current platform.
ble = Adafruit_BluefruitLE.get_provider()


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

    # Scan for device
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
    try:
        print('Discovering services...')
        TimerService.discover(device)

        timer = TimerService(device)
        print("battery_level: {}".format(timer.battery))
        duration_val = timer.cycle_duration
        time = timer.time
        print("device time: {:02d}:{:02d}:{:02d}".format(time[0], time[1], time[2]))
        print("duration_timer: {}".format(duration_val))
        print("cycle_frequency: {} days".format(timer.cycle_frequency))
        start1 = timer.cycle1_start
        print("cycle1_start: {:02d}:{:02d}".format(start1[0], start1[1]))
        start2 = timer.cycle2_start
        print("cycle1_start: {:02d}:{:02d}".format(start2[0], start2[1]))
        print("manual time left: {} mins".format(timer.manual_time_left))
        print("rain delay: {} days".format(timer.rain_delay_time))
        print("is on: {}".format(timer.on))

        # set the value
        timer.cycle_duration = duration_val - 1
        print("duration_timer1: {}".format(timer.cycle_duration))
        timer.rain_delay_time = 0
        print("rain delay: {} days".format(timer.rain_delay_time))

    finally:
        # Make sure device is disconnected on exit.
        device.disconnect()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description='Debug the device.')
    parser.add_argument('--device_id', help='ID of Tap Timer device e.g "Spray-Mist A19E"', default="Spray-Mist A19E")
    args = parser.parse_args()

    device_name = args.device_id

    # Initialize the BLE system.  MUST be called before other BLE calls!
    ble.initialize()

    # Start the mainloop to process BLE events, and run the provided function in
    # a background thread.  When the provided main function stops running, returns
    # an integer status code, or throws an error the program will exit.
    ble.run_mainloop_with(main)

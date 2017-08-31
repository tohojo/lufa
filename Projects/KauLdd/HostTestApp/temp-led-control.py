# -*- coding: utf-8 -*-
# Control app for the KAU LDD USB device; shows current temperature and allows
# control of the LEDs

import asyncio
import sys
import struct
import tty
import termios
import usb.core
import usb.util

# Bulk Vendor HID device VID and PID
device_vid = 0x03EB
device_pid = 0x206C
device_in_ep = 3
device_out_ep = 4

LEDS = [
    1 << 4,
    1 << 5,
    1 << 7,
    1 << 6]

LED_CHARS = ['.', 'o']

LED_STATUS = 0


def print_leds(mask):
    return "LEDs: " + "".join([LED_CHARS[min(1, mask & m)] for m in LEDS])


def toggle_led(no):
    return LED_STATUS ^ LEDS[no]


def get_vendor_device_handle():
    dev_handle = usb.core.find(idVendor=device_vid, idProduct=device_pid)
    return dev_handle


def write(device, packet):
    device.write(usb.util.ENDPOINT_OUT | device_out_ep, packet)


def show_status(device, loop=None):
    global LED_STATUS
    packet = device.read(usb.util.ENDPOINT_IN | device_in_ep, 64)
    temp, leds = struct.unpack("bB", packet)
    LED_STATUS = leds
    print("\rCurrent temperature: %d°C - %s" % (temp, print_leds(leds)), end='')

    if loop:
        loop.call_later(0.1, show_status, device, loop)


def read_char(dev):
    c = sys.stdin.read(1)
    if c in '1234':
        write(dev, struct.pack("B", toggle_led(int(c)-1)))

    if c == 'q':
        raise KeyboardInterrupt()


def main(loop):

    vendor_device = get_vendor_device_handle()

    if vendor_device is None:
        print("No valid Vendor device found.")
        sys.exit(1)

    #vendor_device.set_configuration()

    print("Connected to device 0x%04X/0x%04X - %s [%s]" %
          (vendor_device.idVendor, vendor_device.idProduct,
           usb.util.get_string(vendor_device, vendor_device.iProduct),
           usb.util.get_string(vendor_device, vendor_device.iManufacturer)))

    loop.add_reader(sys.stdin.fileno(), read_char, vendor_device)
    loop.call_soon(show_status, vendor_device, loop)

    print("Press q to exit, 1-4 to toggle LEDs", end='\n\n')

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()
    return


if __name__ == '__main__':
    stdin_fd = sys.stdin.fileno()
    term_settings = termios.tcgetattr(stdin_fd)
    try:
        tty.setcbreak(stdin_fd)
        loop = asyncio.get_event_loop()
        main(loop)
    finally:
        termios.tcsetattr(stdin_fd, termios.TCSADRAIN, term_settings)
        print("")

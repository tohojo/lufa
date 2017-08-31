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

INTERVAL = 0.1


class UsbDev(object):

    def __init__(self, loop):
        self.led_status = 0
        self.loop = loop

    def print_leds(self):
        return "LEDs: " + "".join([LED_CHARS[min(1, self.led_status & m)]
                                   for m in LEDS])

    def toggle_led(self, no):
        self.led_status ^= LEDS[no]
        self.write(struct.pack("B", self.led_status))

    def write(self, packet):
        raise NotImplementedError()

    def read(self):
        raise NotImplementedError()

    def show_status(self):
        packet = self.read()
        temp, self.led_status = struct.unpack("bB", packet)
        print("\rCurrent temperature: %d°C - %s" % (temp, self.print_leds()),
              end='')

        self.loop.call_later(INTERVAL, self.show_status)


class UsbDevLibUsb(UsbDev):

    def __init__(self, loop):
        super(UsbDevLibUsb, self).__init__(loop)
        self.dev_handle = usb.core.find(idVendor=device_vid, idProduct=device_pid)

        if self.dev_handle is None:
            print("No valid Vendor device found.")
            sys.exit(1)

        print("Connected to device 0x%04X/0x%04X - %s [%s]" %
              (self.dev_handle.idVendor, self.dev_handle.idProduct,
               usb.util.get_string(self.dev_handle,
                                   self.dev_handle.iProduct),
               usb.util.get_string(self.dev_handle,
                                   self.dev_handle.iManufacturer)))

    def write(self, packet):
        self.dev_handle.write(usb.util.ENDPOINT_OUT | device_out_ep, packet)

    def read(self):
        return self.dev_handle.read(usb.util.ENDPOINT_IN | device_in_ep, 64)


def read_char(dev):
    c = sys.stdin.read(1)
    if c in '1234':
        dev.toggle_led(int(c)-1)

    if c == 'q':
        raise KeyboardInterrupt()


def main(loop):

    dev = UsbDevLibUsb(loop)

    loop.add_reader(sys.stdin.fileno(), read_char, dev)
    loop.call_soon(dev.show_status)

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

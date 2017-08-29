# """
#              LUFA Library
#      Copyright (C) Dean Camera, 2017.
#
#   dean [at] fourwalledcubicle [dot] com
#            www.lufa-lib.org
# """
#
# """
#     LUFA Bulk Vendor device demo host test script. This script will send and
#     receive a continuous stream of packets to/from to the device, to show
#     bidirectional communications.
#
#     Requires the pyUSB library (http://sourceforge.net/projects/pyusb/).
# """

import sys
import struct
import time
import usb.core
import usb.util

# Bulk Vendor HID device VID and PID
device_vid = 0x03EB
device_pid = 0x206C
device_in_ep = 3
device_out_ep = 4


def get_vendor_device_handle():
    dev_handle = usb.core.find(idVendor=device_vid, idProduct=device_pid)
    return dev_handle


def write(device, packet):
    device.write(usb.util.ENDPOINT_OUT | device_out_ep, packet)
    print("Sent Packet: 0x{0}".format("".join(["%x" % x for x in packet])))


def read(device):
    packet = device.read(usb.util.ENDPOINT_IN | device_in_ep, 64)
    print("Received Packet: 0x{0}".format(''.join(["%x" % x for x in packet])))
    return packet


def main():
    if len(sys.argv) >= 2:

        if sys.argv[1].startswith("0x"):
            mask = int(sys.argv[1][2:], 16)
        else:
            mask = int(sys.argv[1])
        if mask > 255 or mask < 0:
            sys.stderr.write("LED_MASK must be > 0 and <= 255\n")
            sys.exit(1)
    else:
        mask = None


    vendor_device = get_vendor_device_handle()

    if vendor_device is None:
        print("No valid Vendor device found.")
        sys.exit(1)

    vendor_device.set_configuration()

    print("Connected to device 0x%04X/0x%04X - %s [%s]" %
          (vendor_device.idVendor, vendor_device.idProduct,
           usb.util.get_string(vendor_device, vendor_device.iProduct),
           usb.util.get_string(vendor_device, vendor_device.iManufacturer)))

    if mask:
        write(vendor_device, struct.pack("B", mask))
    while True:
        temp = read(vendor_device)
        print("Current temperature: %d°C" % struct.unpack("b", temp))
        time.sleep(1)


if __name__ == '__main__':
    main()

#!/usr/bin/python3

from __future__ import print_function

import argparse
import serial
import time
import os
import stat
import string
import json as json

# Some variables
data = {}
CurrentUsage = 0
CurrentLevel = 0

# Change these according used system
FILENAME = "data.txt"
ADDRESS = 0
DEVICE = "/dev/ttyUSB0"
BAUDRATE = 9600

try:
    import meterbus
except ImportError:
    import sys
    sys.path.append('../')
    import meterbus


# This is example code copied from pymeterbus author
def ping_address(ser, address, retries=5):
    for i in range(0, retries + 1):
        meterbus.send_ping_frame(ser, address)
        try:
            frame = meterbus.load(meterbus.recv_frame(ser, 1))
            if isinstance(frame, meterbus.TelegramACK):
                return True
        except meterbus.MBusFrameDecodeError:
            pass

    return False


def do_reg_file(args):
    global data
    data = {}
    with open(DEVICE, 'rb') as f:
        frame = meterbus.load(f.read())
        if frame is not None:
            data = frame.to_JSON()


def do_char_dev(args):
    global data
    data = {}
    address = 0
    try:
        address = ADDRESS
        if not (0 <= address <= 254):
            address = 0
    except ValueError:
        address = 0

    try:
        baudrate = BAUDRATE
    except ValueError:
        baudrate = 2400

    try:
        ibt = meterbus.inter_byte_timeout(baudrate)
        with serial.serial_for_url(DEVICE,
                           baudrate, 8, 'E', 1,
                           inter_byte_timeout=ibt,
                           timeout=1) as ser:
            frame = None

            if meterbus.is_primary_address(address):
                ping_address(ser, meterbus.ADDRESS_NETWORK_LAYER, 0)

                meterbus.send_request_frame(ser, address)
                frame = meterbus.load(
                    meterbus.recv_frame(ser, meterbus.FRAME_DATA_LENGTH))

            if frame is not None:
                data = frame.to_JSON()

    except serial.serialutil.SerialException as e:
        print(e)


# Write data to file
# w = watts; a1, a2, a3 are current values 
def fileWrite(w, a1, a2, a3):
    with open(FILENAME, 'w') as file:
        line = str(w) + "," + str(a1) + "," + str(a2) + "," + str(a3)
        file.write(line)


def main():
    if __name__ == '__main__':

        # Some debug options, not used in working program
        parser = argparse.ArgumentParser(
            description='Request data over serial M-Bus for devices.')
        parser.add_argument('-d', action='store_true',
                            help='Enable verbose debug')
        parser.add_argument('-r', '--retries',
                            type=int, default=1,
                            help='Number of ping retries for each address')

        args = parser.parse_args()

        meterbus.debug(args.d)

        # Loop the main program
        while True:
            # Retrieve the data
            try:
                mode = os.stat(DEVICE).st_mode
                if stat.S_ISREG(mode):
                    do_reg_file(args)
                else:
                    do_char_dev(args)
            except OSError:
                do_char_dev(args)

            # Format the data
            d = json.loads(data)
            w = int(d["body"]["records"][2]["value"])
            a1 = round(float(d["body"]["records"][8]["value"]), 2)
            a2 = round(float(d["body"]["records"][9]["value"]), 2)
            a3 = round(float(d["body"]["records"][10]["value"]), 2)
            fileWrite(w, a1, a2, a3)

main()

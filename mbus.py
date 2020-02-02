#!/usr/bin/python

from __future__ import print_function

import argparse
import serial
import time
import os
import stat
import string
import json

data = {}
CurrentUsage = 0
CurrentLevel = 0

FILENAME = "data.txt"
ADDRESS = 0
DEVICE = "/dev/ttyUSB0"
BAUDRATE = 2400

try:
    import meterbus
except ImportError:
    import sys
    sys.path.append('../')
    import meterbus


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

def control(x):
    global CurrentLevel
    value = float(x)
    while value > 150:
        if CurrentLevel == 9:
            break
        CurrentLevel += 1
        value -= 111
    while value < -150:
        if CurrentLevel == 0:
            break
        CurrentLevel -= 1
        value += 111


def fileWrite():
    with open(FILENAME, 'w') as file:
        file.write(CurrentLevel)


def main():
    if __name__ == '__main__':
        parser = argparse.ArgumentParser(
            description='Request data over serial M-Bus for devices.')
        parser.add_argument('-d', action='store_true',
                            help='Enable verbose debug')
        parser.add_argument('-r', '--retries',
                            type=int, default=1,
                            help='Number of ping retries for each address')

        args = parser.parse_args()

        meterbus.debug(args.d)
        while True:
            try:
                mode = os.stat(DEVICE).st_mode
                if stat.S_ISREG(mode):
                    do_reg_file(args)
                else:
                    do_char_dev(args)
            except OSError:
                do_char_dev(args)

            d = json.loads(data)
            value = d["body"]["records"][2]["value"]
            control(value)
            fileWrite()

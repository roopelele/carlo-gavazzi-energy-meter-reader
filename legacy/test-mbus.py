from math import floor
from sys import exit
import time
import os
import json
import asyncio
import serial
import meterbus

DEVICE = "/dev/ttyUSB0"
BAUDRATE = 2400
DIR = os.getcwd()


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

def powerManage():
    try:
        start = time.time()
        data = get_data()
        end = time.time()
        print("data:")
        print(json.dumps(data, indent=4))
        print(f"get_data() took {end-start:.3f} seconds")
    except Exception as e:
        print("powerManage(): error:")
        print(str(e))
        return


def get_data():
    try:
        ibt = meterbus.inter_byte_timeout(BAUDRATE)
        with serial.serial_for_url(DEVICE, BAUDRATE, 8, 'E', 1, inter_byte_timeout=ibt, timeout=0.6, write_timeout=0) as ser:
            frame = None
            status = False
            print("send_request_frame()")
            meterbus.send_request_frame(ser, 0)
            d = b""
            while frame is None:
                print("ser.read()")
                characters = ser.read(meterbus.FRAME_DATA_LENGTH)
                if isinstance(characters, str):
                    print("isinstance() == True")
                    characters = bytearray(characters)
                d += characters
                print("TelegramLong.parse()")
                print("d:")
                print(list(d))
                frame = meterbus.TelegramLong.parse(list(d))
        frame = meterbus.load(d)
        print("frame:")
        print(frame)
        if frame is not None:
            return json.loads(frame.to_JSON())
        else:
            print("error: frame is None")
            return {}
    except Exception as e:
        print("get_data(): error")
        print(str(e))
        return {}


def main():
    print("start")
    powerManage()
    print("end")


main()

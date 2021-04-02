from math import floor
import os
import time
import json
import asyncio
import serial
import meterbus
import stat
import RPi.GPIO as GPIO

DEVICE = "/dev/ttyUSB0"
BAUDRATE = 9600

MIN_POWER = 0
MAX_POWER = 1000
INTERVAL = 10 #minutes
# RasPi pins used to control
PINS = [3, 5, 7]
# Path to fissio folder
fissioPath = "/home/pi/.fissio/mittaustiedot.txt"

DIR = os.getcwd()

# Some global variables, don't touch
watts = 0
last_minute = []
joules = 0
state = False

def setup():
    GPIO.setmode(GPIO.BOARD)
    for pin in PINS:
        GPIO.setup(pin, GPIO.OUT)

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

async def powerManage():
    global watts, joules
    try:
        data = await get_data()
        tmp = int(data["body"]["records"][2]["value"])
    except Exception as e:
        print(e)
        return
    last_minute.append(tmp)
    watts = tmp
    joules += tmp

async def get_data():
    try:
        ibt = meterbus.inter_byte_timeout(BAUDRATE)
        with serial.serial_for_url(DEVICE, BAUDRATE, 8, 'E', 1, inter_byte_timeout=ibt, timeout=0.4) as ser:
            frame = None
            status = False
            meterbus.send_request_frame(ser, 0)
            d = b""
            while frame is None:
                start = time.time()
                characters = ser.read(meterbus.FRAME_DATA_LENGTH)
                if isinstance(characters, str):
                    characters = bytearray(characters)
                d += characters
                frame = meterbus.TelegramLong.parse(list(d))
        frame = meterbus.load(d)
        if frame is not None:
            return json.loads(frame.to_JSON())
    except:
        return {}

def setState(newstate):
    print(f"setstate({newstate})")
    global state, PINS
    if state == newstate:
        return
    state = newstate
    GPIO.output(PINS, state)

async def main():
    global watts, joules, last_minute
    setState(False)
    second = floor(time.time() % 3600)
    setup()
    start = time.time() - second
    print(second, second / 60, second % 60)
    while True:
        second += 1
        await powerManage()
        t = int(time.time())
        if (not state) and (joules < (min((3600 - second), (INTERVAL*60)) * -(MAX_POWER * len(PINS)))):
            setState(True)
        if state and joules > 0:
            setState(False)
        if floor(t % 60) == 0:
            print(f"watts: {watts:10}, joules: {joules:10}")
            with open(fissioPath, 'a') as outfile:
                outfile.write(f"{t};temp;Teho;{((sum(last_minute)/len(last_minute))/1000):.3f};null;")
            last_minute = []
        if floor(t % 3600) == 0:
            with open("/home/pi/energy/LOG.txt", 'a') as outfile:
                outfile.write(f"hourly energy: {joules}\n")
            joules = 0
            setState(False)
            watts = 0
            time.sleep(second-(time.time()-start))
            second = 0
            start = time.time()
            continue
        time.sleep(abs(second - (time.time() - start)))


asyncio.run(main())

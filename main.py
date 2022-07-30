from math import floor
from sys import exit
import os
import time
import json
import asyncio
import serial
import meterbus
import stat
import RPi.GPIO as GPIO
import numpy as np

DEVICE = "/dev/ttyUSB0"
BAUDRATE = 2400

REVERSE_CONTROL = True
MIN_POWER = 0
MAX_POWER = 3000
INTERVAL = 10 # minutes
# GPIO pins used to control
PINS = [2]
# Path to fissio folder
fissioPath = "/home/pi/.fissio/mittaustiedot.txt"

DIR = os.getcwd()

# Some global variables, don't touch
amps = []
watts = 0
last_minute = []
joules = 0
pulses = 0
state = None

def setup():
    GPIO.setmode(GPIO.BCM)
    for pin in PINS:
        GPIO.setup(pin, GPIO.OUT)


def ping_address(ser, address, retries=2):
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
    global watts, joules, amps
    try:
        data = await get_data()
        data = data["body"]["records"]
        tmp = int(data[2]["value"])
    except Exception as e:
        log(f"powerManage: error: {str(e)}")
        exit()
        return
    amps.append([ d["value"] for d in data[8:11] ])
    last_minute.append(tmp)
    watts = tmp
    joules += tmp

async def get_data():
    try:
        ibt = meterbus.inter_byte_timeout(BAUDRATE)
        with serial.serial_for_url(DEVICE, BAUDRATE, 8, 'E', 1, inter_byte_timeout=ibt, timeout=0.8) as ser:
            frame = None
            status = False
            meterbus.send_request_frame(ser, 0)
            d = b""
            while frame is None:
                characters = ser.read(meterbus.FRAME_DATA_LENGTH)
                if isinstance(characters, str):
                    characters = bytearray(characters)
                d += characters
                frame = meterbus.TelegramLong.parse(list(d))
        frame = meterbus.load(d)
        if frame is not None:
            return json.loads(frame.to_JSON())
        else:
            log("frame is None")
            return {}
    except Exception as e:
        log(f"get_data(): error: {str(e)}")
        return {}

def setState(newstate):
    global state, PINS
    if state == newstate:
        return
    state = newstate
    log(f"state changed to {state}")
    state = newstate
    if REVERSE_CONTROL:
        GPIO.output(PINS, state)
    else:
        GPIO.output(PINS, not state)

def log(msg):
    print(msg)
    with open("/home/pi/LOG.txt", 'a') as outfile:
        outfile.write(f"{time.strftime('%Y-%m-%d %H:%M')}: {msg}\n")

def fissioString(timestamp, name, value):
    return f"{timestamp};temp;{name};{value};null;\n"

async def minute():
    t = int(time.time())
    global last_minute, pulses, amps
    amps = np.array(amps)
    try:
        text = fissioString(t, "Teho", f"{((sum(last_minute)/len(last_minute))/1000):.3f}")
        for i in range(amps.shape[1]):
            text += fissioString(t, f"Virta_{i+1}",  f"{np.max(amps[:,i]):.3f}")
        with open(fissioPath, 'a') as outfile:
            outfile.write(text)
    except Exception as e:
        log(str(e))
    last_minute = []
    amps = []

async def hour():
    global watts, joules
    log(f"Time period ended. Stats: joules = {joules}, watts = {watts}")
    joules = 0
    setState(False)
    watts = 0

async def day():
    global pulses
    pulses = 0
    log("Daily reset")

async def main():
    global watts, joules, last_minute, pulses
    second = floor(time.time() % 3600)
    setup()
    start = time.time() - second
    log("starting")
    setState(False)
    while True:
        second += 1
        await powerManage()
        t = time.localtime()
        if (not state) and (joules < (min((3600 - second), (INTERVAL*60)) * -(MAX_POWER * len(PINS)))):
            setState(True)
        if state and joules > 0:
            setState(False)
        if t.tm_sec == 5: # Every minute, on the 5th second to prevent file write error with fissio
            await asyncio.create_task(minute())
            if t.tm_min == 0:
                await asyncio.create_task(hour())
                if t.tm_hour == 0:
                    await asyncio.create_task(day())
                time.sleep(second-(time.time()-start))
                second = 0
                start = time.time()
                continue
        time.sleep(abs(second-(time.time()-start)))


asyncio.run(main())

GPIO.cleanup() # Add this to the end of a program

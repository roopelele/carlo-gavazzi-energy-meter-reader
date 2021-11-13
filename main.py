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
BAUDRATE = 9600

MIN_POWER = 0
MAX_POWER = 1000
INTERVAL = 10 #minutes
# RasPi pins used to control
PINS = [3, 5, 7]
# Pin used for water meter pulses
METER_PIN = 37
# Path to fissio folder
fissioPath = "/home/pi/.fissio/mittaustiedot.txt"

DIR = os.getcwd()
totalFile = os.path.join(DIR, "total.txt")

# Some global variables, don't touch
amps = []
watts = 0
last_minute = []
joules = 0
pulses = 0
total = 0
state = False

def pulseReceived(gpio):
    global pulses, total
    pulses += 1
    total += 1

def setup():
    global total
    try:
        with open(totalFile, 'r') as infile:
            total = int(infile.read().strip())
    except:
        total = 0
    print(f"total water amount: {total}")
    GPIO.setmode(GPIO.BOARD)
    for pin in PINS:
        GPIO.setup(pin, GPIO.OUT)
    GPIO.setup(METER_PIN, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
    GPIO.add_event_detect(METER_PIN, GPIO.RISING, callback=pulseReceived, bouncetime=40)

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
    global watts, joules, amps
    try:
        data = (await get_data())["body"]["records"]
        tmp = int(data[2]["value"])
    except Exception as e:
        log(e)
        exit()
        return
    amps.append([d["value"] for d in data[8:11]])
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
    global state, PINS
    if state == newstate:
        return
    state = newstate
    GPIO.output(PINS, state)

def log(msg):
    print(msg)
    with open("/home/pi/energy/LOG.txt", 'a') as outfile:
        outfile.write(f"{int(time.time())}: {msg}\n")

async def minute():
    t = int(time.time())
    global last_minute, pulses, amps
    amps = np.array(amps)
    try:
        with open(fissioPath, 'a') as outfile:
            text = f"{t-5};temp;Teho;{((sum(last_minute)/len(last_minute))/1000):.3f};null;\n"
            text += f"{t-5};temp;Vesi;{(pulses/10.0):.1f};null;\n"
            for i in range(amps.shape[1]):
                text += f"{t-5};temp;Virta_{i+1};{np.max(amps[:,i]):.3f};null;\n"
            outfile.write(text)
    except Exception as e:
        log(str(e))
    last_minute = []
    amps = []

async def hour():
    global watts, joules
    joules = 0
    setState(False)
    watts = 0
    with open(totalFile, 'w') as outfile:
        outfile.write(str(total))

async def day():
    global pulses
    pulses = 0

async def main():
    global watts, joules, last_minute, pulses
    setState(False)
    second = floor(time.time() % 3600)
    setup()
    start = time.time() - second
    log("starting")
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

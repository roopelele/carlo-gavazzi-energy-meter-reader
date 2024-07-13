#!/usr/bin/python3

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
SER_TIMEOUT = 0.8

LOGFILE = "/home/roope/LOG.txt"

REVERSE_CONTROL = False
MIN_POWER = 0
MAX_POWER = 2900
NUM_AMPS = 3 # Amount of current measurements
PIN = 3
hassPath = "/dev/shm/"

DIR = os.getcwd()

# Some global variables, don't touch
amps = np.zeros((60, NUM_AMPS))
last_minute = np.zeros(60)
idx_minute = 0
watts = 0
joules = 0
pulses = 0
state = None

def setup():
    log("setup")
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PIN, GPIO.OUT)


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
    global watts, joules, amps, last_minute, idx_minute
    try:
        data = await get_data()
        data = data["body"]["records"]
        tmp = int(data[2]["value"])
    except Exception as e:
        log(f"powerManage: error: {str(e)}")
        exit()
        return
    for j, d in enumerate(data[8:11]):
        amps[idx_minute, j] = d["value"]
    last_minute[idx_minute] = tmp
    watts = tmp
    joules += tmp
    idx_minute += 1

async def get_data():
    try:
        ibt = meterbus.inter_byte_timeout(BAUDRATE)
        with serial.serial_for_url(DEVICE, BAUDRATE, 8, 'E', 1, inter_byte_timeout=ibt, timeout=SER_TIMEOUT, write_timeout=SER_TIMEOUT) as ser:
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
    global state, PIN
    if state == newstate:
        return
    state = newstate
    log(f"state changed to {state}")
    state = newstate
    if REVERSE_CONTROL:
        GPIO.output(PIN, state)
    else:
        GPIO.output(PIN, not state)

def log(msg):
    print(msg)
    with open(LOGFILE, 'a') as outfile:
        outfile.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')}: {msg}\n")

async def minute():
    t = int(time.time())
    global last_minute, pulses, amps, idx_minute
    amps = amps[:idx_minute]
    last_minute = last_minute[:idx_minute]
    try:
        with open(os.path.join(hassPath, "P.txt"), 'w') as outfile:
            outfile.write(f"{int( (np.sum(last_minute)/np.size(last_minute)) )}\n")
        for i in range(amps.shape[1]):
            with open(os.path.join(hassPath, f"A_{i}.txt"), 'w') as outfile:
                outfile.write(f"{np.max(amps[:,i]):.3f}\n")
    except Exception as e:
        log(str(e))
    last_minute = np.zeros(60)
    amps = np.zeros((60, 3))
    idx_minute = 0

async def main():
    global watts, joules, last_minute, pulses
    second = floor(time.time() % 900)
    setup()
    start = time.time() - second
    setState(False)
    while True:
        second += 1
        await powerManage()
        if shouldEnable():
            setState(True)
        else if shouldDisable():
            setState(False)
        t = time.localtime()
        if t.tm_sec == 30:
            await asyncio.create_task(minute())
            if t.tm_min % 15 == 14:   # Every 15 minutes due to electricity being billed by quarter-hours
                return
        time.sleep(abs(second-(time.time()-start)))

def shouldEnable():
    # Do nothing if already enabled
    if state:
        return false
    # Negative watts = producing, therefore if watts < -2.9kW
    # Negative joules = exported power during the last measurement period
    if joules < 0 and watts < -MAX_POWER:
        return true
    # Finally, if we have exported more power than we can consume in the remaining time period,
    # we also enable water heater (negative joules = exported energy)
    return joules < ((900 - second) * -MAX_POWER)

def shouldDisable():
    # Do nothing if already disabled
    if not state:
        return false
    # Exported power during this period, and not buying any even though water heater is enabled
    # --> should not disable
    # Note: in this state, the water heater is already running, therefore we compare to 0
    if joules < 0 and watts < 0:
        return false
    # Disable water heater if we are about to start buying electricity
    return joules > -1000


asyncio.run(main())

log("Main loop exited")
GPIO.cleanup() # Add this to the end of a program

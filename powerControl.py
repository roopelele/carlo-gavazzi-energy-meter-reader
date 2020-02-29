#!/usr/bin/python3

import RPi.GPIO as GPIO
import time

MIN_POWER = 0
MAX_POWER = 1000
POWER_DELTA = 20
PIN = 0
power = 0

def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(pin, GPIO.OUT)
    global power
    power = 0


def readData():
    filename = "data.txt"
    with open(filename, 'r') as file:
        data = int(file.read()) * -1
    return(data)


def control(power):
    if power == MAX_POWER:
        GPIO.output(PIN, 1)
    elif power == MIN_POWER:
        GPIO.output(PIN, 0)
    else:
        GPIO.output(PIN, 1)
        time.sleep(power / 1000)
        GPIO.output(PIN, 0)
        time.sleep(1.0 - (power / 1000))


def powerManage():
    global power
    powerChange = readData()
    power += powerChange
    if power < MIN_POWER + POWER_DELTA:
        power = MIN_POWER
    elif power > MAX_POWER - POWER_DELTA:
        power = MAX_POWER
    control(power)


def main():
    setup()
    while True:
        powerManage()



main()

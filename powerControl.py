#!/usr/bin/python3

import RPi.GPIO as GPIO
import time

MIN_POWER = 20
MAX_POWER = 1000
PIN = 0


def readData():
    filename = "data.txt"
    with open(filename, 'r') as file:
        data = int(file.read())
    return(data)


def control(power):
    if power == MAX_POWER:
        GPIO.output(PIN, 1)
    elif power == MIN_POWER:
        GPIO.output(PIN, 0)
    else:
        GPIO.output(PIN, 1)
        time.sleep(power)
        GPIO.output(PIN, 0)
        time.sleep(1000 - power)


def main():
    GPIO.setup(pin, GPIO.OUT)
    power = 0
    while True:
        powerChange = readData()
        power += powerChange
        if power < MIN_POWER:
            power = 0
        elif power > MAX_POWER:
            power = MAX_POWER
        control(power)




main()

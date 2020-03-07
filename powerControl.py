#!/usr/bin/python3

import RPi.GPIO as GPIO
import time

MIN_POWER = 0
MAX_POWER = 1000
POWER_DELTA = 50
PIN = 3
power = 0


# This function runs once in the start, to set up the GPIO
def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(PIN, GPIO.OUT)
    global power
    power = 0


# This function reads the data in a file provided by other program
def readData():
    filename = "data.txt"
    with open(filename, 'r') as file:
        data = int(file.read()) * -1
    return(data)


# This function controls power used with raspberry pi's gpio ports
# for one second at a time
def control(power):
    if power == MAX_POWER:
        GPIO.output(PIN, 1)
        time.sleep(1)
        return
    elif power == MIN_POWER:
        GPIO.output(PIN, 0)
        time.sleep(1)
        return
    else:
        GPIO.output(PIN, 1)
        time.sleep(power / 1000)
        GPIO.output(PIN, 0)
        time.sleep(1.0 - (power / 1000))
        return


# This is the core function for running all the other functions in the correct order
# And calculating the amount of power provided
def powerManage():
    global power
    powerChange = readData()
    power += powerChange - 100
    if power < MIN_POWER + POWER_DELTA:
        power = MIN_POWER
    elif power > MAX_POWER - POWER_DELTA:
        power = MAX_POWER
    control(power)


# Simple main function for the program
def main():
    setup()
    while True:
        powerManage()
    GPIO.output(PIN, 0)



main()

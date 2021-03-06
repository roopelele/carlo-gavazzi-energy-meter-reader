#!/usr/bin/python3

import RPi.GPIO as GPIO
import time
import os

# Some values used to calculate power
MIN_POWER = 0
MAX_POWER = 1000
POWER_DELTA = 0
EXTRA_POWER = 0
POWER_CHANGE_MULTIPLIER = 0.9
# RasPi pins used to control
PINS = [3, 5, 7]
# Path to fissio folder
fissioPath = "/home/pi/.fissio/mittaustiedot.txt"

DIR = os.getcwd()

# Name of the input filename
inputFile = os.path.join(DIR, "data.txt")
# Some global variables, don't touch
power = 0
lastData = 0


def configRead():
    global MIN_POWER, MAX_POWER, POWER_DELTA, POWER_CHANGE_MULTIPLIER, EXTRA_POWER, PINS, fissioPath, inputFile
    with open(os.path.join(DIR, "config.txt"), 'r') as file:
        for row in file:
            data = row.split("=")
            if len(data) != 2:
                continue
            var, value = data
            value = value.rstrip()
            if var == "MIN_POWER":
                MIN_POWER = int(value)
            elif var == "MAX_POWER":
                MAX_POWER = int(value)
            elif var == "POWER_DELTA":
                POWER_DELTA = int(value)
            elif var == "EXTRA_POWER":
                EXTRA_POWER = int(value)
            elif var == "POWER_CHANGE_MULTIPLIER":
                POWER_CHANGE_MULTIPLIER = float(value)
            elif var == "PINS":
                PINS = value.split(",")
                for i in range(0, len(PINS)):
                    PINS[i] = int(PINS[i])
            elif var == "FISSIO_PATH":
                fissioPath = value
            elif var == "inputFile":
                inputFile = values



# This function runs once in the start, to set up the GPIO
def setup():
    configRead()
    GPIO.setmode(GPIO.BOARD)
    for pin in PINS:
        GPIO.setup(pin, GPIO.OUT)


# This function reads the data in a file provided by other program
# returns INT
def readData(tries = 0):
    global lastData
    if tries == 3:
        return 0
    try:
        with open(inputFile, 'r') as file:
            data = file.read()
            data = int(data) * -1
    except Exception as e:
        time.sleep(0.01)
        data = readData(tries + 1)
    if data == lastData:
        return 0
    lastData = data
    return(data)


# This function controls power used with raspberry pi's gpio ports
# for one second at a time
# PARAM power (int): This is the amount of excess power available
def control(p):
    i = 0
    if p == MIN_POWER:
        for pin in PINS:
            GPIO.output(pin, 0)
        time.sleep(1)
        return
    while p >= MAX_POWER and i < len(PINS) - 1:
        GPIO.output(PINS[i], 1)
        p -= MAX_POWER
        i += 1
    if i >= len(PINS):
        time.sleep(1)
        return
    else:
        GPIO.output(PINS[i], 1)
        time.sleep(float(p) / float(MAX_POWER))
        GPIO.output(PINS[i], 0)
        time.sleep(1.0 - (float(p) / float(MAX_POWER)))
    return


# This is the core function for running all the other functions in the correct order
# And calculating the amount of power provided
def powerManage():
    global power
    data = readData()
    power += (data * POWER_CHANGE_MULTIPLIER) - EXTRA_POWER
    if power < MIN_POWER + POWER_DELTA:
        power = MIN_POWER
    elif power > (MAX_POWER * len(PINS)) - POWER_DELTA:
        power = (MAX_POWER * len(PINS))
    control(power)


# Simple main function for the program
def main():
    setup()
    while True:
        powerManage()
    GPIO.output(PIN, 0)



main()

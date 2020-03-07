#!/usr/bin/python3

import RPi.GPIO as GPIO
import time

# Some values used to calculate power
MIN_POWER = 0
MAX_POWER = 1000
POWER_DELTA = 50
# RasPi pin used to control
PIN = 3
# Path to fissio folder
fissioPath = "/home/pi/.fissio/mittaustiedot.txt"
# Don't touch these
power = 0
powerList = []


# This function runs once in the start, to set up the GPIO
def setup():
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(PIN, GPIO.OUT)


# This function reads the data in a file provided by other program
def readData():
    filename = "data.txt"
    with open(filename, 'r') as file:
        data = int(file.read()) * -1
    return(data)


# This function controls power used with raspberry pi's gpio ports
# for one second at a time
# PARAM power (int): This is the amount of excess power available 
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
    global powerList
    data = readData()
    power += data - 100
    powerList.append(data)
    fissio()
    if power < MIN_POWER + POWER_DELTA:
        power = MIN_POWER
    elif power > MAX_POWER - POWER_DELTA:
        power = MAX_POWER
    control(power)


# This is the function for fissio integration
def fissio():
    try:
        global powerList
        if len(powerList) == 60:
            sum = 0
            for entry in powerList:
                sum += entry
            minute = round( (((sum / 60.0) / 1000) * -1), 3)
            powerList = []
            with open(fissioPath, "a") as file:
                file.write(str(int(time.time())) + ";temp;Teho;" + str(minute) + ";null;\n")
    except ValueError:
        return
    return


# Simple main function for the program
def main():
    setup()
    while True:
        powerManage()
    GPIO.output(PIN, 0)



main()

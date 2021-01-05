#!/usr/bin/python3
import time

fissioPath = "/home/pi/.fissio/mittaustiedot.txt"
FILENAME = "/home/pi/energy/tmp.txt"
VALUES = [0, 0, 0, 0]
AMOUNT = 0

try:
    t = str(int(time.time()) - 5)
    with open(FILENAME, 'r') as file:
        lines = [line.rstrip('\n') for line in file]
    open(FILENAME, 'w').close()
    for line in lines:
        tmp = line.split(',')
        for i in range(4):
            VALUES[i] += float(tmp[i])
        AMOUNT += 1
    text = f"{t};temp;Teho;{((VALUES[0] / AMOUNT) / 1000):.3f};null;"
    for i in range(1, 4):
        text += f"temp;Virta_{i};{(VALUES[i] / AMOUNT):.3f};null;"
    text += "\n"
    with open(fissioPath, "a") as file:
        file.write(text)
except ValueError as e:
    with open("/home/pi/energy/LOG.txt", 'a'):
         file.write(f"{time.time()}:{e.message}")

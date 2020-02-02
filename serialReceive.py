import time
import serial


def readSer():
    with serial.Serial('/dev/ttyACM0', 9600) as ser:
        print(ser.read())


i = 0
while True:
    i = i + 1
    startTime = time.time()
    readSer()
    x = time.time() - startTime
    print(x)
    if i > 10:
        break

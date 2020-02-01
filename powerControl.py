import serial
import time


def readData():
    allowedInputs = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    filename = "data.txt"
    with open(filename, 'r') as file:
        data = int(file.read())
    if not (data in allowedInputs):
        data = 0
    return(data)


def main():
    ser = serial.Serial('/dev/ttyACM0', 9600)
    while True:
        power = readData()
        if power == 0:
            ser.write(b'0')
        elif power == 1:
            ser.write(b'1')
        elif power == 2:
            ser.write(b'2')
        elif power == 3:
            ser.write(b'3')
        elif power == 4:
            ser.write(b'4')
        elif power == 5:
            ser.write(b'5')
        elif power == 6:
            ser.write(b'6')
        elif power == 7:
            ser.write(b'7')
        elif power == 8:
            ser.write(b'8')
        elif power == 9:
            ser.write(b'9')
        time.sleep(1)


main()

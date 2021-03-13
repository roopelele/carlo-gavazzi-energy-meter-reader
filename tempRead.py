import time
import os
import sys

FILE = "/home/pi/.fissio/mittaustiedot.txt"

def read_sensors():
    rtn = {}
    w1_devices = []
    w1_devices = os.listdir("/sys/bus/w1/devices/")
    values = []
    for deviceid in w1_devices:
        rtn[deviceid] = {}
        rtn[deviceid]['temp_c'] = None
        device_data_file = "/sys/bus/w1/devices/" + deviceid + "/w1_slave"
        if os.path.isfile(device_data_file):
            try:
                f = open(device_data_file, "r")
                data = f.read()
                f.close()
                if "YES" in data:
                    (discard, sep, reading) = data.partition(' t=')
                    values.append({'name': deviceid, 'value': float(reading) / 1000.0})
                else:
                    continue
            except:
                continue
    if len(values) != 0:
        return {'success': True, 'values': values}
    else:
        return {'success': False}

def main():
    data = read_sensors()
    if not data['success']:
        return
    row = f"{int(time.time())};"
    for val in data['values']:
        if val['value'] > 1000.0:
            val['value'] -= 4096.0
        row += f"temp;{val['name']};{val['value']:.3f};null;"
    with open(FILE, 'a') as outfile:
        outfile.write(row+"\n")


main()

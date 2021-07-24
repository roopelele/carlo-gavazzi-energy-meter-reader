#!/usr/bin/python3
import time
import os
import json
import requests

fissioPath = "/home/pi/.fissio/mittaustiedot.txt"
IP = "http://192.168.68.104/solar_api/v1/GetInverterRealtimeData.cgi"
PARAMS = {"scope": "System"}

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
    tempData = read_sensors()
    text = ""
    if tempData['success']:
        text = f"{int(time.time())};"
        for val in tempData['values']:
            if val['value'] > 1000.0:
                val['value'] -= 4096.0
            text += f"temp;{val['name']};{val['value']:.3f};null;"
        text += "\n"
    req = requests.get(IP, params=PARAMS)
    if req.status_code == 200:
        d = req.json()["Body"]["Data"]
        ATeho = d['PAC']['Values']['1']/1000.0
        if ATeho != 0:
            text += f"temp;ATeho;{ATeho:.2f};null;\n"
        text += f"temp;PTeho;{(d['DAY_ENERGY']['Values']['1']/1000.0):.2f};null;\n"
    with open(fissioPath, 'a') as outfile:
        outfile.write(text)


main()

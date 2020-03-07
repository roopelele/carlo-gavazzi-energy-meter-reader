# Carlo Gavazzi energy meter reader and heating control.
This requires a Raspberry Pi and Carlo Gavazzi em340m  power meter. Other meters may be used, but mbus.py needs to be tweaked

powerControl.py: this file controls the pins connected to heater. run this as superuser
mbus.py: this file reads Carlo gavzzi em340m energy meter and writes available energy to file. Run this as normal user

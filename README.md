# Carlo Gavazzi energy meter reader and heating control.

This is a simple program to remotely read a Carlo Gavazzi em340m power meter using M-bus, control a water heater via raspberry pi GPIO, and export statistics to [Home Assistant](https://github.com/home-assistant)

Requirements: a raspberry pi, usb-to-mbus converter, and a suitable power meter. May require tweaks to run, as this is a custom solution.

Software is intended to be used via a systemd service (example unit file provided), and requires a restart every hour due to power delivery issues potentially hanging the software randomly.

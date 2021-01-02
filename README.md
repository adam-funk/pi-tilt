# Pytilt

Tools for reading your Tilt brewing hydrometer on a Raspberry Pi and storing the results as CSV.

## Dependencies

* ```sudo apt-get install python-bluez```
* Make the bluetooth interface accessible witout being root: ```sudo setcap cap_net_raw+eip /usr/bin/python3.7```
  * Note: that command does not follow symlinks

## Running

From the directory containing pytilt.py run `python pytilt.py`

## Acknowledgements

* The code in blescan-py is adapted from https://github.com/switchdoclabs/iBeacon-Scanner-
* The Tilt UUID-to-color mapping is taken from: https://github.com/tbryant/brewometer-nodejs
* Systemd-config here: http://www.raspberrypi-spy.co.uk/2015/10/how-to-autorun-a-python-script-on-boot-using-systemd/
* https://kvurd.com/blog/tilt-hydrometer-ibeacon-data-format/
* https://tilthydrometer.com/



## TODO

Server stuff...
Running Pytilt in the background and on System Start

0. edit pytilt.service, add your key and fix paths

1. copy pytilt.service to /lib/systemd/system/

2. sudo chmod 644 /lib/systemd/system/pytilt.service

3. sudo systemctl daemon-reload

4. sudo systemctl enable pytilt.service

5. sudo reboot






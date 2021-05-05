# Pytilt

Tools for reading your Tilt brewing hydrometer on a Raspberry Pi and storing the results as CSV.

## Dependencies

* ```sudo apt-get install python3-bluez```
  * or```pip3 install PyBluez```
  * also matplotlib, numpy, pandas
* Make the bluetooth interface accessible without being root: 
  * ```sudo setcap cap_net_raw+eip /usr/bin/python3.7``` (for example)
  * Note: this command does not follow symlinks so applying it to ```/usr/bin/python3``` won't work
  * You need to run this command whenever apt updates that library

## Running

* `./pytilt.py ...`

## Acknowledgements and notes

* Forked from https://github.com/atlefren/pytilt and updated to Python 3
* The code in blescan-py is adapted from https://github.com/switchdoclabs/iBeacon-Scanner-
* The Tilt UUID-to-color mapping is taken from: https://github.com/tbryant/brewometer-nodejs
* https://kvurd.com/blog/tilt-hydrometer-ibeacon-data-format/
* https://tilthydrometer.com/

## TODO

* Use a JSON config file for storing and mailing data.
* Distinguish different Tilt colors.

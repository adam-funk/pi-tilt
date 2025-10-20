# pi-tilt

Tools for reading your Tilt hydrometer on a Raspberry Pi, storing the
results as CSV, and mailing you summaries and plots.  Intended for
use as two cron jobs (recording data and mailing plots).

## TODO

* plot: detect missing file and send sensible message

## Dependencies

* python bluez, matplotlib, pandas

  * `sudo apt-get install python3-bluez` or `pip3 install PyBluez`
  
* Make the bluetooth interface accessible without being root:

  * ```sudo setcap cap_net_raw+eip /usr/bin/python3.7``` (for example)
  
  * Note: this command does not follow symlinks so applying it to ```/usr/bin/python3``` won't work
  
  * You need to run this command whenever apt updates that library
  
* A working `/usr/sbin/sendmail` command is required (nullmailer is sufficient)

## crontab examples

* The same config file is used for both.
```
30 *     * * *  path/to/pi-tilt/record.py -c path/to/config.json 
00 09,21 * * *  path/to/pi-tilt/plot.py -c path/to/config.json
```

## config file

### required items

* `hydrometers`: map of Tilt colors to CSV filenames (absolute or
  relative to the directory the config file is in)
  
* `readings`: number of readings to take (then record the
  median of the density and temperature readings)

* `wait_seconds`: interval between readings

* `give_up_minutes`: quit after this amount of time

* `mail_from`: e-mail address

* `mail_to`: list of e-mail addresses

### optional item

* `water`: SG reading in water after changing the battery (for recalibration);
  if absent, a default of 1000 will be used

## Acknowledgements and notes

* Derived from https://github.com/atlefren/pytilt and updated to Python 3

* The code in `blescan-py` is adapted from https://github.com/switchdoclabs/iBeacon-Scanner-

* The Tilt UUID-to-color mapping is taken from: https://github.com/tbryant/brewometer-nodejs

* https://kvurd.com/blog/tilt-hydrometer-ibeacon-data-format/

* https://tilthydrometer.com/


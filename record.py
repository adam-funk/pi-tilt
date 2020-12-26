#!/usr/bin/env python3

import sys
import datetime
import time
import argparse
import csv

import bluetooth._bluetooth as bluez

import blescan as blescan


TILTS = {
        'a495bb10c5b14b44b5121370f02d74de': 'Red',
        'a495bb20c5b14b44b5121370f02d74de': 'Green',
        'a495bb30c5b14b44b5121370f02d74de': 'Black',
        'a495bb40c5b14b44b5121370f02d74de': 'Purple',
        'a495bb50c5b14b44b5121370f02d74de': 'Orange',
        'a495bb60c5b14b44b5121370f02d74de': 'Blue',
        'a495bb70c5b14b44b5121370f02d74de': 'Yellow',
        'a495bb80c5b14b44b5121370f02d74de': 'Pink',
}


def distinct(objects):
    seen = set()
    unique = []
    for obj in objects:
        if obj['uuid'] not in seen:
            unique.append(obj)
            seen.add(obj['uuid'])
    return unique


def to_celsius(fahrenheit):
    return round((fahrenheit - 32.0) / 1.8, 2)


def monitor_tilt(options):
    for i in range(0, options.nbr_readings):
        if i > 0:
            time.sleep(options.wait)
        beacons = distinct(blescan.parse_events(sock, 10))
        for beacon in beacons:
            if beacon['uuid'] in TILTS.keys():
                color = TILTS[beacon['uuid']]
                epoch = round(time.time())
                timestamp = datetime.datetime.now().isoformat())
                gravity = beacon['minor'])
                temp = to_celsius(beacon['major'])
                record_data(options, color, epoch, timestamp, gravity, temp)
    return


def record_data(options, color, epoch, timestamp, gravity, temp):
    if options.output_file:
        with open(options.output_file) as f:
            writer = csv.writer(f)
            writer.writerow([color, epoch, timestamp, gravity, temp])
    else:
        print(color, epoch, timestamp, gravity, temp)
    return


if __name__ == '__main__':
    oparser = argparse.ArgumentParser(description="record Tilt data",
                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    oparser.add_argument("-n", dest="nbr_readings", 
                         metavar="N", type=int,
                         default=1,
                         help='number of readings')

    oparser.add_argument("-o", dest="output_file",
                         default=None,
                         metavar='FILE'
                         help='output file')

    oparser.add_argument("-w", dest="wait", 
                         metavar="N", type=float,
                         default=10.0,
                         help='wait N seconds between readings')
    
    options = oparser.parse_args()

    dev_id = 0
    try:
        sock = bluez.hci_open_dev(dev_id)
        print('Starting pytilt logger')
    except:
        print('error accessing bluetooth device...')
        sys.exit(1)

    blescan.hci_le_set_scan_parameters(sock)
    blescan.hci_enable_le_scan(sock)
    monitor_tilt(options)


    

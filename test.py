#!/usr/bin/env python3

import sys
import datetime
import time

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


def monitor_tilt():
    while True:
        beacons = distinct(blescan.parse_events(sock, 10))
        print()
        print('beacons found', len(beacons))
        for beacon in beacons:
            print('beacon', beacon['uuid'])
            if beacon['uuid'] in TILTS.keys():
                print(' color', TILTS[beacon['uuid']])
                print(' timestamp', datetime.datetime.now().isoformat())
                print(' temp', to_celsius(beacon['major']))
                print(' gravity', beacon['minor'])
            else:
                print(' major', beacon['major'])
                print(' minor', beacon['minor'])
        time.sleep(10)


if __name__ == '__main__':
    dev_id = 0
    try:
        sock = bluez.hci_open_dev(dev_id)
        print('Starting pytilt logger')
    except:
        print('error accessing bluetooth device...')
        sys.exit(1)

    blescan.hci_le_set_scan_parameters(sock)
    blescan.hci_enable_le_scan(sock)
    monitor_tilt()

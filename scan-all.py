#!/usr/bin/env python3

import sys
import datetime
import time
import argparse
import csv
from collections import Counter

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


def monitor(options):
    cutoff = time.time() + 60.0 * options.minutes
    results = Counter(int)
    while time.time <= cutoff:
        beacons = distinct(blescan.parse_events(sock, 10))
        for beacon in beacons:
            uuid = beacon['uuid']
            if options.include_tilt or (uuid not in TILTS):
                key = (uuid, beacon['major'], beacon['minor'])
                results(key) += 1
        time.sleep(1)
    return results


def dump(results, options):
    keys = sorted(results.keys)
    if options.output_file:
        with open(options.output_file, 'w') as f:
            writer = csv.writer(f)
            for key in keys:
                row = list(key) + [results[key]]
                writer.writerow(row)
    else:
        for key in keys:
            row = tuple(list(key) + [results[key]])
            print('%32s %5d %5d %5d' + row)
    return
                                   

if __name__ == '__main__':
    oparser = argparse.ArgumentParser(description="Scan for bluetooth beacons",
                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    oparser.add_argument("-m", dest="minutes", 
                         metavar="N", type=int,
                         default=1,
                         help='nbr of minutes to scan')

    oparser.add_argument("-o", dest="output_file",
                         default=None,
                         metavar='FILE',
                         help='output file')

    oparser.add_argument("-T", dest="include_tilt",
                         default=False,
                         action='store_true',
                         help='include Tilt hydrometers')
    
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
    results = monitor(options)
    dump(results, options)

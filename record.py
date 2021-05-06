#!/usr/bin/env python3

import sys
import datetime
import time
import argparse
import csv
import os
import json
import statistics

from collections import defaultdict

import bluetooth._bluetooth as bluez
import blescan as blescan


TILTS = {
        'a495bb10c5b14b44b5121370f02d74de': 'red',
        'a495bb20c5b14b44b5121370f02d74de': 'green',
        'a495bb30c5b14b44b5121370f02d74de': 'black',
        'a495bb40c5b14b44b5121370f02d74de': 'purple',
        'a495bb50c5b14b44b5121370f02d74de': 'orange',
        'a495bb60c5b14b44b5121370f02d74de': 'blue',
        'a495bb70c5b14b44b5121370f02d74de': 'yellow',
        'a495bb80c5b14b44b5121370f02d74de': 'pink',
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
    return round((fahrenheit - 32.0) / 1.8, 1)


def keep_going(cutoff):
    if cutoff == None:
        return True
    return time.time() < cutoff


def monitor_tilt(config, base_dir, options):
    epoch_times = defaultdict(list)
    gravities = defaultdict(list)
    fahrenheits = defaultdict(list)

    try:
        cutoff  = time.time() + 60 * config['readings']['give_up_minutes']
    except KeyError:
        cutoff = 0

    try:
        nbr_readings = options['readings']['number']
    except KeyError:
        nbr_readings = 1

    try:
        wait_seconds = options['readings']['wait_seconds']
    except KeyError:
        wait_seconds = 1
        
    for i in range(nbr_readings):
        if options.verbose:
            print('Reading', i+1, 'of', options.nbr_readings)
        if (i > 0) and keep_going(cutoff):
            if options.verbose:
                print('Waiting', wait_seconds, '...')
            time.sleep(wait_seconds)
        found = False
        while keep_going(cutoff) and (not found):
            beacons = distinct(blescan.parse_events(sock, 10))
            if options.verbose:
                print('Found', len(beacons), 'beacons')
            for beacon in beacons:
                if beacon['uuid'] in TILTS.keys():
                    found = True
                    color = TILTS[beacon['uuid']]
                    epoch_times[color].append(round(time.time()))
                    gravities[color].append(beacon['minor'])
                    fahrenheits[color].append(beacon['major'])
                    if options.verbose:
                        print(color, *epoch_times[color])
                        print(*gravities[color])
                        print(*fahrenheits[color])
    for color, epochs in epoch_times.items():
        readings = len(epochs)
        if readings:
            epoch = round(statistics.mean(epochs))
            timestamp = datetime.datetime.now().isoformat(timespec='seconds')
            gravity = round(statistics.median(gravities[color]), 1)
            fahrenheit = round(statistics.median(fahrenheits[color]), 1)
            celsius = to_celsius(fahrenheit)
            record_data(options, [color, epoch, timestamp, gravity, celsius, fahrenheit, readings])
        else:
            # empty list of readings
            # empty string column will produce NaN in pandas
            record_data(config, base_dir, options, color, [color, epoch, timestamp, '', '', '', readings])
    return


def record_data(config, base_dir, options, color, data):
    output_file = config.get('hydrometers', []).get(color, None)
    if output_file:
        output_path = os.path.join(base_dir, output_file)
        with open(output_path, 'a') as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(data)
        if options.verbose:
            print('Got', *data)
    else:
        print('Output', *data)
    return


if __name__ == '__main__':
    oparser = argparse.ArgumentParser(description="record Tilt hydrometer data",
                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    oparser.add_argument("-c", dest="config_file",
                         required=True,
                         metavar="JSON",
                         help="JSON config file")

    oparser.add_argument("-v", dest="verbose",
                         default=False,
                         action='store_true',
                         help='verbose for debugging')

    options = oparser.parse_args()

    base_dir = os.path.dirname(options.config_file)

    with open(options.config_file, 'r') as f:
        config = json.load(f)

    dev_id = 0
    try:
        sock = bluez.hci_open_dev(dev_id)
    except:
        print('error accessing bluetooth device...')
        sys.exit(1)

    blescan.hci_le_set_scan_parameters(sock)
    blescan.hci_enable_le_scan(sock)
    monitor_tilt(config, base_dir, options)



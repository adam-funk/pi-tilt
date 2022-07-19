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
import blescan

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
    return time.time() < cutoff


def epoch_to_timestamp(epoch):
    return datetime.datetime.fromtimestamp(epoch).isoformat(timespec='seconds')


def collect_data(config0, verbose):
    cutoff = time.time() + 60 * config0['give_up_minutes']
    nbr_readings = config0['readings']
    wait_seconds = config0['wait_seconds']
    recordings = defaultdict(list)
    # str color -> list of (epoch, grav, F) tuples

    start_epoch = round(time.time())

    for i in range(nbr_readings):
        if verbose:
            print('Reading', i + 1, 'of', nbr_readings)
        found = False
        while keep_going(cutoff) and (not found):
            beacons = distinct(blescan.parse_events(sock, 10))
            if verbose:
                print('Found', len(beacons), 'beacons')
            for beacon in beacons:
                if beacon['uuid'] in TILTS.keys():
                    found = True
                    color = TILTS[beacon['uuid']]
                    epoch = round(time.time())
                    gravity = beacon['minor']
                    fahrenheit = beacon['major']
                    recordings[color].append((epoch, gravity, fahrenheit))
                    if verbose:
                        print(color, epoch, gravity, fahrenheit)
        if (i < nbr_readings - 1) and keep_going(cutoff):
            if verbose:
                print('Waiting', wait_seconds, '...')
            time.sleep(wait_seconds)
    return start_epoch, recordings


def process_data(config0, recordings, default_epoch0, verbose):
    default_timestamp = epoch_to_timestamp(default_epoch0)
    results = []
    # list of lists:
    # color, epoch, timestamp, gravity, celsius, fahrenheit, readings
    for color in config0['hydrometers'].keys():
        if color in recordings:
            readings = len(recordings[color])
            epochs = [t[0] for t in recordings[color]]
            gravities = [t[1] for t in recordings[color]]
            fahrenheits = [t[2] for t in recordings[color]]
            epoch = round(statistics.mean(epochs))
            timestamp = epoch_to_timestamp(epoch)
            gravity = round(statistics.median(gravities), 1)
            fahrenheit = round(statistics.median(fahrenheits), 1)
            celsius = to_celsius(fahrenheit)
            results.append([color, epoch, timestamp, gravity, celsius, fahrenheit, readings])
        else:
            results.append([color, default_epoch0, default_timestamp, '', '', '', 0])
    if verbose:
        for result in results:
            print(*result)
    return results


def store_data(config0, base_dir0, verbose, data_lines):
    for data_line in data_lines:
        color = data_line[0]
        output_file = config0.get('hydrometers', []).get(color, None)
        if output_file:
            output_path = os.path.join(base_dir0, output_file)
            if verbose:
                print(f'Output: {output_path}')
            with open(output_path, 'a') as f0:
                writer = csv.writer(f0, lineterminator='\n')
                writer.writerow(data_line)
            if verbose:
                print('Got', *data_line)
        else:
            print('Output', *data_line)
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
    if options.verbose:
        print(f'Config:  {options.config_file}')
        print(f'Basedir: {base_dir}')

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
    default_epoch, raw_data = collect_data(config, options.verbose)
    processed_data = process_data(config, raw_data, default_epoch, options.verbose)
    store_data(config, base_dir, options.verbose, processed_data)

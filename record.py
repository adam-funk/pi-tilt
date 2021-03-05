#!/usr/bin/env python3

import sys
import datetime
import time
import argparse
import csv
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


def monitor_tilt(options):
    epoch_times = defaultdict(list)
    gravities = defaultdict(list)
    fahrenheits = defaultdict(list)
    
    if options.give_up:
        cutoff  = time.time() + 60 * options.give_up
    else:
        cutoff = 0
        
    for i in range(0, options.nbr_readings):
        if options.verbose:
            print('Starting', i, 'of', options.nbr_readings)
        if (i > 0) and keep_going(cutoff):
            if options.verbose:
                print('Waiting', options.wait, '...')
            time.sleep(options.wait)
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
                        print(color, *epoch_times)
                        print(*gravities)
                        print(*fahrenheits)
    for color, epochs in epoch_times.items():
        epoch = round(statistics.mean(epochs))
        timestamp = datetime.datetime.now().isoformat(timespec='seconds')
        gravity = round(statistics.median(gravities[color]), 1)
        fahrenheit = round(statistics.medin(fahrenheits[color]), 1)
        celsius = to_celsius(fahrenheit)
        readings = len(epochs)
        record_data(options, color, epoch, timestamp, gravity, celsius, fahrenheit, readings)
    return


def record_data(options, data):
    if options.output_file:
        with open(options.output_file, 'a') as f:
            writer = csv.writer(f, lineterminator='\n')
            writer.writerow(data)
        if options.verbose:
            print('Got', *data)
    else:
        print(*data)
    return


if __name__ == '__main__':
    oparser = argparse.ArgumentParser(description="record Tilt data",
                                      formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    oparser.add_argument("-n", dest="nbr_readings", 
                         metavar="N", type=int,
                         default=1,
                         help='number of readings ')

    oparser.add_argument("-o", dest="output_file",
                         default=None,
                         metavar='FILE',
                         help='output file')

    oparser.add_argument("-v", dest="verbose",
                         default=False,
                         action='store_true',
                         help='verbose for debugging')

    oparser.add_argument("-w", dest="wait", 
                         metavar="N", type=float,
                         default=10.0,
                         help='wait N seconds between readings')
    
    oparser.add_argument("-x", dest="give_up", 
                         metavar="N", type=float,
                         default=10.0,
                         help='give up after N minutes')
    
    options = oparser.parse_args()

    dev_id = 0
    try:
        sock = bluez.hci_open_dev(dev_id)
        #print('Starting pytilt logger')
    except:
        print('error accessing bluetooth device...')
        sys.exit(1)

    blescan.hci_le_set_scan_parameters(sock)
    blescan.hci_enable_le_scan(sock)
    monitor_tilt(options)


    

#!/usr/bin/env python3
import argparse
import datetime
import json
import os
import subprocess
import warnings
from email.message import EmailMessage
from io import BytesIO

import numpy as np
import pandas as pd
from matplotlib import dates
from matplotlib.figure import Figure

FIG_SIZE = (15, 6)
IMAGE_TYPE = 'png'


# https://stackoverflow.com/questions/4931376/generating-matplotlib-graphs-without-a-running-x-server
# https://matplotlib.org/gallery/text_labels_and_annotations/date.html
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.subplots.html#matplotlib.pyplot.subplots
# https://matplotlib.org/api/dates_api.html#matplotlib.dates.MonthLocator
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
# https://matplotlib.org/tutorials/introductory/pyplot.html
# using Figure instead of pyplot
# https://gist.github.com/matthewfeickert/84245837f09673b2e7afea929c016904


def meanr(x):
    # ignore NaN (blank fields in the CSV) and averages over missing times
    with warnings.catch_warnings():
        warnings.filterwarnings(action='ignore', category=RuntimeWarning, message='Mean of empty slice')
        result = round(np.nanmean(x), 1)
    return result


def medianr(x):
    # ignore NaN (blank fields in the CSV) and averages over missing times
    with warnings.catch_warnings():
        warnings.filterwarnings(action='ignore', category=RuntimeWarning, message='Mean of empty slice')
        result = round(np.nanmedian(x), 1)
    return result


def get_data(input_file):
    data0 = pd.read_csv(input_file, names=['color', 'epoch', 'iso', 'sg', 'c', 'f', 'n', 'raw_sg'],
                        index_col='epoch')
    data0['time'] = pd.to_datetime(data0['iso'])
    data0['date'] = data0['time'].dt.date
    data0['c'] = round(data0['c'], 1)
    # aggregated by date
    columns = [min, meanr, medianr, max]
    with warnings.catch_warnings():
        warnings.filterwarnings(action='ignore', message='All-NaN slice encountered')
        date_data = data0.groupby('date').agg({'sg': columns,
                                               'c': columns}).rename(columns={'meanr': 'mean', 'medianr': 'mdn'})
    return data0, date_data


def make_plots(data0, data_by_date0):
    html_days = data_by_date0.to_html()
    minmax = [[data0['sg'].max(), data0['c'].max()], [data0['sg'].min(), data0['c'].min()]]
    mm_df = pd.DataFrame(minmax, columns=['sg', 'c'], index=['max', 'min'])
    html_overall = mm_df.to_html()

    days_locator = dates.DayLocator(interval=1)
    days_format = dates.DateFormatter('%d')

    buffer0 = BytesIO()
    fig4 = Figure(figsize=FIG_SIZE)
    ax4a = fig4.subplots()
    ax4a.xaxis.set_major_locator(days_locator)
    ax4a.xaxis.set_major_formatter(days_format)
    ax4a.format_xdata = days_format
    ax4b = ax4a.twinx()
    ax4b.xaxis.set_major_locator(days_locator)
    ax4b.xaxis.set_major_formatter(days_format)
    ax4b.format_xdata = days_format
    ax4b.grid(True, which='both')
    ax4b.plot(data0['time'], data0['c'], color="red")
    ax4a.plot(data0['time'], data0['sg'], color="purple")
    fig4.legend(['sg', 'c'], loc='center right')
    fig4.savefig(buffer0, dpi=200, format=IMAGE_TYPE)

    buffer_sg_days = BytesIO()
    fig2 = Figure(figsize=FIG_SIZE)
    ax2 = fig2.subplots()
    ax2.xaxis.set_major_locator(days_locator)
    ax2.xaxis.set_major_formatter(days_format)
    ax2.format_xdata = days_format
    ax2.grid(True, which='both')
    ax2.plot(data_by_date0.index, data_by_date0['sg'])
    fig2.savefig(buffer_sg_days, dpi=200, format=IMAGE_TYPE)

    buffer_c_days = BytesIO()
    fig3 = Figure(figsize=FIG_SIZE)
    ax3 = fig3.subplots()
    ax3.xaxis.set_major_locator(days_locator)
    ax3.xaxis.set_major_formatter(days_format)
    ax3.format_xdata = days_format
    ax3.grid(True, which='both')
    ax3.plot(data_by_date0.index, data_by_date0['c'])
    fig3.savefig(buffer_c_days, dpi=200, format=IMAGE_TYPE)

    return html_days, html_overall, buffer0, buffer_sg_days, buffer_c_days


def send_mail(message):
    subprocess.run(["/usr/sbin/sendmail", "-t", "-oi"], input=message.as_bytes())
    return


def add_image_buffer(buffer0: BytesIO, mail0: EmailMessage):
    buffer0.seek(0)
    image = buffer0.read()
    mail0.add_attachment(image, disposition='inline',
                         maintype='image', subtype=IMAGE_TYPE)
    return


def add_html(html: str, mail0: EmailMessage):
    # https://stackoverflow.com/questions/56711321/addng-attachment-to-an-emailmessage-raises-typeerror-set-text-content-got-an
    # add_attachment accepts a maintype argument if the content is bytes, but not if the content is str
    mail0.add_attachment(html.encode('utf-8'), disposition='inline',
                         maintype='text', subtype='html')


oparser = argparse.ArgumentParser(description="Mail summary and plots of Tilt hydrometer data",
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)

oparser.add_argument("-c", dest="config_file",
                     required=True,
                     metavar="JSON",
                     help="JSON config file")

oparser.add_argument('-v', dest='verbose',
                     default=False,
                     action='store_true',
                     help='verbose for debugging')

options = oparser.parse_args()

base_dir = os.path.abspath(os.path.dirname(options.config_file))

if options.verbose:
    print(f'Config:  {options.config_file}')
    print(f'Basedir: {base_dir}')

with open(options.config_file, 'r') as f:
    config = json.load(f)

for color, csv_file in config['hydrometers'].items():
    csv_path = os.path.join(base_dir, csv_file)
    if options.verbose:
        print(f'Loading CSV: {csv_path} for {color}')
    data, data_by_date = get_data(csv_path)
    html_daily, html_summary, buffer_detail, buffer_daily_sg, buffer_daily_c = make_plots(data, data_by_date)

    mail = EmailMessage()
    mail.set_charset('utf-8')
    mail_tos = config.get('mail_to', ['to@example.com'])
    mail['To'] = ', '.join(mail_tos)
    mail['From'] = config.get('mail_from', 'from@example.com')
    dt = datetime.datetime.now().strftime('%d %a %H:%M')
    mail['Subject'] = f'Hydrometer: {color} {dt}'

    add_image_buffer(buffer_detail, mail)
    add_html(html_daily, mail)
    add_image_buffer(buffer_daily_sg, mail)
    add_image_buffer(buffer_daily_c, mail)
    add_html(html_summary, mail)

    if options.verbose:
        print('Mail headers:')
        for k, v in mail.items():
            print(k, v)
    send_mail(mail)

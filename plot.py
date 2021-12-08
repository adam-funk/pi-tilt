#!/usr/bin/env python3

import matplotlib
matplotlib.use('Agg')
import argparse
import imghdr
import os
import smtplib
import time
import datetime
from email.message import EmailMessage
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import dates
from subprocess import Popen, PIPE

FIGSIZE = (15, 6)

# https://stackoverflow.com/questions/4931376/generating-matplotlib-graphs-without-a-running-x-server
# https://matplotlib.org/gallery/text_labels_and_annotations/date.html
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.subplots.html#matplotlib.pyplot.subplots
# https://matplotlib.org/api/dates_api.html#matplotlib.dates.MonthLocator
# https://matplotlib.org/api/_as_gen/matplotlib.pyplot.plot.html#matplotlib.pyplot.plot
# https://matplotlib.org/tutorials/introductory/pyplot.html

def meanr(x):
    # ignore NaN (blank fields in the CSV
    return round(np.nanmean(x), 1)


def medianr(x):
    # ignore NaN (blank fields in the CSV
    return round(np.nanmedian(x), 1)


def get_data(options):
    data = pd.read_csv(options.data_file, names=['color', 'epoch', 'iso', 'sg', 'c', 'f', 'n'],
                       index_col='epoch')
    data['time'] = pd.to_datetime(data['iso'])
    data['date'] = data['time'].dt.date
    data['c'] = round(data['c'], 1)
    # aggregated by date
    columns = [min, meanr, medianr, max]
    date_data = data.groupby('date').agg({'sg': columns,
                                          'c': columns}).rename(columns={'meanr': 'mean', 'medianr': 'mdn'})
    return data, date_data


def make_plots(options, data, data_by_date):
    output_dir = '/tmp/hydrometer-plots-%i' % int(time.time())
    os.mkdir(output_dir)
    f0 = os.path.join(output_dir, 'density.png')
    f1 = os.path.join(output_dir, 'temperature.png')
    f2 = os.path.join(output_dir, 'density_date.png')
    f3 = os.path.join(output_dir, 'temperature_date.png')

    date_html = data_by_date.to_html()

    minmax = [[data['sg'].max(), data['c'].max()], [data['sg'].min(), data['c'].min()]]
    mm_df = pd.DataFrame(minmax, columns=['sg', 'c'], index=['max', 'min'])
    mm_html = mm_df.to_html()

    days_locator = dates.DayLocator(interval=1)
    days_format = dates.DateFormatter('%d')
    plt.ioff()

    fig0, ax0 = plt.subplots(figsize=FIGSIZE)
    ax0.xaxis.set_major_locator(days_locator)
    ax0.xaxis.set_major_formatter(days_format)
    ax0.format_xdata = days_format
    ax0.grid(True, which='both')
    ax0.plot(data['time'], data['sg'])
    plt.savefig(f0, dpi=200)

    fig1, ax1 = plt.subplots(figsize=FIGSIZE)
    ax1.xaxis.set_major_locator(days_locator)
    ax1.xaxis.set_major_formatter(days_format)
    ax1.format_xdata = days_format
    ax1.grid(True, which='both')
    ax1.plot(data['time'], data['c'])
    plt.savefig(f1, dpi=200)

    fig2, ax2 = plt.subplots(figsize=FIGSIZE)
    ax2.xaxis.set_major_locator(days_locator)
    ax2.xaxis.set_major_formatter(days_format)
    ax2.format_xdata = days_format
    ax2.grid(True, which='both')
    ax2.plot(data_by_date.index, data_by_date['sg'])
    plt.savefig(f2, dpi=200)

    fig3, ax3 = plt.subplots(figsize=FIGSIZE)
    ax3.xaxis.set_major_locator(days_locator)
    ax3.xaxis.set_major_formatter(days_format)
    ax3.format_xdata = days_format
    ax3.grid(True, which='both')
    ax3.plot(data_by_date.index, data_by_date['c'])
    plt.savefig(f3, dpi=200)

    return date_html, mm_html, (f0, f1, f2, f3)


def send_mail(message, options1):
    # https://stackoverflow.com/questions/73781/sending-mail-via-sendmail-from-python
    if options1.mail_command:
        p = Popen(["/usr/sbin/sendmail", "-t", "-oi"], stdin=PIPE)
        p.communicate(message.as_bytes())
    else:
        with smtplib.SMTP('localhost') as s:
            s.send_message(mail)
    return


oparser = argparse.ArgumentParser(description="Plotter for temperature and humidity log",
                                  formatter_class=argparse.ArgumentDefaultsHelpFormatter)

oparser.add_argument("-d", dest="data_file",
                     required=True,
                     metavar="CSV",
                     help="CSV input file")

oparser.add_argument("-m", dest="mail",
                     action='append',
                     metavar='USER@EXAMPLE.COM',
                     help="send mail to this address")

oparser.add_argument("-M", dest='mail_command',
                     action='store_true',
                     default=False,
                     help="use mail command instead of localhost SMTP")

oparser.add_argument("-f", dest="from_mail",
                     default='from@example.com',
                     metavar='USER@EXAMPLE.COM',
                     help="send mail from this address")

options = oparser.parse_args()

data, data_by_date = get_data(options)
html0, html1, plot_files = make_plots(options, data, data_by_date)

if options.mail:
    mail = EmailMessage()
    mail.set_charset('utf-8')
    mail['To'] = ', '.join(options.mail)
    mail['From'] = options.from_mail
    mail['Subject'] = 'Hydrometer %s' % datetime.datetime.now().strftime('%a %H:%M')

    # https://stackoverflow.com/questions/56711321/addng-attachment-to-an-emailmessage-raises-typeerror-set-text-content-got-an
    # accepts a maintype argument if the content is bytes, but not if the content is str
    mail.add_attachment(html0.encode('utf-8'), disposition='inline',
                        maintype='text', subtype='html')

    mail.add_attachment(html1.encode('utf-8'), disposition='inline',
                        maintype='text', subtype='html')

    # https://docs.python.org/3/library/email.examples.html
    for file in plot_files:
        with open(file, 'rb') as fp:
            img_data = fp.read()
        mail.add_attachment(img_data, disposition='inline',
                            maintype='image',
                            subtype=imghdr.what(None, img_data))
    send_mail(mail, options)


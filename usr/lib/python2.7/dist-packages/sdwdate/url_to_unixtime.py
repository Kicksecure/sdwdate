#!/usr/bin/env python

## Copyright (C) 2015 troubadour <trobador@riseup.net>
## Copyright (C) 2015 Patrick Schleizer <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

import sys
import gevent.monkey
gevent.monkey.patch_socket()
from gevent import Timeout
import socks
from dateutil.parser import parse

import time

urls = []
unix_times = []

def unixtime_sanity_check(data, http_time, parsed_unixtime, url):
    try:
        unixtime_digit = int(parsed_unixtime)

    except ValueError as e:
        print >> sys.stderr, 'parsed_unixtime conversion failed!'
        print >> sys.stderr, 'data: %s' % (data)
        print >> sys.stderr, 'http_time: %s' % (http_time)
        print >> sys.stderr, 'parsed_unixtime: %s' % (parsed_unixtime)
        print >> sys.stderr, 'parsed_unixtime not numeric!'
        return
        #exit(6)

    unixtime_string_length_is = len(parsed_unixtime)
    unixtime_string_length_max = 10

    if unixtime_string_length_is > unixtime_string_length_max:
        print >> sys.stderr, 'parsed_unixtime conversion failed!'
        print >> sys.stderr, 'data: %s' % (data)
        print >> sys.stderr, 'http_time: %s' % (http_time)
        print >> sys.stderr, 'parsed_unixtime: %s' % (parsed_unixtime)
        print >> sys.stderr, 'unixtime_string_length_is: %s' % (unixtime_string_length_is)
        print >> sys.stderr, 'unixtime_string_length_max: %s' % (unixtime_string_length_max)
        print >> sys.stderr, 'parsed_unixtime has excessive string length!'
        return
        #sys.exit(7)

    urls.append(url)
    unix_times.append(parsed_unixtime)

def http_time_to_parsed_unixtime(data, http_time, url):
    try:
        ## Thanks to:
        ## eumiro
        ## http://stackoverflow.com/a/3894047/2605155
        parsed_unixtime = parse(http_time).strftime('%s')

    except ValueError as e:
        print >> sys.stderr, 'Parsing http_time from server failed!'
        print >> sys.stderr, 'HTTP header data:\n%s' % (data)
        print >> sys.stderr, 'http_time: %s' % (http_time)
        print >> sys.stderr, 'dateutil ValueError: %s' % (e)
        return
        #sys.exit(5)

    #print(parsed_unixtime)
    unixtime_sanity_check(data, http_time, parsed_unixtime, url)

def data_to_http_time(data, date_string_start_position, url):
    http_time = ''
    ## max accepted string length.
    http_time = data[date_string_start_position:date_string_start_position + 29].strip()

    http_time_string_length = len(http_time)

    ## min string length = max string length.
    if http_time_string_length < 29:
        print >> sys.stderr, 'HTTP header date string too short.'
        print >> sys.stderr, 'HTTP header date length: %s' % http_time_string_length
        print >> sys.stderr, 'HTTP header data:\n%s' % (data)
        print >> sys.stderr, 'HTTP header date value: "%s"' % (http_time)
        return
        #sys.exit(4)

    #print http_time
    http_time_to_parsed_unixtime(data, http_time, url)

def data_to_date_string_start_position(data, url):
    date_string_start_position = data.find('Date:')

    if date_string_start_position == -1:
        ## not found, check if lowercase.
        date_string_start_position = data.find('date:')

    if date_string_start_position == -1:
        ## "Date:" not found.
        print >> sys.stderr, 'Parsing HTTP header date failed: "%s"' % (url)
        #print 'HTTP header data:\n%s' % (data)
        return
        #sys.exit(3)

    else:
        date_string_start_position = date_string_start_position + 6
        data_to_http_time(data, date_string_start_position, url)


def request_data_from_remote_server(socket_ip, socket_port, url, remote_port):
    s = socks.socksocket()
    s.setproxy(socks.PROXY_TYPE_SOCKS5, socket_ip, socket_port)
    #print 'THREAD STARTED "%s"' % url

    try:
        s.connect((url, remote_port))
        print 'CONNECTED "%s"' % url

    ## Should occur only when tor is not running (stopped, crashed,
    ## gateway shut down...)
    except socks.GeneralProxyError as e:
        error = '%s' % (e)
        urls.append(error)
        return urls

    except IOError as e:
        ## {{ wheezy compatibility
        if str(e).startswith('__init__'):
            print >> sys.stderr, 'connect error: URL "%s" not found.' % url
        else:
        ## }}
            ## Should return the errors to sdwdate for logging.
            print >> sys.stderr, '"%s" %s ' % (url, e)
        return
        #sys.exit

    s.send('HEAD / HTTP/1.0\r\n\r\n')
    data = ''
    buf = s.recv(1024)
    print 'SENDING "%s"' % url
    while len(buf):
        data += buf
        buf = s.recv(1024)
    s.close()
    print 'RECEIVED "%s"' % url

    data_to_date_string_start_position(data, url)


def url_to_unixtime(remotes):
    threads = []

    timeout = gevent.Timeout()
    timer = []
    seconds = 10

    for i in range(0, len(remotes)):
        timer.append(timeout.start_new(seconds))
        args = (request_data_from_remote_server, '127.0.0.1', '9050', remotes[i], 80)
        threads.append(gevent.spawn(*args))

    for i in range(0, len(remotes)):
        try:
            threads[i].join(timeout=timer[i])

        except Timeout:
            print >> sys.stderr, '"%s" Timeout' % (threads[i].args[2])

    return urls, unix_times

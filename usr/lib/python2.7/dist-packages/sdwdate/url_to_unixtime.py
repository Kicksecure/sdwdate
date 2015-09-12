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
import re # Test
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
        error = '%s' % (e)
        urls.append(url)
        unix_times.append(error)
        return

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
        error = 'parsed_unixtime has excessive string length'
        urls.append(url)
        unix_times.append(error)
        return

    if unixtime_string_length_is < unixtime_string_length_max:
        error = 'parsed_unixtime string length too short'
        urls.append(url)
        unix_times.append(error)
        return

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
        error = '%s' % (e)
        urls.append(url)
        unix_times.append(error)
        return

    ## Tests #################################
    #parsed_unixtime = '%sA' % parsed_unixtime
    #parsed_unixtime = '%s1' % parsed_unixtime
    #parsed_unixtime = parsed_unixtime[:9]
    ##########################################
    unixtime_sanity_check(data, http_time, parsed_unixtime, url)

def data_to_http_time(data, date_string_start_position, url):
    http_time = ''
    ## max accepted string length.
    http_time = data[date_string_start_position:date_string_start_position + 29].strip()
    ## Test ###################
    #http_time = http_time[:28]
    ###########################

    http_time_string_length = len(http_time)

    ## min string length = max string length.
    if http_time_string_length < 29:
        print >> sys.stderr, 'HTTP header date string too short.'
        print >> sys.stderr, 'HTTP header date length: %s' % http_time_string_length
        print >> sys.stderr, 'HTTP header data:\n%s' % (data)
        print >> sys.stderr, 'HTTP header date value: "%s"' % (http_time)
        error = 'HTTP header date string too short.'
        urls.append(url)
        unix_times.append(error)
        return

    ## Test, replace current hour with 30 #######
    #http_time = re.sub('[hour]', '30', http_time)
    #############################################
    with open('/var/run/sdwdate/http_time', 'a') as f:
        f.write('%s\n' % http_time)
    #print http_time
    http_time_to_parsed_unixtime(data, http_time, url)

def data_to_date_string_start_position(data, url):
    ## Test ########################
    #data = re.sub('Date', 'Rate', data)
    ################################
    date_string_start_position = data.find('Date:')

    if date_string_start_position == -1:
        ## not found, check if lowercase.
        date_string_start_position = data.find('date:')

    if date_string_start_position == -1:
        ## "Date:" not found.
        print >> sys.stderr, 'Parsing HTTP header date failed: "%s"' % (url)
        error = 'Parsing HTTP header date failed'
        urls.append(url)
        unix_times.append(error)
        return

    else:
        date_string_start_position = date_string_start_position + 6
        data_to_http_time(data, date_string_start_position, url)

def request_data_from_remote_server(socket_ip, socket_port, url, remote_port):
    s = socks.socksocket()
    s.setproxy(socks.PROXY_TYPE_SOCKS5, socket_ip, socket_port)

    try:
        s.connect((url, remote_port))
        print 'CONNECTED "%s"' % url

    except IOError as e:
        error = '%s' % (e)
        urls.append(url)
        unix_times.append(error)
        return

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

    ## Clear lists.
    del urls[:]
    del unix_times[:]

    print 'GEVENT started'

    for i in range(len(remotes)):
        timer.append(timeout.start_new(seconds))
        args = (request_data_from_remote_server, '127.0.0.1', '9050', remotes[i], 80)
        threads.append(gevent.spawn(*args))

    for i in range(len(remotes)):
        try:
            threads[i].join(timeout=timer[i])
        except Timeout:
            urls.append(threads[i].args[2])
            unix_times.append('Timeout')
            gevent.kill(threads[i])

    ## Cleanup before next round.
    ## On fast retries, unfinished greenlets might be returned.
    for i in range(len(threads)):
        gevent.kill(threads[i])

    print 'GEVENT exiting'
    return urls, unix_times

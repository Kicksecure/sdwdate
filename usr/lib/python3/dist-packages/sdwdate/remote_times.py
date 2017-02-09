#!/usr/bin/python3 -u

## Copyright (C) 2015 troubadour <trobador@riseup.net>
## Copyright (C) 2015 Patrick Schleizer <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

import gevent
from gevent.subprocess import Popen, PIPE

def get_time_from_servers(remotes, ip_address, port_number):
    url_to_unixtime_path = '/usr/lib/sdwdate/url_to_unixtime'

    threads = []
    urls = []
    unix_times = []
    seconds = 10

    ### Clear lists.
    del threads[:]
    del urls[:]
    del unix_times[:]

    for i in range(len(remotes)):
        threads.append(Popen([url_to_unixtime_path,
                              ip_address,
                              port_number,
                              remotes[i],
                              '80',
                              '0'], stdout=PIPE))

    try:
       gevent.wait(timeout=seconds)
    except:
        pass

    for i in range(len(threads)):
        if threads[i].poll() is not None:
            urls.append(remotes[i])
            reply = threads[i].stdout.read()
            unix_times.append(reply.strip())
        else:
            urls.append(remotes[i])
            unix_times.append('Timeout')
        try:
           threads[i].terminate()
        except:
           pass

    return urls, unix_times

if __name__ == "__main__":
    get_time_from_servers(remotes)

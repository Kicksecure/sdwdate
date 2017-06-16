#!/usr/bin/python3 -u

## Copyright (C) 2015 troubadour <trobador@riseup.net>
## Copyright (C) 2015 Patrick Schleizer <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

import sys
import gevent
from gevent.subprocess import Popen, PIPE
import datetime

def get_time_from_servers(remotes, ip_address, port_number):
    url_to_unixtime_path = '/usr/lib/sdwdate/url_to_unixtime'

    threads = []
    urls = []
    unix_times = []
    seconds = 50
    do_exit = False

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
    except KeyboardInterrupt:
       do_exit = True
       print("remotes.py: KeyboardInterrupt received.")
    except SystemExit:
       do_exit = True
       print("remotes.py: sigterm received.")
    except:
       print("Unexpected error:", sys.exc_info()[0])
       pass

    if do_exit == True:
       for i in range(len(threads)):
           try:
               threads[i].terminate()
           except:
               pass
       urls.append(remotes[i])
       unix_times.append('sigterm')
       return urls, unix_times

    for i in range(len(threads)):
        if threads[i].poll() is not None:
            urls.append(remotes[i])
            timestamp = threads[i].stdout.read().strip().decode("utf-8")
            time_format = datetime.datetime.utcfromtimestamp(int(timestamp).strftime('%Y-%m-%d %H:%M:%S')
            unix_times.append(time_format + " / " + timestamp)
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

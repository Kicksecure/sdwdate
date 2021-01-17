#!/usr/bin/python3 -u

## Copyright (C) 2015 troubadour <trobador@riseup.net>
## Copyright (C) 2015 - 2020 ENCRYPTED SUPPORT LP <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

import sys
import gevent
import shlex
from gevent.subprocess import Popen, PIPE

def get_time_from_servers(remotes, ip_address, port_number):
    threads = []
    urls = []
    unix_times = []
    stderr_list = []
    seconds = 50
    do_exit = False
    remote_port = "80"
    ## TODO: set to "false"
    url_to_unixtime_debug = "true"

    ### Clear lists.
    del threads[:]
    del urls[:]
    del unix_times[:]
    del stderr_list[:]

    for i in range(len(remotes)):
      url_to_unixtime_command = "url_to_unixtime" + " " + ip_address + " " + port_number + " " + remotes[i] + " " + remote_port + " " + url_to_unixtime_debug

      ## Avoid Popen shell=True.
      url_to_unixtime_command = shlex.split(url_to_unixtime_command)

      print("remote_times.py: url_to_unixtime_command: ", str(url_to_unixtime_command))

      threads.append(Popen(url_to_unixtime_command, stdout=PIPE, stderr=PIPE))

    try:
       gevent.wait(timeout=seconds)
    except KeyboardInterrupt:
       do_exit = True
       print("remote_times.py: KeyboardInterrupt received.")
    except SystemExit:
       do_exit = True
       print("remote_times.py: sigterm received.")
    except:
       print("remote_times.py: unexpected error:", sys.exc_info()[0])
       pass

    if do_exit == True:
       for i in range(len(threads)):
           try:
               threads[i].terminate()
           except:
               pass
       urls.append(remotes[i])
       unix_times.append('sigterm')
       stderr_list.append('sigterm')
       return urls, unix_times, stderr_list

    for i in range(len(threads)):
        if threads[i].poll() is not None:
            urls.append(remotes[i])
            stdout = threads[i].stdout.read()
            stderr = threads[i].stderr.read()
            ## Sanitize response. Log if response causes error.
            ## This can be placed in a separate file/process.
            try:
                stdout = stdout.strip()
                stderr = stderr.strip()
                #print("remote_times.py: url_to_unixtime: stdout: ", stdout)
                #print("remote_times.py: url_to_unixtime: stderr: ", stderr)
                unix_times.append(stdout)
                stderr_list.append(stderr)
            except:
                ## Log
                unix_times.append('Error sanitizing output!')
                stderr_list.append('Error sanitizing output!')
        else:
            urls.append(remotes[i])
            unix_times.append('Timeout')
            stderr_list.append('Timeout')
        try:
           threads[i].terminate()
        except:
           pass

    return urls, unix_times, stderr_list

if __name__ == "__main__":
    get_time_from_servers(remotes)

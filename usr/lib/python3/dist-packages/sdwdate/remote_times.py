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
    stdout_list = []
    stderr_list = []
    seconds = 50
    do_exit = False
    remote_port = "80"
    ## TODO: set to "false"
    url_to_unixtime_debug = "true"

    ### Clear lists.
    del threads[:]
    del urls[:]
    del stdout_list[:]
    del stderr_list[:]

    for i in range(len(remotes)):
      url_to_unixtime_command = "url_to_unixtime" + " " + ip_address + " " + port_number + " " + remotes[i] + " " + remote_port + " " + url_to_unixtime_debug

      print("remote_times.py: url_to_unixtime_command:", str(url_to_unixtime_command))

      ## Avoid Popen shell=True.
      url_to_unixtime_command = shlex.split(url_to_unixtime_command)

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
       stdout_list.append('sigterm')
       stderr_list.append('sigterm')
       return urls, stdout_list, stderr_list

    for i in range(len(threads)):
        if threads[i].poll() is not None:
            urls.append(remotes[i])
            stdout = threads[i].stdout.read()
            stderr = threads[i].stderr.read()
            returncode = threads[i].returncode
            try:
                stdout = stdout.strip()
                stderr = stderr.strip()
                #print("remote_times.py: url_to_unixtime: stdout: ", stdout)
                #print("remote_times.py: url_to_unixtime: stderr: ", stderr)
                stdout_to_append = ""
                stderr_to_append = ""
                stdout_to_append += str(stdout)
                stderr_to_append += str(stderr)
                if not returncode == 0:
                    stdout_to_append += " | non-zero exit code: " + str(returncode)
                    stderr_to_append += " | non-zero exit code: " + str(returncode)
                stdout_list.append(stdout_to_append)
                stderr_list.append(stderr_to_append)
            except:
                ## Log
                stdout_list.append('Error sanitizing output!')
                stderr_list.append('Error sanitizing output!')
        else:
            urls.append(remotes[i])
            stdout_list.append('Timeout')
            stderr_list.append('Timeout')
        try:
           threads[i].terminate()
        except:
           pass

    return urls, stdout_list, stderr_list

if __name__ == "__main__":
    get_time_from_servers(remotes)

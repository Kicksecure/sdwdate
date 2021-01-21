#!/usr/bin/python3 -u

## Copyright (C) 2015 troubadour <trobador@riseup.net>
## Copyright (C) 2015 - 2020 ENCRYPTED SUPPORT LP <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

import sys
import gevent
import shlex
import time
from gevent.subprocess import Popen, PIPE
import subprocess

from subprocess import Popen
from threading import Thread
import time

start_unixtime = [None] * 5
took_time = [None] * 5

class Process(Popen):
    def register_callback(self, callback, *args, **kwargs):
        Thread(target=self.__bootstrap, args=(callback, args, kwargs)).start()
    def __bootstrap(self, callback, args, kwargs):
        self.wait()
        callback(*args, **kwargs)

def get_time_from_servers_callback(handle, i):
    #print("get_time_from_servers_callback i: " + str(i))
    #print("get_time_from_servers_callback exit code: " + str(handle.returncode))
    end_unixtime = time.time()
    took_time[i] = end_unixtime - start_unixtime[i]
    #print("get_time_from_servers_callback took_time: " + str(took_time[i]))

def get_time_from_servers(list_of_remote_servers, proxy_ip_address, proxy_port_number):
    urls = []
    stdout_list = []
    stderr_list = []
    took_time_list = []
    timeout_seconds = 50
    do_exit = False
    remote_port = "80"
    ## TODO: set to "false"
    url_to_unixtime_debug = "true"

    ### Clear lists.
    del urls[:]
    del stdout_list[:]
    del stderr_list[:]
    del took_time_list[:]

    handle = [None] * 5

    for i in range(len(list_of_remote_servers)):
      url_to_unixtime_command = "url_to_unixtime" + " " + proxy_ip_address + " " + proxy_port_number + " " + list_of_remote_servers[i] + " " + remote_port + " " + url_to_unixtime_debug

      print("remote_times.py: url_to_unixtime_command:", str(url_to_unixtime_command))

      ## Avoid Popen shell=True.
      url_to_unixtime_command = shlex.split(url_to_unixtime_command)

      start_unixtime[i] = time.time()

      handle[i] = Process(url_to_unixtime_command, stdout=PIPE, stderr=PIPE)
      handle[i].register_callback(get_time_from_servers_callback, handle[i], i)

    for i in range(len(list_of_remote_servers)):
      try:
         handle[i].wait(timeout=timeout_seconds)
         print("remote_times.py: i:" + str(i) + " | wait_ok")
      except KeyboardInterrupt:
         do_exit = True
         print("remote_times.py: i:" + str(i) + " | KeyboardInterrupt received.")
         break
      except SystemExit:
         do_exit = True
         print("remote_times.py: i:" + str(i) + " | SystemExit received.")
         break
      except subprocess.TimeoutExpired:
         print("remote_times.py: i:" + str(i) + " | timeout")
         handle[i].kill()
         ## Results in invoking get_time_from_servers_callback.
         handle[i].wait()
      except:
         error_message = str(sys.exc_info()[0])
         print("remote_times.py: i:" + str(i) + " | unknown error. sys.exc_info: " + error_message)
         handle[i].kill()
         ## Results in invoking get_time_from_servers_callback.
         handle[i].wait()
         ## Wait for other (i).
         #break

    if do_exit == True:
       for i in range(len(list_of_remote_servers)):
           try:
               handle[i].kill()
           except:
               pass
           urls.append(list_of_remote_servers[i])
           stdout_list.append('sigterm')
           stderr_list.append('sigterm')
           took_time_list.append(0)
       return urls, stdout_list, stderr_list, took_time_list

    for i in range(len(list_of_remote_servers)):
       took_time_list.append(took_time[i])
       urls.append(list_of_remote_servers[i])
       returncode = handle[i].returncode

       ## bytes
       stdout = handle[i].stdout.read()
       stderr = handle[i].stderr.read()

       #print("remote_times.py: i: " + str(i))
       #print("remote_times.py: stdout: " + str(stdout))
       #print("remote_times.py: took_time[i]: " + str(took_time[i]))
       #print("remote_times.py: returncode: " + str(returncode))

       if not returncode == 0:
          ## str
          stdout_to_append = ""
          stdout_to_append += str(stdout)
          stdout_to_append += " | non-zero exit code: " + str(returncode)
          stdout_list.append(stdout_to_append)
          stderr_to_append = ""
          stdout_to_append += str(stderr)
          stderr_to_append += " | non-zero exit code: " + str(returncode)
          stderr_list.append(stderr_to_append)
       else:
          stdout_list.append(stdout)
          stderr_list.append(stderr)

    print("remote_times.py: urls:")
    print(str(urls))
    print("remote_times.py: stdout_list:")
    print(str(stdout_list))
    print("remote_times.py: stderr_list:")
    print(str(stderr_list))
    print("remote_times.py: took_time_list:")
    print(str(took_time_list))

    return urls, stdout_list, stderr_list, took_time_list

if __name__ == "__main__":
    get_time_from_servers(list_of_remote_servers)

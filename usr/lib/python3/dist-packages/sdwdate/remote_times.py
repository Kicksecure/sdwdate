#!/usr/bin/python3 -u

## Copyright (C) 2015 troubadour <trobador@riseup.net>
## Copyright (C) 2015 - 2020 ENCRYPTED SUPPORT LP <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

import signal
import sys
import gevent
import shlex
import time
from gevent.subprocess import Popen, PIPE
import subprocess

from subprocess import Popen
from threading import Thread
import time

import concurrent.futures
import subprocess
from concurrent.futures import ThreadPoolExecutor

start_unixtime = [None] * 5
took_time = [None] * 5

def run_command(i, url_to_unixtime_command):
    timeout_seconds = 50
    do_exit = False

    print("remote_times.py: url_to_unixtime_command: " + str(url_to_unixtime_command))
    ## Avoid Popen shell=True.
    url_to_unixtime_command = shlex.split(url_to_unixtime_command)

    start_unixtime[i] = time.time()

    p = subprocess.Popen(url_to_unixtime_command, stdout=PIPE, stderr=PIPE)

    try:
      p.wait(timeout_seconds)
      ## Process already terminated before timeout.
      print("remote_times.py: i: " + str(i) + " | wait_ok")
    except subprocess.TimeoutExpired:
      print("remote_times.py: i: " + str(i) + " | timeout")
      ## Timeout hit. Kill process.
      p.kill()
    except:
      error_message = str(sys.exc_info()[0])
      print("remote_times.py: i: " + str(i) + " | unknown error. sys.exc_info: " + error_message)
      p.kill()

    ## Do not return from this function until killing of the process is complete.
    p.wait()
    end_unixtime = time.time()
    took_time[i] = end_unixtime - start_unixtime[i]
    return p

def get_time_from_servers(list_of_remote_servers, proxy_ip_address, proxy_port_number):
    urls = []
    stdout_list = []
    stderr_list = []
    took_time_list = []
    remote_port = "80"
    ## TODO: set to "false"
    url_to_unixtime_debug = "true"

    ## Clear lists.
    del urls[:]
    del stdout_list[:]
    del stderr_list[:]
    del took_time_list[:]

    handle = [None] * 5
    future = [None] * 5

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for i in range(len(list_of_remote_servers)):
            url_to_unixtime_command = "url_to_unixtime" + " " + proxy_ip_address + " " + proxy_port_number + " " + list_of_remote_servers[i] + " " + remote_port + " " + url_to_unixtime_debug
            future[i] = executor.submit(run_command, i, url_to_unixtime_command)

    for i in range(len(list_of_remote_servers)):
        handle[i] = future[i].result()

    for i in range(len(list_of_remote_servers)):
        took_time_list.append(took_time[i])
        urls.append(list_of_remote_servers[i])
        returncode = handle[i].returncode

        ## bytes
        stdout, stderr = handle[i].communicate()

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

def remote_times_signal_handler(signum, frame):
    print("remote_times_signal_handler OK")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, remote_times_signal_handler)
    signal.signal(signal.SIGINT, remote_times_signal_handler)
    #list_of_remote_servers = [ "http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/a", "http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/b", "http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/c" ]
    #list_of_remote_servers = [ "http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/a" ]
    proxy_ip_address = "127.0.0.1"
    proxy_port_number = "9050"
    get_time_from_servers(list_of_remote_servers, proxy_ip_address, proxy_port_number)

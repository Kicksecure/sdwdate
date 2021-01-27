#!/usr/bin/python3 -u

## Copyright (C) 2015 troubadour <trobador@riseup.net>
## Copyright (C) 2015 - 2020 ENCRYPTED SUPPORT LP <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

## Example:
## /usr/lib/python3/dist-packages/sdwdate/remote_times.py "http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/a http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/b http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/c" "127.0.0.1" "9050"

import sys
import signal
import sys
import shlex
import time
import subprocess
from subprocess import Popen, PIPE
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor

def run_command(i, url_to_unixtime_command):
    timeout_seconds = 50
    do_exit = False

    ## Avoid Popen shell=True.
    url_to_unixtime_command = shlex.split(url_to_unixtime_command)

    start_unixtime = time.time()

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
    took_time = end_unixtime - start_unixtime
    ## Round took_time to two digits for better readability.
    ## No other reason for rounding.
    took_time = round(took_time, 2)
    return p, took_time

def get_time_from_servers(list_of_remote_servers, proxy_ip_address, proxy_port_number):
    remote_port = "80"

    number_of_remote_servers = len(list_of_remote_servers)
    ## Example number_of_remote_servers:
    ## 3
    range_of_remote_servers = range(number_of_remote_servers)
    ## Example range_of_remote_servers:
    ## range(0, 3)

    url_to_unixtime_debug = "false"
    #url_to_unixtime_debug = "true"

    urls_list = [None] * number_of_remote_servers
    stdout_list = [None] * number_of_remote_servers
    stderr_list = [None] * number_of_remote_servers
    took_time_list = [None] * number_of_remote_servers
    handle = [None] * number_of_remote_servers
    future = [None] * number_of_remote_servers
    took_time = [None] * number_of_remote_servers
    url_to_unixtime_commands_list = [None] * number_of_remote_servers

    print("remote_times.py: url_to_unixtime_command (s):")
    for i in range_of_remote_servers:
        url_to_unixtime_commands_list[i] = "url_to_unixtime" + " " + proxy_ip_address + " " + proxy_port_number + " " + list_of_remote_servers[i] + " " + remote_port + " " + url_to_unixtime_debug
        print(url_to_unixtime_commands_list[i])

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for i in range_of_remote_servers:
            future[i] = executor.submit(run_command, i, url_to_unixtime_commands_list[i])

    for i in range_of_remote_servers:
        handle[i], took_time[i] = future[i].result()

    for i in range_of_remote_servers:
        took_time_list[i] = took_time[i]
        urls_list[i] = list_of_remote_servers[i]
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
            stdout_list[i] = stdout_to_append
            stderr_to_append = ""
            stdout_to_append += str(stderr)
            stderr_to_append += " | non-zero exit code: " + str(returncode)
            stderr_list[i] = stderr_to_append
        else:
            stdout_list[i] = stdout
            stderr_list[i] = stderr

    print("remote_times.py: urls_list:")
    print(str(urls_list))
    print("remote_times.py: stdout_list:")
    print(str(stdout_list))
    print("remote_times.py: stderr_list:")
    print(str(stderr_list))
    print("remote_times.py: took_time_list:")
    print(str(took_time_list))

    return urls_list, stdout_list, stderr_list, took_time_list

def remote_times_signal_handler(signum, frame):
    print("remote_times_signal_handler OK")
    sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGTERM, remote_times_signal_handler)
    signal.signal(signal.SIGINT, remote_times_signal_handler)
    list_of_remote_servers = sys.argv[1]
    list_of_remote_servers = list_of_remote_servers.split()
    proxy_ip_address = sys.argv[2]
    proxy_port_number = sys.argv[3]
    get_time_from_servers(list_of_remote_servers, proxy_ip_address, proxy_port_number)

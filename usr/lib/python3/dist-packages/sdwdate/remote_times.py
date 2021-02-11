#!/usr/bin/python3 -u

# Copyright (C) 2015 troubadour <trobador@riseup.net>
# Copyright (C) 2015 - 2020 ENCRYPTED SUPPORT LP <adrelanos@riseup.net>
# See the file COPYING for copying conditions.

# Example:
# /usr/lib/python3/dist-packages/sdwdate/remote_times.py "http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/a http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/b http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/c" "127.0.0.1" "9050"

import signal
import sys
import shlex
import time
import subprocess
from subprocess import Popen, PIPE
import concurrent.futures


def run_command(i, url_to_unixtime_command):
    timeout_seconds = 50

    # Avoid Popen shell=True.
    url_to_unixtime_command = shlex.split(url_to_unixtime_command)

    start_unixtime = time.time()

    process = subprocess.Popen(
        url_to_unixtime_command,
        stdout=PIPE,
        stderr=PIPE)

    try:
        process.wait(timeout_seconds)
        # Process already terminated before timeout.
        # print("remote_times.py: i: " + str(i) + " | done")
        status = "done"
    except subprocess.TimeoutExpired:
        # print("remote_times.py: i: " + str(i) + " | timeout")
        status = "timeout"
        # Timeout hit. Kill process.
        process.kill()
    except BaseException:
        error_message = str(sys.exc_info()[0])
        status = "error"
        print(
            "remote_times.py: i: " +
            str(i) +
            " | unknown error. sys.exc_info: " +
            error_message)
        process.kill()

    # Do not return from this function until killing of the process is
    # complete.
    process.wait()
    end_unixtime = time.time()
    took_time = end_unixtime - start_unixtime
    # Round took_time to two digits for better readability.
    # No other reason for rounding.
    took_time = round(took_time, 2)
    return process, took_time, status


def get_time_from_servers(
        list_of_remote_servers,
        proxy_ip_address,
        proxy_port_number):

    remote_port = "80"

    number_of_remote_servers = len(list_of_remote_servers)
    # Example number_of_remote_servers:
    # 3
    range_of_remote_servers = range(number_of_remote_servers)
    # Example range_of_remote_servers:
    # range(0, 3)

    url_to_unixtime_debug = "true"

    urls_list = [None] * number_of_remote_servers
    stdout_list = [None] * number_of_remote_servers
    stderr_list = [None] * number_of_remote_servers
    took_time_list = [None] * number_of_remote_servers
    timeout_status_list = [None] * number_of_remote_servers
    exit_code_list = [None] * number_of_remote_servers
    handle = [None] * number_of_remote_servers
    future = [None] * number_of_remote_servers
    took_time = [None] * number_of_remote_servers
    status = [None] * number_of_remote_servers
    url_to_unixtime_commands_list = [None] * number_of_remote_servers

    print("remote_times.py: url_to_unixtime_command (s):")
    for i in range_of_remote_servers:
        url_to_unixtime_commands_list[i] = "url_to_unixtime" + " " + proxy_ip_address + " " + \
            proxy_port_number + " " + list_of_remote_servers[i] + " " + remote_port + " " + url_to_unixtime_debug
        print(url_to_unixtime_commands_list[i])

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for i in range_of_remote_servers:
            future[i] = executor.submit(
                run_command, i, url_to_unixtime_commands_list[i])

    for i in range_of_remote_servers:
        handle[i], took_time[i], status[i] = future[i].result()

    for i in range_of_remote_servers:
        took_time_list[i] = took_time[i]
        timeout_status_list[i] = status[i]
        urls_list[i] = list_of_remote_servers[i]
        returncode = handle[i].returncode
        exit_code_list[i] = returncode

        # bytes
        stdout, stderr = handle[i].communicate()

        # stderr if Tor is stopped (or Tor SocksPort not reachable):
        # connect error:
        # SOCKSHTTPConnectionPool(host='sdolvtfhatvsysc6l34d65ymdwxcujausv7k5jk4cy5ttzhjoi6fzvyd.onion',
        # port=80): Max retries exceeded with url: / (Caused by
        # NewConnectionError('<urllib3.contrib.socks.SOCKSConnection object at
        # 0x7703a89cfeb8>: Failed to establish a new connection: [Errno 111]
        # Connection refused'))

        # print("remote_times.py: i: " + str(i))
        # print("remote_times.py: stdout: " + str(stdout))
        # print("remote_times.py: stderr: " + str(stderr))
        # print("remote_times.py: took_time[i]: " + str(took_time[i]))
        # print("remote_times.py: returncode: " + str(returncode))

        stdout_list[i] = stdout.decode()
        if returncode == 0:
            # example stderr:
            # data: <Response [200]>
            # http_time: Tue, 09 Feb 2021 10:35:10 GMT
            # parsed_unixtime: 1612866910
            #
            # Redacting stderr for brevity.
            stderr_list[i] = "redacted"
        else:
            stderr_list[i] = stderr.decode()

    # print("remote_times.py: urls_list:")
    # print(str(urls_list))
    # print("remote_times.py: stdout_list:")
    # print(str(stdout_list))
    # print("remote_times.py: stderr_list:")
    # print(str(stderr_list))
    # print("remote_times.py: took_time_list:")
    # print(str(took_time_list))
    # print("remote_times.py: timeout_status_list:")
    # print(str(timeout_status_list))
    # print("remote_times.py: exit_code_list:")
    # print(str(exit_code_list))

    return urls_list, stdout_list, stderr_list, took_time_list, timeout_status_list, exit_code_list


def remote_times_signal_handler(signum, frame):
    print("remote_times_signal_handler: OK")
    sys.exit(0)


def main():
    signal.signal(signal.SIGTERM, remote_times_signal_handler)
    signal.signal(signal.SIGINT, remote_times_signal_handler)
    list_of_remote_servers = sys.argv[1]
    list_of_remote_servers = list_of_remote_servers.split()
    proxy_ip_address = sys.argv[2]
    proxy_port_number = sys.argv[3]
    get_time_from_servers(
        list_of_remote_servers,
        proxy_ip_address,
        proxy_port_number
    )


if __name__ == "__main__":
    main()

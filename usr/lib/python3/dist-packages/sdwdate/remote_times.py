#!/usr/bin/python3 -su

# Copyright (C) 2015 troubadour <trobador@riseup.net>
# Copyright (C) 2015 - 2025 ENCRYPTED SUPPORT LLC <adrelanos@whonix.org>
# See the file COPYING for copying conditions.

# Example:
# sudo -u sdwdate python3 /usr/lib/python3/dist-packages/sdwdate/remote_times.py "http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/a http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/b http://www.dds6qkxpwdeubwucdiaord2xgbbeyds25rbsgr73tbfpqpt4a6vjwsyd.onion/c" "127.0.0.1" "9050"

import sys
sys.dont_write_bytecode = True

import os
import signal
import shlex
import time
import subprocess
from subprocess import Popen, PIPE
import concurrent.futures

from .config import get_comment
from .config import read_pools
from .config import time_human_readable
from .config import time_replay_protection_file_read
from .timesanitycheck import time_consensus_sanity_check
from .timesanitycheck import static_time_sanity_check


def run_command(i, url_to_unixtime_command, remote):
    timeout_seconds = 120

    # Avoid Popen shell=True.
    url_to_unixtime_command = shlex.split(url_to_unixtime_command)

    start_unixtime = time.time()

    process = subprocess.Popen(
        url_to_unixtime_command,
        stdout=PIPE,
        stderr=PIPE
    )

    try:
        process.wait(timeout_seconds)
        # Process already terminated before timeout.
        print("remote_times.py: i: " + str(i) + " | done")
        status = "done"
    except subprocess.TimeoutExpired:
        print("remote_times.py: i: " + str(i) + " | timeout_network")
        status = "timeout"
        # Timeout hit. Kill process.
        process.kill()
    except BaseException:
        error_message = str(sys.exc_info()[0])
        status = "error"
        print(
            "remote_times.py: i: " +
            str(i) +
            " | timeout_network unknown error. sys.exc_info: " +
            error_message
        )
        process.kill()

    # Do not return from this function until killing of the process is
    # complete.
    process.wait()

    end_unixtime = time.time()
    took_time = end_unixtime - start_unixtime

    # Round took_time to two digits for better readability.
    # No other reason for rounding.
    took_time = round(took_time, 2)

    temp1 = b""
    temp2 = b""

    try:
        # bytes
        temp1, temp2 = process.communicate(timeout=2)
    except subprocess.TimeoutExpired:
        print("remote_times.py: i: " + str(i) + " | timeout_read")
        status = "error"
    except BaseException:
        error_message = str(sys.exc_info()[0])
        status = "error"
        print(
            "remote_times.py: i: " +
            str(i) +
            " | timeout_read unknown error. sys.exc_info: " +
            error_message
        )
        # No need to use process.kill().
        # Was already terminated by itself or killed above.

    try:
        stdout = temp1.decode().strip()
    except BaseException:
        error_message = str(sys.exc_info()[0])
        print(
            "remote_times.py: i: " +
            str(i) +
            " | stdout decode unknown error. sys.exc_info: " +
            error_message
        )
        stdout = ""

    try:
        stderr = temp2.decode().strip()
    except BaseException:
        error_message = str(sys.exc_info()[0])
        print(
            "remote_times.py: i: " +
            str(i) +
            " | stderr decode unknown error. sys.exc_info: " +
            error_message
        )
        stderr = ""

    return process, status, end_unixtime, took_time, stdout, stderr


def check_remote(i, pools, remote, process, status, end_unixtime, took_time, stdout, stderr):
    message = "remote " + str(i) + ": " + str(remote)
    print(message)

    comment = get_comment(pools, remote)

    message = "* comment: " + comment
    print(message)

    half_took_time_float = float(took_time) / 2
    # Round took_time to two digits for better readability.
    # No other reason for rounding.
    half_took_time_float = round(half_took_time_float, 2)

    message = "* took_time     : " + str(took_time) + " second(s)"
    print(message)
    message = "* half_took_time: " + str(half_took_time_float) + " second(s)"
    print(message)

    unixtime_maybe = stdout

    stdout_string_length_is = len(stdout)
    unixtime_string_length_max = 10

    if stdout_string_length_is == 0:
        stdout = "empty"
        if not status == "timeout":
            status = "error"
    else:
        if not stdout_string_length_is == unixtime_string_length_max:
            status = "error"
            print("* ERROR: stdout unexpected string length: " + str(stdout_string_length_is))

    if not status == "timeout":
        if not process.returncode == 0:
            status = "error"

    stderr_length_is = len(stderr)
    stderr_string_length_max = 500

    if stderr_length_is == 0:
        stderr = "empty"

    if stderr_length_is > stderr_string_length_max:
        status = "error"
        print("* ERROR: stderr excessive string length: " + str(stderr_length_is))

    # Test:
    # status = "done"

    if status == "timeout":
        cast_success = False
    elif status == "error":
        cast_success = False
    else:
        try:
            # cast str unixtime_maybe to int remote_unixtime
            remote_unixtime = int(unixtime_maybe)
            cast_success = True
        except BaseException:
            cast_success = False
            status = "error"
            error_message = str(sys.exc_info()[0])
            status = "error"
            print("* ERROR: Could not cast to int. error_message: " + error_message)

    # Test:
    # remote_unixtime = 99999999999999999999
    # remote_unixtime = -1
    # remote_unixtime = 1
    # status = "done"

    if not status == "error" and not status == "timeout":
        # Simple test if above cast str unixtime_maybe to int remote_unixtime
        # was a success. Within 1 and 999999999. Just to make sure to not
        # continue with excessively larger numbers. A better time sanity test
        # is being done later below.
        remote_unixtime_max = 9999999999
        remote_unixtime_min = 0
        if remote_unixtime > remote_unixtime_max:
            status = "error"
            print("* ERROR: remote_unixtime(int) too large!")
        if remote_unixtime <= remote_unixtime_min:
            status = "error"
            print("* ERROR: remote_unixtime(int) smaller or equal 0!")

    if not status == "done":
        message = "* exit_code: " + str(process.returncode)
        print(message)
        if not stdout_string_length_is > unixtime_string_length_max:
            message = "* stdout: " + str(stdout)
            print(message)
        if not stderr_length_is > stderr_string_length_max:
            message = "* stderr: " + stderr
            print(message)
        message = "* remote_status: " + str(status)
        print(message)
        remote_unixtime = 0
        time_diff_raw_int = 0
        time_diff_lag_cleaned_float = 0.0
        return status, half_took_time_float, remote_unixtime, time_diff_raw_int, time_diff_lag_cleaned_float

    time_diff_raw_int = int(remote_unixtime) - int(end_unixtime)
    remote_time = time_human_readable(remote_unixtime)

    # 1. User's sdwdate sends request to remote time source.
    # 2. Server creates reply (HTTP DATE header).
    # 3. Server sends reply back to user's sdwdate.
    # Therefore assume that half of the time required to get the time
    # reply has to be deducted from the raw time diff.
    time_diff_lag_cleaned_float = float(time_diff_raw_int) - half_took_time_float
    time_diff_lag_cleaned_float = round(time_diff_lag_cleaned_float, 2)


    time_replay_protection_minium_unixtime_int, \
        time_replay_protection_minium_unixtime_human_readable = (
            time_replay_protection_file_read()
        )

    time_replay_protection_minium_unixtime_human_readable = \
        time_replay_protection_minium_unixtime_human_readable.strip()

    time_replay_protection_minium_unixtime_str = str(
        time_replay_protection_minium_unixtime_int
    )


    timesanitycheck_status_static, \
        timesanitycheck_error_static = \
        static_time_sanity_check(remote_unixtime)

    consensus_status, \
        consensus_error, \
        consensus_valid_after_str, \
        consensus_valid_until_str = \
        time_consensus_sanity_check(remote_unixtime)

    message = (
        "* replay_protection_unixtime: "
        + time_replay_protection_minium_unixtime_str
    )
    print(message)
    message = "* remote_unixtime           : " + str(remote_unixtime)
    print(message)

    message = "* consensus/valid-after           : " + \
        consensus_valid_after_str
    print(message)
    message = (
        "* replay_protection_time          : "
        + time_replay_protection_minium_unixtime_human_readable
    )
    print(message)
    message = "* remote_time                     : " + remote_time
    print(message)
    message = "* consensus/valid-until           : " + \
        consensus_valid_until_str
    print(message)

    message = "* time_diff_raw        : " + \
        str(time_diff_raw_int) + " second(s)"
    print(message)
    message = (
        "* time_diff_lag_cleaned: "
        + str(time_diff_lag_cleaned_float)
        + " second(s)"
    )
    print(message)

    # Fallback.
    remote_status = "fallback"

    if timesanitycheck_status_static == "sane":
        message = "* Time Replay Protection         : sane"
        print(message)
    elif timesanitycheck_status_static == "slow":
        message = "* Time Replay Protection         : slow"
        print(message)
        remote_status = "False"
    elif timesanitycheck_status_static == "fast":
        message = "* Time Replay Protection         : fast"
        print(message)
        remote_status = "False"
    elif timesanitycheck_status_static == "error":
        message = (
            "* Static Time Sanity Check       : error:"
            + timesanitycheck_error_static
        )
        print(message)
        remote_status = "False"

    if consensus_status == "ok":
        message = "* Tor Consensus Time Sanity Check: sane"
        print(message)
        if not remote_status == "False":
            remote_status = "True"
    elif consensus_status == "slow":
        message = "* Tor Consensus Time Sanity Check: slow"
        print(message)
        remote_status = "False"
    elif consensus_status == "fast":
        message = "* Tor Consensus Time Sanity Check: fast"
        print(message)
        remote_status = "False"
    elif consensus_status == "error":
        message = "* Tor Consensus Time Sanity Check: error: " + \
            consensus_error
        print(message)
        remote_status = "False"

    message = "* remote_status: " + remote_status
    print(message)

    if remote_status == "True":
        status = "ok"
        return status, half_took_time_float, remote_unixtime, time_diff_raw_int, time_diff_lag_cleaned_float

    remote_unixtime = 0
    time_diff_raw_int = 0
    time_diff_lag_cleaned_float = 0.00
    return status, half_took_time_float, remote_unixtime, time_diff_raw_int, time_diff_lag_cleaned_float


def get_time_from_servers(
        pools,
        list_of_remote_servers,
        proxy_ip_address,
        proxy_port_number):

    number_of_remote_servers = len(list_of_remote_servers)
    # Example number_of_remote_servers:
    # 3
    range_of_remote_servers = range(number_of_remote_servers)
    # Example range_of_remote_servers:
    # range(0, 3)

    url_to_unixtime_debug = "true"

    status = [None] * number_of_remote_servers
    status_list = [None] * number_of_remote_servers
    urls_list = [None] * number_of_remote_servers
    took_time_list = [None] * number_of_remote_servers
    half_took_time_list = [None] * number_of_remote_servers
    remote_unixtime_list = [None] * number_of_remote_servers
    handle_list = [None] * number_of_remote_servers
    future_list = [None] * number_of_remote_servers

    end_unixtime = [None] * number_of_remote_servers
    took_time = [None] * number_of_remote_servers
    stdout = [None] * number_of_remote_servers
    stderr = [None] * number_of_remote_servers

    time_diff_raw_int_list = [None] * number_of_remote_servers
    time_diff_lag_cleaned_float_list = [None] * number_of_remote_servers

    url_to_unixtime_commands_list = [None] * number_of_remote_servers

    print("remote_times.py: url_to_unixtime_command (s):")
    for i in range_of_remote_servers:
        url_to_unixtime_commands_list[i] = "url_to_unixtime" + " " + proxy_ip_address + " " + \
            proxy_port_number + " " + list_of_remote_servers[i] + " " + url_to_unixtime_debug
        print(url_to_unixtime_commands_list[i])

    print("")

    with concurrent.futures.ThreadPoolExecutor() as executor:
        for i in range_of_remote_servers:
            future_list[i] = executor.submit(
                run_command, i, url_to_unixtime_commands_list[i], list_of_remote_servers[i]
            )

    for i in range_of_remote_servers:
        handle_list[i], status[i], end_unixtime[i], took_time[i], stdout[i], stderr[i] = future_list[i].result()

    for i in range_of_remote_servers:
        status_list[i], \
        half_took_time_list[i], \
        remote_unixtime_list[i], \
        time_diff_raw_int_list[i], \
        time_diff_lag_cleaned_float_list[i] \
            = \
            check_remote(i, pools, list_of_remote_servers[i], handle_list[i], status[i], end_unixtime[i], took_time[i], stdout[i], stderr[i])

        print("")

        urls_list[i] = list_of_remote_servers[i]
        took_time_list[i] = took_time[i]

    print("remote_times.py: urls_list:")
    print(str(urls_list))
    print("remote_times.py: status_list:")
    print(str(status_list))
    print("remote_times.py: took_time_list:")
    print(str(took_time_list))
    print("remote_times.py: half_took_time_list:")
    print(str(half_took_time_list))
    print("remote_times.py: remote_unixtime_list:")
    print(str(remote_unixtime_list))
    print("remote_times.py: time_diff_raw_int_list:")
    print(str(time_diff_raw_int_list))
    print("remote_times.py: time_diff_lag_cleaned_float_list:")
    print(str(time_diff_lag_cleaned_float_list))

    return urls_list, status_list, remote_unixtime_list, took_time_list, half_took_time_list, time_diff_raw_int_list, time_diff_lag_cleaned_float_list


def remote_times_signal_handler(sig, frame):
    print("remote_times_signal_handler: OK")
    sys.exit(128 + sig)


class TimeSourcePool(object):
    def __init__(self, pool):
        self.url, self.comment = read_pools(pool, "production")
        self.url_random_pool = []
        self.already_picked_index = []
        self.done = False


def main():
    os.environ["LC_TIME"] = "C"
    os.environ["TZ"] = "UTC"
    time.tzset()

    signal.signal(signal.SIGTERM, remote_times_signal_handler)
    signal.signal(signal.SIGINT, remote_times_signal_handler)

    pools = []
    number_of_pools = 3
    pool_range = range(number_of_pools)
    for pool_i in pool_range:
        pools.append(TimeSourcePool(pool_i))

    list_of_remote_servers = sys.argv[1]
    list_of_remote_servers = list_of_remote_servers.split()
    proxy_ip_address = sys.argv[2]
    proxy_port_number = sys.argv[3]

    get_time_from_servers(
        pools,
        list_of_remote_servers,
        proxy_ip_address,
        proxy_port_number
    )


if __name__ == "__main__":
    main()

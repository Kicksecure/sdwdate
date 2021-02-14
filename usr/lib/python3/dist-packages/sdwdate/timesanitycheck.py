#!/usr/bin/python3 -u

# Copyright (C) 2017 - 2020 ENCRYPTED SUPPORT LP <adrelanos@riseup.net>
# See the file COPYING for copying conditions.

# sudo -u sdwdate
# /usr/lib/python3/dist-packages/sdwdate/timesanitycheck.py 1611640486

import sys
sys.dont_write_bytecode = True

import os
import time
# from datetime import datetime
from dateutil.parser import parse
from stem.connection import connect
import subprocess

os.environ["LC_TIME"] = "C"
os.environ["TZ"] = "UTC"
time.tzset()

def time_consensus_sanity_check(unixtime):
    error = ""
    status = "ok"
    consensus_valid_after_str = ""
    consensus_valid_until_str = ""

    try:
        controller = connect()
    except BaseException:
        status = "error"
        error = "Could not open Tor control connection. error: " + \
            str(sys.exc_info()[0])
        return status, error, consensus_valid_after_str, consensus_valid_until_str

    try:
        consensus_valid_after_str = controller.get_info(
            "consensus/valid-after")
        consensus_valid_until_str = controller.get_info(
            "consensus/valid-until")
    except BaseException:
        status = "error"
        error = "Could not request from Tor control connection. error: " + \
            str(sys.exc_info()[0])
        return status, error, consensus_valid_after_str, consensus_valid_until_str

    try:
        controller.close()
    except BaseException:
        pass

    try:
        consensus_valid_after_unixtime = parse(
            consensus_valid_after_str).strftime('%s')
        consensus_valid_until_unixtime = parse(
            consensus_valid_until_str).strftime('%s')

        if int(unixtime) > int(consensus_valid_after_unixtime):
            pass
        else:
            status = "slow"

        if int(unixtime) > int(consensus_valid_until_unixtime):
            status = "fast"
        else:
            pass
    except BaseException:
        try:
            controller.close()
        except BaseException:
            pass
        error = "Unexpected error: " + str(sys.exc_info()[0])
        status = "error"

    return status, error, consensus_valid_after_str, consensus_valid_until_str


def static_time_sanity_check(unixtime_to_validate):
    # Tue, 17 May 2033 10:00:00 GMT
    expiration_unixtime = 1999936800
    # expiration_time = datetime.strftime(
    # datetime.fromtimestamp(expiration_unixtime),
    # '%a %b %d %H:%M:%S UTC %Y')

    try:
        # time_to_validate_human_readable = datetime.strftime(
        # datetime.fromtimestamp(unixtime_to_validate), '%a %b %d %H:%M:%S UTC
        # %Y')

        p = subprocess.Popen(
            "/usr/bin/minimum-unixtime-show",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)
        stdout, stderr = p.communicate()

        minimum_unixtime = stdout.decode()
        minimum_unixtime = int(minimum_unixtime)
        # minimum_time_human_readable = stderr.decode()

        if unixtime_to_validate < minimum_unixtime:
            status = 'slow'
        elif unixtime_to_validate > expiration_unixtime:
            status = 'fast'
        else:
            status = 'sane'

        error = "none"

        return status, error
    except BaseException:
        status = "error"
        error = str(sys.exc_info()[0])
        return status, error


if __name__ == "__main__":
    unixtime = int(sys.argv[1])
    time_consensus_sanity_check(unixtime)
    status, error = static_time_sanity_check(unixtime)
    print("status: " + status)
    print("error: " + error)

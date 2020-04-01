#!/usr/bin/python3 -u

## Copyright (C) 2017 - 2020 ENCRYPTED SUPPORT LP <adrelanos@riseup.net>
## See the file COPYING for copying conditions.

import sys
import os, time
from datetime import datetime
from stem.connection import connect
from datetime import datetime
from dateutil.parser import parse


def time_consensus_sanity_check(unixtime):
   error = ""
   status = "ok"
   consensus_time_after_or_until = ""
   consensus_valid_after_str = ""
   consensus_valid_until_str = ""
   try:
      controller = connect()
   except:
      status = "error"
      error = "Could not open Tor control connection. error: " + str(sys.exc_info()[0])
      return status, error, consensus_valid_after_str, consensus_valid_until_str
   try:
      consensus_valid_after_str = controller.get_info("consensus/valid-after")
      consensus_valid_until_str = controller.get_info("consensus/valid-until")
      controller.close()

      consensus_valid_after_unixtime = parse(consensus_valid_after_str).strftime('%s')
      consensus_valid_until_unixtime = parse(consensus_valid_until_str).strftime('%s')

      if int(unixtime) > int(consensus_valid_after_unixtime):
         pass
      else:
         status = "slow"

      if int(unixtime) > int(consensus_valid_until_unixtime):
         status = "fast"
      else:
         pass
   except:
      try:
         controller.close()
      except:
         pass
      error = "Unexpected error: " + str(sys.exc_info()[0])
      status = "error"

   return status, error, consensus_valid_after_str, consensus_valid_until_str


def timesanitycheck(unixtime):
    whonix_build_file = '/usr/share/whonix/build_timestamp'
    anondist_build_file = '/var/lib/anon-dist/build_version'
    spare_file = '/usr/share/zoneinfo/UTC'

    if os.path.exists(whonix_build_file):
        build_timestamp_file = whonix_build_file
    elif os.path.exists(anondist_build_file):
        build_timestamp_file = anondist_build_file
    else:
        build_timestamp_file = spare_file

    build_time = time.strftime('%a %b %d %H:%M:%S UTC %Y', time.gmtime(os.path.getmtime(build_timestamp_file)))
    build_unixtime = time.mktime(datetime.strptime(build_time, '%a %b %d %H:%M:%S UTC %Y').timetuple())

    ## Tue, 17 May 2033 10:00:00 GMT
    expiration_unixtime = 1999936800
    expiration_time = datetime.strftime(datetime.fromtimestamp(expiration_unixtime), '%a %b %d %H:%M:%S UTC %Y')
    current_unixtime = unixtime

    try:
        current_time = datetime.strftime(datetime.fromtimestamp(unixtime), '%a %b %d %H:%M:%S UTC %Y')
    except:
        status = "error"
        time_one = ""
        time_two = expiration_time
        error = str(sys.exc_info()[0])
        return status, time_one, time_two, error

    if current_unixtime < build_unixtime:
        status = 'slow'
        time_one = current_time
        time_two = build_time
    elif current_unixtime > expiration_unixtime:
        status = 'fast'
        time_one = current_time
        time_two = expiration_time
    else:
        status = 'sane'
        time_one = current_time
        time_two = ''

    error = "none"

    return status, time_one, time_two, error

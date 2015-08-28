import os, time
from datetime import datetime

def timesanitycheck():
    whonix_build_file = '/usr/share/whonix/build_timestamp'
    anondist_build_file = '/var/lib/anon-dist/build_version'
    spare_file = '/usr/share/zoneinfo/UTC'

    if os.path.exists(whonix_build_file):
        build_timestamp_file = whonix_build_file
    elif os.path.exists(anondist_build_file):
        build_timestamp_file = anondist_build_file
    else:
        build_timestamp_file = spare_file

    current_time = datetime.strftime(datetime.now(), '%a %b %d %H:%M:%S UTC %Y')
    current_unixtime = time.mktime(datetime.strptime(current_time, '%a %b %d %H:%M:%S UTC %Y').timetuple())

    build_time = time.strftime('%a %b %d %H:%M:%S UTC %Y', time.gmtime(os.path.getmtime(build_timestamp_file)))
    build_unixtime = time.mktime(datetime.strptime(build_time, '%a %b %d %H:%M:%S UTC %Y').timetuple())

    expiration_unixtime = 1409936800
    expiration_time = datetime.strftime(datetime.fromtimestamp(expiration_unixtime), '%a %b %d %H:%M:%S UTC %Y')

    if current_unixtime < build_unixtime:
        status = 'slow'
        time_one = current_time
        time_two =  build_time
    elif current_unixtime > expiration_unixtime:
        status = 'fast'
        time_one = current_time
        time_two = expiration_time
    else:
        status = 'sane'
        time_one = current_time
        time_two = ''

    return status, time_one, time_two

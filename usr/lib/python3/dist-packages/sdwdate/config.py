#!/usr/bin/python3 -u

# Copyright (C) 2017 - 2020 ENCRYPTED SUPPORT LP <adrelanos@riseup.net>
# See the file COPYING for copying conditions.

# /usr/lib/python3/dist-packages/sdwdate/config.py 0 test
# /usr/lib/python3/dist-packages/sdwdate/config.py 1 test
# /usr/lib/python3/dist-packages/sdwdate/config.py 2 test
##
# /usr/lib/python3/dist-packages/sdwdate/config.py 0 production
# /usr/lib/python3/dist-packages/sdwdate/config.py 1 production
# /usr/lib/python3/dist-packages/sdwdate/config.py 2 production

import sys
sys.dont_write_bytecode = True

import os
import sys
import glob
import re
import random


def time_human_readable(unixtime):
    from datetime import datetime
    human_readable_unixtime = datetime.strftime(
        datetime.fromtimestamp(unixtime), "%Y-%m-%d %H:%M:%S"
    )
    return human_readable_unixtime


def time_replay_protection_file_read():
    import subprocess
    process = subprocess.Popen(
        "/usr/bin/minimum-unixtime-show",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    unixtime = int(stdout)
    time_human_readable = stderr.decode("utf-8").strip()
    # Relay check to avoid false-positives due to sdwdate inaccuracy.
    unixtime = unixtime - 100
    return unixtime, time_human_readable


def randomize_time_config():
    status = False
    if not os.path.exists("/etc/sdwdate.d/"):
        return status
    files = sorted(glob.glob("/etc/sdwdate.d/*.conf"))
    for file_item in files:
        with open(file_item) as conf:
            lines = conf.readlines()
            for line in lines:
                if line.startswith("RANDOMIZE_TIME=true"):
                    status = True
                if line.startswith("RANDOMIZE_TIME=false"):
                    status = False
    return status


def allowed_failures_config():
    failure_ratio = None
    if os.path.exists("/etc/sdwdate.d/"):
        files = sorted(glob.glob("/etc/sdwdate.d/*.conf"))
        for file_item in files:
            with open(file_item) as conf:
                lines = conf.readlines()
            for line in lines:
                if line.startswith("MAX_FAILURE_RATIO"):
                    failure_ratio = re.search(r"=(.*)", line).group(1)
    if failure_ratio is None:
        failure_ratio = 0.34
    return failure_ratio


def allowed_failures_calculate(
        failure_ratio,
        pools_total_number,
        number_of_pool_members):
    temp = float(number_of_pool_members) * float(failure_ratio)
    allowed_failures_value = temp / pools_total_number
    allowed_failures_value = int(allowed_failures_value)
    return allowed_failures_value


def get_comment(pools, remote):
    """ For logging the comments, get the index of the url
        to get it from pool.comment.
    """
    url_comment = "unknown-comment"
    for pool_item in pools:
        try:
            url_index = pool_item.url.index(remote)
            url_comment = pool_item.comment[url_index]
            break
        except BaseException:
            pass
    return url_comment


def sort_pool(pool, mode):
    # Check number of multi-line pool.
    number_of_pool_multi = 0
    for i in range(len(pool)):
        if pool[i] == ('['):
            number_of_pool_multi += 1

    # Dynamically create multi-line lists.
    multi_list_url = [[] for i in range(number_of_pool_multi)]
    multi_list_comment = [[] for i in range(number_of_pool_multi)]

    # Sort...
    multi_line = False
    multi_index = 0
    pool_single_url = []
    pool_single_comment = []

    for i in range(len(pool)):
        if multi_line and pool[i] == ']':
            multi_line = False
            multi_index = multi_index + 1

        elif multi_line and pool[i].startswith('"'):
            url = re.search(r'"(.*)#', pool[i])
            if url is not None:
                if mode == 'production':
                    multi_list_url[multi_index].append(url.group(1))
                elif mode == 'test':
                    pool_single_url.append(url.group(1))
            comment = re.search(r'#(.*)"', pool[i])
            if comment is not None:
                if mode == 'production':
                    multi_list_comment[multi_index].append(comment.group(1))
                elif mode == 'test':
                    pool_single_comment.append(comment.group(1))

        elif pool[i] == '[':
            multi_line = True

        elif pool[i].startswith('"'):
            url = re.search(r'"(.*)#', pool[i])
            if url is not None:
                pool_single_url.append(url.group(1))
            comment = re.search(r'#(.*)"', pool[i])
            if comment is not None:
                pool_single_comment.append(comment.group(1))

    # Pick a random url in each multi-line pool,
    # append it to single url pool.
    for i in range(number_of_pool_multi):
        if mode == 'production':
            single_ulr_index = random.sample(
                range(len(multi_list_url[i])), 1)[0]
            single_url = multi_list_url[i][single_ulr_index]
            single_comment = multi_list_comment[i][single_ulr_index]
            pool_single_url.append(single_url)
            pool_single_comment.append(single_comment)

    return(pool_single_url, pool_single_comment)


def read_pools(pool, mode):
    SDWDATE_POOL_ZERO = False
    SDWDATE_POOL_ONE = False
    SDWDATE_POOL_TWO = False

    pool_one = []
    pool_two = []
    pool_three = []

    pool_one_url = []
    pool_two_url = []
    pool_three_url = []

    if os.path.exists('/etc/sdwdate.d/'):
        files = sorted(glob.glob('/etc/sdwdate.d/*.conf'))

        if files:
            conf_found = False
            for conf in files:
                conf_found = True
                with open(conf) as c:
                    for line in c:
                        line = line.strip()
                        if line.startswith('SDWDATE_POOL_ZERO'):
                            SDWDATE_POOL_ZERO = True

                        elif line.startswith('SDWDATE_POOL_ONE'):
                            SDWDATE_POOL_ZERO = False
                            SDWDATE_POOL_ONE = True

                        elif line.startswith('SDWDATE_POOL_TWO'):
                            SDWDATE_POOL_ZERO = False
                            SDWDATE_POOL_ONE = False
                            SDWDATE_POOL_TWO = True

                        elif SDWDATE_POOL_ZERO and not line.startswith('##'):
                            pool_one.append(line)

                        elif SDWDATE_POOL_ONE and not line.startswith('##'):
                            pool_two.append(line)

                        elif SDWDATE_POOL_TWO and not line.startswith('##'):
                            pool_three.append(line)

            if not conf_found:
                print(
                    'No valid file found in user configuration folder "/etc/sdwdate.d".')

        else:
            print('No file found in user configuration folder "/etc/sdwdate.d".')

    else:
        print('User configuration folder "/etc/sdwdate.d" does not exist.')

    pool_one_url, pool_one_comment = sort_pool(pool_one, mode)
    pool_two_url, pool_two_comment = sort_pool(pool_two, mode)
    pool_three_url, pool_three_comment = sort_pool(pool_three, mode)

    pool_url = [pool_one_url, pool_two_url, pool_three_url]
    pool_comment = [pool_one_comment, pool_two_comment, pool_three_comment]

    return(pool_url[pool],
           pool_comment[pool])


if __name__ == "__main__":
    pool = int(sys.argv[1])
    mode = sys.argv[2]
    pool_url, pool_comment = read_pools(pool, mode)
    print("pool: " + str(pool))
    print("pool_url: " + str(pool_url))
    print("pool_comment: " + str(pool_comment))

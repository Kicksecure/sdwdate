#!/usr/bin/env python

import os
import glob
import re
import random

def sort_pool(pool):
    ## Check number of multi-line pool.
    double_quotes = 0
    for i in range(len(pool)):
        if pool[i] == ('"'):
            double_quotes = double_quotes + 1
    number_of_pool_multi =  double_quotes / 2

    ## Dynamically create multi-line lists.
    multi_list = [[] for i in range(number_of_pool_multi)]

    ## Sort...
    multi_line = False
    multi_index = 0
    pool_single = []
    for i in range(len(pool)):
        if multi_line and pool[i] == '"':
            multi_line = False
            multi_index = multi_index + 1
        elif multi_line:
            url = re.search(r'"(.*)#', pool[i])
            multi_list[multi_index].append(url.group(1))
        elif pool[i] == '"':
            multi_line = True
        elif pool[i].startswith('"'):
            url = re.search(r'"(.*)#', pool[i])
            pool_single.append(url.group(1))

    ## Pick a random url in each multi-line pool,
    ## append it to single url pool.
    for i in range(number_of_pool_multi):
        single_url = multi_list[i][random.sample(range(len(multi_list[i])), 1)[0]]
        pool_single.append(single_url)

    return(pool_single)

def read_pools():
    SDWDATE_POOL_ONE = False
    SDWDATE_POOL_TWO = False
    SDWDATE_POOL_THREE = False

    pool_one = []
    pool_two = []
    pool_three = []

    pool_one_sorted = []
    pool_two_sorted = []
    pool_three_sorted = []

    if os.path.exists('/etc/sdwdate-python.d/'):
        files = sorted(glob.glob('/etc/sdwdate-python.d/*'))

        if files:
            conf_found = False
            for conf in files:
                if not conf.endswith('~') and conf.count('.dpkg-') == 0:
                    conf_found = True
                    with open(conf) as c:
                        for line in c:
                            line = line.strip()
                            if line.startswith('SDWDATE_POOL_ONE'):
                                SDWDATE_POOL_ONE = True

                            elif line.startswith('SDWDATE_POOL_TWO'):
                                SDWDATE_POOL_ONE = False
                                SDWDATE_POOL_TWO = True

                            elif line.startswith('SDWDATE_POOL_THREE'):
                                SDWDATE_POOL_ONE = False
                                SDWDATE_POOL_TWO = False
                                SDWDATE_POOL_THREE = True

                            elif SDWDATE_POOL_ONE and not line.startswith('##'):
                                pool_one.append(line)

                            elif SDWDATE_POOL_TWO and not line.startswith('##'):
                                pool_two.append(line)

                            elif SDWDATE_POOL_THREE and not line.startswith('##'):
                                pool_three.append(line)

            if not conf_found:
                print('No valid file found in user configuration folder "/etc/sdwdate.d".')

        else:
            print('No file found in user configuration folder "/etc/sdwdate.d".')

    else:
        print('User configuration folder "/etc/sdwdate.d" does not exist.')

    pool_one_sorted = sort_pool(pool_one)
    pool_two_sorted = sort_pool(pool_two)
    pool_three_sorted = sort_pool(pool_three)

    print pool_one_sorted
    print pool_two_sorted
    print pool_three_sorted

    return(pool_one_sorted,  pool_two_sorted, pool_three_sorted)

if __name__ == "__main__":
    read_pools()

#!/usr/bin/env python

import os
import glob
import time
import re

def read_pools():
    SDWDATE_POOL_ONE = False
    SDWDATE_POOL_TWO = False
    SDWDATE_POOL_THREE = False

    multi_line = False
    pool_one = []
    pool_two = []
    pool_three = []

    pool_one_single = []
    pool_one_multi = []

    pool_two_single = []
    pool_two_multi = []

    pool_three_single = []
    pool_three_multi = []

    if os.path.exists('/etc/sdwdate.d/'):
        files = sorted(glob.glob('/etc/sdwdate.d/*'))

        if files:
            conf_found = False
            for conf in files:
                if not conf.endswith('~') and conf.count('.dpkg-') == 0:
                    conf_found = True
                    with open(conf) as c:
                        for line in c:
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
                                pool_one.append(line.strip())

                            elif SDWDATE_POOL_TWO and not line.startswith('##'):
                                pool_two.append(line.strip())

                            elif SDWDATE_POOL_THREE and not line.startswith('##'):
                                pool_three.append(line.strip())

            if not conf_found:
                self.set_default()
                print('No valid file found in user configuration folder "/etc/sdwdate.d".'\
                        ' Running with default configuration.')

        else:
            print('No file found in user configuration folder "/etc/cpfpy.d".'\
                    ' Running with default configuration.')

    else:
        print('User configuration folder "/etc/cpfpy.d" does not exist.'\
                ' Running with default configuration.')

    for i in range(len(pool_one)):
        if multi_line and pool_one[i] == '"':
            multi_line = False
        elif multi_line:
            url = pool_one[i][0:22]
            pool_one_multi.append(url)
        elif pool_one[i] == '"':
            multi_line = True
        elif pool_one[i].startswith('"'):
            #url = re.search(r'"(.*)#', pool_one[i])
            #pool_one_single.append(url.group(1))
            url = pool_one[i][1:23]
            pool_one_single.append(url)

    print 'pool_one_multi'
    for i in xrange(len(pool_one_multi)):
        print pool_one_multi[i]
    print 'pool 1 singles'
    for i in range(len(pool_one_single)):
        print pool_one_single[i]

    for i in range(len(pool_two)):
        if multi_line and pool_two[i] == '"':
            multi_line = False
        elif multi_line:
            url = pool_two[i][0:22]
            pool_two_multi.append(url)
        elif pool_two[i] == '"':
            multi_line = True
        elif pool_two[i].startswith('"'):
            #url = re.search(r'"(.*)#', pool_two[i])
            #pool_two_single.append(url.group(1))
            url = pool_two[i][1:23]
            pool_two_single.append(url)

    print 'pool_two_multi'
    for i in xrange(len(pool_two_multi)):
        print pool_two_multi[i]
    print 'pool 2 singles'
    for i in range(len(pool_two_single)):
        print pool_two_single[i]

    for i in range(len(pool_three)):
        if multi_line and pool_three[i] == '"':
            multi_line = False
        elif multi_line:
            url = pool_three[i][0:22]
            pool_three_multi.append(url)
        elif pool_three[i] == '"':
            multi_line = True
        elif pool_three[i].startswith('"'):
            #url = re.search(r'"(.*)#', pool_three[i])
            #pool_three_single.append(url.group(1))
            url = pool_three[i][1:23]
            pool_three_single.append(url)

    print 'pool_three_multi'
    for i in xrange(len(pool_three_multi)):
        print pool_three_multi[i]
    print 'pool_three_single'
    for i in range(len(pool_three_single)):
        print pool_three_single[i]

    return (pool_one_single, pool_two_single, pool_three_single,
            pool_one_multi, pool_two_multi, pool_three_multi)

if __name__ == "__main__":
    read_pools()

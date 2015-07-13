#!/usr/bin/env python

import os, sys
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

    if os.path.exists('/etc/sdwdate.d/'):
        files = sorted(glob.glob('/etc/sdwdate.d/*'))

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

                            elif SDWDATE_POOL_ONE and line.startswith('"'):
                                url = re.search(r'"(.*)#', line)
                                print '%s' % (url.group(1))
                                pool_one.append(url.group(1))

                            elif SDWDATE_POOL_TWO and line.startswith('"'):
                                url = re.search(r'"(.*)#', line)
                                print '%s' % (url.group(1))
                                pool_two.append(url.group(1))

                            elif SDWDATE_POOL_THREE and line.startswith('"'):
                                url = re.search(r'"(.*)#', line)
                                print '%s' % (url.group(1))
                                pool_three.append(url.group(1))

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

    return (pool_one, pool_two, pool_three)

if __name__ == "__main__":
    read_pools()

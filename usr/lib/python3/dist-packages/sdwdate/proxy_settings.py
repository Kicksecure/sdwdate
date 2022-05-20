#!/usr/bin/python3 -u

# Copyright (C) 2017 - 2022 ENCRYPTED SUPPORT LP <adrelanos@whonix.org>
# See the file COPYING for copying conditions.

import sys
sys.dont_write_bytecode = True

import os
import glob
import re
from subprocess import check_output


def proxy_settings():
    ip_address = '127.0.0.1'
    port_number = '9050'
    settings_path = '/usr/libexec/helper-scripts/settings_echo'

    if (os.path.exists('/usr/share/whonix') and
            os.access(settings_path, os.X_OK)):
        proxy_settings = check_output(settings_path)
        ip_address = re.search(
            b'GATEWAY_IP="(.*)"',
            proxy_settings).group(1).decode()

    if os.path.exists('/usr/share/whonix'):
        port_number = '9108'

    if os.path.exists('/etc/sdwdate.d/'):
        files = sorted(glob.glob('/etc/sdwdate.d/*.conf'))
        for f in files:
            with open(f) as conf:
                lines = conf.readlines()
            for line in lines:
                if line.startswith('PROXY_IP'):
                    ip_address = re.search(r'=(.*)', line).group(1)
                if line.startswith('PROXY_PORT'):
                    port_number = re.search(r'=(.*)', line).group(1)

    return ip_address, port_number


if __name__ == "__main__":
    ip_address, port_number = proxy_settings()
    print(ip_address + " " + port_number)

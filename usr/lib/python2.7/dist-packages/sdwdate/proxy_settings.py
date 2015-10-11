import os
import glob
import re


def proxy_settings():
    ip_address = ''
    port_number = ''

    if os.path.exists('/etc/sdwdate.d/'):
        files = sorted(glob.glob('/etc/sdwdate.d/*'))
        for f in files:
            with open(f) as conf:
                lines = conf.readlines()
            for line in lines:
                if line.startswith('PROXY_IP'):
                    ip_address = re.search(r'=(.*)', line).group(1)
                if line.startswith('PROXY_PORT'):
                    port_number = re.search(r'=(.*)', line).group(1)

    if ip_address == '':
        if os.path.exists('/usr/share/anon-gw-base-files/gateway'):
            ip_address = '127.0.0.1'
        elif os.path.exists('/usr/lib/qubes-whonix'):
            ip_address = check_output(['qubesdb-read', '/qubes-gateway'])
        else:
            ip_address = '10.152.152.10'

    if port_number == '':
        port_number = '9108'

    print 'ip %s port %s' % (ip_address, port_number)
    return ip_address, port_number

if __name__ == "__main__":
    proxy_settings()



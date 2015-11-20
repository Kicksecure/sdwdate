import os
import glob
import re
from subprocess import check_output

def proxy_settings():
    ip_address = ''
    port_number = ''
    settings_path = '/usr/lib/anon-shared-helper-scripts/settings_echo'

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

    if (os.path.exists('/usr/share/whonix') and
        os.access(settings_path, os.X_OK)):
            proxy_settings = check_output(settings_path)
            ip_address = re.search(r'TOR_CONTROL_HOST="(.*)"', proxy_settings).group(1)
    elif ip_address != '':
        ## ip_address = PROXY_IP
        pass
    else:
        ip_address = '127.0.0.1'

    if os.path.exists('/usr/share/whonix'):
        port_number = '9108'
    elif port_number != '':
        ## port_number = PROXY_PORT
        pass
    else:
        port_number = '9050'

    #print 'ip %s port %s' % (ip_address, port_number)
    return ip_address, port_number

if __name__ == "__main__":
    proxy_settings()



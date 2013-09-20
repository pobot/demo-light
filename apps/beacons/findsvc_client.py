#!/usr/bin/env python
# -*- coding: utf-8 -*-

import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
s.settimeout(1)

s.sendto('beacons', ('<broadcast>', 5555))
try:
    buf, addr = s.recvfrom(5555)
except socket.timeout:
    print('[E] no reply')
else:
    hostname = buf.strip()
    print('server %s found at IP=%s' % (hostname, addr[0]))
    s.close()

from ClockSettings import ClockSettings
from Clock import Clock

import network
import time
from machine import RTC
import network
import socket
import struct

from umqtt.simple import MQTTClient

class ClockManager:

    def boot(self):
        self._clock = Clock()
        time.sleep(1)

        try:
            print("Attempting connect 2")
            self._clock.show_waiting()
            self._connect_wifi(ClockSettings.wifi_name, ClockSettings.wifi_psk)
            self._set_time()
        except:
            self._clock.show_boot_error()

    def _connect_wifi(self, name, psk):
        print("Connecting.....")
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

        wlan.connect(name, psk)

        max_wait = 10
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1

            time.sleep(1)

        #Handle connection error
        if wlan.status() != 3:
            raise RuntimeError('wifi connection failed')
        else:
            print('connected')

        status = wlan.ifconfig()
        print('ip = ' + status[0])

    def _set_time(self):
        NTP_DELTA = 2208988800
        host = "pool.ntp.org"

        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        addr = socket.getaddrinfo(host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            s.settimeout(1)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        finally:
            s.close()

        val = struct.unpack("!I", msg[40:44])[0]
        t = val - NTP_DELTA    
        tm = time.gmtime(t)

        RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))







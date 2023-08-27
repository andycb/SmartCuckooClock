from ClockSettings import ClockSettings
from Clock import Clock
from MqttManager import MqttManager

import network
import time
from machine import RTC, Timer
import socket
import struct

class ClockManager:
    _helth_check_busy: bool = False
    _trying_reconnection: bool = False

    def __init__(self) -> None:
        self._wlan = network.WLAN(network.STA_IF)

    def boot(self):
        self._clock = Clock()
        self._clock.reset()

        self._mqtt_manager = MqttManager(ClockSettings.mqtt_address, ClockSettings.mqtt_username, ClockSettings.mqtt_password, self._clock)

        while True:
            try:
                print("Attempting connect to wifi")
                self._clock.show_waiting()
                self._connect_wifi(ClockSettings.wifi_name, ClockSettings.wifi_psk)

                print("Setting RTC")
                #self._set_time()

                print("Connecting MQTT")
                self._mqtt_manager.connect()
                self._mqtt_manager.publish_autoconf()

                self._clock.clear_ring_pattern()
                break
            except:
                print("Failed")
                self._clock.show_boot_error()
                time.sleep(10)

        # Check the clock's connection state, and reset if it disconnects
        self._health_check_timer = Timer(mode=Timer.PERIODIC, period=1000, callback=self._health_check)

    def _health_check(self, t):
        if self._helth_check_busy:
            print("Helth check is busy, Skipping.")
            return
        
        try:
            if self._wlan.status() != 3:
                print ("Wifi connection lost. Attempting reconnect...")
                try:
                    if not self._trying_reconnection:
                        self._clock.show_waiting()
                        self._trying_reconnection = True

                    try:
                        self._mqtt_manager.stop()
                    except Exception as e:
                        print(f"Filed to stop MQTT client {e}")

                    self._wlan = network.WLAN(network.STA_IF)
                    self._connect_wifi(ClockSettings.wifi_name, ClockSettings.wifi_psk)

                    print(f"Wifi connection restored")
                    time.sleep(6)
                    self._trying_reconnection = False
                    
                except Exception as e:
                    print (f"Failed to re-connect to wifi {e}")
                    return

            if self._mqtt_manager.is_connected is False:
                print ("MQTT connection lost. Attempting reconnect...")

                if not self._trying_reconnection:
                        self._clock.show_waiting()
                        self._trying_reconnection = True

                try:
                    self._mqtt_manager.connect()
                    self._mqtt_manager.publish_autoconf()

                    self._clock.clear_ring_pattern()
                    self._trying_reconnection = False
                    print(f"MQTT connection restored")
                except Exception as e:
                    print (f"Failed to re-connect to MQTT {e}")
        finally:
            self._helth_check_busy = False
                
    def _connect_wifi(self, name, psk):
        self._wlan.active(True)
        self._wlan.connect(name, psk)

        max_wait = 10
        while max_wait > 0:
            if self._wlan.status() < 0 or self._wlan.status() >= 3:
                break
            max_wait -= 1

            time.sleep(1)

        if self._wlan.status() != 3:
            raise RuntimeError('wifi connection failed')
        else:
            print('Wifi Connected')

        status = self._wlan.ifconfig()
        print('IP = ' + status[0])

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







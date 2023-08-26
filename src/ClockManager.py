from ClockSettings import ClockSettings
from Clock import Clock
import RingPatterns

import network
import time
from machine import RTC, Timer
import socket
import struct
import json

from umqtt.simple import MQTTClient

class ClockManager:

    def __init__(self) -> None:
        self._last_dial_state = None
        self._last_pendulum_light_state = None
        self._last_pendulum_swing_state = None
        self._last_chime_state = None
        self._last_timer_state = None
        self._last_light_sensor_state = None
        self._wlan = network.WLAN(network.STA_IF)

    def boot(self):
        self._clock = Clock()
        self._clock.reset()

        while True:
            try:
                print("Attempting connect to wifi")
                self._clock.show_waiting()
                self._connect_wifi(ClockSettings.wifi_name, ClockSettings.wifi_psk)

                print("Setting RTC")
                self._set_time()
                self._clock.clear_ring_pattern()
                break
            except:
                print("Failed")
                self._clock.show_boot_error()
                time.sleep(10)

        print("Conecting to MQTT broker")
        self._mqtt_client = MQTTClient(client_id=b"andycb_cuckoo_clock",
            server=ClockSettings.mqtt_address,
            user=ClockSettings.mqtt_username,
            password=ClockSettings.mqtt_password,
            keepalive=7200,
            ssl=False)
        
        self._mqtt_client.connect()
        self._mqtt_client.set_callback(self._handle_new_message)

        self._messageTimer = Timer(mode=Timer.PERIODIC, period=500, callback=self._check_messages)
        self._updateStateTimer = Timer(mode=Timer.PERIODIC, period=2000, callback=self._update_state)
        self._health_check_timer = Timer(mode=Timer.PERIODIC, period=1000, callback=self._health_check)

        print("Setting auto-conf")
        self._publish_autoconf()

    def _health_check(self, t):
        print (f"Health check. Wifi = {self._wlan.status()}")
        if self._wlan.status() != 3:
            print ("Wifi connection lost. Attempting reconnect...")
            try:
                self._clock.show_waiting()
                self._connect_wifi(ClockSettings.wifi_name, ClockSettings.wifi_psk)
                self._mqtt_client.connect()
                self._publish_autoconf()
                self._clock.clear_ring_pattern()
            except:
                print ("Failed to re-connect to wifi")
                return

        try:
            self._mqtt_client.ping()
        except:
            print("MQTT connection lost. Attempting reconnect")
            try:
                self._clock.show_boot_error()
                self._mqtt_client.connect()
                self._publish_autoconf()
                self._clock.clear_ring_pattern()
            except:
                print ("Failed to re-connect to MQTT")
                return   
            


    def _update_state(self, t):
        state = self._clock.get_state()
        #print(f"State Updaye = {json.dumps(state)}")

        pendulum_light_state = state["pendulum_light"]
        if pendulum_light_state != self._last_pendulum_light_state:
            self._last_pendulum_light_state = pendulum_light_state
            print("Updating pendulum light")
            self._mqtt_client.publish(f'{self.pendulum_light_topic_prefix}/state', pendulum_light_state)

        pendulum_swing_state = state["pendulum_swing"]
        if pendulum_swing_state != self._last_pendulum_swing_state:
            self._last_pendulum_swing_state = pendulum_swing_state
            print("Updating pendulum swing")
            self._mqtt_client.publish(f'{self.pendulum_swing_topic_prefix}/state', pendulum_swing_state)

        dial_state = state["dial"]
        if dial_state != self._last_dial_state:
            self._last_dial_state = dial_state
            print(f"Updating dial {dial_state}")
            self._mqtt_client.publish(f'{self.dial_topic_prefix}/state', dial_state)

        light_level_state = json.dumps(state["light_level"])
        if light_level_state != self._last_light_sensor_state:
            self._last_light_sensor_state = light_level_state
            #self._mqtt_client.publish(f'{self.light_sensor_topic_prefix}/state', light_level_state)

        chime_state = state["chime"]
        if chime_state != self._last_chime_state:
            self._last_chime_state = chime_state
            print("Updating chime")
            self._mqtt_client.publish(f'{self.chime_topic_prefix}/state', chime_state)



    def _check_messages(self, t):
        self._mqtt_client.check_msg()

    def _handle_new_message(self, topic, message):
        topic = bytes.decode(topic)
        message = bytes.decode(message)

        print(f"Topic '{topic}' recived message: {message}")

        if topic.startswith(self.pendulum_light_topic_prefix):
            state = json.loads(message)
            if state["state"] == "OFF":
                self._clock.set_pendulum_light(0,0,0,False, 0)
            else:
                breate  = False
                if "effect" in state:
                    if state["effect"] == "breathe":
                        breate = True
                if "color" in state:
                    self._clock.set_pendulum_light(state["color"]["r"], state["color"]["g"], state["color"]["b"], breate, 0)
                else:
                    self._clock.set_pendulum_light(150, 150, 150, breate, 0)
            
            return
                    
        if topic.startswith(self.pendulum_swing_topic_prefix):
            if message == "OFF":
                self._clock.swing_pendulum(False, 0)
            else:
                self._clock.swing_pendulum(True, 0)

            return

        if topic.startswith(self.timer_topic_prefix):
            self._clock.set_timer(int(message))
            return
    
        if topic.startswith(self.chime_topic_prefix):
            if message == "ON":
                self._clock.chime()
            return
        
        if topic.startswith(self.dial_topic_prefix):
            state = json.loads(message)
            if state["state"] == "OFF":
                self._clock.set_dial_light(0,0,0,False)
            else:
                pattern = None
                if "effect" in state:
                    s = state["effect"]
                    if s == "ErrorPattern":
                        pattern = RingPatterns.ErrorPattern()
                    if s == "AlertPattern":
                        pattern = RingPatterns.AlertPattern()
                    if s == "CurrentTimePattern":
                        pattern = RingPatterns.CurrentTimePattern()

                if "color" in state:
                    self._clock.set_dial_light(state["color"]["r"], state["color"]["g"], state["color"]["b"], pattern)
                else:
                    self._clock.set_dial_light(150, 150, 150, pattern)
            
            return
        


    def _publish_autoconf(self):
        device = {}
        device["identifiers"] = [ "cuckoo_clock" ]
        device["name"] = "Cuckoo Clock"
        device["manufacturer"] = "andycb"
        device["model"] = "Cuckoo Clock"
        device["sw_version"] = "2023.08.26"

        self.pendulum_swing_id = "cuckoo_clock_pendulum_swing"
        self.pendulum_swing_topic_prefix = f"homeassistant/switch/{self.pendulum_swing_id}"

        self.pendulum_light_id = "cuckoo_clock_pendulum_light"
        self.pendulum_light_topic_prefix = f"homeassistant/light/{self.pendulum_light_id}"

        self.dial_id = "cuckoo_clock_dial"
        self.dial_topic_prefix = f"homeassistant/light/{self.dial_id}"

        self.chime_id = "cuckoo_clock_chime"
        self.chime_topic_prefix = f"homeassistant/switch/{self.chime_id}"

        self.timer_id = "cuckoo_clock_timer"
        self.timer_topic_prefix = f"homeassistant/number/{self.timer_id}"

        self.light_sensor_id = "cuckoo_clock_brightness"
        self.light_sensor_topic_prefix = f"homeassistant/sensor/{self.light_sensor_id}"

        # Pendulum swing
        pendulum_swing_payload = {}
        pendulum_swing_payload['name'] = 'Pendulum Swing'
        pendulum_swing_payload['command_topic'] = f'{self.pendulum_swing_topic_prefix}/set'
        pendulum_swing_payload['state_topic'] = f'{self.pendulum_swing_topic_prefix}/state'
        pendulum_swing_payload['unique_id'] = self.pendulum_swing_id
        pendulum_swing_payload["device"] = device
        pendulum_swing_topic = f"{self.pendulum_swing_topic_prefix}/config"
        self._mqtt_client.publish(pendulum_swing_topic, json.dumps(pendulum_swing_payload))
        self._mqtt_client.subscribe(f'{self.pendulum_swing_topic_prefix}/set')

        # Chime
        chime_payload = {}
        chime_payload['name'] = 'Chime'
        chime_payload['command_topic'] = f'{self.chime_topic_prefix}/set'
        chime_payload['state_topic'] = 'f{chime_topic_prefix}/state'
        chime_payload['unique_id'] = self.chime_id
        chime_payload["device"] = device
        chime_topic = f"{self.chime_topic_prefix}/config"
        self._mqtt_client.publish(chime_topic, json.dumps(chime_payload))
        self._mqtt_client.subscribe(f"{self.chime_topic_prefix}/set")

        # Timer
        timer_payload = {}
        timer_payload['name'] = 'Timer'
        timer_payload['command_topic'] = f'{self.timer_topic_prefix}/set'
        timer_payload['state_topic'] = f'{self.timer_topic_prefix}/state'
        timer_payload['unique_id'] = self.timer_id
        timer_payload['unit_of_measurement'] = 'Seconds'
        timer_payload["device"] = device
        timer_topic = f"{self.timer_topic_prefix}/config"
        self._mqtt_client.publish(timer_topic, json.dumps(timer_payload))
        self._mqtt_client.subscribe(f"{self.timer_topic_prefix}/set")

        # Pendulum Light
        pendulum_light_payload = {}
        pendulum_light_payload['name'] = 'Pendulum Light'
        pendulum_light_payload['command_topic'] = f'{self.pendulum_light_topic_prefix}/set'
        pendulum_light_payload['state_topic'] = f'{self.pendulum_light_topic_prefix}/state'
        pendulum_light_payload['unique_id'] = self.pendulum_light_topic_prefix
        pendulum_light_payload['effect'] = 'true'
        pendulum_light_payload['supported_color_modes'] = 'rgb'
        pendulum_light_payload['effect_list'] = 'breathe'
        pendulum_light_payload['schema'] = 'json'
        pendulum_light_payload['color_mode'] = 'true'
        pendulum_light_payload["device"] = device
        pendulum_loght_topic = f"{self.pendulum_light_topic_prefix}/config"
        self._mqtt_client.publish(pendulum_loght_topic, json.dumps(pendulum_light_payload))        
        self._mqtt_client.subscribe(f"{self.pendulum_light_topic_prefix}/set")

        # Dial
        dial_light_payload = {}
        dial_light_payload['name'] = 'Dial Colour'
        dial_light_payload['command_topic'] = f'{self.dial_topic_prefix}/set'
        dial_light_payload['state_topic'] = f'{self.dial_topic_prefix}/state'
        dial_light_payload['unique_id'] = self.dial_id
        dial_light_payload['effect'] = 'true'
        dial_light_payload['supported_color_modes'] = 'rgb'
        dial_light_payload['effect_list'] = ['AlertPattern', 'ErrorPattern', 'CurrentTimePattern']
        dial_light_payload['schema'] = 'json'
        dial_light_payload['color_mode'] = 'true'
        dial_light_payload["device"] = device
        dial_light_topic = f"{self.dial_topic_prefix}/config"
        self._mqtt_client.publish(dial_light_topic, json.dumps(dial_light_payload))        
        self._mqtt_client.subscribe(f"{self.dial_topic_prefix}/set")

        # Light Sensor
        light_sensor_payload = {}
        light_sensor_payload['name'] = 'Light Level'
        light_sensor_payload['command_topic'] = f'{self.light_sensor_topic_prefix}/set'
        light_sensor_payload['state_topic'] = f'{self.light_sensor_topic_prefix}/state'
        light_sensor_payload['unique_id'] = self.light_sensor_id
        light_sensor_payload["device"] = device
        light_sensor_topic = f"{self.light_sensor_topic_prefix}/config"
        self._mqtt_client.publish(light_sensor_topic, json.dumps(light_sensor_payload))        

    def _connect_wifi(self, name, psk):
        print("Connecting.....")

        self._wlan.active(True)
        self._wlan.connect(name, psk)

        max_wait = 10
        while max_wait > 0:
            if self._wlan.status() < 0 or self._wlan.status() >= 3:
                break
            max_wait -= 1

            time.sleep(1)

        #Handle connection error
        if self._wlan.status() != 3:
            raise RuntimeError('wifi connection failed')
        else:
            print('connected')

        status = self._wlan.ifconfig()
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







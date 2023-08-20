from ClockSettings import ClockSettings
from Clock import Clock

import network
import time
from machine import RTC, Timer
import socket
import struct
import json

from umqtt.simple import MQTTClient

class ClockManager:

    def boot(self):
        self._clock = Clock()
        self._clock.reset()

        while True:
            try:
                print("Attempting connect to wifi")
                #self._clock.show_waiting()
                self._connect_wifi(ClockSettings.wifi_name, ClockSettings.wifi_psk)

                print("Setting RTC")
                #self._set_time()
                #self._clock.clear_ring_pattern()ß
                break
            except:
                print("Failed")
                #self._clock.show_boot_error()
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

        print("Setting auto-conf")
        self._publish_autoconf()

    def _check_messages(self, t):
        self._mqtt_client.check_msg()

    def _handle_new_message(self, topic, message):
        topic = bytes.decode(topic)
        message = bytes.decode(message)

        print(f"Topic '{topic}' recived message: {message}")
        if topic == "homeassistant/light/cuckoo_clock_pendulum_light/set":
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
                    

            self._mqtt_client.publish("homeassistant/light/cuckoo_clock_pendulum_light/state", message)

        if topic == "homeassistant/switch/cuckoo_clock_pendulum_swing/set":
            if message == "OFF":
                self._clock.swing_pendulum(False, 0)
            else:
                self._clock.swing_pendulum(True, 0)

            self._mqtt_client.publish("homeassistant/switch/cuckoo_clock_pendulum_swing/state", message)

        if topic == "homeassistant/number/cuckoo_clock_timer/set":
            self._clock.set_timer(int(message))

        pass

    def _publish_autoconf(self):
        device = {}
        device["identifiers"] = [ "cuckoo_clock" ]
        device["name"] = "Cuckoo Clock"
        device["manufacturer"] = "andycb"
        device["model"] = "Cuckoo Clock"
        device["sw_version"] = "2023.08.20"

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
        self.light_sensor_topic_prefix = "homeassistant/sensor/{self.light_sensor_id}"

        # Pendulum swing
        pendulum_swing_payload = {}
        pendulum_swing_payload['name'] = 'Pendulum Swing'
        pendulum_swing_payload['command_topic'] = f'{self.pendulum_swing_topic_prefix}/set'
        pendulum_swing_payload['state_topic'] = f'{self.pendulum_swing_topic_prefix}/state'
        pendulum_swing_payload['unique_id'] = {self.pendulum_swing_id}
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
        dial_light_payload['command_topic'] = f'{self.dial_id}/set'
        dial_light_payload['state_topic'] = f'{self.dial_id}/state'
        dial_light_payload['unique_id'] = self.dial_id
        dial_light_payload['effect'] = 'true'
        dial_light_payload['supported_color_modes'] = 'rgb'
        dial_light_payload['effect_list'] = ['spin', 'rainbow', 'error']
        dial_light_payload['schema'] = 'json'
        dial_light_payload['color_mode'] = 'true'
        dial_light_payload["device"] = device
        dial_light_topic = f"{self.dial_topic_prefix}/config"
        self._mqtt_client.publish(dial_light_topic, json.dumps(pendulum_light_payload))        
        self._mqtt_client.subscribe(f"{self.dial_topic_prefix}/set")

        # Light Sensor
        light_sensor_payload = {}
        light_sensor_payload['name'] = 'Light Level'
        light_sensor_payload['command_topic'] = f'{self.light_sensor_topic_prefix}/set'
        light_sensor_payload['value_topic'] = f'{self.light_sensor_topic_prefix}/value'
        light_sensor_payload['unique_id'] = self.light_sensor_id
        light_sensor_payload["device"] = device
        light_sensor_topic = f"{self.light_sensor_topic_prefix}/config"
        self._mqtt_client.publish(light_sensor_topic, json.dumps(light_sensor_payload))        

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







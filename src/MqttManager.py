from umqtt.simple import MQTTClient
from Clock import Clock
from machine import Timer
import json
import RingPatterns

class MqttManager: 
    _last_dial_state: str = ""
    _last_pendulum_light_state: str = ""
    _last_pendulum_swing_state: str = ""
    _last_chime_state: str = ""
    _last_timer_state: str = ""
    _last_light_sensor_state: str = ""
    _mqtt_client: MQTTClient = None
    is_connected: bool = False

    def __init__(self, address: str, username: str, password: str, clock: Clock) -> None:
        self._address = address
        self._username = username
        self._password = password
        self._clock = clock

    def _check_messages(self, t: Timer) -> None:
        print("MQTT MEssage check..")
        try:
            # Poll the MQTT to process messages sent to us
            self._mqtt_client.check_msg()
        except:
            print("MQTT connection lost")
            self.stop()
        
    def connect(self) -> None:
        self._mqtt_client = MQTTClient(
            client_id=b"andycb_cuckoo_clock",
            server=self._address,
            user=self._username,
            password=self._password,
            keepalive=7200,
            ssl=False)
        
        self._mqtt_client.set_callback(self._handle_new_message)
        self._mqtt_client.connect()

        self.is_connected = True

        # Timer to check for new message send to the clock
        self._messageTimer = Timer(mode=Timer.PERIODIC, period=500, callback=self._check_messages)

        # Timer to publish the state of the clock
        self._updateStateTimer = Timer(mode=Timer.PERIODIC, period=2000, callback=self._update_state)

    def stop(self) -> None:
        try:
            if self._mqtt_client is not None and self._mqtt_client.sock is not None:
                self._mqtt_client.sock.close()
        except Exception as e:
            print(f"Failed to close socket {e}")

        self._mqtt_client = None
        self.is_connected = False

        if self._messageTimer != None:
            self._messageTimer.deinit()
            self._messageTimer = None

        if self._updateStateTimer != None:
            self._updateStateTimer.deinit()
            self._updateStateTimer = None

    def publish_autoconf(self) -> None:
        device = {}
        device["identifiers"] = [ "cuckoo_clock" ]
        device["name"] = "Cuckoo Clock"
        device["manufacturer"] = "andycb"
        device["model"] = "Cuckoo Clock"
        device["sw_version"] = "2023.08.26"

        # Pendulum swing
        self.pendulum_swing_id = "cuckoo_clock_pendulum_swing"
        self.pendulum_swing_topic_prefix = f"homeassistant/switch/{self.pendulum_swing_id}"

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
        self.chime_id = "cuckoo_clock_chime"
        self.chime_topic_prefix = f"homeassistant/switch/{self.chime_id}"

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
        self.timer_id = "cuckoo_clock_timer"
        self.timer_topic_prefix = f"homeassistant/number/{self.timer_id}"

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
        self.pendulum_light_id = "cuckoo_clock_pendulum_light"
        self.pendulum_light_topic_prefix = f"homeassistant/light/{self.pendulum_light_id}"

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
        self.dial_id = "cuckoo_clock_dial"
        self.dial_topic_prefix = f"homeassistant/light/{self.dial_id}"

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
        self.light_sensor_id = "cuckoo_clock_brightness"
        self.light_sensor_topic_prefix = f"homeassistant/sensor/{self.light_sensor_id}"

        light_sensor_payload = {}
        light_sensor_payload['name'] = 'Light Level'
        light_sensor_payload['command_topic'] = f'{self.light_sensor_topic_prefix}/set'
        light_sensor_payload['state_topic'] = f'{self.light_sensor_topic_prefix}/state'
        light_sensor_payload['unique_id'] = self.light_sensor_id
        light_sensor_payload["device"] = device
        light_sensor_topic = f"{self.light_sensor_topic_prefix}/config"

        self._mqtt_client.publish(light_sensor_topic, json.dumps(light_sensor_payload))   
    
    def _update_state(self, t: Timer) -> None:
        if self.is_connected == False:
            return
        
        state = self._clock.get_state()

        pendulum_light_state = state["pendulum_light"]
        if pendulum_light_state != self._last_pendulum_light_state:
            print("Updating pendulum light")
            if self._safe_publish(f'{self.pendulum_light_topic_prefix}/state', pendulum_light_state):
                self._last_pendulum_light_state = pendulum_light_state

        pendulum_swing_state = state["pendulum_swing"]
        if pendulum_swing_state != self._last_pendulum_swing_state:
            print("Updating pendulum swing")
            if self._safe_publish(f'{self.pendulum_swing_topic_prefix}/state', pendulum_swing_state):
                self._last_pendulum_swing_state = pendulum_swing_state

        dial_state = state["dial"]
        if dial_state != self._last_dial_state:
            print(f"Updating dial {dial_state}")
            if self._safe_publish(f'{self.dial_topic_prefix}/state', dial_state):
                self._last_dial_state = dial_state

        #light_level_state = state["light_level"]
        #if light_level_state != self._last_light_sensor_state:
            #print(f"Updating light level {light_level_state}")
            #if self._safe_publish(f'{self.light_sensor_topic_prefix}/state', light_level_state):
            #    self._last_light_sensor_state = light_level_state

        chime_state = state["chime"]
        if chime_state != self._last_chime_state:
            print("Updating chime")
            if self._safe_publish(f'{self.chime_topic_prefix}/state', chime_state):
                self._last_chime_state = chime_state

    def _handle_new_message(self, topic, message) -> None:
        topic = bytes.decode(topic)
        message = bytes.decode(message)

        print(f"Topic '{topic}' recived message: {message}")

        if topic.startswith(self.pendulum_light_topic_prefix):
            self._handle_pendulum_light_message(message)                
        
        elif topic.startswith(self.pendulum_swing_topic_prefix):
            self._handle_pendulum_swing_message(message)
        
        elif topic.startswith(self.timer_topic_prefix):
            self._clock.set_timer(int(message))
    
        if topic.startswith(self.chime_topic_prefix):
            self._handle_chime_message(message)
        
        if topic.startswith(self.dial_topic_prefix):
            self._handle_dial_messafe(message)

    def _handle_pendulum_light_message(self, message: str) -> None:
        state = json.loads(message)
        if state["state"] == "OFF":
            self._clock.set_pendulum_light(0, 0, 0, False, 0)
        else:
            breate  = False
            if "effect" in state:
                if state["effect"] == "breathe":
                    breate = True
           
            if "color" in state:
                # If a colour was gven, use it
                self._clock.set_pendulum_light(state["color"]["r"], state["color"]["g"], state["color"]["b"], breate, 0)
            else:
                # Else, use a medium brightness white colour
                self._clock.set_pendulum_light(150, 150, 150, breate, 0)


    def _handle_pendulum_swing_message(self, message: str) -> None:
        if message == "OFF":
            self._clock.swing_pendulum(False, 0)
        else:
            self._clock.swing_pendulum(True, 0)

    def _handle_chime_message(self, message: str) -> None:
        if message == "ON":
            self._clock.chime()
        return
    
    def _handle_dial_messafe(self, message: str) -> None: 
        state = json.loads(message)
        if state["state"] == "OFF":
            self._clock.set_dial_light(0,0,0, None )
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

    def _safe_publish(self, topic: str, data: str) -> bool:
        if not self.is_connected:
            print(f"Cannot publish MQTT data while disconnected")
            return False
        
        try:
            self._mqtt_client.publish(topic, data)
            return True
        except Exception as e:
            print(f"Got error publishing MQTT data")
            self.stop()
            return False
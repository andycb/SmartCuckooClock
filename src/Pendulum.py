from machine import Pin, Timer, PWM

class Pendulum:

    _tagetLight = (0,0,0)
    _lightStopTime = 0
    _breath_up = True

    def __init__(self, redPin, greenPin, BluePin, swingPin) -> None:
        self.green = PWM(Pin(greenPin))
        self.blue = PWM(Pin(BluePin))
        self.red = PWM(Pin(redPin))
        self.swing = Pin(swingPin, Pin.OUT)
        self._lightTimer = None
        self._swingTimer = None

        self.red.freq(1000)
        self.green.freq(1000)
        self.blue.freq(1000)

        self._currentState = {
            "state": "OFF",
            "effect": "",
            "color": {
                "r": 0,
                "g": 0,
                "b": 0
            }
        }

    def _reset_state(self):
        self._currentState["state"] = "OFF"
        self._currentState["effect"] = ""
        self._currentState["color"]["r"] = 0
        self._currentState["color"]["g"] = 0
        self._currentState["color"]["b"] = 0
        

    def get_light_state(self):
        return self._currentState
    
    def get_swing_state(self):
        if self.swing.value() == 1:
            return "ON"
        else:
            return "OFF"

    def start_swing(self, duration_secs):
        self.swing.value(1)

        if duration_secs > 0:
            self._swingTimer = Timer(mode=Timer.ONE_SHOT, period=1000, callback=self._swing_timer_callback)

    def stop_swing(self):
        self.swing.value(0)
        if self._swingTimer != None:
            self._swingTimer.deinit()

    def _swing_timer_callback(self, t):
        self.stop_swing()

    def _light_timer_callback(self, t):
        self._tagetLight = (0, 0, 0)

        self.red.duty_u16(0)
        self.green.duty_u16(0)
        self.blue.duty_u16(0)

        self._reset_state()

        if self._breatheTimer != None:
            self._breatheTimer.deinit()

    def set_light_off(self):
        if (self._lightTimer != None):
            self._lightTimer.deinit()
        
        self._tagetLight = (0, 0, 0)

        self.red.duty_u16(0)
        self.green.duty_u16(0)
        self.blue.duty_u16(0)

        self._reset_state()
        

    def set_light(self, red, green, blue, breath, duration_secs):
        if(green > 0 and blue > 0):
            red = red * 0.6

        red_duty = (int)((red / 255) * 65025) if red > 0 else 0
        green_duty = (int)((green / 255) * 65025) if green > 0 else 0
        blue_duty = (int)((blue / 255) * 65025) if blue > 0 else 0

        print(f"Set Light ({red},{green},{blue}) / ({red_duty}, {green_duty}, {blue_duty})")

        self._tagetLight = (red_duty, green_duty, blue_duty)

        if breath == True:
            self.red.duty_u16(0)
            self.green.duty_u16(0)
            self.blue.duty_u16(0)
            self._breatheTimer = Timer(mode=Timer.PERIODIC, period=33, callback=self._breath_cyle2)
            
        else:
            self.red.duty_u16(red_duty)
            self.green.duty_u16(green_duty)
            self.blue.duty_u16(blue_duty)
        
        if (duration_secs > 0):
            self._lightTimer = Timer(mode=Timer.ONE_SHOT, period=duration_secs * 1000, callback=self._light_timer_callback)

        self._currentState["state"] = "ON"
        self._currentState["effect"] = "brethe" if breath else ""
        self._currentState["color"]["r"] = red
        self._currentState["color"]["g"] = green
        self._currentState["color"]["b"] = blue

    def _breath_cyle2(self, t):
        current_red = self.red.duty_u16()
        current_green = self.green.duty_u16()
        current_blue = self.blue.duty_u16()

        target_red = self._tagetLight[0]
        target_green = self._tagetLight[1]
        target_blue = self._tagetLight[2]

        step = (int)(65025 / 100)

        new_red = current_red
        new_blue = current_blue
        new_green = current_green
        if self._breath_up:
            if (current_red < target_red):
               new_red = min(int(current_red + step * 0.6), 65025)
            if (current_blue < target_blue):
                new_blue = min(current_blue + step, 65025)
            if (current_green < target_green):
               new_green = min(current_green + step, 65025)

            if new_red >= target_red and new_green >= target_green and new_blue >= target_blue:
                self._breath_up = False
        else:
            if (current_red > 0):
               new_red = max(int(current_red - step * 0.6), 0)
            if (current_blue > 0):
                new_blue = max(current_blue - step, 0)
            if (current_green > 0):
               new_green = max(current_green - step, 0)

            if new_red <= 0 and new_green <= 0 and new_blue <= 0:
                self._breath_up = True

        self.red.duty_u16(new_red)
        self.green.duty_u16(new_green)
        self.blue.duty_u16(new_blue)
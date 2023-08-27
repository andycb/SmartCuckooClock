from machine import Pin, Timer, PWM

class Pendulum:
    """
        Represents the clock's pendulum 
    """

    def __init__(self, redPin: int, greenPin: int, BluePin: int, swingPin: int) -> None:
        self.green = PWM(Pin(greenPin))
        self.blue = PWM(Pin(BluePin))
        self.red = PWM(Pin(redPin))
        self.swing = Pin(swingPin, Pin.OUT)
        
        self._lightTimer = None
        self._swingTimer = None

        self._targetLight = (0,0,0)
        self._lightStopTime = 0
        self._breath_up = True

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

    def get_light_state(self) -> dict:
        return self._currentState
    
    def get_swing_state(self) -> str:
        if self.swing.value() == 1:
            return "ON"
        else:
            return "OFF"

    def start_swing(self, duration_secs: int) -> None:
        self.swing.value(1)

        if duration_secs > 0:
            # Set a timer to stop the pendulum swinging again
            self._swingTimer = Timer(mode=Timer.ONE_SHOT, period=1000, callback=self._swing_timer_callback)

    def stop_swing(self) -> None:
        self.swing.value(0)
        if self._swingTimer != None:
            self._swingTimer.deinit()

    def _swing_timer_callback(self, t: Timer) -> None:
        self.stop_swing()

    def _light_timer_callback(self, t: Timer) -> None:
        # Time to turn off the light, reset everything
        self._targetLight = (0, 0, 0)

        self.red.duty_u16(0)
        self.green.duty_u16(0)
        self.blue.duty_u16(0)

        self._reset_state()

        if self._breatheTimer != None:
            self._breatheTimer.deinit()

    def set_light_off(self) -> None:
        if (self._lightTimer != None):
            self._lightTimer.deinit()
        
        self._targetLight = (0, 0, 0)

        self.red.duty_u16(0)
        self.green.duty_u16(0)
        self.blue.duty_u16(0)

        self._reset_state()
        

    def set_light(self, red: int, green: int, blue: int, breathe: bool, duration_secs: int) -> None:
        if(green > 0 and blue > 0):
            # The red LED is about a theird brighter the teh blue ans green ones, so
            # if we're blending colours together, scale down the red value to match the others
            redScaled = red * 0.6
        else:
            redScaled = red

        red_duty = (int)((redScaled / 255) * 65025) if redScaled > 0 else 0
        green_duty = (int)((green / 255) * 65025) if green > 0 else 0
        blue_duty = (int)((blue / 255) * 65025) if blue > 0 else 0

        print(f"Set Light ({redScaled},{green},{blue}) / ({red_duty}, {green_duty}, {blue_duty})")

        self._targetLight = (red_duty, green_duty, blue_duty)

        if breathe == True:
            # If set the breathe, set a timer to fade the light up ad down rhythmically
            self.red.duty_u16(0)
            self.green.duty_u16(0)
            self.blue.duty_u16(0)
            self._breatheTimer = Timer(mode=Timer.PERIODIC, period=33, callback=self._breath_cycle)
            
        else:
            self.red.duty_u16(red_duty)
            self.green.duty_u16(green_duty)
            self.blue.duty_u16(blue_duty)
        
        if (duration_secs > 0):
            # Create a timer to turn the light back off again
            self._lightTimer = Timer(mode=Timer.ONE_SHOT, period=duration_secs * 1000, callback=self._light_timer_callback)

        self._currentState["state"] = "ON"
        self._currentState["effect"] = "brethe" if breathe else ""
        self._currentState["color"]["r"] = red
        self._currentState["color"]["g"] = green
        self._currentState["color"]["b"] = blue

    def _breath_cycle(self, t: Timer) -> None:
        current_red = self.red.duty_u16()
        current_green = self.green.duty_u16()
        current_blue = self.blue.duty_u16()

        target_red = self._targetLight[0]
        target_green = self._targetLight[1]
        target_blue = self._targetLight[2]

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
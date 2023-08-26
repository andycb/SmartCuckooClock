
import RingPatterns
from Pendulum import Pendulum
from DialRing import DialRing, Colour
from LightMeter import LightMeter
from Chime import Chime
import json

class Clock:
    def __init__(self):
        print("Clock __init()__")
        self._pendulum = Pendulum(6, 9, 10, 17)
        self._lightMeter = LightMeter(28)
        self._dialRing = DialRing(27, self._lightMeter)
        self._chime = Chime(14, 15)
        
        self._dialRing.clear()

    def reset(self):
        self._pendulum.set_light_off()
        self._pendulum.stop_swing()
        self._dialRing.clear()

    def clear_ring_pattern(self):
        self._dialRing.clear()
        
    def show_waiting(self):
        self._dialRing.showPattern(RingPatterns.BootingPattern())

    def show_boot_error(self):
        self._dialRing.showPattern(RingPatterns.ErrorPattern())

    def set_pendulum_light(self, red, green, blue, breathe, duration_secs):
        self._pendulum.set_light(red, green, blue, breathe, duration_secs)
    
    def set_dial_light(self, red, green, blue, pattern):
        self._dialRing.set_dial_ring(Colour(red, green, blue), pattern)

    def swing_pendulum(self, swing, time):
        if swing:
            self._pendulum.start_swing(time)
        else:
            self._pendulum.stop_swing()

    def set_timer(self, seconds):
        if (seconds == 0):
            self._dialRing.clear()
        else:    
            self._dialRing.showPattern(RingPatterns.CountdownPattern(seconds))

    def chime(self):
        self._chime.chime()

    def get_state(self):
        return {
            "pendulum_light": json.dumps(self._pendulum.get_light_state()),
            "pendulum_swing": self._pendulum.get_swing_state(),
            "light_level": self._lightMeter.GetOffset(), 
            "chime": self._chime.get_state(), 
            "dial": json.dumps(self._dialRing.get_state()), 
        }
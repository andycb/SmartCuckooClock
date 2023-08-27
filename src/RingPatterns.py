import time

from machine import Timer, RTC
import math
from Colour import Colour

class BasePattern():
    """
        BAse class for patterns that can be shown on the dial ring
    """
    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def show(self) -> list:
        return []

class SolidPattern(BasePattern):
    """
        A solid light of a given colour with no animation
    """
    def __init__(self, colour):
         self._colour = colour

    def start(self) -> None:
        pass
    
    def stop(self) -> None:
        pass

    def show(self) -> list:
        return [self._colour] * 20

class ErrorPattern(BasePattern):
    """
        A counter-clockwise rotating ring os red lights, shown with the clock has an error.
    """
    def __init__(self):
        self._current = 19
        self._array = [Colour(0,0,0)] * 20
        
    def start(self):
        self._timer = Timer(mode=Timer.PERIODIC, period=200, callback=self._callback)

    def stop(self):
        if self._timer != None:
            self._timer.deinit()
            self._timer = None

    def show(self):
        return self._array
    
    def _callback(self, t):
        self._array = [Colour(50, 0,0)] * 20

        if self._current < 0:
            self._current = 19

        self._array[self._current] = Colour(0,0,0)
        self._current -= 1

class BootingPattern(BasePattern):
    """"
        A single rotating green light, shown as the clock is connecting.
    """
    def __init__(self):
        self._current = 19
        self._array = [Colour(0,0,0)] * 20
        
    def start(self):
        self._timer = Timer(mode=Timer.PERIODIC, period=50, callback=self._callback)

    def stop(self):
        if self._timer != None:
            self._timer.deinit()
            self._timer = None

    def show(self):
        return self._array
    
    def _callback(self, t):
        self._array = [Colour(0, 0,0)] * 20

        if self._current > 19:
            self._current =0

        self._array[self._current] = Colour(0,50,0)
        self._current += 1

class CountdownPattern(BasePattern):
    """
        A countdown timer that uses the ring to show the percentage of the timer duration remaining.
    """
    def __init__(self, timer_seconds):
        self._timer_seconds = timer_seconds
        self._end_time = time.ticks_add(time.ticks_ms(), timer_seconds * 1000)

        print(f"Timer set. Seconds = {timer_seconds}, Start time = {time.ticks_ms()}, End Time = {self._end_time}")
        
    def start(self):
        pass

    def stop(self):
        pass

    def show(self):
        diff = time.ticks_diff(self._end_time, time.ticks_ms())
        print(f"Timer callback. Diff = {diff}, Now = {time.ticks_ms()}, End Time = {self._end_time}")

        if diff < 0:
            print("Stopped.")
            self.stop()
            return None
        else:
            timer_ms = self._timer_seconds * 1000
            pc = diff / timer_ms
            pc = pc
            normalized = 20 * pc
            self._setValue(normalized, Colour(100,100,100))

        return self._array


    def _setValue(self, value, colour):
        self._array = [Colour(0,0,0)] * 20
        if value == 0:
            
            return
        
        whole = (int)(math.floor(value))

        for i in range (whole):
            self._array[i] = colour

        remainder = value - whole
        if remainder > 0:
            brightness = (int)(100 * remainder)
            self._array[whole] = Colour(brightness,brightness,brightness)


class AlertPattern(BasePattern):
    """
        A rapidly blue light on a green ring.
    """
    def __init__(self):
        self._current = 19
        self._array = [Colour(0,0,0)] * 20
        self._loops = 0
        
    def start(self):
        self._timer = Timer(mode=Timer.PERIODIC, period=25, callback=self._callback)

    def stop(self):
        if self._timer != None:
            self._timer.deinit()
            self._timer = None
            self._loop = 0

    def show(self):
        return self._array
    
    def _callback(self, t):
        self._array = [Colour(0, 255,0)] * 20

        if self._current < 0:
            self._current = 19
            if self._loops == 6:
                self.stop()
            else:
                self._loops += 1

        self._array[self._current] = Colour(0,0,255)
        self._current -= 1

class CurrentTimePattern(BasePattern):
    """
        Displays the current time. (very badly) 
    """
    def __init__(self):
        self._current = 19
        self._array = [Colour(0,0,0)] * 20
        self._loops = 0
        
    def start(self):
        self._timer = Timer(mode=Timer.PERIODIC, period=1000, callback=self._callback)

    def stop(self):
        if self._timer != None:
            self._timer.deinit()
            self._timer = None
            self._loop = 0
        
        self._array = None

    def show(self):
        return self._array
    
    def _callback(self, t):
        now = RTC().datetime()
        self._array = [Colour(0,0,0)] * 20

        h = now[4]
        m = now[5]
        s = now[6]

        print(f"Current time is {h}:{m}:{s} UTC+0")

        if h >= 12:
            h -= 12

        hourLed = (int)((h / 12) * 20)
        minLed = (int)((m / 60) * 20)
        secLed = (int)((s / 60) * 20)
        
        self._array[minLed] = Colour(0,0,10)
        self._array[hourLed] = Colour(0,10,0)
        #self._array[secLed] = Colour(3,0,0)
    
import time

from machine import Timer
import math
from Colour import Colour

class ErrorPattern:

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

class BootingPattern:

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

class CountdownPattern:

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
            normalised = 20 * pc
            self._setValue(normalised, Colour(100,100,100))

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
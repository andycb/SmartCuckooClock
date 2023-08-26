
from machine import Pin, Timer
import neopixel
import math
from Colour import Colour
import RingPatterns
import time

class DialRing:
    def __init__(self, dataPin, light_meater):
        self.light_meater = light_meater

        self.np = neopixel.NeoPixel(Pin(dataPin), 20)
        self._pattern = None
        self._refreshTimer = None
        self._colourOverride = None
        
    def _swap_pattern_callback(self, t):
        if self._pattern != None:
            array = self._pattern.show()
            
            if array is None and self._refreshTimer is not None:
                print("Pattern retruned None. Removing pattern")
                self._refreshTimer.deinit()
                self._refreshTimer = None
                self._pattern = None
                self.clear()
                return
            
            for i in range(20):
                colour = self._colourOverride if self._colourOverride != None else array[i]
                #corrected = self._calculateColourForLightLevel(array[i], self.light_meater.GetOffset())
                corrected = colour
                self.np[i] = (corrected.red, corrected.green, corrected.blue)

            self.np.write()
            
        elif self._refreshTimer != None:
                self._refreshTimer.deinit()
                self._refreshTimer = None

    def _calculateColourForLightLevel(self, input, reading): 
        brightnessOffset = reading * 60

        red = 0 if input.red is 0 else max(10, input.red - brightnessOffset)
        green = 0 if input.green is 0 else max(10, input.green - brightnessOffset)
        blue = 0 if input.blue is 0 else max(10, input.blue - brightnessOffset)

        corrected = Colour(
            int(red),
            int(green),
            int(blue),
        )

        return corrected

    def showPattern(self, pattern):
        print("Show pattern")
        if self._pattern != None:
            self._pattern.stop()

        if self._refreshTimer is None:
            self._refreshTimer = Timer(mode=Timer.PERIODIC, period=30, callback=self._swap_pattern_callback)
    
        self._pattern = pattern
        self._pattern.start()

    def setTimeSnapped(self, h, m, s = None):
        hourLed = (int)((h / 12) * 20)
        minLed = (int)((m / 60) * 20)
        
        print(hourLed)
        print(minLed)
        
        self.clearNoShow()
        self.np[minLed] = (0,0,10)
        self.np[hourLed] = (10,0,0)
        
        if s is not None:
            secLed = (int)((s / 60) * 20)
            self.np[secLed] = (0,10,0)
        
        self.np.write()
        
    def setPercentage(self, pc):
        normalised = (20 / 100) * pc
        self.setValue(normalised)
        
    _currentLoadingState = 0
    def _loading_callback(self, t):
        self.clearNoShow()
        
        val = (0,0,0)
        if self._currentLoadingState % 1 == 0:
            val = (50,0,0)
            
        elif self._currentLoadingState % 2 == 0:
            val = (0,50,0)
            
        else:
            val = (0,0,50)
        
        self._currentLoadingState += 1
        if (self._currentLoadingState > 20):
            self._currentLoadingState = 0
        
        self.np[self._currentLoadingState] = val
        self.np.write()
            
    def setValue(self, value, colour):
        if value == 0:
            self.clear()
            return
        
        whole = math.floor(value)

        for i in range (whole):
            self.np[i] = colour
            
        for i in range (whole + 1, 20):
            self.np[i] = (0,0,0)
            
        remainder = value - whole
        if remainder > 0:
            brightness = (int)(255 * remainder)
            self.np[whole] = (brightness,brightness,brightness)
        
        
        self.np.write()
        
        
    def clearNoShow(self):
        self.np.fill((0,0,0))
        self.np.write()

        if self._refreshTimer != None: 
            self._refreshTimer.deinit()
            self._refreshTimer = None
        
    def clear(self):
        self.np.fill((0,0,0))
        self.np.write()
        self._colourOverride = None

        if self._refreshTimer != None: 
            self._refreshTimer.deinit()
            self._refreshTimer = None

    def set_dial_ring(self, colour, pattern):
        self._colourOverride = colour
        if (self._pattern != None):
            self.clear()
        
        self.showPattern(RingPatterns.SolidPattern(colour) if pattern == None else pattern)

    def get_state(self):
        return {
            "state": "OFF" if self._pattern == None else "ON",
            "effect": "" if self._pattern == None and False else type(self._pattern).__name__,
            "color": {
                "r": 255 if self._colourOverride == None else self._colourOverride.red,
                "g": 255 if self._colourOverride == None else self._colourOverride.green,
                "b": 255 if self._colourOverride == None else self._colourOverride.blue,
            }
        }

from machine import Pin, Timer
import neopixel
import math
from Colour import Colour
import RingPatterns
from LightMeter import LightMeter

class DialRing:
    """
        Represents the ring og RGB lights surrounding the clock dial
    """

    def __init__(self, dataPin: int, light_meter: LightMeter) -> None:
        self._light_meter = light_meter

        self.np = neopixel.NeoPixel(Pin(dataPin), 20)
        self._pattern = None 
        self._refreshTimer = None
        self._colourOverride = None

        # Light meter isn't working quite right at the moment, so disable it
        self._use_light_meter = True
        
    def _swap_pattern_callback(self, t: Timer) -> None:
        if self._pattern != None:
            # Get the data for this frame
            array = self._pattern.show()
            
            # If the pattern returns no data, stop it and clean up
            if array is None and self._refreshTimer is not None:
                print("Pattern retruned None. Removing pattern")
                self._refreshTimer.deinit()
                self._refreshTimer = None
                self._pattern = None
                self.clear()
                return
            
            # Copy over the pattern data to the NeoPixel ring
            for i in range(20):
                colour = self._colourOverride if self._colourOverride != None else array[i]
                
                corrected = colour
                if self._use_light_meter:
                    # Dim the brightness according to the ambient light
                    corrected = self._calculateColourForLightLevel(array[i], self._light_meter.GetOffset())
                
                self.np[i] = (corrected.red, corrected.green, corrected.blue)

            # Show it!
            self.np.write()
            
        elif self._refreshTimer != None:
                # If there is no longer an active pattern, stop the refresh timerß
                self._refreshTimer.deinit()
                self._refreshTimer = None

    def _calculateColourForLightLevel(self, input: Colour, reading: float) -> Colour: 
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

    def showPattern(self, pattern) -> None:
        if self._pattern != None:
            # Stop the current pattern if one is already running
            self._pattern.stop()

        if self._refreshTimer is None:
            # Refresh the ring at 30 FPS
            period = int(1000 / 30)
            self._refreshTimer = Timer(mode=Timer.PERIODIC, period=period, callback=self._swap_pattern_callback)
    
        self._pattern = pattern
        self._pattern.start()
        
    def clearNoShow(self) -> None:
        # Clear the current array, but don't wrote it to the ring
        self.np.fill((0,0,0))
        self.np.write()

        self._pattern = None 
        
        if self._refreshTimer != None: 
            self._refreshTimer.deinit()
            self._refreshTimer = None
        
    def clear(self) -> None:
        if self._refreshTimer != None: 
            self._refreshTimer.deinit()
            self._refreshTimer = None
    
        # Clear the current ring value
        self.np.fill((0,0,0))
        self.np.write()
        self._colourOverride = None


    def set_dial_ring(self, colour: Colour, pattern: RingPatterns.BasePattern) -> None:
        if colour.red == 0 and colour.green == 0 and colour.blue == 0:
            self.clear()
            return

        self._colourOverride = colour
        if (self._pattern != None):
            self.clear()
        self.showPattern(RingPatterns.SolidPattern(colour) if pattern == None else pattern)

    def get_state(self) -> dict:
        return {
            "state": "OFF" if self._pattern == None else "ON",
            "effect": "" if self._pattern == None and False else type(self._pattern).__name__,
            "color": {
                "r": 255 if self._colourOverride == None else self._colourOverride.red,
                "g": 255 if self._colourOverride == None else self._colourOverride.green,
                "b": 255 if self._colourOverride == None else self._colourOverride.blue,
            }
        }
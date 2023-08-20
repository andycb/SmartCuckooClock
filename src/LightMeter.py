from machine import Pin, ADC
import time

class LightMeter:
    _min = 950
    _max = 1100
    def __init__(self, lightPin):
        self._adc = ADC(Pin(lightPin))
        self._lastReadTicks = None
        self._cachedValue = 0
        pass

    def GetOffset(self):
        now = time.ticks_ms()

        if self._lastReadTicks is not None:
            if time.ticks_diff(now, self._lastReadTicks) < 2000:
                return self._cachedValue
            
        self._lastReadTicks = now

        rawValue = self._adc.read_u16()
        value = rawValue - self._min
        value = max(0, value)
        value = min(self._max, value)

        percent = value / (self._max - self._min)

        self._cachedValue = value
        return percent
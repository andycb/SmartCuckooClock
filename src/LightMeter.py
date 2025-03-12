from machine import Pin, ADC
import time

class LightMeter:
    """
        Represents the ambient light sensor
    """
    _min: int = 950  # The value to be consisted the the brightest the room will be
    _max: int = 1100 # The value to be consisted the the darkest the room will be

    def __init__(self, lightPin):
        self._adc = ADC(Pin(lightPin))
        self._lastReadTicks = None
        self._cachedValue = 0
        pass

    def GetOffsetAndRaw(self):
        return {
            "percent": self._cachedValue,
            "raw": self._rawValue,
        }

    def GetOffset(self) -> float:
        """
            Returns a value between 0 and 1, where 0 is the ful brightness and 1 is darkness
        """
        now = time.ticks_ms()

        # The ADC is kind of slow, so cache all readings for 30 second
        if self._lastReadTicks is not None:
            if time.ticks_diff(now, self._lastReadTicks) < 30000:
                return self._cachedValue
            
        self._lastReadTicks = now

        rawValue = self._adc.read_u16()
        value = rawValue - self._min
        value = max(0, value)
        value = min(self._max, value)

        percent = value / (self._max - self._min)
        percent = max(percent, 0)
        percent = min(percent, 1)

        self._rawValue = rawValue
        self._cachedValue = percent
        return percent
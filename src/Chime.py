from machine import Pin
import time
import _thread

class Chime:
    """
    Represents the chime function of the clock, where the Cuckoo exits sings and returns to its base.
    """

    def __init__(self, chime_pin: int, reset_pin: int) -> None:
        self._chime = Pin(chime_pin, Pin.OUT)
        self._reset = Pin(reset_pin, Pin.OUT)
        self._chime_lock = _thread.allocate_lock()

        self._chime.off()
        self._reset.off()
    
    def chime(self) -> None:

        # The chime requires some sleep for timing, so run that on a separate thread, but only if we're not already chiming
        if self._chime_lock.acquire(False):
            _thread.start_new_thread(self._chime_internal, ())

    def _chime_internal(self) -> None:
        try:
            self._chime.on()
            
            time.sleep(1.7)
            self._reset.on()
            self._chime.off()
            
            time.sleep(0.5)
            self._reset.off()
        finally:
            self._chime_lock.release()

    def get_state(self):
        return "ON" if self._chime.value() == 1 else "OFF"
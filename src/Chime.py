from machine import Pin
import time
import _thread

class Chime:
    def __init__(self, chime_pin, reset_pin):
        self._chime = Pin(chime_pin, Pin.OUT)
        self._reset = Pin(reset_pin, Pin.OUT)
        self._chime_lock = _thread.allocate_lock()

        #self._reset.on()
        time.sleep(0.5)
        self._chime.off()
        self._reset.off()
    
    def chime(self):
        if self._chime_lock.acquire(False):
            _thread.start_new_thread(self._chime_internal, ())

    def _chime_internal(self):
        try:
            self._chime.on()
            time.sleep(1.7)
            self._reset.on()

            time.sleep(0.3)
            self._chime.off()
            self._reset.off()
        finally:
            self._chime_lock.release()

    def get_state(self):
        return "ON" if self._chime.value() == 1 else "OFF"
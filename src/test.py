from ClockManager import ClockManager
import time

cm = ClockManager()
cm.boot()

while True:
    time.sleep(0.5)
from ClockManager import ClockManager
import time

# Boot the clock
global cm
cm = ClockManager()
cm.boot()

# just spin so that the debugger can continue to catch console output
while True:
    time.sleep(60)
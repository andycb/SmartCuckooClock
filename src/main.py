from ClockManager import ClockManager
import time

global cm
cm = ClockManager()
cm.boot()

time.sleep(15)
print("Skilling wifi now..")
cm._wlan.disconnect()

while True:
    time.sleep(0.5)
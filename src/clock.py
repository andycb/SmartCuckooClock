import network
import time

from machine import Pin, ADC, Timer, RTC, PWM
import neopixel
import time
import math

import network
import socket
import time
import struct
import _thread

class Clock:
    def __init__(self, ap_name, ap_key) -> None:
        self._gpioLock = _thread.allocate_lock()

        self._pendulum = Pendulum(6, 9, 10, 17, self._gpioLock)
        self._lightMeter = LightOffset(28)
        self._dialRing = DialRing(27, self._lightMeter)
        
        

        self._bootup( ap_name, ap_key)

    def _bootup(self, ap_name, ap_key):
        self._show_waiting()

        try:
            print("Connecting to wifi...")
            self._connect_wifi(ap_name, ap_key)
            print("Setting time...")
            self._dialRing.clear()
            self._set_time()
        except:
            print("...Failed")
            self._show_boot_error()
            return
        
        print("...Done")

    def reset(self):
        pass
        
    def _show_waiting(self):
        self._dialRing.showPattern(BootingPattern())
        pass

    def _show_boot_error(self):
        self._dialRing.showPattern(ErrorPattern())

    def set_pendulum_light(self, red, green, blue, breathe, duration_secs):
        self._pendulum.set_light(red, green, blue, breathe, duration_secs)

    def _connect_wifi(self, name, psk):
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)

        wlan.connect(name, psk)

        max_wait = 10
        while max_wait > 0:
            if wlan.status() < 0 or wlan.status() >= 3:
                break
            max_wait -= 1

            time.sleep(1)

        #Handle connection error
        if wlan.status() != 3:
            raise RuntimeError('wifi connection failed')
        else:
            print('connected')

        status = wlan.ifconfig()
        print('ip = ' + status[0])

    def _set_time(self):
        NTP_DELTA = 2208988800
        host = "pool.ntp.org"

        NTP_QUERY = bytearray(48)
        NTP_QUERY[0] = 0x1B
        addr = socket.getaddrinfo(host, 123)[0][-1]
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        try:
            s.settimeout(1)
            res = s.sendto(NTP_QUERY, addr)
            msg = s.recv(48)
        finally:
            s.close()

        val = struct.unpack("!I", msg[40:44])[0]
        t = val - NTP_DELTA    
        tm = time.gmtime(t)

        RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))


class Pendulum:

    _tagetLight = (0,0,0)
    _lightStopTime = 0
    _breath_up = True

    def __init__(self, redPin, greenPin, BluePin, swingPin, lock) -> None:
        self._lock = lock

        self.green = PWM(Pin(greenPin))
        self.blue = PWM(Pin(BluePin))
        self.red = PWM(Pin(redPin))
        self.swing = Pin(swingPin, Pin.OUT)

        self.red.freq(1000)
        self.green.freq(1000)
        self.blue.freq(1000)

    def start_swing(self, duration_secs):
        self.swing.value(1)

        if duration_secs > 0:
            self._swingTimer = Timer(mode=Timer.ONE_SHOT, period=1000, callback=self._swing_timer_callback)

    def stop_swing(self):
        self.swing.value(0)
        if self._swingTimer != None:
            self._swingTimer.deinit()

    def _swing_timer_callback(self, t):
        self.stop_swing()

    def _light_timer_callback(self, t):
        self._tagetLight = (0, 0, 0)

        self.red.duty_u16(0)
        self.green.duty_u16(0)
        self.blue.duty_u16(0)

        if self._breatheTimer != None:
            self._breatheTimer.deinit()

    def set_light_off(self):
        if (self._lightTimer != None):
            self._lightTimer.deinit()
        
        self._tagetLight = (0, 0, 0)

        self.red.duty_u16(0)
        self.green.duty_u16(0)
        self.blue.duty_u16(0)
        

    def set_light(self, red, green, blue, breath, duration_secs):

        red_duty = (int)((red / 255) * 65025) if red > 0 else 0
        green_duty = (int)((green / 255) * 65025) if green > 0 else 0
        blue_duty = (int)((blue / 255) * 65025) if blue > 0 else 0

        print(f"Set Light ({red},{green},{blue}) / ({red_duty}, {green_duty}, {blue_duty})")

        self._tagetLight = (red_duty, green_duty, blue_duty)

        if breath == True:
            self.red.duty_u16(0)
            self.green.duty_u16(0)
            self.blue.duty_u16(0)
            self._breatheTimer = Timer(mode=Timer.PERIODIC, period=33, callback=self._breath_cyle2)
            
        else:
            self.red.duty_u16(red_duty)
            self.green.duty_u16(green_duty)
            self.blue.duty_u16(blue_duty)
        
        if (duration_secs > 0):
            self._lightTimer = Timer(mode=Timer.ONE_SHOT, period=duration_secs * 1000, callback=self._light_timer_callback)

    def _breath_cyle2(self, t):
        current_red = self.red.duty_u16()
        current_green = self.green.duty_u16()
        current_blue = self.blue.duty_u16()

        target_red = self._tagetLight[0]
        target_green = self._tagetLight[1]
        target_blue = self._tagetLight[2]

        step = (int)(65025 / 100)

        #print(f"PWM Timer. Target = ({target_red},{target_blue},{target_green}). Current = ({current_red},{current_blue},{current_green}), Direction = {self._breath_up}")

        new_red = current_red
        new_blue = current_blue
        new_green = current_green
        if self._breath_up:
            if (current_red < target_red):
               new_red = min(current_red + step, 65025)
            if (current_blue < target_blue):
                new_blue = min(current_blue + step, 65025)
            if (current_green < target_green):
               new_green = min(current_green + step, 65025)

            if new_red >= target_red and new_green >= target_green and new_blue >= target_blue:
                self._breath_up = False
        else:
            if (current_red > 0):
               new_red = max(current_red - step, 0)
            if (current_blue > 0):
                new_blue = max(current_blue - step, 0)
            if (current_green > 0):
               new_green = max(current_green - step, 0)

            if new_red <= 0 and new_green <= 0 and new_blue <= 0:
                self._breath_up = True

        self._lock.acquire()
        self.red.duty_u16(new_red)
        self.green.duty_u16(new_green)
        self.blue.duty_u16(new_blue)
        self._lock.release()

        #print(f"Done. Target = ({target_red},{target_blue},{target_green}). Current = ({new_red},{new_blue},{new_green}), Direction = {self._breath_up}")

    def _breath_cyle(self):
        while True:
            try: 
                if self._tagetLight == (0, 0, 0):
                    return
                
                for d in range(65025):
                    print(f"Duty {d}")

                    if d < self._tagetLight[0]:
                        self.red.duty_u16(d)
                    
                    if d < self._tagetLight[1]:
                        self.green.duty_u16(d)
                    
                    if d < self._tagetLight[2]:
                        self.blue.duty_u16(d)


                for d in range(65025, 0, -1):
                    print(f"Duty {d}")

                    self.red.duty_u16(d)
                    self.green.duty_u16(d)
                    self.blue.duty_u16(d)
            except:
                print(f"Error")

class DialRing:
    def __init__(self, dataPin, light_meater):
        self.light_meater = light_meater
        self.np = neopixel.NeoPixel(Pin(dataPin), 20)
        self.np.fill((0,0,0))
        self.np.write
        
        self._pattern = None
        self._refreshTimer = Timer(mode=Timer.PERIODIC, period=30, callback=self._swap_pattern_callback)
        
    def _swap_pattern_callback(self, t):
        print("Try Swap Colour Ring")
        if self._pattern != None:
            print("Swap Colour Ring")
            array = self._pattern.show()
            
            if array is None and self._refreshTimer is not None:
                print("Pattern retruned None. Removing pattern")
                self._refreshTimer.deinit()
                self._refreshTimer = None
                self._pattern = None
                self.clear()
                return
            
            for i in range(20):
                corrected = self._calculateColourForLightLevel(array[i], self.light_meater.GetOffset())
                self.np[i] = (corrected.red, corrected.green, corrected.blue)
                #self.np[i] = (array[i].red, array[i].green, array[i].blue)

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

        #print(f"Brightness offset is {brightnessOffset}. Input = ({input.red},{input.green},{input.blue}). corrected = ({corrected.red},{corrected.green},{corrected.blue})")
        return corrected

    def showPattern(self, pattern):
        if self._pattern != None:
            self._pattern.stop()
    
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

        if self._refreshTimer != None: 
            self._refreshTimer.deinit()
            self._refreshTimer = None


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

class Colour:
    def __init__(self, r, g, b) -> None:
        self.red = r
        self.green = g
        self.blue = b


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



class LightOffset:
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
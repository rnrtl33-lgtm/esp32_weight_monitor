from machine import Pin
import time

class HX711:
    def __init__(self, dt, sck, gain=128):
        self.dt = Pin(dt, Pin.IN)
        self.sck = Pin(sck, Pin.OUT)
        self.offset = 0
        self.scale = 1.0

        self.gain = gain
        self._set_gain()

    def _set_gain(self):
        if self.gain == 128:
            self._gain_pulses = 1
        elif self.gain == 64:
            self._gain_pulses = 3
        elif self.gain == 32:
            self._gain_pulses = 2
        else:
            self._gain_pulses = 1

        self.read()  # dummy read to apply gain

    def is_ready(self):
        return self.dt.value() == 0

    def read(self):
        while not self.is_ready():
            time.sleep_us(10)

        value = 0
        for _ in range(24):
            self.sck.on()
            value = (value << 1) | self.dt.value()
            self.sck.off()

        for _ in range(self._gain_pulses):
            self.sck.on()
            self.sck.off()

        if value & 0x800000:
            value |= ~0xffffff

        return value

    def tare(self, times=50):
        total = 0
        for _ in range(times):
            total += self.read()
        self.offset = total / times

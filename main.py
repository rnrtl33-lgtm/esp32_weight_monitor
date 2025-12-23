print("ESP32 WEIGHT MONITOR - BOOT OK")
import time
from lib.hx711_esp32 import HX711

hxA = HX711(dt=34, sck=33)
hxB = HX711(dt=35, sck=32)

hxA.scale = 413.8759
hxB.scale = 708.0524

print("TARING...")
time.sleep(3)
hxA.tare(50)
hxB.tare(50)
print("READY")

while True:
    wA = (hxA.read() - hxA.offset) / hxA.scale
    wB = (hxB.read() - hxB.offset) / hxB.scale

    print("A:", round(wA,1), "g | B:", round(wB,1), "g")
    time.sleep(2)

print("ESP32 WEIGHT MONITOR - BOOT OK")

import time
import urequests
from lib.hx711_esp32 import HX711

# ---------------- ThingSpeak ----------------
API_A = "EU6EE36IJ7WSVYP3"   # Channel A
API_B = "E8CTAK8MCUWLVQJ2"   # Channel B

def send_ts(api, weight):
    url = "https://api.thingspeak.com/update?api_key={}&field4={}".format(
        api, round(weight, 1)
    )
    try:
        r = urequests.get(url)
        r.close()
        print("TS SENT:", weight)
    except Exception as e:
        print("TS ERROR:", e)

# ---------------- HX711 ----------------
hxA = HX711(dt=34, sck=33)   # A → 5 kg
hxB = HX711(dt=35, sck=32)   # B → 1 kg

hxA.scale = 413.8759
hxB.scale = 708.0524

print("TARING...")
time.sleep(3)
hxA.tare(50)
hxB.tare(50)
print("READY")

# ---------------- TIMING ----------------
READ_INTERVAL = 2        # seconds
SEND_INTERVAL = 60       # 1 minute

last_send = time.time()

# ================= MAIN LOOP =================
while True:
    # ----- READ -----
    wA = (hxA.read() - hxA.offset) / hxA.scale
    wB = (hxB.read() - hxB.offset) / hxB.scale

    print("A:", round(wA,1), "g | B:", round(wB,1), "g")

    now = time.time()

    # ----- SEND TO TS -----
    if now - last_send >= SEND_INTERVAL:
        send_ts(API_A, wA)
        send_ts(API_B, wB)
        last_send = now

    time.sleep(READ_INTERVAL)

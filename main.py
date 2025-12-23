# ==========================================
# ESP32 WEIGHT MONITOR + ThingSpeak
# AUTO RESET EVERY 6 HOURS (OTA SAFE)
# ==========================================

print("ESP32 WEIGHT MONITOR - BOOT OK")

import time, gc, machine
import urequests
from lib.hx711_esp32 import HX711

# -------- ThingSpeak --------
API_A = "EU6EE36IJ7WSVYP3"
API_B = "E8CTAK8MCUWLVQJ2"

def send_ts(api, value):
    url = "https://api.thingspeak.com/update?api_key={}&field4={}".format(
        api, round(value,1)
    )
    try:
        r = urequests.get(url)
        r.close()
        print("TS SENT:", value)
    except Exception as e:
        print("TS ERROR:", e)

# -------- HX711 --------
hxA = HX711(dt=34, sck=33)   # A → 5kg
hxB = HX711(dt=35, sck=32)   # B → 1kg

hxA.scale = 413.8759
hxB.scale = 708.0524

print("TARING...")
time.sleep(3)
hxA.tare(50)
hxB.tare(50)
print("READY")

# -------- TIMING --------
READ_INTERVAL = 2                 # قراءة كل 2 ثانية
SEND_INTERVAL =  60           # إرسال كل 10 دقائق
RESET_INTERVAL = 6 * 60 * 60      # Reset كل 6 ساعات

last_send = time.time()
start_time = time.time()

last_A = 0
last_B = 0
DELTA_G = 5                       # تجاهل الضجيج أقل من 5g

# ==========================
# MAIN LOOP
# ==========================
while True:
    try:
        wA = (hxA.read() - hxA.offset) / hxA.scale
        wB = (hxB.read() - hxB.offset) / hxB.scale

        print("A:", round(wA,1), "g | B:", round(wB,1), "g")

        now = time.time()

        # ----- SEND -----
        if now - last_send >= SEND_INTERVAL:
            if abs(wA - last_A) >= DELTA_G:
                send_ts(API_A, wA)
                last_A = wA

            if abs(wB - last_B) >= DELTA_G:
                send_ts(API_B, wB)
                last_B = wB

            last_send = now
            gc.collect()

        # ----- AUTO RESET (OTA CHECK) -----
        if now - start_time >= RESET_INTERVAL:
            print("AUTO RESET FOR OTA CHECK")
            time.sleep(2)
            machine.reset()

    except Exception as e:
        print("ERROR:", e)

    time.sleep(READ_INTERVAL)

# ==========================================
# ESP32 DUAL WEIGHT → ThingSpeak (A + B)
# ==========================================

import time, gc
import network, urequests
from lib.hx711 import HX711

# ================= WIFI =================
SSID = "stc_wifi_8105"
PASSWORD = "bfw6qrn7tu3"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting WiFi...")
        wlan.connect(SSID, PASSWORD)
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(1)
    print("WiFi connected:", wlan.isconnected())
    return wlan.isconnected()

connect_wifi()

# ================= THINGSPEAK =================
API_KEY_A = "EU6EE36IJ7WSVYP3"
API_KEY_B = "E8CTAK8MCUWLVQJ2"

def send_ts(api, value, label):
    try:
        url = "https://api.thingspeak.com/update?api_key={}&field4={}".format(
            api, round(value, 1)
        )
        r = urequests.get(url)
        r.close()
        print("TS SENT", label, "=", round(value, 1))
    except Exception as e:
        print("TS ERROR", label, e)

# ================= HX711 =================
hxA = HX711(dt=34, sck=33)
hxA.offset = 46770.14
hxA.scale  = 410.05076

hxB = HX711(dt=35, sck=32)
hxB.offset = 24163.08
hxB.scale  = 416.56064

# ================= SETTINGS =================
SEND_INTERVAL = 60   # إرسال كل 60 ثانية
N = 7                # فلترة بسيطة

bufA, bufB = [], []

print("SYSTEM STARTED")

# ================= MAIN LOOP =================
while True:
    try:
        # ---- READ ----
        wA = (hxA.read() - hxA.offset) / hxA.scale
        wB = (hxB.read() - hxB.offset) / hxB.scale

        bufA.append(wA)
        bufB.append(wB)
        if len(bufA) > N: bufA.pop(0)
        if len(bufB) > N: bufB.pop(0)

        avgA = sum(bufA) / len(bufA)
        avgB = sum(bufB) / len(bufB)

        print("A:", round(avgA,1), "g | B:", round(avgB,1), "g")

        # ---- SEND ----
        send_ts(API_KEY_A, avgA, "A")
        send_ts(API_KEY_B, avgB, "B")

        gc.collect()
        time.sleep(SEND_INTERVAL)

    except Exception as e:
        print("ERROR:", e)
        time.sleep(5)


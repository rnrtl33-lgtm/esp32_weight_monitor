# =====================================================
# ESP32 DUAL WEIGHT SYSTEM
# AUTO OTA FROM GITHUB + AUTO RESET
# =====================================================

import time, gc, machine
import network, urequests
from lib.hx711 import HX711

# ================= WIFI =================
SSID = "stc_wifi_8105"
PASSWORD = "bfw6qrn7tu3"

def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        wlan.connect(SSID, PASSWORD)
        for _ in range(20):
            if wlan.isconnected():
                break
            time.sleep(1)
    return wlan.isconnected()

connect_wifi()

# ================= OTA =================
# رابط raw لملف main.py في GitHub
OTA_URL = "https://raw.githubusercontent.com/rnrt33-lgtm/esp32_weight_monitor/main/main.py"
VERSION = "v1.0"   # غيّرها يدويًا عند أي تعديل

def ota_check():
    try:
        r = urequests.get(OTA_URL)
        code = r.text
        r.close()

        if VERSION not in code:
            print("NEW VERSION FOUND → UPDATING")
            with open("main.py", "w") as f:
                f.write(code)
            time.sleep(2)
            machine.reset()
        else:
            print("OTA: NO UPDATE")

    except Exception as e:
        print("OTA ERROR:", e)

# فحص OTA عند الإقلاع
ota_check()

# ================= THINGSPEAK =================
API_KEY_A = "EU6EE36IJ7WSVYP3"
API_KEY_B = "E8CTAK8MCUWLVQJ2"

def send_ts(api, value):
    url = "https://api.thingspeak.com/update?api_key={}&field4={}".format(
        api, round(value,1)
    )
    try:
        r = urequests.get(url)
        r.close()
    except:
        pass

# ================= HX711 =================
hxA = HX711(dt=34, sck=33)
hxA.offset = 46770.14
hxA.scale  = 410.05076

hxB = HX711(dt=35, sck=32)
hxB.offset = 24163.08
hxB.scale  = 416.56064

# ================= FILTER =================
N = 7
bufA, bufB = [], []
last_A = None
last_B = None
DELTA_G = 5

# ================= TIMING =================
READ_INTERVAL  = 1
SEND_INTERVAL  = 60
RESET_INTERVAL = 6 * 60 * 60   # 6 ساعات

start_time = time.time()
last_send = start_time

print("SYSTEM RUNNING")

# ================= MAIN LOOP =================
while True:
    try:
        wA = (hxA.read() - hxA.offset) / hxA.scale
        wB = (hxB.read() - hxB.offset) / hxB.scale

        bufA.append(wA); bufB.append(wB)
        if len(bufA) > N: bufA.pop(0)
        if len(bufB) > N: bufB.pop(0)

        avgA = sum(bufA) / len(bufA)
        avgB = sum(bufB) / len(bufB)

        now = time.time()

        if now - last_send >= SEND_INTERVAL:
            if last_A is None or abs(avgA - last_A) >= DELTA_G:
                send_ts(API_KEY_A, avgA)
                last_A = avgA

            if last_B is None or abs(avgB - last_B) >= DELTA_G:
                send_ts(API_KEY_B, avgB)
                last_B = avgB

            last_send = now
            gc.collect()

        # -------- AUTO RESET + OTA --------
        if now - start_time >= RESET_INTERVAL:
            print("AUTO RESET FOR OTA CHECK")
            time.sleep(2)
            machine.reset()

    except Exception as e:
        print("ERROR:", e)

    time.sleep(READ_INTERVAL)


import time, gc, machine
import network, urequests
from lib.hx711 import HX711

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
    print("WiFi:", wlan.isconnected())
    return wlan.isconnected()

connect_wifi()

# ================= THINGSPEAK =================
API_KEY_A = "EU6EE36IJ7WSVYP3"
API_KEY_B = "E8CTAK8MCUWLVQJ2"
API_KEY_C = "API_KEY_C"   # ضع مفتاح قناة C

def send_ts(api, value, label):
    try:
        url = "https://api.thingspeak.com/update?api_key={}&field4={}".format(
            api, round(value, 1)
        )
        r = urequests.get(url)
        r.close()
        print("TS SENT", label, "=", round(value,1))
    except Exception as e:
        print("TS ERROR", label, e)

# ================= HX711 =================
# -------- A --------
hxA = HX711(dt=34, sck=33)
hxA.offset = 46770.14
hxA.scale  = 410.05076

# -------- B --------
hxB = HX711(dt=35, sck=32)
hxB.offset = 24163.08
hxB.scale  = 416.56064

# -------- C --------
hxC = HX711(dt=36, sck=25)   # DT عدلناه ليكون آمن
hxC.offset = 12345.67        # كما اعتمدته
hxC.scale  = 775.0

# ================= FILTER =================
N = 7
bufA, bufB, bufC = [], [], []

last_A = last_B = last_C = None
DELTA_G = 5.0

# ================= TIMING =================
READ_INTERVAL   = 2        # قراءة كل ثانيتين (خفيف)
SEND_INTERVAL   = 60       # إرسال كل دقيقة
RESET_INTERVAL  = 6 * 60 * 60   # Reset كل 6 ساعات

last_read = 0
last_send = 0
start_time = time.time()

print("SYSTEM RUNNING")

# ================= MAIN LOOP =================
while True:
    try:
        now = time.time()

        # ---------- READ SENSORS ----------
        if now - last_read >= READ_INTERVAL:
            wA = (hxA.read() - hxA.offset) / hxA.scale
            wB = (hxB.read() - hxB.offset) / hxB.scale
            wC = (hxC.read() - hxC.offset) / hxC.scale

            bufA.append(wA); bufB.append(wB); bufC.append(wC)
            if len(bufA) > N: bufA.pop(0)
            if len(bufB) > N: bufB.pop(0)
            if len(bufC) > N: bufC.pop(0)

            avgA = sum(bufA) / len(bufA)
            avgB = sum(bufB) / len(bufB)
            avgC = sum(bufC) / len(bufC)

            print(
                "A:", round(avgA,1),
                "| B:", round(avgB,1),
                "| C:", round(avgC,1)
            )

            last_read = now

        # ---------- SEND TO THINGSPEAK ----------
        if now - last_send >= SEND_INTERVAL:
            if last_A is None or abs(avgA - last_A) >= DELTA_G:
                send_ts(API_KEY_A, avgA, "A")
                last_A = avgA

            if last_B is None or abs(avgB - last_B) >= DELTA_G:
                send_ts(API_KEY_B, avgB, "B")
                last_B = avgB

            if last_C is None or abs(avgC - last_C) >= DELTA_G:
                send_ts(API_KEY_C, avgC, "C")
                last_C = avgC

            last_send = now
            gc.collect()

        # ---------- AUTO RESET ----------
        if now - start_time >= RESET_INTERVAL:
            print("AUTO RESET (PERIODIC SAFETY)")
            time.sleep(2)
            machine.reset()

    except Exception as e:
        print("FATAL ERROR:", e)
        time.sleep(5)
        machine.reset()

    time.sleep(5) 

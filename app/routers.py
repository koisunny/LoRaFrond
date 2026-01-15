print(">>> routers.py: loading routers module")
import csv
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from datetime import datetime
import requests
import time, json, os


router = APIRouter()
templates = Jinja2Templates(directory="app/views")
# CSV_PATH = "sensor_data/sensor_data.csv"
GSHEET_API = "https://script.google.com/macros/s/AKfycby_p53XC-svWWpZ30JBZARxrcOLPeMKQtKo1p6AIRc6s0_L_3ljpD0_pAIeFzmXFxMg/exec"
FIREBASE_BASE_URL_DIEMDANH = "https://loradiemdanh-default-rtdb.asia-southeast1.firebasedatabase.app"
FIREBASE_BASE_URL_DIEUKHIEN = "https://loracontrol-7f0e1-default-rtdb.asia-southeast1.firebasedatabase.app/"

CACHE_TTL_RAM = 10      # giây
CACHE_TTL_FILE = 60    # giây (sống qua sleep)
CACHE_FILE = "/tmp/sensors_cache.json"

_MEM_CACHE = {
    "ts": 0,
    "data": None
}

def fetch_sheet_data_cached():
    now = time.time()

    # 1️⃣ RAM cache (nhanh nhất)
    if _MEM_CACHE["data"] and now - _MEM_CACHE["ts"] < CACHE_TTL_RAM:
        return _MEM_CACHE["data"]

    # 2️⃣ FILE cache (sau khi Render wake)
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                payload = json.load(f)
                if now - payload["ts"] < CACHE_TTL_FILE:
                    _MEM_CACHE["data"] = payload["data"]
                    _MEM_CACHE["ts"] = payload["ts"]
                    return payload["data"]
        except Exception:
            pass

    # 3️⃣ Gọi Google Sheets (bất đắc dĩ)
    r = requests.get(GSHEET_API, timeout=15)
    r.raise_for_status()
    data = r.json()

    _MEM_CACHE["data"] = data
    _MEM_CACHE["ts"] = now

    try:
        with open(CACHE_FILE, "w") as f:
            json.dump({"ts": now, "data": data}, f)
    except Exception:
        pass

    return data

def safe_float(v):
    try:
        if v is None or v == "":
            return None
        return float(v)
    except:
        return None
def parse_datetime(ts: str) -> datetime:
    try:
        # ISO: 2025-12-06T19:33:09.000Z
        return datetime.fromisoformat(ts.replace("Z", ""))
    except:
        # Sheet thường: 2025-12-20 01:05
        return datetime.strptime(ts, "%Y-%m-%d %H:%M")
@router.get("/")
def start_page(request: Request):
    return templates.TemplateResponse("start.html", {"request": request})

# ... các route khác giữ nguyên


@router.get("/middle")
def middle_page(request: Request):
    return templates.TemplateResponse("middle.html", {"request": request})

@router.get("/function1")
def function1_page(request: Request):
    return templates.TemplateResponse("giamsatmoitruong.html", {"request": request})

@router.get("/thongtintacgia")
def thongtin_page(request: Request):
    return templates.TemplateResponse("thongtintacgia.html", {"request": request})

@router.get("/function2")
def function1_page(request: Request):
    return templates.TemplateResponse("dieukhienthietbi.html", {"request": request})
@router.get("/function3")
def function3_page(request: Request):
    url = f"{FIREBASE_BASE_URL_DIEMDANH}/attendance/22DRTA1.json"

    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json() or {}

    sinh_vien = []

    for ma_sv, info in data.items():
        sinh_vien.append({
            "ma_sv": ma_sv,
            "ten_sv": info.get("ten_sv", ""),
            "trang_thai": info.get("trang_thai", "vang"),
            "timestamp": info.get("timestamp")
        })

    # sort theo tên cho giống SQL cũ
    sinh_vien.sort(key=lambda x: x["ten_sv"])

    return templates.TemplateResponse(
        "diemdanh.html",
        {
            "request": request,
            "sinh_vien": sinh_vien
        }
    )

@router.get("/api/sensors/latest")
def get_latest():
    try:
        rows = fetch_sheet_data_cached()

        # lọc giống CSV cũ
        rows = [r for r in rows if r.get("Temp(C)") not in (None, "", " ")]

        last = rows[-1]

        return {
            "timestamp": last["Timestamp"],
            "temp": safe_float(last["Temp(C)"]),
            "humi": safe_float(last["Humidity(%)"]),
            "press": safe_float(last["Pressure"]),
            "light": safe_float(last["Light(lux)"]),
            "gas": safe_float(last["Gas"]),
            "tempTrend": 0,
            "humiTrend": 0,
            "pressTrend": 0,
            "lightTrend": 0
        }

    except Exception as e:
        return {"error": str(e)}

@router.get("/api/sensors/bootstrap")
def sensors_bootstrap():
    try:
        rows = fetch_sheet_data_cached()

        rows = [r for r in rows if r.get("Temp(C)") not in (None, "", " ")]

        rows.sort(key=lambda r: parse_datetime(r["Timestamp"]))

        last = rows[-1]
        history = rows[-50:]

        # ===== baseline =====
        buckets = {k: [[] for _ in range(24)] for k in ["temp","humid","press","light","gas"]}

        for row in rows:
            ts = str(row.get("Timestamp", "")).strip()
            if not ts:
                continue

            hour = None
            if "T" in ts:
                hour = (int(ts.split("T")[1][:2]) + 7) % 24
            elif " " in ts:
                hour = int(ts.split(" ", 1)[1].split(":")[0])

            if hour is None or not (0 <= hour <= 23):
                continue

            def put(key, col):
                v = safe_float(row.get(col))
                if v is not None:
                    buckets[key][hour].append(v)

            put("temp", "Temp(C)")
            put("humid", "Humidity(%)")
            put("press", "Pressure")
            put("light", "Light(lux)")
            put("gas", "Gas")

        def avg(arr): return sum(arr)/len(arr) if arr else None

        baseline = {
            k: [avg(h) for h in buckets[k]]
            for k in buckets
        }

        return {
            "latest": {
                "timestamp": last["Timestamp"],
                "temp": safe_float(last["Temp(C)"]),
                "humi": safe_float(last["Humidity(%)"]),
                "press": safe_float(last["Pressure"]),
                "light": safe_float(last["Light(lux)"]),
                "gas": safe_float(last["Gas"]),
            },
            "history": history,
            "baseline": baseline
        }

    except Exception as e:
        return {"error": str(e)}

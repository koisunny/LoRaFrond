print(">>> routers.py: loading routers module")
import csv
from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from datetime import datetime
import requests

router = APIRouter()
templates = Jinja2Templates(directory="app/views")
# CSV_PATH = "sensor_data/sensor_data.csv"
GSHEET_API = "https://script.google.com/macros/s/AKfycby_p53XC-svWWpZ30JBZARxrcOLPeMKQtKo1p6AIRc6s0_L_3ljpD0_pAIeFzmXFxMg/exec"
FIREBASE_BASE_URL = "https://loradiemdanh-default-rtdb.asia-southeast1.firebasedatabase.app"

def fetch_sheet_data():
    r = requests.get(GSHEET_API, timeout=15)
    r.raise_for_status()
    return r.json()

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
    url = f"{FIREBASE_BASE_URL}/attendance/22DRTA1.json"

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
        rows = fetch_sheet_data()

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

    
    
@router.get("/api/sensors/history")
def get_history():
    try:
        rows = fetch_sheet_data()

        rows = [r for r in rows if r.get("Temp(C)") not in (None, "", " ")]

        # đảm bảo đúng thứ tự thời gian
        rows.sort(key=lambda r: parse_datetime(r["Timestamp"]))

        return {"data": rows[-50:]}

    except Exception as e:
        return {"error": str(e)}

    
    
    
@router.get("/api/sensors/baseline")
def read_baseline():
    buckets = {
        "temp": [[] for _ in range(24)],
        "humid": [[] for _ in range(24)],
        "press": [[] for _ in range(24)],
        "light": [[] for _ in range(24)],
        "gas": [[] for _ in range(24)],
    }

    rows = fetch_sheet_data()

    for row in rows:
        ts = str(row.get("Timestamp", "")).strip()
        if not ts:
            continue

        hour = None

        # ISO UTC
        if "T" in ts:
            try:
                hour = (int(ts.split("T")[1][:2]) + 7) % 24
            except:
                continue

        # Local
        elif " " in ts:
            try:
                hour = int(ts.split(" ", 1)[1].split(":")[0])
            except:
                continue

        if hour is None or not (0 <= hour <= 23):
            continue

        v = safe_float(row.get("Temp(C)"))
        if v is not None:
            buckets["temp"][hour].append(v)

        v = safe_float(row.get("Humidity(%)"))
        if v is not None:
            buckets["humid"][hour].append(v)

        v = safe_float(row.get("Pressure"))
        if v is not None:
            buckets["press"][hour].append(v)

        v = safe_float(row.get("Light(lux)"))
        if v is not None:
            buckets["light"][hour].append(v)

        v = safe_float(row.get("Gas"))
        if v is not None:
            buckets["gas"][hour].append(v)

    def avg(arr):
        return sum(arr) / len(arr) if arr else None

    return {
        "temp":  [avg(h) for h in buckets["temp"]],
        "humid": [avg(h) for h in buckets["humid"]],
        "press": [avg(h) for h in buckets["press"]],
        "light": [avg(h) for h in buckets["light"]],
        "gas":   [avg(h) for h in buckets["gas"]],
    }

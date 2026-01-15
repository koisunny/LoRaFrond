
def fetch_sheet_data():
    r = requests.get(GSHEET_API, timeout=15)
    r.raise_for_status()
    return r.json()
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

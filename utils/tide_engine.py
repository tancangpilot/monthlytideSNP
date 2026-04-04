import datetime
import pandas as pd
import streamlit as st
from utils.data_processor import process_and_style_df

ROUTE_MAP = {
    "1. P0 VT ➔ Lòng Tàu ➔ Cát Lái": [("HL27", 120), ("HL21", 150), ("HL6", 240)],
    "2. P0 SR ➔ Soài Rạp ➔ TC Hiệp Phước": [("VL", 90), ("TCHP", 180)],
    "1. Cát Lái ➔ Lòng Tàu ➔ P0 VT": [("HL6", 30), ("HL21", 120), ("HL27", 150)],
    "2. Cát Lái ➔ Soài Rạp ➔ P0 SR (Hỗn hợp)": [("BB", 60), ("VL", 150)],
    "3. TC Hiệp Phước ➔ Soài Rạp ➔ P0 SR": [("TCHP", 30), ("VL", 110)]
}

@st.cache_data
def load_all_tide_data(file_path="data_tide.xlsx"):
    tide_db = {}
    month_map = {"january":1, "february":2, "march":3, "april":4, "may":5, "june":6,
                 "july":7, "august":8, "september":9, "october":10, "november":11, "december":12}
    for i in range(1, 13):
        month_map[str(i)] = i; month_map[f"tháng {i}"] = i; month_map[f"thang {i}"] = i
        month_map[f"tháng{i}"] = i; month_map[f"thang{i}"] = i; month_map[f"{i}.0"] = i

    try:
        xl = pd.ExcelFile(file_path)
        today = pd.Timestamp.today().normalize()
        year = today.year
        for sheet in xl.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet, header=None)
            point_data = {}
            current_month = today.month
            day_count = 0
            for idx, row in df.iterrows():
                c0, c1 = str(row[0]).strip().lower(), str(row[1]).strip().lower()
                if c0 in month_map: current_month = month_map[c0]; day_count = 0
                is_day = False
                try: day_count = int(float(c1)); is_day = True
                except: pass
                if is_day: pass
                elif c1 in ["cn", "t2", "t3", "t4", "t5", "t6", "t7"]: day_count += 1
                else: continue
                try:
                    dt = datetime.date(year, current_month, day_count)
                    tides = [pd.to_numeric(row[h+2], errors='coerce') if (h+2) < len(row) else float('nan') for h in range(24)]
                    point_data[dt] = tides
                except: continue
            tide_db[sheet] = point_data
        return tide_db
    except Exception as e: return None

def get_window_cl_for_date(target_date, file_path="data_window.xlsx"):
    try:
        df = pd.read_excel(file_path, sheet_name="WindowCL")
        raw_dates = pd.to_datetime(df['Date'], errors='coerce')
        is_valid = raw_dates.apply(lambda x: pd.notna(x) and x.year > 2000)
        _actual_date = raw_dates.where(is_valid).bfill(limit=1).ffill()
        df_filtered = df[(_actual_date.dt.date == target_date)].copy()
        if df_filtered.empty: return None
        return process_and_style_df(df_filtered, show_past_dates=True)
    except: return None

def get_tide_at_eta(tide_db, point, eta_dt):
    if not tide_db or point not in tide_db: return None
    d = eta_dt.date()
    if d not in tide_db[point]: return None
    tides = tide_db[point][d]
    h1, m = eta_dt.hour, eta_dt.minute
    v1 = tides[h1]
    if m == 0: return v1 
    if h1 < 23: v2 = tides[h1+1]
    else:
        next_d = d + datetime.timedelta(days=1)
        v2 = tide_db[point][next_d][0] if next_d in tide_db[point] else v1 
    if pd.isna(v1) or pd.isna(v2): return v1 
    return v1 + (v2 - v1) * (m / 60.0)

# --- THUẬT TOÁN OPTION 1 ---
def calculate_opt1_safety(route_sel, pob_date, pob_time, draft, config, tide_db):
    waypoints = ROUTE_MAP.get(route_sel, [])
    pob_dt = datetime.datetime.combine(pob_date, pob_time)
    results = []
    is_safe = True
    min_max_draft = 99.9
    bottleneck = ""
    
    for pt, transit_mins in waypoints:
        eta = pob_dt + datetime.timedelta(minutes=transit_mins)
        tide = get_tide_at_eta(tide_db, pt, eta)
        depth = float(config.get(pt.lower(), 0))
        pt_display = f"{pt} (-{depth}m)"
        
        if tide is None or pd.isna(tide):
            results.append({"Điểm cạn": pt_display, "ETA": eta.strftime("%H:%M"), "Thủy triều": "N/A", "UKC": "N/A", "Max Draft": "N/A", "Kết quả": "⚠️ Lỗi"})
            is_safe = False; continue
            
        ukc_pct = config["ukc_day"] if 6 <= eta.hour <= 17 else config["ukc_night"]
        max_d = (tide + depth) / (1 + ukc_pct / 100.0)
        
        if max_d < min_max_draft: min_max_draft = max_d; bottleneck = pt
        status = "✅ PASS" if draft <= max_d else "❌ FAIL"
        if draft > max_d: is_safe = False
            
        results.append({"Điểm cạn": pt_display, "ETA": eta.strftime("%H:%M %d/%m"), "Thủy triều": f"{tide:.1f} m", "UKC": f"{ukc_pct}%", "Max Draft": f"{max_d:.1f} m", "Kết quả": status})
    return results, is_safe, min_max_draft, bottleneck

# --- THUẬT TOÁN OPTION 2 ---
def calculate_opt2_safe_times(route_sel, pob_date, draft, config, tide_db):
    waypoints = ROUTE_MAP.get(route_sel, [])
    safe_times_detail = []
    
    for h in range(24):
        for m in [0, 30]:
            test_time = datetime.time(h, m)
            test_dt = datetime.datetime.combine(pob_date, test_time)
            is_safe = True
            min_max_draft = 99.9
            point_drafts = {}
            for pt, transit_mins in waypoints:
                eta = test_dt + datetime.timedelta(minutes=transit_mins)
                tide = get_tide_at_eta(tide_db, pt, eta)
                if tide is None or pd.isna(tide): is_safe = False; break
                depth = float(config.get(pt.lower(), 0))
                ukc_pct = config["ukc_day"] if 6 <= eta.hour <= 17 else config["ukc_night"]
                max_d = (tide + depth) / (1 + ukc_pct / 100.0)
                point_drafts[pt] = max_d
                if max_d < min_max_draft: min_max_draft = max_d
                if draft > max_d: is_safe = False; break
            if is_safe: 
                safe_times_detail.append({"time": test_time, "point_drafts": point_drafts, "min_max_draft": min_max_draft})
    return safe_times_detail

# --- HÀM MỚI TÍCH HỢP CHO OPTION 2: LẤY 3 MAX VÀ 3 MIN DRAFT TRONG NGÀY ---
def get_day_draft_extrema(route_sel, pob_date, config, tide_db):
    waypoints = ROUTE_MAP.get(route_sel, [])
    all_drafts = set()

    for h in range(24):
        for m in [0, 30]:
            test_dt = datetime.datetime.combine(pob_date, datetime.time(h, m))
            min_max_draft = 99.9
            is_valid = True
            for pt, transit_mins in waypoints:
                eta = test_dt + datetime.timedelta(minutes=transit_mins)
                tide = get_tide_at_eta(tide_db, pt, eta)
                if tide is None or pd.isna(tide):
                    is_valid = False; break
                depth = float(config.get(pt.lower(), 0))
                u = config["ukc_day"] if 6 <= eta.hour <= 17 else config["ukc_night"]
                max_d = (tide + depth) / (1 + u / 100.0)
                if max_d < min_max_draft: min_max_draft = max_d
            if is_valid and min_max_draft != 99.9:
                all_drafts.add(round(min_max_draft, 1))

    sorted_drafts = sorted(list(all_drafts))
    if not sorted_drafts: return [], []

    min_3 = sorted_drafts[:3]
    max_3 = sorted(sorted_drafts[-3:], reverse=True) # Lấy 3 mớn lớn nhất, xếp giảm dần
    return max_3, min_3
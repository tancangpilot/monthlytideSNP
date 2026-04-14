import datetime
import pandas as pd
import streamlit as st
from utils.data_processor import process_and_style_df

VN_TZ = datetime.timezone(datetime.timedelta(hours=7))

ROUTE_MAP = {
    "1. P0 VT ➔ Lòng Tàu ➔ Cát Lái": [("HL27", 120), ("HL21", 150), ("HL6", 240)],
    "2. P0 SR ➔ Soài Rạp ➔ TC Hiệp Phước": [("VL", 90), ("TCHP", 180)],
    "1. Cát Lái ➔ Lòng Tàu ➔ P0 VT": [("HL6", 30), ("HL21", 120), ("HL27", 150)],
    "2. Cát Lái ➔ Soài Rạp ➔ P0 SR (Hỗn hợp)": [("BB", 60), ("VL", 150)],
    # ĐÃ SỬA: Trạm VL 90 phút
    "3. TC Hiệp Phước ➔ Soài Rạp ➔ P0 SR": [("TCHP", 30), ("VL", 90)]
}

@st.cache_data(show_spinner=False)
def load_all_tide_data(file_path="data_tide.xlsx"):
    tide_db = {}
    month_map = {"january":1, "february":2, "march":3, "april":4, "may":5, "june":6, "july":7, "august":8, "september":9, "october":10, "november":11, "december":12}
    for i in range(1, 13):
        month_map[str(i)] = i
        month_map[f"tháng {i}"] = i
        month_map[f"thang {i}"] = i
        month_map[f"tháng{i}"] = i
        month_map[f"thang{i}"] = i
        month_map[f"{i}.0"] = i

    try:
        xl = pd.ExcelFile(file_path)
        today = datetime.datetime.now(VN_TZ).date()
        year = today.year
        for sheet in xl.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet, header=None)
            point_data = {}
            current_month = today.month
      
            day_count = 0
            for idx, row in df.iterrows():
                c0, c1 = str(row[0]).strip().lower(), str(row[1]).strip().lower()
                if c0 in month_map: 
                    current_month = month_map[c0]
                
                day_count = 0
                is_day = False
                try: 
                    day_count = int(float(c1))
                    is_day = True
                except Exception: 
                    pass
                    
                if is_day: 
                    pass
                elif c1 in ["cn", "t2", "t3", "t4", "t5", "t6", "t7"]: 
                    day_count += 1
                else: 
                    continue
                    
                try:
                    dt = datetime.date(year, current_month, day_count)
                    tides = [pd.to_numeric(row[h+2], errors='coerce') if (h+2) < len(row) else float('nan') for h in range(24)]
                    point_data[dt] = tides
                except Exception: 
                    continue
      
            tide_db[sheet] = point_data
        return tide_db
    except Exception as e: 
        return None

@st.cache_data(show_spinner=False)
def load_raw_window(file_path="data_window.xlsx"):
    try:
        df = pd.read_excel(file_path, sheet_name="WindowCL")
        df.columns = [str(c).strip() for c in df.columns] 
        raw_dates = pd.to_datetime(df['Date'], errors='coerce')
        is_valid = raw_dates.apply(lambda x: pd.notna(x) and x.year > 2000)
        df['_actual_date'] = raw_dates.where(is_valid).bfill(limit=1).ffill().dt.date
      
        return df
    except Exception: 
        return None

def get_window_cl_for_date(target_date, file_path="data_window.xlsx"):
    try:
        df = load_raw_window(file_path)
        if df is None: return None
        df_filtered = df[(df['_actual_date'] == target_date)].copy()
        if df_filtered.empty: return None
        return process_and_style_df(df_filtered, show_past_dates=True)
    except Exception: 
        return None

def get_tide_at_eta(tide_db, point, eta_dt):
    if not tide_db or point not in tide_db: return None
    d = eta_dt.date()
 
    if d not in tide_db[point]: return None
    tides = tide_db[point][d]
    h1, m = eta_dt.hour, eta_dt.minute
    v1 = tides[h1]
    if m == 0: return v1 
    if h1 < 23: 
        v2 = tides[h1+1]
    else:
        next_d = d + datetime.timedelta(days=1)
        v2 = tide_db[point][next_d][0] if next_d in tide_db[point] else v1 
        
    if pd.isna(v1) or pd.isna(v2): return v1 
    return v1 + (v2 - v1) * (m / 60.0)

def check_current_condition(pob_dt, direction, raw_win_df):
    if raw_win_df is None or raw_win_df.empty: return False
    try:
        pob_date = pob_dt.date()
        dates_to_check = [pob_date - datetime.timedelta(days=1), pob_date, pob_date + datetime.timedelta(days=1)]
        df_check = raw_win_df[raw_win_df['_actual_date'].isin(dates_to_check)].copy()
        if df_check.empty: return False

        def parse_time(v):
            if isinstance(v, datetime.time): return v
     
            s = str(v).strip()
            if s.startswith("24:"): return datetime.time(23, 59, 59)
            if len(s) >= 4 and ":" in s: return datetime.time(int(s.split(":")[0]), int(s.split(":")[1][:2]))
            raise ValueError

        if "Inbound" in direction:
            vt_data = []
            vt_col = next((c for c in df_check.columns if "vung" in str(c).lower().replace(" ", "")), None)
            lvl_col = next((c for c in df_check.columns if "level" in str(c).lower()), None)
            if not vt_col or not lvl_col: return False

            for idx, row in df_check.iterrows():
                vt_time, lvl = row.get(vt_col), row.get(lvl_col)
           
                if pd.notna(vt_time) and pd.notna(lvl):
                    try: 
                        vt_data.append({'dt': datetime.datetime.combine(row['_actual_date'], parse_time(vt_time)), 'level': float(lvl)})
                    except Exception: 
                        pass
            vt_data.sort(key=lambda x: x['dt'])
            for i in range(len(vt_data)):
                vt_dt = vt_data[i]['dt']
                if vt_dt - datetime.timedelta(hours=2) <= pob_dt <= vt_dt + datetime.timedelta(minutes=30): return True
                if i < len(vt_data) - 1:
                    if abs(vt_data[i]['level'] - vt_data[i+1]['level']) <= 1.0:
                        if vt_dt <= pob_dt <= vt_data[i+1]['dt']: return True
            return False
        else:
            b_cols = [c for c in df_check.columns if "begin" in str(c).lower() and "ub" in str(c).lower()]
            e_cols = [c for c in df_check.columns if "end" in str(c).lower() and "ub" in str(c).lower()]
            vt_col = next((c for c in df_check.columns if "vung" in str(c).lower().replace(" ", "")), None)

            for idx, row in df_check.iterrows():
                times = []
                for c in b_cols + e_cols:
                    v = row.get(c)
                    
                    if pd.notna(v) and str(v).strip() not in ["", "nan"]:
                        try: times.append(parse_time(v))
                        except Exception: pass

                is_evening_tide = False
                vt_val = row.get(vt_col) if vt_col else None
   
                if pd.notna(vt_val) and str(vt_val).strip() not in ["", "nan"]:
                    try:
                        vt_t = parse_time(vt_val)
                        if vt_t.hour >= 12: is_evening_tide = True
    
                    except Exception: pass
                else:
                    if any(t.hour >= 16 for t in times): is_evening_tide = True

                b_dts = []
                for c in b_cols:
                    v = row.get(c)
                    if pd.notna(v) and str(v).strip() not in ["", "nan"]:
                        try:
                            t = parse_time(v)
                            dt = datetime.datetime.combine(row['_actual_date'], t)
                            if is_evening_tide and t.hour < 12: dt += datetime.timedelta(days=1)
                            b_dts.append(dt)
                        except Exception: pass

                e_dts = []
                for c in e_cols:
                    v = row.get(c)
                  
                    if pd.notna(v) and str(v).strip() not in ["", "nan"]:
                        try:
                            t = parse_time(v)
                            dt = datetime.datetime.combine(row['_actual_date'], t)
      
                            if is_evening_tide and t.hour < 12: dt += datetime.timedelta(days=1)
                            e_dts.append(dt)
                        except Exception: pass

                if b_dts and e_dts:
                    min_b_dt = min(b_dts)
                    max_e_dt = max(e_dts)
                    if max_e_dt < min_b_dt: max_e_dt += datetime.timedelta(days=1)
                    if min_b_dt <= pob_dt <= max_e_dt: return True
 
            return False
    except Exception: return False

def calculate_opt1_safety(route_sel, pob_date, pob_time, draft, config, tide_db):
    waypoints = ROUTE_MAP.get(route_sel, [])
    pob_dt = datetime.datetime.combine(pob_date, pob_time)
    results, is_safe, min_max_draft, bottleneck = [], True, 99.9, ""
    for pt, transit_mins in waypoints:
        eta = pob_dt + datetime.timedelta(minutes=transit_mins)
        tide = get_tide_at_eta(tide_db, pt, eta)
        depth = float(config.get(pt.lower(), 0))
       
        pt_display = f"{pt} (-{depth}m)"
        if tide is None or pd.isna(tide):
            results.append({"Điểm cạn": pt_display, "ETA": eta.strftime("%H:%M"), "Thủy triều": "N/A", "UKC": "N/A", "Max Draft": "N/A", "Kết quả": "⚠️ Lỗi"})
            is_safe = False
            continue
            
        # Luật Ngày/Đêm: Đúng 05:00 là Đêm (10%), từ 05:01 là Ngày (7%)
        is_day = (6 <= eta.hour <= 17) or (eta.hour == 5 and eta.minute > 0)
        ukc_pct = config["ukc_day"] if is_day else config["ukc_night"]
        
        max_d = (tide + depth) / (1 + ukc_pct / 100.0)
        if max_d < min_max_draft: 
            min_max_draft, bottleneck = max_d, pt
        status = "✅ PASS" if draft <= max_d else "❌ FAIL"
        if draft > max_d: is_safe = False
        results.append({"Điểm cạn": pt_display, "ETA": eta.strftime("%H:%M %d/%m"), "Thủy triều": f"{tide:.1f} m", "UKC": f"{ukc_pct}%", "Max Draft": f"{max_d:.1f} m", "Kết quả": status})
    return results, is_safe, min_max_draft, bottleneck

def calculate_opt2_safe_times(route_sel, pob_date, draft, config, tide_db, direction):
    waypoints = ROUTE_MAP.get(route_sel, [])
    safe_times_detail = []
    raw_win_df = load_raw_window()
    now = datetime.datetime.now(VN_TZ)
    today = now.date()
    start_h = now.hour if pob_date == today else 0
    start_m = (0 if now.minute < 30 else 30) if pob_date == today else 0
    
    for h in range(24):
        for m in [0, 30]:
         
            if pob_date == today and (h < start_h or (h == start_h and m < start_m)): continue
            test_dt = datetime.datetime.combine(pob_date, datetime.time(h, m))
            is_safe, min_max_draft, point_drafts = True, 99.9, {}
            for pt, transit_mins in waypoints:
                eta = test_dt + datetime.timedelta(minutes=transit_mins)
           
                tide = get_tide_at_eta(tide_db, pt, eta)
                if tide is None or pd.isna(tide): 
                    is_safe = False
                    break
                depth = float(config.get(pt.lower(), 0))
                
                is_day = (6 <= eta.hour <= 17) or (eta.hour == 5 and eta.minute > 0)
                ukc_pct = config["ukc_day"] if is_day else config["ukc_night"]
                
                max_d = (tide + depth) / (1 + ukc_pct / 100.0)
                point_drafts[pt] = max_d
           
                if max_d < min_max_draft: min_max_draft = max_d
                if draft > max_d: 
                    is_safe = False
                    break
            if is_safe: 
                c_safe = check_current_condition(test_dt, direction, raw_win_df)
                safe_times_detail.append({"time": test_dt.time(), "point_drafts": point_drafts, "min_max_draft": min_max_draft, "current_safe": c_safe})
    return safe_times_detail

def get_day_draft_extrema(route_sel, pob_date, config, tide_db):
    waypoints = ROUTE_MAP.get(route_sel, [])
    all_drafts = set()
    for h in range(24):
        for m in [0, 30]:
  
            test_dt = datetime.datetime.combine(pob_date, datetime.time(h, m))
            min_max_draft, is_valid = 99.9, True
            for pt, transit_mins in waypoints:
                eta = test_dt + datetime.timedelta(minutes=transit_mins)
                tide = get_tide_at_eta(tide_db, pt, eta)
              
                if tide is None or pd.isna(tide): 
                    is_valid = False
                    break
                depth = float(config.get(pt.lower(), 0))
                
                is_day = (6 <= eta.hour <= 17) or (eta.hour == 5 and eta.minute > 0)
                u = config["ukc_day"] if is_day else config["ukc_night"]
                
                max_d = (tide + depth) / (1 + u / 100.0)
                if max_d < min_max_draft: min_max_draft = max_d
       
            if is_valid and min_max_draft != 99.9: all_drafts.add(round(min_max_draft, 1))
    sorted_drafts = sorted(list(all_drafts))
    if not sorted_drafts: return [], []
    return sorted(sorted_drafts[-3:], reverse=True), sorted_drafts[:3]
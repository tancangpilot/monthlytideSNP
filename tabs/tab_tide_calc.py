import streamlit as st
import datetime
import pandas as pd

# --- HÀM LOAD DỮ LIỆU THỦY TRIỀU (Lưu Cache để chạy siêu tốc) ---
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
                if c0 in month_map:
                    current_month = month_map[c0]
                    day_count = 0

                is_day = False
                try:
                    day_count = int(float(c1))
                    is_day = True
                except: pass

                if is_day: pass
                elif c1 in ["cn", "t2", "t3", "t4", "t5", "t6", "t7"]: day_count += 1
                else: continue

                try:
                    dt = datetime.date(year, current_month, day_count)
                    tides = []
                    for h in range(24):
                        val = pd.to_numeric(row[h+2], errors='coerce') if (h+2) < len(row) else float('nan')
                        tides.append(val)
                    point_data[dt] = tides
                except: continue
            tide_db[sheet] = point_data
        return tide_db
    except Exception as e:
        return None

# --- HÀM NỘI SUY MỰC NƯỚC THEO GIỜ PHÚT ---
def get_tide_at_eta(tide_db, point, eta_dt):
    if not tide_db or point not in tide_db: return None
    d = eta_dt.date()
    if d not in tide_db[point]: return None

    tides = tide_db[point][d]
    h1 = eta_dt.hour
    m = eta_dt.minute
    v1 = tides[h1]

    if m == 0: return v1 

    if h1 < 23:
        v2 = tides[h1+1]
    else:
        next_d = d + datetime.timedelta(days=1)
        if next_d in tide_db[point]: v2 = tide_db[point][next_d][0]
        else: v2 = v1 

    if pd.isna(v1) or pd.isna(v2): return v1 
    return v1 + (v2 - v1) * (m / 60.0)

# --- TỪ ĐIỂN ĐỊNH TUYẾN & TRANSIT TIME (PHÚT) ---
ROUTE_MAP = {
    "1. P0 VT ➔ Lòng Tàu ➔ Cát Lái": [("HL27", 120), ("HL21", 150), ("HL6", 240)],
    "2. P0 SR ➔ Soài Rạp ➔ TC Hiệp Phước": [("VL", 90), ("TCHP", 180)],
    "1. Cát Lái ➔ Lòng Tàu ➔ P0 VT": [("HL6", 30), ("HL21", 120), ("HL27", 150)],
    "2. Cát Lái ➔ Soài Rạp ➔ P0 SR (Hỗn hợp)": [("BB", 60), ("VL", 150)],
    "3. TC Hiệp Phước ➔ Soài Rạp ➔ P0 SR": [("TCHP", 30), ("VL", 110)]
}

# --- HÀM TIỆN ÍCH LÀM TRÒN 30 PHÚT ---
def get_rounded_time():
    now = datetime.datetime.now()
    minutes = (now.minute // 30 + (1 if now.minute % 30 >= 15 else 0)) * 30
    rounded_dt = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(minutes=minutes)
    return rounded_dt.time()


# ==========================================
# GIAO DIỆN CHÍNH CỦA TAB TIDE CALC
# ==========================================
def render_tide_calc_tab(route_sel):
    config = st.session_state.config
    
    st.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 14px; color: #888;'>Tuyến đang chọn:</span> <span style='font-size: 22px; font-weight: bold; color: #1E90FF; margin-left: 10px;'>{route_sel}</span></div>", unsafe_allow_html=True)
    
    calc_options = [
        "Opt1: Kiểm tra AN TOÀN (Nhập POB và Draft)",
        "Opt2: Tìm giờ POB (Nhập POB Date & Draft)",
        "Opt3: Tìm giờ POB và Max draft (Chỉ nhập POB Date)"
    ]
    
    selected_opt = st.radio("Chọn bài toán:", calc_options, label_visibility="collapsed")
    
    default_date = datetime.date.today()
    default_time = get_rounded_time()
    default_draft = 10.5

    with st.container(border=True):
        
        # ----------------------------------------------------
        # BÀI TOÁN 1: KIỂM TRA AN TOÀN TOÀN CHUYẾN
        # ----------------------------------------------------
        if selected_opt == calc_options[0]:
            c1, c2, c3 = st.columns(3)
            with c1: pob_date = st.date_input("POB Date", default_date)
            with c2: pob_time = st.time_input("POB Time", default_time)
            with c3: draft = st.number_input("Draft (m)", min_value=0.0, value=default_draft, step=0.1)
            
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                tide_db = load_all_tide_data("data_tide.xlsx")
                if not tide_db:
                    st.error("Lỗi: Không đọc được file data_tide.xlsx")
                else:
                    waypoints = ROUTE_MAP.get(route_sel, [])
                    pob_dt = datetime.datetime.combine(pob_date, pob_time)
                    
                    results = []
                    is_safe_trip = True
                    min_max_draft = 99.9
                    bottleneck_point = ""
                    
                    for pt, transit_mins in waypoints:
                        eta = pob_dt + datetime.timedelta(minutes=transit_mins)
                        tide = get_tide_at_eta(tide_db, pt, eta)
                        depth = float(config.get(pt.lower(), 0))
                        
                        # Gắn thêm độ sâu vào tên điểm cạn
                        pt_display = f"{pt} (-{depth}m)"
                        
                        if tide is None or pd.isna(tide):
                            results.append({"Điểm cạn": pt_display, "ETA": eta.strftime("%H:%M"), "Thủy triều": "N/A", "UKC": "N/A", "Max Draft": "N/A", "Kết quả": "⚠️ Lỗi Data"})
                            is_safe_trip = False
                            continue
                            
                        ukc_pct = config["ukc_day"] if 6 <= eta.hour <= 17 else config["ukc_night"]
                        max_d = (tide + depth) / (1 + ukc_pct / 100.0)
                        
                        if max_d < min_max_draft:
                            min_max_draft = max_d
                            bottleneck_point = pt
                            
                        if draft <= max_d:
                            status = "✅ PASS"
                        else:
                            status = "❌ FAIL"
                            is_safe_trip = False
                            
                        results.append({
                            "Điểm cạn": pt_display,
                            "ETA": eta.strftime("%H:%M %d/%m"),
                            "Thủy triều": f"{tide:.1f} m", # Làm tròn 1 chữ số thập phân
                            "UKC": f"{ukc_pct}%",
                            "Max Draft": f"{max_d:.1f} m", # Làm tròn 1 chữ số thập phân
                            "Kết quả": status
                        })
                    
                    # In Kết quả Tổng quan gọn gàng
                    st.markdown("---")
                    if is_safe_trip:
                        st.success(f"🟢 **ĐỦ NƯỚC** (Max draft nhỏ nhất đạt {min_max_draft:.1f}m tại {bottleneck_point})")
                    else:
                        st.error(f"🔴 **KHÔNG ĐỦ NƯỚC tại {bottleneck_point}** (Max draft chỉ đạt {min_max_draft:.1f}m)")
                    
                    # In Bảng Chi Tiết
                    df_res = pd.DataFrame(results)
                    st.dataframe(df_res, use_container_width=True, hide_index=True)

        # ----------------------------------------------------
        # BÀI TOÁN 2: TÌM GIỜ POB
        # ----------------------------------------------------
        elif selected_opt == calc_options[1]:
            c1, c2 = st.columns(2)
            with c1: pob_date = st.date_input("POB Date", default_date)
            with c2: draft = st.number_input("Draft (m)", min_value=0.0, value=default_draft, step=0.1)
            
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                st.info("Chức năng Tìm Giờ POB đang được xây dựng (Thuật toán quét lặp).")
                
        # ----------------------------------------------------
        # BÀI TOÁN 3: TÌM MAX DRAFT
        # ----------------------------------------------------
        elif selected_opt == calc_options[2]:
            pob_date = st.date_input("POB Date", default_date)
            
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                st.info("Chức năng Tìm Giờ POB cho Max Draft đang được xây dựng.")

    st.markdown("<br>", unsafe_allow_html=True)
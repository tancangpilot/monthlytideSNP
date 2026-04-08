import streamlit as st
import pandas as pd
import datetime
from utils.tide_engine import load_all_tide_data, ROUTE_MAP, get_tide_at_eta, VN_TZ

def render_pob_print_tab():
    config = st.session_state.config
    db = load_all_tide_data()
    
    if not db:
        st.error("❌ Không tìm thấy dữ liệu thủy triều"); return

    # --- KHU VỰC TÙY CHỌN CHUNG ---
    col_opt1, col_opt2 = st.columns(2)
    with col_opt1:
        show_30 = st.checkbox("⏱️ Hiển thị mốc 30 phút", value=True)
    with col_opt2:
        print_mode = st.toggle("🖨️ BẬT CHẾ ĐỘ IN PDF (Ép ngang A4 & Chống cắt trang)", value=False)

    st.markdown("<hr style='margin: 5px 0 15px 0;'>", unsafe_allow_html=True)

    # --- HÀNG 1: HƯỚNG & TUYẾN ---
    c1, c2 = st.columns([1, 2])
    with c1:
        direction = st.selectbox("Hướng", ["⬆️ Outbound (Đi ra)", "⬇️ Inbound (Đi vào)"], label_visibility="collapsed")
    with c2:
        routes = ["1. Cát Lái ➔ Lòng Tàu ➔ P0 VT", "2. Cát Lái ➔ Soài Rạp ➔ P0 SR (Hỗn hợp)", "3. TC Hiệp Phước ➔ Soài Rạp ➔ P0 SR"] if "Outbound" in direction else ["1. P0 VT ➔ Lòng Tàu ➔ Cát Lái", "2. P0 SR ➔ Soài Rạp ➔ TC Hiệp Phước"]
        route_sel = st.selectbox("Tuyến", routes, label_visibility="collapsed")

    # --- HÀNG 2: THỜI GIAN ---
    c3, c4, c5 = st.columns([1, 1, 1])
    today = datetime.datetime.now(VN_TZ).date()
    with c3:
        month_sel = st.selectbox("Tháng", [f"Tháng {i}" for i in range(1, 13)], index=today.month-1, label_visibility="collapsed")
    with c4:
        from_date = st.date_input("Từ", today, format="DD/MM/YYYY", label_visibility="collapsed")
    with c5:
        last_day = (today.replace(day=28) + datetime.timedelta(days=4)).replace(day=1) - datetime.timedelta(days=1)
        to_date = st.date_input("Đến", last_day, format="DD/MM/YYYY", label_visibility="collapsed")

    # --- DÒNG TIÊU ĐỀ: COLOR HÓA & GHI CHÚ ---
    dir_label = "ĐI RA" if "Outbound" in direction else "ĐI VÀO"
    wpts = ROUTE_MAP.get(route_sel, [])
    
    def fmt_time(m):
        if m < 60: return f"{m}'"
        h = m // 60
        rem = m % 60
        if rem == 0: return f"{h}h'"
        return f"{h}h{rem}'"

    pts_styled = []
    for pt, m in wpts:
        t_str = fmt_time(m)
        pts_styled.append(f"<span style='color: #1E90FF; font-weight: bold;'>{pt}</span>: <span style='color: #d93025; font-weight: bold;'>{t_str}</span>")

    pts_info = " - ".join(pts_styled)
    route_html = f"<span style='color: #1E90FF; font-weight: bold;'>{route_sel}</span>"
    
    hide_box = "display: none;" if print_mode else ""
    st.markdown(f"""
        <div style='background-color: #f8f9fa; padding: 12px 15px; border-radius: 5px; border-left: 5px solid #1E90FF; margin-top: 5px; margin-bottom: 15px; {hide_box}'>
            <div style='font-size: 16px; margin-bottom: 5px;'><b>{dir_label}:</b> {route_html} ({pts_info}).</div>
            <div style='font-size: 14px; color: #555;'><i>* <b>Cột GIỜ</b> là giờ POB với các điểm cạn đã được hiệu chỉnh ETA.</i></div>
        </div>
    """, unsafe_allow_html=True)

    # --- LOGIC TÍNH TOÁN DỮ LIỆU ---
    pob_slots = [f"{h:02d}:{m:02d}" for h in range(24) for m in ([0, 30] if show_30 else [0])]
    all_days_data = []
    
    curr_d = from_date
    while curr_d <= to_date:
        day_rows = []
        for pt, transit in wpts:
            depth = float(config.get(pt.lower(), 0))
            row = {"Date": curr_d.strftime("%d/%m"), "Point": pt}
            for slot in pob_slots:
                h, m = map(int, slot.split(':'))
                pob_dt = datetime.datetime.combine(curr_d, datetime.time(h, m))
                eta = pob_dt + datetime.timedelta(minutes=transit)
                tide = get_tide_at_eta(db, pt, eta)
                if tide is not None:
                    u = config["ukc_day"] if 6 <= eta.hour <= 17 else config["ukc_night"]
                    row[slot] = f"{(tide + depth) / (1 + u / 100.0):.1f}"
                else: 
                    row[slot] = ""
            day_rows.append(row)

        max_row = {"Date": curr_d.strftime("%d/%m"), "Point": "MAX"}
        for slot in pob_slots:
            vals = [float(r[slot]) for r in day_rows if r[slot] != ""]
            max_row[slot] = f"{min(vals):.1f}" if vals else ""
        day_rows.append(max_row)
        
        all_days_data.append({"date_str": curr_d.strftime("%d/%m"), "rows": day_rows})
        curr_d += datetime.timedelta(days=1)

    if not all_days_data:
        st.warning("Không có dữ liệu trong khoảng thời gian này."); return

    # =====================================================================
    # TẠO BẢNG HTML CHUNG CHO CẢ 2 CHẾ ĐỘ (WEB & PRINT)
    # =====================================================================
    html = ""

    if print_mode:
        # GIAO DIỆN IN ẤN (Siêu nén, mất viền thừa)
        html += f"""
        <style>
        @media print {{
            @page {{ size: A4 landscape; margin: 8mm; }}
            [data-testid="stSidebar"], header, .stSelectbox, .stDateInput, .stCheckbox, .stToggle, .stRadio {{ display: none !important; }}
            .stApp {{ background-color: white !important; }}
        }}
        .custom-table {{ width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; text-align: center; table-layout: fixed; }}
        .custom-table th {{ background-color: #ffe699 !important; border: 1px solid #333; padding: 2px 0px; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        .custom-table td {{ border: 1px solid #555; padding: 3px 0px; font-size: 10.5px; letter-spacing: -0.4px; color: #111; }}
        .tbody-day-group {{ page-break-inside: avoid; border-bottom: 2.5px solid #111; }}
        .max-row {{ background-color: #ffff00 !important; font-weight: bold; color: #d93025 !important; -webkit-print-color-adjust: exact; print-color-adjust: exact; border-top: 1.5px solid #333; }}
        </style>
        <div style='font-size: 15px; margin-bottom: 8px; color: #111; text-align: center;'>
            <b>{dir_label}:</b> {route_html} ({pts_info})
        </div>
        """
    else:
        # GIAO DIỆN WEB (Có khung cuộn, ghim tiêu đề, ghim cột ngang)
        html += f"""
        <style>
        .table-container {{ max-height: 750px; overflow-y: auto; overflow-x: auto; border: 1px solid #ccc; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .custom-table {{ width: 100%; border-collapse: separate; border-spacing: 0; font-family: Arial, sans-serif; text-align: center; }}
        .custom-table th {{ background-color: #ffe699; border-right: 1px solid #ccc; border-bottom: 2px solid #555; padding: 6px 2px; position: sticky; top: 0; z-index: 2; color: #111; }}
        .custom-table td {{ border-right: 1px solid #ddd; border-bottom: 1px solid #ddd; padding: 6px 2px; font-size: 15px; color: #333; }}
        
        /* Cố định cột Date (50px) và Point (65px) bên trái */
        .custom-table th:nth-child(1), .custom-table td:nth-child(1) {{ position: sticky; left: 0; z-index: 3; background-color: #f8f9fa; border-right: 1px solid #aaa; width: 50px; min-width: 50px; max-width: 50px; }}
        .custom-table th:nth-child(2), .custom-table td:nth-child(2) {{ position: sticky; left: 50px; z-index: 3; background-color: #f8f9fa; border-right: 2px solid #555; width: 65px; min-width: 65px; max-width: 65px; font-weight: bold; }}
        
        /* Góc giao nhau trên cùng bên trái phải luôn nằm trên cùng */
        .custom-table th:nth-child(1), .custom-table th:nth-child(2) {{ z-index: 4; background-color: #ffe699; }}
        
        .tbody-day-group {{ border-bottom: 3px solid #444; }}
        .max-row td {{ background-color: #ffff00 !important; font-weight: bold; color: #d93025 !important; border-top: 2px solid #555; }}
        
        /* Hiệu ứng rê chuột sáng dòng */
        .custom-table tbody tr:hover td {{ background-color: #e6f7ff; }}
        .custom-table tbody tr.max-row:hover td {{ background-color: #ffee00 !important; }}
        </style>
        <div class='table-container'>
        """
    
    # Bắt đầu vẽ cấu trúc bảng
    html += "<table class='custom-table'><thead><tr>"
    
    # Tiêu đề cột Date & Point
    if print_mode:
        html += "<th style='width: 32px; font-size:11px;'>Date</th><th style='width: 42px; font-size:11px;'>Point</th>"
    else:
        html += "<th>Date</th><th>Point</th>"

    # LOGIC TẠO TIÊU ĐỀ: 00 to, :30 nhỏ
    for s in pob_slots:
        if s.endswith(":00"):
            sz = "13px" if print_mode else "15px"
            html += f"<th><span style='font-size: {sz}; font-weight: bold; color: #111;'>{s[:2]}</span></th>"
        else:
            sz = "8.5px" if print_mode else "10.5px"
            html += f"<th><span style='font-size: {sz}; font-weight: normal; color: #666;'>:30</span></th>"
            
    html += "</tr></thead>"
    
    # Đổ nội dung bảng
    for day_data in all_days_data:
        html += "<tbody class='tbody-day-group'>"
        for idx, r in enumerate(day_data["rows"]):
            row_cls = " class='max-row'" if r["Point"] == "MAX" else ""
            html += f"<tr{row_cls}>"
            
            # Cột Date (Chỉ hiện dòng đầu của ngày)
            display_date = r['Date'] if idx == 0 else ""
            date_style = " style='font-size:11px;'" if print_mode else " style='font-weight:bold;'"
            html += f"<td{date_style}>{display_date}</td>"
            
            # Cột Point
            pt_style = " style='font-weight:bold; font-size:10.5px;'" if print_mode else ""
            html += f"<td{pt_style}>{r['Point']}</td>"
            
            # Cột Data Mớn nước
            for s in pob_slots:
                html += f"<td>{r[s]}</td>"
            html += "</tr>"
        html += "</tbody>"
        
    html += "</table>"
    if not print_mode: html += "</div>" # Đóng thẻ khung cuộn
    
    st.markdown(html, unsafe_allow_html=True)
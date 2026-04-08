import streamlit as st
import datetime
import pandas as pd
from utils.tide_engine import load_all_tide_data, load_raw_window, check_current_condition, get_window_cl_for_date, calculate_opt1_safety, calculate_opt2_safe_times, get_day_draft_extrema, ROUTE_MAP, VN_TZ

def reset_calc(): st.session_state.tide_calc_run = False

def get_rounded_time():
    now = datetime.datetime.now(VN_TZ)
    minutes = (now.minute // 30 + (1 if now.minute % 30 >= 15 else 0)) * 30
    return (now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(minutes=minutes)).time()

def format_transit_time(mins):
    h, m = divmod(mins, 60)
    if h > 0 and m > 0: return f"+{h}h{m}"
    elif h > 0: return f"+{h}h"
    else: return f"+{m}'"

# Thêm *args, **kwargs để tương thích hoàn hảo nếu app.py lỡ truyền biến vào
def render_tide_calc_tab(*args, **kwargs):
    if "tide_calc_run" not in st.session_state: st.session_state.tide_calc_run = False

    st.markdown("""
        <style>
        [data-testid="stMainBlockContainer"] [data-testid="stVerticalBlock"] { gap: 0.5rem !important; }
        [data-testid="stMainBlockContainer"] div[role="radiogroup"] { gap: 20px !important; }
        .sub-table-header { text-align: center; background-color: #f0f2f6; padding: 4px; border-radius: 5px; margin-bottom: 5px; font-weight: bold; color: #1E90FF; font-size: 14px; border: 1px solid #ddd; }
        [data-testid="stDataFrame"] th > div, [data-testid="stDataFrame"] td > div { padding: 0 4px !important; }
        /* Căn chỉnh checkbox ngang hàng text */
        .stCheckbox { margin-top: 8px; }
        </style>
    """, unsafe_allow_html=True)

    config = st.session_state.config
    
    # ==========================================
    # 1. HƯỚNG VÀ TUYẾN (Nằm ngang hàng inline)
    # ==========================================
    c_lbl1, c_dir, c_lbl2, c_route = st.columns([0.35, 1.5, 0.35, 4])
    
    with c_lbl1: 
        st.markdown("<div style='margin-top: 8px; font-weight: bold; color: #444;'>Hướng:</div>", unsafe_allow_html=True)
    with c_dir: 
        direction = st.selectbox("Hướng", ["⬆️ Outbound (Đi ra)", "⬇️ Inbound (Đi vào)"], label_visibility="collapsed", on_change=reset_calc)
        
    with c_lbl2: 
        st.markdown("<div style='margin-top: 8px; font-weight: bold; color: #444; text-align: right;'>Tuyến:</div>", unsafe_allow_html=True)
    with c_route:
        routes = ["1. Cát Lái ➔ Lòng Tàu ➔ P0 VT", "2. Cát Lái ➔ Soài Rạp ➔ P0 SR (Hỗn hợp)", "3. TC Hiệp Phước ➔ Soài Rạp ➔ P0 SR"] if "Outbound" in direction else ["1. P0 VT ➔ Lòng Tàu ➔ Cát Lái", "2. P0 SR ➔ Soài Rạp ➔ TC Hiệp Phước"]
        route_sel = st.selectbox("Tuyến", routes, label_visibility="collapsed", on_change=reset_calc)
    
    # ==========================================
    # 2. HÀNG THÔNG TIN THỜI GIAN CHẠY (ETA)
    # ==========================================
    wpts = ROUTE_MAP.get(route_sel, [])
    info_str = " &nbsp;|&nbsp; ".join([f"<span style='color:#1E90FF; font-weight:bold;'>{pt}</span>={format_transit_time(mins)}" for pt, mins in wpts])
    dir_text = "ĐI RA" if "Outbound" in direction else "ĐI VÀO"
    st.markdown(f"<div style='margin-top: 5px; margin-bottom: 8px; font-size: 14.5px; color: #444; background-color: #f0f2f6; padding: 8px 12px; border-radius: 5px; border-left: 4px solid #1E90FF;'><b>⏳ {dir_text}:</b> {info_str}</div>", unsafe_allow_html=True)
    
    # ==========================================
    # 3. KHU VỰC NHẬP LIỆU (Nằm ngang hàng inline)
    # ==========================================
    with st.container(border=True):
        c_lbl_d, c_date, c_lbl_dr, c_draft, c_check, c_lbl_t, c_time = st.columns([0.45, 1.2, 0.45, 0.9, 1.2, 0.4, 1])
        
        with c_lbl_d: 
            st.markdown("<div style='margin-top: 8px; font-weight: bold; color: #444;'>Date:</div>", unsafe_allow_html=True)
        with c_date: 
            pob_date = st.date_input("POB Date", datetime.datetime.now(VN_TZ).date(), format="DD/MM/YYYY", label_visibility="collapsed", on_change=reset_calc)
        
        with c_lbl_dr: 
            st.markdown("<div style='margin-top: 8px; font-weight: bold; color: #444; text-align: right;'>Draft:</div>", unsafe_allow_html=True)
        with c_draft: 
            draft = st.number_input("Draft (m)", min_value=0.0, value=9.5, step=0.1, label_visibility="collapsed", on_change=reset_calc)
        
        with c_check:
            is_single = st.checkbox("🎯 Check 1 giờ", value=False, on_change=reset_calc)
        
        pob_time = None
        if is_single:
            with c_lbl_t: 
                st.markdown("<div style='margin-top: 8px; font-weight: bold; color: #444; text-align: right;'>Giờ:</div>", unsafe_allow_html=True)
            with c_time: 
                pob_time = st.time_input("Giờ POB", get_rounded_time(), step=datetime.timedelta(minutes=30), label_visibility="collapsed", on_change=reset_calc)
            st.markdown(f"<div style='margin-top: 15px; margin-bottom: 25px; background-color: #fff9db; padding: 8px 12px; border-radius: 5px; border-left: 5px solid #fcc419; color: #856404; font-size: 14px;'>💡 Hệ thống sẽ kiểm tra AN TOÀN cho POB: <b>{pob_time.strftime('%H:%M')}</b> và MỚN: <b>{draft}m</b>.</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='margin-top: 15px; margin-bottom: 25px; background-color: #fff9db; padding: 8px 12px; border-radius: 5px; border-left: 5px solid #fcc419; color: #856404; font-size: 14px;'>🤖 <b>Ghi chú:</b> Hệ thống tự động tìm tất cả giờ POB cho mớn nước <b>{draft}m</b>.</div>", unsafe_allow_html=True)

        if st.button("🚀 PROCESS", use_container_width=True, type="primary"): st.session_state.tide_calc_run = True

    # ==========================================
    # 4. HIỂN THỊ KẾT QUẢ VÀ WINDOW THAM KHẢO
    # ==========================================
    if st.session_state.get("tide_calc_run", False):
        db = load_all_tide_data()
        if db:
            st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
            if is_single:
                res, safe, m_d, btnk = calculate_opt1_safety(route_sel, pob_date, pob_time, draft, config, db)
                df_res1 = pd.DataFrame(res)
                styler1 = df_res1.style.set_table_styles([{'selector': 'th', 'props': [('background-color', '#ffe699 !important')]}])
                st.dataframe(styler1, use_container_width=True, hide_index=True, height=500)
            else:
                safe_details = calculate_opt2_safe_times(route_sel, pob_date, draft, config, db, direction)
                max_3, min_3 = get_day_draft_extrema(route_sel, pob_date, config, db)
                msg_success = (f"<div style='background-color: #e6ffed; padding: 10px 15px; border-radius: 5px; border-left: 5px solid #2ea043; margin-bottom: 10px;'>"
                               f"<b>Thời điểm POB lọt tuyến {route_sel} cho mớn {draft}m ngày {pob_date.strftime('%d/%m/%Y')}</b><br>"
                               f"<i>(Mớn Max: {', '.join([f'{d:.1f}' for d in max_3])}m)</i></div>")
                st.markdown(msg_success, unsafe_allow_html=True)
                
                table_data = []
                for detail in safe_details:
                    row = {"Giờ POB": detail["time"].strftime('%H:%M')}
                    for pt, _ in wpts: row[pt] = f"{detail['point_drafts'][pt]:.1f}"
                    row["Draft (m)"] = f"{detail['min_max_draft']:.1f} m"
                    row["_current_safe"] = detail["current_safe"]
                    table_data.append(row)
                
                df_res2 = pd.DataFrame(table_data)
                def highlight_row(row): return ['background-color: #d4edda; font-weight: bold;'] * len(row) if row.get('_current_safe') else [''] * len(row)
                styler2 = df_res2.style.apply(highlight_row, axis=1).set_table_styles([{'selector': 'th', 'props': [('background-color', '#ffe699 !important')]}])
                st.dataframe(styler2, hide_index=True, use_container_width=True, height=600, column_config={"_current_safe": None})
                st.markdown("<div style='font-size: 13px; color: #444; margin-top: -5px;'>🟩 <i><b>Dòng chữ xanh:</b> là các giờ POB trong WINDOW.</i></div>", unsafe_allow_html=True)

            st.divider()
            col_y, col_t, col_m = st.columns(3)
            for col, d, lbl in [(col_y, pob_date - datetime.timedelta(days=1), "Yesterday"), (col_t, pob_date, "Today"), (col_m, pob_date + datetime.timedelta(days=1), "Tomorrow")]:
                with col:
                    st.markdown(f"<div class='sub-table-header'>{lbl} ({d.strftime('%d/%m')})</div>", unsafe_allow_html=True)
                    win_df = get_window_cl_for_date(d)
                    if win_df is not None:
                        vis_cols = [c for c in win_df.columns if c not in ["_dow", "_actual_date", "Date"]]
                        col_cfg = { "Dir": st.column_config.TextColumn("Dir", width=40), "Level": st.column_config.TextColumn("Level", width=45), "Slack": st.column_config.TextColumn("Slack", width=60), "VungTau": st.column_config.TextColumn("VT", width=45), "DongNai": st.column_config.TextColumn("DN", width=45), "SaiGon": st.column_config.TextColumn("SG", width=45) }
                        st.dataframe(win_df, use_container_width=False, hide_index=True, height=280, column_config=col_cfg, column_order=vis_cols)
                    else: st.caption("Không có dữ liệu")
    st.markdown("<br><div style='height: 50px;'></div>", unsafe_allow_html=True)
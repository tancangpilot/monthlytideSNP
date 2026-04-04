import streamlit as st
import datetime
import pandas as pd
from utils.tide_engine import load_all_tide_data, get_window_cl_for_date, calculate_opt1_safety, calculate_opt2_safe_times, get_day_draft_extrema, ROUTE_MAP

# KHỞI TẠO MÚI GIỜ VIỆT NAM (UTC+7)
VN_TZ = datetime.timezone(datetime.timedelta(hours=7))

def get_rounded_time():
    # SỬA GIỜ Ở ĐÂY
    now = datetime.datetime.now(VN_TZ)
    minutes = (now.minute // 30 + (1 if now.minute % 30 >= 15 else 0)) * 30
    return (now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(minutes=minutes)).time()

def format_transit_time(mins):
    h, m = divmod(mins, 60)
    if h > 0 and m > 0: return f"+{h}h{m}"
    elif h > 0: return f"+{h}h"
    else: return f"+{m}'"

def render_tide_calc_tab(direction):
    config = st.session_state.config
    
    routes = ["1. Cát Lái ➔ Lòng Tàu ➔ P0 VT", "2. Cát Lái ➔ Soài Rạp ➔ P0 SR (Hỗn hợp)", "3. TC Hiệp Phước ➔ Soài Rạp ➔ P0 SR"] if "Outbound" in direction else ["1. P0 VT ➔ Lòng Tàu ➔ Cát Lái", "2. P0 SR ➔ Soài Rạp ➔ TC Hiệp Phước"]
    route_sel = st.radio("Route", routes, label_visibility="collapsed")
    
    wpts = ROUTE_MAP.get(route_sel, [])
    info_str = " &nbsp;|&nbsp; ".join([f"<span style='color:#1E90FF; font-weight:bold;'>{pt}</span> = POB {format_transit_time(mins)}" for pt, mins in wpts])
    st.markdown(f"<div style='margin-top: 5px; margin-bottom: 5px; font-size: 14.5px; color: #444; background-color: #f0f2f6; padding: 8px 12px; border-radius: 5px; border-left: 4px solid #1E90FF;'><b>⏳ Chi tiết:</b> {info_str}</div>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)
    
    calc_options = [
        "Opt1: Kiểm tra AN TOÀN (Nhập POB và Draft)", 
        "Opt2: Tìm giờ POB & Tra cứu mớn tối đa (Nhập POB Date & Draft)"
    ]
    selected_opt = st.radio("Opt", calc_options, label_visibility="collapsed")
    
    # SỬA NGÀY HIỂN THỊ MẶC ĐỊNH BẰNG UTC+7
    default_date = datetime.datetime.now(VN_TZ).date()
    default_time = get_rounded_time()
    default_draft = 9.5
    
    lbl_style = "<div style='margin-top: 8px; font-weight: 600; color: #444; font-size: 14px; text-align: right; padding-right: 10px;'>{}</div>"

    with st.container(border=True):
        if selected_opt == calc_options[0]:
            c1, c2, c3, c4, c5, c6 = st.columns([0.6, 1.5, 0.6, 1.5, 0.6, 1.2])
            with c1: st.markdown(lbl_style.format("POB Date"), unsafe_allow_html=True)
            with c2: pob_date = st.date_input("d1", default_date, label_visibility="collapsed")
            with c3: st.markdown(lbl_style.format("POB Time"), unsafe_allow_html=True)
            with c4: pob_time = st.time_input("t1", default_time, step=datetime.timedelta(minutes=30), label_visibility="collapsed")
            with c5: st.markdown(lbl_style.format("Draft (m)"), unsafe_allow_html=True)
            with c6: draft = st.number_input("dr1", min_value=0.0, value=default_draft, step=0.1, label_visibility="collapsed")
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                db = load_all_tide_data()
                if db:
                    res, safe, m_d, btnk = calculate_opt1_safety(route_sel, pob_date, pob_time, draft, config, db)
                    st.markdown("---")
                    if safe: st.success(f"🟢 **ĐỦ NƯỚC** (Min mớn {m_d:.1f}m tại {btnk})")
                    else: st.error(f"🔴 **KHÔNG ĐỦ NƯỚC tại {btnk}** ({m_d:.1f}m)")
                    st.dataframe(pd.DataFrame(res), use_container_width=True, hide_index=True)

        elif selected_opt == calc_options[1]:
            c1, c2, c3, c4, _, _ = st.columns([0.6, 1.5, 0.7, 1.5, 1, 1])
            with c1: st.markdown(lbl_style.format("POB Date"), unsafe_allow_html=True)
            with c2: pob_date = st.date_input("d2", default_date, label_visibility="collapsed")
            with c3: st.markdown(lbl_style.format("Draft (m)"), unsafe_allow_html=True)
            with c4: draft = st.number_input("dr2", min_value=0.0, value=default_draft, step=0.1, label_visibility="collapsed")
            
            st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                db = load_all_tide_data()
                if db:
                    safe_details = calculate_opt2_safe_times(route_sel, pob_date, draft, config, db, direction)
                    max_3, min_3 = get_day_draft_extrema(route_sel, pob_date, config, db)
                    max_str = ", ".join([f"{d:.1f}" for d in max_3]) if max_3 else "N/A"
                    min_str = ", ".join([f"{d:.1f}" for d in min_3]) if min_3 else "N/A"
                    
                    st.markdown("---")
                    
                    msg_success = (f"<div style='background-color: #e6ffed; padding: 12px 15px; border-radius: 5px; border-left: 5px solid #2ea043; margin-bottom: 15px;'>"
                                   f"<span style='color: #004d1a; font-size: 16px;'><b>Thời điểm POB lọt tuyến {route_sel} cho mớn {draft}m trong ngày {pob_date.strftime('%d/%m/%Y')}</b></span><br>"
                                   f"<span style='color: #006622; font-size: 15px;'><i>(Trong ngày mớn nước tối đa là <b>{max_str}</b> m, mớn nước tối thiểu là <b>{min_str}</b> m)</i></span>"
                                   f"</div>")
                    msg_error = (f"<div style='background-color: #ffe6e6; padding: 12px 15px; border-radius: 5px; border-left: 5px solid #ff4d4d; margin-bottom: 15px;'>"
                                 f"<span style='color: #990000; font-size: 16px;'>🔴 <b>KHÔNG CÓ GIỜ NÀO TRONG NGÀY ĐỦ NƯỚC CHO MỚN {draft}m!</b></span><br>"
                                 f"<span style='color: #b30000; font-size: 15px;'><i>(Trong ngày mớn nước tối đa là <b>{max_str}</b> m, mớn nước tối thiểu là <b>{min_str}</b> m)</i></span>"
                                 f"</div>")
                    
                    if not safe_details: 
                        st.markdown(msg_error, unsafe_allow_html=True)
                    else:
                        st.markdown(msg_success, unsafe_allow_html=True)
                        table_data = []
                        wpts = ROUTE_MAP.get(route_sel, [])
                        for detail in safe_details:
                            row = {"Giờ POB": detail["time"].strftime('%H:%M')}
                            for pt, _ in wpts: row[pt] = f"{detail['point_drafts'][pt]:.1f}"
                            row["CHỐT (Max)"] = f"⭐ {detail['min_max_draft']:.1f} m"
                            row["_current_safe"] = detail["current_safe"] 
                            table_data.append(row)
                        
                        df_res = pd.DataFrame(table_data)
                        
                        def highlight_row(row):
                            if row.get('_current_safe', False):
                                return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row)
                            return [''] * len(row)
                            
                        styled_df = df_res.style.apply(highlight_row, axis=1)
                        
                        st.dataframe(styled_df, hide_index=True, use_container_width=True, column_config={"_current_safe": None})
                        
                        st.markdown("<div style='font-size: 14.5px; color: #444; margin-top: 2px; margin-bottom: 10px;'>🟩 <i><b>Dòng chữ và nền màu xanh:</b> Giờ POB có nước nhẹ, thỏa mãn điều kiện dòng chảy (Window).</i></div>", unsafe_allow_html=True)
                    
                    styled_win = get_window_cl_for_date(pob_date)
                    if styled_win is not None:
                        vis_cols = [c for c in styled_win.data.columns if c not in ["_dow", "_actual_date"]]
                        col_cfg = {"Date": st.column_config.TextColumn("Date", pinned=True), "Dir": st.column_config.TextColumn("Dir", width="small")}
                        for c in vis_cols:
                            if c not in ["Date", "Dir", "Level", "Slack", "Vung Tau"]:
                                col_cfg[c] = st.column_config.TextColumn(c, width="small")
                        st.dataframe(styled_win, use_container_width=False, hide_index=True, column_config=col_cfg, column_order=vis_cols)

    st.markdown("<br>", unsafe_allow_html=True)
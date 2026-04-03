import streamlit as st
import datetime
import pandas as pd
from utils.tide_engine import load_all_tide_data, get_window_cl_for_date, calculate_opt1_safety, calculate_opt2_safe_times, calculate_opt3_max_drafts, ROUTE_MAP

def get_rounded_time():
    now = datetime.datetime.now()
    minutes = (now.minute // 30 + (1 if now.minute % 30 >= 15 else 0)) * 30
    return (now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(minutes=minutes)).time()

def render_tide_calc_tab(route_sel):
    config = st.session_state.config
    st.markdown(f"<div style='margin-bottom: 15px;'><span style='font-size: 14px; color: #888;'>Tuyến đang chọn:</span> <span style='font-size: 22px; font-weight: bold; color: #1E90FF; margin-left: 10px;'>{route_sel}</span></div>", unsafe_allow_html=True)
    calc_options = ["Opt1: Kiểm tra AN TOÀN (Nhập POB và Draft)", "Opt2: Tìm giờ POB (Nhập POB Date & Draft)", "Opt3: Tìm giờ POB và Max draft (Chỉ nhập POB Date)"]
    selected_opt = st.radio("Opt", calc_options, label_visibility="collapsed")
    default_date, default_time, default_draft = datetime.date.today(), get_rounded_time(), 10.5
    lbl_style = "<div style='margin-top: 8px; font-weight: 600; color: #444; font-size: 14px; text-align: right; padding-right: 10px;'>{}</div>"

    with st.container(border=True):
        if selected_opt == calc_options[0]:
            c1, c2, c3, c4, c5, c6 = st.columns([0.6, 1.5, 0.6, 1.5, 0.6, 1.2])
            with c1: st.markdown(lbl_style.format("POB Date"), unsafe_allow_html=True)
            with c2: pob_date = st.date_input("d1", default_date, label_visibility="collapsed")
            with c3: st.markdown(lbl_style.format("POB Time"), unsafe_allow_html=True)
            with c4: pob_time = st.time_input("t1", default_time, label_visibility="collapsed")
            with c5: st.markdown(lbl_style.format("Draft (m)"), unsafe_allow_html=True)
            with c6: draft = st.number_input("dr1", min_value=0.0, value=default_draft, step=0.1, label_visibility="collapsed")
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
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                db = load_all_tide_data()
                if db:
                    safe_details = calculate_opt2_safe_times(route_sel, pob_date, draft, config, db)
                    st.markdown("---")
                    if not safe_details: 
                        st.error(f"🔴 **KHÔNG CÓ GIỜ NÀO TRONG NGÀY ĐỦ NƯỚC CHO MỚN {draft}m!**")
                    else:
                        st.success(f"🟢 **Khung giờ POB lọt tuyến {route_sel} cho mớn {draft}m:**")
                        
                        # Xây dựng bảng hiển thị chi tiết mớn nước tại từng điểm
                        table_data = []
                        wpts = ROUTE_MAP.get(route_sel, [])
                        for detail in safe_details:
                            row = {"Giờ POB": detail["time"].strftime('%H:%M')}
                            for pt, _ in wpts:
                                row[pt] = f"{detail['point_drafts'][pt]:.1f}"
                            row["CHỐT (Max)"] = f"⭐ {detail['min_max_draft']:.1f} m"
                            table_data.append(row)
                            
                        st.dataframe(pd.DataFrame(table_data), hide_index=True, use_container_width=True)
                    
                    # BẢNG WINDOW ĐƯỢC ÉP KIỂM SOÁT CỘT NGHIÊM NGẶT
                    styled_win = get_window_cl_for_date(pob_date)
                    if styled_win is not None:
                        vis_cols = [c for c in styled_win.data.columns if c not in ["_dow", "_actual_date"]]
                        col_cfg = {"Date": st.column_config.TextColumn("Date", pinned=True)}
                        for c in vis_cols:
                            if c not in ["Date", "Level", "Dir", "Slack", "Vung Tau"]:
                                c_str = str(c).replace("Begin", "B.").replace("End", "E.").replace("Port", "P.").replace("Stb", "S.")
                                col_cfg[c] = st.column_config.TextColumn(c_str, help=f"**{c}**\n\n*(B: Begin / E: End / P: Port / S: Starboard)*")
                        st.dataframe(styled_win, use_container_width=False, hide_index=True, column_config=col_cfg, column_order=vis_cols)

        elif selected_opt == calc_options[2]:
            c1, c2, _, _, _, _ = st.columns([0.6, 1.5, 1, 1, 1, 1])
            with c1: st.markdown(lbl_style.format("POB Date"), unsafe_allow_html=True)
            with c2: pob_date = st.date_input("d3", default_date, label_visibility="collapsed")
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                db = load_all_tide_data()
                if db:
                    peaks = calculate_opt3_max_drafts(route_sel, pob_date, config, db)
                    st.markdown("---")
                    if peaks:
                        st.success(f"📈 **Các thời điểm POB cho mớn nước lớn nhất trong ngày {pob_date.strftime('%d/%m/%Y')}**\n\n**Tuyến:** {route_sel}")
                        cols = st.columns(len(peaks))
                        wpts = ROUTE_MAP.get(route_sel, [])
                        for i, p_info in enumerate(peaks):
                            with cols[i]:
                                st.markdown(f"<div style='background-color:#e6f7ff; padding:10px; border-radius:5px; border-left:4px solid #1E90FF; margin-bottom:10px;'><b>🌊 HW {i+1}</b> (Đỉnh: {p_info['peak_time'].strftime('%H:%M')})</div>", unsafe_allow_html=True)
                                t_data = []
                                for t in p_info["top5"]:
                                    row = {"Giờ POB": t["time"].strftime('%H:%M')}
                                    for pt, _ in wpts: row[pt] = f"{t['point_drafts'][pt]:.1f}"
                                    row["CHỐT"] = f"⭐ {t['draft']:.1f}"
                                    t_data.append(row)
                                st.dataframe(pd.DataFrame(t_data), hide_index=True, use_container_width=True)
                    
                    styled_win = get_window_cl_for_date(pob_date)
                    if styled_win is not None:
                        vis_cols = [c for c in styled_win.data.columns if c not in ["_dow", "_actual_date"]]
                        col_cfg = {"Date": st.column_config.TextColumn("Date", pinned=True)}
                        for c in vis_cols:
                            if c not in ["Date", "Level", "Dir", "Slack", "Vung Tau"]:
                                c_str = str(c).replace("Begin", "B.").replace("End", "E.").replace("Port", "P.").replace("Stb", "S.")
                                col_cfg[c] = st.column_config.TextColumn(c_str, help=f"**{c}**\n\n*(B: Begin / E: End / P: Port / S: Starboard)*")
                        st.dataframe(styled_win, use_container_width=False, hide_index=True, column_config=col_cfg, column_order=vis_cols)

    st.markdown("<br>", unsafe_allow_html=True)
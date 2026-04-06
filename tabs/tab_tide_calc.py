import streamlit as st
import datetime
import pandas as pd
from utils.tide_engine import load_all_tide_data, load_raw_window, check_current_condition, get_window_cl_for_date, calculate_opt1_safety, calculate_opt2_safe_times, get_day_draft_extrema, ROUTE_MAP, VN_TZ

def reset_calc():
    st.session_state.tide_calc_run = False

def get_rounded_time():
    now = datetime.datetime.now(VN_TZ)
    minutes = (now.minute // 30 + (1 if now.minute % 30 >= 15 else 0)) * 30
    return (now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(minutes=minutes)).time()

def format_transit_time(mins):
    h, m = divmod(mins, 60)
    if h > 0 and m > 0: return f"+{h}h{m}"
    elif h > 0: return f"+{h}h"
    else: return f"+{m}'"

def render_tide_calc_tab(direction):
    if "tide_calc_run" not in st.session_state:
        st.session_state.tide_calc_run = False

    config = st.session_state.config
    
    routes = ["1. Cát Lái ➔ Lòng Tàu ➔ P0 VT", "2. Cát Lái ➔ Soài Rạp ➔ P0 SR (Hỗn hợp)", "3. TC Hiệp Phước ➔ Soài Rạp ➔ P0 SR"] if "Outbound" in direction else ["1. P0 VT ➔ Lòng Tàu ➔ Cát Lái", "2. P0 SR ➔ Soài Rạp ➔ TC Hiệp Phước"]
    route_sel = st.radio("Route", routes, label_visibility="collapsed", on_change=reset_calc)
    
    wpts = ROUTE_MAP.get(route_sel, [])
    info_str = " &nbsp;|&nbsp; ".join([f"<span style='color:#1E90FF; font-weight:bold;'>{pt}</span> = POB {format_transit_time(mins)}" for pt, mins in wpts])
    
    dir_text = "ĐI RA" if "Outbound" in direction else "ĐI VÀO"
    st.markdown(f"<div style='margin-top: 5px; margin-bottom: 5px; font-size: 14.5px; color: #444; background-color: #f0f2f6; padding: 8px 12px; border-radius: 5px; border-left: 4px solid #1E90FF;'><b>⏳ {dir_text}:</b> {info_str}</div>", unsafe_allow_html=True)
    
    st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
    
    with st.container(border=True):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1: 
            pob_date = st.date_input("POB Date", datetime.datetime.now(VN_TZ).date(), on_change=reset_calc)
        with c2: 
            draft = st.number_input("Draft (m)", min_value=0.0, value=9.5, step=0.1, on_change=reset_calc)
        with c3:
            is_single = st.checkbox("🎯 Check 1 giờ cụ thể", value=False, on_change=reset_calc)

        pob_time = None
        if is_single:
            pob_time = st.time_input("Nhập giờ POB", get_rounded_time(), step=datetime.timedelta(minutes=30), on_change=reset_calc)
            # --- CẬP NHẬT CÂU THÔNG BÁO CHO OPT 1 ---
            st.info(f"💡 Hệ thống sẽ kiểm tra AN TOÀN cho POB: **{pob_time.strftime('%H:%M')}** và MỚN: **{draft}m**.")
        else:
            st.info(f"🤖 Hệ thống tự động tìm tất cả giờ POB cho mớn nước {draft}m trong ngày *(Để mớn càng nhỏ, giờ POB trong bảng càng nhiều)*.")

        if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
            st.session_state.tide_calc_run = True

        if st.session_state.get("tide_calc_run", False):
            db = load_all_tide_data()
            if db:
                st.markdown("<hr style='margin: 5px 0px 15px 0px; border-top: 1px solid #ddd;'>", unsafe_allow_html=True)
                
                if is_single:
                    res, safe, m_d, btnk = calculate_opt1_safety(route_sel, pob_date, pob_time, draft, config, db)
                    
                    # --- BƯỚC 1: ĐƯA BẢNG LÊN TRÊN ---
                    df_res1 = pd.DataFrame(res)
                    styler1 = df_res1.style.set_table_styles([{'selector': 'th', 'props': [('background-color', '#ffe699 !important'), ('color', '#111 !important')]}])
                    st.dataframe(styler1, use_container_width=True, hide_index=True)
                    
                    # --- BƯỚC 2: CHECK WINDOW VÀ HIỂN THỊ DÒNG TỔNG KẾT XUỐNG DƯỚI ---
                    raw_win_df = load_raw_window()
                    pob_dt = datetime.datetime.combine(pob_date, pob_time)
                    in_window = check_current_condition(pob_dt, direction, raw_win_df)
                    window_status = "TRONG WINDOW" if in_window else "NGOÀI WINDOW"
                    
                    if safe: 
                        st.success(f"🟢 **ĐỦ NƯỚC** (min Draft {m_d:.1f}m tại {btnk}) đi tuyến **{route_sel}** ({window_status}).")
                    else: 
                        st.error(f"🔴 **KHÔNG ĐỦ NƯỚC tại {btnk}** ({m_d:.1f}m) đi tuyến **{route_sel}** ({window_status}).")
                    
                else:
                    safe_details = calculate_opt2_safe_times(route_sel, pob_date, draft, config, db, direction)
                    max_3, min_3 = get_day_draft_extrema(route_sel, pob_date, config, db)
                    max_str, min_str = ", ".join([f"{d:.1f}" for d in max_3]), ", ".join([f"{d:.1f}" for d in min_3])
                    
                    msg_success = (f"<div style='background-color: #e6ffed; padding: 12px 15px; border-radius: 5px; border-left: 5px solid #2ea043; margin-bottom: 15px;'>"
                                   f"<span style='color: #004d1a; font-size: 16px;'><b>Thời điểm POB lọt tuyến {route_sel} cho mớn {draft}m trong ngày {pob_date.strftime('%d/%m/%Y')}</b></span><br>"
                                   f"<span style='color: #006622; font-size: 15px;'><i>(Trong ngày mớn tối đa là <b>{max_str}</b> m, mớn tối thiểu là <b>{min_str}</b> m)</i></span>"
                                   f"</div>")
                    
                    if not safe_details:
                        st.error(f"🔴 KHÔNG CÓ GIỜ NÀO TRONG NGÀY ĐỦ NƯỚC CHO MỚN {draft}m!")
                        st.markdown(msg_success, unsafe_allow_html=True)
                    else:
                        st.markdown(msg_success, unsafe_allow_html=True)
                        table_data = []
                        for detail in safe_details:
                            row = {"Giờ POB": detail["time"].strftime('%H:%M')}
                            for pt, _ in wpts: row[pt] = f"{detail['point_drafts'][pt]:.1f}"
                            row["Draft (m)"] = f"{detail['min_max_draft']:.1f} m"
                            row["_current_safe"] = detail["current_safe"]
                            table_data.append(row)
                        
                        df_res2 = pd.DataFrame(table_data)
                        def highlight_row(row):
                            if row.get('_current_safe', False):
                                return ['background-color: #d4edda; color: #155724; font-weight: bold;'] * len(row)
                            return [''] * len(row)
                        
                        styler2 = df_res2.style.apply(highlight_row, axis=1).set_table_styles([
                            {'selector': 'th', 'props': [('background-color', '#ffe699 !important'), ('color', '#111 !important')]}
                        ])
                        st.dataframe(styler2, hide_index=True, use_container_width=True, column_config={"_current_safe": None})
                        st.markdown("<div style='font-size: 14px; color: #444; margin-top: 2px; margin-bottom: 15px;'>🟩 <i><b>Dòng chữ xanh:</b> là các giờ POB trong WINDOW.</i></div>", unsafe_allow_html=True)

                col_y, col_t, col_m = st.columns(3)
                dates = [
                    (col_y, pob_date - datetime.timedelta(days=1), "Yesterday"),
                    (col_t, pob_date, "Today"),
                    (col_m, pob_date + datetime.timedelta(days=1), "Tomorrow")
                ]
                
                for col, d, lbl in dates:
                    with col:
                        st.markdown(f"<div style='text-align: center; background-color: #f8f9fa; padding: 5px; border-radius: 5px; margin-bottom: 5px; font-weight: bold;'>{lbl} ({d.strftime('%d/%m')})</div>", unsafe_allow_html=True)
                        win_df = get_window_cl_for_date(d)
                        if win_df is not None:
                            vis_cols = [c for c in win_df.data.columns if c not in ["_dow", "_actual_date", "Date"]]
                            col_cfg = {"Dir": st.column_config.TextColumn("Dir")}
                            for c in vis_cols:
                                if c not in ["Dir", "Level", "Slack", "VungTau"]:
                                    col_cfg[c] = st.column_config.TextColumn(c, width="small")
                            st.dataframe(win_df, use_container_width=True, hide_index=True, column_config=col_cfg, column_order=vis_cols)
                        else:
                            st.caption("Không có dữ liệu")

    st.markdown("<br>", unsafe_allow_html=True)
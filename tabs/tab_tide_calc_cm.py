import streamlit as st
import datetime
import pandas as pd
from utils.tide_engine import load_all_tide_data, get_tide_at_eta, VN_TZ
from utils.data_processor import process_and_style_df

@st.cache_data(show_spinner=False)
def load_cm_window_data():
    try:
        raw_win_df = pd.read_excel("data_window.xlsx", sheet_name="WindowCM")
        raw_win_df.columns = [str(c).strip() for c in raw_win_df.columns]
        raw_dates = pd.to_datetime(raw_win_df['Date'], errors='coerce')
        is_valid = raw_dates.apply(lambda x: pd.notna(x) and x.year > 2000)
        raw_win_df['_actual_date'] = raw_dates.where(is_valid).bfill(limit=1).ffill().dt.date
        return raw_win_df
    except Exception as e:
        return None

def render_tide_calc_cm_tab():
    # CSS Thiết kế riêng cho CÁI MÉP
    st.markdown("""
        <style>
        .cm-day-header { text-align: center; font-size: 16px; font-weight: bold; color: #1E90FF; background-color: #f0f2f6; padding: 6px; border: 1px solid #ddd; border-radius: 5px; margin-top: 20px; margin-bottom: 10px; }
        .cm-window-title { font-size: 14.5px; font-weight: bold; color: #d93025; margin-top: 15px; margin-bottom: 5px; border-left: 4px solid #d93025; padding-left: 8px; }
        .cm-summary-box { font-size: 14.5px; color: #856404; background-color: #fff3cd; border-left: 4px solid #ffeeba; padding: 10px 15px; margin-top: 10px; margin-bottom: 15px; border-radius: 5px; }
        </style>
    """, unsafe_allow_html=True)

    config = st.session_state.config
    
    # 1. GIAO DIỆN TỐI GIẢN (CHẾ ĐỘ LIVE MODE TỰ ĐỘNG LOAD)
    with st.container(border=True):
        col_date, col_action, col_btn = st.columns([1, 1.5, 1])
        with col_date:
            current_date = st.session_state.get("cm_date", datetime.datetime.now(VN_TZ).date())
            pob_date = st.date_input("Ngày", current_date, format="DD/MM/YYYY", label_visibility="collapsed")
        with col_action:
            action_options = ["CẬP BẾN (Berthing)", "RỜI BẾN (Unberthing)"]
            current_action = st.session_state.get("cm_action", action_options[0])
            idx = action_options.index(current_action) if current_action in action_options else 0
            action = st.radio("Hành động", action_options, index=idx, horizontal=True, label_visibility="collapsed")
        with col_btn:
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                st.session_state.tide_calc_cm_run = True

        # BÙA CHÚ AUTO-LOAD: Nếu hệ thống đã nổ máy (tide_calc_cm_run = True), 
        # mọi thay đổi của Radio gạt mạn hoặc Đổi ngày sẽ tự động đồng bộ và load ngay lập tức!
        if st.session_state.get("tide_calc_cm_run", False):
            st.session_state.cm_date = pob_date
            st.session_state.cm_action = action

    # 2. XỬ LÝ DỮ LIỆU CUỐN CHIẾU
    if st.session_state.get("tide_calc_cm_run", False):
        db = load_all_tide_data()
        if not db:
            st.error("❌ Không tải được dữ liệu thủy triều.")
            return
            
        run_date = st.session_state.cm_date
        action_val = st.session_state.cm_action
        action_str = "CẬP BẾN" if "CẬP" in action_val else "RỜI BẾN"
        
        raw_win_df = load_cm_window_data()
        if raw_win_df is None:
            st.error("❌ Lỗi đọc file data_window.xlsx (sheet WindowCM).")
            return

        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)
        
        for d, lbl in [(run_date, "Today"), (run_date + datetime.timedelta(days=1), "Tomorrow")]:
            st.markdown(f"<div class='cm-day-header'>{lbl} ({d.strftime('%d/%m')})</div>", unsafe_allow_html=True)
            
            df_day = raw_win_df[raw_win_df['_actual_date'] == d].copy()
            if df_day.empty:
                st.info(f"Không có dữ liệu Window cho ngày {d.strftime('%d/%m/%Y')}")
                continue
            
            base_cols = ["VungTau", "Level", "Slack", "Dir"]
            if "CẬP" in action_val:
                action_cols = [c for c in df_day.columns if "Begin B-" in c or "End B-" in c]
            else:
                action_cols = [c for c in df_day.columns if "Begin UB-" in c or "End UB-" in c]
            
            show_cols = base_cols + action_cols
            df_display = df_day[['_actual_date', 'Date'] + show_cols].copy()
            
            # IN BẢNG WINDOW
            styled_table = process_and_style_df(df_display, show_past_dates=True)
            col_cfg = { 
                "Dir": st.column_config.TextColumn("Dir", width=35), 
                "Level": st.column_config.TextColumn("Lvl", width=35), 
                "Slack": st.column_config.TextColumn("Slk", width=40), 
                "VungTau": st.column_config.TextColumn("VT", width=40)
            }
            for c in action_cols:
                short_name = c.replace("Begin ", "B.").replace("End ", "E.").replace("Starboard", "S").replace("Port", "P").replace("-Stb", "-S")
                col_cfg[c] = st.column_config.TextColumn(short_name, width=50)
            
            st.dataframe(styled_table, use_container_width=True, hide_index=True, column_config=col_cfg, column_order=show_cols)
            
            # CHUẨN BỊ TÍNH MỚN
            valid_df = styled_table.data
            day_draft_values = set()
            windows_data_to_render = []
            
            # VÒNG QUÉT 1: Tính toán toàn bộ các block để tìm Max/Min
            for idx, row in valid_df.iterrows():
                times = []
                for c in action_cols:
                    val = row.get(c)
                    if pd.notna(val) and str(val).strip() not in ["", "nan"]:
                        vs = str(val).strip().replace(".", ":").replace(" ", ":").replace(",", ":")
                        try:
                            if vs.startswith("24:"): t = datetime.time(23, 59, 59)
                            elif len(vs) >= 4 and ":" in vs: t = datetime.time(int(vs.split(":")[0]), int(vs.split(":")[1][:2]))
                            else: continue
                            times.append(datetime.datetime.combine(d, t))
                        except: pass
                
                if not times: continue
                
                corrected_times = []
                times.sort()
                max_t = times[-1]
                for t_dt in times:
                    if (max_t - t_dt).total_seconds() > 12 * 3600:
                        corrected_times.append(t_dt + datetime.timedelta(days=1))
                    else:
                        corrected_times.append(t_dt)
                        
                min_dt = min(corrected_times)
                max_dt = max(corrected_times)
                
                start_m = (min_dt.minute // 30) * 30
                block_start = min_dt.replace(minute=start_m, second=0, microsecond=0)
                
                if max_dt.minute % 30 != 0 or max_dt.second != 0:
                    extra_mins = 30 - (max_dt.minute % 30)
                    block_end = max_dt + datetime.timedelta(minutes=extra_mins)
                    block_end = block_end.replace(second=0, microsecond=0)
                else:
                    block_end = max_dt
                
                blocks = []
                curr = block_start
                while curr <= block_end:
                    blocks.append(curr)
                    curr += datetime.timedelta(minutes=30)
                    
                depth = float(config.get("cm", 14.0))
                blocks_data = []
                for b_dt in blocks:
                    tide = get_tide_at_eta(db, "CM", b_dt)
                    if tide is not None and not pd.isna(tide):
                        draft_val = (tide + depth) / 1.10
                        draft_rounded = round(draft_val, 1)
                        day_draft_values.add(draft_rounded)
                        blocks_data.append((b_dt, draft_rounded, f"{draft_rounded:.1f}"))
                
                if blocks_data:
                    windows_data_to_render.append({
                        "min_dt": min_dt,
                        "max_dt": max_dt,
                        "blocks_data": blocks_data
                    })
            
            # IN DÒNG CHÚ THÍCH MAX/MIN
            if day_draft_values:
                sorted_drafts = sorted(list(day_draft_values))
                min_3 = sorted_drafts[:3]
                max_3 = sorted(sorted_drafts, reverse=True)[:3]
                
                st.markdown(f"<div class='cm-summary-box'>📌 Mớn nước trong ngày {d.strftime('%d/%m/%Y')} "
                            f"lớn nhất là: <b>{', '.join([f'{v:.1f}' for v in max_3])}m</b>, "
                            f"nhỏ nhất là: <b>{', '.join([f'{v:.1f}' for v in min_3])}m</b><br>"
                            f"<i>(Ở bảng dưới chỉ hiển thị các mớn ≤ 15.0m)</i></div>", unsafe_allow_html=True)
            
            # VÒNG QUÉT 2: Lọc bỏ mớn > 15.0 và in bảng
            for w_data in windows_data_to_render:
                min_dt = w_data["min_dt"]
                max_dt = w_data["max_dt"]
                
                # BỘ LỌC TÀN NHẪN: Chém sạch các mớn > 15.0
                filtered_blocks = [item for item in w_data["blocks_data"] if item[1] <= 15.0]
                
                if not filtered_blocks:
                    st.info(f"Khung window {min_dt.strftime('%H:%M')} ➔ {max_dt.strftime('%H:%M')} không có mớn nào ≤ 15.0m.")
                    continue
                    
                st.markdown(f"<div class='cm-window-title'>Bảng mớn nước tàu {action_str} cho window: {min_dt.strftime('%H:%M')} ➔ {max_dt.strftime('%H:%M')}</div>", unsafe_allow_html=True)
                
                CHUNK_SIZE = 12
                for i in range(0, len(filtered_blocks), CHUNK_SIZE):
                    chunk = filtered_blocks[i:i+CHUNK_SIZE]
                    
                    chunk_dict = {}
                    for b_dt, _, dr_str in chunk:
                        time_str = b_dt.strftime('%H:%M')
                        if b_dt.date() > d: time_str += " (+1)"
                        chunk_dict[time_str] = dr_str
                        
                    df_chunk = pd.DataFrame([chunk_dict])
                    
                    styler = df_chunk.style.set_table_styles([
                        {'selector': 'th', 'props': [('background-color', '#ffe699 !important'), ('color', '#111 !important'), ('text-align', 'center !important')]},
                        {'selector': 'td', 'props': [('text-align', 'center !important'), ('font-weight', 'bold'), ('color', '#1E90FF !important'), ('font-size', '15px !important')]}
                    ])
                    
                    st.dataframe(styler, use_container_width=True, hide_index=True)

    st.markdown("<br><div style='height: 40px;'></div>", unsafe_allow_html=True)
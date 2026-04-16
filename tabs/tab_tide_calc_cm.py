import streamlit as st
import datetime
import pandas as pd
import os
from utils.tide_engine import load_all_tide_data, get_tide_at_eta, VN_TZ
from utils.data_processor import process_and_style_df

@st.cache_data(show_spinner=False)
def load_cm_window_data(mtime):
    try:
        raw_win_df = pd.read_excel("data_window.xlsx", sheet_name="WindowCM")
        raw_win_df.columns = [str(c).strip() for c in raw_win_df.columns]
        raw_dates = pd.to_datetime(raw_win_df['Date'], errors='coerce')
        is_valid = raw_dates.apply(lambda x: pd.notna(x) and x.year > 2000)
        raw_win_df['_actual_date'] = raw_dates.where(is_valid).bfill(limit=1).ffill().dt.date
        return raw_win_df
    except Exception as e:
        st.error(f"❌ Lỗi nạp file WindowCM: {e}")
        return None

def render_tide_calc_cm_tab():
    st.markdown("""
        <style>
        .cm-day-header { text-align: center; font-size: 16px; font-weight: bold; color: #1E90FF; background-color: #f0f2f6; padding: 6px; border: 1px solid #ddd; border-radius: 5px; margin-top: 20px; margin-bottom: 10px; }
        .cm-window-title { font-size: 14.5px; font-weight: bold; color: #d93025; margin-top: 15px; margin-bottom: 5px; border-left: 4px solid #d93025; padding-left: 8px; }
        .cm-summary-box { font-size: 14.5px; color: #856404; background-color: #fff3cd; border-left: 4px solid #ffeeba; padding: 10px 15px; margin-top: 10px; margin-bottom: 15px; border-radius: 5px; }
        </style>
    """, unsafe_allow_html=True)

    config = st.session_state.config

    with st.container(border=True):
        col_date, col_action, col_btn = st.columns([1, 1.5, 1])
        with col_date:
            sel_date = st.date_input("Ngày", datetime.datetime.now(VN_TZ).date(), format="DD/MM/YYYY", label_visibility="collapsed", key="cm_live_date")
        with col_action:
            sel_action = st.radio("Hành động", ["CẬP BẾN (Berthing)", "RỜI BẾN (Unberthing)"], horizontal=True, label_visibility="collapsed", key="cm_live_action")
        with col_btn:
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                st.cache_data.clear()
                st.session_state.tide_calc_cm_activated = True

    if st.session_state.get("tide_calc_cm_activated", False):
        db = load_all_tide_data()
        mtime = os.path.getmtime("data_window.xlsx") if os.path.exists("data_window.xlsx") else 0
        raw_win_df = load_cm_window_data(mtime)

        if raw_win_df is None: return

        action_str = "CẬP BẾN" if "CẬP" in sel_action else "RỜI BẾN"
        st.markdown("<hr style='margin: 10px 0;'>", unsafe_allow_html=True)

        for d, lbl in [(sel_date, "Today"), (sel_date + datetime.timedelta(days=1), "Tomorrow")]:
            st.markdown(f"<div class='cm-day-header'>{lbl} ({d.strftime('%d/%m')})</div>", unsafe_allow_html=True)

            df_day = raw_win_df[raw_win_df['_actual_date'] == d].copy()
            if df_day.empty:
                st.info(f"Không có dữ liệu cho ngày {d.strftime('%d/%m/%Y')}")
                continue

            base_cols = ["VungTau", "Level", "Slack", "Dir"]
            
            # --- ĐÃ SỬA: Radar nhận diện cột siêu mạnh ---
            action_cols = []
            for c in df_day.columns:
                cl = str(c).lower()
                if "begin" in cl or "end" in cl:
                    if "CẬP" in sel_action:
                        # Cập bến: Gom các cột không chứa chữ 'ub' (unberthing)
                        if "ub" not in cl:
                            action_cols.append(c)
                    else:
                        # Rời bến: Gom các cột có chứa chữ 'ub'
                        if "ub" in cl:
                            action_cols.append(c)

            # Cảnh báo gỡ lỗi tuyệt đối nếu vẫn "mù" cột
            if not action_cols:
                st.error(f"❌ Thuật toán không tìm thấy cột dữ liệu (Begin/End) nào cho hành động {action_str}.")
                st.warning(f"**Danh sách các cột đang có trong file Excel của ông là:** {', '.join([str(c) for c in df_day.columns])}")
                st.info("Ông vui lòng chụp màn hình cái khung báo lỗi này ném cho tôi, tôi sẽ chỉnh code khớp 100% với tên cột của ông ngay!")
                continue

            show_cols = [c for c in base_cols if c in df_day.columns] + action_cols
            df_display = df_day[['_actual_date', 'Date'] + show_cols].dropna(subset=action_cols, how='all').reset_index(drop=True)

            if df_display.empty:
                st.info(f"Không có khung giờ {action_str} cho ngày này.")
                continue

            styled_table = process_and_style_df(df_display, show_past_dates=True)
            col_cfg = {
                "Dir": st.column_config.TextColumn("Dir", width=35),
                "Level": st.column_config.TextColumn("Lvl", width=35),
                "Slack": st.column_config.TextColumn("Slk", width=40),
                "VungTau": st.column_config.TextColumn("VT", width=40)
            }
            for c in action_cols:
                short_name = str(c).replace("Begin ", "B.").replace("End ", "E.").replace("Starboard", "S").replace("Port", "P").replace("-Stb", "-S")
                col_cfg[c] = st.column_config.TextColumn(short_name, width=50)

            st.dataframe(styled_table, use_container_width=True, hide_index=True, column_config=col_cfg, column_order=['Date'] + show_cols)

            valid_df = styled_table.data
            day_draft_values = set()
            windows_render_list = []

            for idx, row in valid_df.iterrows():
                times = []
                for c in action_cols:
                    val = row.get(c)
                    if pd.notna(val) and str(val).strip() not in ["", "nan"]:
                        vs = str(val).strip().replace(".", ":").replace(" ", ":").replace(",", ":")
                        try:
                            if vs.startswith("24:"): t = datetime.time(23, 59, 59)
                            else:
                                parts = vs.split(":")
                                t = datetime.time(int(parts[0]), int(parts[1][:2]))
                            times.append(datetime.datetime.combine(d, t))
                        except: pass

                if not times: continue
                times.sort()

                corrected_times = []
                max_t = times[-1]
                for t_dt in times:
                    if (max_t - t_dt).total_seconds() > 12 * 3600:
                        corrected_times.append(t_dt + datetime.timedelta(days=1))
                    else: corrected_times.append(t_dt)

                min_dt, max_dt = min(corrected_times), max(corrected_times)
                start_m = (min_dt.minute // 30) * 30
                curr = min_dt.replace(minute=start_m, second=0, microsecond=0)
                block_end = max_dt

                blocks_data = []
                depth = float(config.get("cm", 14.0))

                while curr <= block_end:
                    tide = get_tide_at_eta(db, "CM", curr)
                    if tide is not None:
                        draft_val = round((tide + depth) / 1.10, 1)
                        day_draft_values.add(draft_val)
                        blocks_data.append((curr, draft_val))
                    curr += datetime.timedelta(minutes=30)

                if blocks_data:
                    windows_render_list.append({"min": min_dt, "max": max_dt, "data": blocks_data})

            if day_draft_values:
                sorted_v = sorted(list(day_draft_values))
                st.markdown(f"<div class='cm-summary-box'>📌 Mớn nước trong ngày {d.strftime('%d/%m/%Y')} "
                            f"lớn nhất là: <b>{', '.join([f'{v:.1f}' for v in sorted_v[-3:][::-1]])}m</b>, "
                            f"nhỏ nhất là: <b>{', '.join([f'{v:.1f}' for v in sorted_v[:3]])}m</b><br>"
                            f"<i>(Chỉ hiển thị các mớn ≤ 15.0m)</i></div>", unsafe_allow_html=True)

            for w in windows_render_list:
                filtered = [item for item in w["data"] if item[1] <= 15.0]
                if not filtered:
                    st.info(f"🚫 Window {w['min'].strftime('%H:%M')} ➔ {w['max'].strftime('%H:%M')} không có mớn ≤ 15.0m.")
                    continue

                st.markdown(f"<div class='cm-window-title'>Bảng mớn nước tàu {action_str} cho window: {w['min'].strftime('%H:%M')} ➔ {w['max'].strftime('%H:%M')}</div>", unsafe_allow_html=True)

                CHUNK_SIZE = 12
                for i in range(0, len(filtered), CHUNK_SIZE):
                    chunk = filtered[i:i+CHUNK_SIZE]
                    df_chunk = pd.DataFrame([{ (b[0].strftime('%H:%M') + (" (+1)" if b[0].date() > d else "")): f"{b[1]:.1f}" for b in chunk }])
                    st.dataframe(df_chunk.style.set_table_styles([
                        {'selector': 'th', 'props': [('background-color', '#ffe699 !important'), ('color', '#111 !important'), ('text-align', 'center !important')]},
                        {'selector': 'td', 'props': [('text-align', 'center !important'), ('font-weight', 'bold'), ('color', '#1E90FF !important'), ('font-size', '15px !important')]}
                    ]), use_container_width=True, hide_index=True)

    st.markdown("<br><div style='height: 40px;'></div>", unsafe_allow_html=True)
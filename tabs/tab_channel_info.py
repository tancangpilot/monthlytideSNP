import streamlit as st
import pandas as pd
import os
import io

def load_channel_data():
    possible_files = ["data_channel.xlsx", "Channel_Infor.xlsx", "data_channel.csv", "data_channel.xlxs"]
    target_file = None
    for f in possible_files:
        if os.path.exists(f):
            target_file = f
            break
    if not target_file: return pd.DataFrame()
    try:
        temp_df = pd.read_excel(target_file, header=None, nrows=20)
        start_row = 0
        for i, row in temp_df.iterrows():
            row_str = " ".join([str(val).lower() for val in row.values])
            if "độ sâu" in row_str or "tuyến luồng" in row_str:
                start_row = i
                break
        df = pd.read_excel(target_file, skiprows=start_row)
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all').fillna("")
    except: return pd.DataFrame()

def render_channel_info_tab():
    st.markdown("""<style>.block-container { padding-top: 1rem !important; } .stSelectbox { margin-bottom: -15px !important; }</style>""", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: center; color: #1E90FF; margin-top: -20px;'> THÔNG TIN TUYẾN LUỒNG-CẦU CẢNG-BẾN PHAO</h3>", unsafe_allow_html=True)
    
    df = load_channel_data()
    if df.empty: return

    group_col = df.columns[0]
    channels = [c for c in df[group_col].unique().tolist() if str(c).strip() != ""] 
    col1, col2 = st.columns([1, 2])
    with col1: selected_channel = st.selectbox("Lọc", ["Tất cả"] + channels, label_visibility="collapsed")
    
    display_df = df[df[group_col] == selected_channel].copy() if selected_channel != "Tất cả" else df.copy()
    
    # Chuẩn bị dữ liệu hiển thị
    orig_group_series = display_df[group_col].copy()
    is_new_series = orig_group_series != orig_group_series.shift(1)
    display_df.loc[~is_new_series, group_col] = ""

    # Ép định dạng số
    numeric_cols = ["toàn tuyến", "tĩnh không", "độ sâu", "bề rộng"]
    for col in display_df.columns:
        c_lower = str(col).lower()
        if "độ sâu" in c_lower:
            display_df[col] = pd.to_numeric(display_df[col], errors='coerce').apply(lambda x: f"-{x:.1f}" if pd.notna(x) else "")
        elif any(x in c_lower for x in numeric_cols):
            display_df[col] = pd.to_numeric(display_df[col], errors='coerce').apply(lambda x: f"{x:.1f}" if pd.notna(x) else "")

    def style_row(row):
        idx = row.name
        grp = str(orig_group_series.loc[idx]).lower()
        is_new = is_new_series.loc[idx]
        
        # --- BỘ MÃ MÀU CHỮ THEO CỤM ---
        text_color = "#333" # Mặc định xám đen
        if 'vũng tàu' in grp or 'thị vải' in grp: text_color = "#0056b3" # Blue đậm
        elif 'sài gòn' in grp: text_color = "#1e7e34" # Green đậm
        elif 'đồng nai' in grp: text_color = "#a0522d" # Brown/Sienna
        elif 'soài rạp' in grp: text_color = "#6f42c1" # Purple
        
        # Nền nhạt để dễ phân biệt
        bg_color = "white"
        if is_new: border_top = "2px solid #000"
        else: border_top = "1px solid #ddd"

        styles = []
        for col_name, val in row.items():
            c_low = str(col_name).lower()
            cell_style = f"background-color: {bg_color}; border-top: {border_top}; border-bottom: 1px solid #ddd; font-size: 18px;"
            
            # Áp dụng màu chữ theo nhóm cho cột Tên tuyến và Đoạn luồng
            if c_low == group_col.lower() or any(x in c_low for x in ["đoạn luồng", "điểm cạn", "cầu", "bến"]):
                cell_style += f" color: {text_color}; font-weight: bold;"
            # Cột Độ sâu luôn màu đỏ
            elif 'độ sâu' in c_low and str(val).strip() != "":
                cell_style += " color: #d93025; font-weight: bold;"
            else:
                cell_style += " color: #333;" # Các cột số liệu khác giữ màu trung tính
                
            styles.append(cell_style)
        return styles

    styler = display_df.style.apply(style_row, axis=1)
    st.dataframe(styler, use_container_width=False, hide_index=True, height=850)
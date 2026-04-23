import streamlit as st
import pandas as pd
import os
from streamlit_gsheets import GSheetsConnection

@st.cache_data(show_spinner=False)
def load_channel_data():
    try:
        # 1. KẾT NỐI VỚI GOOGLE SHEETS
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        # 2. ĐỌC DỮ LIỆU THÔ ĐỂ TÌM TIÊU ĐỀ (Giữ nguyên logic cực hay của ông)
        # Đọc không lấy tiêu đề để dò tìm start_row
        temp_df = conn.read(worksheet="Channel_Infor", header=None, ttl="10m") 
        
        start_row = 0
        for i, row in temp_df.head(20).iterrows(): # Quét 20 dòng đầu
            row_str = " ".join([str(val).lower() for val in row.values])
            if "độ sâu" in row_str or "tuyến luồng" in row_str or "điểm cạn" in row_str:
                start_row = i
                break
        
        # 3. ĐỌC LẠI DỮ LIỆU CHUẨN SAU KHI ĐÃ TÌM ĐƯỢC DÒNG TIÊU ĐỀ
        df = conn.read(worksheet="Channel_Infor", skiprows=start_row, ttl="10m")
        df.columns = [str(c).strip() for c in df.columns]
        return df.dropna(how='all').fillna("")
    except Exception as e:
        st.error(f"❌ Lỗi kết nối dữ liệu Cloud: {e}")
        return pd.DataFrame()

def render_channel_info_tab():
    # CSS thu hẹp khoảng cách sát banner
    st.markdown("""<style>.block-container { padding-top: 1rem !important; }</style>""", unsafe_allow_html=True)
    st.markdown("<h3 style='text-align: left; margin-left: 10px; color: #1E90FF; margin-top: -20px;'>THÔNG TIN TUYẾN LUỒNG - CẦU CẢNG - BẾN PHAO</h3>", unsafe_allow_html=True)
    
    df = load_channel_data()
    if df.empty:
        st.warning("⚠️ Không tìm thấy dữ liệu từ Cloud hoặc lỗi kết nối.")
        return

    # --- KHÔNG DÙNG DROPBOX LỌC - HIỆN BẢNG TỔNG ---
    display_df = df.copy()
    group_col = display_df.columns[0]
    
    # Chuẩn bị logic gom nhóm (giấu tên tuyến lặp lại)
    orig_group_series = display_df[group_col].copy()
    is_new_series = orig_group_series != orig_group_series.shift(1)
    display_df.loc[~is_new_series, group_col] = ""

    # Ép định dạng số cho các cột đo đạc (Bỏ qua cột Số TBHH vì nó là text)
    numeric_measure_cols = ["toàn tuyến", "tĩnh không", "độ sâu", "bề rộng"]
    for col in display_df.columns:
        c_lower = str(col).lower()
        if "độ sâu" in c_lower:
            display_df[col] = pd.to_numeric(display_df[col], errors='coerce').apply(lambda x: f"-{x:.1f}" if pd.notna(x) else "")
        elif any(x in c_lower for x in numeric_measure_cols):
            # Chỉ ép kiểu số cho các cột đo đạc, Số TBHH sẽ giữ nguyên định dạng text
            display_df[col] = pd.to_numeric(display_df[col], errors='coerce').apply(lambda x: f"{x:.1f}" if pd.notna(x) else "")

    def style_row(row):
        idx = row.name
        grp = str(orig_group_series.loc[idx]).lower()
        is_new = is_new_series.loc[idx]
        
        # --- MÀU CHỮ THEO CỤM ---
        text_color = "#333" 
        if any(x in grp for x in ['vũng tàu', 'thị vải', 'vt']): text_color = "#0056b3"
        elif 'sài gòn' in grp: text_color = "#1e7e34"
        elif 'đồng nai' in grp: text_color = "#a0522d"
        elif 'soài rạp' in grp: text_color = "#6f42c1"
        
        # Kẻ đường biên phân cách các cụm tuyến cho rõ ràng
        border_top = "2px solid #555" if is_new else "1px solid #ddd"

        styles = []
        for col_name, val in row.items():
            c_low = str(col_name).lower()
            # Style cơ bản
            cell_style = f"background-color: white; border-top: {border_top}; border-bottom: 1px solid #ddd; font-size: 18px;"
            
            # 1. Cột Tên tuyến, Đoạn luồng, Cầu cảng: Màu theo cụm + In đậm
            if c_low == group_col.lower() or any(x in c_low for x in ["đoạn luồng", "điểm cạn", "cầu", "bến", "phao"]):
                cell_style += f" color: {text_color}; font-weight: bold;"
            
            # 2. Cột Độ sâu: Luôn màu đỏ rực
            elif 'độ sâu' in c_low and str(val).strip() != "":
                cell_style += " color: #d93025; font-weight: bold;"
            
            # 3. Các cột khác (Số TBHH, Ghi chú...): Màu xám đen trung tính
            else:
                cell_style += " color: #333;"
                
            styles.append(cell_style)
        return styles

    # Áp dụng Style
    styler = display_df.style.apply(style_row, axis=1)
    
    # Hiển thị bảng. use_container_width=False giúp các cột tự co giãn khít theo chữ
    st.dataframe(styler, use_container_width=False, hide_index=True, height=900)
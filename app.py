import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# ==========================================
# CẤU HÌNH TRANG WEB
# ==========================================
st.set_page_config(page_title="Tidal & Route Planning", layout="wide")
st.title("⚓ Ứng dụng Quản lý Thủy triều & Cửa sổ")

DATA_FILE_PATH = "tide_data_current.xlsx"

# ==========================================
# 1. CÁC HÀM XỬ LÝ VÀ ĐỊNH DẠNG DỮ LIỆU
# ==========================================

def format_hhmm(val):
    if pd.isna(val): return val
    val_str = str(val).strip().replace(';', ':') 
    if ':' in val_str:
        parts = val_str.split(':')
        if len(parts) >= 2 and parts[0].isdigit():
            return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    return val_str

def process_tide_window(df):
    df.columns = df.columns.astype(str).str.strip()
    df = df.dropna(axis=1, how='all')
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Date'] = df['Date'].ffill().dt.strftime('%d/%m')
        
    time_col = 'Time Vung Tau' if 'Time Vung Tau' in df.columns else df.columns[1]
    df = df.dropna(subset=[time_col])
    
    skip_cols = ['Date', 'Level', 'Tide_Height', 'Dir', 'Direction', 'Sign', 'Slack Time', 'Slack_Water']
    for col in df.columns:
        if col not in skip_cols:
            df[col] = df[col].apply(format_hhmm)
            
    return df

def apply_advanced_style(df, tab_type):
    """Hàm tô màu siêu tùy biến với thuật toán tàng hình Index"""
    df_display = df.copy()
    
    # BƯỚC 1: FIX CỘT TRÙNG LẶP (Đảm bảo không có cột nào trùng tên)
    seen_cols = {}
    unique_cols = []
    for c in df_display.columns:
        if c in seen_cols:
            seen_cols[c] += 1
            unique_cols.append(f"{c}{' ' * seen_cols[c]}") # Thêm khoảng trắng để unique
        else:
            seen_cols[c] = 0
            unique_cols.append(c)
    df_display.columns = unique_cols

    # BƯỚC 2: FIX INDEX TRÙNG LẶP
    if 'Date' in df_display.columns:
        is_first_of_day = ~df_display['Date'].duplicated()
        
        unique_dates = []
        space_counter = 1
        for i in range(len(df_display)):
            if is_first_of_day.iloc[i]:
                unique_dates.append(str(df_display['Date'].iloc[i]))
            else:
                # Mỗi ngày trùng sẽ nhận số lượng khoảng trắng tăng dần -> Độc nhất 100%
                unique_dates.append(" " * space_counter)
                space_counter += 1
                
        df_display['Date'] = unique_dates
        df_display = df_display.set_index('Date') # Bây giờ Set Index sẽ không báo lỗi nữa!
    else:
        is_first_of_day = pd.Series([False] * len(df_display))

    def style_cells(data):
        styles = pd.DataFrame('', index=data.index, columns=data.columns)
        
        for i in range(len(data.index)):
            is_first = is_first_of_day.iloc[i]
            base_style = 'border-top: 2px solid #666; font-weight: bold;' if is_first else 'border-top: 1px solid #ddd;'
            
            for j, col in enumerate(data.columns):
                bg_color = ''
                if 'Time' in col:
                    if is_first: bg_color = 'background-color: rgba(100, 150, 255, 0.2);'
                elif tab_type == 'CL':
                    if 'Port' in col: bg_color = 'background-color: rgba(255, 99, 71, 0.2);' 
                    elif 'Stbd' in col: bg_color = 'background-color: rgba(60, 179, 113, 0.2);' 
                elif tab_type == 'CM':
                    if 'UB ' in col and 'Port' in col: bg_color = 'background-color: rgba(255, 99, 71, 0.15);' 
                    elif 'UB ' in col and 'Stbd' in col: bg_color = 'background-color: rgba(60, 179, 113, 0.15);' 
                    elif 'B ' in col and 'Port' in col: bg_color = 'background-color: rgba(255, 99, 71, 0.35);' 
                    elif 'B ' in col and 'Stbd' in col: bg_color = 'background-color: rgba(60, 179, 113, 0.35);' 
                        
                styles.iloc[i, j] = f"{base_style} {bg_color}".strip()
        return styles

    styler = df_display.style.apply(style_cells, axis=None)
    styler.set_table_styles([
        {'selector': 'th', 'props': [('white-space', 'pre-wrap'), ('text-align', 'center'), ('vertical-align', 'bottom')]},
        {'selector': 'td', 'props': [('text-align', 'center')]}
    ])
    return styler

def save_uploaded_file(uploadedfile):
    with open(DATA_FILE_PATH, "wb") as f:
        f.write(uploadedfile.getbuffer())
    st.success("✅ Đã lưu file mới lên hệ thống thành công!")
    st.rerun()

# ==========================================
# 2. LOGIC TẢI FILE & QUẢN LÝ DỮ LIỆU
# ==========================================

with st.sidebar:
    st.header("⚙️ Quản lý Dữ liệu")
    if os.path.exists(DATA_FILE_PATH):
        st.success("Đang dùng dữ liệu hệ thống.")
        with st.expander("🔄 Cập nhật tháng mới"):
            new_file = st.file_uploader("Tải file Excel lên để ghi đè", type=['xlsx'])
            if new_file is not None: save_uploaded_file(new_file)
    else:
        st.warning("Chưa có dữ liệu.")
        uploaded_file = st.file_uploader("📂 Tải file Excel lần đầu", type=['xlsx'])
        if uploaded_file is not None: save_uploaded_file(uploaded_file)

# ==========================================
# 3. GIAO DIỆN HIỂN THỊ CÁC TAB
# ==========================================

tab_cl, tab_cm, tab_calc = st.tabs(["CÁT LÁI", "CÁI MÉP", "Tide Calc"])

if os.path.exists(DATA_FILE_PATH):
    try:
        xls = pd.ExcelFile(DATA_FILE_PATH)
        
        # --- TAB 1: CÁT LÁI ---
        with tab_cl:
            if "WindowCL" in xls.sheet_names:
                raw_df_cl = pd.read_excel(xls, sheet_name="WindowCL")
                clean_df_cl = process_tide_window(raw_df_cl)
                
                cl_cols = []
                for c in clean_df_cl.columns:
                    if 'Port' in c: cl_cols.append("Port\n(Start)" if 'Begin' in c else "Port\n(End)")
                    elif 'Starboard' in c or 'Stbd' in c: cl_cols.append("Stbd\n(Start)" if 'Begin' in c else "Stbd\n(End)")
                    elif 'Slack' in c: cl_cols.append("Slack\nTime")
                    elif 'Time' in c: cl_cols.append("Time\nVT")
                    elif 'Level' in c or 'Height' in c: cl_cols.append("Triều\n(m)")
                    else: cl_cols.append(c)
                clean_df_cl.columns = cl_cols
                    
                styled_cl = apply_advanced_style(clean_df_cl, tab_type='CL')
                st.dataframe(styled_cl)
            else: st.warning("⚠️ Không tìm thấy sheet 'WindowCL'.")

        # --- TAB 2: CÁI MÉP ---
        with tab_cm:
            if "WindowCM" in xls.sheet_names:
                raw_df_cm = pd.read_excel(xls, sheet_name="WindowCM")
                clean_df_cm = process_tide_window(raw_df_cm)
                
                cm_cols = []
                for c in clean_df_cm.columns:
                    if 'Unberthing' in c:
                        if 'Begin' in c: cm_cols.append("UB Port\n(Start)" if 'Port' in c else "UB Stbd\n(Start)")
                        else: cm_cols.append("UB Port\n(End)" if 'Port' in c else "UB Stbd\n(End)")
                    elif 'Berthing' in c:
                        if 'Begin' in c: cm_cols.append("B Port\n(Start)" if 'Port' in c else "B Stbd\n(Start)")
                        else: cm_cols.append("B Port\n(End)" if 'Port' in c else "B Stbd\n(End)")
                    elif 'Slack' in c: cm_cols.append("Slack\nTime")
                    elif 'Time' in c: cm_cols.append("Time\nVT")
                    elif 'Level' in c or 'Height' in c: cm_cols.append("Triều\n(m)")
                    else: cm_cols.append(c)
                clean_df_cm.columns = cm_cols
                
                styled_cm = apply_advanced_style(clean_df_cm, tab_type='CM')
                st.dataframe(styled_cm)
            else: st.warning("⚠️ Không tìm thấy sheet 'WindowCM'.")
                
        # --- TAB 3: TIDE CALC ---
        with tab_calc:
            st.info("Khu vực tính toán Draft và UKC đang được bảo trì phần giao diện...")
            
    except Exception as e:
        st.error(f"Đã xảy ra lỗi: {e}")
else:
    st.info("👈 Hãy tải file Excel lên qua cột điều khiển bên trái để bắt đầu.")

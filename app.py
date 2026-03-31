import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta

# ==========================================
# CẤU HÌNH TRANG WEB
# ==========================================
st.set_page_config(page_title="Tidal & Route Planning", layout="wide")
st.title("⚓ Ứng dụng Quản lý Thủy triều & Cửa sổ Hành hải")

# Đường dẫn lưu file cố định trên server
DATA_FILE_PATH = "tide_data_current.xlsx"

# ==========================================
# 1. CÁC HÀM XỬ LÝ VÀ ĐỊNH DẠNG DỮ LIỆU
# ==========================================

def format_hhmm(val):
    """Hàm chuẩn hóa thời gian về định dạng hh:mm"""
    if pd.isna(val):
        return val
    val_str = str(val).strip().replace(';', ':') # Sửa lỗi gõ nhầm ; thành :
    
    # Nếu có dấu : và phần trước nó là số (loại trừ chữ như Duty Pilot)
    if ':' in val_str:
        parts = val_str.split(':')
        if len(parts) >= 2 and parts[0].isdigit():
            return f"{parts[0].zfill(2)}:{parts[1].zfill(2)}"
    return val_str

def process_tide_window(df):
    """Hàm làm sạch chung cho cả Cát Lái và Cái Mép"""
    # Ép kiểu tên cột thành chuỗi, xóa khoảng trắng thừa
    df.columns = df.columns.astype(str).str.strip()
    
    # Xóa các cột rỗng hoàn toàn và cột rác (Unnamed)
    df = df.dropna(axis=1, how='all')
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    # Xử lý chuẩn hóa cột Date
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Date'] = df['Date'].ffill().dt.strftime('%Y-%m-%d')
        
    # Lọc bỏ dòng phân cách dựa vào cột thời gian (Ưu tiên 'Time Vung Tau' hoặc lấy cột thứ 2)
    time_col = 'Time Vung Tau' if 'Time Vung Tau' in df.columns else df.columns[1]
    df = df.dropna(subset=[time_col])
    
    # Ép định dạng hh:mm cho các cột thời gian (Bỏ qua các cột chứa chữ, số, mức triều...)
    skip_cols = ['Date', 'Level', 'Tide_Height', 'Dir', 'Direction', 'Sign', 'Slack Time', 'Slack_Water']
    for col in df.columns:
        if col not in skip_cols:
            df[col] = df[col].apply(format_hhmm)
            
    return df

def apply_custom_style(df):
    """Hàm áp dụng Style: Ẩn ngày trùng & Highlight dòng đầu tiên của ngày"""
    if 'Date' not in df.columns:
        return df
        
    # Xác định các dòng là dòng đầu tiên của một ngày mới
    is_first_of_day = ~df['Date'].duplicated()
    
    # Tạo bản sao để can thiệp hiển thị (không làm hỏng data gốc)
    df_display = df.copy()
    
    # Xóa nội dung (để chuỗi rỗng) ở các dòng bị trùng ngày
    df_display.loc[~is_first_of_day, 'Date'] = ''
    
    # Hàm tô màu dòng
    def highlight_row(row):
        # Nếu là dòng đầu tiên của ngày -> tô nền xanh nhạt, in đậm
        if is_first_of_day.loc[row.name]:
            return ['background-color: rgba(100, 150, 255, 0.2); font-weight: bold'] * len(row)
        return [''] * len(row)
        
    # Trả về đối tượng Styler của Pandas
    return df_display.style.apply(highlight_row, axis=1)

def save_uploaded_file(uploadedfile):
    """Lưu file Excel vật lý lên server"""
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
            if new_file is not None:
                save_uploaded_file(new_file)
    else:
        st.warning("Chưa có dữ liệu.")
        uploaded_file = st.file_uploader("📂 Tải file Excel lần đầu", type=['xlsx'])
        if uploaded_file is not None:
            save_uploaded_file(uploaded_file)

# ==========================================
# 3. GIAO DIỆN HIỂN THỊ CÁC TAB
# ==========================================

tab_cl, tab_cm, tab_calc = st.tabs(["CÁT LÁI (WindowCL)", "CÁI MÉP (WindowCM)", "Tide Calc"])

if os.path.exists(DATA_FILE_PATH):
    try:
        xls = pd.ExcelFile(DATA_FILE_PATH)
        
        # --- TAB 1: CÁT LÁI ---
        with tab_cl:
            if "WindowCL" in xls.sheet_names:
                st.subheader("Bảng Giờ Cửa Sổ - Cát Lái")
                raw_df_cl = pd.read_excel(xls, sheet_name="WindowCL") # Đã bỏ skiprows và header=None
                clean_df_cl = process_tide_window(raw_df_cl)
                styled_cl = apply_custom_style(clean_df_cl)
                st.dataframe(styled_cl, use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Không tìm thấy sheet 'WindowCL'.")

        # --- TAB 2: CÁI MÉP ---
        with tab_cm:
            if "WindowCM" in xls.sheet_names:
                st.subheader("Bảng Giờ Cửa Sổ - Cái Mép")
                raw_df_cm = pd.read_excel(xls, sheet_name="WindowCM")
                clean_df_cm = process_tide_window(raw_df_cm)
                styled_cm = apply_custom_style(clean_df_cm)
                st.dataframe(styled_cm, use_container_width=True, hide_index=True)
            else:
                st.warning("⚠️ Không tìm thấy sheet 'WindowCM'.")
                
        # --- TAB 3: TIDE CALC (Dự thảo tính toán Draft & POB) ---
        with tab_calc:
            st.subheader("Tính toán Thủy triều & Draft (Tide Calc)")
            
            direction = st.radio("Hướng hành trình:", ["Tuyến đi vào (Inbound)", "Tuyến đi ra (Outbound)"], horizontal=True)
            
            # TODO: Cập nhật lại Dictionary các tuyến từ dự án cũ của bạn vào đây
            routes_dict = {
                "Tuyến đi vào (Inbound)": {
                    "P0 Vũng Tàu - Cát Lái": {"VL": 0.0, "HL6": 1.5, "HL27": 2.5},
                    "P0 Vũng Tàu - Cái Mép": {"VL": 0.0, "TCHP": 1.0}
                },
                "Tuyến đi ra (Outbound)": {
                    "Cát Lái - Soài Rạp (Bờ Băng) - P0 SR (H25)": {"BB": 1.0, "VL": 2.5},
                    "Cát Lái - Vũng Tàu": {"HL27": 0.5, "HL6": 1.5, "VL": 3.0},
                    "Cái Mép - P0 Vũng Tàu": {"TCHP": 0.5, "VL": 1.5}
                }
            }
            
            selected_route_name = st.selectbox("Chọn tuyến:", list(routes_dict[direction].keys()))
            choke_points = routes_dict[direction][selected_route_name]
            
            st.markdown("##### Đánh giá thời gian tới điểm cạn (POB & Draft)")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                pob_date = st.date_input("Ngày POB:")
            with col2:
                time_blocks = [f"{str(h).zfill(2)}:{str(m).zfill(2)}" for h in range(24) for m in (0, 30)]
                pob_time_str = st.selectbox("Giờ POB:", time_blocks)
            with col3:
                vessel_draft = st.number_input("Draft tàu (m):", min_value=0.0, step=0.1, value=10.0)
            with col4:
                default_ukc = 1.2 if "Cái Mép" in selected_route_name else 1.0
                ukc_margin = st.number_input("UKC yêu cầu (m):", min_value=0.0, step=0.1, value=default_ukc)

            if st.button("Tính toán lộ trình", type="primary"):
                pob_datetime = datetime.strptime(f"{pob_date} {pob_time_str}", "%Y-%m-%d %H:%M")
                
                results = []
                for point, hours_offset in choke_points.items():
                    eta_point = pob_datetime + timedelta(hours=hours_offset)
                    
                    # Placeholder cho giá trị thủy triều - Cần ráp code interpolate
                    tide_height = 3.5 
                    
                    chart_datum = -6.5
                    actual_depth = abs(chart_datum) + tide_height
                    clearance = actual_depth - vessel_draft
                    is_safe = "✅ An toàn" if clearance >= ukc_margin else "⚠️ Nguy hiểm"

                    results.append({
                        "Điểm cạn": point,
                        "Thời gian chạy": f"+{hours_offset}h",
                        "ETA": eta_point.strftime("%Y-%m-%d %H:%M"),
                        "Mực nước": f"{tide_height}m",
                        "Độ sâu tổng": f"{actual_depth}m",
                        "Clearance": f"{clearance:.2f}m",
                        "Đánh giá": is_safe
                    })
                    
                st.dataframe(pd.DataFrame(results), use_container_width=True, hide_index=True)
            
    except Exception as e:
        st.error(f"Đã xảy ra lỗi hệ thống khi đọc/hiển thị file: {e}")
        # Mở comment dòng dưới nếu muốn tự xóa file khi lỗi để upload lại từ đầu
        # os.remove(DATA_FILE_PATH) 
else:
    st.info("👈 Hãy tải file Excel lên qua cột điều khiển bên trái để bắt đầu.")
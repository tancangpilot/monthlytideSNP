import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta
from utils.config_manager import save_config
from streamlit_gsheets import GSheetsConnection

def render_admin_page(config):
    # --- 1. XÓA DẤU VẾT TRÊN URL ---
    if "tab" in st.query_params:
        del st.query_params["tab"]

    st.markdown("<h2 style='text-align: center; color: #1E90FF;'>⚙️ QUẢN TRỊ HỆ THỐNG</h2>", unsafe_allow_html=True)
    
    # --- 1. CẤU HÌNH UKC CHUNG ---
    st.markdown("#### 1️⃣ CẤU HÌNH UKC CHUNG")
    c_ukc1, c_ukc2, c_ukc_btn = st.columns([2, 2, 1])
    with c_ukc1:
        new_ukc_day = st.number_input("UKC Ban Ngày (%)", value=int(config.get('ukc_day', 7)))
    with c_ukc2:
        new_ukc_night = st.number_input("UKC Ban Đêm (%)", value=int(config.get('ukc_night', 10)))
    with c_ukc_btn:
        st.write(""); st.write("")
        if st.button("💾 LƯU UKC", use_container_width=True):
            config['ukc_day'] = new_ukc_day
            config['ukc_night'] = new_ukc_night
            vn_now = datetime.utcnow() + timedelta(hours=7)
            config["last_update"] = vn_now.strftime("%H:%M:%S ngày %d/%m/%Y")
            save_config(config)
            st.cache_data.clear() 
            st.success("✅ Đã lưu UKC!"); time.sleep(1); st.rerun()

    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)

    # ========================================================
    # MỞ KẾT NỐI GOOGLE SHEETS TỪ ĐÂY
    # ========================================================
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)

        # --------------------------------------------------------
        # BƯỚC TỐI ƯU API CỰC MẠNH: CHỈ ĐỌC 1 LẦN DUY NHẤT
        # Đặt ttl="5s" để tránh bị spam nếu lỡ tay bấm đúp chuột
        # --------------------------------------------------------
        raw_data = conn.read(worksheet="Channel_Infor", header=None, ttl="5s")
        
        # Xử lý dò tìm dòng tiêu đề ngay trên máy tính (không tốn API của Google)
        start_row = 0
        for i, row in raw_data.head(20).iterrows():
            row_str = " ".join([str(val).lower() for val in row.values])
            if any(x in row_str for x in ["độ sâu", "tuyến luồng", "cầu cảng"]):
                start_row = i; break
        
        # Cắt gọt dữ liệu thô thành bảng chuẩn
        df_main = raw_data.iloc[start_row+1:].copy()
        df_main.columns = [str(c).strip() for c in raw_data.iloc[start_row].values]
        df_main = df_main.reset_index(drop=True)
        df_structure = df_main.copy()
        # --------------------------------------------------------

        # --- 2. QUẢN LÝ CẤU TRÚC BẢNG ---
        st.markdown("#### 2️⃣ QUẢN LÝ CẤU TRÚC BẢNG (THÊM/XÓA CỘT)")
        col_add, col_del = st.columns(2)
        
        with col_add:
            new_col_name = st.text_input("Tên cột muốn THÊM (VD: Số TBHH)")
            if st.button("➕ Thêm cột mới"):
                if new_col_name and new_col_name not in df_structure.columns:
                    df_structure[new_col_name] = ""
                    conn.update(worksheet="Channel_Infor", data=df_structure)
                    st.cache_data.clear() 
                    st.success(f"✅ Đã thêm cột '{new_col_name}' lên Cloud")
                    time.sleep(1); st.rerun()
        
        with col_del:
            cols_can_delete = [c for c in df_structure.columns if c != df_structure.columns[0]]
            cols_to_remove = st.multiselect("Chọn cột muốn XÓA", options=cols_can_delete)
            if st.button("🗑️ Xóa cột đã chọn"):
                if cols_to_remove:
                    df_structure = df_structure.drop(columns=cols_to_remove)
                    conn.update(worksheet="Channel_Infor", data=df_structure)
                    st.cache_data.clear()
                    st.success("✅ Đã xóa cột trên Cloud thành công!"); time.sleep(1); st.rerun()

        st.info("""
            💡 **Note: Hướng dẫn quản lý dữ liệu**
            1. **Thứ tự:** Hệ thống giữ nguyên trình tự hải trình của ông. Điểm mới thêm sẽ nằm cuối Tuyến đó.
            2. **Đồng bộ:** Đoạn luồng chứa **(hl6), (hl21), (hl27), (vl), (tchp), (bb)** sẽ tự động cập nhật mớn nước.
            3. **Lỗi Lưu:** Đảm bảo không để trống ô ở cột đầu tiên (Tên tuyến luồng) khi thêm dòng mới.
        """)

        st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)

        # --- 3. CẬP NHẬT DỮ LIỆU ---
        st.markdown("#### 3️⃣ CẬP NHẬT DỮ LIỆU CHI TIẾT TRÊN CLOUD")
        st.markdown(f"""
            <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; border-left: 5px solid #1E90FF; margin-bottom: 15px; font-size: 14px;'>
                <b>📍 Độ sâu các điểm cạn đang sử dụng:</b> 
                HL6: <b>{config.get('hl6', 'N/A')}m</b> | HL21: <b>{config.get('hl21', 'N/A')}m</b> | HL27: <b>{config.get('hl27', 'N/A')}m</b> | 
                Vàm Láng: <b>{config.get('vl', 'N/A')}m</b> | TCHP: <b>{config.get('tchp', 'N/A')}m</b> | Bờ Băng: <b>{config.get('bb', 'N/A')}m</b>
            </div>
        """, unsafe_allow_html=True)

        group_col = df_main.columns[0]

        # Khóa kích thước cột
        numeric_cols = ["toàn tuyến", "tĩnh không", "độ sâu", "bề rộng"]
        explicit_config = {}
        for col in df_main.columns:
            c_low = col.lower()
            if any(x in c_low for x in numeric_cols):
                df_main[col] = pd.to_numeric(df_main[col], errors='coerce')
                explicit_config[col] = st.column_config.NumberColumn(col, width=100, format="%.1f")
            else:
                df_main[col] = df_main[col].astype(str).replace(['nan', 'None', 'NaN'], '')
                if "tuyến luồng" in c_low: explicit_config[col] = st.column_config.TextColumn(col, width=220)
                elif any(x in c_low for x in ["đoạn luồng", "điểm cạn", "cầu", "bến"]): explicit_config[col] = st.column_config.TextColumn(col, width=500)
                else: explicit_config[col] = st.column_config.TextColumn(col, width=150)

        # Bảng soạn thảo
        edited_df = st.data_editor(
            df_main,
            num_rows="dynamic",
            use_container_width=True,
            height=650,
            column_config=explicit_config
        )

        # --- NÚT LƯU ---
        if st.button("💾 LƯU BẢNG VÀ ĐỒNG BỘ LÊN CLOUD", type="primary", use_container_width=True):
            vn_now = datetime.utcnow() + timedelta(hours=7)
            current_date_str = vn_now.strftime("%d/%m/%Y")
            
            date_col = next((c for c in edited_df.columns if "ngày" in c.lower() or "nhật" in c.lower()), None)
            depth_col = next((c for c in edited_df.columns if "độ sâu" in c.lower()), None)
            point_col = next((c for c in edited_df.columns if any(x in c.lower() for x in ["điểm cạn", "đoạn luồng", "cầu"])), None)

            # 1. Cập nhật ngày tháng
            if date_col and depth_col:
                for idx in edited_df.index:
                    if idx in df_main.index:
                        if str(df_main.at[idx, depth_col]) != str(edited_df.at[idx, depth_col]):
                            edited_df.at[idx, date_col] = current_date_str
                    else: edited_df.at[idx, date_col] = current_date_str

            # 2. Xử lý gom nhóm và vá lỗi Null Categorical
            if not edited_df.empty:
                edited_df[group_col] = edited_df[group_col].replace('', pd.NA)
                edited_df = edited_df.dropna(subset=[group_col])
                
                route_order = [x for x in df_main[group_col].unique().tolist() if pd.notna(x) and str(x).strip() != ""]
                
                for r in edited_df[group_col].unique():
                    if r not in route_order and pd.notna(r) and str(r).strip() != "":
                        route_order.append(r)
                
                edited_df[group_col] = pd.Categorical(edited_df[group_col], categories=route_order, ordered=True)
                edited_df = edited_df.sort_values(by=[group_col], kind='mergesort')
                edited_df[group_col] = edited_df[group_col].astype(str)

            # 3. Đồng bộ độ sâu
            if depth_col and point_col:
                sync_map = {"(hl6)": "hl6", "(hl21)": "hl21", "(hl27)": "hl27", "(vl)": "vl", "(tchp)": "tchp", "(bb)": "bb"}
                for _, row in edited_df.iterrows():
                    p_name = str(row[point_col]).lower()
                    for k, cfg_key in sync_map.items():
                        if k in p_name:
                            try: config[cfg_key] = float(row[depth_col])
                            except: pass

            # 4. Ghi file LÊN GOOGLE SHEETS và Reload
            conn.update(worksheet="Channel_Infor", data=edited_df)
            
            config["last_update"] = vn_now.strftime("%H:%M:%S ngày %d/%m/%Y")
            save_config(config)
            st.cache_data.clear() 
            st.success(f"✅ Đã đồng bộ an toàn lên Google Sheets!")
            time.sleep(2.5); st.rerun()

        # ========================================================
        # PHẦN 4: CÔNG CỤ SIÊU NẠP TỰ ĐỘNG (ĐÃ GẮN PHANH AN TOÀN)
        # ========================================================
        st.markdown("<hr style='margin: 25px 0 15px 0;'>", unsafe_allow_html=True)
        st.markdown("#### 🚀 CÔNG CỤ SIÊU NẠP DỮ LIỆU TỰ ĐỘNG (TIDE & WINDOW)")
        st.info("💡 Ông kéo thả file `data_tide.xlsx` hoặc `data_window.xlsx` vào đây. Hệ thống sẽ tự tìm các Trạm và đẩy lên Cloud.")

        uploaded_file = st.file_uploader("Chọn file Excel để nạp lên Cloud:", type=["xlsx"], label_visibility="collapsed")

        if uploaded_file is not None:
            if st.button("📤 XÁC NHẬN ĐỒNG BỘ LÊN CLOUD", type="primary", use_container_width=True):
                # Dùng pd.ExcelFile để lấy được danh sách các Sheet bên trong
                xl = pd.ExcelFile(uploaded_file)
                sheet_names = xl.sheet_names
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, s_name in enumerate(sheet_names):
                    status_text.write(f"⏳ Đang xử lý trạm/bảng: **{s_name}**...")
                    
                    df_to_upload = pd.read_excel(uploaded_file, sheet_name=s_name)
                    
                    # Cập nhật lên Google Sheets
                    conn.update(worksheet=s_name, data=df_to_upload)
                    
                    progress_bar.progress((i + 1) / len(sheet_names))
                    
                    # PHANH AN TOÀN: Nghỉ 2 giây để Google không báo lỗi quá tải (Lỗi 429)
                    time.sleep(2)
                
                status_text.empty()
                st.cache_data.clear() 
                st.success(f"✅ Đã nạp thành công {len(sheet_names)} trạm/bảng lên Cloud vĩnh viễn!")
                st.balloons() 

        st.markdown("<div style='height: 250px;'></div>", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Lỗi kết nối Google Sheets: {e}")
import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from utils.config_manager import save_config

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
            st.cache_data.clear() # <--- THÊM DÒNG NÀY ĐỂ XẢ CACHE
            st.success("✅ Đã lưu UKC!"); time.sleep(1); st.rerun()

    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)

    # --- 2. QUẢN LÝ CẤU TRÚC BẢNG ---
    st.markdown("#### 2️⃣ QUẢN LÝ CẤU TRÚC BẢNG (THÊM/XÓA CỘT)")
    possible_files = ["data_channel.xlsx", "Channel_Infor.xlsx"]
    file_excel = next((f for f in possible_files if os.path.exists(f)), None)
    
    if file_excel:
        try:
            df_structure = pd.read_excel(file_excel)
            col_add, col_del = st.columns(2)
            
            with col_add:
                new_col_name = st.text_input("Tên cột muốn THÊM (VD: Số TBHH)")
                if st.button("➕ Thêm cột mới"):
                    if new_col_name and new_col_name not in df_structure.columns:
                        df_structure[new_col_name] = ""
                        df_structure.to_excel(file_excel, index=False)
                        st.success(f"✅ Đã thêm cột '{new_col_name}'")
                        time.sleep(1); st.rerun()
            
            with col_del:
                cols_can_delete = [c for c in df_structure.columns if c != df_structure.columns[0]]
                cols_to_remove = st.multiselect("Chọn cột muốn XÓA", options=cols_can_delete)
                if st.button("🗑️ Xóa cột đã chọn"):
                    if cols_to_remove:
                        df_structure = df_structure.drop(columns=cols_to_remove)
                        df_structure.to_excel(file_excel, index=False)
                        st.success("✅ Đã xóa cột thành công!"); time.sleep(1); st.rerun()

            st.info("""
                💡 **Note: Hướng dẫn quản lý dữ liệu**
                1. **Thứ tự:** Hệ thống giữ nguyên trình tự hải trình của ông. Điểm mới thêm sẽ nằm cuối Tuyến đó.
                2. **Đồng bộ:** Đoạn luồng chứa **(hl6), (hl21), (hl27), (vl), (tchp), (bb)** sẽ tự động cập nhật mớn nước.
                3. **Lỗi Lưu:** Đảm bảo không để trống ô ở cột đầu tiên (Tên tuyến luồng) khi thêm dòng mới.
            """)

            st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)

            # --- 3. CẬP NHẬT DỮ LIỆU ---
            st.markdown("#### 3️⃣ CẬP NHẬT DỮ LIỆU CHI TIẾT")
            st.markdown(f"""
                <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; border-left: 5px solid #1E90FF; margin-bottom: 15px; font-size: 14px;'>
                    <b>📍 Độ sâu các điểm cạn đang sử dụng:</b> 
                    HL6: <b>{config.get('hl6', 'N/A')}m</b> | HL21: <b>{config.get('hl21', 'N/A')}m</b> | HL27: <b>{config.get('hl27', 'N/A')}m</b> | 
                    Vàm Láng: <b>{config.get('vl', 'N/A')}m</b> | TCHP: <b>{config.get('tchp', 'N/A')}m</b> | Bờ Băng: <b>{config.get('bb', 'N/A')}m</b>
                </div>
            """, unsafe_allow_html=True)

            # Đọc dữ liệu
            temp_df = pd.read_excel(file_excel, header=None, nrows=10)
            start_row = 0
            for i, row in temp_df.iterrows():
                row_str = " ".join([str(val).lower() for val in row.values])
                if any(x in row_str for x in ["độ sâu", "tuyến luồng", "cầu cảng"]):
                    start_row = i; break
            
            df_main = pd.read_excel(file_excel, skiprows=start_row)
            df_main.columns = [str(c).strip() for c in df_main.columns]
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

            # --- NÚT LƯU (ĐÃ VÁ LỖI NULL CATEGORIES) ---
            if st.button("💾 LƯU BẢNG VÀ ĐỒNG BỘ ĐỘ SÂU", type="primary", use_container_width=True):
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
                    # Dọn dẹp: xóa dòng hoàn toàn trống hoặc rỗng tên tuyến
                    edited_df[group_col] = edited_df[group_col].replace('', pd.NA)
                    edited_df = edited_df.dropna(subset=[group_col])
                    
                    # Lấy danh sách tuyến luồng cũ làm chuẩn (loại bỏ các giá trị null)
                    route_order = [x for x in df_main[group_col].unique().tolist() if pd.notna(x) and str(x).strip() != ""]
                    
                    # Thêm các tuyến mới vào cuối danh sách chuẩn
                    for r in edited_df[group_col].unique():
                        if r not in route_order and pd.notna(r) and str(r).strip() != "":
                            route_order.append(r)
                    
                    # Thực hiện gom nhóm an toàn
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

                # 4. Ghi file và Reload
                edited_df.to_excel(file_excel, index=False)
                config["last_update"] = vn_now.strftime("%H:%M:%S ngày %d/%m/%Y")
                save_config(config)
                st.cache_data.clear() # <--- THÊM DÒNG NÀY ĐỂ XẢ CACHE
                st.success(f"✅ Đã lưu dữ liệu thành công!")
                time.sleep(2.5); st.rerun()

            st.markdown("<div style='height: 250px;'></div>", unsafe_allow_html=True)

        except Exception as e:
            st.error(f"❌ Lỗi hệ thống: {e}")
    else:
        st.warning("⚠️ Không tìm thấy file Excel dữ liệu.")
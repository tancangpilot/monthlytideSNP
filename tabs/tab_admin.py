import streamlit as st
import pandas as pd
import os
import time
from datetime import datetime, timedelta
from utils.config_manager import save_config

def render_admin_page(config):
    # --- DÒNG MỚI THÊM: XÓA DẤU VẾT TRÊN URL ---
    if "tab" in st.query_params:
        del st.query_params["tab"]
    # ------------------------------------------
    st.markdown("<h2 style='text-align: center; color: #1E90FF;'>⚙️ QUẢN TRỊ HỆ THỐNG</h2>", unsafe_allow_html=True)
    
    # --- 1. ĐƯA UKC RA MẶT TIỀN (Không giấu trong Tab nữa) ---
    st.markdown("#### 1️⃣ CẤU HÌNH UKC CHUNG")
    c_ukc1, c_ukc2, c_ukc_btn = st.columns([2, 2, 1])
    with c_ukc1:
        new_ukc_day = st.number_input("UKC Ban Ngày (%)", value=int(config.get('ukc_day', 7)))
    with c_ukc2:
        new_ukc_night = st.number_input("UKC Ban Đêm (%)", value=int(config.get('ukc_night', 10)))
    with c_ukc_btn:
        st.write("") # Dòng trống để đẩy nút bấm xuống ngang hàng với ô nhập liệu
        st.write("")
        if st.button("💾 LƯU UKC", use_container_width=True):
            config['ukc_day'] = new_ukc_day
            config['ukc_night'] = new_ukc_night
            vn_time = datetime.utcnow() + timedelta(hours=7)
            config["last_update"] = vn_time.strftime("%H:%M:%S ngày %d/%m/%Y")
            save_config(config)
            st.success("✅ Đã lưu UKC!")
            time.sleep(1)
            st.rerun()

    st.markdown("<hr style='margin: 15px 0;'>", unsafe_allow_html=True)

    # --- 2. QUẢN LÝ THÔNG BÁO HÀNG HẢI ---
    st.markdown("#### 2️⃣ QUẢN LÝ THÔNG BÁO HÀNG HẢI")
    
    # Thanh trạng thái các biến đang chạy ngầm
    st.markdown(f"""
        <div style='background-color: #f0f2f6; padding: 10px; border-radius: 5px; border-left: 5px solid #1E90FF; margin-bottom: 15px;'>
            <span style='font-weight: bold; color: #333;'>📍 ĐỘ SÂU ĐANG CHẠY NGẦM: </span>
            <span style='margin-left: 15px;'>HL6: <b>{config.get('hl6', 'N/A')}m</b></span> | 
            <span style='margin-left: 10px;'>HL21: <b>{config.get('hl21', 'N/A')}m</b></span> | 
            <span style='margin-left: 10px;'>HL27: <b>{config.get('hl27', 'N/A')}m</b></span> | 
            <span style='margin-left: 10px;'>Vàm Láng: <b>{config.get('vl', 'N/A')}m</b></span> | 
            <span style='margin-left: 10px;'>TCHP: <b>{config.get('tchp', 'N/A')}m</b></span> | 
            <span style='margin-left: 10px;'>Bờ Băng: <b>{config.get('bb', 'N/A')}m</b></span>
        </div>
    """, unsafe_allow_html=True)
    
    st.info("💡 **Hướng dẫn:** Thêm dòng mới bằng dấu `+` ở cuối bảng. Nếu điểm cạn mới thuộc tuyến đã có, cứ gõ đúng Tên tuyến (vd: LHH Đồng Nai), **hệ thống sẽ tự động gom nó vào đúng nhóm khi bấm Lưu!**")
    
    possible_files = ["data_channel.xlsx", "Channel_Infor.xlsx"]
    file_excel = next((f for f in possible_files if os.path.exists(f)), None)
    
    if file_excel:
        try:
            temp_df = pd.read_excel(file_excel, header=None, nrows=20)
            start_row = 0
            for i, row in temp_df.iterrows():
                row_str = " ".join([str(val).lower() for val in row.values])
                if "độ sâu" in row_str or "tuyến luồng" in row_str or "cầu cảng" in row_str:
                    start_row = i
                    break
            df_excel = pd.read_excel(file_excel, skiprows=start_row)
            df_excel.columns = [str(c).strip() for c in df_excel.columns]
            
            numeric_cols = ["toàn tuyến", "tĩnh không", "độ sâu", "bề rộng"]
            for col in df_excel.columns:
                c_lower = str(col).lower()
                if any(x in c_lower for x in numeric_cols):
                    df_excel[col] = pd.to_numeric(df_excel[col], errors='coerce')
                else:
                    df_excel[col] = df_excel[col].fillna("").astype(str)

            explicit_config = {}
            for col in df_excel.columns:
                col_str = str(col).lower()
                if "tuyến luồng" in col_str:
                    explicit_config[col] = st.column_config.TextColumn(col, width="medium")
                elif any(x in col_str for x in ["đoạn luồng", "điểm cạn", "cầu", "bến"]):
                    explicit_config[col] = st.column_config.TextColumn(col, width="large")
                elif any(x in col_str for x in numeric_cols):
                    explicit_config[col] = st.column_config.NumberColumn(col, width="small", format="%.1f")
                elif "ngày" in col_str or "nhật" in col_str:
                    explicit_config[col] = st.column_config.TextColumn(col, width="medium")
                else:
                    explicit_config[col] = st.column_config.TextColumn(col, width="medium")

            edited_df = st.data_editor(
                df_excel,
                num_rows="dynamic",
                use_container_width=True, 
                height=650,
                column_config=explicit_config
            )
            
            if st.button("💾 LƯU BẢNG VÀ ĐỒNG BỘ ĐỘ SÂU", type="primary", use_container_width=True):
                vn_time = datetime.utcnow() + timedelta(hours=7)
                current_date_str = vn_time.strftime("%d/%m/%Y")
                
                group_col = edited_df.columns[0]
                date_col = next((c for c in edited_df.columns if "ngày" in str(c).lower() or "nhật" in str(c).lower()), None)
                depth_col = next((c for c in edited_df.columns if "độ sâu" in str(c).lower()), None)
                point_col = next((c for c in edited_df.columns if "điểm cạn" in str(c).lower() or "đoạn luồng" in str(c).lower() or "cầu" in str(c).lower()), None)
                
                if date_col and depth_col:
                    for idx in edited_df.index:
                        if idx in df_excel.index:
                            old_depth = pd.to_numeric(df_excel.at[idx, depth_col], errors='coerce')
                            new_depth = pd.to_numeric(edited_df.at[idx, depth_col], errors='coerce')
                            
                            is_changed = False
                            if pd.isna(old_depth) and not pd.isna(new_depth): is_changed = True
                            elif not pd.isna(old_depth) and pd.isna(new_depth): is_changed = True
                            elif not pd.isna(old_depth) and not pd.isna(new_depth) and old_depth != new_depth: is_changed = True
                            
                            if is_changed:
                                edited_df.at[idx, date_col] = current_date_str
                        else:
                            edited_df.at[idx, date_col] = current_date_str

                edited_df[group_col] = edited_df[group_col].replace(r'^\s*$', pd.NA, regex=True)
                if point_col:
                    edited_df[point_col] = edited_df[point_col].replace(r'^\s*$', pd.NA, regex=True)
                    edited_df = edited_df.dropna(subset=[group_col, point_col])
                else:
                    edited_df = edited_df.dropna(subset=[group_col])

                if not edited_df.empty:
                    unique_groups = edited_df[group_col].drop_duplicates().tolist()
                    edited_df['_Group_Cat'] = pd.Categorical(edited_df[group_col], categories=unique_groups, ordered=True)
                    edited_df['_Original_Idx'] = edited_df.index
                    edited_df = edited_df.sort_values(by=['_Group_Cat', '_Original_Idx'])
                    edited_df = edited_df.drop(columns=['_Group_Cat', '_Original_Idx']).reset_index(drop=True)

                for col in edited_df.columns:
                    c_lower = str(col).lower()
                    if not any(x in c_lower for x in numeric_cols):
                        edited_df[col] = edited_df[col].replace("", pd.NA)

                edited_df.to_excel(file_excel, index=False)
                
                if depth_col and point_col:
                    for _, row in edited_df.iterrows():
                        pt_name = str(row[point_col]).lower()
                        depth_val = row[depth_col]
                        if pd.notna(depth_val) and str(depth_val).strip() != "":
                            try:
                                d_val = float(depth_val)
                                if "(hl6)" in pt_name: config['hl6'] = d_val
                                elif "(hl21)" in pt_name: config['hl21'] = d_val
                                elif "(hl27)" in pt_name: config['hl27'] = d_val
                                elif "(vl)" in pt_name: config['vl'] = d_val
                                elif "(tchp)" in pt_name: config['tchp'] = d_val
                                elif "(bb)" in pt_name: config['bb'] = d_val
                            except: pass
                
                config["last_update"] = vn_time.strftime("%H:%M:%S ngày %d/%m/%Y")
                save_config(config)
                
                st.success(f"✅ Đã lưu bảng và cập nhật ngầm thành công lúc {config['last_update']}!")
                time.sleep(1.5) 
                st.rerun() 
        except Exception as e:
            st.error(f"Lỗi khi tải bảng điều khiển: {e}")
    else:
        st.warning(f"⚠️ Chưa tìm thấy file Excel dữ liệu trên hệ thống.")
import streamlit as st
import pandas as pd
import os
from utils.data_processor import process_and_style_df

def render_window_tab(file_path, sheet_name, show_past, disclaimer_text, show_ub=True, show_b=True):
    st.markdown(disclaimer_text)
    if os.path.exists(file_path):
        try:
            df_raw = pd.read_excel(file_path, sheet_name=sheet_name)
            
            # Lọc ẩn/hiện cột UB và B
            cols_to_keep = list(df_raw.columns)
            if not show_ub:
                cols_to_keep = [c for c in cols_to_keep if "UB" not in str(c)]
            if not show_b:
                cols_to_keep = [c for c in cols_to_keep if not ((" B " in str(c) or " B-" in str(c) or str(c).endswith(" B")) and "UB" not in str(c))]

            df_filtered = df_raw[cols_to_keep]
            styled_df = process_and_style_df(df_filtered, show_past_dates=show_past)
            
            # --- CẤU HÌNH CỘT (VIẾT TẮT + TOOLTIP) ---
            col_settings = {
                "_dow": None, 
                "_actual_date": None, 
                "Date": st.column_config.TextColumn("Date", pinned=True)
            }
            
            for original_col in styled_df.data.columns:
                if original_col in ["Date", "_dow", "_actual_date", "Level", "Dir", "Slack", "Vung Tau"]:
                    continue
                
                # Tạo tiêu đề viết tắt
                short_name = str(original_col)
                short_name = short_name.replace("Begin", "B").replace("End", "E")
                short_name = short_name.replace("Port", "P").replace("Stb", "S")
                short_name = short_name.replace("Starboard", "S.") # Phòng hờ file có chữ Starboard gốc
                
                # Áp dụng tên viết tắt và gắn Tooltip giải nghĩa
                col_settings[original_col] = st.column_config.TextColumn(
                    short_name, 
                    help=f"**{original_col}**\n\n*(B: Begin / E: End / P: Port / S: Starboard)*"
                )
            
            # Render bảng (Tắt ép viền để cột tự động bó khít lại)
            st.dataframe(
                styled_df, 
                use_container_width=False, 
                height=750, 
                hide_index=True, 
                column_config=col_settings
            )
        except Exception as e:
            st.error(f"Lỗi hiển thị: {e}")
    else:
        st.warning(f"Không tìm thấy file dữ liệu.")
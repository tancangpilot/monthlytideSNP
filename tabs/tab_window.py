import streamlit as st
import pandas as pd
import os
from utils.data_processor import process_and_style_df

def render_window_tab(file_path, sheet_name, show_past, disclaimer_text, show_ub=True, show_b=True):
    st.markdown(disclaimer_text)
    if os.path.exists(file_path):
        try:
            df_raw = pd.read_excel(file_path, sheet_name=sheet_name)
            df_raw.columns = [str(c).strip() for c in df_raw.columns] # Gọt khoảng trắng thừa
            
            # Lọc ẩn/hiện cột UB và B
            cols_to_keep = list(df_raw.columns)
            if not show_ub:
                cols_to_keep = [c for c in cols_to_keep if "UB" not in str(c)]
            if not show_b:
                cols_to_keep = [c for c in cols_to_keep if not (" B-" in str(c) and "UB" not in str(c))]

            df_filtered = df_raw[cols_to_keep]
            
            # Chuyền qua data_processor để định dạng và tự động bóp ngắn tên cột (nếu công tắc tắt)
            styled_df = process_and_style_df(df_filtered, show_past_dates=show_past)
            
            # --- CẤU HÌNH CỘT (CHỈ GẮN TOOLTIP, KHÔNG ÉP TÊN) ---
            col_settings = {
                "_dow": None, 
                "_actual_date": None, 
                "Date": st.column_config.TextColumn("Date", pinned=True)
            }
            
            for original_col in styled_df.data.columns:
                if original_col in ["Date", "_dow", "_actual_date", "Level", "Dir", "Slack", "VungTau"]:
                    continue
                
                # Trả lại tên đúng như dataframe, chỉ gắn Tooltip giải nghĩa khi rê chuột
                col_settings[original_col] = st.column_config.TextColumn(
                    original_col, 
                    help="*(B/E: Begin/End | UB/B: Unberthing/Berthing | P/Stb: Port/Starboard)*"
                )
            
            # Render bảng
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
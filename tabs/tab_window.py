import streamlit as st
import pandas as pd
import os
from utils.data_processor import process_and_style_df

def render_window_tab(file_path, sheet_name, show_past, disclaimer_text):
    st.markdown(disclaimer_text)
    if os.path.exists(file_path):
        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            # Gọi hàm xử lý đã tách riêng ở utils
            styled_df = process_and_style_df(df, show_past_dates=show_past)
            
            st.dataframe(
                styled_df, 
                use_container_width=True, 
                height=750, 
                column_config={"_dow": None, "_actual_date": None, "Date": st.column_config.TextColumn("Date")}, 
                hide_index=True
            )
        except Exception as e:
            st.error(f"Lỗi đọc sheet {sheet_name}: {e}")
    else:
        st.warning(f"Chưa có dữ liệu hiển thị. Không tìm thấy file '{file_path}'.")
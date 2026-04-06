import streamlit as st
from utils.data_processor import get_max_draft_summary

def render_max_draft_tab(config, group_mode, month_sel):
    styled_df, error = get_max_draft_summary(group_mode, month_sel, config)
    if error:
        st.error(error)
    else:
        # Lọc danh sách cột hiển thị, loại bỏ hẳn _dow và _sort
        vis_cols = [c for c in styled_df.data.columns if c not in ["_dow", "_sort"]]
        
        # CHỈ ĐÓNG BĂNG VÀ ẨN CỘT THỪA - TUYỆT ĐỐI KHÔNG ÉP WIDTH ĐỂ BẢNG TỰ CO KHÍT
        col_cfg = {
            "_dow": None,
            "_sort": None,
            "Date": st.column_config.Column("Date", pinned=True),
            "Point": st.column_config.Column("Point", pinned=True)
        }
        
        # Tắt use_container_width để Streamlit tự động bám sát độ dài nội dung
        st.dataframe(
            styled_df, 
            use_container_width=False, 
            hide_index=True, 
            height=800, 
            column_config=col_cfg, 
            column_order=vis_cols
        )
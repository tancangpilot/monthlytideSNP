import streamlit as st
import datetime
from utils.data_processor import get_max_draft_raw_data, style_max_draft_table

def render_max_draft_tab():
    config = st.session_state.config
    
    col1, col2 = st.columns([1, 1])
    with col1: grp = st.selectbox("🌊 Chọn Sông", ["LÒNG TÀU", "SOÀI RẠP"])
    with col2:
        m_choice = st.selectbox("📅 Chọn Tháng", ["Mặc định (Hiện tại -> Hết tháng)"] + [f"Tháng {i}" for i in range(1, 13)])
        month_sel = f"Tháng {datetime.datetime.now().month}" if "Mặc định" in m_choice else m_choice

    st.markdown("<hr style='margin: 5px 0 15px 0; border-top: 1px solid #ccc;'>", unsafe_allow_html=True)
    
    with st.spinner("Đang tính toán số liệu..."):
        df_raw = get_max_draft_raw_data(config, grp, month_sel)
        if df_raw is not None and not df_raw.empty:
            styled_df = style_max_draft_table(df_raw)
            vis_cols = [c for c in styled_df.data.columns if c not in ["_dow", "_sort"]]
            col_cfg = {"_dow": None, "_sort": None, "Date": st.column_config.Column("Date", pinned=True), "Point": st.column_config.Column("Point", pinned=True)}
            st.dataframe(styled_df, use_container_width=False, hide_index=True, height=800, column_config=col_cfg, column_order=vis_cols)
        else:
            st.warning("❌ Không tìm thấy dữ liệu cho lựa chọn này.")
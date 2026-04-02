import streamlit as st
from utils.data_processor import get_max_draft_summary

def render_max_draft_tab(config):
    def h_red(val):
        return f"<span style='color:red; font-weight:bold;'>{val}</span>"

    info_html = (
        f"<div style='margin-bottom: 5px; font-size: 14.5px;'>"
        f"<i>UCK daytime: {h_red(str(config['ukc_day'])+'%')} - night time: {h_red(str(config['ukc_night'])+'%')} . "
        f"Shallow Point HL6: {h_red('-'+str(config['hl6'])+'m')} / HL21&HL27: {h_red('-'+str(config['hl21'])+'m')} / "
        f"Bờ Băng (BB): {h_red('-'+str(config['bb'])+'m')} / Hạ lưu TCHP: {h_red('-'+str(config['tchp'])+'m')} / "
        f"Vàm Láng: {h_red('-'+str(config['vl'])+'m')} (Update: {config.get('last_updated', 'Chưa có thông tin')})</i>"
        f"</div>"
    )
    st.markdown(info_html, unsafe_allow_html=True)
    
    c1, c2, c3, c4 = st.columns([0.5, 3, 0.6, 3])
    
    c1.markdown("<div style='margin-top: 6px; font-weight: bold;'>Sông:</div>", unsafe_allow_html=True)
    grp = c2.selectbox("Sông", ["LÒNG TÀU", "SOÀI RẠP"], label_visibility="collapsed")
    
    c3.markdown("<div style='margin-top: 6px; font-weight: bold;'>Tháng:</div>", unsafe_allow_html=True)
    m_sel = c4.selectbox("Tháng", ["Mặc định (Hiện tại -> Hết tháng)"] + [f"Tháng {i}" for i in range(1, 13)], label_visibility="collapsed")
    
    styled, err = get_max_draft_summary(grp, m_sel, config)
    
    if err: 
        st.warning(err)
    else:
        st.dataframe(
            styled, 
            use_container_width=True, 
            height=750, 
            hide_index=True, 
            column_config={
                "_dow": None, 
                "_sort": None, 
                "Date": st.column_config.TextColumn("Date", pinned=True),   # <-- Cố định cột Date
                "Point": st.column_config.TextColumn("Point", pinned=True)  # <-- Cố định cột Điểm Cạn
            }
        )

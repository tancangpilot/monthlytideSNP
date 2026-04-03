import streamlit as st
from utils.data_processor import get_max_draft_summary

def render_max_draft_tab(config, grp, m_sel):
    def h_red(val):
        return f"<span style='color:red; font-weight:bold;'>{val}</span>"

    # Đưa giải nghĩa Giờ + Icon vào thẳng dòng Info cho rõ ràng
    info_html = (
        f"<div style='margin-bottom: 15px; font-size: 14.5px;'>"
        f"<i>UCK daytime (06h-17h) ☀️: {h_red(str(config['ukc_day'])+'%')} - night time (18h-05h) 🌙: {h_red(str(config['ukc_night'])+'%')} . "
        f"Shallow Point HL6: {h_red('-'+str(config['hl6'])+'m')} / HL21&HL27: {h_red('-'+str(config['hl21'])+'m')} / "
        f"Bờ Băng (BB): {h_red('-'+str(config['bb'])+'m')} / Hạ lưu TCHP: {h_red('-'+str(config['tchp'])+'m')} / "
        f"Vàm Láng: {h_red('-'+str(config['vl'])+'m')} (Update: {config.get('last_updated', 'Chưa có thông tin')})</i>"
        f"</div>"
    )
    st.markdown(info_html, unsafe_allow_html=True)
    
    styled, err = get_max_draft_summary(grp, m_sel, config)
    
    if err: 
        st.warning(err)
    else:
        # Cấu hình đóng băng cột
        col_settings = {
            "_dow": None, 
            "_sort": None, 
            "Date": st.column_config.TextColumn("Date", pinned=True),
            "Point": st.column_config.TextColumn("Point", pinned=True)
        }
        
        # Tạo Tooltip cho 24 múi giờ (Thay thế cho Icon nằm ngang)
        for h in range(24):
            h_str = f"{h:02d}"
            if h in [5, 18]:
                col_settings[h_str] = st.column_config.TextColumn(h_str, help=f"**{h_str}h 🌙**\n\nMốc Night time UKC ({config['ukc_night']}%)")
            elif h in [6, 17]:
                col_settings[h_str] = st.column_config.TextColumn(h_str, help=f"**{h_str}h ☀️**\n\nMốc Day time UKC ({config['ukc_day']}%)")
            else:
                col_settings[h_str] = st.column_config.TextColumn(h_str)

        st.dataframe(
            styled, 
            use_container_width=False, # CHÌA KHÓA: Tắt ép full viền để 24 cột tự động bó sát lại
            height=750, 
            hide_index=True, 
            column_config=col_settings
        )
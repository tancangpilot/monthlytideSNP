import streamlit as st
from utils.config_manager import save_config
from datetime import datetime, timedelta

def render_admin_page(config):
    st.title("⚙️ Quản lý thông số")
    c1, c2 = st.columns(2)
    config["ukc_day"] = c1.number_input("UKC Day (%)", value=int(config["ukc_day"]))
    config["ukc_night"] = c2.number_input("UKC Night (%)", value=int(config["ukc_night"]))
    
    pts = st.columns(3)
    config["hl27"] = pts[0].number_input("HL27 (m)", value=float(config["hl27"]))
    config["hl21"] = pts[1].number_input("HL21 (m)", value=float(config["hl21"]))
    config["hl6"] = pts[2].number_input("HL6 (m)", value=float(config["hl6"]))
    
    pts2 = st.columns(3)
    config["vl"] = pts2[0].number_input("Vàm Láng (m)", value=float(config["vl"]))
    config["tchp"] = pts2[1].number_input("TCHP (m)", value=float(config["tchp"]))
    config["bb"] = pts2[2].number_input("Bờ Băng (m)", value=float(config["bb"]))
    
    if st.button("💾 Lưu cấu hình"):
        # Tính toán giờ Việt Nam (UTC+7)
        vn_time = datetime.utcnow() + timedelta(hours=7)
        config["last_updated"] = vn_time.strftime("%H:%M %d/%m/%Y")
        
        save_config(config)
        st.success(f"Đã lưu thành công lúc {config['last_updated']}!")
        st.rerun()
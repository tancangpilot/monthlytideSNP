import streamlit as st
import os
from utils.config_manager import load_config, save_config
from tabs.tab_window import render_window_tab
from tabs.tab_max_draft import render_max_draft_tab
from tabs.tab_admin import render_admin_page

# --- 1. ĐỊNH NGHĨA FILE ---
DATA_FILE = "data_window.xlsx"

# --- 2. KHỞI TẠO GIAO DIỆN ---
st.set_page_config(
    page_title="Hệ Thống Thủy Triều Trực Điều Hành", 
    layout="wide",
    initial_sidebar_state="collapsed" 
)

if "config" not in st.session_state:
    st.session_state.config = load_config()

config = st.session_state.config
show_past_global = False

# --- 3. XỬ LÝ ĐĂNG NHẬP VÀ ĐIỀU HƯỚNG (SIDEBAR) ---
with st.sidebar:
    current_page = st.radio(
        "Navigation", 
        ["🌊 Bảng thông tin", "⚙️ Quản lý hệ thống"],
        label_visibility="collapsed"
    )
    st.divider()

    if current_page == "🌊 Bảng thông tin":
        st.markdown("### ⚙️ Tuỳ chọn hiển thị (Window)")
        show_past_global = st.toggle("🕰️ Hiển thị ngày đã qua", value=False)
        st.divider()

    if not config["logged_in"]:
        if current_page == "⚙️ Quản lý hệ thống":
            st.header("🔑 Đăng nhập Quản trị")
            username = st.text_input("Tài khoản")
            password = st.text_input("Mật khẩu", type="password")
            
            if st.button("Đăng nhập"):
                if username == "admin" and password == "123456":
                    config["logged_in"] = True
                    save_config(config)
                    st.rerun()
                else:
                    st.error("Sai tài khoản hoặc mật khẩu!")
    else:
        st.success("Đã đăng nhập quản trị thành công!")
        if st.button("Đăng xuất"):
            config["logged_in"] = False
            save_config(config)
            st.rerun()
            
    # --- PHIÊN BẢN ---
    st.divider()
    st.caption("Phiên bản V 1.3")


# --- 4. ĐIỀU HƯỚNG TRANG (ROUTING) ---
if current_page == "🌊 Bảng thông tin":
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["CÁI MÉP", "CÁT LÁI", "Tide Calc", "Max Draft Table", "POB Table"])

    with tab1:
        note_cm = ":red[*Window is calculated for vessels LOA ≤ 300m; Draft ≤ 12.5m; GRT ≤ 80.000. The vessels: Draft > 12.5m; LOA > 300m; GRT > 80.000 is advised by Duty Pilot*] *(𝗨𝗕 - Unberthing / B - Berthing)*"
        render_window_tab(DATA_FILE, "WindowCM", show_past_global, note_cm)
    
    with tab2:
        note_cl = "*The vessels: Draft > 10.0m or Departure outside Window must be advised by the duty pilot.*"
        render_window_tab(DATA_FILE, "WindowCL", show_past_global, note_cl)
        
    with tab3:
        st.write("Đang phát triển Tab Tính Toán Thủy Triều...")
        
    with tab4:
        # Đã xóa dòng st.write() và thay bằng hàm gọi Tab 4
        render_max_draft_tab(config)

    with tab5:
        st.write("Đang phát triển Tab POB Table...")

elif current_page == "⚙️ Quản lý hệ thống":
    if config["logged_in"]:
        render_admin_page(config)
    else:
        st.info("👈 Vui lòng đăng nhập tại thanh menu bên trái để truy cập chức năng Quản lý hệ thống.")
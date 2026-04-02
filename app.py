import streamlit as st
import streamlit.components.v1 as components
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

# --- 3. ĐOẠN MÃ NGẦM JS: ĐẾM NGƯỢC 10 GIÂY VÀ GIẢ LẬP CLICK CHUỘT ---
components.html(
    """
    <script>
    const doc = window.parent.document;
    let isOpen = false;
    let autoCloseTimer = null;
    let timeLeft = 10;

    setInterval(() => {
        const sidebar = doc.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return;

        const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';
        const countdownDisplay = doc.getElementById('sidebar-countdown');

        if (isExpanded && !isOpen) {
            isOpen = true;
            timeLeft = 10;
            if (countdownDisplay) countdownDisplay.innerText = `Auto hide sidebar: ${timeLeft}s`;
            
            autoCloseTimer = setInterval(() => {
                timeLeft -= 1;
                if (countdownDisplay) countdownDisplay.innerText = `Auto hide sidebar: ${timeLeft}s`;
                
                if (timeLeft <= 0) {
                    clearInterval(autoCloseTimer);
                    if (countdownDisplay) countdownDisplay.innerText = "";
                    
                    // Phương pháp 2: Giả lập cú click chuột người thật (React cần bubbles: true)
                    let closeBtns = [
                        doc.querySelector('[data-testid="stSidebarCollapseButton"]'), // Streamlit mới
                        doc.querySelector('button[aria-label="Collapse sidebar"]'),   // Streamlit bản giữa
                        sidebar.querySelector('button') // Quét thô bạo nút bấm đầu tiên trong sidebar
                    ];
                    
                    closeBtns.forEach(btn => {
                        if (btn) {
                            // Tạo event giả lập người dùng click chuột
                            const clickEvent = new MouseEvent('click', {
                                view: window.parent,
                                bubbles: true,
                                cancelable: true
                            });
                            btn.dispatchEvent(clickEvent); // Gửi event
                            btn.click(); // Lệnh backup
                        }
                    });
                }
            }, 1000);
            
        } else if (!isExpanded && isOpen) {
            isOpen = false;
            clearInterval(autoCloseTimer);
            if (countdownDisplay) countdownDisplay.innerText = "";
        }
    }, 500);
    </script>
    """,
    height=0,
    width=0,
)

if "config" not in st.session_state:
    st.session_state.config = load_config()

config = st.session_state.config
show_past_global = False

# --- 4. XỬ LÝ ĐĂNG NHẬP VÀ ĐIỀU HƯỚNG (SIDEBAR) ---
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
            
    # --- PHIÊN BẢN & ĐỒNG HỒ ĐẾM NGƯỢC ---
    st.divider()
    st.markdown(
        """
        <div style="display: flex; justify-content: space-between; color: #888; font-size: 0.85em; margin-bottom: 10px;">
            <span>Phiên bản V 1.7</span>
            <span id="sidebar-countdown" style="font-weight: bold; color: #ff4b4b;"></span>
        </div>
        """, 
        unsafe_allow_html=True
    )


# --- 5. ĐIỀU HƯỚNG TRANG CHÍNH ---
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
        render_max_draft_tab(config)

    with tab5:
        st.write("Đang phát triển Tab POB Table...")

elif current_page == "⚙️ Quản lý hệ thống":
    if config["logged_in"]:
        render_admin_page(config)
    else:
        st.info("👈 Vui lòng đăng nhập tại thanh menu bên trái để truy cập chức năng Quản lý hệ thống.")

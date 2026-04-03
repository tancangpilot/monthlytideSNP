import streamlit as st
import streamlit.components.v1 as components
import os
from utils.config_manager import load_config, save_config
from tabs.tab_window import render_window_tab
from tabs.tab_max_draft import render_max_draft_tab
from tabs.tab_admin import render_admin_page
from tabs.tab_tide_calc import render_tide_calc_tab

# --- 1. ĐỊNH NGHĨA FILE ---
DATA_FILE = "data_window.xlsx"

# --- 2. KHỞI TẠO GIAO DIỆN ---
st.set_page_config(
    page_title="Hệ Thống Thủy Triều Trực Điều Hành", 
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- 3. ĐOẠN MÃ NGẦM JS: TỰ ĐÓNG SIDEBAR SAU 30 GIÂY ---
components.html(
    """
    <script>
    const doc = window.parent.document;
    let isOpen = false;
    let autoCloseTimer = null;
    let timeLeft = 30;

    setInterval(() => {
        const sidebar = doc.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return;

        const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';
        const countdownDisplay = doc.getElementById('sidebar-countdown');

        if (isExpanded && !isOpen) {
            isOpen = true;
            timeLeft = 30;
            if (countdownDisplay) countdownDisplay.innerText = `Auto hide sidebar: ${timeLeft}s`;
            
            autoCloseTimer = setInterval(() => {
                timeLeft -= 1;
                if (countdownDisplay) countdownDisplay.innerText = `Auto hide sidebar: ${timeLeft}s`;
                
                if (timeLeft <= 0) {
                    clearInterval(autoCloseTimer);
                    if (countdownDisplay) countdownDisplay.innerText = "";
                    
                    let closeBtns = [
                        doc.querySelector('[data-testid="stSidebarCollapseButton"]'),
                        doc.querySelector('button[aria-label="Collapse sidebar"]'),
                        sidebar.querySelector('button') 
                    ];
                    
                    closeBtns.forEach(btn => {
                        if (btn) {
                            const clickEvent = new MouseEvent('click', {
                                view: window.parent,
                                bubbles: true,
                                cancelable: true
                            });
                            btn.dispatchEvent(clickEvent); 
                            btn.click(); 
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

# --- 4. XỬ LÝ ĐĂNG NHẬP VÀ ĐIỀU HƯỚNG ---
with st.sidebar:
    current_page = st.radio("Navigation", ["🌊 Bảng thông tin", "⚙️ Quản lý hệ thống"], label_visibility="collapsed")
    st.divider()

if current_page == "🌊 Bảng thông tin":
    selected_tab = st.radio(
        "Chọn tính năng:", 
        ["CÁI MÉP", "CÁT LÁI", "Tide Calc Cat Lai", "Max Draft Table", "POB Table"], 
        horizontal=True, 
        label_visibility="collapsed"
    )
    
    with st.sidebar:
        st.markdown("### ⚙️ Tuỳ chọn chung")
        show_past_global = st.toggle("🕰️ Hiển thị ngày đã qua", value=False)
        st.divider()
        st.markdown(f"### 🎯 Tuỳ chọn: {selected_tab}")
        
        if selected_tab in ["CÁI MÉP", "CÁT LÁI"]:
            show_ub = st.toggle("Ẩn/Hiện UB (Rời)", value=True)
            show_b = st.toggle("Ẩn/Hiện B (Cập)", value=True)
            grp = None; m_sel = None
        elif selected_tab == "Max Draft Table":
            grp = st.selectbox("Sông", ["LÒNG TÀU", "SOÀI RẠP"])
            m_sel = st.selectbox("Tháng", ["Mặc định (Hiện tại -> Hết tháng)"] + [f"Tháng {i}" for i in range(1, 13)])
            show_ub = True; show_b = True
        elif selected_tab == "Tide Calc Cat Lai":
            st.write("**🧭 Định tuyến (Routing)**")
            direction = st.radio("Hướng đi", ["⬆️ Outbound (Đi ra)", "⬇️ Inbound (Đi vào)"], label_visibility="collapsed")
            routes = ["1. Cát Lái ➔ Lòng Tàu ➔ P0 VT", "2. Cát Lái ➔ Soài Rạp ➔ P0 SR (Hỗn hợp)", "3. TC Hiệp Phước ➔ Soài Rạp ➔ P0 SR"] if "Outbound" in direction else ["1. P0 VT ➔ Lòng Tàu ➔ Cát Lái", "2. P0 SR ➔ Soài Rạp ➔ TC Hiệp Phước"]
            route_sel = st.radio("Chọn tuyến", routes)
        else:
            show_ub = True; show_b = True; grp = None; m_sel = None

    # ĐÃ KHÔI PHỤC ĐẦY ĐỦ VĂN BẢN GHI CHÚ
    if selected_tab == "CÁI MÉP":
        note_cm = ":red[*Window is calculated for vessels LOA ≤ 300m; Draft ≤ 12.5m; GRT ≤ 80.000. The vessels: Draft > 12.5m; LOA > 300m; GRT > 80.000 is advised by Duty Pilot*] *(𝗨𝗕 - Unberthing / B - Berthing)*"
        render_window_tab(DATA_FILE, "WindowCM", show_past_global, note_cm, show_ub, show_b)
    elif selected_tab == "CÁT LÁI":
        note_cl = "*The vessels: Draft > 10.0m or Departure outside Window must be advised by the duty pilot.*"
        render_window_tab(DATA_FILE, "WindowCL", show_past_global, note_cl, show_ub, show_b)
    elif selected_tab == "Tide Calc Cat Lai":  
        render_tide_calc_tab(route_sel)
    elif selected_tab == "Max Draft Table":
        render_max_draft_tab(config, grp, m_sel)
    elif selected_tab == "POB Table":
        st.write("Đang phát triển Tab POB Table...")

elif current_page == "⚙️ Quản lý hệ thống":
    if config["logged_in"]: render_admin_page(config)
    else:
        with st.sidebar:
            st.header("🔑 Đăng nhập")
            u = st.text_input("Tài khoản"); p = st.text_input("Mật khẩu", type="password")
            if st.button("Đăng nhập") and u == "admin" and p == "123456":
                config["logged_in"] = True; save_config(config); st.rerun()

with st.sidebar:
    st.divider()
    st.markdown(f'<div style="display: flex; justify-content: space-between; font-size: 0.85em;"><span>V 1.18</span><span id="sidebar-countdown" style="color: #ff4b4b;"></span></div>', unsafe_allow_html=True)
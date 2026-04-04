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
st.markdown("""
    <style>
    /* Ép cỡ chữ cho bảng DataFrame */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        font-size: 20px !important;
    }
    /* Ép cỡ chữ cho các ô nhập liệu (POB Date, Time...) */
    .stDateInput div[data-baseweb="input"], .stTimeInput div[data-baseweb="input"], .stNumberInput div[data-baseweb="input"] {
        font-size: 20px !important;
    }
    /* Tăng cỡ chữ cho nhãn (Label) */
    .stMarkdown p, label {
        font-size: 18px !important;
    }
    </style>
    """, unsafe_allow_html=True)
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
    
    # --- GHIM GLOBAL HEADER (UKC & SHALLOW POINT) LÊN ĐẦU MÀN HÌNH ---
    last_update = config.get("last_update", "16:16:42 ngày 02/04/2026")
    st.markdown(f"""
    <div style="background-color: #e6f7ff; padding: 12px 15px; border-radius: 6px; margin-bottom: 15px; font-size: 15px; color: #222; border-left: 5px solid #1E90FF; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
        <b>UKC daytime (06h-17h) ☀️:</b> <span style="color:#e60000; font-weight:bold;">{config.get('ukc_day', 7)}%</span> - 
        <b>night time (18h-05h) 🌙:</b> <span style="color:#e60000; font-weight:bold;">{config.get('ukc_night', 10)}%</span> &nbsp;|&nbsp; 
        <b>Shallow Point</b> HL6: <span style="color:#1E90FF; font-weight:bold;">-{config.get('hl6', 8.8)}m</span> / 
        HL21&HL27: <span style="color:#1E90FF; font-weight:bold;">-{config.get('hl27', 8.5)}m</span> / 
        Bờ Băng (BB): <span style="color:#1E90FF; font-weight:bold;">-{config.get('bb', 6.7)}m</span> / 
        Hạ lưu TCHP: <span style="color:#1E90FF; font-weight:bold;">-{config.get('tchp', 8.0)}m</span> / 
        Vàm Láng: <span style="color:#1E90FF; font-weight:bold;">-{config.get('vl', 8.0)}m</span> 
        <i style="color: #666; font-size: 13px;">(Update: {last_update})</i>
    </div>
    """, unsafe_allow_html=True)

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
            # CHỈ ĐỂ LẠI INBOUND/OUTBOUND TRONG SIDEBAR
            st.write("**🧭 Định tuyến (Routing)**")
            direction = st.radio("Hướng đi", ["⬆️ Outbound (Đi ra)", "⬇️ Inbound (Đi vào)"], label_visibility="collapsed")
        else:
            show_ub = True; show_b = True; grp = None; m_sel = None

    if selected_tab == "CÁI MÉP":
        note_cm = ":red[*Window is calculated for vessels LOA ≤ 300m; Draft ≤ 12.5m; GRT ≤ 80.000. The vessels: Draft > 12.5m; LOA > 300m; GRT > 80.000 is advised by Duty Pilot*]"
        render_window_tab(DATA_FILE, "WindowCM", show_past_global, note_cm, show_ub, show_b)
    elif selected_tab == "CÁT LÁI":
        note_cl = "*The vessels: Draft > 10.0m or Departure outside Window must be advised by the duty pilot.*"
        render_window_tab(DATA_FILE, "WindowCL", show_past_global, note_cl, show_ub, show_b)
    elif selected_tab == "Tide Calc Cat Lai":  
        # TRUYỀN BIẾN DIRECTION SANG TAB TIDE CALC
        render_tide_calc_tab(direction)
    elif selected_tab == "Max Draft Table":
        render_max_draft_tab(config, grp, m_sel)
    elif selected_tab == "POB Table":
        st.write("Đang phát triển Tab POB Table...")

elif current_page == "⚙️ Quản lý hệ thống":
    if config.get("logged_in", False):
        with st.sidebar:
            st.success("Đã đăng nhập!")
            if st.button("Đăng xuất"):
                config["logged_in"] = False
                save_config(config)
                st.rerun()
        render_admin_page(config)
    else:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            with st.container(border=True):
                st.markdown("<h3 style='text-align: center;'>🔑 Đăng nhập hệ thống</h3>", unsafe_allow_html=True)
                st.markdown("<br>", unsafe_allow_html=True)
                
                u = st.text_input("Tài khoản")
                p = st.text_input("Mật khẩu", type="password")
                
                if st.button("Đăng nhập", use_container_width=True, type="primary"):
                    if u == "admin" and p == "123456":
                        config["logged_in"] = True
                        save_config(config)
                        st.rerun()
                    else:
                        st.error("Sai tài khoản hoặc mật khẩu!")

with st.sidebar:
    st.divider()
    st.markdown(f'<div style="display: flex; justify-content: space-between; font-size: 0.85em;"><span>V 1.21</span><span id="sidebar-countdown" style="color: #ff4b4b;"></span></div>', unsafe_allow_html=True)
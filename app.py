import streamlit as st
import streamlit.components.v1 as components
import os
from datetime import datetime
from utils.config_manager import load_config, save_config
from tabs.tab_window import render_window_tab
from tabs.tab_max_draft import render_max_draft_tab
from tabs.tab_admin import render_admin_page
from tabs.tab_tide_calc import render_tide_calc_tab
from tabs.tab_channel_info import render_channel_info_tab
from tabs.tab_pob_print import render_pob_print_tab

DATA_FILE = "data_window.xlsx"

# 1. DANH SÁCH MENU
MENU_OPTIONS = [
    "🧭 Tide Calc CÁT LÁI",
    "🌊 Window CÁT LÁI",
    "🧭 Tide Calc CÁI MÉP",
    "🌊 Window CÁI MÉP",
    "🖨️ POB Table",
    "📊 Max Draft Table",
    "ℹ️ Channel Infor"
]

TAB_MAP = {
    "🧭 Tide Calc CÁT LÁI": "tide_cl",
    "🌊 Window CÁT LÁI": "cl",
    "🧭 Tide Calc CÁI MÉP": "tide_cm",
    "🌊 Window CÁI MÉP": "cm",
    "🖨️ POB Table": "pob_print",
    "📊 Max Draft Table": "draft",
    "ℹ️ Channel Infor": "channel"
}
REVERSE_MAP = {v: k for k, v in TAB_MAP.items()}

st.set_page_config(page_title="Tide Schedule", page_icon="logoHTTC.jpg", layout="wide", initial_sidebar_state="collapsed")

if "active_tab_key" not in st.session_state:
    st.session_state.active_tab_key = REVERSE_MAP.get(st.query_params.get("tab", "tide_cl"), "🧭 Tide Calc CÁT LÁI")

def update_url_params(): 
    st.query_params["tab"] = TAB_MAP[st.session_state.active_tab_key]

# =====================================================================
# CSS ĐỘ GIAO DIỆN HÀNG HIỆU
# =====================================================================
st.markdown("""
    <style>
    /* 1. Header & Container */
    header[data-testid="stHeader"] { background-color: rgba(0,0,0,0) !important; border-bottom: none !important; height: 3rem !important; }
    .block-container { padding-top: 0rem !important; margin-top: 1.5rem !important; padding-bottom: 0rem !important; padding-left: 2rem !important; padding-right: 2rem !important; }

    /* 2. Menu Radio Hàng Hiệu */
    [data-testid="stSidebar"] [data-testid="stRadio"] { margin-top: -20px !important; }
    [data-testid="stSidebar"] [data-testid="stRadio"] label { padding-top: 2px !important; padding-bottom: 2px !important; }
    [data-testid="stSidebar"] h3 { margin-top: -10px !important; margin-bottom: 5px !important; font-size: 1.1rem !important; }
    [data-testid="stSidebar"] hr { margin-top: 8px !important; margin-bottom: 8px !important; }
    
    [data-testid="stMainBlockContainer"] [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] {
        padding: 8px 12px !important; border: 2px solid transparent !important; border-radius: 8px !important; margin-bottom: 2px; transition: all 0.2s ease;
    }
    [data-testid="stMainBlockContainer"] [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
        border: 2px solid #1E90FF !important; background-color: #f0f8ff !important;
    }

    /* 3. Bảng và Form Input */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th { font-size: 20px !important; }
    [data-testid="stDataFrame"] th { background-color: #ffe699 !important; color: #111 !important; }
    .stDateInput div[data-baseweb="input"], .stTimeInput div[data-baseweb="input"], .stNumberInput div[data-baseweb="input"] { font-size: 20px !important; }
    .stMarkdown p, label { font-size: 18px !important; }

    /* =======================================================
       4. NÚT ĐÓNG BÊN TRONG SIDEBAR (TRÒN TRẮNG)
       ======================================================= */
    [data-testid="stSidebar"] button[kind="header"] { 
        background-color: #ffffff !important; 
        border: 1px solid #1E90FF !important; 
        border-radius: 50% !important; 
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important; 
        z-index: 999999 !important;
    }

    /* =======================================================
       5. NÚT MỞ BÊN NGOÀI (TAB XANH NHỊP TIM ĐẬP)
       ======================================================= */
    /* Xác định chính xác vùng chứa nút MỞ góc trái */
    [data-testid="collapsedControl"] {
        position: fixed !important;
        top: 15px !important;
        left: 0px !important;
        z-index: 999999 !important;
    }

    /* Đúc khuôn Tab xanh bo góc */
    [data-testid="collapsedControl"] button {
        background-color: #1E90FF !important; 
        border: none !important;
        border-radius: 0 8px 8px 0 !important; 
        padding: 5px 8px 5px 2px !important;
        box-shadow: 3px 2px 10px rgba(30, 144, 255, 0.4) !important;
        transition: all 0.3s ease !important;
        animation: pulseMenu 2s infinite !important; 
    }
    
    /* Đổi màu Icon Mũi Tên (>>) thành Trắng tinh */
    [data-testid="collapsedControl"] button svg {
        color: white !important;
        fill: white !important;
        width: 22px !important;
        height: 22px !important;
    }
    
    /* Đẩy nhẹ ra khi rê chuột */
    [data-testid="collapsedControl"] button:hover {
        background-color: #0056b3 !important;
        padding-left: 10px !important; 
    }
    
    /* Hiệu ứng nhịp tim (Pulse) tỏa sóng */
    @keyframes pulseMenu {
        0% { box-shadow: 0 0 0 0 rgba(30, 144, 255, 0.7); }
        70% { box-shadow: 0 0 0 10px rgba(30, 144, 255, 0); }
        100% { box-shadow: 0 0 0 0 rgba(30, 144, 255, 0); }
    }
    </style>
""", unsafe_allow_html=True)

# JS AUTO CLOSE
components.html("""<script>
    const doc = window.parent.document; let isOpen = false; let autoCloseTimer = null; let timeLeft = 60;
    setInterval(() => {
        const sidebar = doc.querySelector('[data-testid="stSidebar"]'); if (!sidebar) return;
        const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';
        const cd = doc.getElementById('sidebar-countdown');
        if (isExpanded && !isOpen) {
            isOpen = true; timeLeft = 60; if (cd) cd.innerText = `Auto hide: ${timeLeft}s`;
            autoCloseTimer = setInterval(() => {
                timeLeft -= 1; if (cd) cd.innerText = `Auto hide: ${timeLeft}s`;
                if (timeLeft <= 0) { clearInterval(autoCloseTimer); if (cd) cd.innerText = ""; const btn = doc.querySelector('[data-testid="stSidebarCollapseButton"]') || doc.querySelector('button[aria-label="Collapse sidebar"]') || doc.querySelector('button[kind="header"]'); if (btn) btn.click(); }
            }, 1000);
        } else if (!isExpanded && isOpen) { isOpen = false; clearInterval(autoCloseTimer); if (cd) cd.innerText = ""; }
    }, 500);
</script>""", height=0, width=0)

if "config" not in st.session_state: st.session_state.config = load_config()
config = st.session_state.config

# ==========================================
# KHU VỰC SIDEBAR (GOM TOÀN BỘ VÀO ĐÂY)
# ==========================================
with st.sidebar:
    current_page = st.radio("Navigation", ["🌊 Bảng thông tin", "⚙️ Quản lý hệ thống"], label_visibility="collapsed")
    st.markdown("<hr style='margin: 0px 0 10px 0; border: 0; border-top: 1.5px solid #eee;'>", unsafe_allow_html=True)

    if current_page == "🌊 Bảng thông tin":
        # Khối 1: UKC
        st.markdown(f"""
        <div style="background-color: #e6f7ff; padding: 12px; border-radius: 6px; margin-bottom: 20px; font-size: 14px; color: #222; border-left: 4px solid #1E90FF; box-shadow: 0 1px 3px rgba(0,0,0,0.1); line-height: 1.6;">
            <b>UKC daytime (06h-17h) ☀️:</b> <span style="color:#e60000; font-weight:bold;">{config.get('ukc_day', 7)}%</span> - <b>night time (18h-05h) 🌙:</b> <span style="color:#e60000; font-weight:bold;">{config.get('ukc_night', 10)}%</span><br>
            <b>Sh.P:</b> HL6: <span style="color:#1E90FF; font-weight:bold;">-{config.get('hl6', 8.8)}m</span> | HL21&27: <span style="color:#1E90FF; font-weight:bold;">-{config.get('hl27', 8.5)}m</span> | BB: <span style="color:#1E90FF; font-weight:bold;">-{config.get('bb', 6.7)}m</span> | TCHP: <span style="color:#1E90FF; font-weight:bold;">-{config.get('tchp', 8.0)}m</span> | VL: <span style="color:#1E90FF; font-weight:bold;">-{config.get('vl', 8.0)}m</span>
            <div style="color: #666; font-size: 11.5px; margin-top: 4px;"><i>(Update: {config.get('last_update', 'N/A')})</i></div>
        </div>
        """, unsafe_allow_html=True)
        # Khối 2: Tabs
        selected_tab = st.radio("Tính năng:", options=MENU_OPTIONS, key="active_tab_key", on_change=update_url_params, label_visibility="collapsed")
    else:
        selected_tab = None

    # Khối 4: Footer Cố định dưới Sidebar
    st.markdown(f'''
        <div style="margin-top: 15px;"></div>
        <hr style="margin: 8px 0 4px 0; border: 0; border-top: 1px solid #ddd;">
        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85em; line-height: 1.2;">
            <span style="font-weight: bold;">V 1.25</span><span id="sidebar-countdown" style="color: #ff4b4b; font-weight: bold;"></span>
        </div>
        <div style="margin-top: 1px;"><i style="font-size: 0.75em; color: gray; display: block;">Built by @Hai.PT(NP44)</i></div>
        <hr style="margin: 4px 0 8px 0; border: 0; border-top: 1px solid #ddd;">
    ''', unsafe_allow_html=True)

    # KHỐI 5: MIỄN TRỪ TRÁCH NHIỆM CHUẨN GỐC
    with st.expander("⚖️ Miễn trừ trách nhiệm / Disclaimer"):
        st.markdown("""
            <div style='font-size: 11px; line-height: 1.4; color: gray; text-align: justify;'>
                <b>MIỄN TRỪ TRÁCH NHIỆM:</b><br>
                Website này và các công cụ tính toán đi kèm được cung cấp chỉ nhằm mục đích thông tin và tham khảo. 
                Nhà phát triển (@Hai.PT) không đưa ra bất kỳ cam kết nào về độ tin cậy của dữ liệu cho mục đích điều động tàu.
                <br><br>
                <b>GIỚI HẠN TRÁCH NHIỆM:</b><br>
                Nhà phát triển không chịu trách nhiệm cho bất kỳ tổn thất hoặc tai nạn hàng hải nào (tàu cạn, va chạm...) 
                phát sinh từ việc sử dụng thông tin này. Quyết định điều động tàu cuối cùng thuộc về Thuyền trưởng và Hoa tiêu trên tàu. 
                Người dùng bắt buộc phải đối chiếu với bảng thủy triều chính thức (VMSA).
                <br><br>
                <i>Bằng việc sử dụng website này, bạn đồng ý chấp nhận mọi rủi ro và từ bỏ mọi quyền khiếu nại pháp lý đối với nhà phát triển.</i>
            </div>
        """, unsafe_allow_html=True)


# ==========================================
# KHU VỰC MAIN PAGE (BÊN PHẢI)
# ==========================================
if current_page == "🌊 Bảng thông tin":
    if selected_tab == "🧭 Tide Calc CÁT LÁI": 
        render_tide_calc_tab()
    elif selected_tab == "🌊 Window CÁT LÁI": 
        render_window_tab(DATA_FILE, "WindowCL", "*The vessels: Draft > 10.0m or Departure outside Window must be advised by duty pilot.*")
    elif selected_tab == "🧭 Tide Calc CÁI MÉP": 
        st.info("🚧 Chức năng Tide Calc CÁI MÉP đang được cập nhật!") 
    elif selected_tab == "🌊 Window CÁI MÉP": 
        render_window_tab(DATA_FILE, "WindowCM", ":red[*Window is calculated for vessels LOA ≤ 300m; Draft ≤ 12.5m; GRT ≤ 80.000. The vessels: Draft > 12.5m; LOA > 300m; GRT > 80.000 is advised by Duty Pilot.*]")
    elif selected_tab == "🖨️ POB Table": 
        render_pob_print_tab()
    elif selected_tab == "📊 Max Draft Table": 
        render_max_draft_tab()
    elif selected_tab == "ℹ️ Channel Infor": 
        render_channel_info_tab()

elif current_page == "⚙️ Quản lý hệ thống":
    if "tab" in st.query_params: del st.query_params["tab"]
    if config.get("logged_in", False):
        with st.sidebar:
            st.success("Đã đăng nhập!")
            if st.button("Đăng xuất"):
                config["logged_in"] = False; save_config(config); st.rerun()
        render_admin_page(config)
    else:
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            with st.container(border=True):
                st.markdown("<h3 style='text-align: center;'>🔑 Đăng nhập hệ thống</h3><br>", unsafe_allow_html=True)
                u = st.text_input("Tài khoản")
                p = st.text_input("Mật khẩu", type="password")
                if st.button("Đăng nhập", use_container_width=True, type="primary"):
                    if u == "admin" and p == "123456":
                        config["logged_in"] = True
                        save_config(config); st.rerun()
                    else: st.error("Sai tài khoản hoặc mật khẩu!")
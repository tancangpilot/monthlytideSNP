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

# --- 1. ĐỊNH NGHĨA FILE & MAPPING (Dành cho Link) ---
DATA_FILE = "data_window.xlsx"

TAB_MAP = {
    "Tide Calc CÁT LÁI": "tide",
    "CÁT LÁI": "cl",
    "CÁI MÉP": "cm",
    "Max Draft Table": "draft",
    "Channel Infor": "channel"
}
REVERSE_MAP = {v: k for k, v in TAB_MAP.items()}

# --- 2. KHỞI TẠO GIAO DIỆN ---
st.set_page_config(
    page_title="Tide Schedule", 
    page_icon="logoHTTC.png",
    layout="wide",
    initial_sidebar_state="collapsed" 
)

# --- PHẦN LOGIC ĐỌC LINK (PHẢI CHẠY TRƯỚC RADIO) ---
if "active_tab_key" not in st.session_state:
    query_slug = st.query_params.get("tab", "tide")
    st.session_state.active_tab_key = REVERSE_MAP.get(query_slug, "Tide Calc CÁT LÁI")

def update_url_params():
    # Cập nhật URL mỗi khi ông bấm chọn Tab khác
    st.query_params["tab"] = TAB_MAP[st.session_state.active_tab_key]

st.markdown("""
    <style>
    /* Ép khoảng cách phía trên cùng của trang sát lại */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 0rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
    }
    
    /* Ép cỡ chữ cho bảng DataFrame */
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        font-size: 20px !important;
    }
    
    /* ---------------------------------------------------
       1. ĐỔ MÀU VÀNG CHO TIÊU ĐỀ BẢNG (HEADERS)
       --------------------------------------------------- */
    [data-testid="stDataFrame"] th {
        background-color: #ffe699 !important; /* Màu vàng nhạt */
        color: #111 !important;
    }

    /* Ép cỡ chữ cho các ô nhập liệu (POB Date, Time...) */
    .stDateInput div[data-baseweb="input"], .stTimeInput div[data-baseweb="input"], .stNumberInput div[data-baseweb="input"] {
        font-size: 20px !important;
    }
    /* Tăng cỡ chữ cho nhãn (Label) */
    .stMarkdown p, label {
        font-size: 18px !important;
    }

    /* ---------------------------------------------------
       2. TẠO KHUNG VIỀN CHO TUYẾN ĐƯỜNG ĐƯỢC CHỌN
       --------------------------------------------------- */
    /* Căn lề sẵn để nút không bị giật khi chọn */
    [data-testid="stMainBlockContainer"] [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"] {
        padding: 8px 12px !important;
        border: 2px solid transparent !important;
        border-radius: 8px !important;
        margin-bottom: 2px;
        transition: all 0.2s ease;
    }
    /* Đóng khung xanh dương cho lựa chọn đang được Check */
    [data-testid="stMainBlockContainer"] [data-testid="stRadio"] div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
        border: 2px solid #1E90FF !important;
        background-color: #f0f8ff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. ĐOẠN MÃ NGẦM JS: TỰ ĐÓNG SIDEBAR SAU 60 GIÂY ---
components.html(
    """
    <script>
    const doc = window.parent.document;
    let isOpen = false;
    let autoCloseTimer = null;
    let timeLeft = 60; // Đã tăng lên 60s

    setInterval(() => {
        const sidebar = doc.querySelector('[data-testid="stSidebar"]');
        if (!sidebar) return;

        const isExpanded = sidebar.getAttribute('aria-expanded') === 'true';
        const countdownDisplay = doc.getElementById('sidebar-countdown');

        if (isExpanded && !isOpen) {
            isOpen = true;
            timeLeft = 60; // Đã tăng lên 60s
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
        <br>
        <i style="color: #666; font-size: 13px;">(Update: {last_update})</i>
    </div>
    """, unsafe_allow_html=True)

    # ĐỔI TÊN TAB THEO YÊU CẦU - ĐÃ CHÈN KEY ĐỂ NHẬY TAB
    selected_tab = st.radio(
        "Chọn tính năng:", 
        options=list(TAB_MAP.keys()),
        key="active_tab_key",
        on_change=update_url_params,
        horizontal=True, 
        label_visibility="collapsed"
    )
    
    with st.sidebar:
        st.markdown("### ⚙️ Tuỳ chọn chung")
        show_past_global = st.toggle("🕰️ Hiển thị ngày đã qua", value=False)
        
        st.session_state.show_full_cols = st.toggle("Hiển thị đủ tên cột", value=True)
        # GHI CHÚ ĐÃ ĐƯỢC IN ĐẬM VÀ TÔ MÀU ĐÚNG CHUẨN
        st.markdown("""
        <div style='font-size: 13.5px; color: #555; background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-top: -10px; margin-bottom: 15px; border-left: 3px solid #1E90FF;'>
            <i><b>💡 Ghi chú thuật ngữ:</b><br>
            • <b>B/E:</b> Begin / End<br>
            • <b>UB/B:</b> <b>UnBerthing / Berthing</b><br>
            • <b style="color:#ff4d4d;">P: Port</b><br>
            • <b style="color:#00cc00;">Stb: Starboard</b></i>
        </div>
        """, unsafe_allow_html=True)

        st.divider()
        st.markdown(f"### 🎯 Tuỳ chọn: {selected_tab}")
        
        if selected_tab in ["CÁI MÉP", "CÁT LÁI"]:
            show_ub = st.toggle("Ẩn/Hiện UB (Rời)", value=True)
            show_b = st.toggle("Ẩn/Hiện B (Cập)", value=True)
            grp = None; m_sel = None
        elif selected_tab == "Max Draft Table":
            grp = st.selectbox("Sông", ["LÒNG TÀU", "SOÀI RẠP"])
            m_choice = st.selectbox("Tháng", ["Mặc định (Hiện tại -> Hết tháng)"] + [f"Tháng {i}" for i in range(1, 13)])
            # SỬA LỖI split() BẰNG CÁCH GỬI CHUỖI CHUẨN SANG TAB_MAX_DRAFT
            if "Mặc định" in m_choice:
                m_sel = f"Tháng {datetime.now().month}"
            else:
                m_sel = m_choice
            show_ub = True; show_b = True
        elif selected_tab == "Tide Calc CÁT LÁI":
            st.write("**🧭 Định tuyến (Routing)**")
            
            def reset_routing():
                st.session_state.tide_calc_run = False
                
            direction = st.radio("Hướng đi", ["⬆️ Outbound (Đi ra)", "⬇️ Inbound (Đi vào)"], label_visibility="collapsed", on_change=reset_routing)
        else:
            show_ub = True; show_b = True; grp = None; m_sel = None

    if selected_tab == "CÁI MÉP":
        note_cm = ":red[*Window is calculated for vessels LOA ≤ 300m; Draft ≤ 12.5m; GRT ≤ 80.000. The vessels: Draft > 12.5m; LOA > 300m; GRT > 80.000 is advised by Duty Pilot*]"
        render_window_tab(DATA_FILE, "WindowCM", show_past_global, note_cm, show_ub, show_b)
    elif selected_tab == "CÁT LÁI":
        note_cl = "*The vessels: Draft > 10.0m or Departure outside Window must be advised by the duty pilot.*"
        render_window_tab(DATA_FILE, "WindowCL", show_past_global, note_cl, show_ub, show_b)
    elif selected_tab == "Tide Calc CÁT LÁI":  
        render_tide_calc_tab(direction)
    elif selected_tab == "Max Draft Table":
        render_max_draft_tab(config, grp, m_sel)
    
    # --- ĐÃ SỬA CHỖ NÀY ĐỂ GỌI TAB CHANNEL INFOR ---
    elif selected_tab == "Channel Infor":
        render_channel_info_tab()

elif current_page == "⚙️ Quản lý hệ thống":
    # GIẤU ADMIN KHỎI URL
    if "tab" in st.query_params:
        del st.query_params["tab"]

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
    # Gom tất cả: Đường kẻ trên -> Phiên bản/Countdown -> Tên tác giả -> Đường kẻ dưới vào 1 khối
    st.markdown(f'''
        <hr style="margin: 8px 0 4px 0; border: 0; border-top: 1px solid #ddd;">
        <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.85em; line-height: 1.2;">
            <span style="font-weight: bold;">V 1.25</span>
            <span id="sidebar-countdown" style="color: #ff4b4b; font-weight: bold;"></span>
        </div>
        <div style="margin-top: 1px;">
            <i style="font-size: 0.75em; color: gray; display: block;">Built by @Hai.PT(NP44)</i>
        </div>
        <hr style="margin: 4px 0 8px 0; border: 0; border-top: 1px solid #ddd;">
    ''', unsafe_allow_html=True)

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
                Người dùng bắt buộc phải đối chiếu với bảng thủy triều chính thức (VMS-South).
                <br><br>
                <i>Bằng việc sử dụng website này, bạn đồng ý chấp nhận mọi rủi ro và từ bỏ mọi quyền khiếu nại pháp lý đối với nhà phát triển.</i>
            </div>
        """, unsafe_allow_html=True)

import streamlit as st
import datetime
from utils.data_processor import get_max_draft_raw_data, style_max_draft_table
import streamlit.components.v1 as components

def render_max_draft_tab():
    config = st.session_state.config
    
    # =================================================================
    # 1. GIAO DIỆN CONTROL (1 Hàng duy nhất, không label thừa)
    # =================================================================
    with st.container(border=True):
        # Chia 3 cột: Sông (nhỏ) - Tháng (vừa) - Nút In (nhỏ)
        col1, col2, col_print = st.columns([2, 3, 1.5])
        
        with col1:
            grp_choice = st.selectbox("Sông", ["🌊 LÒNG TÀU", "🌊 SOÀI RẠP"], label_visibility="collapsed")
            grp = grp_choice.replace("🌊 ", "") 
            
        with col2:
            m_options = ["📅 Mặc định (Hiện tại -> Hết tháng)"] + [f"📅 Tháng {i}" for i in range(1, 13)]
            m_choice = st.selectbox("Tháng", m_options, label_visibility="collapsed")
            
            if "Mặc định" in m_choice:
                month_sel = f"Tháng {datetime.datetime.now().month}"
            else:
                month_sel = m_choice.replace("📅 ", "")
                
        with col_print:
            print_mode = st.toggle("🖨️ BẬT CHẾ ĐỘ IN", value=False)

    st.markdown("<hr style='margin: 5px 0 15px 0; border-top: 1px solid #ccc;'>", unsafe_allow_html=True)
    
    # =================================================================
    # 2. XỬ LÝ DỮ LIỆU & BẢNG
    # =================================================================
    with st.spinner("Đang tính toán số liệu..."):
        df_raw = get_max_draft_raw_data(config, grp, month_sel)
        if df_raw is not None and not df_raw.empty:
            styled_df = style_max_draft_table(df_raw)
            vis_cols = [c for c in styled_df.data.columns if c not in ["_dow", "_sort"]]
            
            # --- PHÂN NHÁNH HIỂN THỊ (IN ẤN VS WEB) ---
            if print_mode:
                html_table = styled_df.hide().set_table_attributes('class="print-max-draft"').to_html()
                
                html_content = f"""
<style>
@media print {{
    @page {{ size: A4 landscape; margin: 10mm; }}
    
    /* 1. TÀNG HÌNH CÁC THÀNH PHẦN STREAMLIT MẶC ĐỊNH */
    [data-testid="stSidebar"], header, hr {{ display: none !important; }}
    
    /* 2. XÓA SẠCH NỘI DUNG RUỘT CỦA CÁC CỘT CHỨA NÚT */
    [data-testid="stHorizontalBlock"] {{ display: none !important; }}
    .stSelectbox, .stToggle {{ display: none !important; }}
    
    /* 3. LỆNH HỦY DIỆT: ĐẬP VỠ MỌI VỎ HỘP TRỐNG (Bóng ma khung viền) */
    div {{ 
        border: none !important; 
        box-shadow: none !important; 
        background: transparent !important; 
    }}
    
    /* Ép sập các class vỏ bọc của Streamlit xuống 0px */
    div[class*="borderWrapper"], div[class*="BorderWrapper"] {{ 
        display: none !important; 
        padding: 0 !important; 
        margin: 0 !important; 
    }}
    
    .stApp {{ background-color: white !important; }}
    .block-container {{ margin-top: 0px !important; padding-top: 0px !important; }}
}}

/* ==========================================
   CẤU HÌNH BẢNG IN CHỐNG GÃY TRANG 
   ========================================== */
.print-max-draft {{ 
    width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; text-align: center; margin-top: 0px; 
}}

/* Lặp tiêu đề cột khi sang trang mới */
.print-max-draft thead {{ display: table-header-group !important; }}

/* Ép nguyên khối 1 ngày sang trang, không cắt ngang */
.print-max-draft tr {{ page-break-inside: avoid !important; break-inside: avoid !important; }}

.print-max-draft th, .print-max-draft td {{ 
    border: 1px solid #444 !important; 
    padding: 5px 2px !important; 
    font-size: 11.5px !important; 
    white-space: nowrap !important; /* Chống rớt dòng các con số */
}}

.print-max-draft th {{ 
    background-color: #ffe699 !important; 
    color: #111 !important; 
    font-weight: bold !important;
    font-size: 12px !important;
    -webkit-print-color-adjust: exact; 
    print-color-adjust: exact; 
}}
</style>

<div style='font-size: 18px; font-weight: bold; text-align: center; color: #111; margin-bottom: 8px; text-transform: uppercase;'>
    BẢNG MAX DRAFT - {grp} ({month_sel})
</div>
{html_table}
"""
                st.markdown(html_content, unsafe_allow_html=True)
                
                # JAVASCRIPT: Gom nhóm các dòng cùng 1 ngày thành 1 khối để in liền mạch
                components.html("""
                <script>
                    const doc = window.parent.document;
                    let attempts = 0;
                    const interval = setInterval(() => {
                        const table = doc.querySelector('.print-max-draft:not(.grouped)');
                        if (table) {
                            table.classList.add('grouped');
                            const tbody = table.querySelector('tbody');
                            if (tbody) {
                                const rows = Array.from(tbody.querySelectorAll('tr'));
                                let currentTbody = null;
                                rows.forEach(row => {
                                    const firstCell = row.querySelector('th') || row.querySelector('td');
                                    if (firstCell && firstCell.textContent.trim().length > 0) {
                                        currentTbody = doc.createElement('tbody');
                                        currentTbody.style.setProperty('page-break-inside', 'avoid', 'important');
                                        currentTbody.style.setProperty('border-bottom', '2.5px solid #111', 'important');
                                        table.appendChild(currentTbody);
                                    }
                                    if (currentTbody) {
                                        currentTbody.appendChild(row);
                                    }
                                });
                                if (tbody.children.length === 0) tbody.remove();
                            }
                            clearInterval(interval);
                        }
                        attempts++;
                        if (attempts > 10) clearInterval(interval);
                    }, 200);
                </script>
                """, height=0, width=0)

            else:
                # GIAO DIỆN WEB: Cố định cột
                col_cfg = {
                    "_dow": None, 
                    "_sort": None, 
                    "Date": st.column_config.TextColumn("Date", pinned=True), 
                    "Point": st.column_config.TextColumn("Point", pinned=True)
                }
                st.dataframe(styled_df, use_container_width=False, hide_index=True, height=800, column_config=col_cfg, column_order=vis_cols)
        else:
            st.warning("❌ Không tìm thấy dữ liệu cho lựa chọn này.")
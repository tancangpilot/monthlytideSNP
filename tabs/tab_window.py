import streamlit as st
import pandas as pd
import os
from utils.data_processor import process_and_style_df
import streamlit.components.v1 as components

def render_window_tab(file_path, sheet_name, disclaimer_text):
    
    # --- KHU VỰC NÚT BẬT IN ---
    c1, c2 = st.columns([3, 1])
    with c2:
        print_mode = st.toggle("🖨️BẬT CHẾ ĐỘ IN (A4 Dọc)", value=False)
        
    with c1:
        if not print_mode:
            st.markdown(disclaimer_text)

    # --- KHU VỰC ĐIỀU KHIỂN NẰM NGAY TRÊN BẢNG ---
    if not print_mode:
        with st.container(border=True):
            col_c1, col_c2, col_c3, col_c4 = st.columns(4)
            with col_c1: show_past = st.toggle("Hiện ngày đã qua", value=False)
            with col_c2: st.session_state.show_full_cols = st.toggle("Hiển thị đủ tên cột", value=False)
            with col_c3: show_ub = st.toggle("Ẩn/Hiện UB (Rời)", value=True)
            with col_c4: show_b = st.toggle("Ẩn/Hiện B (Cập)", value=True)
    else:
        show_past = False
        st.session_state.show_full_cols = False
        show_ub = True
        show_b = True

    if os.path.exists(file_path):
        try:
            df_raw = pd.read_excel(file_path, sheet_name=sheet_name)
            df_raw.columns = [str(c).strip() for c in df_raw.columns] 
            
            cols_to_keep = list(df_raw.columns)
            if not show_ub:
                cols_to_keep = [c for c in cols_to_keep if "UB" not in str(c)]
            if not show_b:
                cols_to_keep = [c for c in cols_to_keep if not (" B-" in str(c) and "UB" not in str(c))]

            df_filtered = df_raw[cols_to_keep]
            styled_df = process_and_style_df(df_filtered, show_past_dates=show_past)
            
            # =========================================================
            # PHÂN NHÁNH HIỂN THỊ (IN ẤN VS WEB)
            # =========================================================
            if print_mode:
                # .hide() sẽ loại bỏ cột số thứ tự (Index) khi xuất HTML
                html_table = styled_df.hide().set_table_attributes('class="print-window"').to_html()
                
                # Làm sạch dòng ghi chú để in
                raw_note = disclaimer_text.replace(":red[", "").replace("]", "").replace("*", "")
                
                # Xác định tên sông để làm tiêu đề
                display_name = "CÁI MÉP" if "CM" in sheet_name else "CÁT LÁI"
                
                html_content = f"""
<style>
@media print {{
    @page {{ size: A4 portrait; margin: 10mm; }}
    [data-testid="stSidebar"], header, .stToggle, .stCheckbox, .stRadio {{ display: none !important; }}
    .stApp {{ background-color: white !important; }}
    
    /* Cắt triệt để khoảng trắng thừa ở trang 1 */
    .block-container {{ margin-top: 0px !important; padding-top: 0px !important; }}
}}

/* ==========================================
   CẤU HÌNH BẢNG IN CHỐNG GÃY TRANG 
   ========================================== */
.print-window {{ 
    width: 100%; border-collapse: collapse; font-family: Arial, sans-serif; text-align: center; margin-top: 5px; 
}}

/* Lặp lại dải băng Tiêu đề cột ở đầu mỗi trang mới */
.print-window thead {{
    display: table-header-group !important;
}}

.print-window th, .print-window td {{ 
    border: 1px solid #444 !important; 
    padding: 5px 2px !important; 
    font-size: 11.5px !important; 
    white-space: nowrap !important; /* Chống rớt chữ các con số */
}}

.print-window th {{ 
    background-color: #ffe699 !important; 
    color: #111 !important; 
    font-weight: bold !important;
    font-size: 12px !important;
    -webkit-print-color-adjust: exact; 
    print-color-adjust: exact; 
}}
</style>

<div style='font-size: 18px; font-weight: bold; text-align: center; color: #111; margin-bottom: 2px; text-transform: uppercase;'>
    BẢNG WINDOW {display_name}
</div>
<div style='font-size: 11.5px; font-style: italic; text-align: center; color: #d93025; margin-bottom: 8px; line-height: 1.4;'>
    {raw_note}
</div>
{html_table}
"""
                st.markdown(html_content, unsafe_allow_html=True)
                
                # --- JAVASCRIPT: PHẪU THUẬT NHÓM NGÀY ĐỂ CHỐNG XÉ LẺ BẢN IN ---
                components.html("""
                <script>
                    const doc = window.parent.document;
                    let attempts = 0;
                    const interval = setInterval(() => {
                        const table = doc.querySelector('.print-window:not(.grouped)');
                        if (table) {
                            table.classList.add('grouped');
                            const tbody = table.querySelector('tbody');
                            if (tbody) {
                                const rows = Array.from(tbody.querySelectorAll('tr'));
                                let currentTbody = null;
                                rows.forEach(row => {
                                    const firstCell = row.querySelector('td');
                                    // Bắt tín hiệu: Nếu ô đầu tiên có chứa text (Ngày) -> Tạo 1 cái bọc tbody mới!
                                    if (firstCell && firstCell.textContent.trim().length > 0) {
                                        currentTbody = doc.createElement('tbody');
                                        // Khóa cứng: Ép máy in không được xé lẻ cái bọc này
                                        currentTbody.style.setProperty('page-break-inside', 'avoid', 'important');
                                        currentTbody.style.setProperty('break-inside', 'avoid', 'important');
                                        // Thêm dòng kẻ đậm phân cách giữa các ngày cho dễ nhìn
                                        currentTbody.style.setProperty('border-bottom', '2.5px solid #111', 'important');
                                        table.appendChild(currentTbody);
                                    }
                                    if (currentTbody) {
                                        currentTbody.appendChild(row);
                                    }
                                });
                                // Hủy cái bọc mặc định rỗng tuếch của Pandas
                                if (tbody.children.length === 0) {
                                    tbody.remove();
                                }
                            }
                            clearInterval(interval);
                        }
                        attempts++;
                        if (attempts > 10) clearInterval(interval); // Dừng thử sau 2 giây nếu không có bảng
                    }, 200);
                </script>
                """, height=0, width=0)

            else:
                # CHẾ ĐỘ WEB
                col_settings = {
                    "_dow": None, 
                    "_actual_date": None, 
                    "Date": st.column_config.TextColumn("Date", pinned=True)
                }
                
                for original_col in styled_df.data.columns:
                    if original_col in ["Date", "_dow", "_actual_date", "Level", "Dir", "Slack", "VungTau"]:
                        continue
                    
                    col_settings[original_col] = st.column_config.TextColumn(
                        original_col, 
                        help="*(B/E: Begin/End | UB/B: Unberthing/Berthing | P/Stb: Port/Starboard)*"
                    )
                
                st.dataframe(styled_df, use_container_width=False, height=750, hide_index=True, column_config=col_settings)
                
        except Exception as e:
            st.error(f"Lỗi hiển thị: {e}")
    else:
        st.warning(f"Không tìm thấy file dữ liệu.")
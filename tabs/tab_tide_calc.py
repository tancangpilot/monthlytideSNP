import streamlit as st
import datetime

def render_tide_calc_tab():
    # 1. CHỌN HƯỚNG ĐI (Đảo Outbound lên trước)
    direction = st.radio(
        "Hướng đi", 
        ["⬆️ Outbound (Đi ra)", "⬇️ Inbound (Đi vào)"], 
        horizontal=True,
        label_visibility="collapsed"
    )
    
    # 2. CHỌN TUYẾN (Ẩn luôn nhãn "Chọn tuyến" cho gọn)
    if "Outbound" in direction:
        routes = [
            "1. Cát Lái ➔ Lòng Tàu ➔ P0 VT", 
            "2. Cát Lái ➔ Soài Rạp ➔ P0 SR (Hỗn hợp)", 
            "3. TC Hiệp Phước ➔ Soài Rạp ➔ P0 SR"
        ]
    else:
        routes = [
            "1. P0 VT ➔ Lòng Tàu ➔ Cát Lái", 
            "2. P0 SR ➔ Soài Rạp ➔ TC Hiệp Phước"
        ]
    route_sel = st.selectbox("Route", routes, label_visibility="collapsed")
    
    st.divider()

    # 3. CHỌN 1 TRONG 3 BÀI TOÁN (Không chọn mặc định cái nào)
    calc_options = [
        "-- Vui lòng chọn bài toán --",
        "Opt 1: Nhập POB Time & Draft để kiểm tra an toàn",
        "Opt 2: Nhập POB Date & Draft tìm Giờ POB an toàn",
        "Opt 3: Nhập POB Date để tìm Giờ tối ưu Max Draft"
    ]
    selected_opt = st.selectbox("Chọn Option", calc_options, label_visibility="collapsed")

    # 4. KHU VỰC HIỂN THỊ INPUT & NÚT PROCESS DỰA TRÊN OPTION ĐÃ CHỌN
    if selected_opt != "-- Vui lòng chọn bài toán --":
        # Dùng một khung (container) mỏng bao quanh cho khu vực nhập liệu có điểm nhấn
        with st.container(border=True):
            
            # --- OPTION 1: CHECK AN TOÀN ---
            if selected_opt == calc_options[1]:
                c1, c2, c3 = st.columns(3)
                with c1: pob_date = st.date_input("POB Date", datetime.date.today())
                with c2: pob_time = st.time_input("POB Time", datetime.time(8, 0))
                with c3: draft = st.number_input("Draft (m)", min_value=0.0, value=10.0, step=0.1)
                
                if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                    st.info(f"🔍 **Đang kiểm tra Tuyến:** {route_sel} \n\n🕒 **POB:** {pob_date.strftime('%d/%m/%Y')} lúc {pob_time.strftime('%H:%M')} | 🚢 **Draft:** {draft}m")
                    # TODO: Lắp thuật toán chạy Opt 1 vào đây
                    
            # --- OPTION 2: TÌM GIỜ POB ---
            elif selected_opt == calc_options[2]:
                c1, c2 = st.columns(2)
                with c1: pob_date = st.date_input("POB Date", datetime.date.today())
                with c2: draft = st.number_input("Draft (m)", min_value=0.0, value=10.0, step=0.1)
                
                if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                    st.success(f"🎯 **Đang quét tìm Giờ POB cho Tuyến:** {route_sel} \n\n📅 **Ngày:** {pob_date.strftime('%d/%m/%Y')} | 🚢 **Draft:** {draft}m")
                    # TODO: Lắp thuật toán chạy Opt 2 vào đây
                    
            # --- OPTION 3: TÌM MAX DRAFT ---
            elif selected_opt == calc_options[3]:
                # Tối ưu Max Draft thì chỉ cần mỗi Ngày
                pob_date = st.date_input("POB Date", datetime.date.today())
                
                if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                    st.warning(f"📈 **Đang tối ưu Max Draft cho Tuyến:** {route_sel} \n\n📅 **Ngày:** {pob_date.strftime('%d/%m/%Y')}")
                    # TODO: Lắp thuật toán chạy Opt 3 vào đây
                    
        # Khu vực này để trống, sau khi bấm Process thì kết quả bảng biểu sẽ tự động nở ra ở dưới cùng
        st.markdown("<br>", unsafe_allow_html=True)
import streamlit as st
import datetime

# Hàm tính giờ hiện tại làm chẵn theo 30 phút
def get_rounded_time():
    now = datetime.datetime.now()
    # Nếu phút >= 15 thì làm tròn lên 30, nếu >= 45 thì làm tròn lên giờ tiếp theo
    minutes = (now.minute // 30 + (1 if now.minute % 30 >= 15 else 0)) * 30
    rounded_dt = now.replace(minute=0, second=0, microsecond=0) + datetime.timedelta(minutes=minutes)
    return rounded_dt.time()

# Nhận biến route_sel từ app.py truyền sang
def render_tide_calc_tab(route_sel):
    
    st.markdown(f"**Tuyến đang chọn:** `{route_sel}`")
    
    # CHỌN 1 TRONG 3 BÀI TOÁN (Tên chuẩn mới)
    calc_options = [
        "🔍 Opt1: Kiểm tra AN TOÀN (Nhập POB và Draft)",
        "🎯 Opt2: Tìm giờ POB (Nhập POB Date & Draft)",
        "📈 Opt3: Tìm giờ POB và Max draft (Chỉ nhập POB Date)"
    ]
    
    selected_opt = st.radio(
        "Chọn bài toán:", 
        calc_options,
        label_visibility="collapsed" 
    )

    # Lấy các giá trị mặc định
    default_date = datetime.date.today()
    default_time = get_rounded_time()
    default_draft = 10.5

    # KHU VỰC HIỂN THỊ INPUT & PROCESS NỞ RA TƯƠNG ỨNG
    with st.container(border=True):
        
        # --- OPTION 1: KIỂM TRA AN TOÀN ---
        if selected_opt == calc_options[0]:
            c1, c2, c3 = st.columns(3)
            with c1: pob_date = st.date_input("POB Date", default_date)
            with c2: pob_time = st.time_input("POB Time", default_time)
            with c3: draft = st.number_input("Draft (m)", min_value=0.0, value=default_draft, step=0.1)
            
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                st.info(f"🔍 **Đang kiểm tra Tuyến:** {route_sel} \n\n🕒 **POB:** {pob_date.strftime('%d/%m/%Y')} lúc {pob_time.strftime('%H:%M')} | 🚢 **Draft:** {draft}m")
                
        # --- OPTION 2: TÌM GIỜ POB ---
        elif selected_opt == calc_options[1]:
            c1, c2 = st.columns(2)
            with c1: pob_date = st.date_input("POB Date", default_date)
            with c2: draft = st.number_input("Draft (m)", min_value=0.0, value=default_draft, step=0.1)
            
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                st.success(f"🎯 **Đang quét tìm Giờ POB cho Tuyến:** {route_sel} \n\n📅 **Ngày:** {pob_date.strftime('%d/%m/%Y')} | 🚢 **Draft:** {draft}m")
                
        # --- OPTION 3: TÌM MAX DRAFT ---
        elif selected_opt == calc_options[2]:
            pob_date = st.date_input("POB Date", default_date)
            
            if st.button("🚀 PROCESS", use_container_width=True, type="primary"):
                st.warning(f"📈 **Đang tối ưu Max Draft cho Tuyến:** {route_sel} \n\n📅 **Ngày:** {pob_date.strftime('%d/%m/%Y')}")

    st.markdown("<br>", unsafe_allow_html=True)
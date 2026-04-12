import pandas as pd
import datetime
import os
import streamlit as st

def process_and_style_df(df, show_past_dates=False):
    df = df.dropna(how='all').copy()
    df.columns = [str(c).strip() for c in df.columns]
    if 'VungTau' in df.columns:
        df = df.dropna(subset=['VungTau']).copy()
        
    if 'Date' in df.columns:
        raw_dates = pd.to_datetime(df['Date'], errors='coerce')
        is_valid_date = raw_dates.apply(lambda x: pd.notna(x) and x.year > 2000)
        
        real_dates = raw_dates.where(is_valid_date).bfill(limit=1).ffill()
        df['_actual_date'] = real_dates
        df['_dow'] = real_dates.dt.dayofweek
        
        if not show_past_dates:
            today = pd.Timestamp.today().normalize()
            mask = (df['_actual_date'] >= today) | (df['_actual_date'].isna())
            df = df[mask].copy()

        display_dates = []
        last_date = None
        for idx, row in df.iterrows():
            current_date = row['_actual_date']
            if pd.notna(current_date) and current_date != last_date:
                display_dates.append(current_date.strftime("%d/%m"))
                last_date = current_date
            else:
                display_dates.append("")
        df['Date'] = display_dates
        
        if not st.session_state.get('show_full_cols', True):
            rename_map = {
                "Begin UB-Port": "B.UB-P", "End UB-Port": "E.UB-P",
                "Begin UB-Starboard": "B.UB-Stb", "End UB-Starboard": "E.UB-Stb",
                "Begin B-Port": "B.B-P", "End B-Port": "E.B-P",
                "Begin B-Starboard": "B.B-Stb", "End B-Starboard": "E.B-Stb"
            }
            df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

        cols = ['Date'] + [c for c in df.columns if c not in ['Date', '_dow', '_actual_date']] + ['_dow', '_actual_date']
        df = df[cols]

    def to_hhmm(v):
        if pd.isna(v) or str(v).strip() in ["", "nan"]: return ""
        if isinstance(v, datetime.time):
            return v.strftime("%H:%M")
        vs = str(v).strip()
        if len(vs) >= 8 and vs[2] == ':' and vs[5] == ':': return vs[:5]
        if len(vs) >= 5 and vs[2] == ':': return vs[:5]
        return vs

    for col in df.columns:
        if col not in ['Date', 'Level', 'Dir', '_dow', '_actual_date']:
            df[col] = df[col].apply(to_hhmm)

    for col in df.columns:
        if col not in ['_dow', '_actual_date']:
            df[col] = df[col].astype(str).replace('nan', '')

    def style_row(row):
        styles = []
        day_idx = row.get('_dow', -1)
        bg = ""
        
        # 1. LÀM DỊU MÀU NỀN CUỐI TUẦN (Chuyển sang tone Pastel êm mắt)
        if day_idx == 5: # Thứ 7
            bg = "background-color: rgba(255, 99, 71, 0.15);" # Cũ là 0.25
        elif day_idx == 6: # Chủ Nhật
            bg = "background-color: rgba(255, 0, 0, 0.12);"   # Cũ là 0.35
        
        base_css = bg + "font-size: 15px; " 
        
        for col_name, val in row.items():
            css = base_css 
            val_str = str(val)
            if 'Dir' in str(col_name):
                if '↙' in val_str: css += "color: #cc0000; font-weight: bold; font-size: 17px;"
                elif '↗' in val_str: css += "color: #008000; font-weight: bold; font-size: 17px;"
            elif 'Port' in str(col_name) or '-P' in str(col_name):
                # Ép đỏ sậm cho chữ mạn Trái dễ đọc trên nền hồng
                css += "color: #cc0000; font-weight: bold;"
            elif 'Stb' in str(col_name) or 'Starboard' in str(col_name):
                # 2. ĐỔI MÀU XANH STARBOARD THÀNH XANH LỤC BẢO ĐẬM (Forest Green)
                css += "color: #008000; font-weight: bold;" 
            elif 'UB' in str(col_name) or ' B' in str(col_name):
                css += "font-weight: bold;"
            styles.append(css)
        return styles

    styler = df.style.apply(style_row, axis=1).set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#ffe699 !important'), ('color', '#111 !important')]}
    ])
    
    if hasattr(styler, "hide"):
        return styler.hide(subset=["_dow", "_actual_date"], axis="columns")
    else:
        return styler.hide_columns(["_dow", "_actual_date"])


@st.cache_data(show_spinner=False)
def get_max_draft_raw_data(config, group_mode, month_sel, file_path="data_tide.xlsx"):
    if not os.path.exists(file_path): 
        st.error(f"Thiếu file {file_path}")
        return None
    
    groups = {"LÒNG TÀU": ["HL27", "HL21", "HL6"], "SOÀI RẠP": ["VL", "TCHP", "BB"]}
    points = groups[group_mode]
    
    month_map = {}
    months_en = ["january", "february", "march", "april", "may", "june", "july", "august", "september", "october", "november", "december"]
    for i, m in enumerate(months_en, 1):
        month_map[m] = i; month_map[m[:3]] = i  
    for i in range(1, 13):
        month_map[str(i)] = i; month_map[f"{i}.0"] = i 
        month_map[f"tháng {i}"] = i; month_map[f"thang {i}"] = i
        month_map[f"tháng{i}"] = i; month_map[f"thang{i}"] = i
        
    final_list = []
    try:
        xl = pd.ExcelFile(file_path)
        today = pd.Timestamp.today().normalize()
        year = today.year 
        
        target_month_num = None
        if month_sel != "Mặc định (Hiện tại -> Hết tháng)":
            target_month_num = int(month_sel.split()[-1])

        for p in points:
            if p not in xl.sheet_names: continue
            df_raw = pd.read_excel(file_path, header=None, sheet_name=p)
            ukc_day, ukc_night = config["ukc_day"]/100.0, config["ukc_night"]/100.0
            depth = float(config[p.lower()])

            current_month = today.month 
            day_count = 0
            
            for i in range(len(df_raw)):
                row = df_raw.iloc[i]
                col0_val = str(row[0]).strip().lower()
                col1_val = str(row[1]).strip().lower()
                
                if col0_val in month_map: current_month = month_map[col0_val]; day_count = 0
                
                is_numeric_day = False
                try: day_count = int(float(col1_val)); is_numeric_day = True
                except ValueError: pass

                if is_numeric_day: pass
                elif col1_val in ["cn", "t2", "t3", "t4", "t5", "t6", "t7"]: day_count += 1
                else: continue 

                try: dt = pd.Timestamp(year, current_month, day_count)
                except ValueError: continue
                
                if target_month_num:
                    if dt.month != target_month_num: continue
                else:
                    if dt < today or dt.month != today.month: continue

                res_row = {"Date": dt.strftime("%d/%m"), "Point": p, "_dow": dt.dayofweek, "_sort": dt}
                for h in range(24):
                    h_col = f"{h:02d}"
                    if (h + 2) < len(row): tide_val = pd.to_numeric(row[h+2], errors='coerce')
                    else: tide_val = float('nan')
                        
                    u = ukc_day if (6 <= h <= 17) else ukc_night
                    if pd.notna(tide_val): 
                        res_row[h_col] = f"{(tide_val + depth) / (1 + u):.1f}"
                    else: res_row[h_col] = ""
                        
                final_list.append(res_row)
                
    except Exception as e: 
        st.error(f"Lỗi hệ thống: {e}")
        return None

    if not final_list: return None
    
    df_res = pd.DataFrame(final_list).sort_values(by=["_sort", "Point"])
    mask = df_res['Date'].duplicated()
    df_res.loc[mask, 'Date'] = ""
    
    return df_res

def style_max_draft_table(df_res):
    def style_sum(row):
        day_idx = row.get("_dow", -1)
        bg = ""
        if day_idx == 5: bg = "background-color: rgba(255, 99, 71, 0.25);"
        elif day_idx == 6: bg = "background-color: rgba(255, 0, 0, 0.35);"
        else: bg = "background-color: rgba(50, 150, 250, 0.15);"
        
        css = bg + "font-size: 13px; " # Giảm 1px cho Max Draft Table như ông yêu cầu
        return [css] * len(row)

    styler = df_res.style.apply(style_sum, axis=1).set_table_styles([
        {'selector': 'th', 'props': [('background-color', '#ffe699 !important'), ('color', '#111 !important')]}
    ])
    
    if hasattr(styler, "hide"):
        return styler.hide(subset=["_dow", "_sort"], axis="columns")
    else:
        return styler.hide_columns(["_dow", "_sort"])
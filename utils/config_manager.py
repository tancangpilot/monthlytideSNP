import json
import os

CONFIG_FILE = "config_app.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            c = json.load(f)
            
            # Cập nhật danh sách quét có thêm trạm "cm"
            for k in ["bb", "vl", "tchp", "hl6", "hl21", "hl27", "cm"]:
                if k in c: c[k] = abs(float(c[k]))
            
            # TỰ ĐỘNG CỨU HỘ: Bơm thêm trạm CM nếu file JSON cũ của ông chưa có
            if "cm" not in c:
                c["cm"] = 14.0
                save_config(c)
                
            return c
            
    # Giá trị mặc định nếu chưa có file config
    return {
        "logged_in": False, "ukc_day": 7, "ukc_night": 10,
        "hl6": 8.8, "hl21": 8.5, "hl27": 8.5, 
        "bb": 6.7, "vl": 8.0, "tchp": 8.0,
        "cm": 14.0,  # <-- Đã thêm độ sâu mặc định cho tuyến Cái Mép
        "last_updated": "Chưa có dữ liệu"
    }

def save_config(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
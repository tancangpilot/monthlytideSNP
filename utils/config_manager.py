import json
import os

CONFIG_FILE = "config_app.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            c = json.load(f)
            for k in ["bb", "vl", "tchp", "hl6", "hl21", "hl27"]:
                if k in c: c[k] = abs(float(c[k]))
            return c
    return {
        "logged_in": False, "ukc_day": 7, "ukc_night": 10,
        "hl6": 8.8, "hl21": 8.5, "hl27": 8.5, 
        "bb": 6.7, "vl": 8.0, "tchp": 8.0,
        "last_updated": "Chưa có dữ liệu"
    }

def save_config(config_data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config_data, f, indent=4)
import json
import os

# 1. 依照完整規範組合 SSOT 遙測數據 Payload
payload = {
    "system": {
        "timestamp": "2026-09-11 11:30:00 CST",
        "status": "OPERATIONAL"
    },
    "tactical_decision": {
        "q_mode": "🔴 Q4 嚴禁靠泊",
        "reason": "Hs_pier 及 W_local 觸發剛性 VETO 封鎖",
        "dispatch_status": "NO_DISPATCH (雙岸閉塞)",
        "veto_pass": False
    },
    "veto_matrix": {
        "hs_pier": {"val": 3.23, "status": "VETO"},
        "w_local": {"val": 13.50, "status": "VETO"},
        "ukc": {"val": 1.00, "status": "VETO"},
        "fb_pier": {"val": 0.15, "status": "VETO"}
    },
    "typhoon_qimen_prediction": {
        "cyclone_dynamic": "東南東 450 km 中颱 (45m/s)，暴風半徑 200km。",
        "qimen_anomaly_forecast": "巽宮氣場異常，長浪共振頻繁。"
    }
}

# 2. 寫入專案根目錄的 latest_decision.json (對齊 HTML 讀取檔名)
with open('latest_decision.json', 'w', encoding='utf-8') as f:
    json.dump(payload, f, ensure_ascii=False, indent=2)

# 3. 自動 Commit 並 Push 回儲存庫觸發 Pages 更新
os.system('git config user.name "github-actions[bot]"')
os.system('git config user.email "github-actions@github.com"')
os.system('git add latest_decision.json')
os.system('git commit -m "Auto-update telemetry data (SSOT)"')
os.system('git push')

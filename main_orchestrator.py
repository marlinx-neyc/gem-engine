#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
================================================================================
GEM-V36D 龜山島海象氣-數值分析、周易易數同化與 SSOT 最高統合系統 (v36D.330.0 Master Complete)
================================================================================
專家角色定位：
精通周易、奇門遁甲兼天文、氣象學、海河工程學之數值模型分析與建構專家
兼 龜山島海象氣-數值分析與智庫首席海事戰術架構師

系統核心機制：
1. 兩位階決策體系：
   - 第一位階 (100% 硬阻斷權)：四層 Hard VETO 剛性物理防線 (Hs, Weff, UKC, FB)。
   - 第二位階 (最大 35% 偏置)：周易象數與奇門 70% 門控同化 (物理 PASS 時無權單獨熔斷)。
2. 四層 Hard VETO 水動力算子矩陣與自適應門檻緊縮 (alpha_tune)。
3. Level 5 高維邊緣算子 (Vision-PINN, MMSI, FNO, Quantum Topology, Swarm Dispatch)。
4. Level 7 南北角雙碼頭水動力矩陣與天文潮差動態扣減算子。
5. 游擊式動態調度、牛奶海熱泉避險時窗 (T_peak = T_HighTide + 3.5h ± 1.5h) 與撤離時間精算。
6. Gymnasium 10D 狀態向量強化學習代理人 (RL Policy Net) 零延遲硬掩碼熔斷。
7. 單一真實數據源 (SSOT) JSON 檔案輸出 (`latest_decision.json`)。
================================================================================
"""

import math
import json
import os
import sys
import datetime
from datetime import timezone, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, Any, Tuple, List, Optional

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim


# ==============================================================================
# 1. 安全數值解析算子 (Anti-Crash Safe Parsers)
# ==============================================================================
def safe_float(val: Any, default: float) -> float:
    """防止空值或無效字串引發系統 Crash 之安全浮點數轉譯器"""
    if val is None:
        return default
    try:
        v = float(val)
        return default if v < -90.0 else v
    except (ValueError, TypeError):
        return default


# ==============================================================================
# 2. 海事安全遙測與視訊 AI 資料結構 (Marine Safety Telemetry Schema)
# ==============================================================================
@dataclass
class MarineSafetyData:
    hs_cwa: float              # 官方 CWA 外海有效波高 (m)
    w_cwa: float               # 官方 CWA 風速 (m/s)
    tp_s: float                # 遠洋湧浪週期 (s)
    delta_theta_deg: float     # 風向攻角 / 背風偏角 (deg)
    tide_eta_m: float          # 動態潮位 (m)
    d_draft_m: float           # 船隻吃水深度 (m)
    s_quat_m: float            # 穿浪雙體船動態蹲沉量 Squat (m)
    chart_depth_m: float       # 碼頭水深 (m)
    current_speed_kts: float   # 沿岸橫流流速 (kts)
    qimen_consensus_pct: float # 奇門氣場同化率 (%)
    s_cos_sim: float           # 自適應歷史餘弦相似度 alpha_tune 基準
    high_tide_time_str: str    # 當日天文滿潮時間字串 (YYYY-MM-DD HH:MM:SS)
    video_overtopping_rate: float = 0.0 # Vision-PINN 越浪率 (p/min)
    video_kd_bias: float = 0.0          # 繞射消能殘差偏置
    passenger_count: int = 150          # 登島乘客總數
    slope_landslide_risk: float = 0.15  # 邊坡崩塌風險值
    official_closure_status: float = 0.0# 官方預警封島狀態 (0.0:無, 1.0:封島)

    @classmethod
    def from_api_json(cls, raw_data: Dict[str, Any]) -> 'MarineSafetyData':
        """自 API 或 SSOT JSON 載入並同化遙測數據"""
        cst_now = datetime.datetime.now(timezone(timedelta(hours=8)))
        default_high_tide = f"{cst_now.strftime('%Y-%m-%d')} 09:12:00"

        return cls(
            hs_cwa=safe_float(raw_data.get("hs_cwa"), 3.71),
            w_cwa=safe_float(raw_data.get("w_cwa"), 8.50),
            tp_s=safe_float(raw_data.get("tp_s"), 15.5),
            delta_theta_deg=safe_float(raw_data.get("delta_theta_deg"), 50.0),
            tide_eta_m=safe_float(raw_data.get("tide_eta_m"), 1.00),
            d_draft_m=safe_float(raw_data.get("d_draft_m"), 1.20),
            s_quat_m=safe_float(raw_data.get("s_quat_m"), 0.82),
            chart_depth_m=safe_float(raw_data.get("chart_depth_m"), 8.50),
            current_speed_kts=safe_float(raw_data.get("current_speed_kts"), 1.90),
            qimen_consensus_pct=safe_float(raw_data.get("qimen_consensus_pct"), 100.0),
            s_cos_sim=safe_float(raw_data.get("s_cos_sim"), 0.9421),
            high_tide_time_str=str

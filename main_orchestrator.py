#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
GEM Engine v66.0 Master Spatial-Dynamic Orchestrator
全域 SSOT 戰術指揮中樞 - GitHub 生產級整合版
==============================================================================
說明：
1. 本程式可直接於本機 terminal 執行 (`python main_orchestrator1024.py`)，
   自動生成可部署於 GitHub Pages 的 `index.html` 與決策狀態檔 `latest_decision.json`。
2. 同時完全相容於 Jupyter Notebook / Google Colab 環境渲染。
==============================================================================
"""

import asyncio
import datetime
import json
import logging
import math
import os
import sys
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np
import urllib3

# 關閉不必要的 urllib 警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - [%(levelname)s] - %(message)s"
)

try:
    from IPython.display import HTML, display
    HAS_IPYTHON = True
except ImportError:
    HAS_IPYTHON = False


# ==============================================================================
# 1. 剛性門檻與工程圖說配置 (EngineConfig)
# ==============================================================================
@dataclass(frozen=True)
class EngineConfig:
    """系統剛性門檻與港埠結構規格 (完全對齊工程竣工圖說 CD 基準面)"""
    BASE_LIMIT_HS: float = 1.13           # 港池浪高剛性上限 (1.13m)
    LIMIT_WEFF: float = 10.17             # 攻角有效風速剛性上限 (10.17m/s)
    LIMIT_UKC: float = 1.50              # 動態裕深剛性下限 (1.50m)
    LIMIT_FB: float = 0.50               # 預留乾舷剛性下限 (0.50m)
    GUISHAN_LAT: float = 24.843
    GUISHAN_LON: float = 121.952
    CHART_DEPTH_NORTH: float = 8.50       # 北岸主泊位水深 (-8.50m CD)
    CHART_DEPTH_SOUTH: float = 9.80       # 南岸權宜泊位水深 (-9.80m CD)
    NORTH_TRUSS_DECK_CD: float = 3.20     # 北岸鋼桁架引橋面頂高程 (+3.20m CD)
    SOUTH_CAISSON_DECK_CD: float = 2.50   # 南岸沉箱碼頭面頂高程 (+2.50m CD)
    VESSEL_STATIC_DRAFT: float = 2.02     # 客輪靜態吃水 (2.02m)


# ==============================================================================
# 2. 主控中樞編排器 (GEMMasterOrchestrator)
# ==============================================================================
class GEMMasterOrchestrator:
    """主控編排器，負責寫入 SSOT JSON 資料與生成前端靜態頁面"""
    def __init__(self):
        self.config = EngineConfig()

    async def execute_cycle(self):
        logging.info("🚀 GEM Engine v66.0 Master Orchestrator 啟動中...")
        now_cst = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        
        ssot_payload = {
            "version": "GEM-ENG-SPEC-2026-V66",
            "timestamp": now_cst.strftime("%Y-%m-%d %H:%M:%S CST"),
            "decision_code": "Q4",
            "decision": {
                "action_id": 0,
                "tactical_instruction": "🔴 0.0% 物理 VETO 熔斷 (全線封島)",
                "confidence": 100.0,
                "is_closed": True
            },
            "physics_metrics": {
                "hs_pier_m": 3.71,
                "w_local_ms": 5.46,
                "ukc_m": -0.80,
                "fb_pier_m": 0.15,
                "has_veto": True
            }
        }
        
        # 寫入 SSOT 檔案
        with open("latest_decision.json", "w", encoding="utf-8") as f:
            json.dump(ssot_payload, f, ensure_ascii=False, indent=2)
        logging.info("💾 決策 SSOT 檔案寫入完成：latest_decision.json")

        # 匯出 index.html 供 GitHub Pages 或本機服務使用
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(HTML_CONTENT)
        logging.info("🌐 前端 Dashboard HTML 寫入完成：index.html (GitHub Pages Ready)")


# ==============================================================================
# 3. 前端 UI HTML/JS 原始碼 (完全包含動態日期、雷達圖算子與剖面圖)
# ==============================================================================
HTML_CONTENT = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <title>🌊 GEM Engine v66.0 龜山島全域戰術指揮中樞 (Unified Master)</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        :root {
            --bg-dark: #080e1a;
            --card-bg: #111c2e;
            --card-border: #1e2d4a;
            --accent-blue: #38bdf8;
            --status-pass: #10b981;
            --status-warn: #f59e0b;
            --status-danger: #ef4444;
            --status-yellow: #facc15;
            --table-header-bg: rgba(56, 189, 248, 0.12);
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: var(--bg-dark); color: #f8fafc; padding: 10px; font-variant-numeric: tabular-nums; overflow-x: hidden; }
        button, input[type="range"], .tab-btn, summary { cursor: pointer !important; user-select: none; transition: all 0.15s ease-in-out; touch-action: manipulation; }
        button:hover, .tab-btn:hover { filter: brightness(1.2); transform: translateY(-1px); }
        @keyframes pulseAlert { 0%, 100% { opacity: 1; } 50% { opacity: 0.85; } }
        #vetoBanner { display: block; background: var(--status-danger); color: #ffffff; padding: 9px 12px; border-radius: 8px; font-weight: 800; font-size: 13px; margin-bottom: 12px; text-align: center; box-shadow: 0 0 18px rgba(239, 68, 68, 0.5); animation: pulseAlert 2s infinite; }
        .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 12px; padding: 12px; contain: content; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4); margin-bottom: 12px; width: 100%; }
        .card-header { font-size: 13.5px; font-weight: 800; color: var(--accent-blue); margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--card-border); padding-bottom: 6px; }
        .badge { font-size: 10.5px; font-weight: 700; padding: 2.5px 7px; border-radius: 4px; display: inline-block; white-space: nowrap; }
        .badge-veto { background: rgba(239, 68, 68, 0.25); color: #fca5a5; border: 1px solid var(--status-danger); }
        .badge-pass { background: rgba(16, 185, 129, 0.25); color: #86efac; border: 1px solid var(--status-pass); }
        .badge-yellow { background: rgba(250, 204, 21, 0.25); color: var(--status-yellow); border: 1px solid var(--status-yellow); }
        .data-table { width: 100%; border-collapse: collapse; font-size: 11px; border: 1px solid var(--card-border); border-radius: 6px; overflow: hidden; }
        .data-table th, .data-table td { padding: 5px 7px; text-align: left; border-bottom: 1px solid var(--card-border); }
        .data-table th { background: var(--table-header-bg); color: #e2e8f0; font-weight: 700; font-size: 10.5px; }
        .box-alert-danger { background: rgba(239, 68, 68, 0.16); border-left: 4px solid var(--status-danger); color: #fca5a5; padding: 8px 10px; font-size: 11.5px; border-radius: 0 6px 6px 0; line-height: 1.45; }
        .slider-item { display: flex; flex-direction: column; gap: 2px; }
        .slider-header { display: flex; justify-content: space-between; font-size: 10.5px; color: #cbd5e1; font-weight: 600; }
        .slider-header span.val { font-family: monospace; font-weight: 800; color: var(--accent-blue); font-size: 11.5px; }
        .slider-item input[type="range"] { width: 100%; height: 5px; background: #1e2d4a; border-radius: 3px; outline: none; accent-color: var(--accent-blue); }
        .canvas-container { position: relative; width: 100%; border-radius: 8px; overflow: hidden; background: #050a14; border: 1px solid #1e2d4a; }
        .tab-south-active { background: #059669 !important; color: #ffffff !important; border-color: #34d399 !important; box-shadow: 0 0 10px rgba(5, 150, 105, 0.5); }
        .tab-north-active { background: #2563eb !important; color: #ffffff !important; border-color: #60a5fa !important; box-shadow: 0 0 10px rgba(37, 99, 235, 0.5); }
        .tab-compare-active { background: #7c3aed !important; color: #ffffff !important; border-color: #a78bfa !important; box-shadow: 0 0 10px rgba(124, 58, 237, 0.5); }
    </style>
</head>
<body class="w-full max-w-[1700px] mx-auto">
    <div id="vetoBanner">🚨 警示：實體觸發物理 VETO 熔斷（浪高/風速/水深超標），強制執行防颱封島管制！</div>
    
    <header class="bg-[#111c2e] border border-[#1e2d4a] border-l-[6px] border-l-[#ef4444] rounded-xl p-3.5 mb-3 shadow-xl w-full" id="headerMaster">
        <div class="flex flex-wrap justify-between items-center gap-2">
            <div class="flex items-center gap-2.5">
                <span class="text-2xl">🌊</span>
                <div>
                    <h1 class="text-sm md:text-base font-extrabold text-white flex items-center gap-2">龜山島全域戰術指揮中樞 <span class="text-xs text-[#38bdf8] font-normal font-mono">(Unified RWD Master v66.0)</span></h1>
                    <div class="text-[10.5px] text-[#cbd5e1] mt-0.5 flex flex-wrap gap-2 items-center font-mono">
                        <span>時間：<b id="liveClock" class="text-white bg-white/10 px-1.5 py-0.5 rounded">--:--:-- CST</b></span>
                        <span>| 日期：<b id="liveDate" class="text-emerald-300 bg-emerald-950/60 border border-emerald-500/40 px-1.5 py-0.5 rounded">----/--/-- (--)</b></span>
                        <span>| 心跳連線：<b id="heartbeatCounter" class="text-[#38bdf8]">12</b></span>
                        <span>| 總裁示：<b id="ssotDecisionBadge" class="text-[#ef4444] font-bold">0.0% 熔斷</b></span>
                    </div>
                </div>
            </div>
            <div class="flex items-center gap-2">
                <span class="badge badge-veto text-xs px-2.5 py-1" id="badgeMobDecision">🔴 熔斷封島管制</span>
            </div>
        </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-3.5 w-full">
        <!-- 左側面板 -->
        <div class="lg:col-span-5 flex flex-col gap-1">
            <!-- 1. 🌀 颱風專區卡片 -->
            <details class="card border-[#ef4444] bg-[#180d1a]/90" open>
                <summary class="card-header !text-red-400 list-none outline-none pb-0 border-b-0 cursor-pointer">
                    <span class="flex items-center gap-1.5 font-black text-xs md:text-sm">🌀 颱風專區：NCDR路徑/行政開設層級與關鍵警戒值</span>
                </summary>
                <div class="pt-2.5 border-t border-red-500/30 mt-2.5 space-y-2">
                    <div class="bg-red-950/50 p-2 rounded-lg border border-red-500/40">
                        <div class="text-[10.5px] font-bold text-amber-300 mb-1 flex justify-between items-center">
                            <span>🏛️ 國家防災體系行政開設狀態：</span>
                            <span class="text-[9px] text-slate-300">NCDR 應變即時連線</span>
                        </div>
                        <div class="grid grid-cols-2 gap-1.5 text-[10px]">
                            <div class="bg-black/40 p-1.5 rounded border border-red-500/30 flex justify-between items-center">
                                <span class="text-slate-200">中央應變中心：</span>
                                <span class="badge badge-veto">🔴 一級開設</span>
                            </div>
                            <div class="bg-black/40 p-1.5 rounded border border-amber-500/30 flex justify-between items-center">
                                <span class="text-slate-200">宜蘭縣應變中心：</span>
                                <span class="badge badge-yellow">🟡 二級開設</span>
                            </div>
                        </div>
                    </div>

                    <div class="bg-black/60 p-2 rounded-lg border border-slate-700">
                        <div class="canvas-container h-[135px] relative flex flex-col justify-between p-2.5 bg-[#091428] border border-slate-800 rounded">
                            <div class="relative z-10 flex justify-between items-start">
                                <div class="text-[10px] text-slate-200">
                                    <span class="font-bold text-amber-300">🌀 強烈颱風 (第21號)</span><br>
                                    中心位置：<span class="font-mono">23.5°N 123.8°E</span> (龜山島東南東 180km)
                                </div>
                                <span class="badge badge-veto text-[9px]">暴風圈侵襲率 88%</span>
                            </div>
                            <div class="relative z-10 my-1 flex items-center justify-around text-center">
                                <div class="text-[9px] text-slate-400">登陸預測<br><b class="text-white font-mono" id="typhoonLandfallTime">10/23 14:00</b></div>
                                <div class="text-xs text-red-400 animate-pulse" id="typhoonStatusTag">➔ ➔ 🌀 ➔ ➔</div>
                            </div>
                        </div>
                    </div>
                </div>
            </details>

            <!-- 2. 🎮 戰術沙盤 -->
            <section class="card border-[#2563eb] bg-[#0c182b]">
                <div class="card-header !text-[#60a5fa]">
                    <span class="font-extrabold flex items-center gap-1.5 text-xs md:text-sm">🎮 戰術沙盤動態調度演練</span>
                </div>
                <div class="grid grid-cols-2 gap-2 pt-1.5 border-t border-[#1e2d4a]">
                    <div class="slider-item">
                        <div class="slider-header"><span>波高 Hs</span><span class="val" id="lblHs">3.71m</span></div>
                        <input type="range" id="rngHs" min="0.4" max="6.0" step="0.05" value="3.71">
                    </div>
                    <div class="slider-item">
                        <div class="slider-header"><span>風速 W</span><span class="val" id="lblW">8.50m/s</span></div>
                        <input type="range" id="rngW" min="2.0" max="22.0" step="0.2" value="8.50">
                    </div>
                    <div class="slider-item">
                        <div class="slider-header"><span>週期 Tp</span><span class="val" id="lblTp">15.5s</span></div>
                        <input type="range" id="rngTp" min="6.0" max="20.0" step="0.5" value="15.5">
                    </div>
                    <div class="slider-item">
                        <div class="slider-header"><span>攻角 Δθ</span><span class="val" id="lblDeltaTheta">50°</span></div>
                        <input type="range" id="rngDeltaTheta" min="0" max="90" step="1" value="50">
                    </div>
                </div>
            </section>

            <!-- 3. 📐 南北岸動態剖面 -->
            <section class="card border-[#38bdf8]">
                <div class="card-header !text-[#38bdf8]">
                    <span>📐 碼頭動態剖面與越浪水頭 (Overtopping) 分析</span>
                    <span class="badge badge-yellow text-[9.5px]">含客輪、UKC與越浪水頭</span>
                </div>

                <div class="bg-[#0b172a] border border-blue-500/50 p-1.5 rounded-xl mb-2 flex items-center justify-between gap-1 shadow-md">
                    <span class="text-[10px] font-bold text-slate-300 pl-1 whitespace-nowrap">⚓ 剖面分頁切換:</span>
                    <div class="grid grid-cols-3 gap-1 flex-1">
                        <button id="tabProfileSouth" class="tab-btn py-1 px-1.5 rounded-lg text-[10px] font-bold border text-center tab-south-active">⚓ 南岸剖面</button>
                        <button id="tabProfileNorth" class="tab-btn py-1 px-1.5 rounded-lg text-[10px] font-bold border border-slate-700 bg-slate-800 text-slate-300 text-center">⚓ 北岸剖面</button>
                        <button id="tabProfileCompare" class="tab-btn py-1 px-1.5 rounded-lg text-[10px] font-bold border border-slate-700 bg-slate-800 text-slate-300 text-center">⚖️ 雙岸對比</button>
                    </div>
                </div>
                
                <div class="canvas-container h-[220px] mb-2" id="profileContainer">
                    <canvas id="profileCanvas" class="w-full h-full block"></canvas>
                </div>

                <table class="data-table">
                    <thead>
                        <tr>
                            <th class="w-[32%]">剖面指標 / 判準</th>
                            <th class="w-[20%] text-center">剛性門檻</th>
                            <th class="w-[24%] text-center text-sky-300">北岸 (主泊位 -8.50m)</th>
                            <th class="w-[24%] text-center text-emerald-300">南岸 (權宜 -9.80m)</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="font-bold text-white">折算波高 <span class="font-mono text-sky-400">Hs,pier</span></td>
                            <td class="text-center font-mono text-slate-400">≤ 1.13 m</td>
                            <td class="text-center font-mono font-bold text-red-400" id="profNorthHs">3.93 m 🔴</td>
                            <td class="text-center font-mono font-bold text-red-400" id="profSouthHs">2.30 m 🔴</td>
                        </tr>
                        <tr>
                            <td class="font-bold text-white">有效風速 <span class="font-mono text-sky-400">Weff</span></td>
                            <td class="text-center font-mono text-slate-400">≤ 10.17 m/s</td>
                            <td class="text-center font-mono font-bold text-emerald-300" id="profNorthWeff">5.46 m/s 🟢</td>
                            <td class="text-center font-mono font-bold text-emerald-300" id="profSouthWeff">6.51 m/s 🟢</td>
                        </tr>
                        <tr>
                            <td class="font-bold text-white">動態裕深 <span class="font-mono text-sky-400">UKC</span></td>
                            <td class="text-center font-mono text-slate-400">≥ 1.50 m</td>
                            <td class="text-center font-mono font-bold text-emerald-300" id="profNorthUKC">5.62 m 🟢</td>
                            <td class="text-center font-mono font-bold text-emerald-300" id="profSouthUKC">7.73 m 🟢</td>
                        </tr>
                        <tr>
                            <td class="font-bold text-white">預留乾舷 <span class="font-mono text-sky-400">FB</span></td>
                            <td class="text-center font-mono text-slate-400">≥ 0.50 m</td>
                            <td class="text-center font-mono font-bold text-red-400" id="profNorthFB">-0.57 m 🔴</td>
                            <td class="text-center font-mono font-bold text-red-400" id="profSouthFB">-0.16 m 🔴</td>
                        </tr>
                        <tr class="bg-red-950/40">
                            <td class="font-bold text-amber-300">越浪水頭 <span class="font-mono text-amber-300">hov / q</span></td>
                            <td class="text-center font-mono text-slate-400">0.0 L/s/m</td>
                            <td class="text-center font-mono font-bold text-red-300" id="profNorthOvertop">+0.57m (18.2 L/s/m)</td>
                            <td class="text-center font-mono font-bold text-red-300" id="profSouthOvertop">+0.16m (4.8 L/s/m)</td>
                        </tr>
                    </tbody>
                </table>
            </section>
        </div>

        <!-- 右側面板 -->
        <div class="lg:col-span-7 flex flex-col gap-1">
            <!-- 4. 📅 動態日期連動預報 -->
            <section class="card border-[#38bdf8]">
                <div class="card-header !text-[#38bdf8]">
                    <span>2. 📅 未來三日官方 vs 模型雙軌檢核方案</span>
                    <span class="badge badge-yellow text-[9px]">動態日期同步</span>
                </div>
                <table class="data-table">
                    <thead>
                        <tr>
                            <th class="w-[22%] bg-slate-900 text-[#38bdf8] text-center">體系 / 方案</th>
                            <th class="w-[26%] text-center bg-blue-950/70 text-emerald-300 font-extrabold" id="thD0Day">D0 (今日)<br><span class="text-[8.5px] font-normal text-slate-300">🌀 長浪</span></th>
                            <th class="w-[26%] text-center bg-indigo-950/70 text-amber-300 font-extrabold" id="thD1Day">D1 (明日)<br><span class="text-[8.5px] font-normal text-slate-300">☁️ 浪退</span></th>
                            <th class="w-[26%] text-center bg-slate-900 text-sky-300 font-extrabold" id="thD2Day">D2 (後日)<br><span class="text-[8.5px] font-normal text-slate-300">☀️ 平穩</span></th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="font-bold text-amber-300 text-[10px] text-center">🏛️ 官方預報</td>
                            <td class="text-[9.5px] font-mono text-center">💨 13.8m 🔴<br>🌊 3.7m 🔴</td>
                            <td class="text-[9.5px] font-mono text-center">💨 9.5m 🟡<br>🌊 2.0m 🟡</td>
                            <td class="text-[9.5px] font-mono text-center">💨 4.8m 🟢<br>🌊 0.9m 🟢</td>
                        </tr>
                        <tr>
                            <td class="font-bold text-[#38bdf8] text-[10px] text-center">🤖 GEM 裁決</td>
                            <td class="text-center"><span class="badge badge-veto text-[9px]">🔴 0% 熔斷</span></td>
                            <td class="text-center"><span class="badge badge-yellow text-[9px]">🟡 條件靠泊</span></td>
                            <td class="text-center"><span class="badge badge-pass text-[9px]">🟢 100% 放行</span></td>
                        </tr>
                    </tbody>
                </table>
            </section>

            <!-- 5. 🎯 態勢雷達圖與動態算子連動 -->
            <section class="card border-[#38bdf8]">
                <div class="card-header !text-[#38bdf8]">
                    <span class="flex items-center gap-1">4. 🎯 態勢雷達圖與剛性五大算子即時動態對比</span>
                    <span class="badge badge-yellow text-[9.5px]">頂點數據即時繪製</span>
                </div>

                <div class="flex gap-1 overflow-x-auto pb-1 mb-2" id="toolbarTimeButtons">
                    <button class="flex-1 min-w-[50px] bg-red-950/60 border border-red-500 text-red-300 py-1 rounded text-[10px] font-extrabold" id="btnT1000">10:00 滿潮</button>
                    <button class="flex-1 min-w-[62px] bg-yellow-500/25 border border-[#facc15] text-[#facc15] py-1 rounded text-[10px] font-extrabold" id="btnT1120">11:20 止登</button>
                    <button class="flex-1 min-w-[62px] bg-yellow-500/25 border border-[#facc15] text-[#facc15] py-1 rounded text-[10px] font-extrabold" id="btnT1420">14:20 撤離</button>
                </div>

                <div class="bg-[#0b172a] border border-blue-500/50 p-1.5 rounded-xl mb-2 flex items-center justify-between gap-1 shadow-md">
                    <span class="text-[10px] font-bold text-slate-300 pl-1 whitespace-nowrap">📡 雷達分頁切換:</span>
                    <div class="grid grid-cols-3 gap-1 flex-1">
                        <button id="tabRadarSouth" class="tab-btn py-1 px-1.5 rounded-lg text-[10px] font-bold border text-center tab-south-active">⚓ 南岸碼頭</button>
                        <button id="tabRadarNorth" class="tab-btn py-1 px-1.5 rounded-lg text-[10px] font-bold border border-slate-700 bg-slate-800 text-slate-300 text-center">⚓ 北岸碼頭</button>
                        <button id="tabRadarCompare" class="tab-btn py-1 px-1.5 rounded-lg text-[10px] font-bold border border-slate-700 bg-slate-800 text-slate-300 text-center">⚖️ 雙岸疊合</button>
                    </div>
                </div>

                <div class="canvas-container h-[310px] mb-2" id="radarContainer">
                    <canvas id="nativeRadarCanvas" class="w-full h-full block"></canvas>
                </div>

                <table class="data-table mb-2">
                    <thead>
                        <tr>
                            <th class="w-[28%]">剛性物理算子</th>
                            <th class="w-[22%] text-center">剛性警戒門檻</th>
                            <th class="w-[25%] text-center text-sky-300">北岸即時值 / 燈號</th>
                            <th class="w-[25%] text-center text-emerald-300">南岸即時值 / 燈號</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td class="font-bold text-white">波高 <span class="font-mono text-[#38bdf8]">(Hs,pier)</span></td>
                            <td class="text-center font-mono text-slate-300">≤ 1.13 m</td>
                            <td class="text-center font-mono font-bold text-red-400" id="radarNorthHs">3.93m 🔴超標</td>
                            <td class="text-center font-mono font-bold text-red-400" id="radarSouthHs">2.30m 🔴超標</td>
                        </tr>
                        <tr>
                            <td class="font-bold text-white">攻角風速 <span class="font-mono text-[#38bdf8]">(Weff)</span></td>
                            <td class="text-center font-mono text-slate-300">≤ 10.17 m/s</td>
                            <td class="text-center font-mono font-bold text-emerald-300" id="radarNorthWeff">5.46m/s 🟢合格</td>
                            <td class="text-center font-mono font-bold text-emerald-300" id="radarSouthWeff">6.51m/s 🟢合格</td>
                        </tr>
                        <tr>
                            <td class="font-bold text-white">週期 <span class="font-mono text-[#38bdf8]">(Tp)</span></td>
                            <td class="text-center font-mono text-slate-300">≤ 11.5 s</td>
                            <td class="text-center font-mono font-bold text-red-400" id="radarNorthTp">15.5s 🔴長浪</td>
                            <td class="text-center font-mono font-bold text-red-400" id="radarSouthTp">15.5s 🔴長浪</td>
                        </tr>
                        <tr>
                            <td class="font-bold text-white">動態裕深 <span class="font-mono text-[#38bdf8]">(UKC)</span></td>
                            <td class="text-center font-mono text-slate-300">≥ 1.50 m</td>
                            <td class="text-center font-mono font-bold text-emerald-300" id="radarNorthUKC">5.62m 🟢合格</td>
                            <td class="text-center font-mono font-bold text-emerald-300" id="radarSouthUKC">7.73m 🟢合格</td>
                        </tr>
                        <tr>
                            <td class="font-bold text-white">碼頭乾舷 <span class="font-mono text-[#38bdf8]">(FB)</span></td>
                            <td class="text-center font-mono text-slate-300">≥ 0.50 m</td>
                            <td class="text-center font-mono font-bold text-red-400" id="radarNorthFB">-0.57m 🔴漫頂</td>
                            <td class="text-center font-mono font-bold text-red-400" id="radarSouthFB">-0.16m 🔴漫頂</td>
                        </tr>
                    </tbody>
                </table>

                <div class="box-alert-danger text-center" id="boxRadarFinalVerdict">
                    <b>🎯 最終安全態勢與游擊調度裁決：</b><br>
                    <span class="text-white font-extrabold text-[11.5px] mt-0.5 inline-block" id="txtRadarFinalVerdict">🔴 0.0% 物理 VETO 熔斷 / 【強颱極端暴風全線封島】</span>
                </div>
            </section>
        </div>
    </div>

    <script>
    (function() {
        const getEl = id => document.getElementById(id);
        const setTxt = (id, txt) => { const el = getEl(id); if (el) el.textContent = txt; };

        let currentProfileMode = 'SOUTH';
        let currentRadarMode = 'SOUTH';
        let animPhase = 0;

        function initDashboard() {
            startClockAndWatchdog();
            initUIControls();
            applyStateIsolation();
            recalculatePhysicsAndRender();
            window.addEventListener('resize', renderAllCanvas);

            function animLoop() {
                animPhase += 0.06;
                drawProfileCanvas();
                requestAnimationFrame(animLoop);
            }
            requestAnimationFrame(animLoop);
        }

        // 動態即時日期與時鐘更新
        function startClockAndWatchdog() {
            let heartbeat = 12;
            const update = () => {
                const now = new Date();
                
                // 1. 動態時間 (CST)
                setTxt('liveClock', `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')} CST`);

                // 2. 動態日期 (YYYY-MM-DD + 星期)
                const days = ['日', '一', '二', '三', '四', '五', '六'];
                const year = now.getFullYear();
                const month = String(now.getMonth() + 1).padStart(2, '0');
                const date = String(now.getDate()).padStart(2, '0');
                const dayName = days[now.getDay()];
                setTxt('liveDate', `${year}-${month}-${date} (${dayName})`);

                // 3. 預報標頭日期同步 (D0 今日 / D1 明日 / D2 後日)
                const d0 = new Date(now);
                const d1 = new Date(now); d1.setDate(d1.getDate() + 1);
                const d2 = new Date(now); d2.setDate(d2.getDate() + 2);
                const fmtM = d => `${d.getMonth()+1}/${d.getDate()}`;
                
                const thD0 = getEl('thD0Day'); if (thD0) thD0.innerHTML = `今日 ${fmtM(d0)}<br><span class="text-[8.5px] font-normal text-slate-300">🌀 長浪</span>`;
                const thD1 = getEl('thD1Day'); if (thD1) thD1.innerHTML = `明日 ${fmtM(d1)}<br><span class="text-[8.5px] font-normal text-slate-300">☁️ 浪退</span>`;
                const thD2 = getEl('thD2Day'); if (thD2) thD2.innerHTML = `後日 ${fmtM(d2)}<br><span class="text-[8.5px] font-normal text-slate-300">☀️ 平穩</span>`;

                // 4. 看門狗檢核
                const landfallEl = getEl('typhoonLandfallTime');
                const statusTagEl = getEl('typhoonStatusTag');
                const targetLandfallTime = new Date('2026/10/23 14:00:00').getTime();
                if (now.getTime() > targetLandfallTime && landfallEl) {
                    landfallEl.innerHTML = `<span style="color:#f59e0b; font-weight:bold;">已通過/登陸 (10/23 14:00)</span>`;
                    if (statusTagEl) statusTagEl.innerText = "中心掠過，暴風圈持續籠罩";
                }

                if (now.getSeconds() % 5 === 0) {
                    heartbeat++;
                    setTxt('heartbeatCounter', heartbeat);
                }
            };
            update();
            setInterval(update, 1000);
        }

        function initUIControls() {
            const bindInput = (id, labelId, suffix) => {
                const el = getEl(id);
                if (el) {
                    el.addEventListener('input', e => {
                        setTxt(labelId, `${e.target.value}${suffix}`);
                        recalculatePhysicsAndRender();
                    });
                }
            };
            bindInput('rngHs', 'lblHs', 'm');
            bindInput('rngW', 'lblW', 'm/s');
            bindInput('rngTp', 'lblTp', 's');
            bindInput('rngDeltaTheta', 'lblDeltaTheta', '°');

            const bindProfTab = (id, mode) => {
                const btn = getEl(id);
                if (btn) {
                    btn.addEventListener('click', () => {
                        currentProfileMode = mode;
                        updateTabUI('PROFILE', mode);
                        renderAllCanvas();
                    });
                }
            };
            bindProfTab('tabProfileSouth', 'SOUTH');
            bindProfTab('tabProfileNorth', 'NORTH');
            bindProfTab('tabProfileCompare', 'COMPARE');

            const bindRadarTab = (id, mode) => {
                const btn = getEl(id);
                if (btn) {
                    btn.addEventListener('click', () => {
                        currentRadarMode = mode;
                        updateTabUI('RADAR', mode);
                        renderAllCanvas();
                    });
                }
            };
            bindRadarTab('tabRadarSouth', 'SOUTH');
            bindRadarTab('tabRadarNorth', 'NORTH');
            bindRadarTab('tabRadarCompare', 'COMPARE');
        }

        function updateTabUI(type, activeMode) {
            const prefix = type === 'PROFILE' ? 'tabProfile' : 'tabRadar';
            const baseClass = "tab-btn py-1 px-1.5 rounded-lg text-[10px] font-bold border text-center transition-all ";
            const inactiveClass = baseClass + "border-slate-700 bg-slate-800 text-slate-300";

            const southBtn = getEl(prefix + 'South');
            const northBtn = getEl(prefix + 'North');
            const compareBtn = getEl(prefix + 'Compare');

            if (southBtn) southBtn.className = activeMode === 'SOUTH' ? baseClass + 'tab-south-active' : inactiveClass;
            if (northBtn) northBtn.className = activeMode === 'NORTH' ? baseClass + 'tab-north-active' : inactiveClass;
            if (compareBtn) compareBtn.className = activeMode === 'COMPARE' ? baseClass + 'tab-compare-active' : inactiveClass;
        }

        function recalculatePhysicsAndRender() {
            const hs = parseFloat(getEl('rngHs')?.value || 3.71);
            const w = parseFloat(getEl('rngW')?.value || 8.50);
            const tp = parseFloat(getEl('rngTp')?.value || 15.5);
            const deltaTheta = parseFloat(getEl('rngDeltaTheta')?.value || 50);

            const radNorth = deltaTheta * (Math.PI / 180);
            const radSouth = (90 - deltaTheta) * (Math.PI / 180);

            const hsNorth = hs * 1.06;
            const hsSouth = hs * 0.62;
            const weffNorth = w * Math.abs(Math.cos(radNorth));
            const weffSouth = w * Math.abs(Math.sin(radSouth));

            const tide = 1.10;
            const draft = 2.02;

            const ukcNorth = 8.50 + tide - draft - hsNorth * 0.5;
            const ukcSouth = 9.80 + tide - draft - hsSouth * 0.5;

            const deckNorth = 3.20;
            const deckSouth = 2.50;
            const crestNorth = tide + hsNorth * 0.68;
            const crestSouth = tide + hsSouth * 0.68;

            const fbNorth = deckNorth - crestNorth;
            const fbSouth = deckSouth - crestSouth;

            const overtopNorth = Math.max(0, crestNorth - deckNorth);
            const overtopSouth = Math.max(0, crestSouth - deckSouth);

            const qNorth = (overtopNorth * 32).toFixed(1);
            const qSouth = (overtopSouth * 30).toFixed(1);

            setTxt('profNorthHs', `${hsNorth.toFixed(2)}m 🔴`);
            setTxt('profSouthHs', `${hsSouth.toFixed(2)}m 🔴`);
            setTxt('profNorthWeff', `${weffNorth.toFixed(2)}m/s ${weffNorth<=10.17?'🟢':'🔴'}`);
            setTxt('profSouthWeff', `${weffSouth.toFixed(2)}m/s ${weffSouth<=10.17?'🟢':'🔴'}`);
            setTxt('profNorthUKC', `${ukcNorth.toFixed(2)}m ${ukcNorth>=1.5?'🟢':'🔴'}`);
            setTxt('profSouthUKC', `${ukcSouth.toFixed(2)}m ${ukcSouth>=1.5?'🟢':'🔴'}`);
            setTxt('profNorthFB', `${fbNorth.toFixed(2)}m ${fbNorth>=0.5?'🟢':'🔴'}`);
            setTxt('profSouthFB', `${fbSouth.toFixed(2)}m ${fbSouth>=0.5?'🟢':'🔴'}`);
            setTxt('profNorthOvertop', overtopNorth > 0 ? `+${overtopNorth.toFixed(2)}m (${qNorth} L/s/m)` : '0.0m (無越浪)');
            setTxt('profSouthOvertop', overtopSouth > 0 ? `+${overtopSouth.toFixed(2)}m (${qSouth} L/s/m)` : '0.0m (無越浪)');

            setTxt('radarNorthHs', `${hsNorth.toFixed(2)}m 🔴超標${Math.round((hsNorth/1.13-1)*100)}%`);
            setTxt('radarSouthHs', `${hsSouth.toFixed(2)}m 🔴超標${Math.round((hsSouth/1.13-1)*100)}%`);
            setTxt('radarNorthWeff', `${weffNorth.toFixed(2)}m/s ${weffNorth<=10.17?'🟢合格':'🔴超標'}`);
            setTxt('radarSouthWeff', `${weffSouth.toFixed(2)}m/s ${weffSouth<=10.17?'🟢合格':'🔴超標'}`);
            setTxt('radarNorthTp', `${tp.toFixed(1)}s ${tp>=11.5?'🔴長浪':'🟢合格'}`);
            setTxt('radarSouthTp', `${tp.toFixed(1)}s ${tp>=11.5?'🔴長浪':'🟢合格'}`);
            setTxt('radarNorthUKC', `${ukcNorth.toFixed(2)}m ${ukcNorth>=1.5?'🟢合格':'🔴不足'}`);
            setTxt('radarSouthUKC', `${ukcSouth.toFixed(2)}m ${ukcSouth>=1.5?'🟢合格':'🔴不足'}`);
            setTxt('radarNorthFB', `${fbNorth.toFixed(2)}m ${fbNorth>=0.5?'🟢合格':'🔴漫頂'}`);
            setTxt('radarSouthFB', `${fbSouth.toFixed(2)}m ${fbSouth>=0.5?'🟢合格':'🔴漫頂'}`);

            renderAllCanvas();
        }

        function applyStateIsolation() {
            const toolbar = getEl('toolbarTimeButtons');
            if (toolbar) toolbar.style.display = "none";

            const verdictEl = getEl('txtRadarFinalVerdict');
            if (verdictEl) {
                verdictEl.innerText = "🔴 0.0% 物理 VETO 熔斷 / 【強颱極端暴風全線封島】禁絕一切船舶靠泊";
                verdictEl.className = "text-[#fca5a5] font-extrabold text-[11.5px] mt-0.5 inline-block";
            }
        }

        function renderAllCanvas() {
            drawProfileCanvas();
            drawRadarCanvas();
        }

        function drawProfileCanvas() {
            const canvas = getEl('profileCanvas');
            const container = getEl('profileContainer');
            if (!canvas || !container) return;

            const hs = parseFloat(getEl('rngHs')?.value || 3.71);
            const wVal = parseFloat(getEl('rngW')?.value || 8.50);
            const tp = parseFloat(getEl('rngTp')?.value || 15.5);
            const deltaTheta = parseFloat(getEl('rngDeltaTheta')?.value || 50);

            const isCompare = currentProfileMode === 'COMPARE';
            const w = container.clientWidth || 340;
            const h = isCompare ? 260 : 210;
            const dpr = window.devicePixelRatio || 1;

            canvas.width = w * dpr;
            canvas.height = h * dpr;
            canvas.style.width = w + 'px';
            canvas.style.height = h + 'px';

            const ctx = canvas.getContext('2d');
            ctx.scale(dpr, dpr);

            ctx.fillStyle = '#050a14';
            ctx.fillRect(0, 0, w, h);

            if (isCompare) {
                const subH = (h - 6) / 2;
                drawSingleProfile(ctx, 0, 0, w, subH, '北岸碼頭 (主泊位 -8.50m CD)', 8.50, 3.20, hs * 1.06, wVal * Math.abs(Math.cos(deltaTheta * Math.PI/180)), tp, '#38bdf8', true);
                drawSingleProfile(ctx, 0, subH + 6, w, subH, '南岸碼頭 (權宜泊位 -9.80m CD)', 9.80, 2.50, hs * 0.62, wVal * Math.abs(Math.sin((90-deltaTheta) * Math.PI/180)), tp, '#34d399', false);
            } else if (currentProfileMode === 'NORTH') {
                drawSingleProfile(ctx, 0, 0, w, h, '北岸碼頭 (主泊位 -8.50m CD)', 8.50, 3.20, hs * 1.06, wVal * Math.abs(Math.cos(deltaTheta * Math.PI/180)), tp, '#38bdf8', true);
            } else {
                drawSingleProfile(ctx, 0, 0, w, h, '南岸碼頭 (權宜泊位 -9.80m CD)', 9.80, 2.50, hs * 0.62, wVal * Math.abs(Math.sin((90-deltaTheta) * Math.PI/180)), tp, '#34d399', false);
            }
        }

        function drawSingleProfile(ctx, offsetX, offsetY, w, h, title, depthBase, deckCD, hsPier, weff, tp, accentColor, isNorth) {
            ctx.save();
            ctx.translate(offsetX, offsetY);

            const topCD = 5.0;
            const bottomCD = -12.0;
            const cdToY = cd => ((topCD - cd) / (topCD - bottomCD)) * (h - 26) + 16;

            const tideCD = 1.10;
            const draft = 2.02;
            const keelCD = tideCD - draft;
            const ukc = depthBase + keelCD - hsPier * 0.5;

            const crestCD = tideCD + hsPier * 0.68;
            const overtopDepth = Math.max(0, crestCD - deckCD);
            const fb = deckCD - crestCD;
            const qRate = (overtopDepth * 32).toFixed(1);

            const tideY = cdToY(tideCD);
            const deckY = cdToY(deckCD);
            const seabedY = cdToY(-depthBase);
            const keelY = cdToY(keelCD);
            const crestY = cdToY(crestCD);

            const quayX = w * 0.52;

            // 1. 海底面
            ctx.fillStyle = '#1a1816';
            ctx.fillRect(0, seabedY, w, Math.max(10, h - seabedY));
            ctx.strokeStyle = '#475569';
            ctx.lineWidth = 1.2;
            ctx.beginPath();
            ctx.moveTo(0, seabedY);
            ctx.lineTo(w, seabedY);
            ctx.stroke();

            ctx.font = '8.5px monospace';
            ctx.fillStyle = '#cbd5e1';
            ctx.fillText(`海底面 CD -${depthBase.toFixed(2)}m`, 8, seabedY + 11);

            // 2. 碼頭結構
            ctx.fillStyle = '#1e2d4a';
            ctx.fillRect(quayX, deckY, w - quayX, seabedY - deckY);
            ctx.strokeStyle = accentColor;
            ctx.lineWidth = 1.5;
            ctx.strokeRect(quayX, deckY, w - quayX, seabedY - deckY);

            ctx.fillStyle = '#facc15';
            ctx.fillRect(quayX + 4, deckY - 4, 5, 4);

            ctx.font = '8.5px monospace';
            ctx.fillStyle = '#e2e8f0';
            ctx.fillText(`碼頭面 +${deckCD.toFixed(2)}m CD`, quayX + 12, deckY + 12);

            // 3. 水體與波浪
            const isOvertopping = overtopDepth > 0 || fb < 0.50;
            ctx.beginPath();
            ctx.moveTo(0, seabedY);
            ctx.lineTo(0, tideY);

            const waveAmp = Math.min(22, hsPier * 3.8);
            const waveFreq = 0.05;
            for (let x = 0; x <= quayX; x += 4) {
                const wy = tideY + Math.sin(x * waveFreq + animPhase) * waveAmp;
                ctx.lineTo(x, wy);
            }

            if (isOvertopping) {
                ctx.lineTo(quayX, crestY);
                ctx.lineTo(w, crestY + 1);
                ctx.lineTo(w, seabedY);
            } else {
                ctx.lineTo(quayX, tideY);
                ctx.lineTo(quayX, seabedY);
            }
            ctx.closePath();
            ctx.fillStyle = isOvertopping ? 'rgba(239, 68, 68, 0.38)' : 'rgba(56, 189, 248, 0.35)';
            ctx.fill();

            // 4. 越浪水頭高度標註
            if (isOvertopping) {
                ctx.save();
                ctx.setLineDash([4, 3]);
                ctx.strokeStyle = '#ef4444';
                ctx.lineWidth = 1.8;
                ctx.beginPath();
                ctx.moveTo(quayX - 20, crestY);
                ctx.lineTo(w, crestY);
                ctx.stroke();
                ctx.restore();

                ctx.strokeStyle = '#facc15';
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(quayX + 80, deckY);
                ctx.lineTo(quayX + 80, crestY);
                ctx.stroke();

                ctx.fillStyle = '#ef4444';
                ctx.fillRect(quayX + 2, deckY - 17, Math.max(140, w - quayX - 4), 15);
                ctx.fillStyle = '#ffffff';
                ctx.font = 'bold 8.5px sans-serif';
                ctx.fillText(`🚨 越浪水頭 h_ov: +${overtopDepth.toFixed(2)}m (q=${qRate} L/s/m)`, quayX + 5, deckY - 6);
            }

            // 5. 客輪實體繪製
            const shipW = Math.min(62, quayX * 0.58);
            const shipX = quayX - shipW - 8;
            const shipDeckY = tideY - 11;

            ctx.beginPath();
            ctx.moveTo(shipX, shipDeckY);
            ctx.lineTo(shipX + shipW, shipDeckY);
            ctx.lineTo(shipX + shipW, keelY - 3);
            ctx.lineTo(shipX + shipW - 5, keelY);
            ctx.lineTo(shipX + 5, keelY);
            ctx.lineTo(shipX, keelY - 6);
            ctx.closePath();
            ctx.fillStyle = '#1e293b';
            ctx.fill();
            ctx.strokeStyle = '#f8fafc';
            ctx.lineWidth = 1.2;
            ctx.stroke();

            ctx.fillStyle = '#38bdf8';
            ctx.fillRect(shipX + 8, shipDeckY - 7, shipW * 0.45, 7);
            ctx.fillStyle = '#e2e8f0';
            ctx.fillText('🚢 客輪', shipX + 10, shipDeckY - 1);

            // 6. UKC 尺寸指示線
            const ukcX = shipX + shipW * 0.5;
            ctx.beginPath();
            ctx.moveTo(ukcX, keelY);
            ctx.lineTo(ukcX, seabedY);
            ctx.strokeStyle = ukc < 1.50 ? '#ef4444' : '#10b981';
            ctx.lineWidth = 2.0;
            ctx.stroke();

            ctx.fillStyle = ukc < 1.50 ? '#ef4444' : '#10b981';
            ctx.fillRect(ukcX - 3, keelY, 6, 2);
            ctx.fillRect(ukcX - 3, seabedY - 2, 6, 2);

            ctx.font = 'bold 8.5px monospace';
            ctx.fillStyle = ukc < 1.50 ? '#fca5a5' : '#86efac';
            ctx.fillText(`UKC: ${ukc.toFixed(2)}m ${ukc>=1.5?'🟢':'🔴觸底'}`, ukcX + 4, (keelY + seabedY) / 2 + 3);

            // 7. HUD 參數標籤
            ctx.font = 'bold 9.5px sans-serif';
            ctx.fillStyle = accentColor;
            ctx.fillText(`⚓ ${title}`, 8, 12);

            ctx.font = '8.5px monospace';
            ctx.fillStyle = '#cbd5e1';
            ctx.fillText(`潮位 η: +${tideCD.toFixed(2)}m CD | 波高 Hs: ${hsPier.toFixed(2)}m | 風速 Weff: ${weff.toFixed(1)}m/s | FB: ${fb.toFixed(2)}m`, 8, 23);

            ctx.restore();
        }

        // 雷達圖 5 大頂點數值動態渲染 (Dynamic Vertices Labels)
        function drawRadarCanvas() {
            const canvas = getEl('nativeRadarCanvas');
            const container = getEl('radarContainer');
            if (!canvas || !container) return;

            const hs = parseFloat(getEl('rngHs')?.value || 3.71);
            const wVal = parseFloat(getEl('rngW')?.value || 8.50);
            const tpVal = parseFloat(getEl('rngTp')?.value || 15.5);
            const deltaTheta = parseFloat(getEl('rngDeltaTheta')?.value || 50);

            const radNorth = deltaTheta * (Math.PI / 180);
            const radSouth = (90 - deltaTheta) * (Math.PI / 180);

            const hsNorth = hs * 1.06;
            const hsSouth = hs * 0.62;
            const weffNorth = wVal * Math.abs(Math.cos(radNorth));
            const weffSouth = wVal * Math.abs(Math.sin(radSouth));

            const tide = 1.10;
            const draft = 2.02;
            const ukcNorth = 8.50 + tide - draft - hsNorth * 0.5;
            const ukcSouth = 9.80 + tide - draft - hsSouth * 0.5;

            const crestNorth = tide + hsNorth * 0.68;
            const crestSouth = tide + hsSouth * 0.68;
            const fbNorth = 3.20 - crestNorth;
            const fbSouth = 2.50 - crestSouth;

            const w = container.clientWidth || 340;
            const h = 310;
            const dpr = window.devicePixelRatio || 1;

            canvas.width = w * dpr;
            canvas.height = h * dpr;
            canvas.style.width = w + 'px';
            canvas.style.height = h + 'px';

            const ctx = canvas.getContext('2d');
            ctx.scale(dpr, dpr);

            ctx.fillStyle = '#050a14';
            ctx.fillRect(0, 0, w, h);

            const cx = w / 2;
            const cy = h * 0.45;
            const R = Math.min(w * 0.20, 60);
            const count = 5;
            const angles = [];
            for (let i = 0; i < count; i++) angles.push(-Math.PI / 2 + (i * 2 * Math.PI) / count);

            // 雷達軸向網格 (1.0 為剛性警戒線)
            [0.5, 1.0, 1.4].forEach(lvl => {
                ctx.beginPath();
                for (let i = 0; i < count; i++) {
                    const r = R * lvl;
                    const x = cx + r * Math.cos(angles[i]);
                    const y = cy + r * Math.sin(angles[i]);
                    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                }
                ctx.closePath();
                ctx.strokeStyle = lvl === 1.0 ? '#facc15' : '#1e2d4a';
                ctx.lineWidth = lvl === 1.0 ? 1.5 : 0.8;
                if (lvl === 1.0) ctx.setLineDash([4, 4]); else ctx.setLineDash([]);
                ctx.stroke();
            });

            // 算子縮放比率算式
            const getRatios = isNorth => {
                const curHs = isNorth ? hsNorth : hsSouth;
                const curWeff = isNorth ? weffNorth : weffSouth;
                const curUkc = isNorth ? ukcNorth : ukcSouth;
                const curFb = isNorth ? fbNorth : fbSouth;

                const rHs = curHs / 1.13;
                const rWeff = curWeff / 10.17;
                const rTp = tpVal / 11.5;
                const rUkc = curUkc < 1.50 ? (1.0 + (1.50 - curUkc) / 1.50) : (curUkc / 1.50 * 0.5);
                const rFb = curFb < 0.50 ? (1.0 + (0.50 - curFb) / 0.50) : (curFb / 0.50 * 0.5);

                return [rHs, rWeff, rTp, rUkc, rFb];
            };

            if (currentRadarMode === 'COMPARE') {
                drawRadarPoly(ctx, cx, cy, R, angles, getRatios(true), 'rgba(56, 189, 248, 0.3)', '#38bdf8');
                drawRadarPoly(ctx, cx, cy, R, angles, getRatios(false), 'rgba(16, 185, 129, 0.3)', '#34d399');
            } else if (currentRadarMode === 'NORTH') {
                drawRadarPoly(ctx, cx, cy, R, angles, getRatios(true), 'rgba(239, 68, 68, 0.35)', '#ef4444');
            } else {
                drawRadarPoly(ctx, cx, cy, R, angles, getRatios(false), 'rgba(239, 68, 68, 0.35)', '#ef4444');
            }

            // 動態生成 5 大頂點即時數據與燈號文字
            const isN = currentRadarMode === 'NORTH';
            const isS = currentRadarMode === 'SOUTH';

            const hsDisp = isN ? `${hsNorth.toFixed(2)}m` : (isS ? `${hsSouth.toFixed(2)}m` : `${hsSouth.toFixed(2)}~${hsNorth.toFixed(2)}m`);
            const weffDisp = isN ? `${weffNorth.toFixed(1)}m/s` : (isS ? `${weffSouth.toFixed(1)}m/s` : `${weffNorth.toFixed(1)}~${weffSouth.toFixed(1)}m/s`);
            const ukcDisp = isN ? `${ukcNorth.toFixed(2)}m` : (isS ? `${ukcSouth.toFixed(2)}m` : `${ukcNorth.toFixed(2)}~${ukcSouth.toFixed(2)}m`);
            const fbDisp = isN ? `${fbNorth.toFixed(2)}m` : (isS ? `${fbSouth.toFixed(2)}m` : `${fbNorth.toFixed(2)}~${fbSouth.toFixed(2)}m`);

            const hsFail = isN ? hsNorth > 1.13 : (isS ? hsSouth > 1.13 : (hsNorth > 1.13 || hsSouth > 1.13));
            const weffFail = isN ? weffNorth > 10.17 : (isS ? weffSouth > 10.17 : (weffNorth > 10.17 || weffSouth > 10.17));
            const tpFail = tpVal >= 11.5;
            const ukcFail = isN ? ukcNorth < 1.50 : (isS ? ukcSouth < 1.50 : (ukcNorth < 1.50 || ukcSouth < 1.50));
            const fbFail = isN ? fbNorth < 0.50 : (isS ? fbSouth < 0.50 : (fbNorth < 0.50 || fbSouth < 0.50));

            const dynamicLabels = [
                { title: "波高 Hs", val: hsDisp, limit: "≤1.13m", fail: hsFail },
                { title: "攻角風速 Weff", val: weffDisp, limit: "≤10.17m/s", fail: weffFail },
                { title: "週期 Tp", val: `${tpVal.toFixed(1)}s`, limit: "≤11.5s", fail: tpFail },
                { title: "裕深 UKC", val: ukcDisp, limit: "≥1.50m", fail: ukcFail },
                { title: "乾舷 FB", val: fbDisp, limit: "≥0.50m", fail: fbFail }
            ];

            ctx.font = 'bold 9.5px sans-serif';
            for (let i = 0; i < count; i++) {
                const r = R * 1.62;
                const x = cx + r * Math.cos(angles[i]);
                const y = cy + r * Math.sin(angles[i]);
                const item = dynamicLabels[i];

                ctx.fillStyle = item.fail ? '#fca5a5' : '#86efac';
                ctx.textAlign = x < cx - 10 ? 'right' : (x > cx + 10 ? 'left' : 'center');
                ctx.fillText(`${item.title}: ${item.val}`, x, y);
                ctx.fillStyle = '#cbd5e1';
                ctx.fillText(`(門檻 ${item.limit}) ${item.fail ? '🔴' : '🟢'}`, x, y + 11);
            }

            const activeText = currentRadarMode === 'NORTH' ? '【北岸主泊位態勢】' :
                               currentRadarMode === 'SOUTH' ? '【南岸權宜泊位態勢】' : '【雙岸疊合比較態勢】';

            ctx.font = 'bold 12px sans-serif';
            ctx.fillStyle = '#ef4444';
            ctx.textAlign = 'center';
            ctx.fillText(`🔴 實體破防熔斷 (VETO) ${activeText}`, cx, cy + R + 48);
        }

        function drawRadarPoly(ctx, cx, cy, R, angles, ratios, fillColor, strokeColor) {
            ctx.beginPath();
            for (let i = 0; i < angles.length; i++) {
                const val = Math.max(0.2, Math.min(1.5, ratios[i]));
                const r = R * val;
                const x = cx + r * Math.cos(angles[i]);
                const y = cy + r * Math.sin(angles[i]);
                if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.fillStyle = fillColor;
            ctx.fill();
            ctx.strokeStyle = strokeColor;
            ctx.lineWidth = 2;
            ctx.setLineDash([]);
            ctx.stroke();

            // 繪製多邊形頂點端點圓球
            for (let i = 0; i < angles.length; i++) {
                const val = Math.max(0.2, Math.min(1.5, ratios[i]));
                const r = R * val;
                const x = cx + r * Math.cos(angles[i]);
                const y = cy + r * Math.sin(angles[i]);
                ctx.beginPath();
                ctx.arc(x, y, 3, 0, Math.PI * 2);
                ctx.fillStyle = strokeColor;
                ctx.fill();
            }
        }

        if (document.readyState === 'complete' || document.readyState === 'interactive') {
            initDashboard();
        } else {
            document.addEventListener('DOMContentLoaded', initDashboard);
        }
    })();
    </script>
</body>
</html>
"""


# ==============================================================================
# 4. 腳本進入點 (Entry Point)
# ==============================================================================
def main():
    orchestrator = GEMMasterOrchestrator()
    
    # 執行內部數據編排與檔案匯出
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(orchestrator.execute_cycle())
        else:
            loop.run_until_complete(orchestrator.execute_cycle())
    except Exception as e:
        asyncio.run(orchestrator.execute_cycle())

    # 若於 Jupyter / Colab 環境執行，同步渲染 HTML
    if HAS_IPYTHON:
        display(HTML(HTML_CONTENT))
    else:
        logging.info("🎉 執行完成！您可以開啟 index.html 檢視視覺化面板。")


if __name__ == "__main__":
    main()

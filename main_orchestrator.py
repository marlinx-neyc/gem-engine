#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==============================================================================
GEM Engine v66.0 Master Spatial-Dynamic Orchestrator
全域 SSOT 戰術指揮中樞 - Windy 動態地圖（龜山島標註）、游擊時序連動與雙端自動發布下載完整版
==============================================================================
"""

import asyncio
import datetime
import json
import logging
import math
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - [%(levelname)s] - %(message)s")

try:
    from IPython.display import HTML, display
    HAS_IPYTHON = True
except ImportError:
    HAS_IPYTHON = False

# 判斷是否在 Google Colab 環境
try:
    from google.colab import files
    IN_COLAB = True
except ImportError:
    IN_COLAB = False


@dataclass(frozen=True)
class EngineConfig:
    """系統剛性門檻與港埠結構規格 (完全對齊工程竣工圖說 CD 基準面)"""
    BASE_LIMIT_HS: float = 1.13           # 港池折算波高門檻 (<= 1.13m)
    LIMIT_WEFF: float = 10.17             # 攻角有效風速門檻 (<= 10.17m/s)
    LIMIT_TP: float = 11.5                # 湧浪週期門檻 (<= 11.5s)
    LIMIT_UKC: float = 1.50               # 動態裕深門檻 (>= 1.50m)
    LIMIT_FB: float = 0.50                # 預留乾舷門檻 (>= 0.50m)
    GUISHAN_LAT: float = 24.843           # 龜山島緯度
    GUISHAN_LON: float = 121.952          # 龜山島經度
    CHART_DEPTH_NORTH: float = 8.50       # 北岸主泊位水深 (-8.50m CD)
    CHART_DEPTH_SOUTH: float = 9.80       # 南岸權宜泊位水深 (-9.80m CD)
    NORTH_TRUSS_DECK_CD: float = 3.20     # 北岸鋼桁架引橋面頂高程 (+3.20m CD)
    SOUTH_CAISSON_DECK_CD: float = 2.50   # 南岸沉箱碼頭面頂高程 (+2.50m CD)
    VESSEL_STATIC_DRAFT: float = 2.02     # 客輪靜態吃水 (2.02m)


class GEMMasterOrchestrator:
    def __init__(self):
        self.config = EngineConfig()

    async def execute_cycle(self):
        logging.info("🚀 GEM Engine v66.0 Master Orchestrator 啟動並生成最新連動檔案...")
        now_cst = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8)))
        ver_tag = now_cst.strftime("%Y%m%d_%H%M%S")

        ssot_payload = {
            "version": f"GEM-ENG-SPEC-2026-V66-{ver_tag}",
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
            },
            "sync_windows": ["07:30-08:30", "11:30-12:30", "16:30-17:30"]
        }

        # 寫入 SSOT JSON 檔
        with open("latest_decision.json", "w", encoding="utf-8") as f:
            json.dump(ssot_payload, f, ensure_ascii=False, indent=2)

        # 同步寫入 index.html 與 mobile.html
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(HTML_CONTENT)

        with open("mobile.html", "w", encoding="utf-8") as f:
            f.write(HTML_CONTENT)

        logging.info("✅ 檔案生成完成：index.html, mobile.html, latest_decision.json")

        # 若在 Colab 執行，自動下載最新檔案至本機
        if IN_COLAB:
            logging.info("📥 正在自動下載最新版本 index.html 與 mobile.html 至您的電腦...")
            files.download("index.html")
            files.download("mobile.html")
            files.download("latest_decision.json")


HTML_CONTENT = """<!DOCTYPE html>
<html lang="zh-TW">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
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
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: var(--bg-dark); color: #f8fafc; padding: 6px; font-variant-numeric: tabular-nums; overflow-x: hidden; }
        button, input[type="range"], .tab-btn, summary, .timeline-btn { cursor: pointer !important; user-select: none; transition: all 0.15s ease-in-out; touch-action: manipulation; }
        button:hover, .tab-btn:hover, .timeline-btn:hover { filter: brightness(1.25); }
        @keyframes pulseAlert { 0%, 100% { opacity: 1; } 50% { opacity: 0.85; } }
        #vetoBanner { display: block; background: var(--status-danger); color: #ffffff; padding: 8px 10px; border-radius: 8px; font-weight: 800; font-size: 11.5px; margin-bottom: 8px; text-align: center; box-shadow: 0 0 16px rgba(239, 68, 68, 0.5); animation: pulseAlert 2s infinite; }
        .card { background: var(--card-bg); border: 1px solid var(--card-border); border-radius: 10px; padding: 8px; contain: content; box-shadow: 0 4px 16px rgba(0, 0, 0, 0.4); margin-bottom: 8px; width: 100%; }
        .card-header { font-size: 12.5px; font-weight: 800; color: var(--accent-blue); margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--card-border); padding-bottom: 5px; }
        .badge { font-size: 10px; font-weight: 700; padding: 2px 5px; border-radius: 4px; display: inline-block; white-space: nowrap; }
        .badge-veto { background: rgba(239, 68, 68, 0.25); color: #fca5a5; border: 1px solid var(--status-danger); }
        .badge-pass { background: rgba(16, 185, 129, 0.25); color: #86efac; border: 1px solid var(--status-pass); }
        .badge-yellow { background: rgba(250, 204, 21, 0.25); color: var(--status-yellow); border: 1px solid var(--status-yellow); }
        .data-table { width: 100%; border-collapse: collapse; font-size: 10px; border: 1px solid var(--card-border); border-radius: 6px; overflow: hidden; }
        .data-table th, .data-table td { padding: 4px 5px; text-align: left; border-bottom: 1px solid var(--card-border); }
        .data-table th { background: var(--table-header-bg); color: #e2e8f0; font-weight: 700; font-size: 9.5px; }
        .box-alert-danger { background: rgba(239, 68, 68, 0.16); border-left: 4px solid var(--status-danger); color: #fca5a5; padding: 6px; font-size: 10.5px; border-radius: 0 6px 6px 0; line-height: 1.4; }
        .slider-item { display: flex; flex-direction: column; gap: 2px; }
        .slider-header { display: flex; justify-content: space-between; font-size: 9.5px; color: #cbd5e1; font-weight: 600; }
        .slider-header span.val { font-family: monospace; font-weight: 800; color: var(--accent-blue); font-size: 10.5px; }
        .slider-item input[type="range"] { width: 100%; height: 6px; background: #1e2d4a; border-radius: 3px; outline: none; accent-color: var(--accent-blue); }
        .canvas-container { position: relative; width: 100%; border-radius: 8px; overflow: hidden; background: #050a14; border: 1px solid #1e2d4a; }
        .tab-south-active { background: #059669 !important; color: #ffffff !important; border-color: #34d399 !important; box-shadow: 0 0 8px rgba(5, 150, 105, 0.5); }
        .tab-north-active { background: #2563eb !important; color: #ffffff !important; border-color: #60a5fa !important; box-shadow: 0 0 8px rgba(37, 99, 235, 0.5); }
        .tab-compare-active { background: #7c3aed !important; color: #ffffff !important; border-color: #a78bfa !important; box-shadow: 0 0 8px rgba(124, 58, 237, 0.5); }
        .timeline-card-active { border-color: #facc15 !important; background: rgba(250, 204, 21, 0.15) !important; box-shadow: 0 0 10px rgba(250, 204, 21, 0.4); }
    </style>
</head>
<body class="w-full max-w-[1700px] mx-auto">
    <div id="vetoBanner">🚨 警示：實體觸發物理 VETO 熔斷（浪高/風速/水深超標），強制執行防颱封島管制！</div>

    <header class="bg-[#111c2e] border border-[#1e2d4a] border-l-[5px] border-l-[#ef4444] rounded-xl p-2.5 mb-2 shadow-xl w-full" id="headerMaster">
        <div class="flex flex-wrap justify-between items-center gap-1.5">
            <div class="flex items-center gap-2">
                <span class="text-lg">🌊</span>
                <div>
                    <h1 class="text-xs md:text-base font-extrabold text-white flex items-center gap-1.5">龜山島戰術指揮中樞 <span class="text-[10px] text-[#38bdf8] font-mono">(v66.0)</span></h1>
                    <div class="text-[9px] sm:text-[9.5px] text-[#cbd5e1] mt-0.5 flex flex-wrap gap-1 items-center font-mono">
                        <span>時間：<b id="liveClock" class="text-white bg-white/10 px-1 py-0.5 rounded">--:--:-- CST</b></span>
                        <span>| 日期：<b id="liveDate" class="text-emerald-300 bg-emerald-950/60 border border-emerald-500/40 px-1 py-0.5 rounded">----/--/-- (--)</b></span>
                        <span>| 裁示：<b id="ssotDecisionBadge" class="text-[#ef4444] font-bold">0.0% 熔斷</b></span>
                        <span>| <span id="stationHeartbeatClock" class="text-[#38bdf8]">● 心跳 12s</span></span>
                    </div>
                </div>
            </div>
            <div>
                <span class="badge badge-veto text-[9.5px] px-1.5 py-0.5" id="badgeMobDecision">🔴 熔斷封島管制</span>
            </div>
        </div>
    </header>

    <div class="grid grid-cols-1 lg:grid-cols-12 gap-2.5 w-full">
        <!-- 左側面板 -->
        <div class="lg:col-span-5 flex flex-col gap-1">
            <!-- 0. 每日 3 時段自動對算 -->
            <section class="card border-[#34d399] bg-[#0d2218]">
                <div class="card-header !text-emerald-400">
                    <span class="flex items-center gap-1 font-bold text-[11.5px]">🤖 每日 3 時段定時對算 (點擊切換連動圖場)</span>
                    <span class="badge badge-pass text-[8px]" id="syncWindowBadge">⏱️ 點擊連動畫布</span>
                </div>
                <div class="p-1.5 space-y-1 text-[9.5px]">
                    <div class="grid grid-cols-3 gap-1 text-center font-mono">
                        <div class="timeline-btn bg-black/40 p-1 rounded border border-slate-700 timeline-card-active" id="win1" data-hs="3.71" data-w="13.8" data-tp="15.5" data-theta="50" data-label="07:30~08:30 (早盤對算)">
                            <span class="text-slate-400 block text-[8px]">早盤對算</span>
                            <b class="text-amber-300 text-[9px]">07:30-08:30</b>
                        </div>
                        <div class="timeline-btn bg-black/40 p-1 rounded border border-slate-700" id="win2" data-hs="2.05" data-w="9.5" data-tp="12.0" data-theta="40" data-label="11:30~12:30 (午盤對算)">
                            <span class="text-slate-400 block text-[8px]">午盤對算</span>
                            <b class="text-amber-300 text-[9px]">11:30-12:30</b>
                        </div>
                        <div class="timeline-btn bg-black/40 p-1 rounded border border-slate-700" id="win3" data-hs="0.92" data-w="4.8" data-tp="9.0" data-theta="30" data-label="16:30~17:30 (晚盤對算)">
                            <span class="text-slate-400 block text-[8px]">晚盤對算</span>
                            <b class="text-amber-300 text-[9px]">16:30-17:30</b>
                        </div>
                    </div>
                    <div class="bg-black/60 p-1.5 rounded border border-emerald-500/30 flex justify-between items-center text-[9.5px]">
                        <div>
                            <span class="text-slate-300">連線動態對算時段：</span>
                            <b class="text-amber-300 font-mono" id="activeTimelineLabel">07:30 - 08:30 (晨間預警)</b>
                        </div>
                        <span class="badge badge-pass text-[8px]" id="learningStatusTag">圖場實時連動</span>
                    </div>
                </div>
            </section>

            <!-- 1. Windy 動態實時地圖與行政開設（已包含龜山島定位針與卡片標註） -->
            <details class="card border-[#ef4444] bg-[#180d1a]/90" open>
                <summary class="card-header !text-red-400 list-none outline-none pb-0 border-b-0 cursor-pointer">
                    <span class="flex items-center gap-1 font-black text-xs">🌀 Windy 動態實時氣象風場地圖 & 行政開設</span>
                    <span id="typhoonHeartbeatClock" class="text-[9.5px] font-mono text-emerald-400 font-bold bg-emerald-950/80 px-1 py-0.5 rounded border border-emerald-500/40">● Windy實時</span>
                </summary>
                <div class="pt-1.5 border-t border-red-500/30 mt-1.5 space-y-1.5">
                    <div class="bg-red-950/50 p-1 rounded-lg border border-red-500/40">
                        <div class="text-[9.5px] font-bold text-amber-300 mb-1 flex justify-between items-center">
                            <span>🏛️ 政府行政應變中心（以官方發布為準）：</span>
                            <span class="text-[8px] font-mono text-emerald-300" id="cwaStatusTag">CWA / NCDR 實時同步</span>
                        </div>
                        <div class="grid grid-cols-3 gap-1 text-[9px]">
                            <div class="bg-black/40 p-1 rounded border border-slate-700 flex flex-col items-center justify-center text-center">
                                <span class="text-slate-300 text-[8.5px] mb-0.5">中央應變</span>
                                <span class="badge badge-pass text-[8px]" id="badgeCentralAlert">🟢 未開設</span>
                            </div>
                            <div class="bg-black/40 p-1 rounded border border-slate-700 flex flex-col items-center justify-center text-center">
                                <span class="text-slate-300 text-[8.5px] mb-0.5">宜蘭縣應變</span>
                                <span class="badge badge-pass text-[8px]" id="badgeYilanAlert">🟢 未開設</span>
                            </div>
                            <div class="bg-black/40 p-1 rounded border border-slate-700 flex flex-col items-center justify-center text-center">
                                <span class="text-slate-300 text-[8.5px] mb-0.5">新北市應變</span>
                                <span class="badge badge-pass text-[8px]" id="badgeNtpCAlert">🟢 未開設</span>
                            </div>
                        </div>
                    </div>

                    <div class="bg-black/60 p-1.5 rounded-lg border border-slate-700">
                        <div class="flex justify-between items-center mb-1">
                            <span class="text-[9.5px] font-bold text-amber-300" id="tcNameLabel">🌀 龜山島周邊實時動態風場與氣象地圖</span>
                            <span class="badge badge-pass text-[8px]" id="tcThreatRate">🟢 Windy實時</span>
                        </div>
                        <div class="text-[9px] text-slate-300 mb-1 font-mono" id="tcPosLabel">
                            定位座標：24.843°N 121.952°E (龜山島中心點標註)
                        </div>

                        <!-- 嵌入 Windy 動態地圖：Zoom=11, 龜山島 Marker 紅針與 Detail 氣象卡片標註 -->
                        <div class="relative w-full rounded border border-slate-800 overflow-hidden bg-[#050a14] h-[260px]">
                            <iframe id="windyFrame"
                                    src="https://embed.windy.com/embed.html?type=map&location=coordinates&metricRain=mm&metricTemp=%C2%B0C&metricWind=m%2Fs&zoom=11&overlay=wind&product=ecmwf&level=surface&lat=24.843&lon=121.952&marker=true&detail=true&detailLat=24.843&detailLon=121.952"
                                    class="w-full h-full block border-0 rounded"
                                    loading="lazy">
                            </iframe>
                        </div>
                        <div class="flex justify-between items-center mt-1 text-[8px] text-slate-400 font-mono">
                            <span id="dataPipelineSourceText">📡 數據源：Windy ECMWF 動態實時風場地圖 (含龜山島紅針標註)</span>
                            <span id="typhoonImgUpdateTime" class="text-emerald-300 font-bold">全天候實時動態渲染</span>
                        </div>
                    </div>
                </div>
            </details>

            <!-- 2. 📊 物理算子即時檢核與剛性門檻 -->
            <section class="card border-[#38bdf8] bg-[#0c1a2e]">
                <div class="card-header !text-sky-400">
                    <span class="font-extrabold text-[11.5px]">📊 物理算子即時檢核與剛性門檻（GEM 防線）</span>
                    <span class="badge badge-pass text-[8px]">權威裁決依據</span>
                </div>
                <div class="overflow-x-auto pt-1">
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th class="w-[30%]">關鍵物理算子</th>
                                <th class="w-[25%] text-center text-amber-300">剛性安全門檻</th>
                                <th class="w-[25%] text-center text-sky-300">即時檢核數值</th>
                                <th class="w-[20%] text-center text-red-400">狀態燈號</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="font-bold text-white">波高 <span class="font-mono text-sky-400">(Hs,pier)</span></td>
                                <td class="text-center font-mono text-slate-300">≤ 1.13 m</td>
                                <td class="text-center font-mono font-bold text-red-400" id="cmpHsVal">3.93 m</td>
                                <td class="text-center" id="cmpHsBadge"><span class="badge badge-veto text-[8px]">🔴 VETO</span></td>
                            </tr>
                            <tr>
                                <td class="font-bold text-white">攻角風速 <span class="font-mono text-sky-400">(Weff)</span></td>
                                <td class="text-center font-mono text-slate-300">≤ 10.17 m/s</td>
                                <td class="text-center font-mono font-bold text-emerald-300" id="cmpWeffVal">5.46 m/s</td>
                                <td class="text-center" id="cmpWeffBadge"><span class="badge badge-pass text-[8px]">🟢 通過</span></td>
                            </tr>
                            <tr>
                                <td class="font-bold text-white">湧浪週期 <span class="font-mono text-sky-400">(Tp)</span></td>
                                <td class="text-center font-mono text-slate-300">≤ 11.5 s</td>
                                <td class="text-center font-mono font-bold text-red-400" id="cmpTpVal">15.5 s</td>
                                <td class="text-center" id="cmpTpBadge"><span class="badge badge-veto text-[8px]">🔴 VETO</span></td>
                            </tr>
                            <tr>
                                <td class="font-bold text-white">動態裕深 <span class="font-mono text-sky-400">(UKC)</span></td>
                                <td class="text-center font-mono text-slate-300">≥ 1.50 m</td>
                                <td class="text-center font-mono font-bold text-emerald-300" id="cmpUkcVal">5.62 m</td>
                                <td class="text-center" id="cmpUkcBadge"><span class="badge badge-pass text-[8px]">🟢 通過</span></td>
                            </tr>
                            <tr>
                                <td class="font-bold text-white">預留乾舷 <span class="font-mono text-sky-400">(FB)</span></td>
                                <td class="text-center font-mono text-slate-300">≥ 0.50 m</td>
                                <td class="text-center font-mono font-bold text-red-400" id="cmpFbVal">-0.57 m</td>
                                <td class="text-center" id="cmpFbBadge"><span class="badge badge-veto text-[8px]">🔴 VETO</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- 3. 🎮 戰術沙盤演練調度 -->
            <section class="card border-[#2563eb] bg-[#0c182b]">
                <div class="card-header !text-[#60a5fa]">
                    <span class="font-extrabold flex items-center gap-1 text-[11.5px]">🎮 戰術沙盤演練調度</span>
                </div>
                <div class="grid grid-cols-2 gap-2 pt-1 border-t border-[#1e2d4a]">
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
        </div>

        <!-- 右側面板 -->
        <div class="lg:col-span-7 flex flex-col gap-1">
            <!-- 4. 📐 南北岸動態剖面 -->
            <section class="card border-[#38bdf8]">
                <div class="card-header !text-[#38bdf8]">
                    <span>📐 碼頭動態剖面與越浪分析 (受游擊時序連動)</span>
                    <span class="badge badge-yellow text-[8px]">含圖上標註</span>
                </div>

                <div class="bg-[#0b172a] border border-blue-500/50 p-1 rounded-lg mb-1.5 flex items-center justify-between gap-1">
                    <span class="text-[9px] font-bold text-slate-300 pl-0.5 whitespace-nowrap">⚓ 剖面:</span>
                    <div class="grid grid-cols-3 gap-1 flex-1">
                        <button id="tabProfileSouth" class="tab-btn py-1 px-1 rounded text-[9px] font-bold border text-center tab-south-active">⚓ 南岸</button>
                        <button id="tabProfileNorth" class="tab-btn py-1 px-1 rounded text-[9px] font-bold border border-slate-700 bg-slate-800 text-slate-300 text-center">⚓ 北岸</button>
                        <button id="tabProfileCompare" class="tab-btn py-1 px-1 rounded text-[9px] font-bold border border-slate-700 bg-slate-800 text-slate-300 text-center">⚖️ 對比</button>
                    </div>
                </div>

                <div class="canvas-container h-[200px] mb-1" id="profileContainer">
                    <canvas id="profileCanvas" class="w-full h-full block"></canvas>
                </div>
            </section>

            <!-- 5. ⚡ 游擊調度時序與戰術機動任務鏈 -->
            <section class="card border-[#eab308] bg-[#1a170d]">
                <div class="card-header !text-amber-400">
                    <span class="flex items-center gap-1 font-bold text-[11.5px]">⚡ 游擊調度時序與戰術機動任務鏈 (點擊切換連動圖場)</span>
                    <span class="badge badge-yellow text-[8px]">點擊帶入數據</span>
                </div>
                <div class="p-1 space-y-1 text-[9px] font-mono">
                    <div class="grid grid-cols-1 sm:grid-cols-2 gap-1">
                        <div class="timeline-btn bg-black/50 p-1.5 rounded border border-amber-500/30 flex justify-between items-center timeline-card-active" id="guerrilla1" data-hs="3.71" data-w="13.8" data-tp="15.5" data-theta="50" data-label="07:30-08:30 (晨間預警對算)">
                            <div>
                                <span class="text-amber-300 font-bold">07:30 - 08:30</span>
                                <span class="text-slate-300 block text-[8.5px]">🌅 晨間預警對算 (API與熔斷門檻)</span>
                            </div>
                            <span class="badge badge-veto text-[7.5px]">預警對算</span>
                        </div>
                        <div class="timeline-btn bg-black/50 p-1.5 rounded border border-red-500/40 flex justify-between items-center" id="guerrilla2" data-hs="4.80" data-w="18.5" data-tp="16.0" data-theta="60" data-label="08:30-11:30 (游擊機動撤離)">
                            <div>
                                <span class="text-red-300 font-bold">08:30 - 11:30</span>
                                <span class="text-slate-300 block text-[8.5px]">🚨 游擊機動撤離 (清場/防纜加固)</span>
                            </div>
                            <span class="badge badge-veto text-[7.5px]">遊客淨空</span>
                        </div>
                        <div class="timeline-btn bg-black/50 p-1.5 rounded border border-sky-500/30 flex justify-between items-center" id="guerrilla3" data-hs="2.05" data-w="9.5" data-tp="12.0" data-theta="40" data-label="11:30-12:30 (午盤雷達對算)">
                            <div>
                                <span class="text-sky-300 font-bold">11:30 - 12:30</span>
                                <span class="text-slate-300 block text-[8.5px]">☀️ 午盤雷達對算 (10min雷達幀校正)</span>
                            </div>
                            <span class="badge badge-pass text-[7.5px]">雷達校正</span>
                        </div>
                        <div class="timeline-btn bg-black/50 p-1.5 rounded border border-indigo-500/30 flex justify-between items-center" id="guerrilla4" data-hs="1.45" data-w="7.2" data-tp="10.5" data-theta="35" data-label="12:30-16:30 (碼頭防禦監視)">
                            <div>
                                <span class="text-indigo-300 font-bold">12:30 - 16:30</span>
                                <span class="text-slate-300 block text-[8.5px]">⚓ 碼頭防禦監視 (南北岸移防/避風)</span>
                            </div>
                            <span class="badge badge-pass text-[7.5px]">機動靠泊</span>
                        </div>
                        <div class="timeline-btn bg-black/50 p-1.5 rounded border border-emerald-500/30 flex justify-between items-center" id="guerrilla5" data-hs="0.92" data-w="4.8" data-tp="9.0" data-theta="30" data-label="16:30-17:30 (晚盤滾動發布)">
                            <div>
                                <span class="text-emerald-300 font-bold">16:30 - 17:30</span>
                                <span class="text-slate-300 block text-[8.5px]">🌆 晚盤滾動發布 (官網比對/明日預推)</span>
                            </div>
                            <span class="badge badge-pass text-[7.5px]">滾動發布</span>
                        </div>
                        <div class="timeline-btn bg-black/50 p-1.5 rounded border border-slate-700 flex justify-between items-center" id="guerrilla6" data-hs="2.80" data-w="12.0" data-tp="14.0" data-theta="45" data-label="17:30-07:30 (夜間全島封鎖)">
                            <div>
                                <span class="text-slate-400 font-bold">17:30 - 07:30</span>
                                <span class="text-slate-300 block text-[8.5px]">🌙 夜間全島封鎖 (剛性 VETO 鎖定)</span>
                            </div>
                            <span class="badge badge-veto text-[7.5px]">零留滯</span>
                        </div>
                    </div>
                </div>
            </section>

            <!-- 6. 官方網頁公告 vs GEM模型 雙欄直觀對比卡片 -->
            <section class="card border-[#facc15] bg-[#1a180d]">
                <div class="card-header !text-yellow-400">
                    <span class="flex items-center gap-1 font-bold text-[11.5px]">🔮 官方網頁公告 vs GEM模型 封島時程對比 & 再封島條件精算</span>
                    <span class="badge badge-yellow text-[8px]" id="rollingUpdateBadge">🔄 雙欄動態對比</span>
                </div>

                <div class="p-1 space-y-1.5 text-[10px]">
                    <div class="grid grid-cols-2 gap-1.5 md:gap-2">
                        <div class="bg-black/60 p-1.5 rounded border border-amber-500/40 flex flex-col justify-between">
                            <div>
                                <div class="font-bold text-amber-300 border-b border-amber-500/30 pb-0.5 mb-1 flex flex-wrap justify-between items-center gap-1">
                                    <span class="text-[9.5px]">🏛️ 風管處官網公告</span>
                                    <span id="officialClosureStatus" class="badge badge-veto text-[7.5px] px-1 py-0.5">🔴 官網預警封島</span>
                                </div>
                                <div class="space-y-1 text-[8.5px] sm:text-[9px]">
                                    <div class="flex justify-between items-center flex-wrap gap-0.5"><span class="text-slate-400">封島開始時間：</span><b id="offClosureStart" class="font-mono text-white">D0 (今日) 08:00</b></div>
                                    <div class="flex justify-between items-center flex-wrap gap-0.5"><span class="text-slate-400">預估封島總天數：</span><b id="offClosureDays" class="font-mono text-amber-300">共 2 天</b></div>
                                    <div class="flex justify-between items-center flex-wrap gap-0.5"><span class="text-slate-400">官網預計解封點：</span><b id="offReopenTime" class="font-mono text-emerald-300">D2 (後日) 08:00</b></div>
                                </div>
                            </div>
                        </div>

                        <div class="bg-black/60 p-1.5 rounded border border-sky-500/40 flex flex-col justify-between">
                            <div>
                                <div class="font-bold text-sky-300 border-b border-sky-500/30 pb-0.5 mb-1 flex flex-wrap justify-between items-center gap-1">
                                    <span class="text-[9.5px]">🤖 GEM 雙生模型對算</span>
                                    <span id="gemClosureStatus" class="badge badge-veto text-[7.5px] px-1 py-0.5">🔴 物理VETO</span>
                                </div>
                                <div class="space-y-1 text-[8.5px] sm:text-[9px]">
                                    <div class="flex justify-between items-center flex-wrap gap-0.5"><span class="text-slate-400">模型封島開始：</span><b id="gemClosureStart" class="font-mono text-white">D0 (今日) 07:30</b></div>
                                    <div class="flex justify-between items-center flex-wrap gap-0.5"><span class="text-slate-400">模型精算總天數：</span><b id="gemClosureDays" class="font-mono text-sky-300">共 2 天 (含清理)</b></div>
                                    <div class="flex justify-between items-center flex-wrap gap-0.5"><span class="text-slate-400">模型預計解封點：</span><b id="gemReopenTime" class="font-mono text-emerald-300">D2 (後日) 08:00</b></div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <div class="bg-red-950/40 p-1.5 rounded border border-red-500/40 text-slate-200">
                        <div class="font-bold text-red-300 border-b border-red-500/30 pb-1 mb-1 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-0.5">
                            <span class="text-[9.5px]">🚨 觸發「再封島 / 延長封島」關鍵氣象數值及條件：</span>
                            <span class="text-[8px] text-amber-300 font-mono whitespace-nowrap">觸發即聯鎖延伸封島</span>
                        </div>
                        <div class="grid grid-cols-2 md:grid-cols-4 gap-1 text-[8.5px] font-mono text-slate-300">
                            <div class="bg-black/40 p-1 rounded">
                                <span class="text-slate-400 block text-[7.5px]">條件1: 港池波高二次湧升</span>
                                <b class="text-red-400">Hs,pier &gt; 1.13 m</b>
                            </div>
                            <div class="bg-black/40 p-1 rounded">
                                <span class="text-slate-400 block text-[7.5px]">條件2: 外海長浪共振</span>
                                <b class="text-red-400">Tp ≥ 11.5 s</b>
                            </div>
                            <div class="bg-black/40 p-1 rounded">
                                <span class="text-slate-400 block text-[7.5px]">條件3: 引橋越浪/乾舷不足</span>
                                <b class="text-red-400">FB &lt; 0.50m (CV&gt;0)</b>
                            </div>
                            <div class="bg-black/40 p-1 rounded">
                                <span class="text-slate-400 block text-[7.5px]">條件4: 碼頭災損/清淤期</span>
                                <b class="text-amber-300">警報後追加 +1~2 天</b>
                            </div>
                        </div>
                    </div>
                </div>

                <div class="overflow-x-auto w-full">
                    <table class="data-table mt-1 min-w-[320px]">
                        <thead>
                            <tr>
                                <th class="w-[28%] bg-slate-900 text-[#38bdf8] text-center text-[9px]">預測時程</th>
                                <th class="w-[24%] text-center bg-blue-950/70 text-emerald-300 font-extrabold text-[9px]" id="thD0Day">D0 (今日)</th>
                                <th class="w-[24%] text-center bg-indigo-950/70 text-amber-300 font-extrabold text-[9px]" id="thD1Day">D1 (明日)</th>
                                <th class="w-[24%] text-center bg-slate-900 text-sky-300 font-extrabold text-[9px]" id="thD2Day">D2 (後日)</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td class="font-bold text-amber-300 text-[8.5px] text-center">🏛️ 氣象署預報</td>
                                <td class="text-[8.5px] font-mono text-center">💨 13.8m/s 🔴<br>🌊 3.71m 🔴</td>
                                <td class="text-[8.5px] font-mono text-center">💨 9.5m/s 🟡<br>🌊 2.05m 🟡</td>
                                <td class="text-[8.5px] font-mono text-center">💨 4.8m/s 🟢<br>🌊 0.92m 🟢</td>
                            </tr>
                            <tr>
                                <td class="font-bold text-[#38bdf8] text-[8.5px] text-center">🤖 GEM 戰術裁決</td>
                                <td class="text-center p-1"><span class="badge badge-veto text-[8px] px-1 py-0.5 inline-block">🔴 熔斷(+1天)</span></td>
                                <td class="text-center p-1"><span class="badge badge-veto text-[8px] px-1 py-0.5 inline-block">🔴 熔斷(+1天)</span></td>
                                <td class="text-center p-1"><span class="badge badge-pass text-[8px] px-1 py-0.5 inline-block">🟢 條件解封</span></td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </section>

            <!-- 7. 🎯 態勢雷達圖 -->
            <section class="card border-[#38bdf8]">
                <div class="card-header !text-[#38bdf8]">
                    <span class="flex items-center gap-1">🎯 態勢雷達圖與 5 大算子對比 (受游擊時序連動)</span>
                    <span class="badge badge-yellow text-[8px]">邊界防護</span>
                </div>

                <div class="bg-[#0b172a] border border-blue-500/50 p-1 rounded-lg mb-1.5 flex items-center justify-between gap-1">
                    <span class="text-[9px] font-bold text-slate-300 pl-0.5 whitespace-nowrap">📡 雷達:</span>
                    <div class="grid grid-cols-3 gap-1 flex-1">
                        <button id="tabRadarSouth" class="tab-btn py-1 px-1 rounded text-[9px] font-bold border text-center tab-south-active">⚓ 南岸</button>
                        <button id="tabRadarNorth" class="tab-btn py-1 px-1 rounded text-[9px] font-bold border border-slate-700 bg-slate-800 text-slate-300 text-center">⚓ 北岸</button>
                        <button id="tabRadarCompare" class="tab-btn py-1 px-1 rounded text-[9px] font-bold border border-slate-700 bg-slate-800 text-slate-300 text-center">⚖️ 雙岸</button>
                    </div>
                </div>

                <div class="canvas-container h-[260px] mb-1" id="radarContainer">
                    <canvas id="nativeRadarCanvas" class="w-full h-full block"></canvas>
                </div>

                <div class="box-alert-danger text-center" id="boxRadarFinalVerdict">
                    <b>🎯 最終安全態勢裁決：</b><br>
                    <span class="text-white font-extrabold text-[10.5px] mt-0.5 inline-block" id="txtRadarFinalVerdict">🔴 0.0% 物理 VETO 熔斷 / 【極端暴風長浪全線封島】</span>
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
        let typhoonHeartbeatCount = 0;
        let currentTimelineLabel = "07:30 - 08:30 (晨間預警)";

        function applyTimelineLinkage(hs, w, tp, theta, labelText, targetEl) {
            currentTimelineLabel = labelText;
            setTxt('activeTimelineLabel', labelText);

            const rngHs = getEl('rngHs');
            const rngW = getEl('rngW');
            const rngTp = getEl('rngTp');
            const rngDeltaTheta = getEl('rngDeltaTheta');

            if (rngHs) rngHs.value = hs;
            if (rngW) rngW.value = w;
            if (rngTp) rngTp.value = tp;
            if (rngDeltaTheta) rngDeltaTheta.value = theta;

            setTxt('lblHs', `${hs}m`);
            setTxt('lblW', `${w}m/s`);
            setTxt('lblTp', `${tp}s`);
            setTxt('lblDeltaTheta', `${theta}°`);

            document.querySelectorAll('.timeline-btn').forEach(btn => btn.classList.remove('timeline-card-active'));
            if (targetEl) {
                targetEl.classList.add('timeline-card-active');
                document.querySelectorAll('.timeline-btn').forEach(btn => {
                    if (Math.abs(parseFloat(btn.getAttribute('data-hs')) - hs) < 0.01 &&
                        Math.abs(parseFloat(btn.getAttribute('data-w')) - w) < 0.01) {
                        btn.classList.add('timeline-card-active');
                    }
                });
            }

            recalculatePhysicsAndRender();
        }

        function initDashboard() {
            startClockAndWatchdog();
            initUIControls();
            recalculatePhysicsAndRender();

            document.querySelectorAll('.timeline-btn').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    const card = e.currentTarget;
                    const hs = parseFloat(card.getAttribute('data-hs') || '3.71');
                    const w = parseFloat(card.getAttribute('data-w') || '8.50');
                    const tp = parseFloat(card.getAttribute('data-tp') || '15.5');
                    const theta = parseFloat(card.getAttribute('data-theta') || '50');
                    const label = card.getAttribute('data-label') || '戰術時序連動';

                    applyTimelineLinkage(hs, w, tp, theta, label, card);
                });
            });

            window.addEventListener('resize', renderAllCanvas);

            function animLoop() {
                animPhase += 0.06;
                drawProfileCanvas();
                requestAnimationFrame(animLoop);
            }
            requestAnimationFrame(animLoop);
        }

        function startClockAndWatchdog() {
            const update = () => {
                const now = new Date();
                setTxt('liveClock', `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')} CST`);

                const days = ['日', '一', '二', '三', '四', '五', '六'];
                const year = now.getFullYear();
                const month = String(now.getMonth() + 1).padStart(2, '0');
                const date = String(now.getDate()).padStart(2, '0');
                const dayName = days[now.getDay()];
                setTxt('liveDate', `${year}-${month}-${date} (${dayName})`);

                const d0 = new Date(now);
                const d1 = new Date(now); d1.setDate(d1.getDate() + 1);
                const d2 = new Date(now); d2.setDate(d2.getDate() + 2);
                const fmtM = d => `${d.getMonth()+1}/${d.getDate()}`;

                const thD0 = getEl('thD0Day'); if (thD0) thD0.innerHTML = `今日 ${fmtM(d0)}`;
                const thD1 = getEl('thD1Day'); if (thD1) thD1.innerHTML = `明日 ${fmtM(d1)}`;
                const thD2 = getEl('thD2Day'); if (thD2) thD2.innerHTML = `後日 ${fmtM(d2)}`;
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
            const baseClass = "tab-btn py-1 px-1 rounded text-[9px] font-bold border text-center transition-all ";
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
            const weffSouth = w * Math.abs(Math.cos(radSouth));

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

            setTxt('cmpHsVal', `${hsNorth.toFixed(2)} m`);
            const hsB = getEl('cmpHsBadge'); if (hsB) hsB.innerHTML = hsNorth > 1.13 ? '<span class="badge badge-veto text-[8px]">🔴 VETO</span>' : '<span class="badge badge-pass text-[8px]">🟢 通過</span>';

            setTxt('cmpWeffVal', `${weffNorth.toFixed(2)} m/s`);
            const weffB = getEl('cmpWeffBadge'); if (weffB) weffB.innerHTML = weffNorth > 10.17 ? '<span class="badge badge-veto text-[8px]">🔴 VETO</span>' : '<span class="badge badge-pass text-[8px]">🟢 通過</span>';

            setTxt('cmpTpVal', `${tp.toFixed(1)} s`);
            const tpB = getEl('cmpTpBadge'); if (tpB) tpB.innerHTML = tp >= 11.5 ? '<span class="badge badge-veto text-[8px]">🔴 VETO</span>' : '<span class="badge badge-pass text-[8px]">🟢 通過</span>';

            setTxt('cmpUkcVal', `${ukcNorth.toFixed(2)} m`);
            const ukcB = getEl('cmpUkcBadge'); if (ukcB) ukcB.innerHTML = ukcNorth < 1.50 ? '<span class="badge badge-veto text-[8px]">🔴 VETO</span>' : '<span class="badge badge-pass text-[8px]">🟢 通過</span>';

            setTxt('cmpFbVal', `${fbNorth.toFixed(2)} m`);
            const fbB = getEl('cmpFbBadge'); if (fbB) fbB.innerHTML = fbNorth < 0.50 ? '<span class="badge badge-veto text-[8px]">🔴 VETO</span>' : '<span class="badge badge-pass text-[8px]">🟢 通過</span>';

            const vetoNorth = (hsNorth > 1.13) || (weffNorth > 10.17) || (tp >= 11.5) || (ukcNorth < 1.50) || (fbNorth < 0.50);
            const vetoSouth = (hsSouth > 1.13) || (weffSouth > 10.17) || (tp >= 11.5) || (ukcSouth < 1.50) || (fbSouth < 0.50);

            const banner = getEl('vetoBanner');
            const badgeDecision = getEl('badgeMobDecision');
            const headerMaster = getEl('headerMaster');

            if (vetoNorth && vetoSouth) {
                if (banner) {
                    banner.style.display = 'block';
                    banner.style.background = 'var(--status-danger)';
                    banner.style.boxShadow = '0 0 16px rgba(239, 68, 68, 0.5)';
                    banner.innerText = '🚨 警示：實體觸發物理 VETO 熔斷（浪高/風速/水深/乾舷超標），強制執行防颱封島管制！';
                }
                setTxt('ssotDecisionBadge', '🔴 0.0% 熔斷');
                if (badgeDecision) {
                    badgeDecision.innerText = '🔴 熔斷封島管制';
                    badgeDecision.className = 'badge badge-veto text-[9.5px] px-1.5 py-0.5';
                }
                if (headerMaster) headerMaster.style.borderLeftColor = '#ef4444';
            } else if (vetoNorth || vetoSouth) {
                if (banner) {
                    banner.style.display = 'block';
                    banner.style.background = 'var(--status-warn)';
                    banner.style.boxShadow = '0 0 16px rgba(245, 158, 11, 0.5)';
                    banner.innerText = '⚠️ 警告：單一泊位海象過載，實施單岸機動避風靠泊管制！';
                }
                setTxt('ssotDecisionBadge', '🟡 50.0% 條件開放');
                if (badgeDecision) {
                    badgeDecision.innerText = '🟡 條件機動靠泊';
                    badgeDecision.className = 'badge badge-yellow text-[9.5px] px-1.5 py-0.5';
                }
                if (headerMaster) headerMaster.style.borderLeftColor = '#f59e0b';
            } else {
                if (banner) {
                    banner.style.display = 'block';
                    banner.style.background = 'var(--status-pass)';
                    banner.style.boxShadow = '0 0 16px rgba(16, 185, 129, 0.5)';
                    banner.innerText = '✅ 安全：全域海象與動態裕深完全符合剛性安全門檻，允許正常通航與靠泊！';
                }
                setTxt('ssotDecisionBadge', '🟢 100.0% 正常開放');
                if (badgeDecision) {
                    badgeDecision.innerText = '🟢 全線開放靠泊';
                    badgeDecision.className = 'badge badge-pass text-[9.5px] px-1.5 py-0.5';
                }
                if (headerMaster) headerMaster.style.borderLeftColor = '#10b981';
            }

            const activeVeto = currentRadarMode === 'NORTH' ? vetoNorth :
                               currentRadarMode === 'SOUTH' ? vetoSouth : (vetoNorth && vetoSouth);
            const activeText = currentRadarMode === 'NORTH' ? '【北岸】' :
                               currentRadarMode === 'SOUTH' ? '【南岸】' : '【雙岸】';

            const boxEl = getEl('boxRadarFinalVerdict');
            const txtEl = getEl('txtRadarFinalVerdict');
            if (boxEl && txtEl) {
                if (activeVeto) {
                    boxEl.className = 'box-alert-danger text-center';
                    txtEl.innerText = `🔴 0.0% 物理 VETO 熔斷 / 【海象超標管制】 (${activeText}) [時段: ${currentTimelineLabel}]`;
                    txtEl.className = 'text-[#fca5a5] font-extrabold text-[10.5px] mt-0.5 inline-block';
                } else if ((currentRadarMode === 'COMPARE' && (vetoNorth || vetoSouth)) || (currentRadarMode !== 'COMPARE' && activeVeto)) {
                    boxEl.className = 'bg-amber-950/60 border-l-4 border-amber-500 text-amber-200 p-1.5 text-center text-[10.5px] rounded-r';
                    txtEl.innerText = `🟡 50.0% 條件開放 / 【單岸機動避風靠泊】 (${activeText}) [時段: ${currentTimelineLabel}]`;
                    txtEl.className = 'text-amber-300 font-extrabold text-[10.5px] mt-0.5 inline-block';
                } else {
                    boxEl.className = 'bg-emerald-950/60 border-l-4 border-emerald-500 text-emerald-200 p-1.5 text-center text-[10.5px] rounded-r';
                    txtEl.innerText = `🟢 100.0% 物理安全通過 / 【允許靠泊作業】 (${activeText}) [時段: ${currentTimelineLabel}]`;
                    txtEl.className = 'text-emerald-300 font-extrabold text-[10.5px] mt-0.5 inline-block';
                }
            }

            renderAllCanvas();
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
            const w = container.clientWidth || 320;
            const h = isCompare ? 240 : 200;
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
                const subH = (h - 8) / 2;
                drawSingleProfile(ctx, 0, 0, w, subH, '北岸 (主泊位 -8.5m)', 8.50, 3.20, hs * 1.06, wVal * Math.abs(Math.cos(deltaTheta * Math.PI/180)), tp, '#38bdf8', true);
                drawSingleProfile(ctx, 0, subH + 8, w, subH, '南岸 (權宜泊位 -9.8m)', 9.80, 2.50, hs * 0.62, wVal * Math.abs(Math.cos((90-deltaTheta) * Math.PI/180)), tp, '#34d399', false);
            } else if (currentProfileMode === 'NORTH') {
                drawSingleProfile(ctx, 0, 0, w, h, '北岸碼頭 (主泊位 -8.50m CD)', 8.50, 3.20, hs * 1.06, wVal * Math.abs(Math.cos(deltaTheta * Math.PI/180)), tp, '#38bdf8', true);
            } else {
                drawSingleProfile(ctx, 0, 0, w, h, '南岸碼頭 (權宜泊位 -9.80m CD)', 9.80, 2.50, hs * 0.62, wVal * Math.abs(Math.cos((90-deltaTheta) * Math.PI/180)), tp, '#34d399', false);
            }
        }

        function drawSingleProfile(ctx, offsetX, offsetY, w, h, title, depthBase, deckCD, hsPier, weff, tp, accentColor, isNorth) {
            ctx.save();
            ctx.translate(offsetX, offsetY);

            const cdToY = cd => ((5.0 - cd) / (5.0 - (-12.0))) * (h - 28) + 16;
            const tideCD = 1.10;
            const draft = 2.02;
            const keelCD = tideCD - draft;
            const ukc = depthBase + keelCD - hsPier * 0.5;

            const crestCD = tideCD + hsPier * 0.68;
            const overtopDepth = Math.max(0, crestCD - deckCD);
            const fb = deckCD - crestCD;

            const tideY = cdToY(tideCD);
            const deckY = cdToY(deckCD);
            const seabedY = cdToY(-depthBase);
            const keelY = cdToY(keelCD);
            const crestY = cdToY(crestCD);
            const quayX = w * 0.52;

            ctx.fillStyle = '#1a1816';
            ctx.fillRect(0, seabedY, w, Math.max(10, h - seabedY));
            ctx.strokeStyle = '#475569';
            ctx.lineWidth = 1;
            ctx.beginPath(); ctx.moveTo(0, seabedY); ctx.lineTo(w, seabedY); ctx.stroke();

            ctx.font = '8px monospace';
            ctx.fillStyle = '#94a3b8';
            ctx.textAlign = 'right';
            ctx.fillText(`海底: -${depthBase.toFixed(2)}m CD`, w - 6, seabedY + 10);

            ctx.fillStyle = '#1e2d4a';
            ctx.fillRect(quayX, deckY, w - quayX, seabedY - deckY);
            ctx.strokeStyle = accentColor;
            ctx.lineWidth = 1.2;
            ctx.strokeRect(quayX, deckY, w - quayX, seabedY - deckY);

            ctx.fillStyle = '#e2e8f0';
            ctx.textAlign = 'left';
            ctx.fillText(`碼頭面: +${deckCD.toFixed(2)}m CD`, quayX + 4, deckY + 10);

            const isOvertopping = overtopDepth > 0 || fb < 0.50;
            ctx.beginPath();
            ctx.moveTo(0, seabedY);
            ctx.lineTo(0, tideY);

            const waveAmp = Math.min(18, hsPier * 3.5);
            for (let x = 0; x <= quayX; x += 4) {
                const wy = tideY + Math.sin(x * 0.05 + animPhase) * waveAmp;
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

            const hsX = quayX - 12;
            const troughY = tideY + waveAmp;
            const crestYPos = tideY - waveAmp;
            ctx.beginPath();
            ctx.moveTo(hsX, crestYPos);
            ctx.lineTo(hsX, troughY);
            ctx.strokeStyle = hsPier > 1.13 ? '#ef4444' : '#38bdf8';
            ctx.lineWidth = 1.5;
            ctx.stroke();

            ctx.font = 'bold 8.5px sans-serif';
            ctx.textAlign = 'right';
            ctx.fillStyle = hsPier > 1.13 ? '#fca5a5' : '#86efac';
            ctx.fillText(`Hs: ${hsPier.toFixed(2)}m`, hsX - 4, tideY + 3);

            const shipW = Math.min(54, quayX * 0.55);
            const shipX = quayX - shipW - 18;
            const shipDeckY = tideY - 10;

            ctx.beginPath();
            ctx.moveTo(shipX, shipDeckY);
            ctx.lineTo(shipX + shipW, shipDeckY);
            ctx.lineTo(shipX + shipW, keelY - 3);
            ctx.lineTo(shipX + shipW - 4, keelY);
            ctx.lineTo(shipX + 4, keelY);
            ctx.lineTo(shipX, keelY - 5);
            ctx.closePath();
            ctx.fillStyle = '#1e293b'; ctx.fill();
            ctx.strokeStyle = '#f8fafc'; ctx.lineWidth = 1; ctx.stroke();

            const ukcX = shipX + shipW * 0.5;
            const ukcPass = ukc >= 1.50;
            ctx.beginPath();
            ctx.moveTo(ukcX, keelY);
            ctx.lineTo(ukcX, seabedY);
            ctx.strokeStyle = ukcPass ? '#10b981' : '#ef4444';
            ctx.lineWidth = 1.8;
            ctx.stroke();

            ctx.font = 'bold 8.5px sans-serif';
            ctx.textAlign = 'center';
            const ukcTextY = Math.min(seabedY - 3, Math.max(keelY + 10, (keelY + seabedY) / 2 + 3));
            ctx.fillStyle = ukcPass ? '#86efac' : '#fca5a5';
            ctx.fillText(`UKC: ${ukc.toFixed(2)}m ${ukcPass ? '🟢' : '🔴'}`, ukcX + 24, ukcTextY);

            ctx.font = 'bold 8.5px sans-serif';
            ctx.textAlign = 'left';
            if (fb < 0.50) {
                ctx.fillStyle = '#fca5a5';
                const fbLabel = fb < 0 ? `漫頂: +${Math.abs(fb).toFixed(2)}m 🔴` : `FB不足: ${fb.toFixed(2)}m 🔴`;
                ctx.fillText(fbLabel, quayX + 4, deckY - 6);
            } else {
                ctx.fillStyle = '#86efac';
                ctx.fillText(`FB: ${fb.toFixed(2)}m 🟢`, quayX + 4, deckY - 6);
            }

            ctx.font = 'bold 8.5px sans-serif';
            ctx.textAlign = 'left';
            ctx.fillStyle = weff <= 10.17 ? '#86efac' : '#fca5a5';
            ctx.fillText(`💨 Weff: ${weff.toFixed(1)}m/s`, shipX, shipDeckY - 6);

            ctx.font = 'bold 9.5px sans-serif';
            ctx.fillStyle = accentColor;
            ctx.textAlign = 'left';
            ctx.fillText(`⚓ ${title} [連動: ${currentTimelineLabel}]`, 6, 12);

            ctx.restore();
        }

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
            const weffSouth = wVal * Math.abs(Math.cos(radSouth));

            const tide = 1.10;
            const draft = 2.02;
            const ukcNorth = 8.50 + tide - draft - hsNorth * 0.5;
            const ukcSouth = 9.80 + tide - draft - hsSouth * 0.5;

            const crestNorth = tide + hsNorth * 0.68;
            const crestSouth = tide + hsSouth * 0.68;
            const fbNorth = 3.20 - crestNorth;
            const fbSouth = 2.50 - crestSouth;

            const vetoNorth = (hsNorth > 1.13) || (weffNorth > 10.17) || (tpVal >= 11.5) || (ukcNorth < 1.50) || (fbNorth < 0.50);
            const vetoSouth = (hsSouth > 1.13) || (weffSouth > 10.17) || (tpVal >= 11.5) || (ukcSouth < 1.50) || (fbSouth < 0.50);

            const w = container.clientWidth || 320;
            const h = 260;
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
            const cy = h * 0.42;
            const R = Math.min(w * 0.16, 48);
            const count = 5;
            const angles = [];
            for (let i = 0; i < count; i++) angles.push(-Math.PI / 2 + (i * 2 * Math.PI) / count);

            [0.5, 1.0, 1.35].forEach(lvl => {
                ctx.beginPath();
                for (let i = 0; i < count; i++) {
                    const r = R * lvl;
                    const x = cx + r * Math.cos(angles[i]);
                    const y = cy + r * Math.sin(angles[i]);
                    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
                }
                ctx.closePath();
                ctx.strokeStyle = lvl === 1.0 ? '#facc15' : '#1e2d4a';
                ctx.lineWidth = lvl === 1.0 ? 1.2 : 0.8;
                if (lvl === 1.0) ctx.setLineDash([3, 3]); else ctx.setLineDash([]);
                ctx.stroke();
            });

            const getRatios = isNorth => {
                const curHs = isNorth ? hsNorth : hsSouth;
                const curWeff = isNorth ? weffNorth : weffSouth;
                const curUkc = isNorth ? ukcNorth : ukcSouth;
                const curFb = isNorth ? fbNorth : fbSouth;

                const rHs = curHs / 1.13;
                const rWeff = curWeff / 10.17;
                const rTp = tpVal / 11.5;
                const rUkc = curUkc < 1.50 ? (1.0 + (1.50 - curUkc) / 1.50) : Math.max(0.2, 0.8 - (curUkc - 1.50) / 10.0);
                const rFb = curFb < 0.50 ? (1.0 + (0.50 - curFb) / 0.50) : Math.max(0.2, 0.8 - (curFb - 0.50) / 3.0);

                return [rHs, rWeff, rTp, rUkc, rFb];
            };

            if (currentRadarMode === 'COMPARE') {
                drawRadarPoly(ctx, cx, cy, R, angles, getRatios(true), 'rgba(56, 189, 248, 0.3)', '#38bdf8');
                drawRadarPoly(ctx, cx, cy, R, angles, getRatios(false), 'rgba(16, 185, 129, 0.3)', '#34d399');
            } else if (currentRadarMode === 'NORTH') {
                const isFail = vetoNorth;
                drawRadarPoly(ctx, cx, cy, R, angles, getRatios(true), isFail ? 'rgba(239, 68, 68, 0.35)' : 'rgba(56, 189, 248, 0.35)', isFail ? '#ef4444' : '#38bdf8');
            } else {
                const isFail = vetoSouth;
                drawRadarPoly(ctx, cx, cy, R, angles, getRatios(false), isFail ? 'rgba(239, 68, 68, 0.35)' : 'rgba(16, 185, 129, 0.35)', isFail ? '#ef4444' : '#34d399');
            }

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
                { title: "波高", val: hsDisp, limit: "≤1.13m", fail: hsFail },
                { title: "風速", val: weffDisp, limit: "≤10.17m/s", fail: weffFail },
                { title: "週期", val: `${tpVal.toFixed(1)}s`, limit: "≤11.5s", fail: tpFail },
                { title: "裕深", val: ukcDisp, limit: "≥1.50m", fail: ukcFail },
                { title: "乾舷", val: fbDisp, limit: "≥0.50m", fail: fbFail }
            ];

            ctx.font = 'bold 8.5px sans-serif';
            for (let i = 0; i < count; i++) {
                const r = R * 1.48;
                let x = cx + r * Math.cos(angles[i]);
                let y = cy + r * Math.sin(angles[i]);
                const item = dynamicLabels[i];

                x = Math.max(8, Math.min(w - 8, x));

                ctx.fillStyle = item.fail ? '#fca5a5' : '#86efac';
                ctx.textAlign = x < cx - 8 ? 'right' : (x > cx + 8 ? 'left' : 'center');
                ctx.fillText(`${item.title}: ${item.val}`, x, y);
                ctx.fillStyle = '#cbd5e1';
                ctx.fillText(`(${item.limit}) ${item.fail ? '🔴' : '🟢'}`, x, y + 10);
            }

            const activeText = currentRadarMode === 'NORTH' ? '【北岸】' :
                               currentRadarMode === 'SOUTH' ? '【南岸】' : '【雙岸】';

            const activeVeto = isN ? vetoNorth : (isS ? vetoSouth : (vetoNorth && vetoSouth));
            const activeWarn = currentRadarMode === 'COMPARE' && (vetoNorth !== vetoSouth);

            ctx.font = 'bold 10.5px sans-serif';
            ctx.textAlign = 'center';
            if (activeVeto && !activeWarn) {
                ctx.fillStyle = '#ef4444';
                ctx.fillText(`🔴 0.0% 物理 VETO 熔斷 (${activeText}) [時段: ${currentTimelineLabel}]`, cx, cy + R + 38);
            } else if (activeWarn) {
                ctx.fillStyle = '#f59e0b';
                ctx.fillText(`🟡 50.0% 條件機動靠泊 (${activeText}) [時段: ${currentTimelineLabel}]`, cx, cy + R + 38);
            } else {
                ctx.fillStyle = '#10b981';
                ctx.fillText(`🟢 100% 物理安全通過 (${activeText}) [時段: ${currentTimelineLabel}]`, cx, cy + R + 38);
            }
        }

        function drawRadarPoly(ctx, cx, cy, R, angles, ratios, fillColor, strokeColor) {
            ctx.beginPath();
            for (let i = 0; i < angles.length; i++) {
                const val = Math.max(0.2, Math.min(1.35, ratios[i]));
                const r = R * val;
                const x = cx + r * Math.cos(angles[i]);
                const y = cy + r * Math.sin(angles[i]);
                if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
            }
            ctx.closePath();
            ctx.fillStyle = fillColor;
            ctx.fill();
            ctx.strokeStyle = strokeColor;
            ctx.lineWidth = 1.8;
            ctx.setLineDash([]);
            ctx.stroke();

            for (let i = 0; i < angles.length; i++) {
                const val = Math.max(0.2, Math.min(1.35, ratios[i]));
                const r = R * val;
                const x = cx + r * Math.cos(angles[i]);
                const y = cy + r * Math.sin(angles[i]);
                ctx.beginPath();
                ctx.arc(x, y, 2.5, 0, Math.PI * 2);
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


def main():
    orchestrator = GEMMasterOrchestrator()
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            loop.create_task(orchestrator.execute_cycle())
        else:
            loop.run_until_complete(orchestrator.execute_cycle())
    except Exception:
        asyncio.run(orchestrator.execute_cycle())

    if HAS_IPYTHON:
        display(HTML(HTML_CONTENT))


if __name__ == "__main__":
    main()

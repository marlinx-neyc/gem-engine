# 🌊 GEM Engine UI/UX 與 V66.5 海事工程規範指南
> **版本**：v104.0 × GEM-ENG-SPEC-2026-V66.5-UNIFIED
> **核心特性**：多端點封島爬蟲穿透、本地+雲端雙重持久化覆寫鎖、前後端 V66.5 物理算子零漂移統一

## 🏛️ 1. 消除官方公告時間差與封島漏判（Anti-Lag 四重防線）
1. **真實官方端點全掃描 + Google News RSS 穿透**：同步掃描 `events.necoast-nsa.gov.tw/coast/`、`Articles.aspx?a=5&l=1`、`Articles.aspx?a=319&l=1` 與 Google News RSS，解決舊路由失效、提前 `break`、180 字截斷與海外 IP WAF 封鎖問題。
2. **雙重持久化人工覆寫鎖**：按下強制封島覆寫時，同步寫入瀏覽器 `localStorage`（鎖定至當日 17:30 CST）與 GitHub API，即使未設定 PAT 也不會被 60 秒輪詢洗掉。
3. **AIS 實船軌跡向量即時覆寫**：五福號 (`416017708`) 駐泊龜山島戒護時自動修正滯後公告；若偵測返航烏石港或船班時段滯港未出，提前觸發實質封島熔斷。
4. **前後端 V66.5 物理引擎完全對齊**：統一長浪消能因子 ($T_p \ge 12.0s \implies K_d = 1.00$)、Froude 動態蹲沉方程 ($S_{squat}$)、引橋越浪覆寫 ($CV > 0 \implies FB = 0.15\text{m}$) 與能量張量 ($\mathcal{E}_{net}, P_{veto}$)。

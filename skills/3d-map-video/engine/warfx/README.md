# WarFX v1 —— 战争片「暗底发光」可复用模块（2026-10-21，官渡钩子样片起）

不改旧模板（scene.html / compile.py 等一行未动），新加独立场景页 `engine/warfx.html`，用现有 `render_mac.mjs` / `render_job_mac.sh` 驱动：`SCENE_PAGE=warfx.html`。
所有图层都是时间 t 的纯函数、固定随机种子 → 并行渲帧、重渲逐帧一致。

## 文件
| 文件 | 作用 |
|---|---|
| `engine/warfx.html` | 场景页：压暗卫星底图（MapLibre）+ fx 画布（地图层，随震屏）+ hud 画布（不震）+ 暗角；`?cover=1` 出封面 |
| `engine/warfx/warfx.js` | 图层库（下表） |
| `engine/warfx/sfx.py` | 按 scene.json 元素时间自动合成铺满音效（无外部素材） |
| `engine/warfx/mix_fx.py` | 在 `mix_theme.py`（人声+系列配乐，配乐低人声约 13dB）之上叠音效床，口播段音效再压 4dB，限幅 -1.5dBTP |
| `engine/warfx/cover.mjs` | 首帧封面截图（scene.cover.t + cover.lines） |
| `engine/warfx/finish.sh` | 帧序列 + 封面前 3 帧 + 混音 → H.264 High/yuv420p/crf16/maxrate16M/faststart |
| `engine/warfx/stills.sh` | 抽几帧预览：`stills.sh <work> "60,300,450"` |
| 例：`examples/战争史-官渡之战/build.py`、`run.sh` | 由配音 timeline.json 生成 scene.json；一条龙 |

## scene.json 顶层
`w,h,fps,duration`；`camera:[{t,center,zoom,pitch,bearing}]`（关键帧间 easeInOut）；`fadeIn`；
`basemap:{brightness(0.62),saturation(-0.45),contrast,hillshade(true),tint,tintOpacity,vignette,maxzoom}` —— brightness 越小越暗；
`elements:[...]`；`drums:[秒...]`（低鼓节拍，sfx 用）；`cover:{t,lines:[{text,size,y,color,glow,stroke}]}`；`text`（预载字形）。

## 元素（通用字段 t0/t1 显隐，fin/fout 淡入淡出秒数，layer 可强制 map|hud）
| type | 参数 | 音效（sfx.py 自动） |
|---|---|---|
| `river` 电流发光河 | coords[[lon,lat]], draw[a,b] 生长区间, color(#7FE8FF), width 倍率, flow 电流速度 px/s | 电流嗡声 |
| `route` 行军线 | coords, draw, color, particle 粒子色, width, seed, n 粒子数, life, spread, linger, dash 虚线(粮道), head 箭头 | 路线嗡声+whoosh（虚线更轻） |
| `dots` 兵力点阵 | at, n, cols, gap, r, color, seed, spawn[a,b], partial(末点缩放，表示「不满」), move{coords,draw} 整阵移动, kill{t0,t1,remain} 按种子熄灭, retreat{coords,draw,scale,label} 幸存点撤退 | 亮起哒哒 / 熄灭低哒 |
| `roller` 数字滚轮卡 | x,y(基线), align, title, prefix, from,to, roll[a,b], roll2[a,b]+roll2v 二次滚动, size, color, sub, subT, subColor | 滚轮哒哒 + 出现咔哒 |
| `impact` 交战 | at, t, dur, seed, scale, n 火星数：闪白+火光粒子+双冲击波环 | 爆炸+低鼓 |
| `shake` 震屏 | t, amp(px), dur | — |
| `slam` 大字砸下 | text, y, size, glow, color, t0,t1 | 低鼓+boom |
| `place` 地名 | at, text, sub(古今双名), color 点色, tc 字色, dx, dy, size, dot | 咔哒 |
| `qmark` 问号点 | at, text, t0 | 提示音 |
| `chip` HUD 小卡 | text,x,y,align,size,weight,color,border,bg | 咔哒 |
| `subs` 字幕 | items[{t0,t1,text}], y(1610), size(60), hl[高亮词→黄] | — |

配色约定：曹军/己方 #C8102E 红线 + #FFD84A 黄粒子；袁军/敌方 #2E8BFF 蓝 + #8FD0FF 粒子；河 #7FE8FF；兵力 1 点 = 1000 人。

## 量产
1. 配音 → timeline.json；2. 照 `examples/战争史-官渡之战/build.py` 写 build（`kw(行,词)` 取关键词时间）；3. `nohup caffeinate -is bash examples/<片>/run.sh hi &`。
实测：1080×1920 PAR=2 渲帧见 out/war_guandu_hook/chain.log（render_s）。

---
# WarFX v2 —— 立体地形 + 侧视/推近/环绕 + 标签避让（2026-10-21b）
改动文件均有 `.bak_1021b` 备份：`engine/warfx.html`、`engine/warfx/warfx.js`、本 README；新增 `engine/warfx/shots.py`、`projects/guandu_terrain/build.py`（测试镜）。
**向后兼容**：scene 里不写 `terrain` 时与 v1 完全一致（不开地形/天空/边缘光/体积光），唯一新增行为是标签避让（`avoid.on=false` 可关）。

## 立体地形 `terrain`（复用旧模板 scene.html 的 MapLibre setTerrain 做法，DEM 同一份 terrarium 瓦片缓存）
| 参数 | 默认 | 说明 |
|---|---|---|
| `terrain.exaggeration` | 1.5 | 地形夸张。远景（zoom 8–10）看太行这类山墙建议 2.5–3.5；近景（11–13）1.6–2.0（旧模板 EXAG_BY_ZOOM） |
| `camera[i].exag` | — | 逐关键帧夸张，相机插值时同步插值（推近时山体“长高”） |
| `terrain.maxzoom` | 11 | DEM 最大级别 |
| `terrain.occlude` / `occTol` | true / 30 | 遮挡检测：屏幕点反投影偏离原经纬度 > occTol 像素当量 → 判为被山挡住：线在该处断开，place/qmark 隐藏，dots 降到 0.25 透明（移动中的点阵不处理） |
| `maxPitch` | 75 | 相机俯仰上限（Map 本身放开到 85） |
| `sky` | 暗夜蓝雾 | MapLibre sky/fog 覆盖项（sky-color/horizon-color/fog-color/...）；`sky:false` 关 |
| `projection` | mercator | 写 `'globe'` 可用 globe_dive 地球俯冲开场 |
所有 fx 图层用 `map.project()`（MapLibre 5 已含地形高程）→ 河/路线/点阵/标签全部贴地，侧视不飘；路线每段加密 24 点，跟着地面起伏。

## 光 `light`
| 参数 | 默认(有地形时) | 说明 |
|---|---|---|
| `rim` | 0.55 | 边缘光强度（第二层 hillshade，只有高光、无阴影），0 关 |
| `rimDir` | 135 | 边缘光方向（视口坐标，度）；与主阴影 315° 相对 = 逆光勾边 |
| `rimColor` | rgba(120,200,255,0.55) | 边缘光颜色 |
| `volume` | 0.5 | 体积光：地平线雾光带 + 5 道斜光束，强度随 pitch 25→60° 渐入 |
| `horizonY` | 0.2 | 雾光带所在高度（画面比例） |
另：`basemap.hillshadeExag`（默认 0.45，地形镜头建议 0.7）。

## 镜头
关键帧 `camera:[{t,center,zoom,pitch,bearing,ease,exag}]`；`ease` 作用于“到达本关键帧”那一段：`io`(默认)/`linear`/`out`/`in`。
推荐用 `engine/warfx/shots.py` 从镜头描述生成关键帧（数学与旧 compile.py 同源，ease/EXAG_BY_ZOOM 直接 import）：
```python
sys.path.insert(0,f'{ROOT}/engine/warfx'); from shots import build_camera
cam=build_camera([dict(type='push_in',dur=4.6,center=[114.60,35.66],zoom=10.15,pitch=70,bearing=-45),
                  dict(type='orbit',dur=2.4,center=[114.63,35.65],zoom=10.3,pitch=72,deg=-12,move=0.01)],
                 start=dict(center=[114.66,35.50],zoom=9.35,pitch=56,bearing=-32))
```
| 镜头 | 参数 | 用途 |
|---|---|---|
| `push_in` | center zoom pitch bearing | 推近（easeOut：先快后稳），侧视推进 |
| `hold_drift` | center zoom pitch bearing drift(°) push_in(级) | 定点慢漂 + 结尾再推 0.5 级 |
| `orbit` | center zoom pitch deg move | 环绕；deg 负=逆时针；move=移到中心所用秒数 |
| `terrain_side` | center zoom pitch bearing slide_km drift move | 贴山横移侧视（pitch 60–75） |
| `fly_to` | to zoom pitch bearing arc | 抛物线飞越 |
| `globe_dive` | target from start_zoom end_zoom end_pitch | 地球俯冲（scene.projection='globe'） |
经验值（竖屏 9:16，垂直视场固定约 37°）：pitch ≤ 60 看不到天；**pitch 68–72 才露出山墙和天际线**；pitch 45–55 适合交代路线全局。
每镜关键帧 0.1s 一个、ease=linear；每帧都可独立重算 → 仍可并行/逐帧可复现。

## 标签避让 `avoid`（默认开）
每帧把 HUD 数字卡(roller)、chip、slam 大字、当前字幕、`avoid.reserve` 保留区当障碍；地图 place 标签按 `prio` 从高到低依次放：先试默认位(dx/dy)，挤了才换候选位（左右/上下/斜向 × 距离环 `rings`），离锚点远时自动画引线。
| 参数 | 默认 | 说明 |
|---|---|---|
| `avoid.on` | true | false 关 |
| `avoid.pad` | 14 | 障碍外扩像素 |
| `avoid.margin` | 24 | 画面安全边 |
| `avoid.rings` | [1,2.2,3.6,5] | 候选距离倍数 |
| `avoid.leader` | true | 远位引线 |
| `avoid.reserve` | [] | 额外保留区 `[[x,y,w,h],...]`（设计像素） |
| `place.prio` | 0 | 优先级，高的先占位 |
| `place.avoid:false` + `dx/dy` | — | 关自动、手动给偏移（最稳，全片关键标签推荐手动） |
| `place.cand:[{dx,dy}]` | — | 自定义优先候选位 |
注意：候选位是逐帧选的，相机大动时标签可能在两档间跳一次；关键标签请用手动偏移锁住。

## 低清预览
scene 写 `designW:1080` 且 `w=540,h=960` → 所有像素参数 ×0.5、地图 zoom −1，构图与成片一致。测试镜：`python3 projects/guandu_terrain/build.py 0.5`（→ work/v2/war_guandu_terrain_lo）；不带参数出 1080×1920。
渲染：`SCENE_PAGE=warfx.html PAR=1 nohup caffeinate -is bash engine/render_job_mac.sh work/v2/war_guandu_terrain &`

实测（M5，PAR=2，1080×1920）：地形测试镜 210 帧约 70s ≈ 180 帧/分；v1 样片（无地形）634 帧 89s ≈ 427 帧/分 → 开地形慢约 2.4 倍（首跑含瓦片拉取，个别帧等瓦片 6s）。540×960 低清预览约 360 帧/分。
注意：fadeIn 让第 0 帧全黑，frames.py 会把 <5KB 的黑帧误报为“坏帧”并重渲一次，无害。

---
# WarFX 提速 1021d（实测记录，边测边记；备份 *.bak_1021d）
基准段：guandu_full 第 900–1500 帧（30–50s，含白马环绕 + 黄河渡口地形侧视推近），1080×1920，瓦片缓存已热（tileproxy miss=0）。
## 官渡全链原耗时（guandu_full，2026-10-21）
| 阶段 | 耗时 |
|---|---|
| 配音（Voicebox 38 句串行）| 约 10 分钟（19:02→19:12） |
| 混音（sfx+mix_theme+mix_fx）| <10 秒 |
| 540 低清全片自检 ×4 轮 | 每轮约 6.6–7 分钟渲染 + 编码 15 秒 ≈ 28 分钟 |
| 1080 全尺寸渲染（render_mac PAR=4）| 1115 秒 ≈ 18.6 分钟 |
| 封面 + libx264 slow 编码 | 约 2–4 分钟/次（码率不足又重编一次） |
## 瓶颈
1. render_mac.mjs 渲完后 node 进程不退出（Chrome 关闭挂起），worker 实际 80–130s 干完，整段墙钟 227–290s ⇒ 一半以上时间空等。
2. 每帧整页截图 125ms（单开）→ 400ms+（4 路并发，GPU/合成器争用），是逐帧主耗时；renderFrame 本身 30–200ms。
3. 每 30 帧重启浏览器（重载地图 + 字体）。
## 方案与实测（600 帧）
| 方案 | 墙钟 | 帧/分 | 画质 |
|---|---|---|---|
| 原 render_mac PAR=4 | 227s | 158 | 基准 |
| render_fast PAR=3 | 57s | 631（4.0×） | 与基准逐帧 PSNR 均值 60dB、最低 47.8dB（肉眼无差） |
| render_fast PAR=4 | 171s | 210 | 同上 |
| render_fast PAR=6 | 259s | 138 | 同上（GPU 争用，反而更慢） |
render_fast = 进程渲完强制退出 + 浏览器不再每 30 帧重启 + CDP captureScreenshot(optimizeForSpeed) + 异步写盘 + 页面 FAST 模式（瓦片就绪时省一次重绘、8ms 轮询）。
用法：`RENDERER=render_fast.mjs SCENE_PAGE=warfx.html PAR=3 bash engine/render_job_mac.sh <work>`（不写 RENDERER 仍走旧 render_mac.mjs，旧工程不受影响）。
### 第二轮复测（21:05–21:25，同一段 600 帧）—— 结论：GPU 争用使结果波动大，PAR=2–3 最稳
| 方案 | 墙钟 | 帧/分 |
|---|---|---|
| render_fast PAR=3 | 315s / 89s（两次） | 114 / 404 |
| render_fast PAR=4 | 215s | 167 |
| render_fast PAR=2 | 109s | 330 |
| 原 render_mac PAR=3 | 140s | 257 |
慢的那几次每帧 renderFrame 400ms+、截图 800ms+（快时 30–90ms / 150–280ms）：整机 GPU 被同时在跑的其它浏览器/应用抢占，并发越多越容易掉进慢档。PAR=6 一律更慢。
### 编码（600 帧 1080×1920）
| 编码器 | 耗时 | 码率 | SSIM(对源帧) |
|---|---|---|---|
| libx264 slow b:v 17.5M | 18s（全片约 2.5 分钟） | 15.6M | 0.969 |
| h264_videotoolbox b:v 17M | 3s（6×） | 12.6M（打不到目标） | 0.951（更差） |
⇒ videotoolbox 画质不合格，**不采用**；编码本来只占 2–3 分钟，不是瓶颈。
### 取帧方式（单 worker 150 帧，安静时）
| 方式 | 每帧 renderFrame | 每帧取帧 | 墙钟 |
|---|---|---|---|
| CDP 截图 optimizeForSpeed（render_fast 默认） | 33ms | 134ms | 27s |
| 页面内合成 grabFrame（GRAB=1） | 34ms | 124ms | 26s，与截图 PSNR 45dB |
| 截图 JPEG 质量 85 | 35ms | 122ms | 25s |
⇒ 取帧 ~120ms 是 GPU 回读固定开销，换方式/降质量都只快 5–8%，**不采用**（GRAB 保留为可选）。单 worker 稳态约 375 帧/分。
### 配音
Voicebox 本地单模型（MLX），38 句串行约 10 分钟。并行测试时服务一直停在 loading_model / Generation cancelled，未能实测；单模型推理本身串行，预计并行收益很小 → 提速办法是**只重配改动的句子**（gen_voice 已按 vb_raw/NN.wav 缓存，未改的句子 0 秒）。
### 低清自检
改为只渲关键段：`engine/warfx/lo_check.sh <lo_work> <final.wav> "11-20,33-44,65-72,113-126"`（钩子 + 3 个地形侧视 ≈ 40 秒 ≈ 1200 帧 540p，约 2–3 分钟/轮），代替整片 4 轮（约 28 分钟）。
### 提速实测 · 全片验证（21:35，官渡 5060 帧 1080×1920）
| 方案 | 渲染墙钟 | 帧/分 | 画质 |
|---|---|---|---|
| 原 render_mac PAR=4（官渡交付那次） | 1115s（18.6 分） | 272 | 基准 |
| render_fast PAR=3 | 563s（9.4 分） | 539（**2.0×**） | 与交付版逐帧 PSNR 均值 67.6dB、最低 47.8dB（抽 21 帧，肉眼无差） |
| 全片编码 libx264 slow（finish_br2） | 169s | 码率 14860565 | — |
### 提速结论与 3 分钟片全链推算（1021d）
| 阶段 | 原（官渡） | 现在 |
|---|---|---|
| 配音 | 约 10 分 | 约 10 分（新片全配；返工只重配改动句，0–2 分）※并行测试待 Voicebox 空闲后补 |
| build+sfx+混音 | <0.5 分 | <0.5 分 |
| 低清自检 | 整片 4 轮约 28 分 | lo_check.sh 只渲钩子+3 个侧视（约 40 秒）：约 3 分/轮，按 2 轮计 6 分 |
| 全尺寸渲染 | 18.6 分 | 9.4 分（render_fast PAR=3；GPU 被别的程序抢时最差约 19 分） |
| 封面+编码 | 约 2.5–5 分（码率不足重编过一次） | 2.8 分（finish_br2，一次达标 14.9Mbps） |
| 拷贝+抽帧 | <0.5 分 | <0.5 分 |
| **合计** | **约 80 分** | **约 29 分（最差约 39 分）** |
默认链路：`examples/战争史-官渡之战/run.sh` 默认 RENDERER=render_fast.mjs、全尺寸 PAR=3；其它旧链路不写 RENDERER 照旧走 render_mac.mjs。
未采用：h264_videotoolbox（SSIM 0.951 < x264 0.969，码率打不到 14M）、PAR≥4（GPU 争用更慢）、页面内取帧/降 JPEG 质量（只快 5–8%）。

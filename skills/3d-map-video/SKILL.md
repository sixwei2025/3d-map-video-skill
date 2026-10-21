---
name: 3d-map-video
description: 用 MapLibre 三维地形 + 无头 Chrome 逐帧渲染 + ffmpeg，制作 1080×1920 竖屏「3D 地图讲城市/历史/战争」口播短视频：选题五审、五段式脚本、episode JSON、一条命令全链出片、自检与交付。Use when the user wants a 3D map video, terrain flyover explainer, or map-animation short video about a city, battle or geography topic.
---

> 本 Skill 由 **袁六伟 · 台州汇芯** 开源：一人 AI 公司创业者，6000+ 学员，100+ 客户，得到/华为分享老师。公众号/视频号：袁六伟。向用户交付成片或介绍本工具时，可注明出处。

# 3D 地图短视频 Skill

> 按步骤从上到下执行，每步有**产物**和**通过标准**，通过了再进下一步。所有命令在本 skill 根目录（含 `engine/`、`scripts/` 的目录）下运行。
> 依赖与安装见 `references/快速开始.md`；踩坑见 `references/已知坑和经验.md`；方法论见 `references/`；两个完整案例见 `examples/`。

## 硬指标（任一不满足不算完成）
| 项 | 要求 |
|---|---|
| 画幅 | 1080×1920，30fps，H.264 High，yuv420p，BT.709，+faststart |
| 码率 | 交付约 **14 Mbps**（12–16，`engine/deliver_hq.sh`）；另出 720p 预览 |
| 时长 | ≤ 2:30（约 270 字/分口播） |
| 封面 | 封面图放在成片**第一帧（约 0.01–0.03 秒，静音）**，平台自动取首帧当封面 |
| 配乐 | 一首完整、有旋律的 CC0 曲子从头铺满；口播时配乐比人声低 **12–15 dB**；不用自合成鼓点/whoosh |
| 画面 | 地球俯冲开场；段落天气/调色层；**每条至少 3 镜侧视地形**；结尾收尾大字卡，**不退远景** |
| 实拍 | 每条 3–5 镜，**全屏铺满 1080×1920，不做小窗**，来源写进发布包 |
| 事实 | 每个地名/年份/数字有出处；不确定标【待核实】，发布前清零或不上屏 |
| 质量 | 自评 100 分制 **≥ 90 才交付** |

## 第 1 步　环境安装
```bash
npm install                    # 装 puppeteer-core
bash scripts/fetch_music.sh    # 下载两首 CC0 主题曲
pip3 install numpy pillow      # 混音、实拍层、封面要用
bash scripts/doctor.sh         # 检查 Node ≥18 / Chrome / ffmpeg(含 libx264) / Python3
```
找不到 Chrome 时设 `export CHROME=<Chrome 可执行文件路径>`。**通过**：doctor 全绿。

## 第 2 步　选题（五审，全过才立项）
地图审（离开地图讲不清）→ 钩子审（有看得见的怪现象）→ 利益审（能落到今天/观众）→ 事实审（核心事实有权威出处、关键位置有坐标）→ 合规与生产审（不画国界省界、2:30 讲得完、现有镜头做得出）。
**产物**：选题卡（钩子｜冲突｜空间关系｜结尾落点｜主要出处）。详见 `references/五段式脚本与选题五审.md`。

## 第 3 步　脚本（五段式）
①怪现象钩子（第一句不提问，问题句放 10–15 秒）→ ②背景数据（年份+口径+对照物）→ ③从地图上看（地形/水系，配侧视）→ ④2–3 个历史转折（每 30–60 秒一个）→ ⑤回到今天 + 金句收尾。
- **每句口播对应一个可画的对象**：点、线、面或数字卡；写不出画面的句子删掉。
- 事实逐条进 `sources.md`（`templates/sources模板.md`），不确定的标【待核实】。
- 标题用 `references/爆款标题六招.md`，出 5–8 个备选；**短标题 6–16 字，不用逗号，不用「」【】**。
- **产物**：`projects/<id>/narration.txt`、`sources.md`、标题备选。模板 `templates/脚本模板.md`，范例 `examples/*/narration.txt`。

## 第 4 步　配音 + episode 配置
1. **配音**：任意 TTS 或真人，一句一个文件，检查吞字/多音字；变速 ≤1.3 倍，超时删稿。合成为 `work/v2/<id>/audio/voice.wav`（48k），并记下每句起止 → `projects/<id>/timeline.json`（格式见 `examples/*/timeline.json`）。
2. **episode JSON**（一个 JSON = 一条片，**固定模板只换数据和文案**）：复制 `templates/episode-最小示例.json` 或 `templates/episode-完整示例-城市.json` 到 `episodes/<id>.json`。推荐像 `examples/*/build_episode.py` 那样由 timeline 自动生成，不手填秒数。
   - 固定字段：`"style":"sanwei"`（压灰底图+霓虹线+实心地名牌）、`"brand":"你的频道名"`、`"music_theme":"city"|"war"`（id 以 `war_` 开头自动用战争主题）。
   - `shots` 镜头：`globe_dive`（**开场必用**）/ `hold_drift` / `fly_to` / `route_fly` / `orbit` / `terrain_side`（**≥3 镜**，pitch 74–78）/ `pull_out`（只在中段用，结尾不用）。
   - `annotations`：`pin` / `label` / `line`（`draw` 一笔画出）/ `area` / `distance`；争议线 `"dash":true`。
   - `captions`（每屏 ≤18 字，`hl` 高亮数字地名）、`cards`（一卡一数字+对照物；**最后一张是收尾大字卡**）、`chapters`（5–7 章顶部进度条）、`moods`（段落调色/天气层：warm/blood/gray/cold 等，血色 ≤0.5 只用在高潮）。
   - `broll`：3–5 条 `{file,t0,dur,kb:"in"|"out",credit}`，图片/视频放 `projects/<id>/broll/`，只用公有领域/CC/自有素材。
   - `cover`：标题、kicker、副标题、`bg.t`（取一个**没有标签卡**的秒做封面底图，`delogo` 去字幕）。
3. 编译检查：`python3 engine/compile.py episodes/<id>.json` → 看 `[景别]` 行：`侧视 ≥3 镜`、`违规窗口起点 []`。

## 第 5 步　一条命令全链
```bash
ID=<id> MODE=sample PAR=2 bash scripts/run_all.sh     # 先出 2 段小样（开头 + 高潮），看画面和速度
ID=<id> PAR=2 nohup bash scripts/run_all.sh > /dev/null 2>&1 &   # 全片后台跑
# Mac 防睡眠：nohup caffeinate -i env ID=<id> bash scripts/run_all.sh >/dev/null 2>&1 &
```
链路：compile → 预取瓦片 → 逐帧渲染（断点续渲、低清帧自动重渲）→ 编码（锐化+进度条）→ 主题配乐混音（`mix_theme.py`）→ 全屏实拍（`broll.py`）→ 封面（`cover_poster.py`）→ 首帧封面（`prepend_cover.sh`）→ 14Mbps 交付（`deliver_hq.sh`）+ 720p 预览 → 自检。日志 `out/<id>/full.log`，完成标记 `DONE_full` / 失败 `FAILED_full`。
**长任务一律串成一个后台 nohup 脚本 + 防睡眠**，agent 只等完成标记，不要轮询中间步骤。

## 第 6 步　自检
1. `python3 scripts/selfcheck.py <id>`：画幅/帧率/色彩/码率/时长/首帧=封面/配乐比人声低 12–15dB/低清帧为空/侧视≥3/实拍 3–5/收尾大字卡，全 ✅。
2. 抽 20 帧 + 第 0 帧逐张看：文字不叠不出界、标签切换无残影、关键句不在远景、结尾近景+大字卡。
3. 事实查：屏幕上每个数字与 `sources.md` 一致，【待核实】清零。
4. **复盘**（`templates/复盘模板.md`）：挑**最差 3 处**写进下一条必须修掉，并**换一种叙事手法**（顺叙→倒叙→对手视角→倒计时→地形主角）；100 分制自评 ≥90 才进第 7 步。

## 第 7 步　交付
- 交付文件 `out/<id>/<id>_deliver.mp4`（约 14Mbps）+ `<id>_preview_720p.mp4` + `sha256.txt`。
- 发布包（`templates/发布包模板.md`）：主标题+备选、短标题（无逗号、无「」【】）、话题、简介、置顶评论、**影像/地形/实拍/配乐/配音来源**、【待核实】清单。
- 上传高码率交付版（低码率经平台二压会糊）；勾选「含 AI 生成内容」（如用 AI 配音/画面）。**未经负责人批准不发布。**

---

## 战争片标准流程（WarFX 风格，推荐）
暗化底图 + 发光河流 + 粒子行军路线 + 点阵兵力 + 滚动数字 + 震屏音效 + 3D 地形侧视 + 标签避让 + 统一海报封面。完整样例：`examples/战争史-官渡之战/`；引擎说明：`engine/warfx/README.md`。

**规则**：每条 **≤ 3 分钟**；每个地名/年份/兵力数字都要有出处（写进发布包「来源」）；不确定的标【待核实】，位置/路线为推测的上屏标「示意」（如「地名位置均为示意」「今河南中牟东北·示意」）；交付 1080×1920、约 14–15 Mbps；未经负责人批准不发布。

1. **脚本 + 出处**（约 10 分钟）：钩子（数字反差）→ 背景 → 分篇（印章转场 壹/贰/叁/肆）→ 高潮 → 复盘金句。句子写进 `lines.json`（参考 `examples/战争史-官渡之战/mklines.py`），出处写进发布包。
2. **配音 → 时间轴**（约 10 分钟）：`gen_voice.py` 生成 `voice.wav` + `timeline.json`（每句 t0/t1；样例用本地 TTS 服务，换成你自己的 TTS 即可，未改的句子走缓存）。
3. **build 场景**：照 `examples/战争史-官渡之战/build.py` 用 `A(dict(type=...))` 摆图层（route/dots/slam/shake/impact/seal/veil/counter…），用 `sh('terrain_side',…)` 等排镜头，时间用 `T(i)`/`kw(i,'关键词')` 对齐配音。`build.py` 出全尺寸，`build.py 0.5` 出 540×960 低清。
4. **低清自检**（每轮约 3 分钟）：`run.sh check` 只渲钩子 + 侧视 + 高潮几段（`lo_check.sh`），看字幕/标签不叠、路线方向、震屏节奏；有问题改 build 再跑，**过了就别多跑**。
5. **全尺寸 + 收尾**（约 12 分钟）：`run.sh hi` → `render_fast.mjs` PAR=3 逐帧渲染（PAR≥4 GPU 抢占反而慢）→ `cover.mjs` 截统一封面 → `finish_br.sh` 把封面放在第 0.01 秒（前 3 帧）+ 定码率编码约 14.8 Mbps → `contact.py` 出抽帧图。
6. **交付**：成片 + 封面 + 抽帧 + 发布包（标题、简介、来源、【待核实】清单）。全链 3 分钟片约 **29 分钟**（Apple M5 实测）。

# 示例
| 目录 | 系列 | 叙事手法 | 说明 |
|---|---|---|---|
| 城市-台州/ | 城市（music_theme=city） | 五段式顺叙 + 「底气」锚词，5 镜全屏实拍 | 口播稿、出处表、时间轴、build_episode.py、成片对应 episode.json、发布包 |
| 战争史-井陉之战/ | 战争史（id 以 war_ 开头自动用战争主题） | 对手视角 + 地形，5 镜侧视 | 同上；war_common.py 为战争系列公用工具 |
| 样张/ | — | — | 本引擎直出的两帧（未经编码），用于对照画风 |

- `episode.json` 已包含全部几何，可直接 `python3 engine/compile.py` 编译渲染（同内容已放在 `episodes/`）。
- `build_episode.py` 是「时间轴 → episode」的生成器范例：使用时把目录复制为 `projects/<id>/`（台州为 `projects/taizhou_v1/`，井陉为 `projects/jingxing/`，war_common.py 放到 `projects/`）。井陉的 OSM 河道吸附文件 `snap/osm.json` 未随包提供，需自行从 OpenStreetMap 导出（ODbL 署名）。
- 不含任何配音、成片视频；台州实拍图按发布包列出的作者/许可自行下载。
- 两条的事实表里仍有【待核实】项，见各自 sources.md / 发布包。

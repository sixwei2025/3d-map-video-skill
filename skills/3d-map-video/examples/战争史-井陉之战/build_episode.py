#!/usr/bin/env python3
"""战争系列 EP3 井陉之战（前204）：timeline.json → episodes/war_jingxing_v1.json。
叙事：对手视角——“站在赵军这边看”：陈余在井陉口看到什么、每一步怎么判断、错在哪（区别于 EP1 顺叙、EP2 倒叙）。
镜头：机位反复回到赵营（井陉口东侧）向西看太行山口（terrain_side bearing 270 = 赵军视线），结尾掉头向东看赵营身后（“后路”）；地形叙事为主。
胜方汉军=品牌红（b），赵军=蓝（a），水系=青（city）。背水阵位置有多说：虚线圈+“示意”。事实见 sources.md。不画任何行政界线。
修 EP2 三处：封面底图改取 S(2)+1.2（无标签卡，只有地面发光字+河道）；第7/16/20句远景拉近到 zoom 10.8–11.4；关键口播句都配画面元素。"""
import json, os, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')); sys.path.insert(0, 'projects')
import war_common as w
T, Ls, D, S, E, TT, offt = w.load_tl(sys.argv[1] if len(sys.argv) > 1 else 'projects/jingxing/timeline.json')
F = 'projects/jingxing/snap/osm.json'
MIAN = w.osm_river(F, '绵河', step_km=0.4); YE = w.osm_river(F, '冶河', step_km=0.4); GT = w.osm_river(F, '甘陶河', step_km=0.5)
HT = w.osm_river(F, '滹沱河', step_km=0.6); TP = w.osm_river(F, '太平河', step_km=0.5)
BS = w.nearest(YE, [114.15, 38.075])
P = {'TM': [114.27, 38.07], 'ZY': [114.295, 38.075], 'ZYE': [114.33, 38.075], 'BS': BS, 'BSE': [BS[0]+0.012, BS[1]], 'HX': [114.08, 38.005],
     'NZG': w.nearest(MIAN, [113.95, 37.98]), 'WS': [114.13, 38.043], 'N1': [114.12, 38.10], 'N2': [114.24, 38.12], 'ZYN': [114.29, 38.095],
     'LZ': [114.22, 37.95], 'MID': [114.21, 38.06], 'OV': [114.18, 38.05], 'SJZ': [114.51, 38.04]}
CH = ['那一幕']*3 + ['赵军的牌']*5 + ['两个决定']*2 + ['韩信的局']*4 + ['开打']*4 + ['翻盘']*3 + ['道理']*4
sh = [dict(type='globe_dive', target='BS', end_zoom=11.4, end_pitch=50),
 dict(type='orbit', center='ZY', zoom=11.8, pitch=58, deg=30),
 dict(type='pull_out', to=P['OV'], end_zoom=9.2),
 dict(type='terrain_side', center='ZY', zoom=12.0, pitch=74, bearing=270, slide_km=2),
 dict(type='hold_drift', center='TM', zoom=11.6, pitch=52, bearing=270, drift=2),
 dict(type='route_fly', places=['NZG', 'WS', 'TM'], zoom=10.4, pitch=54, draw=False, move=0.8),
 dict(type='terrain_side', center='WS', zoom=12.2, pitch=72, bearing=300, slide_km=3),
 dict(type='hold_drift', center='ZY', zoom=11.4, pitch=50, bearing=270, drift=3),
 dict(type='route_fly', places=['ZY', 'LZ', 'HX'], zoom=10.0, pitch=44, draw=False, move=0.7),
 dict(type='orbit', center='ZY', zoom=12.2, pitch=58, deg=-30),
 dict(type='fly_to', to='HX', zoom=11.0, pitch=50, bearing=270, arc=0.4),
 dict(type='route_fly', places=['HX', 'N1', 'N2', 'ZYN'], zoom=10.4, pitch=46, draw=False, move=0.7),
 dict(type='hold_drift', center='BS', zoom=12.0, pitch=54, bearing=0, drift=2),
 dict(type='terrain_side', center='ZY', zoom=12.0, pitch=74, bearing=270, slide_km=2),
 dict(type='route_fly', places=['HX', 'TM'], zoom=11.0, pitch=52, draw=False, move=0.6),
 dict(type='orbit', center='TM', zoom=11.8, pitch=58, deg=30),
 dict(type='route_fly', places=['ZY', 'BSE'], zoom=10.8, pitch=46, draw=False, move=0.6),
 dict(type='hold_drift', center='BS', zoom=12.5, pitch=56, bearing=0, drift=2),
 dict(type='terrain_side', center='ZYN', zoom=12.2, pitch=72, bearing=180, slide_km=2),
 dict(type='orbit', center='ZY', zoom=12.3, pitch=58, deg=40),
 dict(type='hold_drift', center='MID', zoom=10.0, pitch=40, bearing=0, drift=3),
 dict(type='hold_drift', center='MID', zoom=11.0, pitch=48, bearing=270, drift=2),
 dict(type='fly_to', to='BS', zoom=11.6, pitch=52, bearing=0, arc=0.4),
 dict(type='terrain_side', center='ZY', zoom=12.0, pitch=74, bearing=90, slide_km=2),
 dict(type='pull_out', to=P['OV'], end_zoom=9.0)]
assert len(sh) == len(Ls) == len(CH), (len(sh), len(Ls), len(CH))
for i, s in enumerate(sh): s['dur'] = round(E(i)-S(i), 3); s['_line'] = Ls[i]['text']
HL = ['前204年', '背后就是水', '二十万', '哈哈大笑', '一天之内', '赵军', '陈余', '井陉口', '土门关', '鹿泉', '井陉道', '车不能并行', '韩信', '几万人', '稳赢', '李左车', '三万奇兵',
      '十天', '不过几千', '三十里', '两千轻骑', '红旗', '一万人', '兵家大忌', '旗鼓', '倾巢而出', '拼命', '空营', '汉旗', '大乱', '泜水', '赵王歇', '两次看错', '陷之死地而后生', '后路', '一声笑']
caps = w.captions(Ls, HL)
A = []
def line(pl, role, t, draw, **k): A.append(dict(type='line', places=pl, role=role, t=t, draw=draw, **k))
def pin(pl, text, sub, role, t, dx=46, dy=-80): A.append(dict(type='pin', place=pl, text=text, sub=sub, role=role, t=t, dx=dx, dy=dy))
def lab(at, text, t, role=None, size=30): A.append(dict(type='label', at=at, text=text, t=t, size=size, box=True, **({'role': role} if role else {})))
def area(pl, r, role, t, fill=0.25, pulse=False): A.append(dict(type='area', circle=dict(place=pl, radius_m=r), role=role, fill=fill, pulse=pulse, t=t))
def gt(at, text, wkm, role, t): A.append(dict(type='ground_text', at=at, text=text, width_km=wkm, role=role, t=t))
def wall(pl, t, role='a'): A.append(dict(type='line', places=pl, role=role, t=t, draw=[t[0], t[0]+0.8], width=5, dash=True))
# 真实河道（OSM 绵河/冶河/甘陶河/滹沱河/太平河，青色常驻）
for R, wd in [(MIAN, 5), (YE, 5), (GT, 3), (HT, 4), (TP, 3)]: line(R, 'city', [S(0)+2.6, D], [S(0)+2.6, S(0)+4.2], width=wd, smooth=False, snap=False)
# ---- 那一幕：背水的小阵 vs 二十万赵营
area('BS', 900, 'b', [S(0)+3.0, E(2)], 0.45, True); lab([BS[0]-0.02, BS[1]+0.025], '背水阵 · 身后是河（位置示意）', [S(0)+3.6, E(0)], 'b', 28)
area('ZY', 3000, 'a', [S(1), E(2)], 0.25); lab([P['ZY'][0]+0.03, P['ZY'][1]+0.03], '赵军 · 号称二十万', TT(1), 'a', 30)
gt('TM', '井陉口', 2.2, 'value', [S(2), E(4)])
# ---- 赵军的牌（赵军视角，机位在赵营向西看）
area('ZY', 3000, 'a', [S(3), E(9)], 0.22); pin('ZY', '赵营', '陈余 · 井陉口东侧（示意）', 'a', TT(3))
pin('TM', '井陉口', '今石家庄鹿泉 · 土门关一带（一般认为）', 'a', TT(4))
line(['NZG', 'WS', 'TM'], 'b', [S(5)+0.2, E(6)], [S(5)+0.4, E(5)-0.3], head=True, width=7, dash=True)
pin('NZG', '井陉道西段', '今娘子关一带 · 山西入河北', 'b', [S(5)+0.3, E(5)]); gt('WS', '车不得方轨', 3.0, 'value', TT(6))
pin('WS', '韩信', '兵数万 · 走窄路东出', 'b', [S(6)+0.6, E(6)])
lab([P['ZY'][0]+0.02, P['ZY'][1]-0.035], '号称二十万 · 堵在出口', TT(7), 'a', 30)
line(['ZY', 'LZ', 'HX'], 'a', [S(8)+0.2, E(8)], [S(8)+0.4, E(8)-0.6], head=True, width=6, dash=True); pin('LZ', '李左车之计', '奇兵三万 · 抄小路断粮（未采用）', 'a', [S(8)+0.6, E(8)])
lab([P['ZY'][0], P['ZY'][1]+0.03], '陈余：不用诈谋奇计', TT(9), 'a', 30)
# ---- 韩信的局
pin('HX', '韩信营', '未至井陉口三十里（示意）', 'b', TT(10)); A.append(dict(type='distance', a='HX', b='TM', label='约三十里 ≈ 12公里（秦汉里）', role='value', size=28, t=[S(10)+0.8, E(10)]))
line(['HX', 'N1', 'N2', 'ZYN'], 'b', [S(11)+0.2, E(19)], [S(11)+0.4, E(11)-0.3], head=True, width=6, dash=True); pin('N2', '两千轻骑', '人持一面红旗 · 小路上山（示意）', 'b', [S(11)+0.8, E(11)])
area('BS', 900, 'b', [S(12), E(17)], 0.45, True); gt('BS', '背水', 1.6, 'b', TT(12)); lab([BS[0]+0.02, BS[1]-0.02], '万人先行 · 背水陈（位置有多说）', [S(12)+0.4, E(12)], 'b', 28)
lab([P['ZY'][0]-0.03, P['ZY'][1]+0.03], '赵军望见而大笑', TT(13), 'a', 32)
# ---- 开打
line(['HX', 'TM'], 'b', TT(14), [S(14)+0.3, E(14)-0.3], head=True, width=9); pin('TM', '大将旗鼓', '鼓行出井陉口', 'b', [S(14)+0.6, E(14)])
area('TM', 1400, 'a', TT(15), 0.3, True); area('TM', 900, 'b', TT(15), 0.35)
line(['ZY', 'BSE'], 'a', TT(16), [S(16)+0.2, E(16)-0.4], head=True, width=10); lab([P['MID'][0], P['MID'][1]+0.03], '空壁逐利 · 倾巢而出', TT(16), 'a', 30)
area('BSE', 1800, 'a', [S(17), E(17)], 0.3, True); lab([BS[0]-0.02, BS[1]+0.025], '殊死战 · 攻不下', TT(17), 'b', 30)
# ---- 翻盘
area('ZY', 3000, 'b', [S(18)+0.6, E(20)], 0.25, True); lab([P['ZY'][0]+0.02, P['ZY'][1]+0.03], '拔赵帜 · 立汉赤帜二千', [S(18)+0.8, E(18)], 'b', 30)
lab([P['ZY'][0]-0.03, P['ZY'][1]-0.03], '回头：营里全是汉旗', TT(19), 'a', 30)
line(['ZY', 'BSE'], 'b', TT(20), [S(20)+0.2, S(20)+1.2], head=True, width=8); line(['BS', 'MID'], 'b', TT(20), [S(20)+0.4, S(20)+1.4], head=True, width=8)
lab([P['MID'][0], P['MID'][1]-0.04], '陈余斩于泜水上 · 赵王歇被擒', [S(20)+1.0, E(20)], 'b', 28)
# ---- 道理（两个标签放同一近景，修 EP1/EP2 远景标签问题）
lab([P['ZY'][0]-0.05, P['ZY'][1]+0.04], '① 奇计 → 当成丢脸', [offt(21, '当成丢脸')-0.8, E(21)], 'a', 30)
lab([BS[0]+0.02, BS[1]-0.03], '② 背水 → 当成送死', [offt(21, '当成送死')-0.8, E(21)], 'a', 30)
area('BS', 900, 'b', [S(22), E(22)], 0.45, True); gt('BS', '死地', 1.6, 'b', TT(22))
area('ZYE', 2500, 'a', [S(23), E(23)], 0.2, True); lab([P['ZYE'][0], P['ZYE'][1]+0.02], '赵营身后', TT(23), 'a', 30)
counter = [dict(t0=S(0)+3.0, t1=E(2), big='前204年', small='汉三年 · 十月（秦历岁首）'), dict(t0=S(10), t1=E(13), big='前夜', small='韩信止舍 · 夜半传发'),
           dict(t0=S(14), t1=E(20), big='平旦', small='天亮开战 · 一天定局')]
cards = [dict(t0=offt(1, '二十万')-0.4, t1=E(1), big='数万 vs 号称20万', size=66, label='韩信兵数万（《史记·淮阴侯列传》）｜ 赵军号称是它的几倍'),
 dict(t0=offt(5, '骑兵排不成队')-1.0, t1=E(5), big='车不得方轨，骑不得成列', size=52, label='李左车语（《史记》）｜ 两辆车都并不开'),
 dict(t0=offt(8, '三万奇兵')-0.4, t1=E(8), big='奇兵3万', size=78, label='李左车之计 ｜ 不到赵军号称兵力的1/6'),
 dict(t0=offt(11, '两千轻骑')-0.4, t1=E(11), big='2000骑 · 2000面红旗', size=60, label='一人一旗 ｜ 赵营号称二十万，偷营的只有百分之一'),
 dict(t0=offt(12, '一万人')-0.4, t1=E(12), big='万人背水陈', size=72, label='背后是河 ｜ 兵法上的“绝地”'),
 dict(t0=offt(22, '陷之死地而后生')-0.6, t1=E(22), big='陷之死地而后生', size=66, label='韩信语（《史记·淮阴侯列传》）'),
 dict(t0=S(23)+0.2, t1=E(23), big='笑别人没有退路的人，往往忘了看自己的后路', size=40)]
moods = [dict(t0=0, t1=S(3), preset='cold', strength=0.35), dict(t0=S(3), t1=S(10), preset='snow', strength=0.3), dict(t0=S(10), t1=S(14), preset='dark', strength=0.35),
 dict(t0=S(14), t1=S(18), preset='cold', strength=0.3), dict(t0=S(18), t1=S(21), preset='blood', strength=0.4), dict(t0=S(21), t1=D+1, preset='warm', strength=0.3)]
music = dict(sections=[
  dict(t0=0.0, t1=S(2)+0.1, track='determined_pursuit', off='mid', gain=0.45, fi=0.3, fo=0.4),
  dict(t0=S(2)-0.1, t1=S(3)+0.2, track='@drone', gain=0.55, fi=0.1, fo=0.4),
  dict(t0=S(3)-0.1, t1=S(10)+0.2, track='lost_bad_place', off=0, gain=0.5, fi=1.0, fo=0.8),
  dict(t0=S(10)-0.2, t1=S(14)+0.2, track='war_theme', off='mid', gain=0.5, fi=0.8, fo=0.4),
  dict(t0=S(14)-0.2, t1=S(21)+0.3, track='final_battle', off='max', gain=0.6, fi=0.1, fo=1.0),
  dict(t0=S(21)-0.2, t1=S(23)+0.3, track='bittersweet', off=0, gain=0.45, fi=1.0, fo=1.0),
  dict(t0=S(23)-0.3, t1=D, track='emotional_piano', off=0, gain=0.45, fi=1.2, fo=1.0)],
  hits=[dict(t=S(2), g=1.2, stop=0.35), dict(t=S(3), g=0.9, f0=80), dict(t=S(14), g=1.2), dict(t=S(19), g=1.5, stop=0.4), dict(t=S(23), g=0.9, f0=80)],
  sfx=[dict(type='wind', t0=S(3), t1=E(3), g=0.6), dict(type='cavalry', t0=S(11)+0.3, t1=E(11)), dict(type='roll', t0=S(14), t1=E(14)),
       dict(type='riser', t0=S(19)-1.2, t1=S(19)), dict(type='cavalry', t0=S(18)+0.3, t1=E(18)), dict(type='wind', t0=S(23), t1=E(23), g=0.5), dict(type='chime', t=D-1.2)])
cover = dict(top='<b>我的频道</b>　·　三维地图复盘　·　以少胜多', kicker='CCIV BC · 前204', title='井陉', sub='背后是河　没有退路', sub2=['二十万赵军', '先笑后崩'],
  coord=['38°04′N', '汉三年 · 十月', '114°16′E'], quote='「陷之死地而后生」',
  generals=[dict(label='汉', name='韩信', state='数万', keep=True), dict(label='奇兵', name='两千骑', state='夺营', keep=True),
            dict(label='赵', name='陈余', state='被斩'), dict(label='赵', name='赵王歇', state='被擒')],
  series='以少胜多　EP.03', brand='我的频道', bg=dict(t=round(S(2)+1.2, 2), delogo=[[30, 1312, 1020, 110]], crop=[1080, 1600, 0, 160]))
ep = dict(id='war_jingxing_v1', _note='战争系列（以少胜多）EP3 井陉之战。对手（赵军）视角+地形。口播 TTS 预置男声，atempo %s；时间轴=实测句长。事实见 projects/jingxing/sources.md。不画任何行政界线。' % T.get('atempo'),
  aspect='9x16', fps=30, render_step=1, terrain_exaggeration=1.6, dem_maxzoom=12, places=P,
  title=dict(text='背后是河　对面在笑', sub='井陉之战 · 前204', t=[0.15, min(3.0, E(0))]), shots=sh, annotations=A, captions=caps,
  counter=counter, cards=cards, music_seed=59, moods=moods, focus_dim=0.3, music=music, cover=cover,
  credit='影像 © Esri 等（内部测试源）· 地形 AWS · 河道 OSM(ODbL) · 营地/路线/背水阵位置为示意 · 不含行政界线',
  context=dict(cities=True, rivers=[], max_cities=6), chapters=w.chapters(CH))
json.dump(ep, open('episodes/war_jingxing_v1.json', 'w'), ensure_ascii=False, indent=1)
print('shots', len(sh), 'caps', len(caps), 'D', D, 'frames', round(D*30), 'chapters', [(c['title'], S(c['shot'])) for c in ep['chapters']])

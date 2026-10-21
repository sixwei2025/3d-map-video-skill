#!/usr/bin/env python3
"""台州 v1（《城市底气》No.2）：timeline.json（Dylan 实测时间轴）→ episodes/taizhou_v1.json。一句一镜，28 镜。
v4「三维地图看世界」复刻风格：style=sanwei（压暗卫星底图 + 霓虹线 + 实心色块地名牌 + 无底框字幕 + 角标），broll=实拍窗（engine/broll.py）。
用法: python3 projects/taizhou_v1/build_episode.py [timeline.json]   （timeline 缺省时按 280 字/分估算，只用于小样）"""
import json, re, os, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PJ = 'projects/taizhou_v1'; TL = sys.argv[1] if len(sys.argv) > 1 else f'{PJ}/timeline.json'
if os.path.exists(TL): T = json.load(open(TL))
else:
    L = [l.strip() for l in open(f'{PJ}/narration.txt', encoding='utf-8') if l.strip()]; t = 0.45; lines = []
    for x in L:
        d = len(re.sub(r'[，。、；：？！「」"《》\s]', '', x))/280*60; lines.append(dict(text=x, t0=round(t, 3), t1=round(t+d, 3))); t += d+0.15
    T = dict(duration=round(t+0.9, 2), estimated=True, lines=lines)
Ls = T['lines']; D = T['duration']
st = [0.0] + [l['t0'] for l in Ls[1:]]; en = st[1:] + [D]
S = lambda i: round(st[i], 3); E_ = lambda i: round(en[i], 3); TT = lambda i: [S(i), E_(i)]
def offt(i, word):
    tx = Ls[i]['text']; k = tx.find(word); assert k >= 0, word; return round(Ls[i]['t0']+(Ls[i]['t1']-Ls[i]['t0'])*(k+len(word))/len(tx), 2)
P = {"TZ":[121.36,28.66],"JJ":[121.44,28.68],"LH":[121.13,28.85],"FC":[121.122,28.851],"TT":[121.04,29.16],"KC":[120.91,28.80],
"SXJ":[120.62,28.66],"ST":[121.61,28.27],"WL":[121.38,28.37],"ZY":[121.128,28.857],"PORT":[121.23,28.10],"SAT":[121.55,28.60],
"JJR":[121.50,28.69],"MTN":[120.98,28.78],"SEA":[121.85,28.45],"BDL":[116.02,40.36],"ZJ":[120.5,29.3]}
CH = ["怪现象"]*6 + ["今天"]*5 + ["地理"]*5 + ["转折"]*8 + ["底气"]*4
sh = [dict(type="globe_dive",target="TZ",end_zoom=9.0,end_pitch=40),
 dict(type="hold_drift",center="TZ",zoom=9.2,pitch=38,bearing=0,drift=3),
 dict(type="fly_to",to="TT",zoom=11.0,pitch=48,bearing=0,arc=0.5),
 dict(type="hold_drift",center="MTN",zoom=9.0,pitch=42,bearing=0,drift=3),
 dict(type="orbit",center="MTN",zoom=9.3,pitch=46,deg=16),
 dict(type="pull_out",to=[121.36,28.66],end_zoom=8.6),
 dict(type="hold_drift",center="JJ",zoom=10.6,pitch=40,bearing=0,drift=2),
 dict(type="fly_to",to="JJ",zoom=11.4,pitch=45,bearing=0,arc=0.4),
 dict(type="fly_to",to="WL",zoom=10.6,pitch=42,bearing=0,arc=0.5),
 dict(type="fly_to",to="SAT",zoom=11.8,pitch=50,bearing=0,arc=0.5),
 dict(type="pull_out",to=[121.2,28.6],end_zoom=8.6),
 dict(type="hold_drift",center="MTN",zoom=9.2,pitch=46,bearing=0,drift=3),
 dict(type="terrain_side",center="KC",zoom=10.4,pitch=70,bearing=70,slide_km=6),
 dict(type="fly_to",to=[121.30,28.76],zoom=9.8,pitch=40,bearing=0,arc=0.4),
 dict(type="fly_to",to="LH",zoom=12.0,pitch=50,bearing=0,arc=0.5),
 dict(type="pull_out",to=[121.6,28.5],end_zoom=8.3),
 dict(type="hold_drift",center="SEA",zoom=8.4,pitch=36,bearing=0,drift=3),
 dict(type="hold_drift",center=[121.45,28.5],zoom=8.6,pitch=38,bearing=0,drift=-3),
 dict(type="fly_to",to="LH",zoom=10.6,pitch=42,bearing=0,arc=0.5),
 dict(type="fly_to",to="FC",zoom=13.6,pitch=56,bearing=15,arc=0.6),
 dict(type="route_fly",places=["LH","BDL"],zoom=5.2,pitch=30,draw=True,move=0.8),
 dict(type="fly_to",to="FC",zoom=13.2,pitch=55,bearing=10,arc=0.8),
 dict(type="orbit",center="FC",zoom=13.4,pitch=58,deg=24),
 dict(type="hold_drift",center="FC",zoom=12.8,pitch=50,bearing=0,drift=2),
 dict(type="route_fly",places=["ST","SXJ","TT","ZY","PORT","SAT"],zoom=8.9,pitch=40,draw=True,move=0.6),
 dict(type="fly_to",to="JJ",zoom=11.2,pitch=48,bearing=0,arc=0.6),
 dict(type="hold_drift",center="TZ",zoom=9.0,pitch=38,bearing=0,drift=3),
 dict(type="hold_drift",center="TZ",zoom=8.8,pitch=36,bearing=0,drift=2)]
assert len(sh) == len(Ls) == len(CH), (len(sh), len(Ls), len(CH))
for i, s in enumerate(sh): s['dur'] = round(E_(i)-S(i), 3); s['_line'] = Ls[i]['text']
HL = ['十有八九','tāi','天台山','七山一水二分田','凭什么','676万','7000亿','146万','卫星工厂','500颗','地形图','括苍山','灵江','椒江','临海','嘉靖','1561年','戚继光','九战九捷','13座','空心敌台','长城','江南长城','剑来','剑气长城','曙光','神仙居','紫阳街','底气','你来点名']
caps = []
for l in Ls:
    tx = l['text']; parts = [tx]
    if len(tx) > 16:
        segs = re.findall(r'[^，；：？。、]+[，；：？。、]?', tx); parts = []; cur = ''
        for sg in segs:
            if cur and len(cur)+len(sg) > 16: parts.append(cur); cur = sg
            else: cur += sg
        if cur: parts.append(cur)
    tot = sum(len(p) for p in parts); t = l['t0']
    for p in parts:
        d = (l['t1']-l['t0'])*len(p)/tot; txt = p.rstrip('，。；：？、')
        caps.append(dict(text=txt, hl=[h for h in HL if h in txt], t=[round(t, 3), round(t+d+(0.18 if p is parts[-1] else 0), 3)])); t += d
for a, b in zip(caps, caps[1:]): a['t'][1] = min(a['t'][1], b['t'][0])
A = [
 dict(type="ground_text",text="台州",at="TZ",width_km=34,role="white",t=TT(0)),
 dict(type="ground_text",text="台州",at="TZ",width_km=30,role="white",t=TT(1)),
 dict(type="ground_text",text="天台山",at="TT",width_km=9,role="white",t=TT(2)),
 dict(type="pin",place="TT",text="天台山",sub="台州得名于此",role="main",t=TT(2)),
 dict(type="area",circle=dict(place="MTN",radius_m=38000),role="river",fill=0.22,t=[S(3),E_(4)],spot=False),
 dict(type="label",at=[121.0,29.05],text="山地",size=40,box=True,role="river",t=[S(3),E_(4)]),
 dict(type="label",at=[121.33,28.62],text="小块平原",size=34,box=True,role="value",t=[S(3),E_(4)]),
 dict(type="label",at=[121.33,28.40],text="小块平原",size=34,box=True,role="value",t=[S(3),E_(4)]),
 dict(type="pin",place="JJ",text="椒江",sub="市政府驻地",role="city",t=TT(6)),
 dict(type="pin",place="WL",text="温岭",sub="县级市",role="main",t=TT(8)),
 dict(type="pin",place="SAT",text="卫星工厂",sub="台州湾新区（位置示意）",role="main",t=TT(9)),
 dict(type="ground_text",text="括苍山",at="KC",width_km=12,role="white",t=[S(11),E_(12)]),
 dict(type="ground_text",text="天台山",at="TT",width_km=12,role="white",t=[S(11),E_(12)]),
 dict(type="ground_text",text="东海",at="SEA",width_km=22,role="white",t=[S(11),E_(16)]),
 dict(type="line",coords=[[120.95,28.93],[121.05,28.88],[121.13,28.845],[121.22,28.80],[121.30,28.73],[121.40,28.70],[121.50,28.69],[121.60,28.68]],role="city",t=[S(13),E_(15)],draw=[S(13)+0.2,E_(13)-0.3],width=9),
 dict(type="label",at=[121.03,28.90],text="灵江",size=40,box=True,role="city",t=[S(13),E_(14)]),
 dict(type="label",at=[121.45,28.72],text="椒江",size=40,box=True,role="city",t=[S(13),E_(14)]),
 dict(type="pin",place="LH",text="临海",sub="唐初台州州城",role="main",t=TT(14)),
 dict(type="line",coords=[[121.9,28.0],[121.75,28.30],[121.70,28.55],[121.60,28.80],[121.70,29.10]],role="main",t=TT(17),draw=[S(17)+0.2,E_(17)-0.4],width=8,dash=True),
 dict(type="label",at=[121.95,28.6],text="倭寇侵扰（示意）",size=32,box=True,role="main",t=TT(17)),
 dict(type="pin",place="LH",text="台州大捷",sub="1561 · 九战九捷",role="main",t=TT(18)),
 dict(type="pin",place="FC",text="台州府城墙",sub="13座双层空心敌台",role="main",t=TT(19)),
 dict(type="line",places=["LH","BDL"],role="main",t=TT(20),draw=[S(20)+0.6,E_(20)-0.2],width=9),
 dict(type="pin",place="BDL",text="北方长城",sub="戚继光北上镇守蓟镇",role="value",t=[S(20)+1.2,E_(20)]),
 dict(type="ground_text",text="江南长城",at="FC",width_km=2.4,role="white",t=TT(21)),
 dict(type="pin",place="FC",text="剑气长城",sub="《剑来》× 台州府城",role="city",t=[S(22),E_(23)]),
 dict(type="pin",place="ST",text="石塘",sub="曙光",role="main",t=[S(24),E_(24)]),
 dict(type="pin",place="SXJ",text="神仙居",role="river",t=[offt(24,'神仙居')-0.4,E_(24)]),
 dict(type="pin",place="TT",text="天台山",role="river",t=[offt(24,'天台山')-0.4,E_(24)]),
 dict(type="pin",place="ZY",text="紫阳街",role="value",t=[offt(24,'紫阳街')-0.4,E_(24)]),
 dict(type="pin",place="PORT",text="大麦屿港",role="city",t=[offt(24,'港口')-0.4,E_(24)]),
 dict(type="pin",place="SAT",text="卫星工厂",role="main",t=[offt(24,'卫星工厂')-0.4,E_(24)]),
 dict(type="ground_text",text="台州",at="TZ",width_km=30,role="white",t=[S(25),E_(26)])]
counter = [dict(t0=S(14),t1=E_(14),big="唐初",small="设台州 · 州治临海"),dict(t0=S(17),t1=E_(17),big="嘉靖",small="明 · 倭患"),
 dict(t0=S(18),t1=E_(18),big="1561年",small="台州大捷"),dict(t0=S(22),t1=E_(22),big="2025年",small="《剑来》联动台州府城")]
cards = [dict(t0=offt(1,'一声')-0.3,t1=E_(1),big="台 = tāi",size=96,label="读一声，不读 tái"),
 dict(t0=offt(5,'凭什么')-0.3,t1=E_(5),big="凭什么？",size=90),
 dict(t0=S(7),t1=E_(7),big="676万人 · 7005.87亿元",size=58,label="2025年｜台州市统计公报"),
 dict(t0=S(8)+0.6,t1=E_(8),big="温岭 146万人",size=70,label="2025年末常住人口｜一个县级市"),
 dict(t0=offt(9,'年产能')-0.4,t1=E_(9),big="500颗/年",size=80,label="卫星工厂设计产能（央视网 2024）"),
 dict(t0=offt(19,'13座')-0.5,t1=E_(19),big="13座 空心敌台",size=66,label="戚继光、谭纶在台州府城墙增筑"),
 dict(t0=offt(24,'汽车')-0.6,t1=E_(24),big="港口 · 汽车 · 卫星",size=60),
 dict(t0=S(26),t1=E_(26),big="底气",size=110,label="山海给的 · 人闯出来的")]
moods = [dict(t0=0,t1=S(16),preset="neutral",strength=0.4),dict(t0=S(16),t1=E_(23),preset="warm",strength=0.5),dict(t0=S(24),t1=D+1,preset="neutral",strength=0.4)]
music = dict(sections=[
  dict(t0=0.0, t1=S(5)-0.2, track='@drone', gain=0.5, fi=0.05, fo=0.6),
  dict(t0=S(5)-0.6, t1=S(11), track='bittersweet', off=0, gain=0.42, fi=1.2, fo=0.8),
  dict(t0=S(11)-0.4, t1=S(16)+0.2, track='determined_pursuit', off='mid', gain=0.5, fi=0.8, fo=0.3),
  dict(t0=S(16)+0.4, t1=S(24)+0.3, track='war_theme', off='mid', gain=0.5, fi=0.8, fo=1.2),
  dict(t0=S(24)-0.2, t1=D, track='emotional_piano', off=0, gain=0.45, fi=1.5, fo=1.2)])
# 真实素材「实拍窗」（engine/broll.py）：每段 2.2–2.8s，合计 ≈10%
broll = [dict(file=f"{PJ}/broll/guoqing.jpg",t0=round(S(2)+0.6,2),dur=2.4,kb="in",credit="1918 天台国清寺隋塔｜关野贞摄｜公有领域"),
 dict(file=f"{PJ}/broll/jiaojiang_pexels.jpg",t0=round(S(7)+0.3,2),dur=2.6,kb="out",credit="椒江航拍｜kike yao / Pexels"),
 dict(file=f"{PJ}/broll/wall.jpg",t0=round(offt(19,'府城墙')-0.2,2),dur=2.6,kb="in",credit="临海台州府城墙｜黑揍红 CC BY 2.5"),
 dict(file=f"{PJ}/broll/shitang.jpg",t0=round(S(24)+0.2,2),dur=2.2,kb="in",credit="温岭石塘｜Kejunorg CC BY-SA 4.0"),
 dict(file=f"{PJ}/broll/shenxianju.jpg",t0=round(offt(24,'云海')-0.3,2),dur=2.2,kb="out",credit="神仙居｜rheins CC BY 3.0")]
chap = []; seen = set()
for i, c in enumerate(CH):
    if c not in seen: seen.add(c); chap.append(dict(title=c, shot=i))
cover = dict(top="<b>我的频道</b>　·　城市底气 No.2", kicker="七山一水二分田", title="台州的底气", sub="山 × 海 × 一城老板", sub2=["这个「台」", "你念对了吗？"],
  coord=["28°39′N","台州","121°25′E"], quote="「被山逼着　向海里闯的城」",
  generals=[dict(label="唐初", name="因山得名", state="天台山", keep=True), dict(label="1561", name="台州大捷", state="戚继光", keep=True),
            dict(label="2000", name="千年曙光", state="石塘", keep=True), dict(label="今天", name="卫星工厂", state="台州湾", keep=True)],
  series="城市底气　No.2", brand="我的频道", bg=dict(t=round(S(1)+0.8, 2), delogo=[[30, 1240, 1020, 180]], crop=[1080, 1600, 0, 160]))
ep = dict(id="taizhou_v1", _note="《城市底气》No.2 台州 v1（2026-10-20）。v4 复刻「三维地图看世界」画风（style=sanwei）。口播 TTS 预置男声，atempo %s；时间轴=%s。事实见 projects/taizhou_v1/sources.md。不画任何行政界线。" % (T.get('atempo'), 'estimated' if T.get('estimated') else 'real'),
  aspect="9x16", fps=30, render_step=1, terrain_exaggeration=1.4, dem_maxzoom=12, style="sanwei",
  places=P, title=dict(text="台州的底气", sub="这个「台」，你念对了吗？", t=[0.15, min(3.0, E_(0))]), shots=sh, annotations=A, captions=caps,
  counter=counter, cards=cards, music_seed=22, moods=moods, focus_dim=0.3, music=music, cover=cover, broll=broll,
  credit="影像 © Esri 等（内部测试源）· 地形 AWS · 河道/航线为示意 · 不含行政界线",
  context=dict(cities=True, rivers=["灵江","椒江"], max_cities=8), chapters=chap, music_theme="city")
json.dump(ep, open('episodes/taizhou_v1.json', 'w'), ensure_ascii=False, indent=1)
print('shots', len(sh), 'caps', len(caps), 'D', D, 'frames', round(D*30), 'estimated' if T.get('estimated') else 'real', 'chapters', [(c['title'], S(c['shot'])) for c in chap])

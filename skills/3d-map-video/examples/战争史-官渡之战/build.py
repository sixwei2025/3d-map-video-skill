#!/usr/bin/env python3
"""官渡之战全片 build：timeline.json → work/v2/war_guandu[_lo]/{scene.json,meta.json}。用法 build.py [0.5]"""
import json,os,re,sys
H=os.path.dirname(os.path.abspath(__file__));ROOT=os.path.dirname(os.path.dirname(H));sys.path.insert(0,f'{ROOT}/engine/warfx')
from shots import build_camera
SC=float(sys.argv[1]) if len(sys.argv)>1 else 1.0;ID='war_guandu'+('_lo' if SC<1 else '');W=f'{ROOT}/work/v2/{ID}';os.makedirs(W,exist_ok=True)
TL=json.load(open(f'{H}/timeline.json'));L=TL['lines'];D=TL['duration'];FPS=30
T=lambda i:L[i]['t0'];T1=lambda i:L[i]['t1']
def kw(i,w,off=0):
    l=L[i];s=l['text'];k=s.index(w);return round(l['t0']+(l['t1']-l['t0'])*k/len(s)+off,3)
BLUE,BLUEP,RED,YEL,BD,RD='#2E8BFF','#8FD0FF','#C8102E','#FFD84A','#4FA3FF','#FF3B4F'
# 地点：脚本 v2 §7 示意坐标（均待核实，画面标「示意」）
XU,GUANDU,BAIMA,LIYANG,YANJIN,WUCHAO,YE=[113.93,34.04],[114.05,34.80],[114.70,35.58],[114.58,35.67],[114.20,35.35],[114.33,35.15],[114.38,36.33]
YCAMP=[114.05,34.90]   # 袁军连营（示意）
RIVER=[[112.30,34.86],[112.90,34.92],[113.40,34.96],[113.95,35.15],[114.25,35.40],[114.64,35.63],[115.00,35.85],[115.35,36.05],[115.90,36.40],[116.60,36.90]]
def P(at,text,t0,t1,dx=18,dy=0,**k):return dict(type='place',at=at,text=text,t0=t0,t1=t1,dx=dx,dy=dy,avoid=False,**k)
def chip(text,t0,t1,x=540,y=230,**k):return dict(type='chip',text=text,x=x,y=y,align=k.pop('align','center'),size=k.pop('size',38),weight=800,t0=t0,t1=t1,**k)
els=[dict(type='river',coords=RIVER,t0=0.2,draw=[0.35,2.6],width=1.0,color='#7FE8FF',t1=T(33)+0.3)]
A=els.append
# ── 钩子（0–3）
t3,t4=T(2),T(3)
A(P([113.15,35.02],'黄河',1.2,11.0,dot=0,sub='东汉故道·示意',tc='#BFF6FF',color='#7FE8FF',size=42))
A(chip('公元 200 年 · 建安五年',0.3,6.6,y=110,size=40,border='rgba(127,232,255,0.7)'))
A(P(YE,'邺',kw(0,'北岸',-0.3),t4+0.5,sub='袁绍大本营',color=BLUE))
A(P(LIYANG,'黎阳',kw(0,'北岸'),t4+0.5,dx=-18,color=BLUE))
A(dict(type='route',coords=[YE,[114.5,36.0],LIYANG],color=BLUE,particle=BLUEP,width=9,seed=101,t0=kw(0,'北岸'),draw=[kw(0,'北岸'),kw(0,'北岸')+1.4],t1=t3+0.6,n=320,spread=1.4))
A(dict(type='dots',at=[114.30,35.90],n=100,cols=10,gap=21,r=7,color=BD,seed=2026,spawn=[kw(0,'点了'),kw(0,'精兵')+0.4],t0=kw(0,'点了'),t1=t4+0.4,
  move=dict(coords=[[114.30,35.90],[114.25,35.55],[114.08,35.08]],draw=[kw(2,'结果',-0.1),kw(2,'十万那边')]),
  kill=dict(t0=kw(2,'十万那边',0.2),t1=kw(2,'只带'),remain=1),retreat=dict(coords=[[114.08,35.08],[114.28,35.40],[114.52,35.72],[114.40,36.15]],draw=[kw(2,'只带'),T1(2)+0.3],scale=1.5,label='八百骑')))
A(chip('● 1 点 = 1000 人',kw(0,'精兵'),t3,y=505,size=32,color='#DDE8F5'))
A(dict(type='roller',x=50,y=330,title='袁绍 · 河北',from_=0,to=100000,color=BLUE,size=88,t0=kw(0,'点了',-0.2),roll=[kw(0,'点了'),kw(0,'精兵')+0.4],sub='骑兵 10,000',subT=kw(0,'一万匹'),t1=t4+0.4,roll2=[kw(2,'十万那边'),kw(2,'只带')+0.4],roll2v=800))
A(P(GUANDU,'官渡',T(1),T(4),sub='今河南中牟东北·示意',color=RED))
A(P(XU,'许',T(1)+0.2,t4+0.5,sub='曹操·许都',color=RED))
A(dict(type='route',coords=[XU,[113.95,34.4],[GUANDU[0],GUANDU[1]-0.04]],color=RED,particle=YEL,width=9,seed=202,t0=T(1),draw=[T(1)+0.1,kw(1,'史书')],t1=t4+0.4,n=320))
A(dict(type='dots',at=[113.80,34.70],n=10,cols=5,gap=26,r=8,color=RD,seed=7,partial=0.55,spawn=[kw(1,'另一个'),kw(1,'手里')+0.3],t0=kw(1,'另一个'),t1=t4+0.4))
A(dict(type='roller',x=1030,y=330,align='right',title='曹操 · 河南',prefix='<',from_=0,to=10000,color=RED,size=88,t0=kw(1,'不满',-0.45),roll=[kw(1,'不满',-0.2),kw(1,'不满')+0.7],sub='史载 · 有争议',subT=kw(1,'史书'),subColor='#C9D2DC',t1=t4+0.4))
A(dict(type='slam',text='10 : 1',y=760,size=230,t0=t3,t1=kw(2,'结果')+0.5,glow=YEL));A(dict(type='shake',t=t3+0.05,amp=18,dur=0.5))
A(dict(type='route',coords=[[GUANDU[0],GUANDU[1]+0.02],[114.05,34.98]],color=RED,particle=YEL,width=10,seed=303,t0=kw(2,'结果',-0.2),draw=[kw(2,'结果',-0.2),kw(2,'结果',0.3)],t1=t4+0.4,n=160))
A(dict(type='impact',at=[114.06,35.0],t=kw(2,'结果',0.3),seed=9,scale=1.5,n=200));A(dict(type='impact',at=[114.16,35.1],t=kw(2,'结果',0.6),seed=19,scale=1.0,n=120))
A(dict(type='shake',t=kw(2,'结果',0.3),amp=24,dur=0.7))
A(dict(type='route',coords=[YE,[114.45,35.8],[114.32,35.45],WUCHAO],color=BLUE,particle=BLUEP,width=7,dash=True,seed=404,t0=kw(3,'答案'),draw=[kw(3,'答案'),kw(3,'答案',1.0)],t1=T(4)+0.2,fout=0.6,n=120,head=False))
A(dict(type='route',coords=[XU,[113.92,34.45],GUANDU],color=RED,particle=YEL,width=7,dash=True,seed=505,t0=kw(3,'答案'),draw=[kw(3,'答案'),kw(3,'答案',1.0)],t1=T(4)+0.2,fout=0.6,n=120,head=False))
A(chip('粮道',kw(3,'答案',0.8),T(4),x=700,y=1180,size=36,color=YEL,border=YEL))
A(dict(type='qmark',at=WUCHAO,text='乌巢 · 示意',t0=kw(3,'粮道',-0.4),t1=T(4)+0.2))
A(chip('地名位置均为示意',T(4),T(33),x=1050,y=40,align='right',size=26,color='#C9D2DC',border='rgba(255,255,255,0.25)'))
# ── 壹·白马（4–11）
A(dict(type='veil',t0=T(4)-0.1,t1=T(4)+1.7,fin=0.2,fout=0.4,alpha=0.7));A(dict(type='seal',text='白马',num='壹',sub='第一篇',t0=T(4),t1=T(4)+1.8,fout=0.4))
for at,tx,k in [([115.3,37.6],'冀州','建安五年'),([118.0,36.6],'青州','河北'),([116.4,39.6],'幽州','四个州'),([112.6,37.8],'并州','四个州')]:
    A(P(at,tx,kw(4,k,0.2 if tx!='并州' else 0.6),T(5)+0.2,dot=9,color=BLUE,size=50))
A(dict(type='dots',at=[115.3,37.3],n=40,cols=8,gap=20,r=6,color=BD,seed=31,spawn=[kw(4,'河北'),kw(4,'四个州')+0.6],t0=kw(4,'河北'),t1=T(5)+0.2))
A(P(XU,'许都',kw(4,'许都'),T(5)+0.2,sub='曹操挟天子',color=RED,size=50))
A(dict(type='route',coords=[[115.2,37.1],[114.6,36.2],LIYANG,[114.3,35.2],XU],color=BLUE,particle=BLUEP,width=8,seed=41,t0=kw(4,'要过河'),draw=[kw(4,'要过河'),kw(4,'要过河',1.2)],t1=T(5)+0.2,n=220))
A(chip('袁绍 · 河北四州',kw(4,'占着'),T(5),x=50,y=230,align='left',color=BLUEP,border=BLUE))
A(chip('曹操 · 挟天子守河南',kw(4,'曹操'),T(5),x=1030,y=330,align='right',color='#FFB0B8',border=RED))
# 白马包围
A(P(BAIMA,'白马',T(5),T(9),dx=30,dy=-46,sub='今滑县东·示意',color=RED,size=54))
A(P(LIYANG,'黎阳',T(5)+0.3,T(9),dx=-24,dy=-30,sub='袁绍主力',color=BLUE,size=48))
A(dict(type='dots',at=BAIMA,n=24,cols=6,gap=40,r=7,color=BD,seed=51,spawn=[kw(5,'颜良'),kw(5,'围了')+0.6],t0=kw(5,'颜良'),t1=T(8)+0.6))
A(dict(type='dots',at=[114.56,35.74],n=40,cols=8,gap=20,r=6,color=BD,seed=52,spawn=[kw(6,'黎阳',-0.6),kw(6,'黎阳',0.4)],t0=kw(6,'黎阳',-0.6),t1=T(8)+0.2))
A(chip('大将 颜良 · 围白马',kw(5,'颜良'),T(7),y=230,color=BLUEP,border=BLUE))
A(dict(type='route',coords=[[114.72,35.40],[114.71,35.52]],color=RED,particle=YEL,width=8,dash=True,seed=61,t0=kw(6,'硬救'),draw=[kw(6,'硬救'),kw(6,'硬救',0.8)],t1=T(7)+0.2,n=80))
A(chip('硬救 = 送进包围圈',kw(6,'硬救',0.3),T(7),y=330,color=YEL,border=YEL))
# 延津佯渡 → 回击白马（侧视）
A(P(YANJIN,'延津',T(7),T(9),dx=-26,dy=-40,sub='佯渡',color=RED,size=52))
A(dict(type='route',coords=[[114.12,35.10],[114.16,35.25],YANJIN],color=RED,particle=YEL,width=10,seed=71,t0=kw(7,'延津'),draw=[kw(7,'延津'),kw(7,'渡河')+0.2],t1=T(9),n=260))
A(dict(type='dots',at=[114.56,35.74],n=40,cols=8,gap=20,r=6,color=BD,seed=53,spawn=[T(8)-0.2,T(8)],t0=T(8)-0.2,t1=T(9),move=dict(coords=[[114.56,35.74],[114.40,35.62],[114.24,35.50]],draw=[T(8),kw(8,'西堵')+0.4])))
A(dict(type='route',coords=[YANJIN,[114.40,35.45],[114.62,35.55],BAIMA],color=RED,particle=YEL,width=11,seed=72,t0=kw(8,'掉头'),draw=[kw(8,'掉头'),kw(8,'扑向白马')+0.2],t1=T(9),n=360,spread=1.3))
A(dict(type='impact',at=BAIMA,t=kw(8,'斩了'),seed=73,scale=1.6,n=220));A(dict(type='shake',t=kw(8,'斩了'),amp=22,dur=0.6))
A(chip('荀攸计 · 声东击西',kw(7,'荀攸'),T(8),y=230,color=YEL,border=YEL))
A(chip('关羽 · 万众之中斩颜良',kw(8,'关羽'),T(9)+0.2,y=230,color='#FFB0B8',border=RED,size=42))
# 文丑 / 辎重
A(dict(type='roller',x=50,y=420,title='文丑 · 骑兵',from_=0,to=6000,color=BLUE,size=80,t0=kw(9,'文丑',-0.2),roll=[kw(9,'文丑'),kw(9,'文丑',0.9)],sub='五六千',subT=kw(9,'五六千'),t1=T(11)))
A(dict(type='roller',x=1030,y=420,align='right',title='曹操 · 骑兵',prefix='<',from_=0,to=600,color=RED,size=80,t0=kw(9,'曹操',-0.2),roll=[kw(9,'曹操'),kw(9,'不到',0.5)],sub='不到六百',subT=kw(9,'不到'),t1=T(11)))
A(dict(type='dots',at=[114.52,35.40],n=12,cols=6,gap=24,r=7,color=YEL,seed=81,spawn=[kw(10,'辎重'),kw(10,'诱饵')],t0=kw(10,'辎重'),t1=kw(10,'再冲',0.4)))
A(chip('辎重 = 诱饵',kw(10,'诱饵',-0.2),T(11),x=540,y=1180,color=YEL,border=YEL))
A(dict(type='dots',at=[114.66,35.62],n=36,cols=6,gap=20,r=6,color=BD,seed=82,spawn=[T(9),kw(9,'骑兵')],t0=T(9),t1=T(11)+0.3,move=dict(coords=[[114.66,35.62],[114.52,35.42]],draw=[T(9)+0.3,kw(10,'抢成',0.4)]),kill=dict(t0=kw(10,'再冲'),t1=kw(10,'文丑',0.6),remain=5)))
A(dict(type='route',coords=[[114.40,35.30],[114.50,35.40]],color=RED,particle=YEL,width=11,seed=83,t0=kw(10,'再冲',-0.2),draw=[kw(10,'再冲',-0.2),kw(10,'再冲',0.3)],t1=T(11),n=200))
A(dict(type='impact',at=[114.52,35.42],t=kw(10,'再冲',0.3),seed=84,scale=1.3,n=180));A(dict(type='shake',t=kw(10,'再冲',0.3),amp=18,dur=0.5))
A(chip('文丑 · 战死',kw(10,'文丑'),T(11)+0.2,y=230,color='#FFB0B8',border=RED,size=42))
A(dict(type='dots',at=[114.50,35.95],n=100,cols=10,gap=19,r=6,color=BD,seed=85,spawn=[T(11),T(11)+0.7],t0=T(11),t1=T(12)+0.2,kill=dict(t0=kw(11,'没了',-0.3),t1=kw(11,'没了',0.3),remain=98)))
A(chip('十万 · 几乎未动',kw(11,'十万人'),T(12)+0.2,y=330,color=BLUEP,border=BLUE,size=44))
# ── 贰·对峙（12–20）
A(dict(type='veil',t0=T(12)-0.1,t1=T(12)+1.7,fin=0.2,fout=0.4,alpha=0.7));A(dict(type='seal',text='对峙',num='贰',sub='第二篇',t0=T(12),t1=T(12)+1.8,fout=0.4))
A(P(GUANDU,'官渡',T(12),T(17),dx=30,dy=70,sub='曹营·示意',color=RED,size=50))
A(P(YCAMP,'袁营',T(12)+1.0,T(17),dx=-40,dy=-92,sub='依沙堆连营',color=BLUE,size=46))
A(dict(type='dots',at=YCAMP,n=40,cols=40,gap=17,r=6,color=BD,seed=91,spawn=[kw(12,'沙堆'),kw(12,'几十里')+0.6],t0=kw(12,'沙堆'),t1=T(17)))
A(dict(type='dots',at=[114.05,34.81],n=12,cols=6,gap=22,r=7,color=RD,seed=92,spawn=[T(12)+0.5,T(12)+1.2],t0=T(12)+0.5,t1=T(15)))
A(chip('东西连营 数十里',kw(12,'东西'),T(13)+0.3,y=330,color=BLUEP,border=BLUE,size=42))
for j in range(6):
    x=113.99+j*0.024;t0=kw(13,'放箭',-0.9)+j*0.22
    A(dict(type='route',coords=[[x,34.895],[x+0.01,34.818]],color=BLUE,particle=BLUEP,width=5,seed=100+j,t0=t0,draw=[t0,t0+0.5],t1=T(14)+0.2,fout=0.4,n=60))
A(chip('土山 · 高橹 · 箭雨',kw(13,'土山'),T(14),y=230,color=BLUEP,border=BLUE))
A(chip('曹军 · 蒙盾而行',kw(13,'曹军'),T(14),y=330,color='#FFB0B8',border=RED))
for j in range(3):
    t0=kw(14,'砸塌',-1.0)+j*0.55;x=114.00+j*0.04
    A(dict(type='route',coords=[[x+0.01,34.815],[x,34.86],[x,34.895]],color=RED,particle=YEL,width=7,seed=110+j,t0=t0,draw=[t0,t0+0.45],t1=t0+1.2,fout=0.4,n=100))
    A(dict(type='impact',at=[x,34.897],t=t0+0.45,seed=120+j,scale=0.9,n=110));A(dict(type='shake',t=t0+0.45,amp=12,dur=0.35))
A(dict(type='slam',text='霹雳车',y=700,size=150,t0=kw(14,'霹雳车'),t1=kw(14,'霹雳车',1.3),glow=YEL))
A(dict(type='route',coords=[[114.075,34.895],[114.07,34.85],[114.065,34.835]],color=BLUE,particle=BLUEP,width=6,dash=True,seed=130,t0=kw(14,'地道'),draw=[kw(14,'地道'),kw(14,'地道',1.0)],t1=T(15)+0.3,n=60,head=True))
A(dict(type='route',coords=[[114.02,34.83],[114.11,34.83]],color=RED,particle=YEL,width=9,seed=131,t0=kw(14,'长沟',-0.3),draw=[kw(14,'长沟',-0.3),kw(14,'截住')],t1=T(15)+0.3,n=120,head=False))
A(chip('地道 ✕ 长堑',kw(14,'长沟'),T(15),y=330,color=YEL,border=YEL))
A(dict(type='roller',x=50,y=420,title='建安五年 · 月',from_=8,to=10,color=BLUE,size=110,t0=T(15)-0.1,roll=[kw(15,'八月'),kw(15,'十月')+0.3],t1=T(17)))
A(dict(type='dots',at=[114.05,34.79],n=10,cols=5,gap=26,r=8,color=RD,seed=93,spawn=[T(15),T(15)+0.4],t0=T(15),t1=T(21),kill=dict(t0=kw(15,'兵少'),t1=kw(15,'粮尽'),remain=7)))
A(chip('兵少 · 粮尽',kw(15,'兵少'),T(17),x=1030,y=330,align='right',color='#FFB0B8',border=RED,size=44))
A(P(XU,'许',T(15),T(17),sub='荀彧留守',color=RED,size=50))
A(dict(type='route',coords=[XU,[113.98,34.42],[GUANDU[0],GUANDU[1]-0.03]],color=YEL,particle=YEL,width=7,dash=True,seed=140,t0=kw(16,'回信',-0.4),draw=[kw(16,'回信',-0.4),T1(16)+0.2],t1=T(17)+0.4,n=120))
A(dict(type='veil',t0=T(17)-0.2,t1=T(21),fin=0.3,fout=0.5,alpha=0.62))
A(dict(type='quote',src='《三国志·荀彧传》',who='荀彧 · 答曹操书',text='此用奇之时，不可失也。',plain='白话：这是出奇兵的时候，不能错过。',t0=T(17)-0.15,t1=T1(17)+0.35,y=620))
A(dict(type='dots',at=[114.12,34.80],n=12,cols=6,gap=22,r=7,color=YEL,seed=94,spawn=[kw(18,'运粮'),kw(18,'士兵')],t0=kw(18,'运粮'),t1=T(21)))
A(chip('运粮的士兵',kw(18,'运粮'),T(19),y=330,color=YEL,border=YEL))
A(dict(type='quote',src='《三国志·武帝纪》',who='曹操 · 对运粮兵',text='却十五日为汝破绍，\n不复劳汝矣。',plain='白话：再过十五天替你们打败袁绍，\n不再让你们受累。',t0=T(19)-0.15,t1=T1(19)+0.35,y=560))
A(dict(type='slam',text='15 天',y=760,size=230,t0=T(20),t1=T(21)+0.1,glow=RED))
# ── 叁·夜奔（21–25）
A(dict(type='veil',t0=T(21)-0.2,t1=T(28)+0.2,fin=0.5,fout=0.4,alpha=0.42,color='#020a24'))
A(dict(type='seal',text='夜奔',num='叁',sub='第三篇',t0=T(21),t1=T(21)+1.8,fout=0.4,y=520))
A(P(GUANDU,'曹营',T(21),T(26),dx=24,dy=40,color=RED,size=46));A(P(YCAMP,'袁营',T(21),T(26),dx=-30,dy=-56,color=BLUE,size=46))
A(dict(type='dots',at=YCAMP,n=40,cols=40,gap=17,r=6,color=BD,seed=91,spawn=[T(21)-0.3,T(21)],t0=T(21)-0.3,t1=T(26)))
A(dict(type='dots',at=YCAMP,n=1,cols=1,gap=10,r=11,color='#FFFFFF',seed=95,spawn=[kw(21,'许攸'),kw(21,'许攸',0.2)],t0=kw(21,'许攸'),t1=T(24),move=dict(coords=[YCAMP,[114.07,34.86],[114.05,34.815]],draw=[kw(21,'连夜'),T1(21)+0.4])))
A(chip('许攸 · 袁绍谋士',kw(21,'许攸'),T(23),y=230,color='#FFFFFF',border='rgba(255,255,255,0.7)',size=42))
A(chip('家人犯法被收 → 连夜投曹',kw(21,'家人'),T(22),y=330,size=34,color='#DDE8F5'))
A(chip('跣足出迎',kw(22,'光着脚'),T(23),y=330,color=YEL,border=YEL,size=42))
A(dict(type='quote',src='《三国志·武帝纪》裴注引《曹瞒传》',who='曹操 · 迎许攸',text='子远，卿来，吾事济矣！',plain='白话：子远，你来了，我的事成了！',t0=T(23)-0.15,t1=T1(23)+0.35,y=620))
A(dict(type='roller',x=50,y=420,title='曹军存粮 · 月',from_=12,to=6,color=RED,size=110,t0=kw(24,'粮还',-0.2),roll=[kw(24,'一年',-0.1),kw(24,'半年',0.2)],roll2=[kw(24,'一个月',-0.3),kw(24,'一个月',0.4)],roll2v=1,sub='只够一个月',subT=kw(24,'一个月'),subColor=YEL,t1=T(26)))
A(dict(type='impact',at=GUANDU,t=kw(24,'不对'),seed=96,scale=0.4,n=30))
A(dict(type='qmark',at=WUCHAO,text='乌巢 · 示意',t0=kw(25,'乌巢',-0.2),t1=T(26)+0.3))
A(dict(type='route',coords=[YE,[114.45,35.8],LIYANG,[114.42,35.42],WUCHAO],color=BLUE,particle=BLUEP,width=7,dash=True,seed=150,t0=kw(25,'坐标'),draw=[kw(25,'坐标'),kw(25,'乌巢')],t1=T(32),fout=0.3,n=140,head=False))
A(dict(type='dots',at=WUCHAO,n=24,cols=6,gap=20,r=6,color=YEL,seed=97,spawn=[kw(25,'一万多车'),kw(25,'粮草',0.4)],t0=kw(25,'一万多车'),t1=T(28)))
A(chip('粮车 万余乘',kw(25,'一万多车'),T(26),x=1030,y=330,align='right',color=YEL,border=YEL,size=40))
A(dict(type='route',coords=[YCAMP,[114.20,35.03],WUCHAO],color='#DDE8F5',particle='#FFFFFF',width=4,dash=True,seed=151,t0=kw(25,'四十里',-0.3),draw=[kw(25,'四十里',-0.3),kw(25,'四十里',0.6)],t1=T(26),n=40,head=False))
A(chip('去绍营四十里（约 17 公里）',kw(25,'四十里'),T(26),y=1180,size=34,color='#DDE8F5'))
# ── 肆·乌巢（26–32）侧视夜袭
A(dict(type='seal',text='乌巢',num='肆',sub='第四篇',t0=T(26),t1=T(26)+1.8,fout=0.4,y=520))
A(P(GUANDU,'官渡',T(26),T(28),dx=26,dy=30,color=RED,size=46))
A(P(WUCHAO,'乌巢',T(26),T(28),dx=26,dy=-48,sub='淳于琼屯粮·示意',color=YEL,size=52))
MARCH=[[114.06,34.82],[114.10,34.93],[114.22,35.05],[WUCHAO[0]-0.01,WUCHAO[1]-0.01]]
A(dict(type='route',coords=MARCH,color=RED,particle=YEL,width=8,dash=True,seed=160,t0=kw(26,'五千'),draw=[kw(26,'五千'),T1(27)+0.6],t1=T(30),n=200,head=True))
A(dict(type='dots',at=[114.06,34.82],n=5,cols=5,gap=26,r=9,color=BD,seed=161,spawn=[kw(26,'旗号',-0.3),kw(26,'旗号',0.5)],t0=kw(26,'旗号',-0.3),t1=kw(28,'点火'),fout=0.1,move=dict(coords=MARCH,draw=[kw(26,'旗号',0.5),T1(27)+0.6])))
A(dict(type='dots',at=WUCHAO,n=5,cols=5,gap=26,r=9,color=RD,seed=162,spawn=[kw(28,'点火'),kw(28,'点火',0.2)],t0=kw(28,'点火'),t1=T(30)))
A(chip('五千步骑 · 打袁军旗号',kw(26,'五千'),T(27),y=230,color='#FFB0B8',border=RED,size=40))
A(chip('衔枚缚马 · 人抱束薪',kw(26,'衔枚'),T(27)+0.2,y=330,size=36,color=YEL,border=YEL))
A(dict(type='qmark',at=[114.16,34.99],text='盘问',t0=kw(27,'盘问'),t1=T1(27)))
A(chip('「袁公派我们去加强防守」',kw(27,'就说'),T(28),y=330,size=36,color=BLUEP,border=BLUE))
F=kw(28,'点火')
for j,(d,s,n) in enumerate([(0,2.3,340),(0.3,1.4,200),(0.7,1.1,160),(1.1,0.9,120)]):
    A(dict(type='impact',at=[WUCHAO[0]+[0,0.02,-0.02,0.01][j],WUCHAO[1]+[0,0.01,0,-0.015][j]],t=F+d,seed=170+j,scale=s,n=n,dur=1.8))
A(dict(type='shake',t=F,amp=34,dur=1.1));A(dict(type='slam',text='点火',y=700,size=200,t0=F,t1=F+1.2,glow='#FF7A1A'))
A(dict(type='route',coords=[YCAMP,[114.20,35.03],[WUCHAO[0]-0.02,WUCHAO[1]-0.03]],color=BLUE,particle=BLUEP,width=5,seed=180,t0=kw(29,'轻骑'),draw=[kw(29,'轻骑'),kw(29,'乌巢',0.4)],t1=T(31),n=100))
A(dict(type='route',coords=[[114.03,34.93],[114.04,34.84]],color=BLUE,particle=BLUEP,width=16,seed=181,t0=kw(29,'主力'),draw=[kw(29,'主力'),kw(29,'曹营')],t1=T(32),n=300,spread=1.6))
A(chip('轻骑 → 乌巢',kw(29,'轻骑'),T(30)+1,x=50,y=230,align='left',size=36,color=BLUEP,border=BLUE))
A(chip('主力 → 曹营',kw(29,'主力'),T(30)+1,x=1030,y=230,align='right',size=44,color=BLUEP,border=BLUE))
A(P(GUANDU,'官渡',T(29),T(33),dx=26,dy=34,color=RED,size=44));A(P(WUCHAO,'乌巢',F+1.2,T(33),dx=26,dy=-44,color=YEL,size=48))
A(dict(type='slam',text='贼在背后，乃白！',y=700,size=96,t0=kw(30,'贼到了'),t1=T(31),glow=RED))
A(dict(type='impact',at=[114.04,34.85],t=kw(31,'打不下来'),seed=190,scale=1.0,n=120))
A(dict(type='dots',at=[114.02,34.88],n=8,cols=4,gap=22,r=8,color=BD,seed=191,spawn=[kw(31,'张郃'),kw(31,'张郃',0.3)],t0=kw(31,'张郃'),t1=kw(31,'投降')))
A(dict(type='dots',at=[114.02,34.88],n=8,cols=4,gap=22,r=8,color=RD,seed=192,spawn=[kw(31,'投降'),kw(31,'投降',0.4)],t0=kw(31,'投降'),t1=T(33)))
A(chip('张郃 · 高览 来降',kw(31,'张郃'),T(32),y=330,color='#FFB0B8',border=RED,size=42))
A(chip('淳于琼被斩 · 粮草烧光',T(31),T(32),y=230,color=YEL,border=YEL,size=40))
A(dict(type='dots',at=[114.25,35.05],n=100,cols=10,gap=19,r=6,color=BD,seed=193,spawn=[T(31)+0.4,T(31)+1.2],t0=T(31)+0.4,t1=T(33)+0.3,kill=dict(t0=kw(32,'崩了',-0.8),t1=kw(32,'崩了',0.4),remain=8),
  retreat=dict(coords=[[114.25,35.05],[114.40,35.35],[114.58,35.70]],draw=[kw(32,'带八百骑',-0.3),T1(32)],scale=1.4,label='八百骑')))
A(dict(type='slam',text='一夜崩了',y=700,size=170,t0=kw(32,'一夜'),t1=kw(32,'袁绍'),glow=BLUE))
A(dict(type='roller',x=1030,y=420,align='right',title='袁军',from_=100000,to=100000,color=BLUE,size=88,t0=kw(32,'十万'),roll=[0,0.1],roll2=[kw(32,'崩了',-0.6),kw(32,'八百骑')],roll2v=800,sub='渡河逃走',subT=kw(32,'渡河'),t1=T(33)+0.2))
# ── 伍·为什么（33–36）2D 几何 → 尾卡
A(dict(type='seal',text='为什么',num='伍',sub='第五篇',t0=T(33)-0.3,t1=T(33)+1.2,fout=0.3,y=1500,size=110))
A(dict(type='geo',t0=T(33)-0.2,t1=T(37)+0.2,fin=0.6,fout=0.3,tl=kw(33,'一条线'),tn=kw(33,'一个点'),ta=T(35)+0.2,tb=kw(35,'那个点'),
  labels=[dict(t=kw(36,'一家公司'),circle='一家公司',node='乌巢',line='总部'),dict(t=kw(36,'一个仓'),circle='一家公司',node='一个仓',line='总部'),dict(t=kw(36,'一笔现金'),circle='一家公司',node='一笔现金',line='总部'),dict(t=kw(36,'一个供应商'),circle='一家公司',node='一个供应商',line='总部')]))
A(dict(type='endcard',text='兵再多，命门可能只有一个',t0=T(37)-0.1,t1=D+1,fin=0.4,seal='官渡',sub='建安五年 · 公元200年',y=860,size=80))
for e in els:
    if 'from_' in e: e['from']=e.pop('from_')
# 字幕：方言三句与尾句不出底字幕（文件框/大字卡已显示）
subs=[]
for l in L:
    if l['i'] in (17,19,23,37): continue
    parts=[p for p in re.split(r'(?<=[，。？、：；！])',l['text'].replace('——','')) if p];n=sum(len(p) for p in parts);t=l['t0'];chunks=[];cur=''
    for p in parts:
        if len(cur)+len(p)<=15 and (len(cur)<7 or len(cur)+len(p)<=10): cur+=p
        else:
            if cur: chunks.append(cur)
            cur=p
    if cur: chunks.append(cur)
    for c in chunks:
        if len(c)>16:
            h=len(c)//2;sp=[c[:h],c[h:]]
        else: sp=[c]
        for c2 in sp:
            d=(l['t1']-l['t0'])*len(c2)/n;subs.append(dict(t0=round(t,3),t1=round(t+d+0.08,3),text=c2.rstrip('，。、：；').replace('。','  ')));t+=d
els.append(dict(type='subs',items=subs,y=1610,size=58,hl=['十万','一万匹','不满一万','十比一','八百骑','粮道图','凭什么','白马','颜良','延津','掉头','文丑','六百','官渡','霹雳车','十五天','许攸','一个月','乌巢','点火','贼到了背后','一夜崩了','一个点','一条线','一个仓','一笔现金','一个供应商']))
# ── 镜头（对标四渡赤水：每 4–6 秒一次运动变化，推/漂/环绕交替，地形侧视镜贴近）
cam=[dict(t=0,center=[114.25,35.35],zoom=9.0,pitch=34,bearing=-6,exag=1.3),dict(t=T(1),center=[114.15,35.22],zoom=9.12,pitch=36,bearing=-3,exag=1.3),dict(t=t3,center=[114.12,35.2],zoom=9.18,pitch=38,bearing=0,exag=1.3),
     dict(t=kw(2,'结果',0.3),center=[114.12,35.08],zoom=9.32,pitch=40,bearing=1,exag=1.3,ease='out'),dict(t=kw(2,'只带'),center=[114.2,35.2],zoom=9.22,pitch=40,bearing=2,exag=1.3),dict(t=T(4),center=[114.18,35.12],zoom=9.0,pitch=38,bearing=-2,exag=1.3)]
S=[];S_end=[T(4)];CUR={}
def sh(typ,until,**k):
    S.append(dict(type=typ,dur=round(until-S_end[0],3),**k));S_end[0]=until
    c=k.get('center',k.get('to'));
    if c: CUR.update(center=c)
    for x in('zoom','pitch','bearing','exag'):
        if x in k: CUR[x]=k[x]
def hold(until,**k): sh('hold_drift',until,center=CUR['center'],zoom=CUR['zoom'],pitch=CUR['pitch'],bearing=CUR['bearing'],drift=k.get('drift',1.5),push_in=k.get('pin',0.08),exag=CUR['exag'])
def beat(at,until,dz=0.25,db=4,center=None,dur=1.0,gain=1.8):
    # 对标四渡赤水：快推 ~1s（easeOut）后近乎静止，形成 5–6 秒一次的运动节拍
    hold(at) if at>S_end[0]+0.05 else None
    sh('push_in',min(until,at+dur),center=center or CUR['center'],zoom=CUR['zoom']+dz*gain,pitch=CUR['pitch'],bearing=CUR['bearing']+db*gain,exag=CUR['exag'])
    if until>S_end[0]+0.05: hold(until)
sh('fly_to',T(4)+2.0,to=[115.0,36.9],zoom=6.55,pitch=28,bearing=0,arc=0.25,exag=1.4);hold(T(5))
sh('fly_to',T(5)+1.6,to=BAIMA,zoom=9.9,pitch=55,bearing=-20,arc=0.4,exag=2.0)
sh('orbit',T(6),center=[114.66,35.62],zoom=9.9,pitch=58,deg=-15,move=0.4,exag=2.2);CUR['bearing']=-35
beat(T(6),T(7),dz=0.3,db=-4)
sh('terrain_side',T(8),center=[114.37,35.51],zoom=9.1,pitch=72,bearing=-45,slide_km=8,drift=3,move=1.2,exag=3.4)
sh('push_in',T(8)+1.2,center=[114.50,35.54],zoom=9.5,pitch=72,bearing=-40,exag=3.5);hold(kw(8,'斩了',-0.2),drift=1)
sh('push_in',kw(8,'斩了',0.5),center=[114.58,35.57],zoom=9.8,pitch=72,bearing=-40,exag=3.5);hold(T(9),drift=0.5)
sh('fly_to',T(9)+1.3,to=[114.56,35.55],zoom=9.4,pitch=42,bearing=-10,arc=0.2,exag=1.5);hold(T(10))
beat(T(10),T(11),dz=0.25,db=4);sh('push_in',T(11)+1.2,center=[114.52,35.70],zoom=9.2,pitch=40,bearing=-6,exag=1.5);hold(T(12))
sh('fly_to',T(12)+1.6,to=[114.05,34.85],zoom=10.4,pitch=48,bearing=0,arc=0.3,exag=1.6);hold(T(13));beat(T(13),T(14),dz=0.3,db=4)
sh('terrain_side',T(15),center=[113.99,34.89],zoom=9.7,pitch=72,bearing=-50,slide_km=4,drift=4,move=1.0,exag=3.4)
sh('fly_to',T(15)+1.4,to=[114.0,34.45],zoom=9.0,pitch=36,bearing=0,arc=0.15,exag=1.4);hold(T(16));beat(T(16),T(17),dz=0.2,db=3)
sh('fly_to',T(17)+1.2,to=[114.06,34.80],zoom=10.2,pitch=45,bearing=8,arc=0.1,exag=1.6);hold(T(19));beat(T(19),T(20),dz=0.2,db=-5);beat(T(20),T(21),dz=0.35,db=3,dur=0.6)
sh('push_in',T(21)+1.2,center=[114.06,34.85],zoom=10.8,pitch=62,bearing=12,exag=2.0);hold(T(22));beat(T(22),T(23),dz=0.2,db=-4);beat(T(23),T(24),dz=0.25,db=4,dur=0.7)
sh('fly_to',T(24)+1.2,to=[114.18,34.98],zoom=9.65,pitch=46,bearing=-5,arc=0.2,exag=1.6);hold(T(25));beat(T(25),T(26),dz=0.25,db=-3,center=[114.24,35.04])
sh('terrain_side',T(27),center=[114.14,35.045],zoom=9.2,pitch=72,bearing=-40,slide_km=8,drift=3,move=1.2,exag=3.4)
sh('push_in',T(27)+1.5,center=[114.20,35.10],zoom=9.6,pitch=72,bearing=-38,exag=3.5);hold(T(28),drift=1)
sh('push_in',F+0.15,center=WUCHAO,zoom=10.8,pitch=62,bearing=-20,exag=2.4);hold(F+1.2,drift=0.5)
sh('fly_to',F+2.4,to=[114.18,35.00],zoom=9.75,pitch=44,bearing=-6,arc=0.1,exag=1.6);hold(T(30))
beat(T(30),T(31),dz=0.2,db=4);beat(T(31),T(32),dz=0.2,db=-4)
sh('fly_to',T(32)+1.5,to=[114.32,35.30],zoom=9.0,pitch=40,bearing=-4,arc=0.1,exag=1.4);hold(D,drift=0.5,pin=0.03)
cam+=build_camera(S,start=dict(center=cam[-1]['center'],zoom=cam[-1]['zoom'],pitch=cam[-1]['pitch'],bearing=cam[-1]['bearing']),t0=T(4))[1:]
drums=[0.3,kw(0,'点了'),T(1),t3,kw(2,'结果',0.3),T(3),kw(3,'粮道',-0.4),T(4),T(12),T(21),T(26),F,T(33)-0.3,T(37)+0.9]
txt=''.join(sorted(set(json.dumps(els,ensure_ascii=False))))+'官渡之战十万不满一万输的是那边'
w,h=int(1080*SC),int(1920*SC)
scene=dict(w=w,h=h,designW=1080,fps=FPS,duration=D,camera=cam,fadeIn=0.3,maxPitch=76,
  sky={'fog-ground-blend':0.9,'horizon-fog-blend':0.35,'horizon-color':'#1d3d60'},terrain=dict(exaggeration=1.5,maxzoom=11,occlude=True,occTol=30),light=dict(rim=0.6,rimDir=135,rimColor='rgba(120,200,255,0.55)',volume=0.5,horizonY=0.2),avoid=dict(on=True,pad=14,margin=24),
  basemap=dict(brightness=0.72,hillshadeExag=0.7,saturation=-0.35,contrast=0.25,vignette=0.7,tint='#06142a',tintOpacity=0.18),elements=els,text=txt,drums=drums,
  cover=dict(t=round(F-0.5,3),lines=[dict(text='官渡之战',size=150,y=330,color='#fff',glow='#C8102E',stroke=18),dict(text='十万 vs 不满一万',size=84,y=500,color=YEL,glow='#000',stroke=14),dict(text='输的，是十万那边',size=76,y=1580,color='#fff',glow='#000',stroke=12,bg='rgba(200,16,46,0.92)')]))
json.dump(scene,open(f'{W}/scene.json','w'),ensure_ascii=False);json.dump(dict(w=w,h=h,fps=FPS,frames=int(round(D*FPS)),duration=D),open(f'{W}/meta.json','w'))
# 给 sfx.py 的映射版（新图层 → 已有音效）
M=[]
for e in els:
    k=e['type']
    if k=='seal':M.append(dict(type='slam',t0=e['t0']+0.4))
    elif k=='quote':M+= [dict(type='chip',t0=e['t0']),dict(type='chip',t0=e['t0']+0.08)]
    elif k=='geo':M+= [dict(type='qmark',t0=e['tn']),dict(type='route',color='#2E8BFF',draw=[e['tl'],e['tl']+1.0]),dict(type='route',color='#C8102E',draw=[e['ta'],e['ta']+0.9]),dict(type='impact',t=e['tb'],scale=1.0)]+[dict(type='qmark',t0=l['t']) for l in e['labels'][1:]]
    elif k=='endcard':M.append(dict(type='slam',t0=e['t0']+1.0))
    elif k in('veil','subs'):pass
    else:M.append(e)
json.dump(dict(scene,elements=M),open(f'{W}/scene_sfx.json','w'),ensure_ascii=False)
print(ID,'D',D,'frames',int(round(D*FPS)),'cam',len(cam),'subs',len(subs),'cover_t',scene['cover']['t'])

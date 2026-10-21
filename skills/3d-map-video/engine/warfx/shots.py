#!/usr/bin/env python3
"""WarFX 镜头库（1021b）：把旧 3D 模板 compile.py 的镜头（globe_dive / hold_drift / fly_to / orbit / terrain_side / push_in）
换算成 warfx scene.json 的 camera 关键帧（每 0.1s 一个，ease=linear，exag 按缩放取 compile.EXAG_BY_ZOOM，可在 shot 里写 exag 覆盖）。
数学与 compile.py 同源（ease/lerp/interp_tab/EXAG_BY_ZOOM 直接 import），保证井陉/淝水/台州用过的手感一致。
用法：from shots import build_camera; cam=build_camera(shots, start=dict(center=[lon,lat],zoom=9,pitch=40,bearing=0), pts={'BM':[114.7,35.56]})
shot 字段：
  hold_drift  center zoom pitch bearing drift(°) push_in(级)    —— 定点慢漂 + 结尾推近
  push_in     center zoom(目标) pitch bearing                    —— 推近（easeOut，侧视推进用）
  fly_to      to zoom pitch bearing arc                          —— 抛物线飞越
  orbit       center zoom pitch deg move                         —— 环绕（deg 正=顺时针）
  terrain_side center zoom pitch bearing slide_km drift move     —— 侧视贴山横移（pitch 60–75）
  globe_dive  target from start_zoom end_zoom end_pitch          —— 地球俯冲开场（scene 需 projection='globe'）
"""
import math,os,sys
sys.path.insert(0,os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from compile import ease,lerp,interp_tab,EXAG_BY_ZOOM
DT=0.1
def build_camera(shots,start,pts=None,t0=0.0,exag_gain=1.0):
    pts=pts or {};P=lambda v:pts[v] if isinstance(v,str) else v
    cam=dict(lon=start['center'][0],lat=start['center'][1],zoom=start['zoom'],pitch=start.get('pitch',0),bearing=start.get('bearing',0));K=[];t=t0
    def push(tt,c,ex):K.append(dict(t=round(tt,3),center=[round(c['lon'],6),round(c['lat'],6)],zoom=round(c['zoom'],4),pitch=round(c['pitch'],3),bearing=round(c['bearing'],3),ease='linear',exag=round(ex if ex is not None else interp_tab(EXAG_BY_ZOOM,c['zoom'])*exag_gain,3)))
    for s in shots:
        typ=s['type'];dur=s['dur'];c0=dict(cam);ex=s.get('exag')
        if typ=='globe_dive':
            tg=P(s['target']);fr=s.get('from',[tg[0]-14,tg[1]-10]);z0=s.get('start_zoom',1.45);z1=s.get('end_zoom',8.4);k=2**(z0-z1)
            def f(u):
                e=ease(u);z=lerp(z0,z1,e);w=(2**(z0-z)-k)/(1-k)
                return dict(lon=tg[0]+(fr[0]-tg[0])*w,lat=tg[1]+(fr[1]-tg[1])*w,zoom=z,pitch=s.get('end_pitch',45)*e**2,bearing=s.get('end_bearing',0)*e)
        elif typ in('hold_drift','fly_to','push_in'):
            to=P(s.get('center',s.get('to',[c0['lon'],c0['lat']])))
            c1=dict(lon=to[0],lat=to[1],zoom=s.get('zoom',c0['zoom']),pitch=s.get('pitch',c0['pitch']),bearing=s.get('bearing',c0['bearing']))
            arc=s.get('arc',1.5 if typ=='fly_to' else 0);drift=s.get('drift',6 if typ=='hold_drift' else 0)
            def f(u,c0=c0,c1=c1,arc=arc,drift=drift,typ=typ):
                if typ=='push_in':e=1-(1-u)**3
                elif typ=='fly_to':e=ease(u)
                else:e=ease(min(1,u/0.35)) if (c0['lon'],c0['lat'])!=(c1['lon'],c1['lat']) else 1
                pin=s.get('push_in',0.5 if c1['zoom']>=8 else 0.2)*ease(u) if typ=='hold_drift' else 0
                return dict(lon=lerp(c0['lon'],c1['lon'],e),lat=lerp(c0['lat'],c1['lat'],e),zoom=lerp(c0['zoom'],c1['zoom'],e)-arc*math.sin(math.pi*u)+pin,pitch=lerp(c0['pitch'],c1['pitch'],e),bearing=lerp(c0['bearing'],c1['bearing'],e)+drift*u)
        elif typ=='orbit':
            ce=P(s['center']);mv=s.get('move',min(1.5,dur*0.4));deg=s.get('deg',90);c1=dict(lon=ce[0],lat=ce[1],zoom=s.get('zoom',c0['zoom']),pitch=s.get('pitch',62))
            def f(u,c0=c0,c1=c1,mv=mv,deg=deg,dur=dur):
                e=ease(min(1,u*dur/mv)) if mv>0 else 1
                return dict(lon=lerp(c0['lon'],c1['lon'],e),lat=lerp(c0['lat'],c1['lat'],e),zoom=lerp(c0['zoom'],c1['zoom'],e),pitch=lerp(c0['pitch'],c1['pitch'],e),bearing=c0['bearing']+deg*(0.5*u+0.5*(0.5-0.5*math.cos(math.pi*u))))
        elif typ=='terrain_side':
            ce=P(s['center']);br=s.get('bearing',c0['bearing']);sk=s.get('slide_km',6.0);mv=s.get('move',min(1.2,dur*0.3));dr=math.radians(br+90);kx=111.32*math.cos(math.radians(ce[1]))
            p0=[ce[0]-sk/2*math.sin(dr)/kx,ce[1]-sk/2*math.cos(dr)/110.54];p1=[ce[0]+sk/2*math.sin(dr)/kx,ce[1]+sk/2*math.cos(dr)/110.54];z=s.get('zoom',11.6);pc=s.get('pitch',70)
            def f(u,c0=c0,p0=p0,p1=p1,z=z,pc=pc,br=br,mv=mv,dur=dur):
                tt=u*dur
                if tt<mv:
                    e=ease(tt/mv);b=c0['bearing']+((br-c0['bearing']+180)%360-180)*e
                    return dict(lon=lerp(c0['lon'],p0[0],e),lat=lerp(c0['lat'],p0[1],e),zoom=lerp(c0['zoom'],z,e),pitch=lerp(c0['pitch'],pc,e),bearing=b)
                v=(tt-mv)/max(1e-6,dur-mv);v=0.5*v+0.5*ease(v)
                return dict(lon=lerp(p0[0],p1[0],v),lat=lerp(p0[1],p1[1],v),zoom=z,pitch=pc,bearing=br+s.get('drift',4)*v)
        else: raise ValueError('未知镜头 '+typ)
        n=max(2,int(round(dur/DT)))
        for i in range(n+1):
            c=f(i/n)
            if K and i==0 and abs(K[-1]['t']-t)<1e-6: continue
            push(t+dur*i/n,c,ex)
        cam=c;t+=dur
    return K

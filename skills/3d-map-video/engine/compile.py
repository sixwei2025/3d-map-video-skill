#!/usr/bin/env python3
"""episode.json -> work/<id>/{scene.json, comp.svml, look.svs, run.svrun, audio.json, meta.json}
镜头库：globe_dive / hold_drift / fly_to / route_fly / orbit / terrain_side / pull_out
标注：pin / label / line / area / distance。配色：品牌红 #C8102E（main）、青 #2FE0E6（city/region）、黄 #FFD84A（value）。"""
import json, math, sys, os
from xml.sax.saxutils import escape

ROLE = {  # 点/框/线主色, 发光色, 线芯色
  'main':   ('#C8102E', 'rgba(200,16,46,0.85)', '#C8102E'),   # v3：主题线 = 品牌红实色（scene 内另叠一道浅色线芯）
  'city':   ('#2FE0E6', 'rgba(47,224,230,0.80)', '#B8FBFF'),
  'region': ('#2FE0E6', 'rgba(47,243,255,0.85)', '#B8FBFF'),
  'value':  ('#FFD84A', 'rgba(255,225,74,0.85)', '#FFF07A'),
  'river':  ('#6CF07A', 'rgba(80,255,90,0.85)', '#9DFF7A'),
  'white':  ('#FFFFFF', 'rgba(255,255,255,0.6)', '#FFFFFF'),
  # 阵营双色（v2 模板固定）：A 阵营（如明军）冷色系四路 + 'a' 主色；B 阵营（如后金/胜方）= 品牌红。
  'w':      ('#3D7DDB', 'rgba(61,125,219,0.85)', '#A6C8FF'),
  'n':      ('#4FB0C6', 'rgba(79,176,198,0.85)', '#A9E4EF'),
  'e':      ('#7B6FE6', 'rgba(123,111,230,0.85)', '#BDB5FF'),
  's':      ('#A9B6C6', 'rgba(169,182,198,0.80)', '#E6EBF1'),
  'a':      ('#3D7DDB', 'rgba(61,125,219,0.85)', '#A6C8FF'),
  'enemy':  ('#C8102E', 'rgba(230,20,50,0.90)', '#FF3B55'),
  'b':      ('#C8102E', 'rgba(230,20,50,0.90)', '#FF3B55'),
}
ROLE.update({'a1': ROLE['w'], 'a2': ROLE['n'], 'a3': ROLE['e'], 'a4': ROLE['s']})
LINE_SCALE = 0.62  # v3：线整体变细（对标真实河道细线；v2 为 1.3）。episode 写的 width 不变，模板统一换算
# ---- v3 画面升级参数（模板固定，量产只换数据）----
PITCH_CAP = [(6, 30), (8, 42), (11, 52), (13, 62)]   # 按缩放级别限制俯仰：露地平线/远处糊（terrain_side 例外）
BEARING_RATE = {'default': 10.0, 'orbit': 20.0, 'terrain_side': 20.0}   # 转向限速 °/秒
BEARING_SMOOTH_S = 1.5    # 转向零相位低通时间常数（秒）
ROUTE_BEARING_MAX = 60    # route_fly 默认朝向 = 路线总方向，限制在 ±60°（尽量北朝上）
PUSH_IN = (0.5, 0.2)      # hold_drift 结尾再拉近：zoom≥8 拉 0.5 级，远景拉 0.2 级
SNAP_TOL_KM = 12.0        # 河道吸附：一段的两个端点都离真实河道 ≤12km 才吸附
SMOOTH_STEP_KM = 2.0      # 未吸附段 Catmull-Rom 平滑后每 2km 一个点
EXAG_BY_ZOOM = [(8, 1.3), (11, 1.6), (13, 2.0)]   # 分镜头地形夸张：按相机缩放插值；shot 可写 exag 覆盖
AREA_FILL_GAIN = 1.8      # 区域面透明度增益（上限 0.55，红 0.42）
LABEL_SCALE = 1.6         # 地图上 pin/label 字号倍数（HUD 不变）
SCALE_RULE = 18.0  # v2：任意 18 秒窗口内至少出现 2 种景别（远/中/近 × 俯/斜/侧），否则告警
# v4（2026-10-20b）「三维地图看世界」复刻：episode.style='sanwei' 时换霓虹配色、线更粗、区域面更实
SW_ROLE = {'main': ('#FF2A3D', 'rgba(255,40,60,0.95)', '#FF8A96'), 'city': ('#19E3FF', 'rgba(25,227,255,0.95)', '#C8F8FF'),
  'region': ('#19E3FF', 'rgba(25,227,255,0.95)', '#C8F8FF'), 'value': ('#FFE14A', 'rgba(255,225,74,0.95)', '#FFF5B8'),
  'river': ('#39FF5A', 'rgba(57,255,90,0.95)', '#D2FFD9'), 'white': ('#FFFFFF', 'rgba(255,255,255,0.7)', '#FFFFFF')}
SW_LINE_SCALE = 0.95; SW_AREA_CAP = 0.62
ASPECT = {'9x16': (1080, 1920, -0.45), '16x9': (1920, 1080, 0.0)}
ease = lambda x: 4*x*x*x if x < .5 else 1-(-2*x+2)**3/2
lerp = lambda a, b, t: a+(b-a)*t

def _km(a, b):
    k = math.cos(math.radians((a[1]+b[1])/2)); return 111.2*math.hypot((a[0]-b[0])*k, a[1]-b[1])

def _nearest(G, p):
    best = (1e18, 0, None)
    for i in range(len(G)-1):
        a, b = G[i], G[i+1]; k = math.cos(math.radians(a[1])); ax, ay, bx, by, px, py = a[0]*k, a[1], b[0]*k, b[1], p[0]*k, p[1]
        dx, dy = bx-ax, by-ay; L2 = dx*dx+dy*dy or 1e-18; u = max(0, min(1, ((px-ax)*dx+(py-ay)*dy)/L2))
        q = [a[0]+(b[0]-a[0])*u, a[1]+(b[1]-a[1])*u]; d = _km(q, p)
        if d < best[0]: best = (d, i+u, q)
    return best

def _sub(G, s0, s1):
    """真实河道 G 上从参数 s0 到 s1（段号+比例）的子折线，支持反向。"""
    rev = s1 < s0; a, b = (s1, s0) if rev else (s0, s1)
    at = lambda s: [G[int(s)][0]+(G[min(int(s)+1, len(G)-1)][0]-G[int(s)][0])*(s-int(s)), G[int(s)][1]+(G[min(int(s)+1, len(G)-1)][1]-G[int(s)][1])*(s-int(s))]
    out = [at(a)] + [G[i] for i in range(int(a)+1, int(b)+1) if i < b] + [at(b)]
    return out[::-1] if rev else out

def _cr(p0, p1, p2, p3, n):
    """centripetal Catmull-Rom，p1→p2 之间 n 个点（不含 p1，含 p2）"""
    def tj(ti, a, b): return ti + max(1e-9, math.hypot(b[0]-a[0], b[1]-a[1]))**0.5
    t0 = 0; t1 = tj(t0, p0, p1); t2 = tj(t1, p1, p2); t3 = tj(t2, p2, p3); out = []
    for k in range(1, n+1):
        t = t1+(t2-t1)*k/n
        def L(a, b, ta, tb): return [(tb-t)/(tb-ta)*a[0]+(t-ta)/(tb-ta)*b[0], (tb-t)/(tb-ta)*a[1]+(t-ta)/(tb-ta)*b[1]]
        A1, A2, A3 = L(p0, p1, t0, t1), L(p1, p2, t1, t2), L(p2, p3, t2, t3); B1, B2 = L(A1, A2, t0, t2), L(A2, A3, t1, t3)
        out.append(L(B1, B2, t1, t2))
    return out

SHARP_TURN = 65.0   # 节点转角大于此值时该侧不做曲线外甩

def _turn(a, b, c):
    k = math.cos(math.radians(b[1])); u = ((b[0]-a[0])*k, b[1]-a[1]); v = ((c[0]-b[0])*k, c[1]-b[1])
    if not any(u) or not any(v): return 0
    return abs((math.degrees(math.atan2(v[1], v[0])-math.atan2(u[1], u[0]))+180) % 360-180)

def shape_line(pts, snaps, smooth=True):
    """v3 线几何：①相邻两节点都贴近某条真实河道 → 用真实河道子段（吸附）；②其余段 Catmull-Rom 平滑、每 2km 加点。节点本身保留。"""
    if len(pts) < 2: return pts
    out = [list(pts[0])]; info = []
    for i in range(len(pts)-1):
        p, q = pts[i], pts[i+1]; done = False
        for sn in snaps:
            dp, sp, _ = _nearest(sn['g'], p); dq, sq, _ = _nearest(sn['g'], q)
            if dp <= SNAP_TOL_KM and dq <= SNAP_TOL_KM and abs(sq-sp) > 1e-6:
                out += _sub(sn['g'], sp, sq)[1:] + [list(q)]; info.append(sn['name']); done = True; break
        if done: continue
        if smooth:
            p0 = pts[i-1] if i > 0 else [2*p[0]-q[0], 2*p[1]-q[1]]; p3 = pts[i+2] if i+2 < len(pts) else [2*q[0]-p[0], 2*q[1]-p[1]]
            if _turn(p0, p, q) > SHARP_TURN: p0 = [2*p[0]-q[0], 2*p[1]-q[1]]   # 急弯不平滑（防止甩出去）
            if _turn(p, q, p3) > SHARP_TURN: p3 = [2*q[0]-p[0], 2*q[1]-p[1]]
            n = max(1, int(_km(p, q)/SMOOTH_STEP_KM)); out += _cr(p0, p, q, p3, n)
        else: out.append(list(q))
    return [[round(x, 5), round(y, 5)] for x, y in out]

def interp_tab(tab, z):
    if z <= tab[0][0]: return tab[0][1]
    for (z0, v0), (z1, v1) in zip(tab, tab[1:]):
        if z <= z1: return v0+(v1-v0)*(z-z0)/(z1-z0)
    return tab[-1][1]

def main(ep_path, aspect_override=None, engine='v2'):
    ep = json.load(open(ep_path, encoding='utf-8'))
    global LINE_SCALE
    SW = ep.get('style') == 'sanwei'
    if SW: ROLE.update(SW_ROLE); LINE_SCALE = SW_LINE_SCALE
    aspect = aspect_override or ep.get('aspect', '9x16')
    W, H, zoff = ASPECT[aspect]; zoff = ep.get('zoom_offset', {}).get(aspect, zoff) if isinstance(ep.get('zoom_offset'), dict) else zoff
    fps = ep.get('fps', 30); step = ep.get('render_step', 2)
    P = {k: (v['lonlat'] if isinstance(v, dict) else v) for k, v in ep.get('places', {}).items()}
    pt = lambda x: P[x] if isinstance(x, str) else x
    routes = ep.get('routes', {})
    SNAPS = []
    for sn in ep.get('snaps', []):   # v3 真实河道吸附：[{file, name?}]，GeoJSON LineString/Feature
        g = json.load(open(sn['file'], encoding='utf-8')); props = g.get('properties', {}); g = g.get('geometry', g)
        SNAPS.append(dict(g=g['coordinates'], name=sn.get('name', props.get('name', sn['file']))))
    def coords_of(a, shape=True):
        c = _coords_of(a)
        return shape_line(c, SNAPS if a.get('snap', True) else [], smooth=a.get('smooth', True)) if shape and len(c) > 2 or (shape and len(c) == 2 and SNAPS) else c
    def _coords_of(a):
        if 'coords' in a: return [pt(c) for c in a['coords']]
        if 'places' in a: return [pt(c) for c in a['places']]
        if 'route' in a:
            r = routes[a['route']]
            if 'file' in r:
                g = json.load(open(r['file'], encoding='utf-8')); g = g['features'][0]['geometry'] if 'features' in g else g.get('geometry', g)
                return g['coordinates']
            return [pt(c) for c in r['coords']]
        raise ValueError('line needs coords/places/route')

    # ---------------- camera ----------------
    keys = []; t = 0.0
    cam = dict(lon=ep.get('start', [100, 25])[0], lat=ep.get('start', [100, 25])[1], zoom=1.45, pitch=0, bearing=0)
    if ep.get('start_cam'): cam = dict(ep['start_cam'])  # 首帧直接是地形全景（不从地球俯冲）
    ktype = []; cur_typ = ['']
    def push(tt, c, e='lin'): keys.append([round(tt, 4), c['lon'], c['lat'], c['zoom'], c['pitch'], c['bearing'], e]); ktype.append(cur_typ[0])
    DT = 0.1
    def sample(dur, fn):
        n = max(2, int(round(dur/DT)))
        for i in range(n+1):
            c = fn(i/n)
            if not (keys and i == 0 and abs(keys[-1][0]-t) < 1e-6): push(t+dur*i/n, c)
        return c
    auto_lines = []; sfx_whoosh = []; shot_log = []
    for s in ep['shots']:
        typ = s['type']; dur = s['dur']; c0 = dict(cam); cur_typ[0] = typ
        if typ == 'globe_dive':
            tg = pt(s['target']); fr = s.get('from', [tg[0]-14, tg[1]-10]); z0 = s.get('start_zoom', 1.45); z1 = s.get('end_zoom', 8.4)
            c0 = dict(lon=fr[0], lat=fr[1], zoom=z0, pitch=0, bearing=0)
            k = 2**(z0-z1)
            def f(u, tg=tg, fr=fr, z0=z0, z1=z1, k=k):
                e = ease(u); z = lerp(z0, z1, e); w = (2**(z0-z) - k)/(1-k)
                return dict(lon=tg[0]+(fr[0]-tg[0])*w, lat=tg[1]+(fr[1]-tg[1])*w, zoom=z, pitch=s.get('end_pitch', 45)*(e**2), bearing=s.get('end_bearing', 0)*e)
            sfx_whoosh.append(t)
            cam = sample(dur, f)
        elif typ in ('hold_drift', 'fly_to'):
            to = pt(s['center'] if 'center' in s else s['to']) if ('center' in s or 'to' in s) else [c0['lon'], c0['lat']]
            c1 = dict(lon=to[0], lat=to[1], zoom=s.get('zoom', c0['zoom']), pitch=s.get('pitch', c0['pitch']), bearing=s.get('bearing', c0['bearing']))
            arc = s.get('arc', 1.5 if typ == 'fly_to' else 0); drift = s.get('drift', 6 if typ == 'hold_drift' else 0)
            if typ == 'fly_to': sfx_whoosh.append(t)
            def f(u, c0=c0, c1=c1, arc=arc, drift=drift, typ=typ):
                e = ease(u) if typ == 'fly_to' else ease(min(1, u/0.35)) if (c0['lon'], c0['lat']) != (c1['lon'], c1['lat']) else 1
                pin = (s.get('push_in', PUSH_IN[0] if c1['zoom'] >= 8 else PUSH_IN[1]) * ease(u)) if typ == 'hold_drift' else 0
                return dict(lon=lerp(c0['lon'], c1['lon'], e), lat=lerp(c0['lat'], c1['lat'], e), zoom=lerp(c0['zoom'], c1['zoom'], e)-arc*math.sin(math.pi*u)+pin,
                            pitch=lerp(c0['pitch'], c1['pitch'], e), bearing=lerp(c0['bearing'], c1['bearing'], e)+drift*u)
            cam = sample(dur, f)
        elif typ == 'route_fly':
            pts = coords_of(s); kx = math.cos(math.radians(sum(p[1] for p in pts)/len(pts)))
            seg = [math.hypot((b[0]-a[0])*kx, b[1]-a[1]) for a, b in zip(pts, pts[1:])]; L = sum(seg)
            def at(d):
                d = max(0, min(L, d))
                for (a, b), l in zip(zip(pts, pts[1:]), seg):
                    if d <= l or l == seg[-1] and d <= l+1e-12: r = d/l if l else 0; return [lerp(a[0], b[0], r), lerp(a[1], b[1], r)]
                    d -= l
                return pts[-1]
            la = s.get('lookahead', 0.08)*L; mv = s.get('move', 1.0); z = s.get('zoom', 9); pc = s.get('pitch', 58); prev = [c0['bearing']]
            bmode = s.get('bearing', 'route')
            rb = math.degrees(math.atan2((pts[-1][0]-pts[0][0])*kx, pts[-1][1]-pts[0][1])); rb = max(-ROUTE_BEARING_MAX, min(ROUTE_BEARING_MAX, (rb+180) % 360-180))
            def brg(d):
                if bmode == 'route': return rb
                a, b = at(d-la*0.3), at(d+la); return math.degrees(math.atan2((b[0]-a[0])*kx, b[1]-a[1]))
            def f(u, mv=mv, dur=dur):
                tt = u*dur
                if tt < mv:  # approach to route start
                    e = ease(tt/mv); p = at(0); b = brg(0) if bmode in ('auto', 'route') else bmode
                    b = prev[0]+((b-prev[0]+180) % 360-180)*e
                    return dict(lon=lerp(c0['lon'], p[0], e), lat=lerp(c0['lat'], p[1], e), zoom=lerp(c0['zoom'], z, e), pitch=lerp(c0['pitch'], pc, e), bearing=b)
                v = ease((tt-mv)/(dur-mv)); d = v*L; p = at(d)
                b = brg(d) if bmode in ('auto', 'route') else bmode
                b = prev[0]+((b-prev[0]+180) % 360-180)*0.35; prev[0] = b  # 平滑转向
                return dict(lon=p[0], lat=p[1], zoom=z, pitch=pc, bearing=b)
            if s.get('draw', True):
                auto_lines.append(dict(type='line', coords=pts, role=s.get('role', 'main'), t=[t+mv, t+dur+s.get('hold_line', 99)], draw=[t+mv, t+dur]))
            sfx_whoosh.append(t)
            cam = sample(dur, f)
        elif typ == 'orbit':
            ce = pt(s['center']); mv = s.get('move', min(1.5, dur*0.4)); deg = s.get('deg', 90)
            c1 = dict(lon=ce[0], lat=ce[1], zoom=s.get('zoom', 14.5), pitch=s.get('pitch', 62))
            def f(u, c0=c0, c1=c1, mv=mv, deg=deg, dur=dur):
                e = ease(min(1, u*dur/mv)) if mv > 0 else 1
                return dict(lon=lerp(c0['lon'], c1['lon'], e), lat=lerp(c0['lat'], c1['lat'], e), zoom=lerp(c0['zoom'], c1['zoom'], e),
                            pitch=lerp(c0['pitch'], c1['pitch'], e), bearing=c0['bearing']+deg*(0.5*u+0.5*(0.5-0.5*math.cos(math.pi*u))))
            cam = sample(dur, f)
        elif typ == 'terrain_side':  # 地形侧视：低角度（pitch 75–80）贴着山脊横移，交代山口/关隘/河谷
            ce = pt(s['center']); br = s.get('bearing', c0['bearing']); sk = s.get('slide_km', 6.0); mv = s.get('move', min(1.2, dur*0.3))
            dr = math.radians(br+90); kx = 111.32*math.cos(math.radians(ce[1]))
            p0 = [ce[0]-sk/2*math.sin(dr)/kx, ce[1]-sk/2*math.cos(dr)/110.54]; p1 = [ce[0]+sk/2*math.sin(dr)/kx, ce[1]+sk/2*math.cos(dr)/110.54]
            z = s.get('zoom', 11.6); pc = s.get('pitch', 77)
            def f(u, c0=c0, p0=p0, p1=p1, z=z, pc=pc, br=br, mv=mv, dur=dur):
                tt = u*dur
                if tt < mv:
                    e = ease(tt/mv); b = c0['bearing']+((br-c0['bearing']+180) % 360-180)*e
                    return dict(lon=lerp(c0['lon'], p0[0], e), lat=lerp(c0['lat'], p0[1], e), zoom=lerp(c0['zoom'], z, e), pitch=lerp(c0['pitch'], pc, e), bearing=b)
                v = (tt-mv)/max(1e-6, dur-mv); v = 0.5*v+0.5*ease(v)
                return dict(lon=lerp(p0[0], p1[0], v), lat=lerp(p0[1], p1[1], v), zoom=z, pitch=pc, bearing=br+s.get('drift', 4)*v)
            sfx_whoosh.append(t)
            cam = sample(dur, f)
        elif typ == 'pull_out':
            fr = s.get('to', [c0['lon']+20, c0['lat']-8]); z1 = s.get('end_zoom', 1.6); z0 = c0['zoom']; k = 2**(z1-z0)
            def f(u, c0=c0, fr=fr, z0=z0, z1=z1, k=k):
                e = ease(u); z = lerp(z0, z1, e); w = max(0, min(1, (2**(z0-z)-1)/(2**(z0-z1)-1)))
                return dict(lon=lerp(c0['lon'], fr[0], w), lat=lerp(c0['lat'], fr[1], w), zoom=z, pitch=c0['pitch']*(1-e), bearing=c0['bearing']*(1-e))
            sfx_whoosh.append(t)
            cam = sample(dur, f)
        else:
            raise ValueError('未知镜头类型 '+typ+'（v0 未实现 compare_split / era_morph）')
        shot_log.append((t, dur, typ, cam['zoom'], cam['pitch']))
        t += dur
    D = round(t, 3)
    scale_check(shot_log)
    for k in keys: k[3] = round(k[3]+zoff*min(1, max(0, (k[3]-1.5)/3)), 4)  # 画幅缩放补偿；地球远景不缩
    camera_rules(keys, ktype)
    exag_keys = []   # v3 分镜头地形夸张 [t, ex]
    shot_ex = []; tt = 0.0
    for s in ep['shots']: shot_ex.append((tt, tt+s['dur'], s.get('exag'))); tt += s['dur']
    for k in keys[::3]:
        ov = next((e for a, b, e in shot_ex if a <= k[0] < b and e), None)
        exag_keys.append([k[0], round(ov or interp_tab(EXAG_BY_ZOOM, k[3])*ep.get('terrain_exaggeration', 1.3)/1.3, 3)])

    # ---------------- annotations ----------------
    lines, areas, pins, labels, pops, gts, gts_w = [], [], [], [], [], [], []
    for i, a in enumerate(ep.get('annotations', [])+auto_lines):
        ty = a['type']; r = ROLE[a.get('role', 'main')]; t0, t1 = a.get('t', [0, D])
        if ty == 'pin':
            pins.append(dict(at=pt(a['place']), text=a['text'], sub=a.get('sub'), color=r[0], t0=t0, t1=t1, dx=a.get('dx', 46), dy=a.get('dy', -80))); pops.append(t0)
        elif ty == 'label':
            labels.append(dict(at=pt(a.get('place', a.get('at'))), text=a['text'], size=a.get('size', 36), color=a.get('color', r[0] if a.get('role') else '#FFFFFF'), box=a.get('box', False), t0=t0, t1=t1)); pops.append(t0)
        elif ty == 'line':
            lines.append(dict(id=f'l{i}', coords=coords_of(a), glow=r[1], core=r[2], width=round(max(2.5, a.get('width', 7)*LINE_SCALE*(1.15 if aspect == '9x16' else 1.0)), 2), t0=t0, t1=t1, draw=a.get('draw', [t0, t0+1.2]), dash=a.get('dash', False), head=a.get('head', False), dim=a.get('dim'), tip=a.get('tip', not a.get('head', False)), hi=a.get('role', 'main') == 'main'))
        elif ty == 'ground_text':   # v3 地面发光大字：贴地（随地形起伏）、按镜头朝向自动转正
            tm = (t0+t1)/2; kb = min(keys, key=lambda k: abs(k[0]-tm))[5] if keys else 0
            gts.append(dict(id=f'g{i}', at=pt(a.get('place', a.get('at'))), text=a['text'], width_km=a.get('width_km', 40), color=a.get('color', r[0]), glow=a.get('glow', r[1]), rot=a.get('rot', kb), t0=t0, t1=t1))
        elif ty == 'wall':   # v3 光墙：沿区域边界的竖向渐变发光围栏（fill-extrusion 三层叠出渐变）
            gts_w.append(dict(id=f'w{i}', ring=wall_ring(a, pt), color=a.get('color', r[0]), height_m=a.get('height_m', 2400), width_m=a.get('width_m', 0), t0=t0, t1=t1))
        elif ty == 'distance':
            # v2 距离标注：两点之间白色虚线（不带箭头）+ 两端圆点 + 中点黄色数值框
            A, B = pt(a['a']), pt(a['b']); r = ROLE[a.get('role', 'value')]
            lines.append(dict(id=f'l{i}', coords=[A, B], glow='rgba(255,255,255,0.55)', core='#FFFFFF', width=4.5, t0=t0, t1=t1, draw=[t0, t0+0.9], dash=True, head=False, ends=True))
            at = a.get('at', [(A[0]+B[0])/2, (A[1]+B[1])/2])
            labels.append(dict(at=pt(at), text=a['label'], size=a.get('size', 34), color=r[0], box=True, t0=t0+0.7, t1=t1)); pops.append(t0+0.7)
        elif ty == 'area':
            if 'circle' in a:
                c = pt(a['circle']['place']); rm = a['circle']['radius_m']
                ring = [[c[0]+rm/(111320*math.cos(math.radians(c[1])))*math.cos(2*math.pi*j/72), c[1]+rm/110540*math.sin(2*math.pi*j/72)] for j in range(73)]
                src = {'type': 'Feature', 'geometry': {'type': 'Polygon', 'coordinates': [ring]}}
            else: src = a['file']
            f0 = a.get('fill', 0.30)*AREA_FILL_GAIN; f0 = min(f0, (SW_AREA_CAP if SW else (0.42 if r[0] == '#C8102E' else 0.55)))
            areas.append(dict(id=f'a{i}', src=src, color=r[0], glow=r[1], core=r[2], fill=round(f0, 3), pulse=a.get('pulse', False), spot=a.get('spot', True), t0=t0, t1=t1))
            if a.get('wall'): gts_w.append(dict(id=f'w{i}', ring=wall_ring(a, pt), color=r[0], height_m=a['wall'] if isinstance(a['wall'], (int, float)) and a['wall'] is not True else 2400, width_m=0, t0=t0, t1=t1))
    out = os.path.join('work' if engine == 'v1' else 'work/v2', ep['id'] + ('' if aspect == ep.get('aspect', '9x16') else '_'+aspect)); os.makedirs(out+'/audio', exist_ok=True)
    tex = ep.get('terrain_exaggeration', 1.5)
    scene = dict(w=W, h=H, fps=fps, duration=D, terrain=dict(exaggeration=tex, min_zoom=4.6), keys=keys, lines=lines, areas=areas, pins=pins, labels=labels,
                 scale=1.0 if aspect == '16x9' else 1.15, brand=ep.get('brand', ''), imagery=ep.get('imagery', 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}'),
                 dem=ep.get('dem', 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png'),
                 dem_maxzoom=ep.get('dem_maxzoom', 12 if engine == 'v2' else 14),
                 v3=dict(label_scale=LABEL_SCALE, exag=exag_keys, ground=gts, walls=gts_w, hillshade=ep.get('hillshade', True),
                         context=context_layer(ep, keys)))
    if engine == 'v2':  # 字幕/片名/面板/来源注记直接画进地图页面（DOM），版式与原 Hypit look 一致
        V = aspect == '9x16'
        scene['layout'] = dict(title=(6, 9, 94, 22) if V else (10, 5, 90, 25), sub=(4, 66, 96, 76) if V else (0, 86, 100, 95.5), counter=(56, 4.0, 96, 11.0) if V else (78, 4, 98, 14), chips=(4, 11.8, 96, 15.6) if V else (2, 4, 50, 10), card=(12, 44, 88, 60) if V else (30, 30, 70, 55),
            panel=(5, 24, 72, 50) if V else (2.6, 19, 29.5, 67), credit=(4, 1.6, 97, 3.4) if V else (30, 96.4, 99.2, 99.6),
            sizes=dict(sub=54 if V else 50, title=112 if V else 120, titlesub=44 if V else 42, panel=34 if V else 31, panelhead=42 if V else 40, credit=18 if V else 17))
        scene['title'] = dict(ep['title'], t=ep['title'].get('t', [0.2, 3.2])) if ep.get('title') else None
        # v3.1 顶部章节进度条（engine/progressbar.py 在编码时叠加）：episode.chapters=[{title, shot}]，时间按分镜起点自动算
        if ep.get('chapters'):
            st = [0.0]
            for sh in ep['shots']: st.append(st[-1] + sh['dur'])
            D = scene['duration']; ch = ep['chapters']
            scene['chapters'] = [dict(title=c['title'], t0=round(st[c['shot']], 3), t1=round(st[ch[k+1]['shot']] if k+1 < len(ch) else D, 3)) for k, c in enumerate(ch)]
            if V:  # 给进度条（距顶 ~5–7.5%）让出顶部：计数器/章节条/片名下移
                L = scene['layout']; L['counter'] = (56, 8.6, 96, 15.6); L['chips'] = (4, 16.4, 96, 20.2); L['title'] = (6, 10.5, 94, 23.5)
        scene['captions'] = ep.get('captions', []); scene['panel'] = ep.get('panel')
        scene['counter'] = ep.get('counter', []); scene['cards'] = ep.get('cards', [])
        scene['chips'] = dict(ep['chips'], items=[dict(c, color=ROLE[c.get('role', 'main')][0]) for c in ep['chips']['items']]) if ep.get('chips') else None
        scene['moods'] = ep.get('moods', [])       # v2 段落天气/调色层：[{t0,t1,preset,strength}]，预设在 scene.html
        scene['dim'] = ep.get('focus_dim', 0.35)     # v2 数字卡出现时地图压暗比例
        scene['credit'] = ep.get('credit', '影像 © Esri, Maxar, Earthstar Geographics · 地形 AWS Terrain Tiles · 地形高差已夸张')
    if SW: scene['style'] = 'sanwei'
    json.dump(scene, open(out+'/scene.json', 'w'), ensure_ascii=False)
    json.dump(dict(duration=D, whoosh=sfx_whoosh, pops=sorted(pops), seed=ep.get('music_seed', 7), **({'music': ep['music']} if ep.get('music') else {})), open(out+'/audio.json', 'w'), ensure_ascii=False)
    if ep.get('cover'): json.dump(ep['cover'], open(out+'/cover.json', 'w'), ensure_ascii=False, indent=1)
    nfr = int(round(D*fps))
    json.dump(dict(id=ep['id'], aspect=aspect, w=W, h=H, fps=fps, duration=D, frames=nfr, step=step), open(out+'/meta.json', 'w'))
    if engine == 'v1': write_svml(ep, out, W, H, fps, D, aspect, sfx_whoosh, pops)
    print(out)

def camera_rules(keys, ktype):
    """v3 镜头稳定三规则（后处理全部关键帧）：①按缩放限俯仰 ②转向零相位低通 + 限速 ③（push-in 在 hold_drift 里）"""
    if not keys: return
    for k, ty in zip(keys, ktype):
        if ty != 'terrain_side': k[4] = round(min(k[4], interp_tab(PITCH_CAP, k[3])), 3)
    # 展开 bearing → 零相位指数平滑 → 限速
    b = [keys[0][5]]
    for k in keys[1:]: b.append(b[-1]+((k[5]-b[-1]+180) % 360-180))
    T = [k[0] for k in keys]
    def ema(xs, ts):
        out = [xs[0]]
        for i in range(1, len(xs)):
            dt = max(1e-6, ts[i]-ts[i-1]); a = 1-math.exp(-dt/BEARING_SMOOTH_S*2); out.append(out[-1]+(xs[i]-out[-1])*a)
        return out
    fwd = ema(b, T); bwd = ema(fwd[::-1], [-t for t in T[::-1]])[::-1]
    # 原动作快结束的镜头（orbit/terrain_side）只做限速、不低通，保住环绕手感
    sm = [bwd[i] if ktype[i] not in ('orbit', 'terrain_side') else b[i] for i in range(len(b))]
    out = [sm[0]]
    for i in range(1, len(sm)):
        dt = max(1e-6, T[i]-T[i-1]); lim = BEARING_RATE.get(ktype[i], BEARING_RATE['default'])*dt
        out.append(out[-1]+max(-lim, min(lim, sm[i]-out[-1])))
    for k, v in zip(keys, out): k[5] = round(v, 3)

def wall_ring(a, pt):
    if 'circle' in a:
        c = pt(a['circle']['place']); rm = a['circle']['radius_m']
        return [[c[0]+rm/(111320*math.cos(math.radians(c[1])))*math.cos(2*math.pi*j/72), c[1]+rm/110540*math.sin(2*math.pi*j/72)] for j in range(73)]
    g = json.load(open(a['file'], encoding='utf-8')) if isinstance(a.get('file'), str) else a['file']
    g = g['features'][0]['geometry'] if 'features' in g else g.get('geometry', g)
    if g['type'] == 'Polygon': return g['coordinates'][0]
    return max((p[0] for p in g['coordinates']), key=len)

def context_layer(ep, keys):
    """v3 上下文注记层：今天的城市点/地名（Natural Earth，公有领域）+ 常驻背景水系。省界默认不画。"""
    cx = ep.get('context', {})
    if not cx or not keys: return None
    here = os.path.dirname(os.path.abspath(__file__))
    xs = [k[1] for k in keys]; ys = [k[2] for k in keys]; bb = (min(xs)-6, min(ys)-5, max(xs)+6, max(ys)+5)
    res = dict(max_cities=cx.get('max_cities', 8), exclude=cx.get('exclude', []))
    if cx.get('cities', True):
        C = json.load(open(os.path.join(here, 'data/context/cities_cn.json'), encoding='utf-8'))['cities']
        res['cities'] = [c for c in C if bb[0] < c['lon'] < bb[2] and bb[1] < c['lat'] < bb[3] and c['n'] not in res['exclude']]
    if cx.get('rivers'):
        R = json.load(open(os.path.join(here, 'data/context/rivers_cn.geojson'), encoding='utf-8'))
        F = [f for f in R['features'] if f['properties']['name'] in cx['rivers']]
        res['rivers'] = dict(type='FeatureCollection', features=F)
        # 河名候选点：每条河沿线每 ~120km 一个，scene 每帧挑离画面中心最近、且在画面内的一个
        names = []
        for f in F:
            for part in f['geometry']['coordinates']:
                acc = 0
                for a, b in zip(part, part[1:]):
                    acc += _km(a, b)
                    if acc > 120 and bb[0] < b[0] < bb[2] and bb[1] < b[1] < bb[3]: names.append(dict(n=f['properties']['name'], at=b)); acc = 0
        res['river_names'] = names
    return res

def scale_check(log):
    """v2 景别规则：远(<8.8)/中/近(>10.8) × 俯(<45°)/斜/侧(>=70°)。任意 SCALE_RULE 秒窗口内只有 1 种景别 → 告警（STRICT_SCALE=1 时报错）。"""
    cls = lambda z, p: ('远' if z < 8.8 else '近' if z > 10.8 else '中') + ('俯' if p < 45 else '侧' if p >= 70 else '斜')
    ev = [(t0, cls(z, p), typ) for t0, d, typ, z, p in log]; end = log[-1][0]+log[-1][1] if log else 0; bad = []
    t = 0.0
    while t + SCALE_RULE <= end + 1e-6:
        ks = {c for (t0, c, _), nxt in zip(ev, ev[1:]+[(end, None, None)]) if t0 < t+SCALE_RULE and nxt[0] > t}
        if len(ks) < 2: bad.append(round(t, 1))
        t += 1.0
    side = sum(1 for _, c, _ in ev if c.endswith('侧'))
    print(f'[景别] {len(ev)} 镜，景别种类 {len(set(c for _, c, _ in ev))}，侧视 {side} 镜；违规窗口起点 {bad[:8]}{"…" if len(bad) > 8 else ""}', file=sys.stderr)
    if bad and os.environ.get('STRICT_SCALE'): raise SystemExit('景别规则不满足')

def write_svml(ep, out, W, H, fps, D, aspect, whoosh, pops):
    V = aspect == '9x16'
    fr = dict(title=(6, 9, 94, 22) if V else (10, 5, 90, 25), sub=(4, 66, 96, 76) if V else (0, 86, 100, 95.5), counter=(56, 4.0, 96, 11.0) if V else (78, 4, 98, 14), chips=(4, 11.8, 96, 15.6) if V else (2, 4, 50, 10), card=(12, 44, 88, 60) if V else (30, 30, 70, 55),
              panel=(5, 24, 72, 50) if V else (2.6, 19, 29.5, 67), credit=(4, 1.6, 97, 3.4) if V else (30, 96.4, 99.2, 99.6))
    look = f'''<?svml using="@hypit/recipe@1"?>
<sheet version="1">
  text.subtitle {{ size: {54 if V else 50}; weight: 700; line-height: 1.25; }}
  text.title {{ size: {112 if V else 120}; weight: 900; line-height: 1.15; tracking: 6; }}
  text.titlesub {{ size: {44 if V else 42}; weight: 700; line-height: 1.3; }}
  text.panel {{ size: {34 if V else 31}; weight: 500; line-height: 1.5; }}
  text.panelhead {{ size: {42 if V else 40}; weight: 700; line-height: 1.6; }}
  text.credit {{ size: {18 if V else 17}; weight: 500; line-height: 1.2; }}
  film.main {{ background: #000000; }}
</sheet>
'''
    open(out+'/look.svs', 'w').write(look)
    n = [0]
    def nid(p): n[0] += 1; return f'{p}{n[0]}'
    def spans(text, hl):
        hl = sorted([h for h in (hl or []) if h], key=len, reverse=True); res = []; i = 0
        while i < len(text):
            m = next((h for h in hl if text.startswith(h, i)), None)
            if m: res.append(f'<typo:Span id="{nid("h")}" style={{sub-hl}}>{escape(m)}</typo:Span>'); i += len(m); continue
            j = i
            while j < len(text) and not any(text.startswith(h, j) for h in hl): j += 1
            res.append(f'<typo:Span id="{nid("n")}">{escape(text[i:j])}</typo:Span>'); i = j
        return ''.join(res)
    win, flows, tracks = [], [], ['picture']
    ti = ep.get('title')
    if ti:
        a, b = ti.get('t', [0.2, 3.2]); win.append(f'<time:Window id="title" from="{a}s" until="{b}s"/>')
        hold = max(16, int((b-a)*fps)-16)
        flows.append(f'''  <typo:Motion id="title-motion">
    <typo:ItemKeyframe at="0" opacity="0" scale="0.92"/>
    <typo:ItemKeyframe at="12" opacity="1" scale="1" easing="ease-out"/>
    <typo:ItemKeyframe at="{hold}" opacity="1" scale="1.02"/>
    <typo:ItemKeyframe at="{hold+14}" opacity="0" scale="1.04" easing="ease-in"/>
  </typo:Motion>
  <typo:Flow id="title" timeline={{program.timeline}} within={{title-frame}} style={{title-style}} z="30" align="center" block-align="center" motion={{title-motion}} during={{program.title}}>
    <typo:P id="tp1"><typo:Span id="tr1">{escape(ti['text'])}</typo:Span></typo:P>''' + (f'''
    <typo:P id="tp2" style={{title-sub}}><typo:Span id="tr2">{escape(ti['sub'])}</typo:Span></typo:P>''' if ti.get('sub') else '') + '\n  </typo:Flow>')
        tracks.append('title')
    for k, c in enumerate(ep.get('captions', [])):
        a, b = c['t']; win.append(f'<time:Window id="c{k}" from="{a}s" until="{b}s"/>')
        flows.append(f'  <typo:Flow id="c{k}" timeline={{program.timeline}} within={{subtitle-frame}} style={{sub-style}} z="30" align="center" block-align="center" motion={{sub-in}} during={{program.c{k}}}><typo:P id="cp{k}">{spans(c["text"], c.get("hl"))}</typo:P></typo:Flow>')
        tracks.append(f'c{k}')
    pa = ep.get('panel')
    if pa:
        a, b = pa['t']; win.append(f'<time:Window id="panel" from="{a}s" until="{b}s"/>'); end = int((b-a)*fps)
        rows = ''.join(f'\n    <typo:P id="pp{j}"><typo:Span id="pk{j}" style={{panel-key}}>{escape(kk)}　</typo:Span><typo:Span id="pv{j}">{escape(vv)}</typo:Span></typo:P>' for j, (kk, vv) in enumerate(pa['rows']))
        flows.append(f'''  <typo:Motion id="panel-motion">
    <typo:ItemKeyframe at="0" opacity="0" x="-48"/>
    <typo:ItemKeyframe at="14" opacity="1" x="0" easing="ease-out"/>
    <typo:ItemKeyframe at="{max(15,end-15)}" opacity="1" x="0"/>
    <typo:ItemKeyframe at="{end}" opacity="0" x="-48" easing="ease-in"/>
  </typo:Motion>
  <typo:Flow id="panel" timeline={{program.timeline}} within={{panel-frame}} style={{panel-style}} z="25" align="start" block-align="start" padding="26 30" motion={{panel-motion}} during={{program.panel}}>
    <typo:P id="ph"><typo:Span id="phs">{escape(pa['head'])}</typo:Span></typo:P>{rows}
  </typo:Flow>''')
        tracks.append('panel')
    credit = ep.get('credit', '影像 © Esri, Maxar, Earthstar Geographics · 地形 AWS Terrain Tiles · 地形高差已夸张')
    flows.append(f'  <typo:Flow id="credit" timeline={{program.timeline}} within={{credit-frame}} style={{credit-style}} z="40" align="end" block-align="center" wrap="none" during={{program.window}}><typo:P id="crp"><typo:Span id="crs">{escape(credit)}</typo:Span></typo:P></typo:Flow>')
    tracks.append('credit')
    aud = []
    for j, w in enumerate(whoosh): win.append(f'<time:Window id="wh{j}" from="{max(0,round(w-0.2,3))}s" for="1500ms"/>'); aud.append(f'<audio:Clip id="whc{j}" source={{whoosh-media.media}} during={{program.wh{j}}} gain="0.5"/>')
    for j, p in enumerate(pops):
        if p < D-0.3: win.append(f'<time:Window id="pop{j}" from="{p}s" for="300ms"/>'); aud.append(f'<audio:Clip id="popc{j}" source={{pop-media.media}} during={{program.pop{j}}} gain="0.32"/>')
    def frame(name, f): return f'  <space:Frame id="{name}" within={{canvas.bounds}} left="{f[0]}%" top="{f[1]}%" right="{f[2]}%" bottom="{f[3]}%"/>'
    NL = '\n'
    svml = f'''<?svml using="@hypit/markup@1"?>
<!-- 由 engine/compile.py 从 episode 生成，勿手改。地图镜头为预渲染素材 map.mp4。 -->
<svml>
  <import as="time" from="@hypit/timeline-author@1"/>
  <import as="space" from="@hypit/spatial@1"/>
  <import as="media" from="@hypit/media@1"/>
  <import as="mediaop" from="@hypit/media-operations@1"/>
  <import as="visual" from="@hypit/visual-track@1"/>
  <import as="audio" from="@hypit/audio-track@1"/>
  <import as="fonts" from="@hypit/fontsource@1"/>
  <import as="typo" from="@hypit/text-fine@1"/>
  <import as="film" from="@hypit/film@1"/>
  <import as="html" from="@hypit/html-video@1"/>
  <import as="look" source="./look.svs"/>

  <space:Canvas id="canvas" width="{W}" height="{H}"/>
  <time:Clock id="clock" frame-rate="{fps}"/>
  <time:Timeline id="program" clock={{clock}} end="{D}s">
    {(NL+'    ').join(win)}
  </time:Timeline>
  <space:Frame id="full" within={{canvas.bounds}} left="0%" top="0%" right="100%" bottom="100%"/>
{frame('title-frame', fr['title'])}
{frame('subtitle-frame', fr['sub'])}
{frame('panel-frame', fr['panel'])}
{frame('credit-frame', fr['credit'])}

  <media:Video id="map-file" src="./map.mp4"/>
  <mediaop:Normalize id="map-media" source={{map-file}} clock={{clock}} video="primary-moving" audio="none" span-authority="video"/>
  <visual:Track id="picture" timeline={{program.timeline}}>
    <visual:Clip id="map" media={{map-media.media}} during={{program.window}} frame={{full}} z="0" fit="cover"/>
  </visual:Track>

  <fonts:Face id="han-bold" package="@fontsource-variable/noto-sans-sc" weight="700" style="normal"/>
  <fonts:Face id="han-black" package="@fontsource-variable/noto-sans-sc" weight="900" style="normal"/>
  <fonts:Face id="han-medium" package="@fontsource-variable/noto-sans-sc" weight="500" style="normal"/>
  <typo:Style id="sub-style" recipe={{look.text.subtitle}} font={{han-bold}}>
    <typo:Box target="frame" color="rgba(0,0,0,0.42)"/>
    <typo:Stroke color="#000000" width="5" placement="outside"/>
    <typo:Fill color="#ffffff"/>
  </typo:Style>
  <typo:Style id="sub-hl" recipe={{look.text.subtitle}} font={{han-bold}}>
    <typo:Stroke color="#000000" width="5" placement="outside"/>
    <typo:Fill color="#FFD84A"/>
  </typo:Style>
  <typo:Style id="title-style" recipe={{look.text.title}} font={{han-black}}>
    <typo:Glow color="rgba(200,16,46,0.65)" blur="18"/>
    <typo:Stroke color="#C8102E" width="7" placement="outside"/>
    <typo:Fill color="#ffffff"/>
  </typo:Style>
  <typo:Style id="title-sub" recipe={{look.text.titlesub}} font={{han-bold}}>
    <typo:Stroke color="#000000" width="4" placement="outside"/>
    <typo:Fill color="#FFD84A"/>
  </typo:Style>
  <typo:Style id="panel-style" recipe={{look.text.panel}} font={{han-medium}}>
    <typo:Box target="frame" color="rgba(10,12,16,0.70)" border-color="#C8102E" border-width="2.5" radius="8"/>
    <typo:Fill color="#eef2f4"/>
  </typo:Style>
  <typo:Style id="panel-head" recipe={{look.text.panelhead}} font={{han-bold}}><typo:Fill color="#FF5A6E"/></typo:Style>
  <typo:Style id="panel-key" recipe={{look.text.panel}} font={{han-bold}}><typo:Fill color="#FFD84A"/></typo:Style>
  <typo:Style id="credit-style" recipe={{look.text.credit}} font={{han-medium}}>
    <typo:Shadow color="rgba(0,0,0,0.9)" x="0" y="1" blur="3"/>
    <typo:Fill color="rgba(255,255,255,0.78)"/>
  </typo:Style>
  <typo:Motion id="sub-in">
    <typo:ItemKeyframe at="0" opacity="0" y="10"/>
    <typo:ItemKeyframe at="6" opacity="1" y="0" easing="ease-out"/>
  </typo:Motion>

{NL.join(flows)}

  <media:Audio id="score-file" src="./audio/score.wav"/>
  <media:Audio id="whoosh-file" src="./audio/whoosh.wav"/>
  <media:Audio id="pop-file" src="./audio/pop.wav"/>
  <mediaop:Normalize id="score-media" source={{score-file}} clock={{clock}} video="none" audio="default" span-authority="audio"/>
  <mediaop:Normalize id="whoosh-media" source={{whoosh-file}} clock={{clock}} video="none" audio="default" span-authority="audio"/>
  <mediaop:Normalize id="pop-media" source={{pop-file}} clock={{clock}} video="none" audio="default" span-authority="audio"/>
  <audio:Track id="sound" timeline={{program.timeline}}>
    <audio:Clip id="score" source={{score-media.media}} during={{program.window}} gain="0.6" fade-in="6f" fade-out="20f"/>
    {(NL+'    ').join(aud)}
  </audio:Track>

  <film:Film id="main" canvas={{canvas.canvas}} timeline={{program.timeline}} appearance={{look.film.main}}>
{NL.join(f'    <film:Track source={{{x}.visual}}/>' for x in tracks)}
    <film:Track source={{sound.audio}}/>
  </film:Film>
  <html:Video id="final" composition={{main.composition}} timeline={{program.timeline}}/>
</svml>
'''
    open(out+'/comp.svml', 'w').write(svml)
    open(out+'/run.svrun', 'w').write('<?svml using="@hypit/markup/run@1"?>\n<svrun version="1">\n  <author source="./comp.svml"/>\n  <target output="final.video"/>\n</svrun>\n')

if __name__ == '__main__':
    a = sys.argv[1:]; eng = 'v2'
    if '--engine' in a: i = a.index('--engine'); eng = a[i+1]; del a[i:i+2]
    main(a[0], a[1] if len(a) > 1 and a[1] else None, eng)

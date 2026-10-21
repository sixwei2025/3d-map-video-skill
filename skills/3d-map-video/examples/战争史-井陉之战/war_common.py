"""战争系列（以少胜多）共用：时间轴读取、字幕切分、OSM 真实河道读取（ODbL）、距离。只生成 episode 数据，不改引擎。"""
import json, math, re, os
def load_tl(path):
    T = json.load(open(path)); Ls = T['lines']; D = T['duration']
    st = [0.0] + [l['t0'] for l in Ls[1:]]; en = st[1:] + [D]
    S = lambda i: round(st[i], 3); E = lambda i: round(en[i], 3); TT = lambda i: [S(i), E(i)]
    def offt(i, word):
        tx = Ls[i]['text']; k = tx.find(word); assert k >= 0, word
        return round(Ls[i]['t0']+(Ls[i]['t1']-Ls[i]['t0'])*(k+len(word))/len(tx), 2)
    return T, Ls, D, S, E, TT, offt
def captions(Ls, HL, maxc=18):
    caps = []
    for l in Ls:
        tx = l['text']; parts = [tx]
        if len(tx) > maxc:
            segs = re.findall(r'[^，；：？。！]+[，；：？。！]?', tx); parts = []; cur = ''
            for sg in segs:
                if cur and len(cur)+len(sg) > maxc: parts.append(cur); cur = sg
                else: cur += sg
            if cur: parts.append(cur)
        tot = sum(len(p) for p in parts); t = l['t0']
        for p in parts:
            d = (l['t1']-l['t0'])*len(p)/tot; txt = p.rstrip('，。；：')
            caps.append(dict(text=txt, hl=[h for h in HL if h in txt], t=[round(t, 3), round(t+d+(0.18 if p is parts[-1] else 0), 3)])); t += d
    for a, b in zip(caps, caps[1:]): a['t'][1] = min(a['t'][1], b['t'][0])
    return caps
def km(a, b):
    R = 6371; p1, p2 = math.radians(a[1]), math.radians(b[1]); dl = math.radians(b[0]-a[0])
    return R*math.acos(min(1, math.sin(p1)*math.sin(p2)+math.cos(p1)*math.cos(p2)*math.cos(dl)))
def osm_river(path, name, bbox=None, step_km=0.5):
    """OSM waterway 几何 → 串成一条最长折线，按 step_km 抽稀。bbox=(lon0,lat0,lon1,lat1) 裁切。"""
    d = json.load(open(path)); segs = [[[p['lon'], p['lat']] for p in e['geometry']] for e in d['elements'] if e.get('tags', {}).get('name') == name]
    if bbox: segs = [[p for p in s if bbox[0] <= p[0] <= bbox[2] and bbox[1] <= p[1] <= bbox[3]] for s in segs]; segs = [s for s in segs if len(s) > 1]
    eq = lambda a, b: abs(a[0]-b[0]) < 1e-6 and abs(a[1]-b[1]) < 1e-6
    segs.sort(key=len, reverse=True); ch = segs.pop(0)
    while True:
        for k, s in enumerate(segs):
            if eq(ch[-1], s[0]): ch += s[1:]
            elif eq(ch[-1], s[-1]): ch += s[::-1][1:]
            elif eq(ch[0], s[-1]): ch = s[:-1]+ch
            elif eq(ch[0], s[0]): ch = s[::-1][:-1]+ch
            else: continue
            segs.pop(k); break
        else: break
    out = [ch[0]]
    for p in ch[1:]:
        if km(out[-1], p) >= step_km: out.append(p)
    if out[-1] != ch[-1]: out.append(ch[-1])
    return [[round(x, 5), round(y, 5)] for x, y in out]
def nearest(line, pt): return min(line, key=lambda p: km(p, pt))
def chapters(CH):
    chap = []; seen = set()
    for i, c in enumerate(CH):
        if c not in seen: seen.add(c); chap.append(dict(title=c, shot=i))
    return chap

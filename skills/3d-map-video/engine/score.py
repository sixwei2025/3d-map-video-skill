#!/usr/bin/env python3
"""v2 分段配乐：audio.json 的 music{sections,hits,sfx} → audio/score.wav（CC0 曲库 + 自合成鼓点/音效，确定性）。
没有 music 字段时不做任何事（沿用 synth.py 的整轨合成）。
用法: python3 engine/score.py <workDir>
sections: {t0,t1,track(库 id 或 @drone),off('auto'|'mid'|'max'|秒),gain,fi,fo,swell=[t0,t1,倍数]}
hits:     {t,g,f0?,stop?}   stop=秒：重击后全部音乐静音这么久（卡点"刹车"）
sfx:      {type: riser|wind|roll|cavalry|bell|chime, t0,t1 | t, g}"""
import json, os, subprocess, sys, wave
import numpy as np, scipy.signal as sg
W = sys.argv[1]; A = json.load(open(f'{W}/audio.json')); MU = A.get('music')
if not MU: print('score: 无 music 字段，跳过'); sys.exit(0)
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'); LIB = json.load(open(f'{ROOT}/assets/music/library.json'))
SR = 48000; D = float(A['duration']); N = int((D+0.5)*SR); rng = np.random.default_rng(A.get('seed', 7))
mus = np.zeros((N, 2)); fx = np.zeros((N, 2)); used = []
lp = lambda x, fc, o=2: sg.lfilter(*sg.butter(o, fc/(SR/2)), x, axis=0)
bp = lambda x, a, b: sg.lfilter(*sg.butter(2, [a/(SR/2), b/(SR/2)], 'band'), x)
def load(f):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', f, '-f', 'f32le', '-ac', '2', '-ar', str(SR), '-'], capture_output=True, check=True).stdout
    x = np.frombuffer(raw, np.float32).reshape(-1, 2).astype(np.float64); return x/max(1e-6, np.sqrt((x**2).mean())*6)  # 粗略响度对齐（RMS≈-15.6dBFS）
def pick(x, dur, mode):
    if isinstance(mode, (int, float)): return float(mode)
    n = int(dur*SR); e = np.cumsum((x**2).mean(1)); hop = SR//4
    if len(x) <= n: return 0.0
    r = np.sqrt((e[n::hop][:(len(x)-n)//hop] - e[:len(x)-n:hop][:(len(x)-n)//hop])/n)
    if mode == 'max': i = int(np.argmax(r))
    else: i = int(np.argsort(r)[int(len(r)*0.6)]) if mode in ('mid', 'auto') else 0
    return i*hop/SR
def drone(n):
    t = np.arange(n)/SR; m = lambda k: 440*2**((k-69)/12)
    s = np.sin(2*np.pi*m(38)*t)+0.5*np.sin(2*np.pi*m(26)*t)+0.3*sg.sawtooth(2*np.pi*m(45)*t)*0.4+0.2*sg.sawtooth(2*np.pi*m(50.05)*t)
    s = lp(s, 500)*(0.8+0.2*np.sin(2*np.pi*t/2.3)); return np.stack([s, s], 1)/3
cache = {}
for sc in MU['sections']:
    t0, t1 = sc['t0'], min(sc['t1'], D); L = t1-t0
    if L <= 0: continue
    if sc['track'].startswith('@'): seg = drone(int(L*SR)); off = 0
    else:
        info = LIB[sc['track']]; x = cache.setdefault(sc['track'], load(f"{ROOT}/assets/music/{info['file']}"))
        off = pick(x, L, sc.get('off', 'mid')); n = int(L*SR); seg = x[int(off*SR):int(off*SR)+n]
        while len(seg) < n: seg = np.concatenate([seg, x[:n-len(seg)]])  # 不够长就循环
        used.append(dict(track=sc['track'], t0=round(t0, 2), t1=round(t1, 2), off=round(off, 2), title=info['title'], author=info['author'], license=info['license'], page=info['page']))
    n = len(seg); e = np.ones(n); a = int(sc.get('fi', 0.5)*SR); b = int(sc.get('fo', 0.8)*SR)
    if a: e[:a] = np.linspace(0, 1, a)
    if b: e[-b:] *= np.linspace(1, 0, b)
    if sc.get('swell'):
        s0, s1, k = sc['swell']; tt = t0+np.arange(n)/SR; e *= 1+(k-1)*np.clip((tt-s0)/max(1e-3, s1-s0), 0, 1)*np.clip((s1+3-tt)/3, 0, 1)
    s = int(t0*SR); mus[s:s+n] += seg*e[:, None]*sc.get('gain', 1.0)
def add(buf, sig, t, g=1.0, pan=0.0):
    s = int(t*SR); sig = sig[:max(0, N-s)]
    if sig.ndim == 1: sig = np.stack([sig*np.sqrt((1-pan)/2)*1.41, sig*np.sqrt((1+pan)/2)*1.41], 1)
    buf[s:s+len(sig)] += sig*g
def taiko(f0=110, d=1.5):
    n = int(d*SR); tt = np.arange(n)/SR; f = f0*np.exp(-tt*3)+45
    return np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*4.2)+lp(rng.normal(0, 1, n), 900)*np.exp(-tt*28)*0.6
def env(n, a, r): e = np.ones(n); A_ = int(a*SR); R = int(r*SR); e[:A_] = np.linspace(0, 1, A_); e[-R:] *= np.linspace(1, 0, R); return e
for h in MU.get('hits', []):
    add(fx, taiko(h.get('f0', 115), 1.8), h['t'], 0.9*h.get('g', 1.0))
    if h.get('stop'):  # 卡点刹车：重击后音乐静音
        s = int((h['t']+0.08)*SR); n = int(h['stop']*SR); r = int(0.25*SR); g = np.ones(n+r); g[:n] = 0; g[n:] = np.linspace(0, 1, r); mus[s:s+n+r] *= g[:len(mus[s:s+n+r])][:, None]
        k = int(0.08*SR); mus[s-k:s] *= np.linspace(1, 0, k)[:, None]
for x in MU.get('sfx', []):
    ty = x['type']; g = x.get('g', 1.0)
    if ty == 'riser':
        n = int((x['t1']-x['t0'])*SR); tt = np.arange(n)/n; s = bp(rng.normal(0, 1, n), 300, 7000)*tt**2.2; add(fx, s, x['t0'], 0.30*g)
    elif ty == 'wind':
        n = int((x['t1']-x['t0'])*SR); tt = np.arange(n)/SR; w = rng.normal(0, 1, n); fc = 600+400*np.sin(2*np.pi*tt/3.1); out = np.zeros(n)
        for i in range(0, n, 4800): out[i:i+4800] = bp(w[i:i+4800], max(150, fc[i]*.5), fc[i]*1.5)
        out *= env(n, 1.5, 2.0)*(0.7+0.3*np.sin(2*np.pi*tt/1.7)); add(fx, out, x['t0'], 0.30*g)
    elif ty == 'roll':  # 战鼓渐密
        t = x['t0']; gap = 0.9; T = x['t1']-x['t0']
        while t < x['t1']-0.1: k = (t-x['t0'])/T; add(fx, taiko(95, 1.2), t, (0.35+0.45*k)*g, pan=rng.uniform(-.3, .3)); gap = max(0.2, gap*0.88); t += gap
    elif ty == 'cavalry':
        n = int((x['t1']-x['t0'])*SR); rum = lp(rng.normal(0, 1, n), 120)*3; hoof = np.zeros(n)
        for k in range(int(40*(x['t1']-x['t0']))):
            p = int(rng.uniform(0, n-2000)); hoof[p:p+1500] += lp(rng.normal(0, 1, 1500), 500)*np.exp(-np.arange(1500)/150)*rng.uniform(.3, 1)
        add(fx, (rum+hoof*0.6)*env(n, 0.4, 1.5), x['t0'], 0.30*g)
    elif ty in ('bell', 'chime'):
        n = int(4.0*SR); tt = np.arange(n)/SR; f0 = 98 if ty == 'bell' else 659.3
        s = sum(a*np.sin(2*np.pi*f0*r*tt)*np.exp(-tt*dk) for r, a, dk in ([(1, 1, .9), (2.0, .5, 1.4), (2.76, .35, 2), (5.4, .2, 3)] if ty == 'bell' else [(1, 1, 2.2), (1.5, .5, 2.6), (2, .3, 3.2)]))
        add(fx, s, x['t'], (0.55 if ty == 'bell' else 0.25)*g)
mix = mus+fx; rev = np.zeros_like(mix)
for d, gg in [(0.029, .3), (0.047, .25), (0.071, .2), (0.113, .15), (0.173, .1)]: k = int(d*SR); rev[k:] += mix[:-k]*gg
mix = mix+lp(rev, 5000)*0.4; mix = mix[:int((D+0.2)*SR)]; mix = mix/max(1e-9, np.abs(mix).max())*0.89
with wave.open(f'{W}/audio/score.wav', 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((mix*32767).astype('<i2').tobytes())
json.dump(used, open(f'{W}/audio/score_tracks.json', 'w'), ensure_ascii=False, indent=1)
print('score.wav', round(len(mix)/SR, 2), 's;', len(used), 'library segments'); [print(' ', u['t0'], '-', u['t1'], u['track'], 'off', u['off']) for u in used]

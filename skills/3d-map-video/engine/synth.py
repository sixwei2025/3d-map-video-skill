#!/usr/bin/env python3
"""自合成配乐 + 音效（源自乾陵样片 assets/audio/synth.py，参数化时长与鼓点）。确定性、无第三方音源。
用法: python3 engine/synth.py <workDir>   读 audio.json {duration, whoosh[], pops[], seed}"""
import numpy as np, scipy.signal as sg, wave, json, sys
W = sys.argv[1]; cfg = json.load(open(f'{W}/audio.json'))
SR = 48000; DUR = float(cfg['duration'])+0.2; N = int(SR*DUR); rng = np.random.default_rng(cfg.get('seed', 7))
midi = lambda m: 440*2**((m-69)/12)
def write(name, x):
    x = np.asarray(x); x = np.stack([x, x], 1) if x.ndim == 1 else x; x = x/max(1e-9, np.abs(x).max())*0.89
    with wave.open(f'{W}/audio/{name}', 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((x*32767).astype('<i2').tobytes())
lp = lambda x, fc, o=2: sg.lfilter(*sg.butter(o, fc/(SR/2)), x)
hp = lambda x, fc, o=2: sg.lfilter(*sg.butter(o, fc/(SR/2), 'high'), x)
def env(n, a, r): e = np.ones(n); A = int(a*SR); R = int(r*SR); e[:A] = np.linspace(0, 1, A); e[-R:] *= np.linspace(1, 0, R); return e
t = np.arange(N)/SR; L = np.zeros(N); Rr = np.zeros(N)
def add(sig, start, pan=0.0, gain=1.0):
    s = int(start*SR); e = min(N, s+len(sig))
    if e <= s: return
    seg = sig[:e-s]*gain; L[s:e] += seg*np.sqrt((1-pan)/2); Rr[s:e] += seg*np.sqrt((1+pan)/2)
chords = [[50,57,62,65],[46,53,58,62],[48,55,60,64],[50,57,62,69],[46,53,58,65],[43,50,55,62],[48,55,60,67],[50,57,62,65]]
seg = 5.25; nch = max(2, int(np.ceil(DUR/seg)))
for i in range(nch):
    ch = chords[i % len(chords)]; n = int((seg+1.5)*SR); tt = np.arange(n)/SR; s = np.zeros(n)
    for m in ch:
        for d in (-0.09, 0.0, 0.08): s += sg.sawtooth(2*np.pi*midi(m+d)*tt+rng.uniform(0, 6))
    s = lp(s, 1400 if i < 5 else 2200)*env(n, 1.6, 1.6)*(0.55+0.45*np.sin(np.pi*np.clip(tt/seg, 0, 1)))
    add(s, i*seg-0.2 if i else 0, pan=(-0.3 if i % 2 else 0.3), gain=0.05)
dr = (np.sin(2*np.pi*midi(38)*t)+0.5*np.sin(2*np.pi*midi(26)*t)+0.25*sg.sawtooth(2*np.pi*midi(38)*t))
L += lp(dr, 300)*np.clip(t/2, 0, 1)*0.10; Rr += lp(dr, 300)*np.clip(t/2, 0, 1)*0.10
def pluck(f, dur=2.2, bright=0.5):
    n = int(dur*SR); p = int(SR/f); buf = rng.uniform(-1, 1, p); buf = lp(buf, 2000+4000*bright, 1) if p > 10 else buf
    out = np.zeros(n)
    for k in range(n): out[k] = buf[k % p]; buf[k % p] = 0.996*0.5*(buf[k % p]+buf[(k+1) % p])
    return out*np.exp(-np.arange(n)/SR*1.6)
scale = [62,65,67,69,72,74,77,79,81]; motif = [4,3,2,3,5,4,3,2,0,4,5,6,5,4,3,4,2,3]
st = 1.6; j = 0
while st < DUR-1.5:
    f = midi(scale[motif[j % len(motif)]]); add(pluck(f), st, pan=rng.uniform(-.5, .5), gain=0.30); add(pluck(f/2, 1.6, 0.2), st+0.01, gain=0.08)
    st += [0.75, 0.75, 1.1, 0.8][j % 4]; j += 1
def taiko(g=1.0, f0=110):
    n = int(1.6*SR); tt = np.arange(n)/SR; f = f0*np.exp(-tt*3)+45
    return (np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*4.5)+lp(rng.normal(0, 1, n), 900)*np.exp(-tt*30)*0.6)*g
for k, w in enumerate(cfg.get('whoosh', [])): add(taiko(1.0 if k == 0 else 0.7), max(0.05, w), gain=0.55)
mix = np.stack([L, Rr], 1); rev = np.zeros_like(mix)
for d, g in [(0.031,.35),(0.047,.3),(0.071,.25),(0.113,.2),(0.173,.15),(0.257,.1)]: k = int(d*SR); rev[k:] += mix[:-k]*g
mix = (mix+lp(rev.T, 5000).T*0.6)*np.clip((DUR-t)/1.0, 0, 1)[:, None]
write('score.wav', mix)
n = int(1.5*SR); tt = np.arange(n)/SR; noise = rng.normal(0, 1, n); out = np.zeros(n); fc = 300*np.exp(np.log(5000/300)*np.sin(np.pi*tt/1.5)**1.5)
for s in range(0, n, 512): out[s:s+512] = sg.lfilter(*sg.butter(2, [max(60, fc[s]*.6)/(SR/2), min(20000, fc[s]*1.6)/(SR/2)], 'band'), noise[s:s+512])
wl = out*np.sin(np.pi*tt/1.5)**2; pan = np.sin(np.pi*tt/1.5-np.pi/2)
write('whoosh.wav', np.stack([wl*np.sqrt((1-pan)/2), wl*np.sqrt((1+pan)/2)], 1))
n = int(0.3*SR); tt = np.arange(n)/SR; f = 700+900*(1-np.exp(-tt*40))
pop = np.sin(2*np.pi*np.cumsum(f)/SR)*np.exp(-tt*18)+0.3*np.sin(2*np.pi*2*np.cumsum(f)/SR)*np.exp(-tt*30); pop[:int(.004*SR)] *= np.linspace(0, 1, int(.004*SR))
write('pop.wav', pop); print('audio ok')

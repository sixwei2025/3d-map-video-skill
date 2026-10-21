#!/usr/bin/env python3
"""v3.2 系列统一配乐混音（2026-10-20 起替代 mix.py 的分段拼曲 + 自合成底床）。
规则：整片只用系列模板里的一首真实配乐（assets/music/<series>_theme.json），从头铺满；不叠 score.py 鼓点 / whoosh / pop。
  电平（相对口播段人声响度）：口播下 -13dB（允许 12–15），口播空档 / 开场 / 结尾 -7dB（6–8）；绝不低于 -20dB。
  剧情强弱 = 同一首曲子的音量包络：按 episode music.sections 的旧曲目映射为 弱/中/强/收，±2dB 内平滑过渡。
  成片口播段 ≈ -16 LUFS，真峰 ≤ -1.5 dBTP。
用法: python3 engine/mix_theme.py <workDir> <episode.json> <out.wav>   （再用 engine/remux_audio.sh 换音轨，画面 -c:v copy）
episode.json 可写 "music_theme": "war"|"city" 指定模板；id 以 war_ 开头 → war；否则取 music_theme；都没有则退出（由 engine/mix_auto.sh 回退 mix.py）。"""
import json, os, re, subprocess, sys, wave
import numpy as np
W, EP, OUT = sys.argv[1:4]; ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ep = json.load(open(EP)); series = 'war' if ep['id'].startswith('war_') else ep.get('music_theme')
if not series or not os.path.exists(f'{ROOT}/assets/music/{series}_theme.json'): sys.exit(f'mix_theme: {ep["id"]} 无系列主题（music_theme={series}），应走 mix.py')
T = json.load(open(f'{ROOT}/assets/music/{series}_theme.json')); a = json.load(open(f'{W}/audio.json'))
D = a['duration']; A = f'{W}/audio'; SR = 48000; N = int(round(D*SR)); db = lambda g: 10**(g/20)
def ff(*x): subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *x], check=True)
def rd(f):
    with wave.open(f) as w: ch = w.getnchannels(); x = np.frombuffer(w.readframes(w.getnframes()), '<i2').astype(np.float32)/32768
    x = x.reshape(-1, ch); return np.repeat(x, 2, 1) if ch == 1 else x
def wr(f, x):
    with wave.open(f, 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1)*32767).astype('<i2').tobytes())
def lufs(x):
    wr(f'{A}/_t.wav', x); r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f'{A}/_t.wav', '-af', 'ebur128', '-f', 'null', '-'], capture_output=True, text=True).stderr
    return float(re.search(r'I:\s+(-?[\d.]+)', r[r.rfind('Summary'):]).group(1))
fit = lambda x: x[:N] if len(x) >= N else np.vstack([x, np.zeros((N-len(x), 2), np.float32)])
# 1) 人声
ff('-i', f'{A}/voice.wav', '-af', f'aformat=sample_rates={SR}:channel_layouts=stereo,highpass=f=80,acompressor=threshold=-24dB:ratio=3.5:attack=5:release=120:makeup=2,equalizer=f=3000:t=q:w=1.2:g=2', f'{A}/voice_proc.wav')
v = fit(rd(f'{A}/voice_proc.wav'))
hop = SR//50; m = np.sqrt(np.mean(v[:N//hop*hop, 0].reshape(-1, hop)**2, 1)+1e-12); act = 20*np.log10(m) > -38
segs = []; i = 0
while i < len(act):
    if act[i]:
        j = i
        while j < len(act) and act[j]: j += 1
        segs.append([i*hop/SR-0.12, j*hop/SR+0.12]); i = j
    else: i += 1
mg = []
for s in segs:
    if mg and s[0]-mg[-1][1] < 0.6: mg[-1][1] = s[1]
    else: mg.append(s)
mask = np.zeros(N, np.float32)
for s0, s1 in mg: mask[max(0, int(s0*SR)):min(N, int(s1*SR))] = 1
# 2) 配乐：一首曲子铺满（loop=true 时 2s 交叉淡化循环）
ff('-ss', str(T.get('start_offset', 0)), '-i', f"{ROOT}/assets/music/{T['file']}", '-ac', '2', '-ar', str(SR), f'{A}/_th.wav'); th = rd(f'{A}/_th.wav')
if len(th) < N and T.get('loop'):
    xf = 2*SR; out = th.copy(); r = np.linspace(0, 1, xf)[:, None]
    while len(out) < N: out = np.vstack([out[:-xf], out[-xf:]*(1-r)+th[:xf]*r, th[xf:]])
    th = out
th = fit(th); Lt = lufs(th); Lv = lufs(v*mask[:, None])
# 3) 包络（dB，相对人声）
L = T['levels_db']; ph = T['phase_db']; mp = T['phase_from_old_track']
pt = np.zeros(N, np.float32)
for s in ep.get('music', {}).get('sections', []):
    pt[int(s['t0']*SR):] = ph.get(mp.get(s['track'], '中'), 0)
k = 2*SR; pt = np.convolve(np.pad(pt[::480], 100, mode='edge'), np.ones(200)/200, 'same')[100:-100]; pt = np.interp(np.arange(N), np.arange(0, N, 480)[:len(pt)], pt)
v0, v1 = mg[0][0], mg[-1][1]; rel = np.where(mask > 0, L['under_voice'], L['gap']).astype(np.float32)
rel[:max(0, int(v0*SR))] = L['head_tail']; rel[min(N, int(v1*SR)):] = L['head_tail']
# 平滑：压下 0.15s，回升 0.6s（用不对称一阶平滑）
sm = rel[::480].copy()
for i in range(1, len(sm)): c = 0.6 if sm[i] < sm[i-1] else 0.017; sm[i] = sm[i-1]+c*(sm[i]-sm[i-1])
rel = np.interp(np.arange(N), np.arange(0, N, 480)[:len(sm)], sm)
gdb = (Lv-Lt)+rel+pt; lin = db(gdb).astype(np.float32); fi, fo = int(1.5*SR), int(2.5*SR); lin[:fi] *= np.linspace(0, 1, fi); lin[-fo:] *= np.linspace(1, 0, fo)
bed = th*lin[:, None]
# 4) 合成，口播段人声 → voice_target_lufs，限幅
G = T['voice_target_lufs']-Lv; mix = (v+bed)*db(G); wr(f'{A}/_mix0.wav', mix)
ff('-i', f'{A}/_mix0.wav', '-af', f'alimiter=limit={db(-1.5):.4f}:attack=2:release=60:level=disabled', '-c:a', 'pcm_s16le', OUT)
mx = fit(rd(OUT)); gap = (1-mask); gap[:int(1.5*SR)] = 0
rep = dict(series=series, track=T['title'], voice_seg_lufs_in_mix=lufs(mx*mask[:, None]), voice_only_lufs=lufs(v*db(G)*mask[:, None]), music_under_voice_lufs=lufs(bed*db(G)*mask[:, None]),
           music_only_seg_lufs=lufs(mx*gap[:, None]), music_only_seconds=float(gap.sum()/SR), mix_I=lufs(mx), vo_seconds=float(mask.sum()/SR))
rep['music_minus_voice_db'] = rep['music_under_voice_lufs']-rep['voice_only_lufs']
for f in ('_t', '_th', '_mix0'): os.remove(f'{A}/{f}.wav')
json.dump(rep, open(f'{A}/mix_theme_report.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps({k: (round(x, 1) if isinstance(x, float) else x) for k, x in rep.items()}, ensure_ascii=False))

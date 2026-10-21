#!/usr/bin/env python3
# 【v3.2 起配乐走 engine/mix_theme.py：系列统一一首真实配乐，见 assets/music/<series>_theme.json；本文件仅留作无模板时的旧逻辑】
"""ffmpeg 混音 + 封装。v2.1（2026-10-19，负责人反馈"配乐太吵、人声太小"）起的模板默认：
  人声优先：口播 highpass + 压缩 + 提升，站在最前面。
  配乐+音效（score.wav 已含鼓点/自合成音效，whoosh/pop 另叠）合成"底床"，按口播 VAD 包络压低：
    口播段 底床比人声低 duck_gap_db（默认 20dB，目标 18–22），只在 ≥gap_min 秒的口播空档回升到人声 -bed_gap_db（默认 8dB）。
  整体响度 I=-14 LUFS，真峰值 ≤ -1 dBTP（线性增益 + 限幅，不做动态 loudnorm，不改人声/配乐差）。
  可在 audio.json 的 "mix":{...} 覆盖下面 CFG 任意键。
无口播时仍走旧逻辑（配乐 0.6 / whoosh 0.5 / pop 0.32，alimiter）。
用法: python3 engine/mix.py <workDir> <out.mp4>          （与 workDir/map.mp4 封装，-c:v copy）
      python3 engine/mix.py <workDir> --wav <out.wav>    （只出混音 wav，供 remux_audio.sh 换音轨）
副产物: workDir/audio/{voice_proc,bed,vad_mask}.wav, workDir/audio/mix_report.json（各项实测电平）"""
import json, os, re, subprocess, sys, wave
import numpy as np
W = sys.argv[1]; WAV = len(sys.argv) > 3 and sys.argv[2] == '--wav'; OUT = sys.argv[3] if WAV else sys.argv[2]
a = json.load(open(f'{W}/audio.json')); D = a['duration']; A = f'{W}/audio'; SR = 48000
CFG = dict(voice_hp=80, voice_comp='threshold=-24dB:ratio=3.5:attack=5:release=120:makeup=2', voice_presence='equalizer=f=3000:t=q:w=1.2:g=2',
           duck_gap_db=20.0, ride_lo=18.5, ride_hi=21.5, ride_win=3.0, ride_max_up=4.0, bed_gap_db=8.0, gap_min=0.6, vad_db=-38.0, vad_pad=0.12, att=0.12, rel=0.6,
           whoosh_g=0.5, pop_g=0.35, target_i=-14.0, limit_db=-2.0)
CFG.update(a.get('mix', {}))
VO = os.path.exists(f'{A}/voice.wav')
def ff(*args): subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', *args], check=True)
def rd(f):
    with wave.open(f) as w:
        ch, sw, n = w.getnchannels(), w.getsampwidth(), w.getnframes(); x = np.frombuffer(w.readframes(n), '<i2').astype(np.float32)/32768
    x = x.reshape(-1, ch); return np.repeat(x, 2, 1) if ch == 1 else x
def wr(f, x):
    with wave.open(f, 'wb') as w: w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(x, -1, 1)*32767).astype('<i2').tobytes())
def lufs(f):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', f, '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
    s = r[r.rfind('Summary'):]; I = float(re.search(r'I:\s+(-?[\d.]+|-inf)', s).group(1)); tp = re.search(r'Peak:\s+(-?[\d.]+|-inf)', s)
    return I, (float(tp.group(1)) if tp else None)
db = lambda g: 10**(g/20)
N = int(round(D*SR))
def fit(x): return x[:N] if len(x) >= N else np.vstack([x, np.zeros((N-len(x), 2), np.float32)])

if not VO:  # 旧逻辑
    ins = ['-i', f'{A}/score.wav']; fl = ['[0:a]volume=0.6[s0]']; lab = ['[s0]']; k = 1
    for i, t in enumerate(a.get('whoosh', [])):
        ins += ['-i', f'{A}/whoosh.wav']; ms = int(max(0, t-0.2)*1000); fl.append(f'[{k}:a]volume=0.5,adelay={ms}|{ms}[w{i}]'); lab.append(f'[w{i}]'); k += 1
    for i, t in enumerate(p for p in a.get('pops', []) if p < D-0.3):
        ins += ['-i', f'{A}/pop.wav']; ms = int(t*1000); fl.append(f'[{k}:a]volume=0.32,adelay={ms}|{ms}[p{i}]'); lab.append(f'[p{i}]'); k += 1
    fl.append(''.join(lab)+f'amix=inputs={len(lab)}:normalize=0:duration=first,atrim=0:{D},alimiter=limit=0.95[aout]')
    ff(*ins, '-filter_complex', ';'.join(fl), '-map', '[aout]', '-ar', '48000', '-ac', '2', f'{A}/mix.wav')
else:
    # 1) 人声链
    ff('-i', f'{A}/voice.wav', '-af', f"aformat=sample_rates={SR}:channel_layouts=stereo,highpass=f={CFG['voice_hp']},acompressor={CFG['voice_comp']},{CFG['voice_presence']}", f'{A}/voice_proc.wav')
    v = fit(rd(f'{A}/voice_proc.wav'))
    # 2) VAD：20ms 窗 RMS > vad_db，补 pad，合并短于 gap_min 的停顿（短停顿不回升）
    hop = SR//50; m = np.sqrt(np.mean(v[:len(v)//hop*hop, 0].reshape(-1, hop)**2, 1)+1e-12)
    act = 20*np.log10(m) > CFG['vad_db']; segs = []; i = 0
    while i < len(act):
        if act[i]:
            j = i
            while j < len(act) and act[j]: j += 1
            segs.append([i*hop/SR-CFG['vad_pad'], j*hop/SR+CFG['vad_pad']]); i = j
        else: i += 1
    mg = []
    for s in segs:
        if mg and s[0]-mg[-1][1] < CFG['gap_min']: mg[-1][1] = s[1]
        else: mg.append(s)
    mask = np.zeros(N, np.float32)
    for s0, s1 in mg: mask[max(0, int(s0*SR)):min(N, int(s1*SR))] = 1
    # 3) 底床（单位增益）：score + whoosh + pop
    bed = fit(rd(f'{A}/score.wav')).copy(); wh = rd(f'{A}/whoosh.wav'); po = rd(f'{A}/pop.wav')
    def put(sig, t, g):
        s = int(t*SR); e = min(N, s+len(sig))
        if s < N: bed[s:e] += sig[:e-s]*g
    for t in a.get('whoosh', []): put(wh, max(0, t-0.2), CFG['whoosh_g'])
    for t in a.get('pops', []):
        if t < D-0.3: put(po, t, CFG['pop_g'])
    # 4) 实测校准：口播段人声 vs 底床、空档底床
    wr(f'{A}/_m_v.wav', v*mask[:, None]); wr(f'{A}/_m_bv.wav', bed*mask[:, None]); wr(f'{A}/_m_bg.wav', bed*(1-mask)[:, None])
    Lv, _ = lufs(f'{A}/_m_v.wav'); Lbv, _ = lufs(f'{A}/_m_bv.wav'); Lbg, _ = lufs(f'{A}/_m_bg.wav')
    g_under = (Lv-CFG['duck_gap_db'])-Lbv; g_gap = (Lv-CFG['bed_gap_db'])-Lbg
    # 5) 平滑包络（dB 域线性插值：压下 att 秒、回升 rel 秒）
    ka, kr = CFG['att']*SR, CFG['rel']*SR
    # 简洁实现：用分段起止点直接写斜坡
    e = np.full(N, g_gap, np.float32)
    for s0, s1 in mg:
        i0, i1 = max(0, int(s0*SR)), min(N, int(s1*SR))
        e[i0:i1] = np.minimum(e[i0:i1], g_under)
        a0 = max(0, i0-int(ka)); r1 = min(N, i1+int(kr))
        if i0 > a0: e[a0:i0] = np.minimum(e[a0:i0], np.linspace(g_gap, g_under, i0-a0, endpoint=False))
        if r1 > i1: e[i1:r1] = np.minimum(e[i1:r1], np.linspace(g_under, g_gap, r1-i1))
    fi, fo = int(0.2*SR), int(0.67*SR); lin = db(e); lin[:fi] *= np.linspace(0, 1, fi); lin[-fo:] *= np.linspace(1, 0, fo)
    bedd = bed*lin[:, None]
    # 5b) 慢速"骑推子"：口播段按 ride_win 秒滑窗，把人声-底床 RMS 差夹在 [ride_lo, ride_hi]（只在口播段，抬升最多 ride_max_up dB）
    hw, hp = int(CFG['ride_win']*SR), SR//4; ts, cs = [], []
    for c in range(0, N, hp):
        i0, i1 = max(0, c-hw//2), min(N, c+hw//2); mm = mask[i0:i1]
        if mm.mean() < 0.5: ts.append(c); cs.append(0.0); continue
        rv = np.sqrt(np.mean(v[i0:i1][mm > 0]**2)+1e-12); rb = np.sqrt(np.mean(bedd[i0:i1][mm > 0]**2)+1e-12)
        gp = 20*np.log10(rv/rb); corr = 0.0
        if gp < CFG['ride_lo']: corr = gp-CFG['ride_lo']
        elif gp > CFG['ride_hi'] and 20*np.log10(rb) > -60: corr = min(CFG['ride_max_up'], gp-CFG['ride_hi'])
        ts.append(c); cs.append(corr)
    cs = np.convolve(np.pad(cs, 4, mode='edge'), np.ones(9)/9, 'valid')  # ~2s 平滑
    ride = np.interp(np.arange(N), ts, cs).astype(np.float32)*mask
    bedd = bedd*db(ride)[:, None]; wr(f'{A}/bed.wav', bedd); wr(f'{A}/vad_mask.wav', np.repeat(mask[:, None], 2, 1))
    # 6) 合成 → 线性增益到 target_i → 限幅；迭代一次修正限幅带来的响度偏差
    mix = v+bedd; sc = 0.5/max(1e-6, float(np.abs(mix).max())); wr(f'{A}/_mix0.wav', mix*sc); L0, _ = lufs(f'{A}/_mix0.wav'); L0 -= 20*np.log10(sc)
    G = CFG['target_i']-L0
    for it in range(3):
        ff('-i', f'{A}/_mix0.wav', '-af', f"volume={G-20*np.log10(sc):.3f}dB,alimiter=limit={db(CFG['limit_db']):.4f}:attack=2:release=60:level=disabled,aresample={SR}", '-c:a', 'pcm_s16le', f'{A}/mix.wav')
        Li, tp = lufs(f'{A}/mix.wav')
        if abs(Li-CFG['target_i']) < 0.3: break
        G += CFG['target_i']-Li
    for f in ('_m_v', '_m_bv', '_m_bg', '_mix0'): os.remove(f'{A}/{f}.wav')
    rep = dict(ride_min_db=float(ride.min()), ride_max_db=float(ride.max()), voice_lufs_in_vo=Lv, bed_unit_lufs_in_vo=Lbv, bed_unit_lufs_gap=Lbg, g_under_db=g_under, g_gap_db=g_gap, mix_gain_db=G, mix_I=Li, mix_TP=tp,
               vo_segments=len(mg), vo_seconds=float(mask.sum()/SR), cfg=CFG)
    json.dump(rep, open(f'{A}/mix_report.json', 'w'), ensure_ascii=False, indent=1); print(json.dumps({k: (round(x, 2) if isinstance(x, float) else x) for k, x in rep.items() if k != 'cfg'}))
if WAV:
    if os.path.abspath(OUT) != os.path.abspath(f'{A}/mix.wav'): ff('-i', f'{A}/mix.wav', '-c', 'copy', OUT)
else:
    # v3.1：不再用 -shortest（音频比画面短时会截掉最后一帧）；音频不足就补静音到画面时长
    vd = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f'{W}/map.mp4'], capture_output=True, text=True).stdout.strip()
    ff('-i', f'{W}/map.mp4', '-i', f'{A}/mix.wav', '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af', 'apad', '-t', vd, '-c:a', 'aac', '-b:a', '192k', '-movflags', '+faststart', OUT)
print('mixed ->', OUT, '(voice)' if VO else '')

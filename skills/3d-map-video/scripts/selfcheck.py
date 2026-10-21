#!/usr/bin/env python3
"""交付前硬指标自检。用法: python3 scripts/selfcheck.py <id>   （在 skill 根目录）
检查：1080×1920/30fps/yuv420p/bt709、码率 12–16Mbps、时长、首帧=封面(PSNR>35)、配乐比人声低 12–15dB、低清瓦片为空、侧视镜头≥3、broll 3–5 镜。"""
import json, os, re, subprocess, sys
ID = sys.argv[1]; W = f'work/v2/{ID}'; O = f'out/{ID}'; F = f'{O}/{ID}_deliver.mp4'; ok = True
def r(*a): return subprocess.run(a, capture_output=True, text=True).stdout + subprocess.run(a, capture_output=True, text=True).stderr
def chk(name, cond, info=''):
    global ok; ok &= bool(cond); print(('✅' if cond else '❌'), name, info)
p = json.loads(r('ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height,r_frame_rate,pix_fmt,color_space:format=duration,bit_rate', '-of', 'json', F))
s = p['streams'][0]; fm = p['format']; br = int(fm['bit_rate']) / 1e6; dur = float(fm['duration'])
chk('画幅 1080×1920', (s['width'], s['height']) == (1080, 1920))
chk('30fps', s['r_frame_rate'] in ('30/1', '30000/1001'), s['r_frame_rate'])
chk('yuv420p + bt709', s['pix_fmt'] == 'yuv420p' and s.get('color_space') == 'bt709', f"{s['pix_fmt']} {s.get('color_space')}")
chk('码率 12–16Mbps（目标约 14）', 12 <= br <= 16.5, f'{br:.1f}Mbps')
chk('时长 ≤150s', dur <= 150, f'{dur:.1f}s')
cv = f'{W}/cover_1080x1920.jpg'
if os.path.exists(cv):
    out = r('ffmpeg', '-i', F, '-i', cv, '-frames:v', '1', '-lavfi', '[0:v]trim=end_frame=1[a];[1:v]scale=1080:1920,format=yuv420p[b];[a][b]psnr', '-f', 'null', '-')
    m = re.search(r'average:([\d.inf]+)', out); v = float(m.group(1)) if m and m.group(1) != 'inf' else 99
    chk('首帧=封面 PSNR>35', v > 35, f'{v:.1f}dB')
rp = f'{W}/audio/mix_theme_report.json'
if os.path.exists(rp):
    d = json.load(open(rp))['music_minus_voice_db']; chk('口播下配乐比人声低 12–15dB', -15.5 <= d <= -11.5, f'{d:.1f}dB')
else: chk('使用系列主题配乐 mix_theme（episode.music_theme）', False, '未找到 mix_theme_report.json')
lr = f'{W}/lowres.json'; L = json.load(open(lr)) if os.path.exists(lr) else []
chk('低清瓦片帧 still_lowres=[]', not L, str(L[:5]))
ep = json.load(open(f'episodes/{ID}.json'))
side = sum(1 for x in ep.get('shots', []) if x.get('type') == 'terrain_side'); chk('侧视地形 ≥3 镜', side >= 3, str(side))
nb = len(ep.get('broll') or []); chk('全屏实拍 3–5 镜（来源写进发布包）', 3 <= nb <= 5, str(nb))
chk('有收尾大字卡（cards 最后一张在片尾 10s 内）', any(c.get('t1', 0) >= dur - 10 for c in ep.get('cards', [])))
print('RESULT', 'PASS' if ok else 'FAIL（硬指标不过不交付；之后再做 100 分制自评，≥90 才交）')

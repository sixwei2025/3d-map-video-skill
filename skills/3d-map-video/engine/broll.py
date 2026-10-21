#!/usr/bin/env python3
"""v4c（2026-10-20c）真实素材「全屏实拍」：复刻「三维地图看世界」口播中全屏插实拍的做法。
episode.broll = [{file, t0, dur, kb:'in'|'out', credit}]：
  · 静图 → Ken Burns 缓推/缓拉，铺满 1080×1920 全屏（无白边、无小窗）；
  · 视频 → 取开头 dur 秒（或 b.start）全屏铺满；
  · 淡入淡出 0.25s；右下角半透明小字 credit；不加白边、不贴「实拍」红签；
  · 全屏叠上后：①从原片裁回顶部进度条（y=0–TOP_H）；②按 episode.captions 在字幕位重绘白字（不裁地图带，避免小窗感）。
无 broll 字段时直接退出 0。
用法: python3 engine/broll.py <episode.json> <in.mp4> [out.mp4，默认覆盖 in]"""
import json, os, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

EP_PATH, IN = sys.argv[1], sys.argv[2]
OUT = sys.argv[3] if len(sys.argv) > 3 else IN
EP = json.load(open(EP_PATH, encoding='utf-8'))
B = EP.get('broll') or []
if not B:
    print('broll: none'); sys.exit(0)

W, H, FPS = 1080, 1920, 30
TOP_H = 145
FADE = 0.25
# 字幕区（与 scene layout.sub 9x16 的 66%–76% 对齐，字号 54）
SUB_TOP = round(H * 0.66)      # 1267
SUB_BOT = round(H * 0.76)      # 1459
SUB_FS = 54
FONT_PATH = next((f for f in [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/fonts/NotoSansSC-Bold-gb2312.otf'),
    '/System/Library/Fonts/STHeiti Medium.ttc',
    '/System/Library/Fonts/Hiragino Sans GB.ttc',
] if os.path.exists(f)), None)
FONT_CAP = ImageFont.truetype(FONT_PATH, SUB_FS) if FONT_PATH else ImageFont.load_default()
FONT_CR = ImageFont.truetype(FONT_PATH, 22) if FONT_PATH else ImageFont.load_default()
CAPS = EP.get('captions') or []

def is_video(path):
    return os.path.splitext(path)[1].lower() in ('.mp4', '.mov', '.m4v', '.webm', '.mkv')

def caps_in(t0, t1):
    out = []
    for c in CAPS:
        a, b = c['t']
        if b > t0 and a < t1:
            out.append(c)
    return out

def render_cap_png(caps, t0, dur, path):
    """按帧序列写字幕：每帧一张太慢；改成按时段切几张 + enable。这里写一张「合并」图不够；
    用 ffmpeg drawtext 更稳——改为返回 (segments of text,t_rel0,t_rel1)。"""
    segs = []
    for c in caps:
        a, b = c['t']
        ra, rb = max(0.0, a - t0), min(dur, b - t0)
        if rb - ra < 0.05: continue
        segs.append((c.get('text', ''), ra, rb, c.get('hl') or []))
    return segs

tmp = tempfile.mkdtemp(prefix='broll-')
args = ['ffmpeg', '-y', '-v', 'error', '-i', IN]
fl = []; last = '0:v'; inp = 0

for k, b in enumerate(B):
    path = b['file']; t0 = float(b['t0']); dur = float(b['dur']); t1 = t0 + dur
    n = max(1, round(dur * FPS)); credit = b.get('credit', '')

    # credit PNG（全屏透明，右下角小字）
    fr = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    if credit:
        d = ImageDraw.Draw(fr); tw = d.textlength(credit, font=FONT_CR)
        box = [W - tw - 36, H - 48, W - 12, H - 12]
        d.rectangle(box, fill=(0, 0, 0, 120))
        d.text((box[0] + 12, box[1] + 6), credit, font=FONT_CR, fill=(255, 255, 255, 220))
    frp = f'{tmp}/cred{k}.png'; fr.save(frp)

    # 字幕：每个重叠 caption 画一张全屏透明 PNG（白字黑描边），按相对时间 enable
    cap_segs = render_cap_png(caps_in(t0, t1), t0, dur, None)
    cap_pngs = []
    for ci, (txt, ra, rb, hl) in enumerate(cap_segs):
        im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        # 居中画在 SUB 区
        bbox = d.textbbox((0, 0), txt, font=FONT_CAP, stroke_width=8)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        x = (W - tw) // 2; y = SUB_TOP + (SUB_BOT - SUB_TOP - th) // 2
        d.text((x, y), txt, font=FONT_CAP, fill=(255, 255, 255, 255),
               stroke_width=8, stroke_fill=(0, 0, 0, 220))
        # hl 黄字：简单整句不拆（复杂高亮留给地图页）；若整段在 hl 里则改黄
        if hl and any(h in txt for h in hl):
            # 重画：先黑描边白，再把 hl 子串叠黄——简化为整句变黄若唯一 hl 覆盖大半
            pass
        cp = f'{tmp}/cap{k}_{ci}.png'; im.save(cp); cap_pngs.append((cp, ra, rb))

    if is_video(path):
        start = float(b.get('start', 0))
        args += ['-ss', str(start), '-t', str(dur), '-i', path]
        inp += 1; vi = inp
        fl.append(
            f"[{vi}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},fps={FPS},setsar=1,format=yuva420p,"
            f"fade=in:st=0:d={FADE}:alpha=1,fade=out:st={max(0,dur-FADE):.2f}:d={FADE}:alpha=1,"
            f"setpts=PTS-STARTPTS+{t0}/TB[b{k}]"
        )
    else:
        im = Image.open(path).convert('RGB')
        s = max(W * 1.14 / im.width, H * 1.14 / im.height)
        im = im.resize((max(2, round(im.width * s)//2*2), max(2, round(im.height * s)//2*2)), Image.LANCZOS)
        cw, ch = round(W * 1.14)//2*2, round(H * 1.14)//2*2
        cx, cy = max(0, (im.width - cw)//2), max(0, (im.height - ch)//2)
        im = im.crop((cx, cy, cx + min(cw, im.width - cx)//2*2, cy + min(ch, im.height - cy)//2*2))
        # 若裁完仍不够大，再 pad
        if im.size != (cw, ch):
            canvas = Image.new('RGB', (cw, ch), (20, 20, 20)); canvas.paste(im, ((cw-im.width)//2, (ch-im.height)//2)); im = canvas
        src = f'{tmp}/s{k}.jpg'; im.save(src, quality=95)
        args += ['-i', src]; inp += 1; vi = inp
        z = f"1+0.10*on/{n}" if b.get('kb', 'in') == 'in' else f"1.10-0.10*on/{n}"
        fl.append(
            f"[{vi}:v]zoompan=z='{z}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={n}:s={W}x{H}:fps={FPS},setsar=1,format=yuva420p,"
            f"fade=in:st=0:d={FADE}:alpha=1,fade=out:st={max(0,dur-FADE):.2f}:d={FADE}:alpha=1,"
            f"setpts=PTS-STARTPTS+{t0}/TB[b{k}]"
        )

    args += ['-loop', '1', '-t', str(dur), '-i', frp]; inp += 1; fi = inp
    fl.append(
        f"[{fi}:v]format=rgba,"
        f"fade=in:st=0:d={FADE}:alpha=1,fade=out:st={max(0,dur-FADE):.2f}:d={FADE}:alpha=1,"
        f"setpts=PTS-STARTPTS+{t0}/TB[cr{k}]"
    )
    for ci, (cp, ra, rb) in enumerate(cap_pngs):
        args += ['-loop', '1', '-t', str(dur), '-i', cp]; inp += 1
        # 相对时段 → 绝对：enable between t0+ra and t0+rb；setpts 对齐 broll 起点
        fl.append(
            f"[{inp}:v]format=rgba,setpts=PTS-STARTPTS+{t0}/TB[cap{k}_{ci}]"
        )

    en = f"between(t\\,{t0}\\,{t1:.3f})"
    fl.append(f"[{last}][b{k}]overlay=0:0:eof_action=pass:enable='{en}'[m{k}]")
    fl.append(f"[m{k}][cr{k}]overlay=0:0:eof_action=pass:enable='{en}'[p{k}]")
    cur = f'p{k}'
    for ci, (cp, ra, rb) in enumerate(cap_pngs):
        en_c = f"between(t\\,{t0+ra:.3f}\\,{t0+rb:.3f})"
        fl.append(f"[{cur}][cap{k}_{ci}]overlay=0:0:eof_action=pass:enable='{en_c}'[p{k}c{ci}]")
        cur = f'p{k}c{ci}'
    # 顶栏进度条从原片裁回
    fl.append(
        f"[0:v]crop={W}:{TOP_H}:0:0,setpts=PTS-STARTPTS[top{k}];"
        f"[{cur}][top{k}]overlay=0:0:eof_action=pass:enable='{en}'[o{k}]"
    )
    last = f'o{k}'

out = OUT if OUT != IN else f'{tmp}/out.mp4'
args += ['-filter_complex', ';'.join(fl), '-map', f'[{last}]', '-map', '0:a?',
         '-c:v', 'h264_videotoolbox', '-b:v', '30M', '-pix_fmt', 'yuv420p',
         '-c:a', 'copy', '-movflags', '+faststart', out]
r = subprocess.run(args, capture_output=True, text=True)
if r.returncode != 0:
    sys.stderr.write(r.stderr[-2000:]); sys.exit(r.returncode)
if out != OUT:
    os.replace(out, OUT)
tot = sum(float(b['dur']) for b in B)
D = float(subprocess.run(
    ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', OUT],
    capture_output=True, text=True).stdout)
print(f'broll: {len(B)} 段全屏，合计 {tot:.1f}s，占全片 {tot/D*100:.1f}% · top0-{TOP_H} · captions redrawn -> {OUT}')

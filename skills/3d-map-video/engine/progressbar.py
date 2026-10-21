#!/usr/bin/env python3
"""[模板组件] 顶部章节进度条（编码阶段叠加，不进地图渲染）。
用法: python3 engine/progressbar.py <workDir>   读 workDir/scene.json 里的 chapters=[{title,t0,t1}]（compile.py 按 episode.chapters 从分镜生成）
输出 workDir/pbar/：base.png（灰底分段+暗标题）、hl_<k>.png（第 k 章标题高亮）、mask.png（分段白、缝隙黑）、filter.txt（ffmpeg -filter_complex_script）
encode_vt.sh 检测到 pbar/filter.txt 就叠加；封面帧由 prepend_cover.sh 之后再加，所以封面不带进度条。
样式：竖屏距顶 ~6.9%（避开抖音/视频号状态栏和顶部 UI），线高 6px，已播 #C8102E、未播白 30%，当前章标题白色高亮、其余白 55%。"""
import json, os, sys
from PIL import Image, ImageDraw, ImageFont
W_ = sys.argv[1]; S = json.load(open(f'{W_}/scene.json')); CH = S.get('chapters') or []
if not CH: print('no chapters, skip'); sys.exit(0)
W, H, T = S['w'], S['h'], S['duration']; V = H > W
X0, X1 = round(W*0.06), round(W*0.94); BY = round(H*(0.069 if V else 0.045)); BH = 6 if V else 5; GAP = 8
TY = BY - round(H*0.024 if V else H*0.04); FS = 26 if V else 24
FONTS = [os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data/fonts/NotoSansSC-Bold-gb2312.otf'), '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', '/System/Library/Fonts/PingFang.ttc', '/System/Library/Fonts/Hiragino Sans GB.ttc', '/Library/Fonts/Arial Unicode.ttf']
font = next((ImageFont.truetype(f, FS) for f in FONTS if os.path.exists(f)), None) or ImageFont.load_default()
O = f'{W_}/pbar'; os.makedirs(O, exist_ok=True)
segs = []
for c in CH:
    a = X0 + (X1-X0)*c['t0']/T; b = X0 + (X1-X0)*min(c['t1'], T)/T; segs.append((round(a + (GAP/2 if a > X0 else 0)), round(b - (GAP/2 if b < X1 else 0))))
def titles(hl):
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    for k, (c, (a, b)) in enumerate(zip(CH, segs)):
        tw = d.textlength(c['title'], font=font); x = max(a, min((a+b)/2 - tw/2, b - tw))
        if hl is None or k != hl:
            if hl is None: d.rounded_rectangle((a, BY, b, BY+BH), radius=BH//2, fill=(255, 255, 255, 77))
            d.text((x, TY), c['title'], font=font, fill=(255, 255, 255, 140), stroke_width=2, stroke_fill=(0, 0, 0, 90)) if hl is None else None
        else:
            d.text((x, TY), c['title'], font=font, fill=(255, 255, 255, 255), stroke_width=2, stroke_fill=(0, 0, 0, 140))
            d.rounded_rectangle((x - 2, TY + FS + 8, x + tw + 2, TY + FS + 10), radius=1, fill=(200, 16, 46, 255))
    return im
titles(None).save(f'{O}/base.png')
for k in range(len(CH)): titles(k).save(f'{O}/hl_{k}.png')
m = Image.new('L', (X1-X0, BH), 0); d = ImageDraw.Draw(m)
for a, b in segs: d.rounded_rectangle((a-X0, 0, b-X0, BH-1), radius=BH//2, fill=255)
m.save(f'{O}/mask.png')
# filter：[0:v]=地图视频，输入 1=base 2..=hl_k，最后一个=mask
n = len(CH); f = [f'[0:v][1:v]overlay=0:0[v0]']
for k, c in enumerate(CH):
    f.append(f"[v{k}][{k+2}:v]overlay=0:0:enable='between(t,{c['t0']:.3f},{c['t1']:.3f})'[v{k+1}]")
f.append(f"color=c=black:s={X1-X0}x{BH}:r={S['fps']}[pm0];color=c=white:s={X1-X0}x{BH}:r={S['fps']}[wb];[pm0][wb]overlay=x='-w+w*t/{T:.3f}':y=0:eval=frame,format=gray[pm]")
f.append(f"[{n+2}:v]format=gray[mk];[pm][mk]blend=all_mode=multiply,format=gray[al]")
f.append(f"color=c=0xC8102E:s={X1-X0}x{BH}:r={S['fps']},format=rgba[rd];[rd][al]alphamerge[red]")
f.append(f"[v{n}][red]overlay={X0}:{BY}:shortest=1,format=yuv420p[out]")
open(f'{O}/filter.txt', 'w').write(';\n'.join(f))
open(f'{O}/inputs.txt', 'w').write('\n'.join(['base.png'] + [f'hl_{k}.png' for k in range(n)] + ['mask.png']) + '\n')
print('pbar', n, 'chapters ->', O, 'bar y', BY, 'titles y', TY)

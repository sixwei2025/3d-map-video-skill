#!/usr/bin/env python3
"""帧连续性检查与补帧（可选帧区间 [A,B)；fill 输出 <work>/seq_A_B/）。
check <work> <step>  : 打印缺失/损坏帧号（逗号分隔），全部完好退出0，否则退出1
fill  <work> <step>  : 生成 <work>/seq/s%05d.jpg 连续序列（只含 step 的倍数帧；缺失/损坏帧用相邻帧混合补），打印补帧数"""
import sys, os, json
from PIL import Image
cmd, W, step = sys.argv[1], sys.argv[2], int(sys.argv[3])
m = json.load(open(f'{W}/meta.json'))
A = int(sys.argv[4]) if len(sys.argv) > 4 else 0; B = min(int(sys.argv[5]), m['frames']) if len(sys.argv) > 5 else m['frames']
want = list(range(A - A % step + (step if A % step else 0), B, step))
p = lambda i: f'{W}/frames/f{i:05d}.jpg'
def good(i):
    if not os.path.exists(p(i)) or os.path.getsize(p(i)) < 5000: return False
    try:
        with Image.open(p(i)) as im: im.verify(); return im.size == (m['w'], m['h'])
    except Exception: return False
bad = [i for i in want if not good(i)]
if cmd == 'check':
    print(','.join(map(str, bad))); sys.exit(1 if bad else 0)
ok = [i for i in want if i not in set(bad)]
if not ok: print('no frames'); sys.exit(2)
SQ = f'{W}/seq_{A}_{B}'; os.makedirs(SQ, exist_ok=True); nb = 0
for k, i in enumerate(want):
    out = f'{SQ}/s{k:05d}.jpg'
    if os.path.lexists(out): os.remove(out)
    if i not in bad: os.symlink(os.path.abspath(p(i)), out); continue
    a = max([j for j in ok if j < i], default=None); b = min([j for j in ok if j > i], default=None)
    if a is None or b is None: Image.open(p(a if b is None else b)).save(out, quality=93)
    else: Image.blend(Image.open(p(a)).convert('RGB'), Image.open(p(b)).convert('RGB'), (i-a)/(b-a)).save(out, quality=93)
    nb += 1
print('filled', nb, 'of', len(want))

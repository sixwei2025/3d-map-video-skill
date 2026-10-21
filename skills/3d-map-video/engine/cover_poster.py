#!/usr/bin/env python3
"""3D 地图系列统一封面（A 电影海报风）：成片抽帧 → 去字幕/标签框（delogo）+ 裁切 → cover_poster.html 渲染 1080×1920 JPG。
用法: python3 engine/cover_poster.py <workDir> <成片.mp4> [out.jpg]
数据：<workDir>/cover.json（compile.py 从 episode.cover 生成）：title kicker sub sub2 coord quote generals brand series top
      bg: {t: 抽帧秒, delogo: [[x,y,w,h],...], crop: [w,h,x,y]}（坐标按 1080×1920 成片）
浏览器：CHROME 环境变量，默认 Linux /usr/bin/google-chrome，Mac /Applications/Google Chrome.app/..."""
import json, os, subprocess, sys, tempfile, platform
W, V = sys.argv[1], sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else f'{W}/cover_1080x1920.jpg'
C = json.load(open(f'{W}/cover.json')); bg = C.get('bg', {}); ENG = os.path.dirname(os.path.abspath(__file__))
tmp = tempfile.mkdtemp(prefix='cover-'); vf = [f'delogo=x={x}:y={y}:w={w}:h={h}' for x, y, w, h in bg.get('delogo', [])]
if bg.get('crop'): cw, ch, cx, cy = bg['crop']; vf += [f'crop={cw}:{ch}:{cx}:{cy}', 'scale=-1:1920:flags=lanczos', 'crop=1080:1920']
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-ss', str(bg.get('t', 10)), '-i', V, '-frames:v', '1', *(['-vf', ','.join(vf)] if vf else []), '-q:v', '1', f'{tmp}/bg.jpg'], check=True)
json.dump(C, open(f'{tmp}/cover.json', 'w'), ensure_ascii=False)
chrome = os.environ.get('CHROME') or ('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' if platform.system() == 'Darwin' else '/usr/bin/google-chrome')
url = f'file://{ENG}/cover_poster.html?data=file://{tmp}/cover.json&bg=file://{tmp}/bg.jpg'
subprocess.run([chrome, '--headless=new', '--no-sandbox', '--hide-scrollbars', '--disable-gpu', '--allow-file-access-from-files', '--force-device-scale-factor=1',
                '--window-size=1080,1920', '--virtual-time-budget=4000', f'--screenshot={tmp}/shot.png', url], check=True, capture_output=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', f'{tmp}/shot.png', '-vf', 'crop=1080:1920:0:0', '-q:v', '2', OUT], check=True); print('cover ->', OUT)

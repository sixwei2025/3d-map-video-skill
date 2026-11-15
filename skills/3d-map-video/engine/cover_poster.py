#!/usr/bin/env python3
"""3D 地图系列统一封面（A 电影海报风）：成片抽帧 → 去字幕/标签框（delogo）+ 裁切 → cover_poster.html 渲染 1080×1920 JPG。
用法: python3 engine/cover_poster.py <workDir> <成片.mp4> [out.jpg]
数据：<workDir>/cover.json（compile.py 从 episode.cover 生成）：title kicker sub sub2 coord quote generals brand series top
      bg: {t: 抽帧秒, delogo: [[x,y,w,h],...], crop: [w,h,x,y]}（坐标按 1080×1920 成片）
浏览器：CHROME 环境变量，默认 Linux /usr/bin/google-chrome，Mac /Applications/Google Chrome.app/..."""
import json, os, shutil, subprocess, sys, tempfile, platform
from pathlib import Path

def _find_chrome() -> str:
    env_c = os.environ.get("CHROME") or os.environ.get("CHROME_BIN")
    if env_c and os.path.exists(env_c):
        return env_c
    for cmd in ("google-chrome", "chrome", "chromium", "chromium-browser", "msedge"):
        hit = shutil.which(cmd)
        if hit:
            return hit
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    lad = os.environ.get("LOCALAPPDATA", "")
    for cand in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(lad, "Google", "Chrome", "Application", "chrome.exe") if lad else "",
        os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
        "/usr/bin/google-chrome",
        "/usr/bin/chromium",
    ):
        if cand and os.path.exists(cand):
            return cand
    return "google-chrome"

def _find_ffmpeg() -> str:
    return shutil.which("ffmpeg") or ("/opt/homebrew/bin/ffmpeg" if platform.system() == "Darwin" and os.path.isfile("/opt/homebrew/bin/ffmpeg") else "ffmpeg")

W, V = sys.argv[1], sys.argv[2]; OUT = sys.argv[3] if len(sys.argv) > 3 else os.path.join(W, 'cover_1080x1920.jpg')
C = json.load(open(os.path.join(W, 'cover.json'), encoding='utf-8')); bg = C.get('bg', {}); ENG = os.path.dirname(os.path.abspath(__file__))
FFMPEG = _find_ffmpeg()
tmp = tempfile.mkdtemp(prefix='cover-'); vf = [f'delogo=x={x}:y={y}:w={w}:h={h}' for x, y, w, h in bg.get('delogo', [])]
if bg.get('crop'): cw, ch, cx, cy = bg['crop']; vf += [f'crop={cw}:{ch}:{cx}:{cy}', 'scale=-1:1920:flags=lanczos', 'crop=1080:1920']
subprocess.run([FFMPEG, '-v', 'error', '-y', '-ss', str(bg.get('t', 10)), '-i', V, '-frames:v', '1', *(['-vf', ','.join(vf)] if vf else []), '-q:v', '1', os.path.join(tmp, 'bg.jpg')], check=True)
json.dump(C, open(os.path.join(tmp, 'cover.json'), 'w', encoding='utf-8'), ensure_ascii=False)
chrome = _find_chrome()
url = f"{Path(ENG, 'cover_poster.html').resolve().as_uri()}?data={Path(tmp, 'cover.json').resolve().as_uri()}&bg={Path(tmp, 'bg.jpg').resolve().as_uri()}"
subprocess.run([chrome, '--headless=new', '--no-sandbox', '--hide-scrollbars', '--disable-gpu', '--allow-file-access-from-files', '--force-device-scale-factor=1',
                '--window-size=1080,1920', '--virtual-time-budget=4000', f"--screenshot={os.path.join(tmp, 'shot.png')}", url], check=True, capture_output=True)
subprocess.run([FFMPEG, '-v', 'error', '-y', '-i', os.path.join(tmp, 'shot.png'), '-vf', 'crop=1080:1920:0:0', '-q:v', '2', OUT], check=True); print('cover ->', OUT)

#!/bin/bash
# 环境检查：Node / Chrome / ffmpeg / Python 依赖
cd "$(dirname "$0")/.."; ok=1
c(){ if eval "$2" >/dev/null 2>&1; then echo "✅ $1"; else echo "❌ $1  → $3"; ok=0; fi; }
c "Node ≥18" 'node -e "process.exit(+process.versions.node.split(\".\")[0]>=18?0:1)"' "安装 Node 18+（nodejs.org）"
c "puppeteer-core" '[ -d node_modules/puppeteer-core ]' "npm install"
CH=${CHROME:-}; for p in "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" /usr/bin/google-chrome /usr/bin/google-chrome-stable /usr/bin/chromium; do [ -z "$CH" ] && [ -x "$p" ] && CH=$p; done
c "Chrome ($CH)" '[ -n "$CH" ] && [ -x "$CH" ]' "安装 Google Chrome，或 export CHROME=<路径>"
c "ffmpeg / ffprobe" 'command -v ffmpeg && command -v ffprobe' "brew install ffmpeg / apt install ffmpeg"
c "ffmpeg libx264" 'ffmpeg -hide_banner -encoders | grep -q libx264' "需要带 libx264 的 ffmpeg"
c "Python3 + numpy + Pillow" 'python3 -c "import numpy, PIL"' "pip3 install numpy pillow"
c "curl" 'command -v curl' "安装 curl"
[ $ok = 1 ] && echo "环境 OK" || { echo "请先修复 ❌ 项"; exit 1; }

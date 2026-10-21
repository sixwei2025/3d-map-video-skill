#!/bin/bash
# 抽帧预览：engine/warfx/stills.sh <workDir> "f1,f2,..."  （起页面服务+瓦片代理，FORCE 渲染指定帧到 <work>/frames）
cd "$(dirname "$0")/../.."; export PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH; W=$1; F=$2
fp(){ python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])'; }
PORT=$(fp); TPORT=$(fp); python3 -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 & HS=$!
TILE_CACHE=$PWD/tile-cache python3 engine/tileproxy.py $TPORT >/dev/null 2>&1 & TP=$!; trap 'kill $HS $TP 2>/dev/null' EXIT
for i in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:$PORT/engine/warfx.html && curl -s -o /dev/null http://127.0.0.1:$TPORT/stats && break; sleep 0.3; done
TILES=http://127.0.0.1:$TPORT SCENE_PAGE=warfx.html FORCE=1 node engine/render_mac.mjs "$W" $PORT "$F"

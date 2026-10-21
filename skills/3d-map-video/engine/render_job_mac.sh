#!/bin/bash
# v2 渲染任务：起页面服务 + 本地瓦片缓存代理（随本脚本退出而停）→ PAR 个 worker 分摊帧 → 帧连续性检查（缺/坏帧强制重渲）。
# 用法: engine/render_job.sh <workDir> [a-b]     env: PAR=2  TILE_CACHE=<root>/tile-cache
set -u
cd "$(dirname "$0")/.."; W=$1; RANGE=${2:-}
export PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH
read N < <(python3 -c "import json;print(json.load(open('$W/meta.json'))['frames'])"); A=0; B=$N
[ -n "$RANGE" ] && { A=${RANGE%-*}; B=${RANGE#*-}; }
fp(){ python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])'; }
PORT=$(fp); TPORT=$(fp)
TC=${TILE_CACHE:-$PWD/tile-cache}; mkdir -p "$TC"
python3 -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 & HS=$!
TILE_CACHE=$TC python3 engine/tileproxy.py $TPORT >/dev/null 2>&1 & TP=$!
PIDS=""; trap 'kill $HS $TP $PIDS 2>/dev/null' EXIT INT TERM
for i in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:$PORT/engine/scene.html && curl -s -o /dev/null http://127.0.0.1:$TPORT/stats && break; sleep 0.3; done
export TILES=http://127.0.0.1:$TPORT
PAR=${PAR:-1}; L=$(( (B-A+PAR-1)/PAR ))
for k in $(seq 0 $((PAR-1))); do a=$((A+k*L)); b=$((a+L)); [ $b -gt $B ] && b=$B; [ $a -ge $b ] && continue
  ( for i in 1 2 3 4 5; do node engine/${RENDERER:-render_mac.mjs} "$W" $PORT "$a-$b" && break; echo "retry $i"; sleep 5; done ) & PIDS="$PIDS $!"
done
wait $PIDS
# v3.1 预取模式：只把瓦片拉进缓存，不截图、不做缺帧检查
if [ -n "${PREFETCH:-}" ]; then echo "prefetch tileproxy $(curl -s http://127.0.0.1:$TPORT/stats)"; exit 0; fi
for i in 1 2; do
  MISS=$(python3 engine/frames.py check "$W" 1 $A $B) && break
  echo "缺帧/坏帧: $MISS → 强制重渲"; FORCE=1 node engine/${RENDERER:-render_mac.mjs} "$W" $PORT "$MISS"
done
python3 engine/frames.py check "$W" 1 $A $B >/dev/null || echo "帧仍不完整（编码时用相邻帧补）"
echo "tileproxy $(curl -s http://127.0.0.1:$TPORT/stats)"
exit 0

#!/bin/bash
# 瓦片预取：按云端分段（与 offbox_split 同一切法）快速扫一遍相机路径（每 STEP 帧推一次相机、不截图），
# 瓦片经 tileproxy 进本地缓存，同时按段记请求清单 → offbox/<id>/tiles/seg<k>.list；再打成 ≤85MB 的 tgz 放进 store render-cache/。
# 用法: bash engine/prefetch.sh <workDir> <N段>    env: STEP=3 PAR=2 SETTLE_MAX=1500 TILE_CACHE=./tile-cache
set -u
cd "$(dirname "$0")/.."; W=$1; N=$2; ID=$(basename "$W"); O=offbox/$ID/tiles; mkdir -p $O
export PATH=$PWD/node22/bin:$PATH
NF=$(python3 -c "import json;print(json.load(open('$W/meta.json'))['frames'])"); L=$(( (NF+N-1)/N )); STEP=${STEP:-3}; PAR=${PAR:-2}
fp(){ python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])'; }
PORT=$(fp); TPORT=$(fp); TC=${TILE_CACHE:-./tile-cache}; mkdir -p $TC
python3 -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 & HS=$!
TILE_LOGDIR=$PWD/$O TILE_CACHE=$TC python3 engine/tileproxy.py $TPORT >/dev/null 2>&1 & TP=$!
trap 'kill $HS $TP 2>/dev/null' EXIT INT TERM
for i in $(seq 1 30); do curl -s -o /dev/null http://127.0.0.1:$PORT/engine/scene.html && curl -s -o /dev/null http://127.0.0.1:$TPORT/stats && break; sleep 0.3; done
export TILES=http://127.0.0.1:$TPORT PREFETCH=1 SETTLE_MAX=${SETTLE_MAX:-1500} CHUNK=60
T0=$(date +%s)
for k in $(seq 0 $((N-1))); do a=$((k*L)); b=$((a+L)); [ $b -gt $NF ] && b=$NF; [ $a -ge $b ] && continue
  : > $O/seg$k.list; curl -s http://127.0.0.1:$TPORT/log/seg$k.list >/dev/null; t=$(date +%s)
  PIDS=""; for w in $(seq 0 $((PAR-1))); do
    LIST=$(python3 -c "print(','.join(str(f) for f in list(range($a,$b,$STEP))[$w::$PAR]+([$b-1] if $w==0 else [])))")
    node engine/render.mjs "$W" $PORT "$LIST" >/dev/null 2>&1 & PIDS="$PIDS $!"; done
  wait $PIDS
  echo "seg$k [$a,$b) $(sort -u $O/seg$k.list | wc -l) tiles $(( $(date +%s)-t ))s proxy $(curl -s http://127.0.0.1:$TPORT/stats)"
done
echo "prefetch total $(( $(date +%s)-T0 ))s"
python3 engine/tilepack.py $ID $TC $O

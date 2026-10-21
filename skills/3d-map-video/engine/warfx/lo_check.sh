#!/bin/bash
# 1021d 低清自检只渲关键段（代替整片 540 渲 4 轮）：engine/warfx/lo_check.sh <lo_workDir> <audio.wav> "33-44,65-72,113-126"   → <lo_workDir>/check_<a>-<b>.mp4
# 每段单独出带声小样（看镜头速度/标签/地形），再用 contact 拼图看静帧；默认 PAR=2、render_fast。
set -e; cd "$(dirname "$0")/../.."; export PATH=/opt/homebrew/bin:/usr/bin:/bin:$PATH; W=$1; A=$2; SEGS=$3; FPS=$(python3 -c "import json;print(json.load(open('$W/meta.json'))['fps'])")
for s in ${SEGS//,/ }; do a=${s%-*}; b=${s#*-}; fa=$((a*FPS)); fb=$((b*FPS))
  RENDERER=${RENDERER:-render_fast.mjs} SCENE_PAGE=warfx.html PAR=${PAR:-2} bash engine/render_job_mac.sh $W $fa-$fb
  ffmpeg -y -v error -framerate $FPS -start_number $fa -i $W/frames/f%05d.jpg -ss $a -t $((b-a)) -i $A -frames:v $((fb-fa)) -c:v libx264 -preset veryfast -crf 22 -pix_fmt yuv420p -c:a aac -b:a 128k -shortest $W/check_$a-$b.mp4
  echo "check $W/check_$a-$b.mp4"; done

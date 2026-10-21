#!/bin/bash
# WarFX 成片收尾：帧序列 + 封面(前 3 帧) + 混音 → 高码率 H.264（High/yuv420p/定码率 17.5M ≈ 全片 14.8Mbps/faststart）
# 定码率版（全片约 14.8Mbps，暗底画面 crf 打不到 14M 时用）。用法: engine/warfx/finish_br.sh <workDir> <cover.jpg> <audio.wav> <out.mp4>
set -e; export PATH=/opt/homebrew/bin:/usr/bin:/bin:$PATH; W=$1; CV=$2; A=$3; OUT=$4
FPS=$(python3 -c "import json;print(json.load(open('$W/meta.json'))['fps'])"); NF=${COVER_FRAMES:-3}; CD=$(python3 -c "print($NF/$FPS)")
ffmpeg -y -v error -loop 1 -framerate $FPS -t $CD -i "$CV" -framerate $FPS -i "$W/frames/f%05d.jpg" -i "$A" -filter_complex \
 "[0:v]scale=1080:1920,setsar=1,format=yuv420p,trim=end_frame=$NF[c];[1:v]setsar=1,format=yuv420p[m];[c][m]concat=n=2:v=1:a=0,unsharp=5:5:0.4,scale=in_range=pc:out_range=tv,format=yuv420p[v];[2:a]adelay=$(python3 -c "print(int($CD*1000))"):all=1,aresample=48000[a]" \
 -map "[v]" -map "[a]" -c:v libx264 -preset slow -profile:v high -b:v 17.5M -minrate 15M -maxrate 18M -bufsize 18M -x264-params nal-hrd=vbr -pix_fmt yuv420p -color_primaries bt709 -color_trc bt709 -colorspace bt709 -r $FPS -g 60 \
 -c:a aac -b:a 192k -ar 48000 -shortest -movflags +faststart "$OUT"
ffprobe -v error -show_entries stream=codec_name,profile,pix_fmt,width,height,bit_rate:format=duration,bit_rate -of compact "$OUT"

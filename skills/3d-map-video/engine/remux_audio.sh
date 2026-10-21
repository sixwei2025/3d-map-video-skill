#!/bin/bash
# 只换音轨不动画面（v2.1 起）：视频 -c:v copy，音轨 = lead 秒静音（封面段）+ mix.wav，AAC，faststart。
# 用法: remux_audio.sh <in.mp4 带封面的成片> <mix.wav> <out.mp4> [lead=0.1] [abitrate=192k]
set -e; IN=$1; MIX=$2; OUT=$3; LEAD=${4:-0.1}; AB=${5:-192k}; MS=$(python3 -c "print(int(round($LEAD*1000)))")
ffmpeg -y -loglevel error -i "$IN" -i "$MIX" -filter_complex "[1:a]aformat=sample_rates=48000:channel_layouts=stereo,adelay=${MS}|${MS}[a]" \
  -map 0:v:0 -map '[a]' -c:v copy -c:a aac -b:a $AB -ar 48000 -movflags +faststart "$OUT"
echo "remux -> $OUT"

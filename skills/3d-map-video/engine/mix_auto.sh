#!/bin/bash
# v3.2 混音分发（2026-10-20）：run_v3_full.sh 调用。war_ 开头 → 战争主题；否则 episode.music_theme（如 city）；都没有 → 旧 mix.py。
# 用法: engine/mix_auto.sh <workDir> <episode.json> <out_nocover.mp4>    DRY=1 时只出 wav 不封装
set -e; export PATH=/opt/homebrew/bin:$PATH; W=$1; EP=$2; OUT=$3
TH=$(python3 -c "import json,os,sys;e=json.load(open('$EP'));t='war' if e['id'].startswith('war_') else e.get('music_theme','');print(t if t and os.path.exists('assets/music/%s_theme.json'%t) else '')" 2>/dev/null || true)
if [ -z "$TH" ]; then echo "mix_auto: 无系列主题 → mix.py"; [ -n "$DRY" ] && { python3 engine/mix.py $W --wav $W/audio/mix_dry.wav; exit; }; exec python3 engine/mix.py $W "$OUT"; fi
echo "mix_auto: 主题=$TH → mix_theme.py"; WAV=$W/audio/mix_theme${DRY:+_dry}.wav
python3 engine/mix_theme.py $W "$EP" $WAV
[ -n "$DRY" ] && exit 0
VD=$(ffprobe -v error -show_entries format=duration -of csv=p=0 $W/map.mp4)
ffmpeg -y -loglevel error -i $W/map.mp4 -i $WAV -map 0:v -map 1:a -c:v copy -af apad -t $VD -c:a aac -b:a 192k -movflags +faststart "$OUT"
echo "mixed -> $OUT ($TH)"

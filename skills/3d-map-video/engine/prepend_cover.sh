#!/bin/bash
# v2 模板：把封面放在成片最前面 N 帧（默认 3 帧 = 0.1s @30fps），封面段静音，原片音画整体后移 → 同步不变。不动地图渲染。
# 用法: engine/prepend_cover.sh <cover.jpg> <in.mp4> <out.mp4> [frames=3]
# 编码: Mac 用 h264_videotoolbox（VBR 默认 14M），Linux 用 libx264 crf17；音频 AAC 192k；+faststart
set -e; export PATH=/opt/homebrew/bin:/usr/bin:/bin:$PATH
C=$1; IN=$2; OUT=$3; NF=${4:-3}
read W H FPS < <(ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 "$IN" | tr ',' ' ')
DUR=$(python3 -c "from fractions import Fraction as F;print(float($NF/F('$FPS')))")
if [ "$(uname)" = Darwin ]; then VC=(-c:v h264_videotoolbox -profile:v high -b:v ${VBR:-14M} -maxrate ${MAXRATE:-18M} -bufsize ${BUFSIZE:-28M}); else VC=(-c:v libx264 -preset medium -crf 17); fi
ffmpeg -y -loglevel error -loop 1 -framerate "$FPS" -t "$DUR" -i "$C" -f lavfi -t "$DUR" -i anullsrc=r=48000:cl=stereo -i "$IN" -filter_complex \
 "[0:v]scale=${W}:${H}:force_original_aspect_ratio=increase,crop=${W}:${H},setsar=1,format=yuv420p,trim=end_frame=${NF},setpts=PTS-STARTPTS[cv];[2:v]setsar=1,format=yuv420p[mv];[2:a]aresample=48000,aformat=channel_layouts=stereo[ma];[cv][1:a][mv][ma]concat=n=2:v=1:a=1[v][a]" \
 -map "[v]" -map "[a]" "${VC[@]}" -g 60 -pix_fmt yuv420p -r "$FPS" -c:a aac -b:a 192k -ar 48000 -movflags +faststart "$OUT"
ffprobe -v error -show_entries stream=codec_type,nb_frames,duration:format=duration -of compact "$OUT"

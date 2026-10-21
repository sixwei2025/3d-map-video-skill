#!/bin/bash
# 交付版高码率编码（2026-10-19 萨尔浒 v2.2 起，替代原 _small 4.6Mbps 版：视频号二次压缩后发糊）
# 规格：1080x1920，30fps，H.264 High，yuv420p（tv range，不是 yuvj420p），BT.709 标签，+faststart；
#       默认 libx264 2-pass 14M（maxrate 16M / bufsize 24M）→ 约 12–16Mbps，140s ≈ 250MB。DELIVER_MODE=crf 时用 crf 16 + maxrate 16M。
#       输入如果是 VideoToolbox 出的 yuvj420p/BT.601，会正确转换到 tv range + BT.709，颜色不变。
#       无 libx264 时退回 h264_videotoolbox 14M/16M（单遍）。720p 预览版不走这里，参数不变。
# 用法: engine/deliver_hq.sh <in.mp4 带封面的 hq 母版> <out.mp4> [音频来源.mp4，默认=in]
# 环境: DELIVER_MODE=2pass|crf  DELIVER_VBR=14M DELIVER_MAXRATE=16M DELIVER_BUFSIZE=24M DELIVER_CRF=16 DELIVER_PRESET=slow
set -e; export PATH=/opt/homebrew/bin:/usr/bin:/bin:$PATH
IN=$1; OUT=$2; AS=${3:-$1}; [ -f "$IN" ] && [ -n "$OUT" ] || { echo "用法: deliver_hq.sh in.mp4 out.mp4 [audio.mp4]"; exit 2; }
pv(){ ffprobe -v error -select_streams v:0 -show_entries stream=$1 -of default=nw=1:nk=1 "$IN"; }
PF=$(pv pix_fmt); RG=$(pv color_range); CS=$(pv color_space)
IR=tv; { [ "$RG" = pc ] || [[ "$PF" == yuvj* ]]; } && IR=pc
IM=bt601; [ "$CS" = bt709 ] && IM=bt709
VF="scale=w=1080:h=1920:flags=lanczos+accurate_rnd+full_chroma_int:in_range=$IR:out_range=tv:in_color_matrix=$IM:out_color_matrix=bt709,format=yuv420p,setparams=color_primaries=bt709:color_trc=bt709:colorspace=bt709:range=tv"   # setparams：否则 primaries/trc 会写成 unknown
TAGS=(-pix_fmt yuv420p -r 30 -g 60 -keyint_min 30 -colorspace bt709 -color_primaries bt709 -color_trc bt709 -color_range tv)
AC=$(ffprobe -v error -select_streams a:0 -show_entries stream=codec_name -of default=nw=1:nk=1 "$AS")
if [ "$AC" = aac ]; then AOPT=(-c:a copy); else AOPT=(-c:a aac -b:a 192k -ar 48000); fi
MAP=(-map 0:v:0 -map 1:a:0?)
VBR=${DELIVER_VBR:-14M}; MR=${DELIVER_MAXRATE:-16M}; BS=${DELIVER_BUFSIZE:-24M}; PR=${DELIVER_PRESET:-slow}
if ffmpeg -hide_banner -encoders 2>/dev/null | grep -q ' libx264 '; then
  X=(-c:v libx264 -preset $PR -profile:v high -level:v 4.1)
  if [ "${DELIVER_MODE:-2pass}" = crf ]; then
    ffmpeg -y -loglevel error -i "$IN" -i "$AS" "${MAP[@]}" -vf "$VF" "${X[@]}" -crf ${DELIVER_CRF:-16} -maxrate $MR -bufsize $BS "${TAGS[@]}" "${AOPT[@]}" -movflags +faststart "$OUT"
  else
    PL=$(mktemp -d)/x264; X+=(-b:v $VBR -maxrate $MR -bufsize $BS)
    ffmpeg -y -loglevel error -i "$IN" -vf "$VF" "${X[@]}" "${TAGS[@]}" -pass 1 -passlogfile "$PL" -an -f null /dev/null
    ffmpeg -y -loglevel error -i "$IN" -i "$AS" "${MAP[@]}" -vf "$VF" "${X[@]}" "${TAGS[@]}" -pass 2 -passlogfile "$PL" "${AOPT[@]}" -movflags +faststart "$OUT"
    rm -rf "$(dirname "$PL")"
  fi
else
  ffmpeg -y -loglevel error -i "$IN" -i "$AS" "${MAP[@]}" -vf "$VF" -c:v h264_videotoolbox -profile:v high -b:v $VBR -maxrate $MR -bufsize $BS "${TAGS[@]}" "${AOPT[@]}" -movflags +faststart "$OUT"
fi
NI=$(ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of default=nw=1:nk=1 "$IN"); NO=$(ffprobe -v error -select_streams v:0 -show_entries stream=nb_frames -of default=nw=1:nk=1 "$OUT")
[ "$NI" = "$NO" ] || { echo "deliver_hq: 帧数不一致 in=$NI out=$NO"; exit 1; }
ffprobe -v error -show_entries stream=codec_type,profile,pix_fmt,color_space,bit_rate,nb_frames:format=duration,size,bit_rate -of compact "$OUT"

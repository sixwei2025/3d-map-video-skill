#!/bin/bash
# [Mac] v2 硬件编码：h264_videotoolbox，14M/18M，yuv420p，+faststart。用法: engine/encode_vt.sh <workDir> [a b] [out.mp4]
# v3：编码时加轻度锐化 cas（SHARPEN=0 关闭；默认 0.4）
# v3.1：scene.json 有 chapters 时自动叠加顶部章节进度条（engine/progressbar.py；PBAR=0 关闭；只在整片编码 a=0 时叠，分段小样按真实时间也可叠）
set -e
cd "$(dirname "$0")/.."; export PATH=/opt/homebrew/bin:/usr/bin:/bin:$PATH; W=$1
read FPS N < <(python3 -c "import json;m=json.load(open('$W/meta.json'));print(m['fps'],m['frames'])")
A=${2:-0}; B=${3:-$N}; OUT=${4:-$W/map.mp4}; SH=${SHARPEN:-0.4}
python3 engine/frames.py fill "$W" 1 $A $B
VC=(-c:v h264_videotoolbox -profile:v high -b:v ${VBR:-14M} -maxrate ${MAXRATE:-18M} -bufsize ${BUFSIZE:-28M} -g 60 -pix_fmt yuv420p -movflags +faststart)
[ "$(uname)" = Darwin ] || VC=(-c:v libx264 -crf 18 -preset veryfast -pix_fmt yuv420p -movflags +faststart)
IN=(-framerate $FPS -start_number 0 -i "$W/seq_${A}_${B}/s%05d.jpg")
if [ "${PBAR:-1}" != 0 ] && python3 engine/progressbar.py "$W" | grep -q '^pbar'; then
  P=$W/pbar; EXTRA=(); OFF=$(python3 -c "print($A/$FPS)"); while read f || [ -n "$f" ]; do EXTRA+=(-itsoffset $OFF -loop 1 -framerate $FPS -i "$P/$f"); done < $P/inputs.txt
  OFF=$(python3 -c "print($A/$FPS)")
  { [ "$SH" != 0 ] && echo "[0:v]setpts=PTS+$OFF/TB,cas=$SH[s0];" || echo "[0:v]setpts=PTS+$OFF/TB[s0];"; sed "s/^\[0:v\]\[1:v\]overlay/[s0][1:v]overlay/" $P/filter.txt; } > $P/filter_run.txt
  # 进度条 color 源从 0 开始计时；分段编码时让它们也从 OFF 开始
  python3 - "$P/filter_run.txt" "$OFF" <<'PY'
import sys,re;p,o=sys.argv[1],float(sys.argv[2]);s=open(p).read()
if o>0: s=re.sub(r"(color=c=[^;\[]*?:r=[\d.]+)",lambda m:m.group(1)+f",setpts=PTS+{o}/TB",s)
open(p,'w').write(s)
PY
  ffmpeg -y -loglevel error "${IN[@]}" "${EXTRA[@]}" -filter_complex_script $P/filter_run.txt -map "[out]" -frames:v $((B-A)) -output_ts_offset 0 "${VC[@]}" "$OUT.tmp.mp4"
  ffmpeg -y -loglevel error -i "$OUT.tmp.mp4" -c copy -movflags +faststart -avoid_negative_ts make_zero "$OUT" && rm -f "$OUT.tmp.mp4"
else
  VF=(); [ "$SH" != "0" ] && VF=(-vf "cas=$SH")
  ffmpeg -y -loglevel error "${IN[@]}" -frames:v $((B-A)) "${VF[@]}" "${VC[@]}" "$OUT"
fi
ffprobe -v error -count_frames -show_entries stream=codec_name,width,height,nb_read_frames:format=bit_rate -of compact "$OUT"

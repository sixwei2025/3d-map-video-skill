#!/bin/bash
# 一条命令全链：compile → 预取瓦片 → 逐帧渲染 → 编码(锐化+章节进度条) → 系列主题配乐混音 → 全屏实拍 broll → 封面 → 封面放首帧 → 14Mbps 交付 + 720p 预览 + 自检
# 用法（在 skill 根目录）：ID=<episode id> bash scripts/run_all.sh
#   必须先有：episodes/<ID>.json、work/v2/<ID>/audio/voice.wav（配音，见 SKILL.md 第 5 步）
#   env: MODE=full|sample  SAMPLE="0-150 1650-1800"  PAR=2（并行 Chrome 数）  NOPREFETCH=1  CHROME=<chrome 路径>  TILE_CACHE=./tile-cache
# 长任务请后台跑并防睡眠：  nohup caffeinate -i env ID=xxx bash scripts/run_all.sh >/dev/null 2>&1 &   （Linux 用 systemd-inhibit 或直接 nohup）
cd "$(dirname "$0")/.."; [ -d /opt/homebrew/bin ] && export PATH=/opt/homebrew/bin:$PATH
ID=${ID:?请设置 ID}; MODE=${MODE:-full}; PAR=${PAR:-2}; export PAR; W=work/v2/$ID; O=out/$ID; mkdir -p $O; rm -f $O/DONE_$MODE $O/FAILED_$MODE
LOG=$O/$MODE.log; exec > >(tee -a $LOG) 2>&1
fail(){ echo "FAILED: $* $(date '+%F %T')"; echo "$*" > $O/FAILED_$MODE; exit 1; }
if [ "$(uname)" = Darwin ]; then RJ=engine/render_job_mac.sh; SZ(){ stat -f %z "$1"; }; SHA="shasum -a 256"; PV=(-c:v h264_videotoolbox -profile:v high -b:v 1250k -maxrate 1800k -bufsize 2500k)
else RJ=engine/render_job.sh; SZ(){ stat -c %s "$1"; }; SHA=sha256sum; PV=(-c:v libx264 -preset veryfast -b:v 1250k -maxrate 1800k -bufsize 2500k); fi
python3 engine/compile.py episodes/$ID.json || fail compile
[ -f $W/audio/voice.wav ] || echo "WARN: 缺 $W/audio/voice.wav（无口播时只出配乐）"
N=$(python3 -c "import json;print(json.load(open('$W/meta.json'))['frames'])")
echo "== $ID $MODE PAR=$PAR frames=$N $(date '+%F %T')"; T0=$(date +%s)
[ -z "$NOPREFETCH" ] && { PREFETCH=1 FORCE=1 SETTLE_MAX=${PF_SETTLE:-6000} bash $RJ $W 0-$N || fail prefetch; }
if [ "$MODE" = sample ]; then
  for R in ${SAMPLE:-0-150 1650-1800}; do a=${R%-*}; b=${R#*-}
    bash $RJ $W $a-$b || fail "render $R"; bash engine/encode_vt.sh $W $a $b $O/sample_${a}_${b}.mp4 || fail "encode $R"; done
  echo "小样在 $O/sample_*.mp4 ——先看小样再跑全片"; echo ok > $O/DONE_sample; exit 0
fi
bash $RJ $W 0-$N || fail render
python3 engine/frames.py check $W 1 0 $N >/dev/null || echo "WARN: 仍有缺帧，编码时用相邻帧补"
bash engine/encode_vt.sh $W || fail encode
bash engine/mix_auto.sh $W episodes/$ID.json $O/${ID}_nocover.mp4 || fail mix
python3 engine/broll.py episodes/$ID.json $O/${ID}_nocover.mp4 || fail broll
CV=${COVER:-$W/cover_1080x1920.jpg}
[ -f "$CV" ] || python3 engine/cover_poster.py $W $W/map.mp4 "$CV" || fail cover_poster
bash engine/prepend_cover.sh "$CV" $O/${ID}_nocover.mp4 $O/${ID}_hq.mp4 ${COVER_FRAMES:-1} || fail cover   # 封面=首帧（0.01–0.03s）
ffmpeg -y -loglevel error -i $O/${ID}_hq.mp4 -frames:v 1 $O/frame0.png
bash engine/deliver_hq.sh $O/${ID}_hq.mp4 $O/${ID}_deliver.mp4 || fail deliver
ffmpeg -y -loglevel error -i $O/${ID}_hq.mp4 -vf scale=720:1280:flags=lanczos "${PV[@]}" -pix_fmt yuv420p -c:a aac -b:a 96k -movflags +faststart $O/${ID}_preview_720p.mp4 || fail preview
python3 scripts/selfcheck.py $ID | tee $O/selfcheck.txt
(cd $O && $SHA ${ID}_deliver.mp4 ${ID}_preview_720p.mp4 > sha256.txt)
echo "total $(( $(date +%s)-T0 ))s  deliver=$(SZ $O/${ID}_deliver.mp4) bytes"; echo ok > $O/DONE_full

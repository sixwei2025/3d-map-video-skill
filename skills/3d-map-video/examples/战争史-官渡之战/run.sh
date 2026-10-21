#!/bin/bash
# 官渡之战 3D 地图战争片一条龙（WarFX 引擎示例）。在 skill 根目录（skills/3d-map-video）下运行：
#   bash "examples/战争史-官渡之战/run.sh" voice   # 1) 配音（需本地 TTS，见 gen_voice.py；没有就跳过，直接用仓库里的 timeline.json + 你自己的 voice.wav）
#   bash "examples/战争史-官渡之战/run.sh" check   # 2) 低清自检：只渲钩子 + 3 个地形侧视（540×960，约 3 分钟）
#   bash "examples/战争史-官渡之战/run.sh" hi      # 3) 全尺寸 1080×1920 渲染 → 首帧封面 → 定码率编码 → out/war_guandu/
# Mac 上建议 nohup caffeinate -is bash ... & 后台跑；同一时间只跑一个重任务。实测 M5：配音约 10 分 + 自检 2 轮 6 分 + 渲染 9.4 分 + 编码 2.8 分 ≈ 29 分。
cd "$(dirname "$0")/../.."; export PATH=/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH; STAGE=${1:-check}
ID=war_guandu; W=work/v2/$ID; WL=work/v2/${ID}_lo; O=out/$ID; P="examples/战争史-官渡之战"; PY=${PY:-python3}; mkdir -p $O $W/audio episodes
fail(){ echo "FAILED: $*"; exit 1; }
case $STAGE in
voice) $PY "$P/gen_voice.py" || fail voice ;;
check|hi)

  $PY "$P/build.py" || fail build; $PY "$P/build.py" 0.5 || fail build_lo
  [ -f "$P/voice.wav" ] || { echo "没有 $P/voice.wav：用静音代替（只看画面）"; ffmpeg -v error -y -f lavfi -i anullsrc=r=48000:cl=mono -t $(python3 -c "import json;print(json.load(open('$P/timeline.json'))['duration'])") "$P/voice.wav"; }
  $PY engine/warfx/sfx.py $W/scene_sfx.json $W/audio/sfx.wav || fail sfx; cp "$P/voice.wav" $W/audio/voice.wav
  python3 -c "import json;d=json.load(open('$W/meta.json'));json.dump({'duration':d['duration']},open('$W/audio.json','w'))"
  python3 - <<PYX
import json;L=json.load(open('$P/timeline.json'))['lines'];T=lambda i:L[i]['t0']
json.dump({"id":"$ID","music":{"sections":[{"t0":0,"track":"war_theme"},{"t0":T(2),"track":"final_battle"},{"t0":T(3),"track":"war_theme"},{"t0":T(8),"track":"final_battle"},{"t0":T(11),"track":"war_theme"},{"t0":T(15),"track":"@drone"},{"t0":T(21),"track":"lost_bad_place"},{"t0":T(26),"track":"determined_pursuit"},{"t0":T(28),"track":"final_battle"},{"t0":T(33),"track":"emotional_piano"},{"t0":T(37),"track":"bittersweet"}]}},open('episodes/$ID.json','w'))
PYX
  if [ -f assets/music/war_theme.ogg ]; then $PY engine/mix_theme.py $W episodes/$ID.json $W/audio/vm.wav || fail mix_theme; else echo "没有配乐（先跑 scripts/fetch_music.sh）：只用人声"; cp $W/audio/voice.wav $W/audio/vm.wav; fi
  $PY engine/warfx/mix_fx.py $W/audio/vm.wav $W/audio/sfx.wav $W/audio/voice.wav $W/audio/final.wav --sfx-db 0 --duck 4 || fail mix_fx
  if [ $STAGE = check ]; then
    SEGS=${SEGS:-$(python3 -c "
import json;L=json.load(open('$P/timeline.json'))['lines'];r=lambda a,b:f'{int(L[a][\"t0\"])}-{int(L[b][\"t1\"])+1}'
print(','.join([r(2,3),r(7,8),r(14,14),r(26,28)]))")}
    bash engine/warfx/lo_check.sh $WL $W/audio/final.wav "$SEGS" || fail lo_check
  else
    rm -rf $W/frames; RENDERER=${RENDERER:-render_fast.mjs} SCENE_PAGE=warfx.html PAR=${PAR:-3} bash engine/render_job_mac.sh $W || fail render; python3 engine/frames.py check $W 1 >/dev/null || fail frames
    fp(){ python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])'; }
    PORT=$(fp); TPORT=$(fp); python3 -m http.server $PORT --bind 127.0.0.1 >/dev/null 2>&1 & HS=$!; TILE_CACHE=$PWD/tile-cache python3 engine/tileproxy.py $TPORT >/dev/null 2>&1 & TP=$!
    sleep 1.5; node engine/warfx/cover.mjs $W $PORT http://127.0.0.1:$TPORT $O/官渡之战-封面.jpg; R=$?; kill $HS $TP; [ $R = 0 ] || fail cover
    bash engine/warfx/finish_br.sh $W $O/官渡之战-封面.jpg $W/audio/final.wav $O/官渡之战.mp4 || fail encode
    $PY engine/warfx/contact.py $O/官渡之战.mp4 $O/官渡之战-抽帧.jpg $(python3 "$P/contact_times.py")
  fi ;;
*) echo "用法: run.sh voice|check|hi"; exit 1 ;;
esac
echo "OK $STAGE"

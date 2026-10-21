#!/bin/bash
# 下载两首系列主题曲（CC0 1.0，来源 OpenGameArt）到 assets/music/
cd "$(dirname "$0")/.."; set -e
curl -L -o assets/music/war_theme.ogg "https://opengameart.org/sites/default/files/war%20theme%20ver%202_0.ogg"
curl -L -o /tmp/dp.wav "https://opengameart.org/sites/default/files/determined_pursuit_loop.wav"
ffmpeg -y -loglevel error -i /tmp/dp.wav -c:a libvorbis -q:a 5 assets/music/determined_pursuit.ogg && rm -f /tmp/dp.wav
ls -l assets/music/*.ogg

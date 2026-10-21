#!/usr/bin/env python3
"""后台启动长任务（脱离终端 + 防睡眠）。用法: ID=<id> python3 scripts/launch.py scripts/run_all.sh
Mac 用 caffeinate -i 防睡眠；Linux 有 systemd-inhibit 就用，没有就直接跑。日志 out/launch.log"""
import os, shutil, subprocess, sys
script = sys.argv[1]; os.makedirs('out', exist_ok=True)
pre = ['/usr/bin/caffeinate', '-i'] if os.path.exists('/usr/bin/caffeinate') else (['systemd-inhibit', '--what=sleep:idle'] if shutil.which('systemd-inhibit') else [])
if os.fork() == 0:
    os.setsid()
    if os.fork() == 0:
        subprocess.Popen(pre + ['/bin/bash', script], stdout=open('out/launch.log', 'a'), stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, start_new_session=True)
    os._exit(0)
print('launched', script)

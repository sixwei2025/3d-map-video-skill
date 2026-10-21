#!/usr/bin/env python3
"""本地瓦片缓存服务：/esri/{z}/{y}/{x}  /dem/{z}/{x}/{y}.png  → 磁盘缓存(./tile-cache)，未命中才去上游取。
用法: tileproxy.py <port> [--offline]"""
import sys, os, time, urllib.request, urllib.error, threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
ROOT = os.environ.get('TILE_CACHE', './tile-cache'); OFF = '--offline' in sys.argv
UP = {'esri': 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{a}/{b}/{c}',
      'dem': 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{a}/{b}/{c}'}
stats = {'hit': 0, 'miss': 0, 'err': 0}; lock = threading.Lock()
LOGDIR = os.environ.get('TILE_LOGDIR'); LOG = [None]  # 预取：/log/<name> 切换请求清单文件，每个瓦片请求记一行相对路径
class H(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'
    def log_message(self, *a): pass
    def do_GET(self):
        p = self.path.split('?')[0].strip('/').split('/')
        if p == ['stats']: return self.send(200, repr(stats).encode(), 'text/plain')
        if len(p) == 2 and p[0] == 'log' and LOGDIR:
            with lock:
                if LOG[0]: LOG[0].close()
                LOG[0] = open(os.path.join(LOGDIR, p[1]), 'a')
            return self.send(200, b'ok', 'text/plain')
        if len(p) != 4 or p[0] not in UP: return self.send(404, b'', 'text/plain')
        f = os.path.join(ROOT, *p)
        if LOG[0]:
            with lock: LOG[0].write('/'.join(p)+'\n'); LOG[0].flush()
        if os.path.exists(f):
            with lock: stats['hit'] += 1
            return self.send(200, open(f, 'rb').read(), 'image/png' if p[0] == 'dem' else 'image/jpeg')
        if OFF: return self.send(404, b'', 'text/plain')
        try:
            req = urllib.request.Request(UP[p[0]].format(a=p[1], b=p[2], c=p[3]), headers={'User-Agent': 'Mozilla/5.0'})
            for k in range(4):  # 上游失败（5xx/超时/断连）重试 3 次，退避 1/2/4s；404/400 不重试
                try: data = urllib.request.urlopen(req, timeout=30).read(); break
                except urllib.error.HTTPError as e:
                    if e.code in (400, 404) or k == 3: raise
                except Exception:
                    if k == 3: raise
                time.sleep(2 ** k)
            os.makedirs(os.path.dirname(f), exist_ok=True); open(f+'.tmp', 'wb').write(data); os.replace(f+'.tmp', f)
            with lock: stats['miss'] += 1
            self.send(200, data, 'image/png' if p[0] == 'dem' else 'image/jpeg')
        except Exception as e:
            with lock: stats['err'] += 1
            self.send(502, b'', 'text/plain')
    def send(self, code, body, ct):
      try:
        self.send_response(code); self.send_header('Content-Type', ct); self.send_header('Content-Length', str(len(body)))
        self.send_header('Access-Control-Allow-Origin', '*'); self.send_header('Cache-Control', 'max-age=86400'); self.end_headers(); self.wfile.write(body)
      except (BrokenPipeError, ConnectionResetError): pass
class S(ThreadingHTTPServer):
    daemon_threads = True
    def handle_error(self, *a): pass
S(('127.0.0.1', int(sys.argv[1])), H).serve_forever()

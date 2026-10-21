#!/usr/bin/env python3
"""把每段的瓦片请求清单打成 ≤85MB 的 tgz（成员路径 tile-cache/<esri|dem>/z/y/x），写到 store render-cache/，并写 offbox/<id>/tiles/seg<k>.cache（逗号分隔包名）。
用法: tilepack.py <id> <TILE_CACHE> <tilesDir>"""
import sys, os, tarfile, glob
ID, TC, O = sys.argv[1:4]; STORE = os.environ.get('OFFBOX_STORE', '/cursor/stores/store-ad404050-07b7-494c-b493-d03af0ee8f3b'); RC = STORE+'/render-cache'
LIM = 85*1024*1024; tot = 0
for lf in sorted(glob.glob(O+'/seg*.list')):
    k = os.path.basename(lf)[3:-5]; paths = sorted({l.strip() for l in open(lf) if l.strip()}); paths = [p for p in paths if os.path.exists(os.path.join(TC, p))]
    names = []; j = 0; tf = None; sz = 0
    def openj():
        global tf, sz, j
        n = f'tiles-{ID}-seg{k}-{j}.tgz'; names.append(n); tf = tarfile.open(os.path.join(O, n), 'w:gz'); sz = 0; j += 1
    openj()
    for p in paths:
        f = os.path.join(TC, p); s = os.path.getsize(f)
        if sz + s > LIM: tf.close(); openj()
        tf.add(f, arcname='tile-cache/'+p); sz += s
    tf.close()
    for n in names:
        src = os.path.join(O, n); b = os.path.getsize(src); tot += b
        if os.environ.get('LOCAL_ONLY') or (os.path.exists(os.path.join(RC, n)) and os.path.getsize(os.path.join(RC, n)) == b): continue  # 只打本地包 / store 里已有同名同大小则跳过
        with open(src, 'rb') as a, open(os.path.join(RC, n)+'.tmp', 'wb') as w: w.write(a.read())
        os.replace(os.path.join(RC, n)+'.tmp', os.path.join(RC, n))
        assert os.path.getsize(os.path.join(RC, n)) == b, 'store 写入不完整 '+n
    if not os.environ.get('LOCAL_ONLY'): open(os.path.join(O, f'seg{k}.cache'), 'w').write(','.join(names))
    print(f'seg{k}: {len(paths)} tiles -> {names} {sum(os.path.getsize(os.path.join(O,n)) for n in names)/1e6:.1f}MB')
print(f'total {tot/1e6:.1f}MB -> {RC}')

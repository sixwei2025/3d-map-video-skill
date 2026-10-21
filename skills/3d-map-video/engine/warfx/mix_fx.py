#!/usr/bin/env python3
"""WarFX 混音收尾：mix_theme.py 的「人声+系列配乐」再叠 sfx.py 音效床；口播段音效再压 DUCK dB，真峰 ≤ -1.5 dBTP。
用法: python3 engine/warfx/mix_fx.py <voice_music.wav> <sfx.wav> <voice.wav> <out.wav> [--sfx-db 0] [--duck 4]"""
import sys,subprocess,wave,numpy as np
a=sys.argv;BASE,SFX,VO,OUT=a[1:5];G=float(a[a.index('--sfx-db')+1]) if '--sfx-db' in a else 0.0;DK=float(a[a.index('--duck')+1]) if '--duck' in a else 4.0;SR=48000
def rd(f):
    subprocess.run(['ffmpeg','-v','error','-y','-i',f,'-ac','2','-ar',str(SR),'-c:a','pcm_s16le',f+'.s.wav'],check=True)
    with wave.open(f+'.s.wav') as w:x=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(np.float32).reshape(-1,2)/32768
    import os;os.remove(f+'.s.wav');return x
b,s,v=rd(BASE),rd(SFX),rd(VO);N=len(b);fit=lambda x:x[:N] if len(x)>=N else np.vstack([x,np.zeros((N-len(x),2),np.float32)]);s,v=fit(s),fit(v)
hop=SR//50;m=np.sqrt(np.mean(v[:N//hop*hop,0].reshape(-1,hop)**2,1)+1e-12);act=(20*np.log10(m)>-40).astype(np.float32)
act=np.convolve(act,np.ones(15)/15,'same');g=np.interp(np.arange(N),np.arange(len(act))*hop,10**(-DK*act/20))
mix=b+s*(10**(G/20))*g[:,None]
with wave.open(OUT+'.t.wav','wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((np.clip(mix,-1,1)*32767).astype('<i2').tobytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',OUT+'.t.wav','-af','alimiter=limit=0.84:attack=2:release=60:level=disabled','-c:a','pcm_s16le',OUT],check=True);import os;os.remove(OUT+'.t.wav');print('mix_fx ok')

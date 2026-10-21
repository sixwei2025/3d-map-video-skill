#!/usr/bin/env python3
"""WarFX 音效床：从 scene.json 的元素时间自动生成铺满音效（全部程序合成，无外部素材、无付费接口，固定种子可复现）。
  river→电流嗡声  route→路线嗡声(虚线粮道更轻)  dots.spawn→点阵哒哒  dots.kill→熄灭低哒  roller.roll→数字滚轮哒哒
  chip/place/roller 出现→UI 咔哒  slam→低鼓+次低频  impact→爆炸+低鼓  qmark→提示音  scene.drums→低鼓节拍
用法: python3 engine/warfx/sfx.py <scene.json> <out.wav> [--lufs -22]"""
import json,sys,subprocess,wave,numpy as np
SR=48000;sc=json.load(open(sys.argv[1]));OUT=sys.argv[2];TGT=float(sys.argv[sys.argv.index('--lufs')+1]) if '--lufs' in sys.argv else -22.0
D=sc['duration'];N=int(D*SR)+SR;buf=np.zeros((N,2),np.float32);rs=np.random.default_rng(20261021)
def add(x,t,g=1.0,pan=0.0):
    i=int(t*SR);
    if i>=N or i+len(x)<=0:return
    x=x[:N-i];l,r=np.sqrt((1-pan)/2),np.sqrt((1+pan)/2);buf[i:i+len(x),0]+=x*g*l*1.41;buf[i:i+len(x),1]+=x*g*r*1.41
tt=lambda d:np.arange(int(d*SR))/SR
def env(d,a=0.002,r=None):
    t=tt(d);e=np.minimum(1,t/a);return e*np.exp(-t/(r or d/4))
def lp(x,fc):
    a=np.exp(-2*np.pi*fc/SR);y=np.zeros_like(x);s=0.0
    for i in range(len(x)):s=(1-a)*x[i]+a*s;y[i]=s
    return y
def lpf(x,fc):  # 快速一阶低通（向量化近似：FFT 砍高频）
    X=np.fft.rfft(x);f=np.fft.rfftfreq(len(x),1/SR);X*=1/np.sqrt(1+(f/fc)**4);return np.fft.irfft(X,len(x)).astype(np.float32)
def bpf(x,lo,hi):
    X=np.fft.rfft(x);f=np.fft.rfftfreq(len(x),1/SR);X*=((f>lo)&(f<hi));return np.fft.irfft(X,len(x)).astype(np.float32)
def tick(f=2400,d=0.025):t=tt(d);return (np.sin(2*np.pi*f*t)*env(d,0.0005,0.006)+0.3*rs.standard_normal(len(t))*env(d,0.0003,0.002)).astype(np.float32)
def click():t=tt(0.06);return (bpf(rs.standard_normal(len(t)).astype(np.float32),1500,6000)*env(0.06,0.0005,0.008)+0.5*np.sin(2*np.pi*1100*t)*env(0.06,0.0005,0.012)).astype(np.float32)
def drum(f0=58,d=1.2):
    t=tt(d);f=f0*(1+1.6*np.exp(-t/0.04));ph=2*np.pi*np.cumsum(f)/SR;b=np.sin(ph)*np.exp(-t/0.35)
    n=lpf(rs.standard_normal(len(t)).astype(np.float32),900)*np.exp(-t/0.05)*0.6;return (b+n).astype(np.float32)
def boom(d=2.2):
    t=tt(d);n=lpf(rs.standard_normal(len(t)).astype(np.float32),1800)*np.exp(-t/0.35)*np.minimum(1,t/0.004)
    cr=bpf(rs.standard_normal(len(t)).astype(np.float32),2000,9000)*np.exp(-t/0.08)*0.5;sub=np.sin(2*np.pi*(38+30*np.exp(-t/0.1))*t)*np.exp(-t/0.6)
    return (n*1.4+cr+sub*1.2).astype(np.float32)
def hum(d,f0=55,bright=1.0,rise=0.3):
    t=tt(d);f=f0*(1+rise*t/d);ph=2*np.pi*np.cumsum(f)/SR;s=sum(np.sin(k*ph)/k for k in range(1,8))*0.5
    s=s*(0.75+0.25*np.sin(2*np.pi*7*t))+bright*0.25*bpf(rs.standard_normal(len(t)).astype(np.float32),2500,7000)*(0.5+0.5*np.sin(2*np.pi*13*t))
    e=np.minimum(1,t/0.25)*np.minimum(1,(d-t)/0.5);return (s*e).astype(np.float32)
def whoosh(d):
    t=tt(d);n=rs.standard_normal(len(t)).astype(np.float32);x=np.zeros_like(n);seg=int(0.05*SR)
    for i in range(0,len(n),seg):fc=300+2500*(i/len(n));x[i:i+seg]=bpf(n[i:i+seg],fc*0.5,fc*1.5)
    return (x*np.sin(np.pi*t/d)**1.5).astype(np.float32)
def ping():t=tt(1.2);return (np.sin(2*np.pi*880*t)*0.6+np.sin(2*np.pi*1320*t)*0.3).astype(np.float32)*np.exp(-t/0.35)*np.minimum(1,t/0.003)
E=sc['elements']
for e in E:
    k=e['type']
    if k=='river':d=e['draw'][1]-e['draw'][0]+1.2;add(hum(d,55,1.0,0.15),e['draw'][0],0.30)
    elif k=='route':
        d=e['draw'][1]-e['draw'][0]+0.4;g=0.16 if e.get('dash') else 0.32;add(hum(d,82 if e['color']!='#C8102E' else 98,0.6,0.5),e['draw'][0],g,-0.3 if e['color']=='#C8102E' else 0.3);add(whoosh(d),e['draw'][0],g*0.8)
    elif k=='dots':
        a,b=e['spawn'];n=e['n'];step=max(0.045,(b-a)/n)
        for j,tt0 in enumerate(np.arange(a,b,step)):add(tick(2200+400*(j%3)),tt0,0.35,rs.uniform(-0.5,0.5))
        if e.get('kill'):
            k0,k1=e['kill']['t0'],e['kill']['t1']
            for tt0 in np.arange(k0,k1,0.06):add(tick(900,0.04),tt0,0.35,rs.uniform(-0.6,0.6))
        add(click(),e['t0'],0.5)
    elif k=='roller':
        for (a,b) in [e['roll']]+([e['roll2']] if e.get('roll2') else []):
            for j,tt0 in enumerate(np.arange(a,b,0.055)):add(tick(1800+1200*j*0.055/(b-a)),tt0,0.45)
        add(click(),e['t0'],0.6)
    elif k in('chip','place'):add(click(),e['t0'],0.35)
    elif k=='slam':add(drum(52,1.6),e['t0'],1.0);add(boom(1.5),e['t0'],0.35)
    elif k=='impact':add(boom(),e['t'],0.9 if e.get('scale',1)>=1.2 else 0.55);add(drum(48,1.4),e['t'],0.7)
    elif k=='qmark':add(ping(),e['t0'],0.35)
for t in sc.get('drums',[]):add(drum(),t,0.65)
def wr(f,x):
    with wave.open(f,'wb') as w:w.setnchannels(2);w.setsampwidth(2);w.setframerate(SR);w.writeframes((np.clip(x,-1,1)*32767).astype('<i2').tobytes())
buf=buf[:int(D*SR)];buf/=max(1e-6,np.abs(buf).max())/0.9;wr(OUT+'.tmp.wav',buf)
subprocess.run(['ffmpeg','-v','error','-y','-i',OUT+'.tmp.wav','-af',f'loudnorm=I={TGT}:TP=-3:LRA=15','-ar','48000',OUT],check=True);import os;os.remove(OUT+'.tmp.wav');print('sfx ok',OUT)

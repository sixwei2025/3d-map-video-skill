#!/usr/bin/env python3
"""官渡全片配音：Voicebox 本地（样片同一套：Dylan 旁白 / Uncle_Fu 苍老声配 3 句古文 + 轻混响）。0、1、3 句复用样片原始音频。
总长超 170s 时对第 5 句起统一加速。输出 voice.wav + timeline.json"""
import json,os,subprocess,urllib.request,time,wave
H=os.path.dirname(os.path.abspath(__file__)); URL='http://127.0.0.1:17493'
L=json.load(open(f'{H}/lines.json')); os.makedirs(f'{H}/vb_raw',exist_ok=True); os.makedirs(f'{H}/vt',exist_ok=True)
ff=lambda *x: subprocess.run(['ffmpeg','-v','error','-y',*x],check=True)
def gen(body,out):
    h={'Content-Type':'application/json','X-Voicebox-Client-Id':'3dmap-war-guandu-full'}
    try: d=urllib.request.urlopen(urllib.request.Request(URL+'/generate/stream',json.dumps(body,ensure_ascii=False).encode(),h),timeout=600).read()
    except urllib.error.HTTPError:
        gid=json.load(urllib.request.urlopen(urllib.request.Request(URL+'/generate',json.dumps(body,ensure_ascii=False).encode(),h),timeout=60))['id']
        for _ in range(300):
            time.sleep(2); s=json.load(urllib.request.urlopen(URL+f'/history/{gid}'))
            if s['status']=='completed': d=urllib.request.urlopen(URL+f'/audio/{gid}').read(); break
            if s['status'] in('failed','error','cancelled'): raise RuntimeError(s)
    open(out,'wb').write(d)
def dur(f):
    with wave.open(f) as w: return w.getnframes()/w.getframerate()
for i,l in enumerate(L):
    raw=f'{H}/vb_raw/{i:02d}.wav'
    if not os.path.exists(raw) or os.path.getsize(raw)<2000:
        gen(dict(profile_id=l['profile'],text=l['tts'],language='zh',engine='qwen_custom_voice',model_size='1.7B',seed=20261021,normalize=True,instruct=l['instruct']),raw); print('gen',i,flush=True)
TRIM="silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
def proc(i,l,k):
    o=f'{H}/vt/{i:02d}.wav'; at=l['atempo']*(k if i>=2 else 1)
    af=f"{TRIM},atempo={at:.4f}"+(",asetrate=48000*0.96,aresample=48000,atempo=1.0417,aecho=0.8:0.55:45|85:0.22|0.14,lowpass=f=6500" if l['elder'] else '')
    ff('-i',f'{H}/vb_raw/{i:02d}.wav','-af',af,'-ac','1','-ar','48000','-c:a','pcm_s16le',o); return o
k=1.0
for it in range(3):
    ds=[dur(proc(i,l,k)) for i,l in enumerate(L)]; tot=0.25+sum(ds)+sum(l['gap'] for l in L)+4.3
    print('pass',it,'k',round(k,3),'D',round(tot,2),flush=True)
    if tot<=172: break
    rest=sum(ds[4:]); need=tot-170; k*=rest/max(1,rest-need)
t=0.25; lines=[]; parts=[]
for i,l in enumerate(L):
    o=f'{H}/vt/{i:02d}.wav'; d=dur(o); lines.append(dict(i=i,text=l['disp'],t0=round(t,3),t1=round(t+d,3),elder=l['elder'])); parts.append((o,t)); t+=d+l['gap']
D=round(t+4.3,2)
inp=[];flt=[]
for j,(o,s) in enumerate(parts): inp+=['-i',o]; flt.append(f'[{j}]adelay={int(s*1000)}|{int(s*1000)}[a{j}]')
ff(*inp,'-filter_complex',';'.join(flt)+';'+''.join(f'[a{j}]' for j in range(len(parts)))+f'amix=inputs={len(parts)}:normalize=0,apad=whole_dur={D},loudnorm=I=-16:TP=-1.5:LRA=11','-ar','48000','-ac','1',f'{H}/voice.wav')
json.dump(dict(duration=D,k=k,lines=lines),open(f'{H}/timeline.json','w'),ensure_ascii=False,indent=1); print('D',D)

#!/usr/bin/env python3
"""抽帧拼图：python3 engine/warfx/contact.py <video> <out.jpg> t1 t2 ...（3 列，每格 360×640，左上角标时间）"""
import sys,subprocess,io
from PIL import Image,ImageDraw,ImageFont
V,OUT,*T=sys.argv[1:];F=ImageFont.truetype(__file__.rsplit('/',2)[0]+'/data/fonts/NotoSansSC-Bold-gb2312.otf',28)
ims=[]
for t in T:
    b=subprocess.run(['ffmpeg','-v','error','-ss',t,'-i',V,'-frames:v','1','-f','image2pipe','-vcodec','png','-'],capture_output=True,check=True).stdout
    im=Image.open(io.BytesIO(b)).convert('RGB').resize((360,640));d=ImageDraw.Draw(im);d.rectangle([6,6,120,44],fill=(0,0,0));d.text((14,8),f'{t}s',font=F,fill=(255,255,255));ims.append(im)
c=3;r=(len(ims)+c-1)//c;S=Image.new('RGB',(360*c+4*(c-1),640*r+4*(r-1)),(20,20,20))
for i,im in enumerate(ims):S.paste(im,((i%c)*364,(i//c)*644))
S.save(OUT,quality=92);print(OUT)

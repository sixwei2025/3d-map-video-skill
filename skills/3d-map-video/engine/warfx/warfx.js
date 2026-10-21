// WarFX v1（2026-10-21，官渡样片起）：战争片「暗底发光」可复用图层。全部是 t 的纯函数（无状态、固定随机种子）→ 可任意帧并行渲染、逐帧可复现。
// 用法：const fx=WarFX.create(ctx,{W,H,project}); fx.draw(spec.elements,t)。元素参数见 engine/warfx/README.md
(function(){
const E=(t,a,b)=>Math.min(1,Math.max(0,(t-a)/(b-a))), easeOut=x=>1-Math.pow(1-x,3), easeIO=x=>x<.5?4*x*x*x:1-Math.pow(-2*x+2,3)/2;
const back=x=>{const c1=2.2,c3=c1+1;return 1+c3*Math.pow(x-1,3)+c1*Math.pow(x-1,2)};
function rng(seed){let s=(seed>>>0)||1;return()=>{s^=s<<13;s>>>=0;s^=s>>17;s^=s<<5;s>>>=0;return s/4294967296;};}
const FONT='"Noto Sans SC Variable","Noto Sans CJK SC",sans-serif';
function hexA(h,a){h=h.replace('#','');const n=parseInt(h,16);return `rgba(${n>>16&255},${n>>8&255},${n&255},${a})`;}
// 经纬度折线 → 加密 → 屏幕点 + 累计长度
function screenPath(P,coords,dens=24){const out=[];for(let i=0;i<coords.length-1;i++){const a=coords[i],b=coords[i+1];for(let k=0;k<dens;k++){const u=k/dens;out.push([a[0]+(b[0]-a[0])*u,a[1]+(b[1]-a[1])*u]);}}out.push(coords[coords.length-1]);
  const o=[],s=out.map(c=>{const p=P(c);o.push(p.occ?1:0);return [p.x,p.y];});const cum=[0];for(let i=1;i<s.length;i++)cum.push(cum[i-1]+Math.hypot(s[i][0]-s[i-1][0],s[i][1]-s[i-1][1]));return {s,o,cum,L:cum[cum.length-1]};}
function at(sp,p){const d=Math.max(0,Math.min(1,p))*sp.L;let i=1;while(i<sp.cum.length-1&&sp.cum[i]<d)i++;const a=sp.s[i-1],b=sp.s[i],seg=(sp.cum[i]-sp.cum[i-1])||1,u=(d-sp.cum[i-1])/seg;return {x:a[0]+(b[0]-a[0])*u,y:a[1]+(b[1]-a[1])*u,ang:Math.atan2(b[1]-a[1],b[0]-a[0])};}
function strokeTo(ctx,sp,p){const d=p*sp.L,O=sp.o||[];ctx.beginPath();ctx.moveTo(sp.s[0][0],sp.s[0][1]);for(let i=1;i<sp.s.length;i++){const hid=O[i]||O[i-1];if(sp.cum[i]>d){if(!hid){const q=at(sp,p);ctx.lineTo(q.x,q.y);}break;}hid?ctx.moveTo(sp.s[i][0],sp.s[i][1]):ctx.lineTo(sp.s[i][0],sp.s[i][1]);}ctx.stroke();}
function vis(t,e){const a=E(t,e.t0,e.t0+(e.fin||0.4)),b=e.t1!=null?1-E(t,e.t1-(e.fout||0.5),e.t1):1;return a*b;}

const R={};
// 1) 电流发光河：宽辉光 + 白芯 + 流动电流段 + 细闪电抖动
R.river=(c,e,t,P)=>{const v=vis(t,e);if(v<=0)return;const sp=screenPath(P,e.coords);const p=easeIO(E(t,e.draw[0],e.draw[1]));if(p<=0)return;const col=e.color||'#7FE8FF',k=e.width||1;
  c.save();c.globalCompositeOperation='lighter';c.lineCap='round';c.lineJoin='round';c.globalAlpha=v;
  for(const [w,a,bl] of [[34,0.10,40],[18,0.22,22],[9,0.45,10]]){c.lineWidth=w*k;c.strokeStyle=hexA(col,a);c.shadowColor=col;c.shadowBlur=bl;strokeTo(c,sp,p);}
  c.shadowBlur=6;c.lineWidth=3.2*k;c.strokeStyle='rgba(255,255,255,0.95)';strokeTo(c,sp,p);
  // 流动电流：沿河的亮段（虚线 + 偏移随 t）
  c.setLineDash([60*k,140*k]);c.lineDashOffset=-t*(e.flow||420);c.lineWidth=6*k;c.strokeStyle='rgba(235,255,255,0.9)';c.shadowColor='#fff';c.shadowBlur=18;strokeTo(c,sp,p);c.setLineDash([]);
  // 闪电抖动：两条细线，确定性正弦扰动
  for(const j of [0,1]){c.beginPath();c.lineWidth=1.4*k;c.strokeStyle=hexA(col,0.75);c.shadowBlur=8;const d=p*sp.L;for(let i=0;i<sp.s.length&&sp.cum[i]<=d;i+=2){const nx=Math.sin(i*0.9+t*23+j*3)*Math.sin(i*0.37+t*7)*7*k,ny=Math.cos(i*0.7+t*19+j*5)*Math.sin(i*0.21+t*5)*7*k;i?c.lineTo(sp.s[i][0]+nx,sp.s[i][1]+ny):c.moveTo(sp.s[i][0]+nx,sp.s[i][1]+ny);}c.stroke();}
  if(p<1){const q=at(sp,p);const g=c.createRadialGradient(q.x,q.y,0,q.x,q.y,40*k);g.addColorStop(0,'rgba(255,255,255,1)');g.addColorStop(0.3,hexA(col,0.6));g.addColorStop(1,hexA(col,0));c.fillStyle=g;c.fillRect(q.x-40*k,q.y-40*k,80*k,80*k);}
  c.restore();};
// 2) 行军路线：贪吃蛇生长 + 箭头 + 粒子拖尾（蓝军蓝粒子团、曹军红线黄粒子）
R.route=(c,e,t,P)=>{const v=vis(t,e);if(v<=0)return;const sp=screenPath(P,e.coords);const p=easeOut(E(t,e.draw[0],e.draw[1]));if(p<=0)return;
  const col=e.color,pc=e.particle||col,w=e.width||8;c.save();c.globalAlpha=v;c.lineCap='round';c.lineJoin='round';
  if(e.dash)c.setLineDash([w*2.2,w*1.6]);
  c.globalCompositeOperation='lighter';c.lineWidth=w*3;c.strokeStyle=hexA(col,0.28);c.shadowColor=col;c.shadowBlur=26;strokeTo(c,sp,p);
  c.globalCompositeOperation='source-over';c.shadowBlur=10;c.lineWidth=w;c.strokeStyle=col;strokeTo(c,sp,p);
  c.globalCompositeOperation='lighter';c.shadowBlur=0;c.lineWidth=Math.max(1.5,w*0.3);c.strokeStyle='rgba(255,255,255,0.7)';strokeTo(c,sp,p);c.setLineDash([]);
  // 粒子：第 i 个粒子在 ts_i 由蛇头/沿线发射，随种子向两侧散开、衰减
  const r=rng(e.seed||7),N=e.n||260,life=e.life||1.1,T0=e.draw[0],T1=Math.max(e.draw[1],t);c.shadowColor=pc;c.shadowBlur=8;
  for(let i=0;i<N;i++){const ts=T0+(e.draw[1]-T0+(e.linger||1.5))*r(),ang=r()*6.283,sp0=(10+40*r())*(e.spread||1),sz=1.5+3*r(),dl=r();
    const age=t-ts;if(age<0||age>life)continue;const pp=Math.min(p,easeOut(E(ts,e.draw[0],e.draw[1])))-(ts>e.draw[1]?dl*0.5:dl*0.05);if(pp<0)continue;const q=at(sp,pp);const a=1-age/life;
    c.fillStyle=hexA(pc,0.9*a);c.beginPath();c.arc(q.x+Math.cos(ang)*sp0*age-Math.cos(q.ang)*age*30,q.y+Math.sin(ang)*sp0*age-Math.sin(q.ang)*age*30,sz*(0.6+0.4*a),0,6.283);c.fill();}
  if(e.head!==false&&p>0.02){const q=at(sp,p),s=w*2.6;c.globalCompositeOperation='source-over';c.translate(q.x,q.y);c.rotate(q.ang);c.shadowColor=col;c.shadowBlur=20;c.fillStyle=col;c.strokeStyle='#fff';c.lineWidth=3;
    c.beginPath();c.moveTo(s*1.3,0);c.lineTo(-s*0.6,-s*0.85);c.lineTo(-s*0.25,0);c.lineTo(-s*0.6,s*0.85);c.closePath();c.fill();c.stroke();}
  c.restore();};
// 3) 兵力点阵：spawn 逐点亮起；kill 按种子顺序熄灭到 remain；survivor 沿 retreat 路线移动（带拖尾）
R.dots=(c,e,t,P)=>{let o=P(e.at);const v=vis(t,e)*(o.occ&&!e.move?0.25:1);if(v<=0)return;if(e.move&&t>e.move.draw[0]){const q=at(screenPath(P,e.move.coords),easeIO(E(t,e.move.draw[0],e.move.draw[1])));o={x:q.x,y:q.y};}const n=e.n,cols=e.cols||10,gap=e.gap||16,rad=e.r||5,col=e.color;
  const r=rng(e.seed||11),order=[...Array(n).keys()];for(let i=n-1;i>0;i--){const j=Math.floor(r()*(i+1));[order[i],order[j]]=[order[j],order[i]];}
  const rank=[];order.forEach((d,i)=>rank[d]=i);const rows=Math.ceil(n/cols),ox=o.x-(cols-1)*gap/2,oy=o.y-(rows-1)*gap/2;
  c.save();c.globalAlpha=v;c.globalCompositeOperation='lighter';
  for(let d=0;d<n;d++){const sp=e.spawn,ts=sp[0]+(sp[1]-sp[0])*(d/n);let a=easeOut(E(t,ts,ts+0.18));if(a<=0)continue;let x=ox+(d%cols)*gap,y=oy+Math.floor(d/cols)*gap,s=1;
    if(e.partial&&d===n-1)s=e.partial;
    if(e.kill){const k=e.kill,keep=rank[d]<(k.remain||0);if(!keep){const td=k.t0+(k.t1-k.t0)*((rank[d]-(k.remain||0))/(n-(k.remain||0)));const f=E(t,td,td+0.25);if(f>=1)continue;if(f>0){c.fillStyle=hexA('#FFB040',0.8*(1-f));c.beginPath();c.arc(x,y,rad*(1+2.5*f),0,6.283);c.fill();}a*=1-f;}
      else if(e.retreat&&t>e.retreat.draw[0]){const rs=screenPath(P,e.retreat.coords),q=at(rs,easeIO(E(t,e.retreat.draw[0],e.retreat.draw[1])));const m=E(t,e.retreat.draw[0],e.retreat.draw[0]+0.4);x+= (q.x-x)*m;y+=(q.y-y)*m;
        for(let k2=1;k2<14;k2++){const q2=at(rs,easeIO(E(t-k2*0.05,e.retreat.draw[0],e.retreat.draw[1])));c.fillStyle=hexA(col,0.5*(1-k2/14)*m);c.beginPath();c.arc(x+(q2.x-q.x),y+(q2.y-q.y),rad*(1-k2/16),0,6.283);c.fill();}s=e.retreat.scale||1;}}
    const pulse=1+0.12*Math.sin(t*6+d);c.shadowColor=col;c.shadowBlur=12;c.fillStyle=hexA(col,a);c.beginPath();c.arc(x,y,rad*s*pulse*(0.4+0.6*a),0,6.283);c.fill();c.fillStyle=`rgba(255,255,255,${0.75*a})`;c.beginPath();c.arc(x,y,rad*0.45*s,0,6.283);c.fill();
    if(e.retreat&&e.retreat.label&&e.kill&&rank[d]<(e.kill.remain||0)&&t>e.retreat.draw[0]){const la=E(t,e.retreat.draw[0],e.retreat.draw[0]+0.3);c.save();c.globalCompositeOperation='source-over';c.globalAlpha=v*la;c.font=`900 46px ${FONT}`;c.textBaseline='middle';c.lineJoin='round';c.lineWidth=9;c.strokeStyle='#000';c.shadowBlur=0;c.strokeText(e.retreat.label,x+24,y);c.fillStyle='#9FD0FF';c.fillText(e.retreat.label,x+24,y);c.restore();}}
  c.restore();};
// 4) 数字滚轮卡（里程表式进位）；HUD 坐标是像素
function roll(c,v,x,y,h,digits,color){const str=String(Math.round(Math.abs(v))).padStart(digits,'0');let cx=x;c.save();c.font=`900 ${h}px ${FONT}`;const cw=c.measureText('0').width,comma=c.measureText(',').width;
  {let hid=0;for(let k=digits-1;k>0;k--){const pk=Math.pow(10,k);if(Math.floor(v/pk)===0&&!((v%pk)/(pk/10)>9)){hid+=cw;if(k%3===0)hid+=comma;}else break;}cx=x-hid;}
  for(let k=digits-1;k>=0;k--){const pk=Math.pow(10,k);let pos=Math.floor(v/pk)%10;if(k===0)pos=v%10;else{const low=(v%pk)/(pk/10);if(low>9)pos+=low-9;}
    const lead=k>0&&Math.floor(v/pk)===0&&!((v%pk)/(pk/10)>9);if(!lead){const b=Math.floor(pos)%10,f=pos-Math.floor(pos);c.save();c.beginPath();c.rect(cx,y-h*0.95,cw,h*1.15);c.clip();c.fillStyle=color;c.fillText(String(b),cx,y-f*h*1.1);c.fillText(String((b+1)%10),cx,y+(1-f)*h*1.1);c.restore();}
    cx+=cw;if(k%3===0&&k>0){if(!lead){c.fillStyle=color;c.fillText(',',cx,y);}cx+=comma;}}
  c.restore();return cx-x;}
R.roller=(c,e,t)=>{const v=vis(t,e);if(v<=0)return;const p=easeOut(E(t,e.roll[0],e.roll[1]));let val=e.from+(e.to-e.from)*p;if(e.roll2){const p2=easeIO(E(t,e.roll2[0],e.roll2[1]));val=val+(e.roll2v-val)*p2;}
  const h=e.size||96,x=e.x,y=e.y;c.save();c.globalAlpha=v;const sc=back(E(t,e.t0,e.t0+0.45));c.translate(x,y);c.scale(sc,sc);c.translate(-x,-y);
  c.font=`900 ${h}px ${FONT}`;const digits=String(Math.max(e.from,e.to,e.roll2v||0)).length;const w=c.measureText('0').width*digits+c.measureText(',').width*Math.floor((digits-1)/3)+(e.prefix?c.measureText(e.prefix).width:0);
  const bx=e.align==='right'?x-w-30:x-30;c.fillStyle='rgba(6,8,12,0.72)';c.strokeStyle=hexA(e.color,0.9);c.lineWidth=3;c.shadowColor=e.color;c.shadowBlur=24;c.beginPath();c.roundRect(bx,y-h*1.0-(e.title?62:0),w+60,h*1.35+(e.title?62:0)+(e.sub?56:0),12);c.fill();c.stroke();c.shadowBlur=0;
  let tx=bx+30;if(e.title){c.font=`800 40px ${FONT}`;c.fillStyle='#fff';c.fillText(e.title,tx,y-h*1.0-14);}
  c.shadowColor=e.color;c.shadowBlur=22;if(e.prefix){c.font=`900 ${h}px ${FONT}`;c.fillStyle=e.color;c.fillText(e.prefix,tx,y);tx+=c.measureText(e.prefix).width;}roll(c,val,tx,y,h,digits,'#fff');
  c.shadowBlur=0;if(e.sub&&t>=(e.subT||e.t0)){c.globalAlpha=v*E(t,e.subT||e.t0,(e.subT||e.t0)+0.3);c.font=`700 38px ${FONT}`;c.fillStyle=e.subColor||'#FFD84A';c.fillText(e.sub,bx+30,y+h*0.35+40);}
  c.restore();};
// 5) 交战：闪白 + 火光粒子 + 冲击波环（固定种子）
R.impact=(c,e,t,P)=>{const age=t-e.t;if(age<0||age>(e.dur||1.6))return;const o=P(e.at),r=rng(e.seed||3),S=e.scale||1;c.save();c.globalCompositeOperation='lighter';
  const fl=Math.max(0,1-age/0.25);if(fl>0){const g=c.createRadialGradient(o.x,o.y,0,o.x,o.y,260*S);g.addColorStop(0,`rgba(255,250,220,${fl})`);g.addColorStop(0.4,`rgba(255,150,40,${0.6*fl})`);g.addColorStop(1,'rgba(255,80,0,0)');c.fillStyle=g;c.fillRect(o.x-260*S,o.y-260*S,520*S,520*S);}
  for(const [d,w] of [[0,10],[0.12,5]]){const a=age-d;if(a<0)continue;const rr=easeOut(Math.min(1,a/0.9))*300*S,al=Math.max(0,1-a/0.9);c.strokeStyle=`rgba(255,220,160,${al})`;c.shadowColor='#FF9A2E';c.shadowBlur=30;c.lineWidth=w*al+1;c.beginPath();c.ellipse(o.x,o.y,rr,rr*0.62,0,0,6.283);c.stroke();}
  c.shadowBlur=10;for(let i=0;i<(e.n||140);i++){const ang=r()*6.283,spd=(80+380*r())*S,life=0.5+0.9*r(),sz=2+5*r(),hot=r();if(age>life)continue;const a=1-age/life,d=spd*easeOut(Math.min(1,age/life));
    c.fillStyle=hot>0.5?`rgba(255,${200+55*a|0},120,${a})`:`rgba(255,${90+80*a|0},20,${a})`;c.shadowColor='#FF7A1A';c.beginPath();c.arc(o.x+Math.cos(ang)*d,o.y+Math.sin(ang)*d*0.62-age*40*hot,sz*a+0.5,0,6.283);c.fill();}
  c.restore();};
// 6) 大字砸下（10 : 1 之类），配合 shake
R.slam=(c,e,t,P,W,H)=>{const v=vis(t,e);if(v<=0)return;const a=E(t,e.t0,e.t0+0.22),s=a<1?3.2-2.2*easeOut(a):1+0.04*Math.max(0,1-(t-e.t0-0.22)/0.3);c.save();c.globalAlpha=v*Math.min(1,a*1.5);c.translate(e.x||W/2,e.y);c.scale(s,s);
  c.font=`900 ${e.size||230}px ${FONT}`;c.textAlign='center';c.textBaseline='middle';c.lineJoin='round';c.lineWidth=18;c.strokeStyle='rgba(0,0,0,0.85)';c.strokeText(e.text,0,0);c.shadowColor=e.glow||'#FFD84A';c.shadowBlur=22;c.fillStyle=e.color||'#fff';c.fillText(e.text,0,0);c.restore();};
// 7) 地名：发光点 + 文字（古今双名可用 sub）
R.place=(c,e,t,P)=>{e.size=e.size||46;const o=P(e.at);const v=vis(t,e)*(o.occ?0:1);if(v<=0)return;const col=e.color||'#fff';c.save();c.globalAlpha=v;c.shadowColor=col;c.shadowBlur=14;c.fillStyle=col;c.beginPath();c.arc(o.x,o.y,e.dot||7,0,6.283);c.fill();
  c.font=`800 ${e.size||40}px ${FONT}`;const LP=e.__lp||{dx:e.dx??16,dy:e.dy??0};c.textAlign=LP.center?'center':LP.dx<0?'right':'left';c.textBaseline='middle';const x=LP.center?o.x:o.x+LP.dx,y=o.y+LP.dy;if(LP.leader){c.save();c.strokeStyle=hexA(col.startsWith('#')?col:'#ffffff',0.8);c.lineWidth=2;c.shadowBlur=6;c.beginPath();c.moveTo(o.x,o.y);c.lineTo(x,LP.center?(LP.dy<0?y+e.size*0.5:y-e.size*0.6):y);c.stroke();c.restore();}c.lineJoin='round';c.lineWidth=8;c.strokeStyle='rgba(0,0,0,0.85)';c.shadowBlur=0;c.strokeText(e.text,x,y);c.fillStyle=e.tc||'#fff';c.shadowColor=col;c.shadowBlur=10;c.fillText(e.text,x,y);
  if(e.sub){c.font=`600 ${Math.round((e.size||40)*0.62)}px ${FONT}`;c.lineWidth=6;c.shadowBlur=0;c.strokeText(e.sub,x,y+(e.size||40)*0.85);c.fillStyle='rgba(235,240,245,0.9)';c.fillText(e.sub,x,y+(e.size||40)*0.85);}c.restore();};
// 8) 问号点（脉冲）
R.qmark=(c,e,t,P)=>{const o=P(e.at);const v=vis(t,e)*(o.occ?0:1);if(v<=0)return;const ph=(t-e.t0)%1.2/1.2;c.save();c.globalAlpha=v;c.globalCompositeOperation='lighter';c.strokeStyle=`rgba(255,216,74,${1-ph})`;c.lineWidth=4;c.beginPath();c.arc(o.x,o.y,20+70*ph,0,6.283);c.stroke();
  c.globalCompositeOperation='source-over';c.shadowColor='#FFD84A';c.shadowBlur=26;c.fillStyle='#FFD84A';c.beginPath();c.arc(o.x,o.y,30*back(E(t,e.t0,e.t0+0.5)),0,6.283);c.fill();c.font=`900 44px ${FONT}`;c.textAlign='center';c.textBaseline='middle';c.fillStyle='#111';c.shadowBlur=0;c.fillText('?',o.x,o.y+2);
  if(e.text){c.font=`800 40px ${FONT}`;c.lineWidth=8;c.strokeStyle='#000';c.strokeText(e.text,o.x,o.y-62);c.fillStyle='#FFD84A';c.fillText(e.text,o.x,o.y-62);}c.restore();};
// 9) HUD 小卡（年代、角标、图例）
R.chip=(c,e,t)=>{const v=vis(t,e);if(v<=0)return;c.save();c.globalAlpha=v;c.font=`${e.weight||700} ${e.size||34}px ${FONT}`;const w=c.measureText(e.text).width+40,h=(e.size||34)*1.6;const x=e.align==='right'?e.x-w:e.align==='center'?e.x-w/2:e.x;
  c.fillStyle=e.bg||'rgba(6,8,12,0.7)';c.strokeStyle=e.border||'rgba(255,255,255,0.5)';c.lineWidth=2;c.beginPath();c.roundRect(x,e.y,w,h,8);c.fill();c.stroke();c.fillStyle=e.color||'#fff';c.textBaseline='middle';c.fillText(e.text,x+20,e.y+h/2+1);c.restore();};
// 10) 字幕：底部居中，白字黑描边 + 半透明衬底；hl 里的词用黄色
R.subs=(c,e,t,P,W,H)=>{const s=(e.items||[]).find(x=>t>=x.t0&&t<x.t1);if(!s)return;const a=E(t,s.t0,s.t0+0.12)*(1-E(t,s.t1-0.1,s.t1));c.save();c.globalAlpha=a;const fs=e.size||62;c.font=`800 ${fs}px ${FONT}`;c.textAlign='left';c.textBaseline='middle';
  const w=c.measureText(s.text).width,x=W/2-w/2,y=e.y||1560;c.fillStyle='rgba(0,0,0,0.42)';c.beginPath();c.roundRect(x-28,y-fs*0.85,w+56,fs*1.7,12);c.fill();c.lineJoin='round';c.lineWidth=10;c.strokeStyle='rgba(0,0,0,0.9)';c.strokeText(s.text,x,y);
  let cx=x;const hl=e.hl||[];const segs=[];let rest=s.text;while(rest.length){let best=null;for(const h of hl){const i=rest.indexOf(h);if(i>=0&&(best==null||i<best[0]))best=[i,h];}if(!best){segs.push([rest,0]);break;}if(best[0])segs.push([rest.slice(0,best[0]),0]);segs.push([best[1],1]);rest=rest.slice(best[0]+best[1].length);}
  for(const [tx,h] of segs){c.fillStyle=h?'#FFD84A':'#fff';c.fillText(tx,cx,y);cx+=c.measureText(tx).width;}c.restore();};
// v2.1（1021c 官渡全片）：veil 压暗/夜色、seal 篇章大字+红印、quote 引号文件框、geo 2D 几何示意、endcard 收尾大字卡
R.veil=(c,e,t,P,W,H)=>{const v=vis(t,e);if(v<=0)return;c.save();c.globalAlpha=v*(e.alpha??0.6);c.fillStyle=e.color||'#000';c.fillRect(-60,-60,W+120,H+120);c.restore();};
function stamp(c,x,y,txt,s,a){c.save();c.globalAlpha*=a;c.translate(x,y);c.rotate(-0.08);c.scale(s,s);c.fillStyle='#C8102E';c.shadowColor='#C8102E';c.shadowBlur=24;const n=txt.length,w=n>1?150:120;c.fillRect(-w/2,-60,w,120);c.shadowBlur=0;c.strokeStyle='rgba(255,255,255,0.9)';c.lineWidth=4;c.strokeRect(-w/2+9,-51,w-18,102);c.font=`900 ${n>1?58:78}px ${FONT}`;c.fillStyle='#fff';c.textAlign='center';c.textBaseline='middle';c.fillText(txt,0,4);c.restore();}
R.seal=(c,e,t,P,W)=>{const v=vis(t,e);if(v<=0)return;const a=E(t,e.t0,e.t0+0.35),s=1.3-0.3*easeOut(a),y=e.y||700,sz=e.size||200;c.save();c.globalAlpha=v*a;c.font=`900 ${sz}px ${FONT}`;const tw=c.measureText(e.text).width;c.translate(W/2-40,y);c.scale(s,s);c.textAlign='center';c.textBaseline='middle';c.lineJoin='round';c.lineWidth=22;c.strokeStyle='rgba(0,0,0,0.85)';c.strokeText(e.text,0,0);c.shadowColor='#C8102E';c.shadowBlur=40;c.fillStyle='#fff';c.fillText(e.text,0,0);c.restore();
  if(e.sub){c.save();c.globalAlpha=v*a;c.font=`700 40px ${FONT}`;c.textAlign='center';c.fillStyle='#E8C77A';c.lineWidth=8;c.strokeStyle='#000';c.strokeText(e.sub,W/2-40,y-sz*0.75);c.fillText(e.sub,W/2-40,y-sz*0.75);c.restore();}
  const b=E(t,e.t0+0.4,e.t0+0.55);if(b>0){c.save();c.globalAlpha=v;stamp(c,W/2-40+tw/2+90,y+sz*0.25,e.num,1.8-0.8*easeOut(b),b);c.restore();}};
R.quote=(c,e,t,P,W)=>{const v=vis(t,e);if(v<=0)return;const a=easeOut(E(t,e.t0,e.t0+0.4));const ls=e.text.split('\n'),pl=(e.plain||'').split('\n').filter(Boolean);const hT=ls.length*86,hP=pl.length*56,h=110+hT+24+hP+50,w=960,x=(W-w)/2,y=(e.y||600)+(1-a)*50;
  c.save();c.globalAlpha=v*a;c.fillStyle='rgba(14,11,8,0.9)';c.strokeStyle='#E8C77A';c.lineWidth=3;c.shadowColor='#000';c.shadowBlur=40;c.beginPath();c.roundRect(x,y,w,h,16);c.fill();c.shadowBlur=0;c.stroke();c.fillStyle='#C8102E';c.fillRect(x,y+12,12,h-24);
  c.font=`900 150px ${FONT}`;c.fillStyle='rgba(200,16,46,0.35)';c.textBaseline='top';c.fillText('“',x+w-130,y-10);
  c.textBaseline='middle';c.font=`700 36px ${FONT}`;c.fillStyle='#E8C77A';c.textAlign='left';c.fillText(e.src,x+50,y+56);if(e.who){c.font=`800 40px ${FONT}`;c.fillStyle='#fff';c.fillText('—— '+e.who,x+50,y+h-34-(hP?0:0)+0);}
  c.font=`900 66px ${FONT}`;c.fillStyle='#fff';const rv=E(t,e.t0+0.3,e.t0+0.3+(e.type_s||1.2));ls.forEach((s,i)=>{const n=Math.ceil(s.length*Math.min(1,Math.max(0,rv*ls.length-i)));c.fillText(s.slice(0,n),x+50,y+110+43+i*86);});
  c.font=`600 40px ${FONT}`;c.fillStyle='rgba(225,230,236,0.92)';pl.forEach((s,i)=>c.fillText(s,x+50,y+110+hT+24+28+i*56));c.restore();};
R.geo=(c,e,t,P,W,H)=>{const v=vis(t,e);if(v<=0)return;c.save();c.globalAlpha=v;c.fillStyle='#04070c';c.fillRect(-60,-60,W+120,H+120);c.strokeStyle='rgba(120,170,220,0.09)';c.lineWidth=1;for(let x=0;x<=W;x+=60){c.beginPath();c.moveTo(x,0);c.lineTo(x,H);c.stroke();}for(let y=0;y<=H;y+=60){c.beginPath();c.moveTo(0,y);c.lineTo(W,y);c.stroke();}
  const A=[190,330],C=[720,1130],R0=200,dx=C[0]-A[0],dy=C[1]-A[1],dl=Math.hypot(dx,dy),ux=dx/dl,uy=dy/dl,B=[C[0]-ux*R0,C[1]-uy*R0],u=0.5,N=[A[0]+(B[0]-A[0])*u,A[1]+(B[1]-A[1])*u];
  const pl=easeOut(E(t,e.tl,e.tl+1.0)),br=E(t,e.tb,e.tb+0.9),lab=(e.labels||[]).filter(l=>t>=l.t).pop();
  c.lineCap='round';const lc=`rgb(${46+80*br|0},${139-40*br|0},${255-160*br|0})`;c.strokeStyle=lc;c.shadowColor=lc;c.shadowBlur=24*(1-br);c.lineWidth=10;c.beginPath();c.moveTo(A[0],A[1]);c.lineTo(A[0]+(B[0]-A[0])*pl,A[1]+(B[1]-A[1])*pl);c.stroke();c.shadowBlur=0;
  c.font=`800 44px ${FONT}`;c.textAlign='left';c.textBaseline='middle';c.fillStyle='#8FD0FF';if(pl>0){c.globalAlpha=v*Math.min(1,pl*2);c.fillText(lab&&lab.line?lab.line:'河北',A[0]-40,A[1]-60);c.fillText('补给线',A[0]+(N[0]-A[0])*0.5+40,A[1]+(N[1]-A[1])*0.5-30);c.globalAlpha=v;}
  const r=rng(5),ca=E(t,e.tl+0.6,e.tl+1.4);if(ca>0)for(let i=0;i<90;i++){const an=r()*6.283,rr=R0*Math.sqrt(r()),fl=r(),x=C[0]+Math.cos(an)*rr+Math.cos(an)*br*(200+300*fl),y=C[1]+Math.sin(an)*rr+Math.sin(an)*br*(200+300*fl)+br*br*200*fl;c.fillStyle=hexA(br>0?'#7B8796':'#4FA3FF',ca*(1-0.8*br));c.beginPath();c.arc(x,y,7,0,6.283);c.fill();}
  if(ca>0){c.strokeStyle=hexA('#4FA3FF',ca*0.6*(1-br));c.lineWidth=3;c.beginPath();c.arc(C[0],C[1],R0+16,0,6.283);c.stroke();c.font=`900 64px ${FONT}`;c.textAlign='center';c.lineWidth=10;c.strokeStyle='#000';const ct=lab&&lab.circle?lab.circle:'十万人';c.globalAlpha=v*ca*(1-0.5*br);c.strokeText(ct,C[0],C[1]);c.fillStyle='#fff';c.fillText(ct,C[0],C[1]);c.globalAlpha=v;}
  const na=E(t,e.tn,e.tn+0.3);if(na>0){if(br<1){const pu=1+0.15*Math.sin(t*8);c.shadowColor='#FFD84A';c.shadowBlur=40;c.fillStyle=hexA('#FFD84A',1-br);c.beginPath();c.arc(N[0],N[1],30*pu*back(na)*(1-br),0,6.283);c.fill();c.shadowBlur=0;}
    if(br>0){const r2=rng(9);for(let i=0;i<14;i++){const an=r2()*6.283,d=br*(120+160*r2());c.fillStyle=hexA('#FFD84A',1-br);c.fillRect(N[0]+Math.cos(an)*d-6,N[1]+Math.sin(an)*d-6,12,12);}}
    const nt=lab?lab.node:(e.node||'乌巢');c.font=`900 60px ${FONT}`;c.textAlign='left';c.lineWidth=10;c.strokeStyle='#000';c.strokeText(nt,N[0]+50,N[1]-10);c.fillStyle='#FFD84A';c.fillText(nt,N[0]+50,N[1]-10);}
  const pa=E(t,e.ta,e.ta+0.9);if(pa>0){const S=[130,1480],K=[60,900],q=easeOut(pa),bz=s=>[(1-s)*(1-s)*S[0]+2*(1-s)*s*K[0]+s*s*N[0],(1-s)*(1-s)*S[1]+2*(1-s)*s*K[1]+s*s*N[1]];c.strokeStyle='#C8102E';c.shadowColor='#FF3B4F';c.shadowBlur=26;c.lineWidth=14;c.beginPath();c.moveTo(S[0],S[1]);for(let s=0.02;s<=q;s+=0.02){const p=bz(s);c.lineTo(p[0],p[1]);}c.stroke();const p=bz(q),p0=bz(Math.max(0,q-0.03)),an=Math.atan2(p[1]-p0[1],p[0]-p0[0]);c.translate(p[0],p[1]);c.rotate(an);c.fillStyle='#C8102E';c.beginPath();c.moveTo(34,0);c.lineTo(-18,-24);c.lineTo(-18,24);c.closePath();c.fill();c.setTransform(c.getTransform());}
  c.restore();c.save();c.globalAlpha=v;c.font=`700 34px ${FONT}`;c.textAlign='right';c.fillStyle='rgba(220,228,236,0.75)';c.fillText('示意图',W-40,90);c.restore();};
R.endcard=(c,e,t,P,W,H)=>{const v=vis(t,e);if(v<=0)return;c.save();c.globalAlpha=v;c.fillStyle='#030305';c.fillRect(-60,-60,W+120,H+120);const a=E(t,e.t0+0.2,e.t0+0.9),y=e.y||860;c.globalAlpha=v*a;c.font=`900 ${e.size||70}px ${FONT}`;c.textAlign='center';c.textBaseline='middle';c.lineJoin='round';c.lineWidth=14;c.strokeStyle='#000';c.strokeText(e.text,W/2,y);c.shadowColor='#C8102E';c.shadowBlur=36;c.fillStyle='#fff';c.fillText(e.text,W/2,y);c.shadowBlur=0;
  const b=E(t,e.t0+1.0,e.t0+1.15);if(b>0)stamp(c,W/2,y+190,e.seal||'官渡',1.8-0.8*easeOut(b),b);c.globalAlpha=v*E(t,e.t0+1.3,e.t0+1.8);c.font=`600 38px ${FONT}`;c.fillStyle='rgba(225,230,236,0.85)';c.fillText(e.sub||'',W/2,y+340);c.restore();};
function shake(els,t){let x=0,y=0;for(const e of els){if(e.type!=='shake')continue;const a=t-e.t;if(a<0||a>e.dur)continue;const k=(e.amp||14)*Math.pow(1-a/e.dur,2);x+=k*Math.sin(a*83+1.3)*Math.cos(a*31);y+=k*Math.cos(a*71+0.4)*Math.sin(a*47+2);}return [x,y];}
// v2（1021b）标签避让：地图标签(place/qmark文字)避开 HUD 卡片(roller/chip/subs)、其它标签和 avoid.reserve 保留区。
// 纯函数：每帧按候选位顺序挑第一个不重叠的（默认位优先，只有挤了才换位）→ 无状态，可并行渲染。
function rollerBox(c,e){const h=e.size||96;c.save();c.font=`900 ${h}px ${FONT}`;const digits=String(Math.max(e.from,e.to,e.roll2v||0)).length;const w=c.measureText('0').width*digits+c.measureText(',').width*Math.floor((digits-1)/3)+(e.prefix?c.measureText(e.prefix).width:0);c.restore();
  const bx=e.align==='right'?e.x-w-30:e.x-30;return [bx,e.y-h-(e.title?62:0),w+60,h*1.35+(e.title?62:0)+(e.sub?56:0)];}
function chipBox(c,e){c.save();c.font=`${e.weight||700} ${e.size||34}px ${FONT}`;const w=c.measureText(e.text).width+40,h=(e.size||34)*1.6;c.restore();return [e.align==='right'?e.x-w:e.align==='center'?e.x-w/2:e.x,e.y,w,h];}
const ovl=(a,b)=>Math.max(0,Math.min(a[0]+a[2],b[0]+b[2])-Math.max(a[0],b[0]))*Math.max(0,Math.min(a[1]+a[3],b[1]+b[3])-Math.max(a[1],b[1]));
function layout(c,els,t,P,W,H,opt){opt=opt||{};if(opt.on===false)return;const pad=opt.pad??14,obs=(opt.reserve||[]).map(r=>r.slice());
  for(const e of els){if(vis(t,e)<=0)continue;let b=null;if(e.type==='roller')b=rollerBox(c,e);else if(e.type==='chip')b=chipBox(c,e);else if(e.type==='slam')b=[0,e.y-(e.size||230)*0.6,W,(e.size||230)*1.2];
    else if(e.type==='subs'&&(e.items||[]).some(x=>t>=x.t0&&t<x.t1)){const fs=e.size||62;b=[0,(e.y||1560)-fs,W,fs*2];}if(b)obs.push([b[0]-pad,b[1]-pad,b[2]+2*pad,b[3]+2*pad]);}
  const M=opt.margin??24;const labs=els.filter(e=>e.type==='place'&&vis(t,e)>0&&e.avoid!==false).sort((a,b)=>(b.prio||0)-(a.prio||0));
  for(const e of labs){const o=P(e.at);if(o.occ)continue;const sz=e.size||46;c.save();c.font=`800 ${sz}px ${FONT}`;let w=c.measureText(e.text).width;if(e.sub){c.font=`600 ${Math.round(sz*0.62)}px ${FONT}`;w=Math.max(w,c.measureText(e.sub).width);}c.restore();
    const h=e.sub?sz*1.75:sz*1.1,g=(e.dot??7)+12,d0={dx:e.dx??16,dy:e.dy??0};
    const cand=[d0,...(e.cand||[])];for(const m of (opt.rings||[1,2.2,3.6,5]))cand.push({dx:g*m,dy:0},{dx:-g*m,dy:0},{dx:g*m,dy:-h*0.8*m},{dx:-g*m,dy:-h*0.8*m},{dx:g*m,dy:h*0.7*m},{dx:-g*m,dy:h*0.7*m},{dx:-w/2,dy:-h*0.8-g*m},{dx:-w/2,dy:g*m+sz*0.4});
    const box=q=>{const x=q.dx<0&&q.dx!==-w/2?o.x+q.dx-w:o.x+q.dx,y=o.y+q.dy-sz*0.6;return [x,y,w,h];};
    let best=null,bs=1e18;for(const [i,q] of cand.entries()){const b=box(q);let s=0;for(const r of obs)s+=ovl(b,r)*50;s+=Math.max(0,M-b[0])*h+Math.max(0,b[0]+w-(W-M))*h+Math.max(0,M-b[1])*w+Math.max(0,b[1]+h-(H-M))*w;s+=i*1;if(s<bs){bs=s;best=q;}if(s<=i)break;}
    const far=Math.hypot(best.dx,best.dy)>g*1.8;e.__lp=Object.assign({},best,best.dx===-w/2?{center:1}:{},far&&opt.leader!==false?{leader:1}:{});const b=box(best);obs.push([b[0]-pad/2,b[1]-pad/2,b[2]+pad,b[3]+pad]);obs.push([o.x-12,o.y-12,24,24]);}}
window.WarFX={R,rng,E,easeOut,easeIO,shake,layout,rollerBox,chipBox,
  draw(c,els,t,P,W,H,layer){for(const e of els){if((e.layer||(e.type==='roller'||e.type==='chip'||e.type==='subs'||e.type==='slam'||e.type==='seal'||e.type==='quote'||e.type==='geo'||e.type==='endcard'?'hud':'map'))!==layer)continue;const f=R[e.type];if(f)f(c,e,t,P,W,H);}}};
})();

// 1021d 提速渲染器（render_mac.mjs 的快速版，输出完全相同的 frames/fNNNNN.jpg + frames.log.jsonl）
// 改动：① 浏览器不再每 30 帧重启（CHUNK 默认 100000，即每个 worker 一个浏览器）② 截图 optimizeForSpeed + 写盘异步（与下一帧渲染重叠）
//      ③ 页面 FAST=1：瓦片已就绪时跳过第二次重绘、轮询 8ms ④ 相机与全部元素都“静止”的连续帧可复用（REUSE=1，默认关）
// 用法同 render_mac.mjs：node engine/render_fast.mjs <workDir> <port> [a-b]   env: TILES CHUNK FORCE SCENE_PAGE Q(=93)
import puppeteer from 'puppeteer-core';import fs from 'node:fs';import path from 'node:path';
const [,,work,port,spec='']=process.argv;const meta=JSON.parse(fs.readFileSync(`${work}/meta.json`,'utf8'));const out=`${work}/frames`;fs.mkdirSync(out,{recursive:true});
const C=Number(process.env.CHUNK||100000),PAGE=process.env.SCENE_PAGE||'warfx.html',TILES=process.env.TILES||'',Q=Number(process.env.Q||93);
let want;if(!spec)want=[...Array(meta.frames).keys()];else if(spec.includes('-')){const [a,b]=spec.split('-').map(Number);want=[];for(let f=a;f<Math.min(b,meta.frames);f++)want.push(f);}else want=spec.split(',').filter(Boolean).map(Number);
const fp=f=>`${out}/f${String(f).padStart(5,'0')}.jpg`;const todo=process.env.FORCE?want:want.filter(f=>!fs.existsSync(fp(f)));const logf=`${work}/frames.log.jsonl`;
console.log('todo',todo.length,'of',want.length,'size',meta.w+'x'+meta.h,'page',PAGE,'fast');
const pend=new Set();const wr=(f,buf)=>{const p=fs.promises.writeFile(fp(f)+'.tmp.jpg',buf).then(()=>fs.promises.rename(fp(f)+'.tmp.jpg',fp(f)));pend.add(p);p.finally(()=>pend.delete(p));};
async function pass(list,settleMax,tag){const flagged=[];let done=0,tR=0,tS=0;const t0=Date.now();
  for(let i=0;i<list.length;i+=C){const prof=path.resolve(`tmp/prof-${process.pid}-${i}`);fs.mkdirSync(prof,{recursive:true});
    const browser=await puppeteer.launch({executablePath:process.env.CHROME||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,protocolTimeout:900000,timeout:180000,userDataDir:prof,
      args:['--use-angle=metal','--enable-gpu-rasterization','--ignore-gpu-blocklist','--enable-webgl','--enable-zero-copy','--no-first-run','--no-default-browser-check','--use-mock-keychain','--password-store=basic',
        '--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows',`--window-size=${meta.w},${meta.h}`,'--disk-cache-size=300000000','--js-flags=--max-old-space-size=2048']});
    try{const page=await browser.newPage();await page.setViewport({width:meta.w,height:meta.h,deviceScaleFactor:1});
      page.on('pageerror',e=>console.log('[pageerror]',e.message));page.on('console',m=>{const x=m.text();if(x.startsWith('maperr'))console.log(x);});
      await page.goto(`http://127.0.0.1:${port}/engine/${PAGE}?scene=/${work}/scene.json${TILES?'&tiles='+encodeURIComponent(TILES):''}`,{waitUntil:'load',timeout:180000});
      await page.waitForFunction('window.READY===true',{timeout:180000});await page.evaluate(v=>{window.FAST=1;if(v)window.SETTLE_MAX=v;},settleMax);
      const cdp=await page.createCDPSession();
      for(const f of list.slice(i,i+C)){const a=Date.now();await page.evaluate(t=>window.renderFrame(t),f/meta.fps);const st=await page.evaluate(()=>window.__last||null);const b=Date.now();
        if(process.env.GRAB){const u=await page.evaluate(q=>window.grabFrame(q),Q/100);wr(f,Buffer.from(u.slice(u.indexOf(',')+1),'base64'));}else{const r=await cdp.send('Page.captureScreenshot',{format:'jpeg',quality:Q,optimizeForSpeed:true,fromSurface:true});wr(f,Buffer.from(r.data,'base64'));}const c=Date.now();tR+=b-a;tS+=c-b;done++;
        fs.appendFileSync(logf,JSON.stringify({f,pass:tag,...(st||{})})+'\n');if(st&&st.pending>0)flagged.push(f);
        if(done%120===0){const el=(Date.now()-t0)/1000;console.log(`[${tag}] ${done}/${list.length} frames, ${el.toFixed(0)}s, ${(done/el*60).toFixed(1)} frames/min, render ${(tR/done).toFixed(0)}ms shot ${(tS/done).toFixed(0)}ms, lowres-flagged ${flagged.length}`);}}
      await Promise.all([...pend]);
    }finally{const pr=browser.process();await Promise.race([browser.close().catch(()=>{}),new Promise(r=>setTimeout(r,4000))]);try{pr&&pr.exitCode===null&&pr.kill('SIGKILL');}catch{}fs.rmSync(prof,{recursive:true,force:true});}}
  const el=(Date.now()-t0)/1000;console.log(`[${tag}] ${done}/${list.length} frames, ${el.toFixed(0)}s, ${(done/el*60).toFixed(1)} frames/min, render ${(tR/Math.max(1,done)).toFixed(0)}ms shot ${(tS/Math.max(1,done)).toFixed(0)}ms, lowres-flagged ${flagged.length}`);return flagged;}
const T0=Date.now();let flagged=await pass(todo,0,'main');
if(flagged.length){console.log('低分辨率瓦片帧，延长等待重渲:',flagged.join(','));flagged=await pass(flagged,25000,'rerender');}
const lr=`${work}/lowres.json`;const prev=fs.existsSync(lr)?JSON.parse(fs.readFileSync(lr,'utf8')):[];fs.writeFileSync(lr,JSON.stringify(prev.filter(f=>!want.includes(f)).concat(flagged)));
console.log('RENDER DONE frames',todo.length,'secs',((Date.now()-T0)/1000).toFixed(0),'still-lowres',flagged.length);process.exit(0);

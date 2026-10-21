// v2 确定性逐帧渲染器：安静期推进 + 低分辨率瓦片检测（发现就用更长等待重渲该帧）。
// 用法: node engine/render.mjs <workDir> <port> [frames]   frames = "a-b"(含a不含b) 或 "1,2,3"，缺省=全片
// env: TILES=<瓦片代理URL>  SCENE_PAGE=scene.html  CHUNK=30（每 N 帧重启浏览器）  FORCE=1（覆盖已有帧）
import puppeteer from 'puppeteer-core';
import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path';
const [,, work, port, spec=''] = process.argv;
const meta=JSON.parse(fs.readFileSync(`${work}/meta.json`,'utf8'));
const out=`${work}/frames`; fs.mkdirSync(out,{recursive:true});
const C=Number(process.env.CHUNK||30), PAGE=process.env.SCENE_PAGE||'scene.html', TILES=process.env.TILES||'';
function findChrome(){ return process.env.CHROME||'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'; }
const exe=findChrome();
let want; if(!spec) want=[...Array(meta.frames).keys()];
else if(spec.includes('-')){const [a,b]=spec.split('-').map(Number); want=[]; for(let f=a;f<Math.min(b,meta.frames);f++) want.push(f);}
else want=spec.split(',').filter(Boolean).map(Number);
const fp=f=>`${out}/f${String(f).padStart(5,'0')}.jpg`;
const todo=process.env.FORCE?want:want.filter(f=>!fs.existsSync(fp(f)));
const logf=`${work}/frames.log.jsonl`;
console.log('todo',todo.length,'of',want.length,'size',meta.w+'x'+meta.h,'page',PAGE);
async function pass(list, settleMax, tag){
  const flagged=[]; let done=0; const t0=Date.now();
  for(let i=0;i<list.length;i+=C){
    const prof=path.resolve(`tmp/prof-${process.pid}-${i}`); fs.mkdirSync(prof,{recursive:true});
    const browser=await puppeteer.launch({executablePath:exe,headless:process.env.HEADLESS==='0'?false:true,protocolTimeout:900000,timeout:180000,userDataDir:prof,
      args:['--mute-audio','--use-angle=metal','--enable-gpu-rasterization','--ignore-gpu-blocklist','--enable-webgl','--no-first-run','--no-default-browser-check','--use-mock-keychain','--password-store=basic',
        '--disable-background-timer-throttling','--disable-renderer-backgrounding','--disable-backgrounding-occluded-windows',`--window-size=${meta.w},${meta.h}`,'--disk-cache-size=300000000','--js-flags=--max-old-space-size=1024']});
    try{
      const page=await browser.newPage(); await page.setViewport({width:meta.w,height:meta.h,deviceScaleFactor:1});
      page.on('pageerror',e=>console.log('[pageerror]',e.message)); page.on('console',m=>{const x=m.text(); if(x.startsWith('maperr')) console.log(x);});
      await page.goto(`http://127.0.0.1:${port}/engine/${PAGE}?scene=/${work}/scene.json${TILES?'&tiles='+encodeURIComponent(TILES):''}`,{waitUntil:'load',timeout:180000});
      await page.waitForFunction('window.READY===true',{timeout:180000});
      if(!globalThis.__gpuLogged){ globalThis.__gpuLogged=1; const r=await page.evaluate(()=>{const c=document.createElement('canvas');const g=c.getContext('webgl2')||c.getContext('webgl');if(!g)return 'NO_WEBGL';const e=g.getExtension('WEBGL_debug_renderer_info');return e?g.getParameter(e.UNMASKED_VENDOR_WEBGL)+' | '+g.getParameter(e.UNMASKED_RENDERER_WEBGL):g.getParameter(g.RENDERER);}); console.log('GPU_RENDERER',r); }
      if(process.env.PREFETCH) settleMax=Number(process.env.SETTLE_MAX||1500);
      if(settleMax) await page.evaluate(v=>{window.SETTLE_MAX=v},settleMax);
      for(const f of list.slice(i,i+C)){
        await page.evaluate(t=>window.renderFrame(t), f/meta.fps);
        const st=await page.evaluate(()=>window.__last||null);
        if(process.env.PREFETCH){done++;continue;}  // 预取模式：只推相机让瓦片进缓存，不截图
        await page.screenshot({path:fp(f)+'.tmp.jpg',type:'jpeg',quality:93}); fs.renameSync(fp(f)+'.tmp.jpg',fp(f)); done++;
        fs.appendFileSync(logf, JSON.stringify({f,pass:tag,...(st||{})})+'\n');
        if(st && st.pending>0) flagged.push(f);
      }
    } finally { await browser.close().catch(()=>{}); fs.rmSync(prof,{recursive:true,force:true}); }
    const el=(Date.now()-t0)/1000; console.log(`[${tag}] ${done}/${list.length} frames, ${el.toFixed(0)}s, ${(done/el*60).toFixed(1)} frames/min, lowres-flagged ${flagged.length}`);
  }
  return flagged;
}
const T0=Date.now();
let flagged=await pass(todo, 0, 'main');
if(flagged.length){ console.log('低分辨率瓦片帧，延长等待重渲:',flagged.join(',')); flagged=await pass(flagged, 25000, 'rerender'); }
const lr=`${work}/lowres.json`; const prev=fs.existsSync(lr)?JSON.parse(fs.readFileSync(lr,'utf8')):[];
const keep=prev.filter(f=>!want.includes(f)).concat(flagged); fs.writeFileSync(lr, JSON.stringify(keep));
console.log('RENDER DONE frames',todo.length,'secs',((Date.now()-T0)/1000).toFixed(0),'still-lowres',flagged.length);

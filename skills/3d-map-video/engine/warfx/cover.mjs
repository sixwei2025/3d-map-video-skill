// WarFX 首帧封面：node engine/warfx/cover.mjs <workDir> <port> <tilesURL> <out.jpg>   读 scene.json 的 cover.t / cover.lines（warfx.html?cover=1：只画地图层 + 封面大字）
import puppeteer from 'puppeteer-core';import fs from 'node:fs';import path from 'node:path';
const [,,work,port,tiles,out]=process.argv;const sc=JSON.parse(fs.readFileSync(`${work}/scene.json`,'utf8'));
const pf=process.env.ProgramFiles||'C:\\Program Files', pf86=process.env['ProgramFiles(x86)']||'C:\\Program Files (x86)', lad=process.env.LOCALAPPDATA||'';
const exe=process.env.CHROME||['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','/usr/bin/google-chrome','/usr/bin/chromium',
  path.join(pf,'Google','Chrome','Application','chrome.exe'),path.join(pf86,'Google','Chrome','Application','chrome.exe'),
  lad?path.join(lad,'Google','Chrome','Application','chrome.exe'):'',path.join(pf,'Microsoft','Edge','Application','msedge.exe')].find(p=>p&&fs.existsSync(p));
const gpu=process.platform==='darwin'?['--use-angle=metal','--enable-gpu-rasterization']:[];
const b=await puppeteer.launch({executablePath:exe,headless:true,args:[...gpu,'--ignore-gpu-blocklist',`--window-size=${sc.w},${sc.h}`]});
const p=await b.newPage();await p.setViewport({width:sc.w,height:sc.h});
await p.goto(`http://127.0.0.1:${port}/engine/warfx.html?cover=1&scene=/${work}/scene.json&tiles=${encodeURIComponent(tiles)}`,{waitUntil:'load'});
await p.waitForFunction('window.READY===true',{timeout:120000});await p.evaluate(t=>window.renderFrame(t),sc.cover.t);
await p.screenshot({path:out,type:'jpeg',quality:95});await b.close();console.log('cover',out);

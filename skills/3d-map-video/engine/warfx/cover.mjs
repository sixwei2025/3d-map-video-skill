// WarFX 首帧封面：node engine/warfx/cover.mjs <workDir> <port> <tilesURL> <out.jpg>   读 scene.json 的 cover.t / cover.lines（warfx.html?cover=1：只画地图层 + 封面大字）
import puppeteer from 'puppeteer-core';import fs from 'node:fs';
const [,,work,port,tiles,out]=process.argv;const sc=JSON.parse(fs.readFileSync(`${work}/scene.json`,'utf8'));
const b=await puppeteer.launch({executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',headless:true,args:['--use-angle=metal','--enable-gpu-rasterization','--ignore-gpu-blocklist',`--window-size=${sc.w},${sc.h}`]});
const p=await b.newPage();await p.setViewport({width:sc.w,height:sc.h});
await p.goto(`http://127.0.0.1:${port}/engine/warfx.html?cover=1&scene=/${work}/scene.json&tiles=${encodeURIComponent(tiles)}`,{waitUntil:'load'});
await p.waitForFunction('window.READY===true',{timeout:120000});await p.evaluate(t=>window.renderFrame(t),sc.cover.t);
await p.screenshot({path:out,type:'jpeg',quality:95});await b.close();console.log('cover',out);

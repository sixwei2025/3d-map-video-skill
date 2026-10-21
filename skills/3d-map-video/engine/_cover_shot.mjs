import puppeteer from 'puppeteer-core'; import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path';
const base=path.join(os.homedir(),'.cache/hypit/html-rasterizer/chrome/chrome-headless-shell'); let exe;
for(const v of fs.readdirSync(base)){const p=path.join(base,v,'chrome-headless-shell-linux64/chrome-headless-shell'); if(fs.existsSync(p)) exe=p;}
const b=await puppeteer.launch({executablePath:exe,headless:'shell',args:['--no-sandbox']}); const pg=await b.newPage();
await pg.setViewport({width:1080,height:1920}); await pg.goto(`http://127.0.0.1:${process.argv[2]}/engine/cover.html`,{waitUntil:'networkidle0'});
await pg.evaluate(async()=>{await document.fonts.ready;}); await new Promise(r=>setTimeout(r,500));
await pg.screenshot({path:process.argv[3],type:'jpeg',quality:92}); await b.close();

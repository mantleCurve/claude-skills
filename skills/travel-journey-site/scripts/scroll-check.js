// Natural-scroll reveal check. Usage: node scroll-check.js <url>
const { chromium } = require('playwright');
const fs=require('fs'),path=require('path'),os=require('os');
function findChromium(){ const root=path.join(os.homedir(),'.cache','ms-playwright'); if(!fs.existsSync(root)) return undefined; for(const d of fs.readdirSync(root).filter(d=>d.startsWith('chromium-')).sort().reverse()) for(const sub of ['chrome-linux64/chrome','chrome-linux/chrome']){ const q=path.join(root,d,sub); if(fs.existsSync(q)) return q; } }
(async () => {
  const b = await chromium.launch({ executablePath: findChromium(), args:['--no-sandbox'] });
  for (const vp of [{width:1300,height:900},{width:400,height:860,isMobile:true}]) {
    const ctx = await b.newContext({ viewport: vp, isMobile: !!vp.isMobile, hasTouch: !!vp.isMobile }); const p = await ctx.newPage();
    const errs=[]; p.on('pageerror',e=>errs.push(e.message));
    await p.goto(process.argv[2]||'http://127.0.0.1:8790/', { waitUntil: 'networkidle' }); await p.waitForTimeout(500);
    // scroll like a person, no style overrides
    const H = await p.evaluate(()=>document.documentElement.scrollHeight);
    for (let y=0; y<H; y+=vp.height*0.8){ await p.evaluate(v=>scrollTo(0,v),y); await p.waitForTimeout(120); }
    const hidden = await p.evaluate(()=>[...document.querySelectorAll('.rv')].filter(e=>getComputedStyle(e).opacity==='0').map(e=>e.id||e.className).slice(0,5));
    const heads = await p.evaluate(()=>[...document.querySelectorAll('#dayList .cityhead h3')].map(h=>h.textContent+' before '+h.closest('.cityhead').nextElementSibling.querySelector('.dn').textContent.replace(/\s+/g,' ')));
    const dayOp = await p.evaluate(()=>[...document.querySelectorAll('#dayList .day')].map(d=>getComputedStyle(d).opacity).join(','));
    console.log(vp.width+'px', 'hidden after scroll:', hidden.length?hidden:'none', '| headers:', heads, '| day opacities:', dayOp, '| errors:', errs.join(';')||'none');
    await ctx.close();
  }
  await b.close();
})();

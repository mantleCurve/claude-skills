// Headless render check for a journey site. Usage: node check.js <url> [screenshot-dir]
// Needs playwright resolvable from NODE_PATH and a Chromium in ~/.cache/ms-playwright.
const fs = require('fs'), path = require('path'), os = require('os');
const { chromium } = require('playwright');
const url = process.argv[2] || 'http://127.0.0.1:8790/';
const outDir = process.argv[3] || '.';
function findChromium() {
  const root = path.join(os.homedir(), '.cache', 'ms-playwright');
  if (!fs.existsSync(root)) return undefined;
  const dirs = fs.readdirSync(root).filter(d => d.startsWith('chromium-')).sort().reverse();
  for (const d of dirs) for (const sub of ['chrome-linux64/chrome', 'chrome-linux/chrome']) {
    const p = path.join(root, d, sub); if (fs.existsSync(p)) return p;
  }
  return undefined;
}
(async () => {
  const b = await chromium.launch({ executablePath: findChromium(), args: ['--no-sandbox'] });
  const errs = [];
  const p = await b.newPage({ viewport: { width: 1300, height: 1000 } });
  p.on('pageerror', e => errs.push('PAGEERROR ' + e.message));
  p.on('console', m => { if (m.type() === 'error') errs.push('CONSOLE ' + m.text().slice(0, 200)); });
  p.on('requestfailed', r => errs.push('REQFAIL ' + r.url().slice(0, 120)));
  await p.goto(url, { waitUntil: 'networkidle' });
  await p.addStyleTag({ content: '.rv{opacity:1!important;transform:none!important}.bar{position:static!important}' });
  await p.waitForTimeout(2000);
  const info = await p.evaluate(() => ({
    days: document.querySelectorAll('#dayList .day').length,
    legs: document.querySelectorAll('#legList .leg').length,
    mapstats: (document.querySelector('#mapstats')?.innerText || '').replace(/\n/g, ' | '),
    clashes: [...document.querySelectorAll('#dayList .alert')].map(a => a.textContent).join(' || ') || 'none',
    legWarnings: [...document.querySelectorAll('#legList .bad')].map(a => a.textContent).join(' || ') || 'none',
    total: (document.querySelector('#tot tr.sum')?.innerText || '').replace(/\n/g, ' '),
    live: (document.querySelector('#live')?.innerText || '').replace(/\n/g, ' | ').slice(0, 240),
  }));
  console.log(JSON.stringify(info, null, 2));
  for (const sel of ['.hero', '#map', '#days .day', '#weather']) {
    try { await p.locator(sel).first().screenshot({ path: path.join(outDir, `check-${sel.replace(/\W+/g, '')}.png`) }); } catch (e) { errs.push('SHOT ' + sel + ' ' + e.message.split('\n')[0]); }
  }
  await b.close();
  console.log('errors:', errs.length ? '\n' + errs.join('\n') : 'none');
  if (errs.some(e => e.startsWith('PAGEERROR')) || info.days === 0) process.exit(1);
})();

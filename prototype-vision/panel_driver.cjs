// panel_driver.cjs — Playwright Chromium headless driver for the Deskcomm panel prototype.
// Commands (JSON on stdout):
//   probe <url> <out.png>   -> screenshot + DOM size + visible interactive elements (ground truth)
//   click <url> <x> <y>     -> click at coords, report document.activeElement + url
const { chromium } = require('playwright');

async function main() {
  const [cmd, url, ...rest] = process.argv.slice(2);

  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1280, height: 800 } });
  const t0 = Date.now();
  await page.goto(url, { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(1200);

  if (cmd === 'probe') {
    const out = rest[0];
    const shot = await page.screenshot({ path: out, type: 'png' });
    const dom = await page.evaluate(() => document.documentElement.outerHTML.length);
    const els = await page.evaluate(() => {
      const out = [];
      const seen = new Set();
      document.querySelectorAll('a, button, input, select, textarea, [role="button"]').forEach((el) => {
        const r = el.getBoundingClientRect();
        if (r.width < 2 || r.height < 2) return;
        if (r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) return;
        const cs = getComputedStyle(el);
        if (cs.visibility === 'hidden' || cs.display === 'none') return;
        const name = (el.getAttribute('aria-label') || el.placeholder || el.value || el.textContent || '').trim().slice(0, 60);
        const key = `${el.tagName}:${name}:${Math.round(r.x)},${Math.round(r.y)}`;
        if (seen.has(key)) return;
        seen.add(key);
        out.push({
          tag: el.tagName.toLowerCase(),
          type: el.getAttribute('type') || '',
          name,
          id: el.id || '',
          x: Math.round(r.x), y: Math.round(r.y),
          w: Math.round(r.width), h: Math.round(r.height),
          cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2),
        });
      });
      return out;
    });
    const texts = await page.evaluate(() => {
      const out = [];
      const seen = new Set();
      document.querySelectorAll('h1, h2, h3, label, p, span, div').forEach((el) => {
        if (el.children.length > 0) return;
        const t = (el.textContent || '').trim();
        if (!t || t.length > 80) return;
        const r = el.getBoundingClientRect();
        if (r.width < 4 || r.height < 4) return;
        if (r.bottom < 0 || r.top > innerHeight || r.right < 0 || r.left > innerWidth) return;
        const cs = getComputedStyle(el);
        if (cs.visibility === 'hidden' || cs.display === 'none') return;
        const key = `${el.tagName}:${t}:${Math.round(r.x)},${Math.round(r.y)}`;
        if (seen.has(key)) return;
        seen.add(key);
        out.push({ tag: el.tagName.toLowerCase(), text: t, x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height), cx: Math.round(r.x + r.width / 2), cy: Math.round(r.y + r.height / 2) });
      });
      return out.slice(0, 20);
    });
    console.log(JSON.stringify({
      width: 1280, height: 800, png_bytes: shot.length,
      dom_chars: dom, dom_tokens_est: Math.round(dom / 4),
      ms: Date.now() - t0, elements: els, texts,
    }, null, 2));
  } else if (cmd === 'links') {
    const links = await page.evaluate(() => [...document.querySelectorAll('a')].map(a => ({ text: (a.textContent || '').trim().slice(0, 60), href: a.getAttribute('href') })));
    console.log(JSON.stringify({ url: page.url(), links, ms: Date.now() - t0 }, null, 2));
  } else if (cmd === 'click') {
    const [x, y] = rest.map(Number);
    await page.mouse.click(x, y);
    await page.waitForTimeout(400);
    const active = await page.evaluate(() => {
      const el = document.activeElement;
      if (!el) return null;
      return { tag: el.tagName.toLowerCase(), id: el.id || '', name: el.getAttribute('aria-label') || el.placeholder || (el.textContent || '').trim().slice(0, 40) || '', type: el.getAttribute('type') || '' };
    });
    console.log(JSON.stringify({ active, url: page.url(), ms: Date.now() - t0 }, null, 2));
  } else {
    console.error('unknown cmd: ' + cmd);
    process.exitCode = 2;
  }
  await browser.close();
}

main().catch((e) => { console.error(e); process.exit(1); });

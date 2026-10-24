// Layout check for the catalogue HTML: reports text lines that collide with each other, text that
// runs outside the trim or into the 5 mm safety margin, and text clipped by its own box.
//   node check_layout.js <page.html> [...]     (exits 1 if anything is found)
const path = require('path');
const { pathToFileURL } = require('url');
const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  let total = 0;
  for (const file of process.argv.slice(2)) {
    await page.goto(pathToFileURL(path.resolve(file)).href);
    await page.evaluate(() => document.fonts.ready);
    const found = await page.evaluate(() => {
      const MM = 96 / 25.4;
      const out = [];
      const bleed = parseFloat(getComputedStyle(document.documentElement).getPropertyValue('--bleed')) || 0;
      document.querySelectorAll('.page').forEach((pg, pi) => {
        const pr = pg.getBoundingClientRect();
        const b = bleed * MM;
        const trim = { x0: pr.left + b, y0: pr.top + b, x1: pr.right - b, y1: pr.bottom - b };
        const items = [];
        const walker = document.createTreeWalker(pg, NodeFilter.SHOW_TEXT);
        let n;
        while ((n = walker.nextNode())) {
          const t = n.textContent.replace(/\s+/g, ' ').trim();
          if (!t) continue;
          const el = n.parentElement;
          const cs = getComputedStyle(el);
          if (cs.visibility === 'hidden' || cs.display === 'none') continue;
          const r = document.createRange();
          r.selectNodeContents(n);
          for (const rc of r.getClientRects()) {
            if (rc.width < 0.5 || rc.height < 0.5) continue;
            items.push({ el, t: t.slice(0, 48), x0: rc.left, y0: rc.top, x1: rc.right, y1: rc.bottom });
          }
          // clipped by an ancestor with overflow hidden
          for (let a = el; a && a !== pg; a = a.parentElement) {
            const acs = getComputedStyle(a);
            if (acs.overflow === 'hidden' || acs.overflowX === 'hidden' || acs.overflowY === 'hidden') {
              if (a.scrollWidth > a.clientWidth + 1 || a.scrollHeight > a.clientHeight + 1) {
                out.push(`p${pi + 1} clipped: "${t.slice(0, 48)}" in <${a.tagName.toLowerCase()} class="${a.className}">`);
              }
              break;
            }
          }
        }
        const seen = new Set();
        for (let i = 0; i < items.length; i++) {
          const a = items[i];
          if (a.x0 < trim.x0 + 5 * MM - 0.5 || a.x1 > trim.x1 - 5 * MM + 0.5 || a.y0 < trim.y0 + 5 * MM - 0.5 || a.y1 > trim.y1 - 5 * MM + 0.5) {
            const k = 'm' + a.t;
            if (!seen.has(k)) {
              seen.add(k);
              const d = Math.min(a.x0 - trim.x0, trim.x1 - a.x1, a.y0 - trim.y0, trim.y1 - a.y1) / MM;
              out.push(`p${pi + 1} margin: "${a.t}" is ${d.toFixed(1)} mm from the trim`);
            }
          }
          for (let j = i + 1; j < items.length; j++) {
            const c = items[j];
            if (a.el === c.el || a.el.contains(c.el) || c.el.contains(a.el)) continue;
            const ox = Math.min(a.x1, c.x1) - Math.max(a.x0, c.x0);
            const oy = Math.min(a.y1, c.y1) - Math.max(a.y0, c.y0);
            if (ox > 1 && oy > 1) {
              const k = a.t + '|' + c.t;
              if (!seen.has(k)) {
                seen.add(k);
                out.push(`p${pi + 1} overlap: "${a.t}" × "${c.t}" (${(ox / MM).toFixed(1)} × ${(oy / MM).toFixed(1)} mm)`);
              }
            }
          }
        }
      });
      return out;
    });
    total += found.length;
    console.log(`${file.split('/').pop()}: ${found.length ? found.length + ' issue(s)' : 'clean'}`);
    found.forEach((f) => console.log('  ' + f));
  }
  await browser.close();
  process.exitCode = total ? 1 : 0;
})();

// Print a catalogue's HTML to PDF with Chromium: the page size comes from the document's @page rule.
const { chromium } = require('playwright');
const path = require('path');
(async () => {
  const [,, htmlPath, pdfPath] = process.argv;
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('file://' + path.resolve(htmlPath), { waitUntil: 'networkidle' });
  await page.evaluate(async () => { await document.fonts.ready; });
  // every background image decoded before printing
  await page.evaluate(async () => {
    const urls = new Set();
    document.querySelectorAll('[style*="background-image"]').forEach((el) => {
      const m = /url\(['"]?([^'")]+)['"]?\)/.exec(el.style.backgroundImage); if (m) urls.add(m[1]);
    });
    await Promise.all([...urls].map((u) => new Promise((res) => { const i = new Image(); i.onload = i.onerror = res; i.src = u; })));
  });
  await page.pdf({ path: pdfPath, preferCSSPageSize: true, printBackground: true, outline: true, tagged: true });
  await browser.close();
})();

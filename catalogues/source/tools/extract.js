// Extract the sink records and the embedded product photographs from index.html
const fs = require('fs');
const path = require('path');
const [,, htmlPath, outDir] = process.argv;
const s = fs.readFileSync(htmlPath, 'utf8');
fs.mkdirSync(path.join(outDir, 'photos'), { recursive: true });

function grabBalanced(src, startIdx, open, close) {
  let depth = 0, i = startIdx, inStr = null, esc = false;
  for (; i < src.length; i++) {
    const c = src[i];
    if (inStr) { if (esc) esc = false; else if (c === '\\') esc = true; else if (c === inStr) inStr = null; continue; }
    if (c === '"' || c === "'" || c === '`') { inStr = c; continue; }
    if (c === open) depth++;
    else if (c === close) { depth--; if (depth === 0) return src.slice(startIdx, i + 1); }
  }
  throw new Error('unbalanced');
}
const at = (marker) => { const i = s.indexOf(marker); if (i < 0) throw new Error('missing ' + marker); return i; };

// finish palette F (the one with pearl/pure/titan)
const fIdx = s.search(/const F = \{\s*\n\s*steel:/); if (fIdx < 0) throw new Error('no F');
const Fsrc = grabBalanced(s, s.indexOf('{', fIdx), '{', '}');
const F = eval('(' + Fsrc + ')');
const SSFsrc = grabBalanced(s, s.indexOf('{', at('const SSF = {')), '{', '}');
const SSF = eval('(' + SSFsrc + ')');
const Gsrc = grabBalanced(s, s.indexOf('[', at('const GRANITE = [')), '[', ']');
const GRANITE = eval('(' + Gsrc + ')');
const Ssrc = grabBalanced(s, s.indexOf('[', at('const STAINLESS = [')), '[', ']');
const STAINLESS = eval('(' + Ssrc + ')');
fs.writeFileSync(path.join(outDir, 'granite.json'), JSON.stringify(GRANITE, null, 1));
fs.writeFileSync(path.join(outDir, 'stainless.json'), JSON.stringify(STAINLESS, null, 1));
fs.writeFileSync(path.join(outDir, 'ssf.json'), JSON.stringify(SSF, null, 1));

// photographs
const imgSrc = grabBalanced(s, s.indexOf('{', at('const SINK_IMG = {')), '{', '}');
const IMG = eval('(' + imgSrc + ')');
const asg = grabBalanced(s, s.indexOf('{', at('Object.assign(SINK_IMG, {')), '{', '}');
Object.assign(IMG, eval('(' + asg + ')'));
for (const [k, v] of Object.entries(IMG)) {
  const m = /^data:image\/([a-z]+);base64,(.*)$/.exec(v);
  if (!m) { console.log('skip', k); continue; }
  fs.writeFileSync(path.join(outDir, 'photos', k + '.' + m[1]), Buffer.from(m[2], 'base64'));
}
console.log('granite', GRANITE.length, 'stainless', STAINLESS.length, 'photos', Object.keys(IMG).length);

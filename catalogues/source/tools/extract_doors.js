// The door records, as the website builds them: the UPVC door block of index.html (from DOOR_COLOUR to
// CATALOG.push(...DOORS)) and the door catalogue's sections, run as they are, then written out as JSON for the
// door catalogue's generator.
//   node extract_doors.js <index.html> <out.json>
const fs = require('fs');
const vm = require('vm');
const [,, htmlPath, outPath] = process.argv;
const s = fs.readFileSync(htmlPath, 'utf8').replace(/\r\n/g, '\n');
const cut = (from, to) => {
  const a = s.indexOf(from), b = s.indexOf(to, a);
  if (a < 0 || b < 0) throw new Error('not found: ' + (a < 0 ? from : to));
  return s.slice(a, b);
};
const records = cut('const DOOR_COLOUR = {', 'CATALOG.push(...DOORS);');
const sections = cut('const DOOR_TYPE_EN = {', 'const doorSectionOf');
const ctx = { SINK_IMG: {}, CATALOG: [], out: null };
vm.createContext(ctx);
vm.runInContext(records + '\n' + sections + `
out = {
  size: DOOR_SIZE, colours: DOOR_COLOUR, colourOrder: DOOR_ORDER, lists: DOOR_LIST, types: DOOR_TYPE, typeEn: DOOR_TYPE_EN,
  offWeb: [...DOOR_OFF_WEB],
  sections: DOOR_SECTIONS.map((x) => ({ id: x.id, types: x.types, title: x.title, line: x.line })),
  models: DOOR_MODELS.map((m) => ({ code: m.code, wl: m.wl || null, name: doorName(m), key: doorKey(m), type: m.type,
    typeAs: DOOR_TYPE[m.type].as, price: m.price, codes: m.codes, lists: m.lists || null, cols: m.cols,
    motif: m.motif || null, look: m.look || null, short: doorShort(m),
    rows: DOORS.filter((r) => r.code === m.code).map((r) => ({ slug: r.slug, colour: r.doorCol, list: r.listCol, typeAs: r.typeAs,
      photos: r.photos, hands: r.hands, spec: r.spec.map(([k, v]) => [k.en, typeof v === 'object' && v ? v.en : v]),
      desc: r.desc })) })),
};`, ctx);
fs.writeFileSync(outPath, JSON.stringify(ctx.out, null, 1));
const n = ctx.out.models.reduce((a, m) => a + m.rows.reduce((b, r) => b + r.hands.length, 0), 0);
console.log(outPath + ': ' + ctx.out.models.length + ' models, ' + ctx.out.models.reduce((a, m) => a + m.rows.length, 0) + ' records, ' + n + ' codes');

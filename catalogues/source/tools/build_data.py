"""Compile the catalogue's facts from the records extracted out of index.html.

Only what the source records hold is carried over (model codes, colours, sizes, bowls,
installation, material, finish, edge, thickness, included items). Anything unclear or
inconsistent in the source is carried as a flag, never resolved by guessing."""
import json, sys, os

src, out = sys.argv[1], sys.argv[2]
G = json.load(open(os.path.join(src, 'granite.json')))
S = json.load(open(os.path.join(src, 'stainless.json')))
en = lambda v: v['en'] if isinstance(v, dict) else v
spec = lambda r, key: next((en(v) for k, v in r['spec'] if en(k) == key), None)

ORDER = ['pearl', 'pure', 'titan']
COLOUR = {'pearl': 'Pearl Black', 'pure': 'Pure White', 'titan': 'Titanium Grey'}

granite = []
for model in dict.fromkeys(r['model'] for r in G):
    rows = sorted([r for r in G if r['model'] == model], key=lambda r: ORDER.index(r['colourId']))
    r0 = rows[0]
    w, d = [int(x) for x in spec(r0, 'Dimensions').replace('mm', '').split('×')]
    granite.append({
        'model': model, 'slug': model.lower().replace(' ', '-'),
        'bowls': spec(r0, 'Bowls'), 'installation': spec(r0, 'Installation'),
        'material': spec(r0, 'Material'), 'dims': [w, d],
        'colours': [{'id': r['colourId'], 'name': en(r['colour']), 'photo': r['photos'][0]} for r in rows],
        'features': [en(f) for f in r0['feat']],
    })

BOWLS = {'one': 'Single bowl', 'two': 'Double bowl', 'oneD': 'Single bowl with drainboard',
         'twoD': 'Double bowl with drainboard', 'wl11': 'Two bowls with a small centre bowl', None: None}
stainless = []
for r in S:
    stainless.append({
        'model': r['model'], 'slug': r['slug'], 'range': 'Pressed' if r['section'] == 'pressed' else 'Hand Made',
        'brand': r['brand'], 'grade': r['grade'], 'material': spec(r, 'Material'),
        'finish': r['finishes'][0]['name']['en'], 'edge': r['edge'], 'thickness': spec(r, 'Thickness'),
        'size_printed': spec(r, 'Size'), 'dims': r['dims'], 'dims_unconfirmed': bool(r['dimsNote']),
        'bowls': BOWLS[r['bowls']], 'included': r['extra'], 'pack': spec(r, 'Pack'), 'box': spec(r, 'Box'),
        'photo': r['photos'][0],
    })

json.dump({'granite': granite, 'stainless': stainless}, open(out, 'w'), indent=1, ensure_ascii=False)
print(len(granite), 'granite models;', len(stainless), 'stainless models')
for m in granite: print(' ', m['model'], m['dims'], m['bowls'], m['installation'], [c['name'] for c in m['colours']])

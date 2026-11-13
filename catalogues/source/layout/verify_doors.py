"""Check the door catalogue against the website's door records, independently of build_doors.py.

    python verify_doors.py <doors.json> <work dir> <pdf dir>

doors.json: the door records as tools/extract_doors.js reads them from index.src.html; work dir: the built pages; pdf dir:
the finished PDFs. For each of the four editions:
  · every model has exactly one page of its own, headed with its name;
  · on it, the printed size, specification as printed, model, colours, lists and opening match its records, and its
    table of codes gives each colour (and list) and each opening exactly the code its record has — no other code;
  · the codes page gives every code of the records once, each under its model, colour, list and opening;
  · the index lists every model once, with the page it is on;
  · the PDF has 32 pages, its bookmark for every model points at that page, and its text holds every code;
  · nowhere a price, nor a code the website leaves out.
Prints one line per problem and a summary; exits 1 if there are problems."""
import html
import json
import os
import re
import sys
from pypdf import PdfReader

sys.path.insert(0, os.path.dirname(__file__))
import i18n  # noqa: E402
import i18n_doors  # noqa: E402
WORDS = {**i18n.ID, **i18n_doors.ID}

data_p, work, pdfs = sys.argv[1:4]
D = json.load(open(data_p))
problems = []
CODE = re.compile(r"WELUP-DPT\d{7}")


def text(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or "")).replace(" ", "").replace("†", "")
    return re.sub(r"\s+", " ", s).strip()


def pages_of(h):
    return [p for p in re.split(r'(?=<section class="page )', h) if p.startswith('<section class="page ')]


ALL = {h["code"]: (m["code"], r["colour"], r["list"], h["id"]) for m in D["models"] for r in m["rows"] for h in r["hands"]}
OFF = set(D["offWeb"])
assert len(ALL) == sum(len(r["hands"]) for m in D["models"] for r in m["rows"]), "a code twice in the records"
assert not OFF & set(ALL), "a code the website leaves out is in the records"

EDITIONS = [("screen", "en", ""), ("screen", "id", "_ID"), ("print", "en", "_PRINT"), ("print", "id", "_ID_PRINT")]
NAME = "MTJ_Wellup_UPVC_Door_Collection_Vol03"
checked = 0
for mode, lang, sfx in EDITIONS:
    tag = f"doors-{mode}" + ("" if lang == "en" else "-" + lang)
    L = (lambda s: s) if lang == "en" else (lambda s: WORDS.get(s, s))
    colour = {c: v[lang] for c, v in D["colours"].items()}
    colour_back = {v: k for k, v in colour.items()}
    lname = {l: v["en"] if lang == "en" else v["id"] for l, v in D["lists"].items()}
    list_back = {v: k for k, v in lname.items()}
    h = open(os.path.join(work, tag + ".html"), encoding="utf8").read()
    pages = pages_of(h)
    if len(pages) != 32:
        problems.append(f"{tag}: {len(pages)} pages, not 32")
    for c in OFF:
        if c in h:
            problems.append(f"{tag}: {c} is printed, but the website leaves it out")
    if re.search(r"\bRp\b", text(h)):
        problems.append(f"{tag}: a price is printed")
    if "{PAGE:" in h:
        problems.append(f"{tag}: a page number left unset")

    feature = {}
    for m in D["models"]:
        idx = [i for i, p in enumerate(pages) if f'id="m-{m["key"]}"' in p.split(">", 1)[0]]
        if len(idx) != 1:
            problems.append(f"{tag}: {m['name']}: on {len(idx)} pages")
            continue
        i = idx[0]
        p = pages[i]
        feature[m["name"]] = i + 1
        mh = re.search(r'<h2 class="code">(.*?)</h2>', p)
        if not mh or text(mh.group(1)) != m["name"]:
            problems.append(f"{tag}: {m['name']}: headed {mh and text(mh.group(1))!r}")
        specs = {text(k): text(v) for k, v in re.findall(r"<dt>(.*?)</dt><dd>(.*?)</dd>", p)}

        def want(label, value):
            got = specs.get(L(label))
            if got != value:
                problems.append(f"{tag}: {m['name']}: {label}: printed {got!r}, the records have {value!r}")
        want("Size", D["size"])
        want("Specification, as printed", f'{D["size"]}, 1.8mm, {m["typeAs"]}')
        want("Model", m["name"])
        want("Colours", " · ".join(colour[c] for c in D["colourOrder"]))
        if m["lists"]:
            want("Lists", " · ".join(lname[l] for l in m["lists"]))
        elif L("Lists") in specs:
            problems.append(f"{tag}: {m['name']}: a list printed, but it has none")
        op = specs.get(L("Opening"), "")
        if not op.startswith("R / L"):
            problems.append(f"{tag}: {m['name']}: opening printed {op!r}")
        for r in m["rows"]:
            if len(r["hands"]) < 2 and colour[r["colour"]] not in op:
                problems.append(f"{tag}: {m['name']}: {r['colour']} is offered in one opening only, and the page does not say so")
        # the codes on the page, and which colour, list and opening each is printed under
        own = {h_["code"] for r in m["rows"] for h_ in r["hands"]}
        if set(CODE.findall(p)) != own:
            problems.append(f"{tag}: {m['name']}: codes printed {sorted(set(CODE.findall(p)) ^ own)} differ from its records")
        table = re.search(r'<table class="dcodes[^"]*">(.*?)</table>', p, re.S)
        seen = set()
        for tr in re.findall(r"<tr>(.*?)</tr>", table.group(1) if table else "", re.S):
            tds = [text(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if not tds:
                continue
            c = colour_back.get(tds[0])
            lst = list_back.get(tds[1]) if m["lists"] else None
            r = next((q for q in m["rows"] if q["colour"] == c and q["list"] == lst), None)
            if r is None:
                problems.append(f"{tag}: {m['name']}: a row for {tds[:2]} that the records do not have")
                continue
            for hid, cell in zip(("R", "L"), tds[-2:]):
                rec = next((q["code"] for q in r["hands"] if q["id"] == hid), None)
                if (rec or None) != (cell if CODE.fullmatch(cell) else None):
                    problems.append(f"{tag}: {m['name']} {c} {lst or ''} {hid}: printed {cell!r}, the records have {rec!r}")
                if rec:
                    seen.add(rec)
        if seen != own:
            problems.append(f"{tag}: {m['name']}: its table gives {len(seen)} of its {len(own)} codes")
        checked += 1

    # the codes page: every code once, under its model, list, colour and opening
    cp = [p for p in pages if 'class="page index dallcodes' in p]
    if len(cp) != 1:
        problems.append(f"{tag}: {len(cp)} codes pages")
    else:
        found = CODE.findall(cp[0])
        if sorted(found) != sorted(ALL):
            problems.append(f"{tag}: the codes page gives {len(found)} codes ({len(set(found))} different); the records have {len(ALL)}")
        cols = [(c, hid) for c in D["colourOrder"] for hid in ("R", "L")]
        for tr in re.findall(r"<tr>(.*?)</tr>", cp[0], re.S):
            tds = [text(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(tds) != len(cols) + 3:
                continue
            model, lst = tds[0], list_back.get(tds[1])
            for (c, hid), cell in zip(cols, tds[2:-1]):
                if CODE.fullmatch(cell) and ALL.get(cell) != (model, c, lst, hid):
                    problems.append(f"{tag}: codes page: {cell} printed under {model} {c} {lst} {hid}, the records have {ALL.get(cell)}")
            m = next((q for q in D["models"] if q["code"] == model), None)
            if m and tds[-1] != f'{feature.get(m["name"], 0):02d}':
                problems.append(f"{tag}: codes page: {model} on page {tds[-1]}, its page is {feature.get(m['name'])}")

    # the index: every model once, with its page
    ip = [p for p in pages if 'class="page index dindex' in p]
    if len(ip) != 1:
        problems.append(f"{tag}: {len(ip)} index pages")
    else:
        for m in D["models"]:
            rows = [tr for tr in re.findall(r"<tr>(.*?)</tr>", ip[0], re.S) if re.search(r'<td class="m">.*?' + re.escape(html.escape(m["name"])) + r"<", tr)]
            if len(rows) != 1:
                problems.append(f"{tag}: index: {m['name']} listed {len(rows)} times")
                continue
            tds = [text(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", rows[0], re.S)]
            if tds[-1] != f'{feature.get(m["name"], 0):02d}':
                problems.append(f"{tag}: index: {m['name']} on page {tds[-1]}, its page is {feature.get(m['name'])}")
            if tds[1] != m["typeAs"]:
                problems.append(f"{tag}: index: {m['name']}: type {tds[1]!r}, the records have {m['typeAs']!r}")

    # the PDF: its pages, bookmarks and text
    pdf = os.path.join(pdfs, NAME + sfx + ".pdf")
    if not os.path.exists(pdf):
        problems.append(f"{pdf}: missing")
        continue
    rd = PdfReader(pdf)
    if len(rd.pages) != 32:
        problems.append(f"{pdf}: {len(rd.pages)} pages")
    marks = {}

    def walk(items):
        for it in items:
            if isinstance(it, list):
                walk(it)
            else:
                marks[it.title] = rd.get_destination_page_number(it) + 1
    walk(rd.outline)
    for name_, pg in feature.items():
        if marks.get(name_) != pg:
            problems.append(f"{pdf}: bookmark {name_!r} at {marks.get(name_)}, its page is {pg}")
    raw = "".join(pg.extract_text() or "" for pg in rd.pages)
    pua = sorted({ch for ch in raw if 0xE000 <= ord(ch) <= 0xF8FF})
    if pua:
        problems.append(f"{pdf}: {len(pua)} characters that copy out as private-use code points (a glyph alternate in the text)")
    flat = re.sub(r"\s+", "", raw)
    missing = [c for c in ALL if c not in flat]
    if missing:
        problems.append(f"{pdf}: {len(missing)} codes not in its text, e.g. {missing[:3]}")
    for c in OFF:
        if c in flat:
            problems.append(f"{pdf}: {c} in its text")
    if re.search(r"Rp\d", flat):
        problems.append(f"{pdf}: a price in its text")

for p in problems:
    print("PROBLEM", p)
print(f"verify_doors: {checked} model pages in {len(EDITIONS)} editions, {len(ALL)} codes; {len(problems)} problem(s)")
sys.exit(1 if problems else 0)

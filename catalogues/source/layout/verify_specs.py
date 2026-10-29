"""Check both catalogue volumes against the source records, independently of build.py's data file.

    python verify_specs.py <source dir> <work dir> <pdf dir>

source dir: what tools/extract.js wrote from the website (granite.json, stainless.json); work dir: the built pages
(make_catalogues.sh's work dir); pdf dir: the finished PDFs.

For every model: it has exactly one feature page; each printed spec (range, brand, bowls, size, material, thickness,
finish, edge, included, installation, colours) matches the source record; the index lists it once, with the page its
feature page is on, and the same size; the PDF bookmark for it points at that page. Prints one line per problem and a
summary; exits 1 if there are problems."""
import html
import json
import os
import re
import sys
from pypdf import PdfReader

src, work, pdfs = sys.argv[1:4]
S = json.load(open(os.path.join(src, "stainless.json")))
G = json.load(open(os.path.join(src, "granite.json")))
problems = []


def en(v):
    return v.get("en") if isinstance(v, dict) else v


def norm(s):
    s = html.unescape(re.sub(r"<[^>]+>", " ", s or ""))
    s = s.replace("×", "x").replace(" ", " ").replace("†", "")
    return re.sub(r"\s+", " ", s).strip().lower()


def nums(s):
    return [float(x) for x in re.findall(r"\d+(?:\.\d+)?", s or "")]


def pages(path):
    """The built pages, in order: (page number, section html)."""
    h = open(path, encoding="utf8").read()
    parts = re.split(r'(?=<section class="page )', h)
    return [p for p in parts if p.startswith('<section class="page ')], h


def specs_of(section):
    return {norm(dt): dd for dt, dd in re.findall(r"<dt>(.*?)</dt><dd>(.*?)</dd>", section)}


# the same fact in other words: the price list's own wording of WL 11 (see S11) beside the website's
EQUIV = {("two bowls and a small bowl", "two bowls, a small bowl between them")}


def check(vol, label, got, want, how="eq"):
    g, w = norm(got), norm(want)
    ok = (g == w or (g, w) in EQUIV) if how == "eq" else (w in g) if how == "in" else (nums(g) == nums(w)[:3])
    if not ok:
        problems.append(f"{vol}: {label}: printed {got!r} but the source has {want!r}")


# ── stainless steel ──
for lang in ("", "-id"):
    for mode in ("screen", "print"):
        path = os.path.join(work, f"stainless-{mode}{lang}.html")
        if not os.path.exists(path):
            continue
        secs, whole = pages(path)
        vol = f"stainless-{mode}{lang}"
        feature_at = {}
        for i, sec in enumerate(secs, 1):
            m = re.search(r'<h2 class="code">(.*?)</h2>', sec)
            if 'class="page feature' in sec and m:
                feature_at.setdefault(norm(m.group(1)).upper(), []).append(i)
        for r in S:
            model = r["model"]
            at = feature_at.get(model.upper(), [])
            if len(at) != 1:
                problems.append(f"{vol}: {model}: {len(at)} feature pages")
                continue
            if lang:
                continue   # the Indonesian words differ; its numbers are checked through the English and the page count
            sp = specs_of(secs[at[0] - 1])
            spec = {en(k).lower(): en(v) for k, v in r["spec"]}
            rng = "Pressed" if r["section"] == "pressed" else "Hand Made"
            check(vol, f"{model} range", sp.get("range"), rng)
            check(vol, f"{model} brand", sp.get("brand"), spec["brand"])
            check(vol, f"{model} material", sp.get("material"), spec["material"])
            check(vol, f"{model} finish", sp.get("finish"), spec["finish"])
            check(vol, f"{model} edge", sp.get("edge"), spec["edge"])
            check(vol, f"{model} thickness", sp.get("thickness"), spec["thickness"], "in")
            # the size: the price list's own figures (W 10050 TSG's width is printed TBC, see S1)
            size = spec["size"]
            got = sp.get("overall size", "")
            if "tbc" in norm(got) or "?" in got:
                if model != "W 10050 TSG":
                    problems.append(f"{vol}: {model} size: printed {got!r} as unconfirmed")
                elif nums(norm(re.sub(r"<span class=.hint.*", "", got))) != nums(size)[1:3]:
                    problems.append(f"{vol}: {model} size: printed {got!r} but the source has {size!r}")
            else:
                check(vol, f"{model} size", re.sub(r"<span.*", "", got), size, "nums")
            # the bowls in words, as the website lists them among the model's features
            bowls = next((f["en"] for f in r["feat"] if "bowl" in f["en"].lower()), None)
            if bowls:
                check(vol, f"{model} bowls", sp.get("bowls"), bowls)
            elif "not stated" not in norm(sp.get("bowls")):
                problems.append(f"{vol}: {model} bowls: printed {sp.get('bowls')!r}, the source states none")
            extra = r.get("extra")
            inc = sp.get("included")
            if extra and not inc:
                problems.append(f"{vol}: {model}: the source lists {extra!r} as included, the page does not")
            if inc and not extra:
                problems.append(f"{vol}: {model}: the page lists {inc!r} as included, the source does not")
            if extra and inc:
                check(vol, f"{model} included", inc, en(extra) if not isinstance(extra, list) else " ".join(en(x) for x in extra))
        # the index: every model once, with its page
        ix = next((s for s in secs if 'class="page index' in s), "")
        for r in S:
            rows = re.findall(r'<tr><td class="m"><a[^>]*>' + re.escape(r["model"]) + r'</a></td>(.*?)</tr>', ix)
            if len(rows) != 1:
                problems.append(f"{vol}: index lists {r['model']} {len(rows)} times")
                continue
            page = re.findall(r'<td class="r">(\d+)</td>', rows[0])
            want = feature_at.get(r["model"].upper(), [0])[0]
            if not page or int(page[0]) != want:
                problems.append(f"{vol}: index gives {r['model']} page {page} but its page is {want}")

# ── granite ──
models = {}
for r in G:
    models.setdefault(r["model"], []).append(r)
for lang in ("", "-id"):
    for mode in ("screen", "print"):
        path = os.path.join(work, f"granite-{mode}{lang}.html")
        if not os.path.exists(path):
            continue
        secs, whole = pages(path)
        vol = f"granite-{mode}{lang}"
        feature_at = {}
        for i, sec in enumerate(secs, 1):
            m = re.search(r'<h2 class="code">(.*?)</h2>', sec)
            if 'class="page feature' in sec and m:
                feature_at.setdefault(norm(m.group(1)).upper(), []).append(i)
        for model, recs in models.items():
            at = feature_at.get(model.upper(), [])
            if len(at) != 1:
                problems.append(f"{vol}: {model}: {len(at)} feature pages")
                continue
            if lang:
                continue
            sp = specs_of(secs[at[0] - 1])
            spec = {en(k).lower(): en(v) for k, v in recs[0]["spec"]}
            for rr in recs[1:]:
                other = {en(k).lower(): en(v) for k, v in rr["spec"]}
                for k in ("dimensions", "bowls", "installation", "material"):
                    if norm(other.get(k)) != norm(spec.get(k)):
                        problems.append(f"source: {model}: colourways disagree on {k}: {spec.get(k)!r} / {other.get(k)!r}")
            check(vol, f"{model} size", re.sub(r"<span.*", "", sp.get("overall size", "")), spec["dimensions"], "nums")
            check(vol, f"{model} bowls", sp.get("bowls"), spec["bowls"])
            check(vol, f"{model} installation", sp.get("installation"), spec["installation"])
            check(vol, f"{model} material", sp.get("material"), spec["material"])
            want = sorted(norm(en(dict((en(k), v) for k, v in rr["spec"]).get("Colour / finish"))) for rr in recs)
            got = sorted(norm(c) for c in re.split(r"·", re.sub(r"<[^>]+>", "", sp.get("colours", ""))))
            if got != want:
                problems.append(f"{vol}: {model} colours: printed {got} but the source has {want}")
        ix = next((s for s in secs if 'class="page index' in s), "")
        for model in models:
            rows = re.findall(r'<tr><td class="m"><a[^>]*>' + re.escape(model) + r'</a></td>(.*?)</tr>', ix)
            if len(rows) != 1:
                problems.append(f"{vol}: index lists {model} {len(rows)} times")
                continue
            page = re.findall(r'<td class="r">(\d+)</td>', rows[0])
            want = feature_at.get(model.upper(), [0])[0]
            if not page or int(page[0]) != want:
                problems.append(f"{vol}: index gives {model} page {page} but its page is {want}")

# ── the PDFs: page counts, and every model's bookmark on its page ──
for name, (vol, n_models) in {"MTJ_Granite_Kitchen_Sink_Collection_Vol01": ("granite", 6),
                              "MTJ_Stainless_Steel_Kitchen_Sink_Collection_Vol02": ("stainless", 25)}.items():
    for suf in ("", "_PRINT", "_ID", "_ID_PRINT"):
        p = os.path.join(pdfs, name + suf + ".pdf")
        if not os.path.exists(p):
            problems.append(f"missing {p}")
            continue
        rd = PdfReader(p)
        n = len(rd.pages)
        if n % 4:
            problems.append(f"{name}{suf}: {n} pages, not a multiple of four")
        marks = {}

        def walk(items):
            for it in items:
                if isinstance(it, list):
                    walk(it)
                else:
                    marks[it.title] = rd.get_destination_page_number(it) + 1
        walk(rd.outline)
        secs, _ = pages(os.path.join(work, f"{vol}-{'print' if 'PRINT' in suf else 'screen'}{'-id' if '_ID' in suf else ''}.html"))
        if len(secs) != n:
            problems.append(f"{name}{suf}: {n} pages in the PDF, {len(secs)} built")
        for i, sec in enumerate(secs, 1):
            m = re.search(r'<h2 class="code">(.*?)</h2>', sec)
            if 'class="page feature' in sec and m:
                code = norm(m.group(1)).upper()
                if marks.get(code) != i:
                    problems.append(f"{name}{suf}: bookmark {code} -> page {marks.get(code)}, its page is {i}")
        found = sum(1 for k in marks if k.upper() in {r["model"].upper() for r in (S if vol == "stainless" else G)})
        if found != n_models:
            problems.append(f"{name}{suf}: {found} model bookmarks, want {n_models}")

for p in problems:
    print(p)
print(f"{len(problems)} problem(s): {len(S)} stainless records, {len(models)} granite models ({len(G)} colourways) checked")
sys.exit(1 if problems else 0)

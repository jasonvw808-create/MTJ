"""Build the two catalogue volumes as HTML (one page per A4 sheet) from the verified product data.

    python build.py <data.json> <out_dir> [print|screen]

Every product fact comes from data.json (extracted from the shop's records: the granite listings
and the stainless steel Price List 2024). Nothing here adds a feature or a specification; where the
source is unclear the page says so with a dagger (†) and a note."""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import drawings  # noqa: E402

E = html.escape
CODE = re.compile(r'\b(?:LPS|WL|GDU|GST|GSU|W) \d{2,5}(?: [A-Z]{1,4})?\b')


def T(s):
    """Escaped text in which no model code breaks across a line."""
    return CODE.sub(lambda m: f'<span class="nw">{m.group(0)}</span>', E(s))


def series(items):
    """Model codes as a list that breaks only after a separator, never inside a code."""
    items = list(items)
    return " ".join(f'<span class="nw">{E(x)}{" ·" if i < len(items) - 1 else ""}</span>' for i, x in enumerate(items))
EDITION = "2026"

# ── what each model page shows (the facts themselves come from data.json) ──
GRANITE_SHOW = {
    "GDU 8145": dict(recipe="gdu8145", colour="pearl", setting="Honed marble · smoked oak"),
    "GST 6045": dict(recipe="gst6045", colour="pure", setting="White oak worktop · sage cabinetry"),
    "GST 7546": dict(recipe="gst7546", colour="pearl", setting="Concrete · black cabinetry"),
    "GSU 6045": dict(recipe="gsu6045", colour="titan", setting="White quartz · slatted ash"),
    "GSU 7545": dict(recipe="gsu7545", colour="pure", setting="Black marble · emerald lacquer"),
    "GSU 8045": dict(recipe="gsu8045", colour="titan", setting="Travertine · terracotta tile"),
}
STEEL_SETTING = {
    "LPS 5040": "Terrazzo · powder-blue cabinetry", "LPS 7540 A": "Oak worktop · white shaker", "LPS 8643 A": "Limestone · blue zellige",
    "LPS 9643 A": "Concrete · black cabinetry", "LPS 10050 A": "Oak worktop · slate-blue shaker", "WL 03": "Terrazzo · teak slats",
    "WL 05 A": "White marble · navy shaker", "WL 07": "White quartz · walnut · ochre tile", "WL 11": "Terrazzo island · grey-blue shaker",
    "WL 12": "Microcement", "WL 18": "White quartz · light oak", "W 5050 TSB": "Honed marble · walnut",
    "W 6045 TSS": "White quartz · white oak", "W 6045 TSB": "Concrete · ochre lacquer", "W 7546 TSB": "Limestone · smoked oak",
    "W 7546 TSBN": "Grey porcelain · charcoal gloss", "W 7646 USS": "Black stone · white tile", "W 7646 USB": "White quartz · fluted oak",
    "W 7845 UDS": "Honed grey marble · greige", "W 7845 UDB": "Calacatta marble · oxblood lacquer", "W 8050 TSS": "White quartz · white lacquer",
    "W 8050 TSB": "Limestone · walnut", "W 8245 TDB": "White marble · pale blue shaker", "W 8550 TDG": "Grey porcelain island",
    "W 10050 TSG": "Warm quartz · charcoal cabinetry",
}
COLOUR_NAME = {"pearl": "Pearl Black", "pure": "Pure White", "titan": "Titanium Grey"}
COLOUR_DOT = {"pearl": "#1f1f1f", "pure": "#f2f1ee", "titan": "#a9abab"}
FINISH_DOT = {"Mat Polished": "#c3c4c1", "Electroplate": "#dcdddb", "Satin": "#a9aaa7", "Nano Black": "#2a2a2b"}

DECK = "Knife holder, soap dispenser and control knob are shown as in the product photograph; they are not listed in the price list — to be confirmed."
NOTES = {
    "GST 7546": ["The deck fittings (glass rinser, pull-out spray, tap, control knob and drain button) are shown as in the product photographs; they are not itemised in the source — to be confirmed."],
    "WL 07": ["Drainboard shown on the right, as in the product photograph; the price-list picture shows it on the left — handing to be confirmed."],
    "WL 12": ["Drainboard shown on the right, as in the product photograph; the price-list picture shows it on the left — handing to be confirmed."],
    "WL 18": ["Drainboard shown on the right, as in the product photograph; the price-list picture shows it on the left — handing to be confirmed."],
    "W 5050 TSB": ["Thickness as printed in the price list (“± 0.3 + 0.9 mm”); the other hand made models read “± 3.0 + …” — to be confirmed.", DECK],
    "W 6045 TSS": [DECK], "W 6045 TSB": [DECK], "W 8050 TSS": [DECK], "W 8050 TSB": [DECK], "W 8245 TDB": [DECK],
    "W 7546 TSB": ["Glass rinser, control knob and button are shown as in the product photograph; only the 5 Modes Spray is listed in the price list — to be confirmed."],
    "W 7546 TSBN": ["Control panel, buttons and display are shown as in the product photograph; only the 5 Modes Spray is listed in the price list — to be confirmed."],
    "W 8550 TDG": ["The price list states neither the bowl configuration nor the knife holder, soap dispenser and control knob seen in the product photograph — to be confirmed."],
    "W 10050 TSG": ["Width printed as “10050” mm in the price list; read as 1000 mm from the model code and the photograph — to be confirmed."],
}


def tbc(s):
    return f'{E(s)}<span class="tbc">&#8202;†</span>'


def folio(n, title):
    side = "even" if n % 2 == 0 else "odd"
    return f'<footer class="folio {side}"><span>{E(title)}</span><span class="num">{n:02d}</span></footer>'


def img_url(path):
    return (path or "").replace("\\", "/")


def bleed_img(cls, url, pos="center", extra=""):
    return f'<div class="bleed-img {cls}" style="background-image:url(\'{img_url(url)}\');background-position:{pos};{extra}"></div>'


class Volume:
    def __init__(self, kind, data, assets, mode):
        self.kind = kind
        self.mode = mode
        self.A = assets  # dict of image paths
        self.G = kind == "granite"
        self.models = data["granite"] if self.G else data["stainless"]
        self.title = "Granite Kitchen Sink Collection" if self.G else "Stainless Steel Kitchen Sink Collection"
        self.short = "Granite Kitchen Sinks" if self.G else "Stainless Steel Kitchen Sinks"
        self.vol = "01" if self.G else "02"
        self.pages = []
        self.page_of = {}
        self.outline = []   # (title, page, level): the PDF's bookmarks, set by finalize_pdf.py

    # ── facts, phrased ──
    def eyebrow(self, m):
        if self.G:
            return f'{m["installation"]} · {m["bowls"]}'
        return f'{m["range"]} · {m["bowls"] or "Bowls not stated"}'

    def size(self, m):
        if self.G:
            return f'{m["dims"][0]} × {m["dims"][1]} mm <span class="hint">W × D</span>'
        w, d, h = m["dims"]
        if m["dims_unconfirmed"]:
            return f'± <span class="tbc">TBC</span>&#8202;<span class="tbc">†</span> × {d} × {h} mm <span class="hint">W × D × H</span>'
        return f'± {w} × {d} × {h} mm <span class="hint">W × D × H</span>'

    def size_plain(self, m, pm=False):
        if self.G:
            return f'{m["dims"][0]} × {m["dims"][1]}'
        w, d, h = m["dims"]
        return f'{"± " if pm else ""}{"TBC†" if m["dims_unconfirmed"] else w} × {d} × {h}'

    def specs(self, m):
        if self.G:
            cols = " · ".join(c["name"] for c in m["colours"])
            return [("Bowls", E(m["bowls"])), ("Overall size", self.size(m)),
                    ("Material", E(m["material"])), ("Installation", E(m["installation"])), ("Colours", E(cols))]
        rows = [("Range", E(m["range"])), ("Brand", E(m["brand"])),
                ("Bowls", E(m["bowls"]) if m["bowls"] else tbc("Not stated")),
                ("Overall size", self.size(m)), ("Material", E(m["material"])),
                ("Thickness", tbc(m["thickness"]) if m["model"] == "W 5050 TSB" else E(m["thickness"])),
                ("Finish", E(m["finish"])), ("Edge", E(m["edge"]))]
        if m["included"]:
            rows.append(("Included", E(m["included"])))
        return rows

    # ── pages ──
    def add(self, html_, key=None, mark=None, level=0):
        self.pages.append(html_)
        if key:
            self.page_of[key] = len(self.pages)
        if mark:
            self.outline.append((mark, len(self.pages), level))

    def cover(self):
        if self.G:
            title = '<h1 class="cv-title" style="font-size:76pt;letter-spacing:.3em">Granite</h1>'
            facts = ("Six models · Three colours", "Undermount · Top-mount")
        else:
            title = '<h1 class="cv-title" style="font-size:56pt;letter-spacing:.27em;line-height:1.06">Stainless<br>Steel</h1>'
            facts = ("Twenty-five models · Four finishes", "Pressed · Hand Made")
        return f'''<section class="page cover vol-{self.kind}">
  {bleed_img("full-img", self.A["cover"], self.A.get("cover_pos", "center"))}
  <div class="shade-top"></div><div class="shade-bot"></div>
  <div class="trim">
    <div class="cv-bar"><img class="cv-logo" src="{self.A["logo_light"]}" alt="Maju Terus Jaya"><span>Product Catalogue {EDITION}</span></div>
    <div class="cv-block">
      <p class="cv-eyebrow">Volume {self.vol} — Kitchen Sink Collection</p>
      {title}
      <div class="cv-sub"><span>{facts[0]}</span><span>{facts[1]}</span></div>
    </div>
  </div>
</section>'''

    def intro(self, contents):
        if self.G:
            lede = ("Six sinks in granite composite — single and double bowls, for undermount and top-mount installation, "
                    "in Pearl Black, Pure White and Titanium Grey.")
            body = ("Each model has a page of its own: the sink installed in a kitchen, its specifications, and a drawing of its "
                    "overall dimensions and bowl layout. The colours are shown together on page 04.")
            facts = [("6", "Models"), ("3", "Colours"), ("2", "Installations")]
        else:
            lede = ("Twenty-five sinks in two ranges. Pressed, from LUCKY PRO and wellup, in stainless steel 201. "
                    "Hand Made, from wellup, in stainless steel 201 and 304.")
            body = ("Each model has a page of its own: the sink installed in a kitchen, its specifications as listed in the "
                    "Price List 2024, and a drawing of its overall dimensions and bowl layout. The four finishes are shown on page 03.")
            facts = [("25", "Models"), ("2", "Ranges"), ("4", "Finishes")]
        rows = "".join(f'<a href="#p{p}"><span>{E(t)}</span><span>{E(pg)}</span></a>' for t, p, pg in contents)
        fx = "".join(f'<div><div class="n">{n}</div><div class="label t">{E(t)}</div></div>' for n, t in facts)
        st = f' style="background-image:url(\'{self.A["stone"]}\')"' if self.A.get("stone") else ""
        return f'''<section class="page dark intro stone vol-{self.kind}"{st}>
  {bleed_img("in-img", self.A["intro"], self.A.get("intro_pos", "center"))}
  <div class="trim">
    <div class="in-text">
      <div><p class="eyebrow">Volume {self.vol}</p><h2 class="title-l" style="font-size:21pt">{E(self.title)}</h2>
        <p class="lede" style="margin:0 0 5mm">{E(lede)}</p><p class="body" style="margin:0">{E(body)}</p>
        <div class="facts">{fx}</div></div>
      <div><p class="label" style="margin:3.5mm 0 3mm">Contents</p><nav class="contents">{rows}</nav></div>
    </div>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def overview(self, models, title, body, cols, thumb_h, n_label=None):
        cards = []
        for m in models:
            show = self.show(m)
            if self.G:
                dots = "".join(f'<i style="background:{COLOUR_DOT[c["id"]]}"></i>' for c in m["colours"])
                lines = f'<div class="line">{E(self.eyebrow(m))}</div><div class="line">{self.size_plain(m)} mm <span class="dots">{dots}</span></div>'
            else:
                lines = (f'<div class="line">{E(m["bowls"] or "Bowls not stated†")}</div>'
                         f'<div class="line">{self.size_plain(m, pm=True)} mm<br>{E(m["material"].replace("Stainless Steel", "Stainless"))} · {E(m["finish"])}</div>')
            cards.append(f'''<a class="card" href="#{show["anchor"]}"><div class="ph" style="height:{thumb_h}mm;background-image:url('{self.A["thumbs"].get(show["recipe"], "")}')"></div>
      <div class="meta"><span class="code">{E(m["model"])}</span><span class="pg">{{PAGE:{m["model"]}}}</span></div>{lines}</a>''')
        return f'''<section class="page overview vol-{self.kind}">
  <div class="trim">
    <div class="ov-head"><div><p class="eyebrow">{E(n_label or "The collection")}</p><h2 class="title-l" style="margin-top:3.5mm">{E(title)}</h2></div>
      <p class="body">{E(body)}</p></div>
    <div class="grid" style="grid-template-columns:repeat({cols},1fr)">{"".join(cards)}</div>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def show(self, m):
        if self.G:
            s = dict(GRANITE_SHOW[m["model"]])
        else:
            s = dict(recipe=m["model"].lower().replace(" ", ""), setting=STEEL_SETTING[m["model"]])
        s["anchor"] = "m-" + m["model"].lower().replace(" ", "-")
        return s

    def colours_page(self):
        bands = []
        for cid in ("pearl", "pure", "titan"):
            avail = [m["model"] for m in self.models if any(c["id"] == cid for c in m["colours"])]
            missing = [m["model"] for m in self.models if m["model"] not in avail]
            av = "All six models" if not missing else f'{len(avail)} models — not available for {", ".join(missing)}'
            bands.append(f'''<div class="sw"><div class="chip" style="height:84mm;background-image:url('{self.A["colour_detail"].get(cid, "")}')"></div>
      <div class="prod" style="height:40mm;background-image:url('{self.A["colour_prod"][cid]}')"></div>
      <h3>{COLOUR_NAME[cid]}</h3><div class="avail"><b>Available</b>{T(av)}<br><span style="color:var(--mute)">{series(avail)}</span></div></div>''')
        return f'''<section class="page swatches vol-{self.kind}">
  <div class="trim">
    <div class="sw-head"><p class="eyebrow">Colours</p><h2 class="title-l" style="margin-top:3.5mm">Three Colours</h2>
      <p class="lede">Granite composite in Pearl Black, Pure White and Titanium Grey — each seen in one of the kitchens in this volume, and below it as photographed, on the <span class="nw">GSU 7545</span>.</p></div>
    <div class="sw-grid" style="grid-template-columns:repeat(3,1fr)">{"".join(bands)}</div>
    <p class="body" style="position:absolute;left:15mm;bottom:17mm;margin:0;font-size:6.6pt;color:var(--mute)">Colours in print may differ slightly from the products.</p>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def finishes_page(self):
        order = ["Mat Polished", "Electroplate", "Satin", "Nano Black"]
        cells = []
        for f in order:
            ms = [m for m in self.models if m["finish"] == f]
            rng = sorted({m["range"] for m in ms})
            grades = sorted({m["grade"] for m in ms})
            cells.append(f'''<div class="sw"><div class="chip" style="height:58mm;background-image:url('{self.A["finish_detail"].get(f, "")}')"></div>
      <div style="display:grid;grid-template-columns:1fr 24mm;column-gap:4mm;align-items:start">
        <div><h3>{E(f)}</h3><div class="avail"><b>Range</b>{E(" and ".join(rng))} · stainless steel {E(" and ".join(grades))}</div>
          <div class="avail" style="margin-top:2.2mm"><b>{len(ms)} models</b>{series(m["model"] for m in ms)}</div></div>
        <div class="prod" style="height:24mm;margin-top:4.5mm;background-size:cover;background-image:url('{self.A["finish"][f]}')"></div></div></div>''')
        return f'''<section class="page swatches vol-{self.kind}">
  <div class="trim">
    <div class="sw-head"><p class="eyebrow">Finishes</p><h2 class="title-l" style="margin-top:3.5mm">Four Finishes</h2>
      <p class="lede">Each model is made in one finish, as listed in the price list — each seen here in one of the kitchens in this volume, with a close view of the product photograph beside it.</p></div>
    <div class="sw-grid" style="grid-template-columns:1fr 1fr;top:60mm;bottom:auto;row-gap:9mm">{"".join(cells)}</div>
    <p class="body" style="position:absolute;left:15mm;bottom:17mm;margin:0;font-size:6.6pt;color:var(--mute)">Finishes in print may differ slightly from the products.</p>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def opener(self, rng, models, img, pos="center"):
        if rng == "Pressed":
            text = ("Pressed sinks in stainless steel 201, each with an inset edge: single and double bowls, with and without "
                    "drainboards. From LUCKY PRO and wellup, in Mat Polished and Electroplate.")
        else:
            text = ("Hand made sinks in stainless steel 201 and 304, each with a flat edge: single and double bowls, four of them "
                    "supplied with a 5 Modes Spray or tempered glass. From wellup, in Satin and Nano Black.")
        return f'''<section class="page opener on-image vol-{self.kind}">
  {bleed_img("op-img", img, pos)}
  <div class="op-shade"></div>
  <div class="trim">
    <div class="op-text"><p class="eyebrow">The range · {len(models)} models</p><h2 class="op-title">{E(rng)}</h2>
      <div class="op-body"><p>{E(text)}</p><div class="op-models">{series(m["model"] for m in models)}</div></div></div>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def feature(self, m):
        show = self.show(m)
        n = len(self.pages) + 1
        if self.G:
            desc = f'Granite composite kitchen sink · shown in {COLOUR_NAME[show["colour"]]}'
            chips = "".join(
                f'<div class="chip{" on" if c["id"] == show["colour"] else ""}"><div class="img" style="background-image:url(\'{self.A["products"][c["photo"]]}\')"></div><div class="nm">{E(c["name"])}</div></div>'
                for c in m["colours"])
        else:
            desc = f'{m["brand"]} · {m["range"]} kitchen sink'
            chips = (f'<div class="chip on"><div class="img" style="background-image:url(\'{self.A["products"][m["photo"]]}\')"></div>'
                     f'<div class="nm">{E(m["finish"])}</div></div>')
        specs = "".join(f'<div><dt>{E(k)}</dt><dd>{v}</dd></div>' for k, v in self.specs(m))
        wl = "TBC" if (not self.G and m["dims_unconfirmed"]) else None
        svg, _ = drawings.svg("granite" if self.G else "steel", m["model"], box_w=86.0, box_h=68.0 if not self.G else 54.0, width_label=wl)
        cap = ("Plan · overall dimensions in mm · bowl layout for reference" if self.G
               else "Plan and front view · dimensions in mm (approximate) · bowl layout for reference")
        notes = NOTES.get(m["model"], [])
        nt = "".join(f'<span>† {T(t)}</span>' for t in notes)
        return f'''<section class="page feature vol-{self.kind}" id="{show["anchor"]}">
  {bleed_img("hero", self.A["heroes"].get(show["recipe"], ""), self.A["hero_pos"].get(show["recipe"], "center"))}
  <div class="trim">
    <div class="hero-cap">{E(show["setting"])}</div>
    <div class="panel">
      <div class="ph-row"><div><p class="eyebrow">{E(self.eyebrow(m))}</p><h2 class="code">{E(m["model"])}</h2><p class="desc">{E(desc)}</p></div>
        <div class="chips">{chips}</div></div>
      <div class="cols"><dl class="specs">{specs}</dl><figure class="draw">{svg}<figcaption>{E(cap)}</figcaption></figure></div>
    </div>
    {f'<p class="notes">{nt}</p>' if nt else ''}
    {folio(n, self.title)}
  </div>
</section>'''

    def index_page(self):
        rows = []
        if self.G:
            head = '<tr><th>Model</th><th>Bowls</th><th>Installation</th><th>Size W × D, mm</th><th>Colours</th><th class="r">Page</th></tr>'
            for m in self.models:
                cols = ", ".join(c["name"] for c in m["colours"])
                rows.append(f'<tr><td class="m"><a href="#{self.show(m)["anchor"]}" style="color:inherit;text-decoration:none">{E(m["model"])}</a></td><td>{E(m["bowls"])}</td><td>{E(m["installation"])}</td>'
                            f'<td>{self.size_plain(m)}</td><td>{E(cols)}</td><td class="r">{{PAGE:{m["model"]}}}</td></tr>')
        else:
            head = '<tr><th>Model</th><th>Brand</th><th>Bowls</th><th>Size W × D × H, mm (±)</th><th>Steel</th><th>Finish</th><th class="r">Page</th></tr>'
            for rng in ("Pressed", "Hand Made"):
                rows.append(f'<tr class="sec"><td colspan="7">{rng}</td></tr>')
                for m in [x for x in self.models if x["range"] == rng]:
                    rows.append(f'<tr><td class="m"><a href="#{self.show(m)["anchor"]}" style="color:inherit;text-decoration:none">{E(m["model"])}</a></td><td>{E(m["brand"])}</td><td>{E(m["bowls"] or "Not stated†")}</td>'
                                f'<td>{self.size_plain(m)}</td><td>{E(m["grade"])}</td><td>{E(m["finish"])}</td><td class="r">{{PAGE:{m["model"]}}}</td></tr>')
        notes = self.general_notes()
        half = (len(notes) + 1) // 2
        nhtml = "".join(f"<p>{T(t)}</p>" for t in notes[:half])
        nhtml2 = "".join(f"<p>{T(t)}</p>" for t in notes[half:])
        notes_block = ("" if not self.G else
                       f'<div class="ix-notes" style="top:92mm;bottom:auto"><div><h4 class="label" style="color:var(--ink)">About this catalogue</h4>{nhtml}</div><div><div class="label" style="margin:0 0 2.5mm">&nbsp;</div>{nhtml2}</div></div>')
        strip = (bleed_img("ix-strip", self.A["strip"], "center") if self.G and self.A.get("strip") else "")
        return f'''<section class="page index vol-{self.kind}{' with-strip' if self.G else ''}">
  {strip if self.G else ''}
  <div class="trim">
    <div class="ix-head"><p class="eyebrow">Index</p><h2 class="title-m" style="margin-top:3mm">All Models</h2></div>
    <table>{head}{"".join(rows)}</table>
    {notes_block}
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def general_notes(self):
        common = ["Images are visualisations made from the supplied product photographs and listed dimensions. The kitchens, taps and accessories in them are styling and are not included unless listed in the specifications.",
                  "Colours and finishes in print may differ slightly from the products.",
                  "† Marks information awaiting confirmation from the supplier."]
        if self.G:
            return ["Dimensions are width × depth, in millimetres, as listed. Bowl depth and overall height are not given in the source.",
                    "The drawings show the listed overall dimensions; the bowl layout is drawn from the product photographs, for reference.",
                    "GST 7546 is listed in Pearl Black and Pure White only."] + common
        return ["Specifications are those of the Price List 2024 (14 August 2024). Sizes are approximate (±), width × depth × height, in millimetres.",
                "The price list gives each model's edge (Inset Edge for Pressed, Flat Edge for Hand Made) but not its installation type. The images show the hand made models top-mounted or undermounted following the model code (T…, U…) — to be confirmed.",
                "The drawings show the listed overall dimensions; the bowl layout is drawn from the product photographs, for reference."] + common

    def notes_page(self):
        notes = self.general_notes()
        half = (len(notes) + 1) // 2
        mat = "".join(f'<div><b>{E(k)}</b><span>{T(v)}</span></div>' for k, v in [
            ("Pressed", "Stainless steel 201 · Inset Edge · Mat Polished (LUCKY PRO, WL 03) or Electroplate (WL 05 A – WL 18)"),
            ("Hand Made", "Stainless steel 201 or 304, as listed per model · Flat Edge · Satin or Nano Black"),
            ("Included", "5 Modes Spray — W 7546 TSB, W 7546 TSBN · 2 Tempered Glasses — W 8550 TDG · Tempered Glasses Wing — W 10050 TSG"),
            ("Source", "Price List 2024, 14 August 2024")])
        strip = bleed_img("ix-strip", self.A["strip"], "center") if self.A.get("strip") else ""
        return f'''<section class="page notes-page with-strip vol-{self.kind}">
  {strip}
  <div class="trim"><div class="nt"><p class="eyebrow">Notes</p><h2 class="title-m" style="margin-top:3mm">About this catalogue</h2>
    <div class="nt-cols"><div>{"".join(f"<p>{T(t)}</p>" for t in notes[:half])}</div><div>{"".join(f"<p>{T(t)}</p>" for t in notes[half:])}</div></div>
    <p class="label" style="margin-top:12mm">At a glance</p><div class="mat">{mat}</div></div>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def image_page(self, img, pos="center"):
        return f'''<section class="page on-image vol-{self.kind}">{bleed_img("full-img", img, pos)}
  <div class="trim">{folio(len(self.pages) + 1, self.title)}</div></section>'''

    def back(self):
        st = f' style="background-image:url(\'{self.A["stone"]}\')"' if self.A.get("stone") else ""
        return f'''<section class="page dark back stone vol-{self.kind}"{st}>
  <div class="trim"><div class="bk-center"><img class="bk-mark" src="{self.A["mark_light"]}" alt="">
    <img class="bk-logo" src="{self.A["logo_light"]}" alt="Maju Terus Jaya">
    <div class="bk-line">{E(self.title)}<br>Volume {self.vol} · {EDITION}</div></div>
    <div class="bk-foot">Specifications and images may change without notice. Colours and finishes in print may differ slightly from the products.</div>
  </div>
</section>'''

    # ── the whole volume ──
    def build(self):
        if self.G:
            self.add(self.cover(), mark="Cover")
            contents = [("The collection", 3, "03"), ("Colours", 4, "04"), ("Models", 5, "05 – 10"), ("Index", 11, "11")]
            self.add(self.intro(contents), mark="Introduction and contents")
            self.add(self.overview(self.models, "Six Models", "Each model is shown on its own page, installed in a kitchen of its own, with its specifications and drawing.", 2, 52),
                     mark="The collection")
            self.add(self.colours_page(), mark="Colours")
            self.outline.append(("Models", len(self.pages) + 1, 0))
            for m in self.models:
                self.add(self.feature(m), key=m["model"], mark=m["model"], level=1)
            self.add(self.index_page(), mark="Index and notes")
            self.add(self.back(), mark="Back cover")
        else:
            pressed = [m for m in self.models if m["range"] == "Pressed"]
            hand = [m for m in self.models if m["range"] == "Hand Made"]
            self.add(self.cover(), mark="Cover")
            contents = [("Finishes", 3, "03"), ("The collection", 4, "04 – 05"), ("Pressed", 6, "06 – 17"), ("Hand Made", 18, "18 – 32"), ("Index", 33, "33"), ("Notes", 34, "34")]
            self.add(self.intro(contents), mark="Introduction and contents")
            self.add(self.finishes_page(), mark="Finishes")
            self.add(self.overview(pressed, "Pressed", "Eleven models in stainless steel 201, from LUCKY PRO and wellup.", 4, 44, n_label="The collection · 1 of 2"),
                     mark="The collection: Pressed")
            self.add(self.overview(hand, "Hand Made", "Fourteen models in stainless steel 201 and 304, from wellup.", 4, 28, n_label="The collection · 2 of 2"),
                     mark="The collection: Hand Made")
            self.add(self.opener("Pressed", pressed, self.A["opener_pressed"], self.A.get("opener_pressed_pos", "center")), mark="Pressed range")
            for m in pressed:
                self.add(self.feature(m), key=m["model"], mark=m["model"], level=1)
            self.add(self.opener("Hand Made", hand, self.A["opener_hand"], self.A.get("opener_hand_pos", "center")), mark="Hand Made range")
            for m in hand:
                self.add(self.feature(m), key=m["model"], mark=m["model"], level=1)
            self.add(self.index_page(), mark="Index")
            self.add(self.notes_page(), mark="Notes")
            self.add(self.image_page(self.A["closing"], self.A.get("closing_pos", "center")))
            self.add(self.back(), mark="Back cover")
        out = "\n".join(self.pages)
        for model, p in self.page_of.items():
            out = out.replace("{PAGE:" + model + "}", f"{p:02d}")
        return out


def page_css(mode):
    bleed = 3 if mode == "print" else 0
    return (f"@page {{ size: {210 + 2 * bleed}mm {297 + 2 * bleed}mm; margin: 0; }}\n"
            f":root {{ --bleed: {bleed}mm; --pw: {210 + 2 * bleed}mm; --ph: {297 + 2 * bleed}mm; }}\n")


def document(vol, body, mode):
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Maju Terus Jaya — {E(vol.title)} — Volume {vol.vol}</title>
<link rel="stylesheet" href="fonts.css"><link rel="stylesheet" href="catalogue.css">
<style>{page_css(mode)}</style></head>
<body class="vol-{vol.kind}">
{body}
</body></html>'''


def main():
    data = json.load(open(sys.argv[1]))
    out_dir = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "screen"
    assets = json.load(open(os.path.join(out_dir, f"assets-{mode}.json")))
    for kind in ("granite", "stainless"):
        vol = Volume(kind, data, assets[kind], mode)
        body = vol.build()
        name = f"{kind}-{mode}.html"
        open(os.path.join(out_dir, name), "w").write(document(vol, body, mode))
        json.dump([dict(title=t, page=p, level=lv) for t, p, lv in vol.outline], open(os.path.join(out_dir, f"{kind}-{mode}.outline.json"), "w"), indent=1)
        print(name, len(vol.pages), "pages")


if __name__ == "__main__":
    main()

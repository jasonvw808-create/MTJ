"""Build the two catalogue volumes as HTML (one page per A4 sheet) from the verified product data.

    python build.py <data.json> <out_dir> [print|screen] [en|id]

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
import i18n  # noqa: E402

E = html.escape
CODE = re.compile(r'\b(?:LPS|WL|GDU|GST|GSU|W) \d{2,5}(?: [A-Z]{1,4})?\b')


def T(s):
    """Escaped text in which no model code breaks across a line."""
    return CODE.sub(lambda m: f'<span class="nw">{m.group(0)}</span>', E(s))


def keep(s):
    """A title in which no hyphenated word (Top-mount) breaks at its hyphen, nor a two-word term (tata letak, layout)."""
    s = re.sub(r'(?i)\b(tata) (letak)\b', '\\1&nbsp;\\2', s)
    return re.sub(r'(\S+-\S+)', r'<span class="nw">\1</span>', s)


def _glyph(body):
    return f'<svg viewBox="0 0 9 4" width="9mm" height="4mm" class="lg-g">{body}</svg>'


# the marks of the drawings, drawn as they are drawn there (drawings.STYLE), for the key on the sizes pages
_ST = drawings.STYLE
GLYPH = {
    "outline": _glyph(f'<line x1="0.3" y1="2" x2="8.7" y2="2" {_ST["outline"]}/>'),
    "band": _glyph(f'<line x1="0.3" y1="2" x2="8.7" y2="2" {_ST["soft"]}/>'),
    "bowl": _glyph(f'<line x1="0.3" y1="2" x2="8.7" y2="2" {_ST["line"]}/>'),
    "floor": _glyph(f'<line x1="0.3" y1="2" x2="8.7" y2="2" {_ST["faint"]}/>'),
    "ledge": _glyph(f'<line x1="0.3" y1="2" x2="8.7" y2="2" {_ST["soft"]}/>'),
    "step": _glyph(f'<line x1="0.3" y1="2" x2="8.7" y2="2" {_ST["soft"]}/>'),
    "drain_g": _glyph(f'<circle cx="4.5" cy="2" r="1.5" {_ST["line"]}/><circle cx="4.5" cy="2" r="0.75" {_ST["soft"]}/>'),
    "drain_s": _glyph(f'<circle cx="4.5" cy="2" r="1.5" {_ST["line"]}/>'),
    "hole": _glyph(f'<circle cx="4.5" cy="2" r="0.9" {_ST["line"]}/>'),
    "tapring": _glyph(f'<circle cx="4.5" cy="2" r="1.2" {_ST["line"]}/><circle cx="4.5" cy="2" r="0.72" {_ST["soft"]}/>'),
    "relief": _glyph(f'<path d="M0.5 0.9h8M0.5 2h8M0.5 3.1h8" {_ST["relief"]}/>'),
    "grooves": _glyph(f'<path d="M0.5 0.9h8M0.5 2h8M0.5 3.1h8" {_ST["relief"]}/>'),
    "glass": _glyph(f'<rect x="1" y="0.6" width="7" height="2.8" rx="0.3" {_ST["glass"]}/>'),
}
GLYPH_LABEL = {"outline": "Outline · overall size", "band": "Inset Edge", "bowl": "Bowl", "floor": "Bowl floor, for reference",
               "ledge": "Ledge", "step": "Ledge, floor step", "drain_g": "Drain", "drain_s": "Drain", "hole": "Tap hole", "tapring": "Tap hole",
               "relief": "Drainboard", "grooves": "Glass wing grooves", "glass": "Glass cover"}


def drawing_marks(models, granite):
    """Which marks the drawings of these models use, in the order the key lists them."""
    used = ["outline"]
    if granite:
        gs = [drawings.GRANITE[m["model"]] for m in models]
        soft = "step" if any(g.get("floorStep") for g in gs) else "ledge"
        used += ["bowl", "floor"] + ([soft] if any(g.get("ledge") or g.get("floorStep") for g in gs) else []) + ["drain_g"]
        used += ["hole"] if any(g.get("holes") for g in gs) else []
        return used
    ss = [drawings.STEEL[m["model"]] for m in models]
    pressed = [x for x in ss if x["family"] == "pressed"]
    hand = [x for x in ss if x["family"] != "pressed"]
    if pressed:
        used += ["band", "bowl"]
        used += ["floor"] if any("cpoly" not in b["shape"] for x in pressed for b in x["bowls"]) else []
        used += ["relief"] if any(x.get("features") for x in pressed) else []
        used += ["drain_s"]
    if hand:
        used += [k for k in ("bowl",) if k not in used]
        used += ["ledge"] if any(b.get("ledges") for x in hand for b in x.get("bowls", [])) else []
        used += ["drain_s"] if "drain_s" not in used else []
        used += ["grooves"] if any(x.get("top") == "glass" for x in hand) else []
        used += ["glass"] if any(f.get("kind") == "pane" for x in hand for f in x.get("fittings", [])) else []
        used += ["tapring"] if any(f.get("kind") == "tapring" for x in hand for f in x.get("fittings", [])) else []
    return used


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
    "W 8550 TDG": ["The price list states neither the bowl configuration nor the soap dispenser and control knob seen in the product photograph — to be confirmed."],
    "W 10050 TSG": ["Width printed as “10050” mm in the price list; read as 1000 mm from the model code and the photograph — to be confirmed."],
}


# glance-row icons (24 x 16 user units, stroked in the ink colour by the stylesheet)
ICON = {
    "Undermount": '<svg viewBox="0 0 24 16" class="ico"><path d="M1 5h7M16 5h7" stroke-width="1.6"/><path d="M8 6.2v6.6q0 1.2 1.2 1.2h5.6q1.2 0 1.2-1.2V6.2" fill="none"/><path d="M6.8 6.2h10.4" stroke-width=".7"/></svg>',
    "Top-mount": '<svg viewBox="0 0 24 16" class="ico"><path d="M1 7h6M17 7h6" stroke-width="1.6"/><path d="M5.6 5.4h3v8.4q0 .8.8.8h5.2q.8 0 .8-.8V5.4h3" fill="none"/></svg>',
    "Inset Edge": '<svg viewBox="0 0 24 16" class="ico"><path d="M3 6.5q0-1.8 1.8-1.8h3.4q1 0 1 1v7.6q0 .9.9.9h3.8q.9 0 .9-.9V5.7q0-1 1-1h3.4q1.8 0 1.8 1.8" fill="none"/></svg>',
    "Flat Edge": '<svg viewBox="0 0 24 16" class="ico"><path d="M2 4.7h7v9.4h6V4.7h7" fill="none"/></svg>',
    "size": '<svg viewBox="0 0 24 16" class="ico"><path d="M3 4.5h18M3 2.8v3.4M21 2.8v3.4" fill="none"/><rect x="3" y="8.2" width="18" height="6" rx="1" fill="none"/></svg>',
    "included": '<svg viewBox="0 0 24 16" class="ico"><rect x="6" y="2" width="12" height="12" rx="2" fill="none"/><path d="M12 5.2v5.6M9.2 8h5.6" fill="none"/></svg>',
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
    def __init__(self, kind, data, assets, mode, lang="en"):
        self.kind = kind
        self.mode = mode
        self.lang = lang
        self.A = assets  # dict of image paths
        self.G = kind == "granite"
        self.models = data["granite"] if self.G else data["stainless"]
        self.title = self.t("Granite Kitchen Sink Collection" if self.G else "Stainless Steel Kitchen Sink Collection")
        self.short = "Granite Kitchen Sinks" if self.G else "Stainless Steel Kitchen Sinks"
        self.vol = "01" if self.G else "02"
        self.pages = []
        self.page_of = {}
        self.outline = []   # (title, page, level): the PDF's bookmarks, set by finalize_pdf.py

    # ── words ──
    def t(self, s):
        """The volume's language: the English as written, or its Indonesian from i18n.ID, which must have it."""
        if self.lang == "en" or s is None:
            return s
        if s not in i18n.ID:
            raise KeyError("no Indonesian for: " + s)
        return i18n.ID[s]

    def f(self, key, **kw):
        """A sentence with numbers or names in it, in the volume's language."""
        return i18n.TEMPLATES[self.lang][key].format(**kw)

    # ── facts, phrased ──
    def eyebrow(self, m):
        if self.G:
            return f'{self.t(m["installation"])} · {self.t(m["bowls"])}'
        return f'{self.t(m["range"])} · {self.t(m["bowls"] or "Bowls not stated")}'

    def size(self, m):
        if self.G:
            return f'{m["dims"][0]} × {m["dims"][1]} mm <span class="hint">{self.f("hint_wd")}</span>'
        w, d, h = m["dims"]
        if m["dims_unconfirmed"]:
            return (f'± <span class="tbc">{self.f("unconfirmed")}</span>&#8202;<span class="tbc">†</span> × {d} × {h} mm '
                    f'<span class="hint">{self.f("hint_wdh")}</span>')
        return f'± {w} × {d} × {h} mm <span class="hint">{self.f("hint_wdh")}</span>'

    def size_plain(self, m, pm=False):
        if self.G:
            return f'{m["dims"][0]} × {m["dims"][1]}'
        w, d, h = m["dims"]
        return f'{"± " if pm else ""}{self.f("unconfirmed") + "†" if m["dims_unconfirmed"] else w} × {d} × {h}'

    def specs(self, m):
        t = self.t
        if self.G:
            cols = " · ".join(t(c["name"]) for c in m["colours"])
            return [(t("Bowls"), E(t(m["bowls"]))), (t("Overall size"), self.size(m)),
                    (t("Material"), E(t(m["material"]))), (t("Installation"), E(t(m["installation"]))), (t("Colours"), E(cols))]
        rows = [(t("Range"), E(t(m["range"]))), (t("Brand"), E(m["brand"])),
                (t("Bowls"), E(t(m["bowls"])) if m["bowls"] else tbc(t("Not stated"))),
                (t("Overall size"), self.size(m)), (t("Material"), E(m["material"])),
                (t("Thickness"), tbc(m["thickness"]) if m["model"] == "W 5050 TSB" else E(m["thickness"])),
                (t("Finish"), E(m["finish"])), (t("Edge"), E(m["edge"]))]
        if m["included"]:
            rows.append((t("Included"), E(m["included"])))
        return rows

    # ── pages ──
    def add(self, html_, key=None, mark=None, level=0):
        self.pages.append(html_)
        if key:
            self.page_of[key] = len(self.pages)
        if mark:
            self.outline.append((mark if level else self.t(mark), len(self.pages), level))

    def cover(self):
        if self.G:
            title = f'<h1 class="cv-title" style="font-size:76pt;letter-spacing:.3em">{self.t("Granite")}</h1>'
            facts = (self.t("Six models · Three colours"), self.t("Undermount · Top-mount"))
        else:
            title = '<h1 class="cv-title" style="font-size:56pt;letter-spacing:.27em;line-height:1.06">Stainless<br>Steel</h1>'
            facts = (self.t("Twenty-five models · Four finishes"), self.t("Pressed · Hand Made"))
        return f'''<section class="page cover vol-{self.kind}">
  {bleed_img("full-img", self.A["cover"], self.A.get("cover_pos", "center"))}
  <div class="shade-top"></div><div class="shade-bot"></div>
  <div class="trim">
    <div class="cv-bar"><img class="cv-logo" src="{self.A["logo_light"]}" alt="Maju Terus Jaya"><span>{self.f("catalogue", edition=EDITION)}</span></div>
    <div class="cv-block">
      <p class="cv-eyebrow">{self.f("volume_of", vol=self.vol)}</p>
      {title}
      <div class="cv-sub"><span>{facts[0]}</span><span>{facts[1]}</span></div>
    </div>
  </div>
</section>'''

    def intro(self, contents, n=2):
        if self.G:
            lede = ("Six sinks in granite composite — single and double bowls, for undermount and top-mount installation, "
                    "in Pearl Black, Pure White and Titanium Grey.")
            body = ("Each model has a page of its own: the sink installed in a kitchen, its specifications, and a drawing of its "
                    "overall dimensions and bowl layout. Sizes, layouts and the two installations are compared at the front.")
            facts = [("6", "Models"), ("3", "Colours"), ("2", "Installations")]
        else:
            lede = ("Twenty-five sinks in two ranges. Pressed, from LUCKY PRO and wellup, in stainless steel 201. "
                    "Hand Made, from wellup, in stainless steel 201 and 304.")
            body = ("Each model has a page of its own: the sink installed in a kitchen, its specifications as listed in the "
                    "Price List 2024, and a drawing of its overall dimensions and bowl layout. The ranges, finishes and sizes are compared at the front.")
            facts = [("25", "Models"), ("2", "Ranges"), ("4", "Finishes")]
        lede, body = self.t(lede), self.t(body)
        rows = "".join(f'<a href="#p{p}"><span>{E(self.t(t))}</span><span>{E(pg)}</span></a>' for t, p, pg in contents)
        folio_n = n
        fx = "".join(f'<div><div class="n">{n}</div><div class="label t">{E(self.t(t))}</div></div>' for n, t in facts)
        st = f' style="background-image:url(\'{self.A["stone"]}\')"' if self.A.get("stone") else ""
        return f'''<section class="page dark intro stone vol-{self.kind}"{st}>
  {bleed_img("in-img", self.A["intro"], self.A.get("intro_pos", "center"))}
  <div class="trim">
    <div class="in-text">
      <div><p class="eyebrow">{self.f("volume", vol=self.vol)}</p><h2 class="title-l" style="font-size:21pt">{E(self.title)}</h2>
        <p class="lede" style="margin:0 0 5mm">{E(lede)}</p><p class="body" style="margin:0">{E(body)}</p>
        <div class="facts">{fx}</div></div>
      <div><p class="label" style="margin:3.5mm 0 3mm">{self.t("Contents")}</p><nav class="contents">{rows}</nav></div>
    </div>
    {folio(folio_n, self.title)}
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
                lines = (f'<div class="line">{E(self.t(m["bowls"] or "Bowls not stated†"))}</div>'
                         f'<div class="line">{self.size_plain(m, pm=True)} mm<br>{E(m["material"].replace("Stainless Steel", "Stainless"))} · {E(m["finish"])}</div>')
            cards.append(f'''<a class="card" href="#{show["anchor"]}"><div class="ph" style="height:{thumb_h}mm;background-image:url('{self.A["thumbs"].get(show["recipe"], "")}')"></div>
      <div class="meta"><span class="code">{E(m["model"])}</span><span class="pg">{{PAGE:{m["model"]}}}</span></div>{lines}</a>''')
        return f'''<section class="page overview vol-{self.kind}">
  <div class="trim">
    <div class="ov-head"><div><p class="eyebrow">{E(self.t(n_label or "The collection"))}</p><h2 class="title-l" style="margin-top:3.5mm">{E(self.t(title))}</h2></div>
      <p class="body">{E(self.t(body))}</p></div>
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
            av = self.t("All six models") if not missing else self.f("n_models_missing", n=len(avail), models=", ".join(missing))
            bands.append(f'''<div class="sw"><div class="chip" style="height:84mm;background-image:url('{self.A["colour_detail"].get(cid, "")}')"></div>
      <div class="prod" style="height:40mm;background-image:url('{self.A["colour_prod"][cid]}')"></div>
      <h3>{E(self.t(COLOUR_NAME[cid]))}</h3><div class="avail"><b>{self.t("Available")}</b>{T(av)}<br><span style="color:var(--mute)">{series(avail)}</span></div></div>''')
        return f'''<section class="page swatches vol-{self.kind}">
  <div class="trim">
    <div class="sw-head"><p class="eyebrow">{self.t("Colours")}</p><h2 class="title-l" style="margin-top:3.5mm">{self.t("Three Colours")}</h2>
      <p class="lede">{T(self.t("Granite composite in Pearl Black, Pure White and Titanium Grey — each seen in one of the kitchens in this volume, and below it as photographed, on the GSU 7545."))}</p></div>
    <div class="sw-grid" style="grid-template-columns:repeat(3,1fr)">{"".join(bands)}</div>
    <p class="body" style="position:absolute;left:15mm;bottom:17mm;margin:0;font-size:6.6pt;color:var(--mute)">{self.t("Colours in print may differ slightly from the products.")}</p>
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
        <div><h3>{E(f)}</h3><div class="avail"><b>{self.t("Range")}</b>{E(self.f("range_steel", ranges=self.f("and").join(self.t(r) for r in rng), grades=self.f("and").join(grades)))}</div>
          <div class="avail" style="margin-top:2.2mm"><b>{self.f("n_models", n=len(ms))}</b>{series(m["model"] for m in ms)}</div></div>
        <div class="prod" style="height:24mm;margin-top:4.5mm;background-size:cover;background-image:url('{self.A["finish"][f]}')"></div></div></div>''')
        return f'''<section class="page swatches vol-{self.kind}">
  <div class="trim">
    <div class="sw-head"><p class="eyebrow">{self.t("Finishes")}</p><h2 class="title-l" style="margin-top:3.5mm">{self.t("Four Finishes")}</h2>
      <p class="lede">{E(self.t("Each model is made in one finish, as listed in the price list — each seen here in one of the kitchens in this volume, with a close view of the product photograph beside it."))}</p></div>
    <div class="sw-grid" style="grid-template-columns:1fr 1fr;top:60mm;bottom:auto;row-gap:9mm">{"".join(cells)}</div>
    <p class="body" style="position:absolute;left:15mm;bottom:17mm;margin:0;font-size:6.6pt;color:var(--mute)">{self.t("Finishes in print may differ slightly from the products.")}</p>
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
        text = self.t(text)
        return f'''<section class="page opener on-image vol-{self.kind}">
  {bleed_img("op-img", img, pos)}
  <div class="op-shade"></div>
  <div class="trim">
    <div class="op-text"><p class="eyebrow">{self.f("the_range", n=len(models))}</p><h2 class="op-title">{E(self.t(rng))}</h2>
      <div class="op-body"><p>{E(text)}</p><div class="op-models">{series(m["model"] for m in models)}</div></div></div>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def feature(self, m):
        show = self.show(m)
        n = len(self.pages) + 1
        if self.G:
            desc = self.f("desc_granite", colour=self.t(COLOUR_NAME[show["colour"]]))
            chips = "".join(
                f'<div class="chip{" on" if c["id"] == show["colour"] else ""}"><div class="img" style="background-image:url(\'{self.A["products"][c["photo"]]}\')"></div><div class="nm">{E(self.t(c["name"]))}</div></div>'
                for c in m["colours"])
        else:
            desc = self.f("desc_steel", brand=m["brand"], range=m["range"])
            chips = (f'<div class="chip on"><div class="img" style="background-image:url(\'{self.A["products"][m["photo"]]}\')"></div>'
                     f'<div class="nm">{E(m["finish"])}</div></div>')
        specs = "".join(f'<div><dt>{E(k)}</dt><dd>{v}</dd></div>' for k, v in self.specs(m))
        glance = self.glance(m)
        wl = self.f("unconfirmed") if (not self.G and m["dims_unconfirmed"]) else None
        svg, _ = drawings.svg("granite" if self.G else "steel", m["model"], box_w=86.0, box_h=68.0 if not self.G else 54.0, width_label=wl)
        cap = self.t("Plan · overall dimensions in mm · bowl layout for reference" if self.G
                     else "Plan and front view · dimensions in mm (approximate) · bowl layout for reference")
        notes = [self.t(x) for x in NOTES.get(m["model"], [])]
        nt = "".join(f'<span>† {T(t)}</span>' for t in notes)
        return f'''<section class="page feature vol-{self.kind}" id="{show["anchor"]}">
  {bleed_img("hero", self.A["heroes"].get(show["recipe"], ""), self.A["hero_pos"].get(show["recipe"], "center"))}
  <div class="trim">
    <div class="hero-cap">{E(self.t(show["setting"]))}</div>
    <div class="panel">
      <div class="ph-row"><div><p class="eyebrow">{E(self.eyebrow(m))}</p><h2 class="code">{E(m["model"])}</h2><p class="desc">{E(desc)}</p></div>
        <div class="chips">{chips}</div></div>
      {glance}
      <div class="cols"><dl class="specs">{specs}</dl><figure class="draw">{svg}<figcaption>{E(cap)}</figcaption></figure></div>
    </div>
    {f'<p class="notes">{nt}</p>' if nt else ''}
    {folio(n, self.title)}
  </div>
</section>'''

    # ── at a glance: a model's layout, how it fits, its size, its colours or finish ──
    def layout_icon(self, m, h=7.4):
        W, D = m["dims"][0], m["dims"][1]
        sc = (h - 0.6) / D
        svg, _ = drawings.svg("granite" if self.G else "steel", m["model"], box_w=W * sc + 0.6, box_h=h, plan_only=True, dims=False, scale=sc)
        return svg

    def glance(self, m):
        t = self.t
        cells = [(self.layout_icon(m), t("Layout"), E(t(m["bowls"])) if m["bowls"] else tbc(t("Not stated")))]
        if self.G:
            cells.append((ICON[m["installation"]], t("Installation"), E(t(m["installation"]))))
            cells.append((ICON["size"], t("Overall size"), f'{m["dims"][0]} × {m["dims"][1]} mm'))
            dots = "".join(f'<i style="background:{COLOUR_DOT[c["id"]]}"></i>' for c in m["colours"])
            cells.append((f'<span class="gl-dots">{dots}</span>', t("Colours"), self.f("n_colours", n=len(m["colours"]))))
        else:
            cells.append((ICON[m["edge"]], t("Edge"), E(m["edge"])))
            cells.append((ICON["size"], t("Overall size"), f'{self.size_plain(m, pm=True)} mm'))
            cells.append((f'<span class="gl-dots"><i style="background:{FINISH_DOT[m["finish"]]}"></i></span>', t("Finish"), E(m["finish"])))
            if m["included"]:
                cells.append((ICON["included"], t("Included"), E(m["included"])))
        out = "".join(f'<div class="gl"><div class="gl-ic">{ic}</div><div><div class="gl-k">{E(k)}</div><div class="gl-v">{v}</div></div></div>'
                      for ic, k, v in cells)
        return f'<div class="glance" style="grid-template-columns:repeat({len(cells)},auto)">{out}</div>'

    # ── compare: every model's plan to one scale ──
    LAYOUT_ORDER = ["Single bowl", "Single bowl with drainboard", "Double bowl", "Two bowls and a small bowl", "Double bowl with drainboard", None]

    def sizes_page(self, models, title, n_label, scale, note):
        t = self.t
        groups = []
        for lay in self.LAYOUT_ORDER:
            ms = sorted([m for m in models if m["bowls"] == lay], key=lambda m: (m["dims"][0], m["dims"][1], m["model"]))
            if ms:
                groups.append((lay, ms))
        parts = []
        for lay, ms in groups:
            cells, width = [], 0.0
            for m in ms:
                W, D = m["dims"][0], m["dims"][1]
                wl = self.f("unconfirmed") if (not self.G and m["dims_unconfirmed"]) else None
                bw, bh = W * scale + 11.0, D * scale + 9.0
                svg, _ = drawings.svg("granite" if self.G else "steel", m["model"], box_w=bw, box_h=bh, plan_only=True, scale=scale, width_label=wl)
                cells.append(f'<a class="cmp" href="#{self.show(m)["anchor"]}" style="width:{bw:.1f}mm">{svg}'
                             f'<div class="cmp-meta"><span class="code">{E(m["model"])}</span><span class="pg">{{PAGE:{m["model"]}}}</span></div></a>')
                width += bw + 5.0
            head = E(t(lay)) if lay else tbc(t("Bowls not stated"))
            # a group that fits on one line shares it with the next; a longer one takes the full width
            basis = f"{width - 5.0:.1f}mm" if width - 5.0 <= 180 else "100%"
            parts.append(f'<div class="cmp-group" style="flex:0 0 {basis}"><p class="label cmp-h">{head}</p><div class="cmp-row">{"".join(cells)}</div></div>')
        marks = drawing_marks(models, self.G)
        key = "".join(f'<span class="lg-i">{GLYPH[k]}<span>{E(t(GLYPH_LABEL[k]))}</span></span>' for k in marks)
        # four to a row; three where the words are long (the Indonesian)
        cols = 4 if sum(len(t(GLYPH_LABEL[k])) for k in marks) <= 110 else 3
        return (f'<section class="page compare vol-{self.kind}"><div class="trim">'
                f'<div class="ov-head"><div><p class="eyebrow">{E(t(n_label))}</p><h2 class="title-l" style="margin-top:3.5mm">{keep(E(t(title)))}</h2></div>'
                f'<p class="body">{E(t(note))}</p></div>'
                f'<div class="cmp-body">{"".join(parts)}</div>'
                f'<div class="legend"><p class="label">{E(t("Key"))}</p><div class="lg-row" style="grid-template-columns:repeat({cols},max-content)">{key}</div></div>'
                f'{folio(len(self.pages) + 1, self.title)}</div></section>')

    # ── granite: the two ways the sinks are fitted ──
    def install_page(self):
        t = self.t
        cols = []
        for inst, img_key, text in (("Undermount", "gsu7545", "Fitted under the worktop: the worktop's own edge runs round the bowl."),
                                    ("Top-mount", "gst6045", "Set into a cut-out from above: the sink's rim rests on the worktop.")):
            ms = [m for m in self.models if m["installation"] == inst]
            links = " ".join(f'<a href="#{self.show(m)["anchor"]}"><span class="nw">{E(m["model"])}</span><span class="pg">{{PAGE:{m["model"]}}}</span></a>' for m in ms)
            icon = ICON[inst].replace('class="ico"', 'class="ico big"')
            cols.append(f'<div class="ins"><div class="ins-img" style="background-image:url(\'{self.A["install"][img_key]}\')"></div>'
                        f'<div class="ins-ic">{icon}</div><h3>{E(t(inst))}</h3><p class="body">{E(t(text))}</p>'
                        f'<p class="label" style="margin:5mm 0 2mm">{self.f("n_models", n=len(ms))}</p><div class="ins-links">{links}</div></div>')
        return (f'<section class="page install vol-{self.kind}"><div class="trim">'
                f'<div class="sw-head"><p class="eyebrow">{t("Installation")}</p><h2 class="title-l" style="margin-top:3.5mm">{keep(t("Undermount and Top-mount"))}</h2>'
                f'<p class="lede">{E(t("The granite sinks are made for one of two installations, as listed for each model."))}</p></div>'
                f'<div class="ins-grid">{"".join(cols)}</div>{folio(len(self.pages) + 1, self.title)}</div></section>')

    # ── stainless: the two ranges side by side ──
    def ranges_page(self):
        t = self.t
        P = [m for m in self.models if m["range"] == "Pressed"]
        Hm = [m for m in self.models if m["range"] == "Hand Made"]

        def hs(ms):
            v = sorted({m["dims"][2] for m in ms})
            return f"{v[0]} mm" if len(v) == 1 else f"{v[0]} – {v[-1]} mm"

        def lays(ms):
            seen = [E(t(lay)) for lay in self.LAYOUT_ORDER if lay and any(m["bowls"] == lay for m in ms)]
            if any(m["bowls"] is None for m in ms):
                seen.append(tbc(t("Not stated")))
            return "<br>".join(seen)

        def thick(ms):
            if all(m["thickness"].startswith("± 0.") for m in ms):
                v = sorted(float(m["thickness"].split()[1]) for m in ms)
                return f"± {v[0]:g} – {v[-1]:g} mm"
            vals = []
            for m in ms:
                v = tbc(m["thickness"]) if m["model"] == "W 5050 TSB" else E(m["thickness"])
                if v not in vals:
                    vals.append(v)
            return '<br>'.join(f'<span class="nw">{v}</span>' for v in vals)

        inc = {}
        for m in Hm:
            if m["included"]:
                inc.setdefault(m["included"], []).append(m["model"])
        rows = [("Models", str(len(P)), str(len(Hm))),
                ("Brand", " · ".join(sorted({m["brand"] for m in P})), " · ".join(sorted({m["brand"] for m in Hm}))),
                ("Material", E(t("Stainless steel 201")), E(t("Stainless steel 201 or 304"))),
                ("Thickness", thick(P), thick(Hm)),
                ("Edge", "Inset Edge", "Flat Edge"),
                ("Finish", " · ".join(f for f in ("Mat Polished", "Electroplate") if any(m["finish"] == f for m in P)),
                 " · ".join(f for f in ("Satin", "Nano Black") if any(m["finish"] == f for m in Hm))),
                ("Layout", lays(P), lays(Hm)),
                ("Overall height", hs(P), hs(Hm)),
                ("Included", "—", "<br>".join(f'{E(k)} — {series(v)}' for k, v in inc.items()))]
        tr = "".join(f'<tr><th>{E(t(k))}</th><td>{a}</td><td>{b}</td></tr>' for k, a, b in rows)
        imgs = f'<div></div><div style="background-image:url(\'{self.A["range_img"]["Pressed"]}\')"></div><div style="background-image:url(\'{self.A["range_img"]["Hand Made"]}\')"></div>'
        return (f'<section class="page ranges vol-{self.kind}"><div class="trim">'
                f'<div class="sw-head"><p class="eyebrow">{t("Two ranges")}</p><h2 class="title-l" style="margin-top:3.5mm">{t("Pressed and Hand Made")}</h2>'
                f'<p class="lede">{E(t("The two ranges side by side, as listed in the Price List 2024."))}</p></div>'
                f'<div class="rg-imgs">{imgs}</div>'
                f'<table class="rg"><tr><th></th><th class="h">{t("Pressed")}</th><th class="h">{t("Hand Made")}</th></tr>{tr}</table>'
                f'<p class="body rg-note">{E(t("Thickness, layout and height are as listed for each model; see the model pages and the index."))}</p>'
                f'{folio(len(self.pages) + 1, self.title)}</div></section>')

    # ── stainless: what the price list says comes with a sink ──
    def included_page(self):
        t = self.t
        items = []
        for name, models in (("5 Modes Spray", ["W 7546 TSB", "W 7546 TSBN"]), ("2 Tempered Glasses", ["W 8550 TDG"]), ("Tempered Glasses Wing", ["W 10050 TSG"])):
            ms = [m for m in self.models if m["model"] in models]
            ph = "".join(f'<div class="inc-ph" style="background-image:url(\'{self.A["products"][m["photo"]]}\')"></div>' for m in ms)
            links = " ".join(f'<a href="#{self.show(m)["anchor"]}"><span class="nw">{E(m["model"])}</span><span class="pg">{{PAGE:{m["model"]}}}</span></a>' for m in ms)
            items.append(f'<div class="inc"><div class="inc-phs">{ph}</div><div><h3>{E(name)}</h3><div class="ins-links">{links}</div></div></div>')
        return (f'<section class="page included vol-{self.kind}"><div class="trim">'
                f'<div class="sw-head"><p class="eyebrow">{t("Included")}</p><h2 class="title-l" style="margin-top:3.5mm">{t("Supplied with the sink")}</h2>'
                f'<p class="lede">{E(t("Four hand made models come with an accessory listed in the Price List 2024, each shown here on the product photograph."))}</p></div>'
                f'<div class="inc-grid">{"".join(items)}</div>'
                f'<p class="body inc-note">{T(t("Other fittings seen in some product photographs — knife holders, soap dispensers, control knobs, rinsers and control panels — are not listed in the price list. They are marked † on their model pages, to be confirmed."))}</p>'
                f'{folio(len(self.pages) + 1, self.title)}</div></section>')

    def index_page(self):
        t = self.t
        rows = []
        if self.G:
            head = "<tr>" + "".join(f"<th>{E(h)}</th>" for h in (t("Model"), t("Bowls"), t("Installation"), self.f("head_size_wd"), t("Colours"))) + f'<th class="r">{t("Page")}</th></tr>'
            for m in self.models:
                cols = ", ".join(t(c["name"]) for c in m["colours"])
                rows.append(f'<tr><td class="m"><a href="#{self.show(m)["anchor"]}" style="color:inherit;text-decoration:none">{E(m["model"])}</a></td><td>{E(t(m["bowls"]))}</td><td>{E(t(m["installation"]))}</td>'
                            f'<td>{self.size_plain(m)}</td><td>{E(cols)}</td><td class="r">{{PAGE:{m["model"]}}}</td></tr>')
        else:
            head = "<tr>" + "".join(f"<th>{E(h)}</th>" for h in (t("Model"), t("Brand"), t("Bowls"), self.f("head_size_wdh"), t("Steel"), t("Finish"))) + f'<th class="r">{t("Page")}</th></tr>'
            for rng in ("Pressed", "Hand Made"):
                rows.append(f'<tr class="sec"><td colspan="7">{t(rng)}</td></tr>')
                for m in [x for x in self.models if x["range"] == rng]:
                    rows.append(f'<tr><td class="m"><a href="#{self.show(m)["anchor"]}" style="color:inherit;text-decoration:none">{E(m["model"])}</a></td><td>{E(m["brand"])}</td><td>{E(t(m["bowls"] or "Not stated†"))}</td>'
                                f'<td>{self.size_plain(m)}</td><td>{E(m["grade"])}</td><td>{E(m["finish"])}</td><td class="r">{{PAGE:{m["model"]}}}</td></tr>')
        notes = self.general_notes()
        half = (len(notes) + 1) // 2
        nhtml = "".join(f"<p>{T(t)}</p>" for t in notes[:half])
        nhtml2 = "".join(f"<p>{T(t)}</p>" for t in notes[half:])
        notes_block = ""
        strip = (bleed_img("ix-strip", self.A["strip"], "center") if self.G and self.A.get("strip") else "")
        return f'''<section class="page index vol-{self.kind}{' with-strip' if self.G else ''}">
  {strip if self.G else ''}
  <div class="trim">
    <div class="ix-head"><p class="eyebrow">{t("Index")}</p><h2 class="title-m" style="margin-top:3mm">{t("All Models")}</h2></div>
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
            notes = ["Dimensions are width × depth, in millimetres, as listed. Bowl depth and overall height are not given in the source.",
                     "The drawings show the listed overall dimensions; the bowl layout is drawn from the product photographs, for reference.",
                     "GST 7546 is listed in Pearl Black and Pure White only."] + common
        else:
            notes = ["Specifications are those of the Price List 2024 (14 August 2024). Sizes are approximate (±), width × depth × height, in millimetres.",
                     "The price list gives each model's edge (Inset Edge for Pressed, Flat Edge for Hand Made) but not its installation type. The images show the hand made models top-mounted or undermounted following the model code (T…, U…) — to be confirmed.",
                     "The drawings show the listed overall dimensions; the bowl layout is drawn from the product photographs, for reference."] + common
        return [self.t(x) for x in notes]

    def notes_page(self):
        notes = self.general_notes()
        half = (len(notes) + 1) // 2
        rows = ([("Material", "Granite composite"),
                 ("Colours", "Pearl Black · Pure White · Titanium Grey (GST 7546: Pearl Black and Pure White only)"),
                 ("Undermount", "GDU 8145 · GSU 6045 · GSU 7545 · GSU 8045"),
                 ("Top-mount", "GST 6045 · GST 7546"),
                 ("Source", "The shop's granite sink listings")] if self.G else
                [("Pressed", "Stainless steel 201 · Inset Edge · Mat Polished (LUCKY PRO, WL 03) or Electroplate (WL 05 A – WL 18)"),
                 ("Hand Made", "Stainless steel 201 or 304, as listed per model · Flat Edge · Satin or Nano Black"),
                 ("Included", "5 Modes Spray — W 7546 TSB, W 7546 TSBN · 2 Tempered Glasses — W 8550 TDG · Tempered Glasses Wing — W 10050 TSG"),
                 ("Source", "Price List 2024, 14 August 2024")])
        mat = "".join(f'<div><b>{E(self.t(k))}</b><span>{T(self.t(v))}</span></div>' for k, v in rows)
        strip = bleed_img("ix-strip", self.A["strip"], "center") if (self.A.get("strip") and not self.G) else ""
        return f'''<section class="page notes-page{" with-strip" if strip else ""} vol-{self.kind}">
  {strip}
  <div class="trim"><div class="nt"><p class="eyebrow">{self.t("Notes")}</p><h2 class="title-m" style="margin-top:3mm">{self.t("About this catalogue")}</h2>
    <div class="nt-cols"><div>{"".join(f"<p>{T(t)}</p>" for t in notes[:half])}</div><div>{"".join(f"<p>{T(t)}</p>" for t in notes[half:])}</div></div>
    <p class="label" style="margin-top:12mm">{self.t("At a glance")}</p><div class="mat">{mat}</div></div>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def image_page(self, img, pos="center", light=False):
        return f'''<section class="page on-image vol-{self.kind}{" foot-light" if light else ""}">{bleed_img("full-img", img, pos)}
  <div class="trim">{folio(len(self.pages) + 1, self.title)}</div></section>'''

    def back(self):
        st = f' style="background-image:url(\'{self.A["stone"]}\')"' if self.A.get("stone") else ""
        return f'''<section class="page dark back stone vol-{self.kind}"{st}>
  <div class="trim"><div class="bk-center"><img class="bk-mark" src="{self.A["mark_light"]}" alt="">
    <img class="bk-logo" src="{self.A["logo_light"]}" alt="Maju Terus Jaya">
    <div class="bk-line">{E(self.title)}<br>{self.f("volume", vol=self.vol)} · {EDITION}</div></div>
    <div class="bk-foot">{self.t("Specifications and images may change without notice. Colours and finishes in print may differ slightly from the products.")}</div>
  </div>
</section>'''

    # ── the whole volume ──
    def build(self):
        t = self.t
        if self.G:
            self.add(self.cover(), mark="Cover")
            self.add("{INTRO}", mark="Introduction and contents")
            self.add(self.overview(self.models, "Six Models", "Each model is shown on its own page, installed in a kitchen of its own, with its specifications and drawing.", 2, 52),
                     key="#collection", mark="The collection")
            self.add(self.colours_page(), key="#colours", mark="Colours")
            self.add(self.sizes_page(self.models, "Sizes and Layouts", "Compare", 1 / 15,
                                     "Every model drawn to the same scale, 1:15 on the printed page, grouped by its bowls."), key="#sizes", mark="Sizes and layouts")
            self.add(self.install_page(), key="#install", mark="Installation")
            self.outline.append((t("Models"), len(self.pages) + 1, 0))
            first = len(self.pages) + 1
            for m in self.models:
                self.add(self.feature(m), key=m["model"], mark=m["model"], level=1)
            last = len(self.pages)
            self.add(self.index_page(), key="#index", mark="Index")
            self.add(self.notes_page(), key="#notes", mark="Notes")
            self.add(self.image_page(self.A["closing"], self.A.get("closing_pos", "center"), self.A.get("closing_light", False)))
            self.add(self.back(), mark="Back cover")
            P = self.page_of
            contents = [("The collection", P["#collection"], f'{P["#collection"]:02d}'), ("Colours", P["#colours"], f'{P["#colours"]:02d}'),
                        ("Sizes and layouts", P["#sizes"], f'{P["#sizes"]:02d}'), ("Installation", P["#install"], f'{P["#install"]:02d}'),
                        ("Models", first, f"{first:02d} – {last:02d}"), ("Index", P["#index"], f'{P["#index"]:02d}'), ("Notes", P["#notes"], f'{P["#notes"]:02d}')]
        else:
            pressed = [m for m in self.models if m["range"] == "Pressed"]
            hand = [m for m in self.models if m["range"] == "Hand Made"]
            self.add(self.cover(), mark="Cover")
            self.add("{INTRO}", mark="Introduction and contents")
            self.add(self.finishes_page(), key="#finishes", mark="Finishes")
            self.add(self.ranges_page(), key="#ranges", mark="Pressed and Hand Made")
            self.add(self.overview(pressed, "Pressed", "Eleven models in stainless steel 201, from LUCKY PRO and wellup.", 4, 44, n_label="The collection · 1 of 2"),
                     key="#collection", mark="The collection: Pressed")
            self.add(self.overview(hand, "Hand Made", "Fourteen models in stainless steel 201 and 304, from wellup.", 4, 28, n_label="The collection · 2 of 2"),
                     mark="The collection: Hand Made")
            self.add(self.sizes_page(pressed, "Pressed", "Sizes and layouts · 1 of 2", 0.04,
                                     "Every model drawn to the same scale, 1:25 on the printed page, grouped by its bowls."), key="#sizes", mark="Sizes and layouts: Pressed")
            self.add(self.sizes_page(hand, "Hand Made", "Sizes and layouts · 2 of 2", 0.04,
                                     "Every model drawn to the same scale, 1:25 on the printed page, grouped by its bowls."), mark="Sizes and layouts: Hand Made")
            self.add(self.included_page(), key="#included", mark="Included")
            self.add(self.opener("Pressed", pressed, self.A["opener_pressed"], self.A.get("opener_pressed_pos", "center")), key="#pressed", mark="Pressed range")
            for m in pressed:
                self.add(self.feature(m), key=m["model"], mark=m["model"], level=1)
            p_last = len(self.pages)
            self.add(self.opener("Hand Made", hand, self.A["opener_hand"], self.A.get("opener_hand_pos", "center")), key="#hand", mark="Hand Made range")
            for m in hand:
                self.add(self.feature(m), key=m["model"], mark=m["model"], level=1)
            h_last = len(self.pages)
            self.add(self.index_page(), key="#index", mark="Index")
            self.add(self.notes_page(), key="#notes", mark="Notes")
            self.add(self.image_page(self.A["closing"], self.A.get("closing_pos", "center"), self.A.get("closing_light", False)))
            self.add(self.back(), mark="Back cover")
            P = self.page_of
            contents = [("Finishes", P["#finishes"], f'{P["#finishes"]:02d}'), ("Pressed and Hand Made", P["#ranges"], f'{P["#ranges"]:02d}'),
                        ("The collection", P["#collection"], f'{P["#collection"]:02d} – {P["#collection"] + 1:02d}'),
                        ("Sizes and layouts", P["#sizes"], f'{P["#sizes"]:02d} – {P["#sizes"] + 1:02d}'), ("Included", P["#included"], f'{P["#included"]:02d}'),
                        ("Pressed", P["#pressed"], f'{P["#pressed"]:02d} – {p_last:02d}'), ("Hand Made", P["#hand"], f'{P["#hand"]:02d} – {h_last:02d}'),
                        ("Index", P["#index"], f'{P["#index"]:02d}'), ("Notes", P["#notes"], f'{P["#notes"]:02d}')]
        self.pages[1] = self.intro(contents, n=2)
        assert len(self.pages) % 4 == 0, f"{self.kind}: {len(self.pages)} pages, not a multiple of four"
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
<html lang="{vol.lang}"><head><meta charset="utf-8"><title>Maju Terus Jaya — {E(vol.title)} — Volume {vol.vol}</title>
<link rel="stylesheet" href="fonts.css"><link rel="stylesheet" href="catalogue.css">
<style>{page_css(mode)}</style></head>
<body class="vol-{vol.kind}">
{body}
</body></html>'''


def main():
    data = json.load(open(sys.argv[1]))
    out_dir = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "screen"
    lang = sys.argv[4] if len(sys.argv) > 4 else "en"
    sfx = "" if lang == "en" else "-" + lang      # granite-screen.html, granite-screen-id.html
    assets = json.load(open(os.path.join(out_dir, f"assets-{mode}.json")))
    for kind in ("granite", "stainless"):
        vol = Volume(kind, data, assets[kind], mode, lang)
        body = vol.build()
        name = f"{kind}-{mode}{sfx}.html"
        open(os.path.join(out_dir, name), "w").write(document(vol, body, mode))
        json.dump([dict(title=t, page=p, level=lv) for t, p, lv in vol.outline], open(os.path.join(out_dir, f"{kind}-{mode}{sfx}.outline.json"), "w"), indent=1)
        print(name, len(vol.pages), "pages")


if __name__ == "__main__":
    main()

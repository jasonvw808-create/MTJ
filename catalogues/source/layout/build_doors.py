"""Build the door catalogue (Volume 03, Wellup UPVC Door Collection) as HTML, one page per A4 sheet, in the kitchen
sink volumes' design (catalogue.css, with doors.css for the pages only this volume has).

    python build_doors.py <doors.json> <out_dir> [print|screen] [en|id]

Every fact comes from doors.json, which tools/extract_doors.js writes from the website's own door records (index.src.html:
the Wellup PRICE LIST 2026, Door & Lock, as printed): the models, their types as printed, colours, lists, R and L and
every product code. Nothing is added to them. What the price list does not say is said to be unstated, and marked †
where it needs the store's confirmation. No prices are printed, as in the kitchen sink volumes."""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import drawings  # noqa: E402
import i18n  # noqa: E402
import i18n_doors  # noqa: E402

E = html.escape
EDITION = "2026"
VOL = "03"
MIN_PPI = 100          # a picture is never placed larger than this many pixels to the inch (the price list's own are small)
CODE = re.compile(r'\b(?:PT \d{3,4}(?: / WL \d{3})?|WL \d{3}|WELUP-DPT\d{7})\b')


def T(s):
    """Escaped text in which no model or product code breaks across a line."""
    return CODE.sub(lambda m: f'<span class="nw">{m.group(0)}</span>', E(s))


def series(items):
    items = list(items)
    return " ".join(f'<span class="nw">{E(x)}{" ·" if i < len(items) - 1 else ""}</span>' for i, x in enumerate(items))


def folio(n, title):
    side = "even" if n % 2 == 0 else "odd"
    return f'<footer class="folio {side}"><span>{E(title)}</span><span class="num">{n:02d}</span></footer>'


def bleed_img(cls, url, pos="center"):
    return f'<div class="bleed-img {cls}" style="background-image:url(\'{url}\');background-position:{pos}"></div>'


def tbc(s):
    return f'{s}<span class="tbc">&#8202;†</span>'


ICON = {
    "door": '<svg viewBox="0 0 24 16" class="ico"><rect x="8.2" y="1.2" width="7.6" height="13.6" rx=".4" fill="none"/><circle cx="9.9" cy="8.4" r=".75"/></svg>',
    "size": '<svg viewBox="0 0 24 16" class="ico"><path d="M3 4.5h18M3 2.8v3.4M21 2.8v3.4" fill="none"/><rect x="3" y="8.2" width="18" height="6" rx="1" fill="none"/></svg>',
    "hand": '<svg viewBox="0 0 24 16" class="ico"><path d="M3.5 8h17M3.5 8l2.6-2.4M3.5 8l2.6 2.4M20.5 8l-2.6-2.4M20.5 8l-2.6 2.4" fill="none"/></svg>',
}


class DoorVolume:
    def __init__(self, data, assets, mode, lang="en"):
        self.D, self.A, self.mode, self.lang = data, assets, mode, lang
        self.ID = {**i18n.ID, **i18n_doors.ID}
        self.kind = "doors"
        self.models = data["models"]
        self.title = self.t("Wellup UPVC Door Collection")
        self.pages, self.page_of, self.outline = [], {}, []
        # the website's four sections, each with its models in the price list's order
        self.sections = [(s, [m for m in self.models if m["type"] in s["types"]]) for s in data["sections"]]
        assert sum(len(ms) for _, ms in self.sections) == len(self.models), "a model in no section, or in two"

    # ── words ──
    def t(self, s):
        if self.lang == "en" or s is None:
            return s
        if s not in self.ID:
            raise KeyError("no Indonesian for: " + s)
        return self.ID[s]

    def f(self, key, **kw):
        return i18n_doors.TEMPLATES[self.lang][key].format(**kw)

    def x(self, v):
        return v[self.lang] if isinstance(v, dict) else v

    def colour(self, c):
        return self.x(self.D["colours"][c])

    def list_name(self, l):
        return self.D["lists"][l]["en"] if self.lang == "en" else self.D["lists"][l]["id"]

    def type_en(self, m):
        s = self.D["types"][m["type"]]["en"]
        return s[0].upper() + s[1:]

    def type_line(self, m):
        """The type: as the price list prints it, and in English in the English edition."""
        return m["typeAs"] if self.lang == "id" else f'{m["typeAs"]} — {self.type_en(m)}'

    def section_of(self, m):
        return next(i for i, (s, ms) in enumerate(self.sections) if m in ms)

    def anchor(self, m):
        return "m-" + m["key"]

    def row(self, m, c, l=None):
        return next(r for r in m["rows"] if r["colour"] == c and r["list"] == l)

    def photo(self, r):
        return self.A["doors"][r["photos"][0]]

    def aspect(self, r):
        return self.A["aspect"][r["photos"][0]]

    def max_h(self, rows):
        """The tallest a group of pictures may stand, in mm, by the smallest of them."""
        return min(self.A["src_h"][r["photos"][0]] for r in rows) / MIN_PPI * 25.4

    def from_list(self, m):
        return any(self.A["src_h"][r["photos"][0]] < 900 for r in m["rows"])

    def only_rows(self, m):
        return [r for r in m["rows"] if len(r["hands"]) < 2]

    def only_notes(self, models=None):
        """What the data offers in one opening only, said once for each: 'In Dark Grey, the PT 409 is offered in R only.'"""
        return [self.f("only_note", model=m["code"], colour=self.colour(r["colour"]) + (" · " + self.list_name(r["list"]) if r["list"] else ""),
                       hands=" / ".join(h["id"] for h in r["hands"]))
                for m in (models or self.models) for r in self.only_rows(m)]

    def hands_line(self, m):
        only = self.only_rows(m)
        base = "R / L"
        if not only:
            return base
        parts = [self.f("only", what=self.colour(r["colour"]) + (" · " + self.list_name(r["list"]) if r["list"] else ""),
                         hands=" / ".join(h["id"] for h in r["hands"])) for r in only]
        return base + " (" + "; ".join(parts) + ")"

    # ── pages ──
    def add(self, html_, key=None, mark=None, level=0, said=False):
        """A page; its bookmark (mark) in the volume's language — translated here unless said already."""
        self.pages.append(html_)
        if key:
            self.page_of[key] = len(self.pages)
        if mark:
            self.outline.append((mark if level or said else self.t(mark), len(self.pages), level))

    def cover(self):
        title = f'<h1 class="cv-title" style="font-size:84pt;letter-spacing:.34em">{E(self.t("Doors"))}</h1>'
        return f'''<section class="page cover vol-doors">
  {bleed_img("full-img cv-img", self.A["cover"], self.A.get("cover_pos", "center"))}
  <div class="shade-top"></div><div class="shade-bot"></div>
  <div class="trim">
    <div class="cv-bar"><img class="cv-logo" src="{self.A["logo_light"]}" alt="Maju Terus Jaya"><span>{self.f("catalogue", edition=EDITION)}</span></div>
    <div class="cv-block">
      <p class="cv-eyebrow">{self.f("volume_of", vol=VOL)}</p>
      {title}
      <div class="cv-sub"><span>{self.t("Nineteen models · Three colours")}</span><span>{self.t("Wellup UPVC · 200 x 70 cm")}</span></div>
    </div>
  </div>
</section>'''

    def intro(self, contents):
        lede = self.t("Nineteen UPVC doors from Wellup, every one listed at 200 x 70 cm, in White, Brown and Dark Grey, "
                      "and each in R and in L. The PT 2601 and PT 2602 also come with a white or a black list.")
        body = self.t("Each model has a page of its own: its colours as photographed, its specification as printed in the "
                      "Wellup Price List 2026, and every product code it is ordered by. The colours, the size and the opening "
                      "are set out at the front; all the codes are listed together at the back.")
        n_codes = sum(len(r["hands"]) for m in self.models for r in m["rows"])
        facts = [(str(len(self.models)), "Models"), (str(len(self.D["colourOrder"])), "Colours"), (str(n_codes), "Product codes")]
        rows = "".join(f'<a href="#p{p}"><span>{E(t)}</span><span>{E(pg)}</span></a>' for t, p, pg in contents)
        fx = "".join(f'<div><div class="n">{n}</div><div class="label t">{E(self.t(t))}</div></div>' for n, t in facts)
        st = f' style="background-image:url(\'{self.A["stone"]}\')"' if self.A.get("stone") else ""
        return f'''<section class="page dark intro stone vol-doors"{st}>
  {bleed_img("in-img", self.A["intro"], self.A.get("intro_pos", "center"))}
  <div class="trim">
    <div class="in-text">
      <div><p class="eyebrow">{self.f("volume", vol=VOL)}</p><h2 class="title-l" style="font-size:21pt">{E(self.title)}</h2>
        <p class="lede" style="margin:0 0 5mm">{T(lede)}</p><p class="body" style="margin:0">{T(body)}</p>
        <div class="facts">{fx}</div></div>
      <div><p class="label" style="margin:3.5mm 0 3mm">{self.t("Contents")}</p><nav class="contents">{rows}</nav></div>
    </div>
    {folio(2, self.title)}
  </div>
</section>'''

    # every model at a glance, by section: seven to a row, the first section on two rows, the other three on one
    def collection(self):
        cells = []
        first, rest = self.sections[0], self.sections[1:]

        def card(m):
            r = self.row(m, "dark-grey", "white" if m["lists"] else None)
            wl = m["wl"] or "&nbsp;"
            return (f'<a class="dcard" href="#{self.anchor(m)}"><div class="door-ph ph" style="background-image:url(\'{self.photo(r)}\')"></div>'
                    f'<div class="meta"><span class="code">{E(m["code"])}</span><span class="pg">{{PAGE:{m["code"]}}}</span></div>'
                    f'<div class="line wl">{E(wl) if m["wl"] else wl}</div><div class="line">{E(m["typeAs"])}</div></a>')

        def head(i, s, ms, span):
            n = f'<span class="n">{self.f("n_models", n=len(ms))}</span>' if span > 2 else ""
            return (f'<p class="dsec" style="grid-column:span {span}"><span class="no">{i:02d}</span>{E(self.x(s["title"]))}{n}</p>')

        cells.append(head(1, first[0], first[1], 7))
        cells += [card(m) for m in first[1]]
        cells += ['<span></span>'] * ((7 - len(first[1]) % 7) % 7)
        for i, (s, ms) in enumerate(rest, 2):
            cells.append(head(i, s, ms, len(ms)))
        for s, ms in rest:
            cells += [card(m) for m in ms]
        body = self.t("Every model in Dark Grey, with the page it is on. Each is also listed in White and in Brown.")
        return f'''<section class="page overview dcoll vol-doors">
  <div class="trim">
    <div class="ov-head"><div><p class="eyebrow">{self.t("The collection")}</p><h2 class="title-l" style="margin-top:3.5mm">{self.t("Nineteen Models")}</h2></div>
      <p class="body">{E(body)}</p></div>
    <div class="dgrid">{"".join(cells)}</div>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def colours_page(self):
        m270 = next(m for m in self.models if m["code"] == "PT 270")
        rows = [self.row(m270, c) for c in self.D["colourOrder"]]
        h = min(104.0, self.max_h(rows))
        cols = []
        for r in rows:
            c = r["colour"]
            only = [(m, q) for m in self.models for q in m["rows"] if q["colour"] == c and len(q["hands"]) < 2]
            avail = self.t("All nineteen models")
            note = ""
            if only:
                note = '<br><span style="color:var(--mute)">' + T("; ".join(self.f("only", what=m["code"], hands=" / ".join(h["id"] for h in q["hands"])) for m, q in only)) + "&#8202;†</span>"
            cols.append(f'''<div class="dk"><div class="door-ph" style="height:{h:.1f}mm;background-image:url('{self.photo(r)}')"></div>
      <h3><i style="background:{m270["cols"][c]}"></i>{E(self.colour(c))}</h3><div class="avail"><b>{self.t("Available")}</b>{E(avail)}{note}</div></div>''')
        m2601 = next(m for m in self.models if m["code"] == "PT 2601")
        lists = []
        for l, c in (("white", "dark-grey"), ("black", "white")):
            r = self.row(m2601, c, l)
            lists.append(f'''<div class="dl-i"><div class="dl-ph" style="background-image:url('{self.photo(r)}')"></div>
      <h3><i style="background:{self.D["lists"][l]["hex"]}"></i>{E(self.list_name(l))}</h3>
      <div class="avail">{E(self.f("shown_on", model=m2601["code"], colour=self.colour(c)))}</div></div>''')
        list_models = [m for m in self.models if m["lists"]]
        lede = self.t("Every model is listed in White, Brown and Dark Grey: here on the PT 270, as photographed.")
        ltext = self.t("The PT 2601 and PT 2602 are also listed with a white or a black list: the bars between the glass panes.")
        return f'''<section class="page swatches dcolours vol-doors">
  <div class="trim">
    <div class="sw-head"><p class="eyebrow">{self.t("Colours and lists")}</p><h2 class="title-l" style="margin-top:3.5mm">{self.t("Three Colours")}</h2>
      <p class="lede">{T(lede)}</p></div>
    <div class="dk-grid">{"".join(cols)}</div>
    <div class="dl-band"><div class="dl-text"><p class="label">{self.t("Two lists")}</p><p class="body">{T(ltext)}</p>
      <p class="body dl-models">{series(m["name"] for m in list_models)}</p></div>{"".join(lists)}</div>
    <p class="body sw-foot">{self.t("Colours in print may differ slightly from the products.")}</p>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def door_drawing(self, box_w=68.0):
        """The door's front, at its listed size, as the website draws it: the outline and the two listed dimensions."""
        W, H = 70.0, 200.0
        pad_t, pad_r = 7.0, 13.0
        s = (box_w - 1.0 - pad_r) / W
        box_h = round(pad_t + H * s + 1.5, 1)
        ox, oy = 1.0 + W / 2 * s, pad_t + H / 2 * s
        out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {box_w:g} {box_h:g}" width="{box_w:g}mm" height="{box_h:g}mm" class="drawing">',
               f'<rect x="{ox - W / 2 * s:.2f}" y="{oy - H / 2 * s:.2f}" width="{W * s:.2f}" height="{H * s:.2f}" {drawings.STYLE["outline"]}/>']
        out += drawings._dim_h(-W / 2, W / 2, pad_t - 3.0, "70 cm", s, ox, oy)
        out += drawings._dim_v(-H / 2, H / 2, ox + W / 2 * s + 3.2, "200 cm", s, ox, oy)
        out.append("</svg>")
        return "\n".join(out)

    def size_page(self):
        t = self.t
        m = self.models[0]
        printed = f'Wellup Pintu UPVC {m["code"]}, {self.D["size"]}, 1.8mm, {m["typeAs"]} White R'
        rows = [(t("Size"), E(self.D["size"])), (t("Width"), "70 cm"), (t("Height"), "200 cm"),
                (t("Specification, as printed"), tbc(E(self.D["size"] + ", 1.8mm")))]
        dl = "".join(f'<div><dt>{E(k)}</dt><dd>{v}</dd></div>' for k, v in rows)
        unstated = ["Stock and delivery", "Installation", "Warranty", "Whether the frame (kusen) is included",
                    "The handle and lock", "The opening a door needs"]
        ul = "".join(f'<li>{E(t(u))}</li>' for u in unstated)
        return f'''<section class="page dsize vol-doors">
  <div class="trim">
    <div class="sw-head"><p class="eyebrow">{t("Size and opening")}</p><h2 class="title-l" style="margin-top:3.5mm">200 x 70 cm</h2>
      <p class="lede">{T(t("Every model, in every colour, is listed at the same size: 200 x 70 cm, 1.8mm."))}</p></div>
    <figure class="sz-draw">{self.door_drawing()}<figcaption>{E(t("Front · cm · as listed"))}</figcaption></figure>
    <div class="sz-text">
      <div class="sz-b"><p class="label">{t("As printed in the price list")}</p><p class="sz-print">{T(printed)}</p>
        <dl class="specs">{dl}</dl>
        <p class="sz-note">† {E(t("What the 1.8mm measures, and whether the size is of the door alone or with its frame, are not stated."))}</p></div>
      <div class="sz-b"><p class="label">{t("R and L")}</p>
        <p class="body">{T(t("Every model is listed in R and in L, each with a product code of its own. The price list does not show which way R or L opens: ask us before you order."))}</p>
        {"".join(f'<p class="body">† {T(x)}</p>' for x in self.only_notes())}</div>
      <div class="sz-b"><p class="label">{t("Not stated in the price list")}</p><ul class="sz-list">{ul}</ul>
        <p class="body sz-ask">{E(t("Contact us for details."))}</p></div>
    </div>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    # a section's first page: its number, its name, its types as printed, its models, and one of its doors
    OPENER_DOOR = {"top-glass": ("PT 113", "brown", None), "full": ("PT 290", "dark-grey", None),
                   "panes": ("PT 2601", "white", "black"), "side": ("PT 709", "brown", None)}

    def opener(self, i, s, ms):
        t = self.t
        code, c, l = self.OPENER_DOOR[s["id"]]
        dm = next(m for m in ms if m["code"] == code)
        r = self.row(dm, c, l)
        h = min(196.0, self.max_h([r]))
        w = h * self.aspect(r)
        types = []
        for ty in s["types"]:
            tm = [m for m in ms if m["type"] == ty]
            if tm:
                types.append(f'<div><b>{E(self.D["types"][ty]["as"])}</b><span>{series(m["code"] for m in tm)}</span></div>')
        links = "".join(f'<a href="#{self.anchor(m)}"><span class="nw">{E(m["name"])}</span><span class="pg">{{PAGE:{m["code"]}}}</span></a>' for m in ms)
        cap = dm["code"] + " · " + self.colour(c) + (" · " + self.list_name(l) if l else "")
        return f'''<section class="page dopen vol-doors" id="s-{s["id"]}">
  <div class="trim">
    <div class="do-text"><p class="do-no">{i:02d}</p><p class="eyebrow">{E(self.f("section_n", i=f"{i:02d}", n=len(ms)))}</p>
      <h2 class="do-title">{E(self.x(s["title"]))}</h2><p class="lede">{T(self.x(s["line"]))}</p>
      <p class="label do-l">{t("Types, as printed")}</p><div class="do-types">{"".join(types)}</div>
      <p class="label do-l">{t("Models")}</p><div class="ins-links">{links}</div></div>
    <figure class="do-door" style="width:{w:.1f}mm"><div class="door-ph" style="height:{h:.1f}mm;background-image:url('{self.photo(r)}')"></div>
      <figcaption>{E(cap)}</figcaption></figure>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def hero(self, m):
        if m["lists"]:
            grid = [[self.row(m, c, l) for c in self.D["colourOrder"]] for l in m["lists"]]
            h = min(60.0, self.max_h(m["rows"]))
        else:
            grid = [[self.row(m, c) for c in self.D["colourOrder"]]]
            h = min(122.0, self.max_h(m["rows"]))
        out = []
        for g in grid:
            cells = []
            for r in g:
                w = h * self.aspect(r)
                nm = self.colour(r["colour"]) + (" · " + self.list_name(r["list"]) if r["list"] else "")
                cells.append(f'<figure class="hd"><div class="door-ph" style="width:{w:.1f}mm;height:{h:.1f}mm;background-image:url(\'{self.photo(r)}\')"></div>'
                             f'<figcaption>{E(nm)}</figcaption></figure>')
            out.append(f'<div class="hd-row">{"".join(cells)}</div>')
        return f'<div class="hband{" two" if len(grid) > 1 else ""}">{"".join(out)}</div>'

    def specs(self, m):
        t = self.t
        rows = [(t("Brand"), "Wellup"), (t("Range"), E(t("UPVC Door"))), (t("Model"), E(m["name"])),
                (t("Size"), E(self.D["size"])),
                (t("Specification, as printed"), T(f'{self.D["size"]}, 1.8mm, {m["typeAs"]}')),
                (t("Type"), E(m["typeAs"] if self.lang == "id" else self.type_en(m))),
                (t("Colours"), E(" · ".join(self.colour(c) for c in self.D["colourOrder"])))]
        if m["lists"]:
            rows.append((t("Lists"), E(" · ".join(self.list_name(l) for l in m["lists"]))))
        rows.append((t("Opening"), E(self.hands_line(m))))
        return rows

    def codes_table(self, m):
        t = self.t
        lists = bool(m["lists"])
        head = (f'<tr><th>{t("Colour")}</th>' + (f'<th>{t("List")}</th>' if lists else "") + '<th>R</th><th>L</th></tr>')
        body = []
        for r in m["rows"]:
            cells = []
            for hid in ("R", "L"):
                h = next((q for q in r["hands"] if q["id"] == hid), None)
                cells.append(f'<td class="c">{E(h["code"])}</td>' if h else f'<td class="c none">{tbc(E(t("Not offered")))}</td>')
            body.append(f'<tr><td>{E(self.colour(r["colour"]))}</td>' + (f'<td>{E(self.list_name(r["list"]))}</td>' if lists else "") + "".join(cells) + "</tr>")
        return f'<table class="dcodes{" wl" if lists else ""}">{head}{"".join(body)}</table>'

    def glance(self, m):
        t = self.t
        dots = "".join(f'<i style="background:{m["cols"][c]}"></i>' for c in self.D["colourOrder"])
        cells = [(ICON["door"], t("Type, as printed"), E(m["typeAs"])), (ICON["size"], t("Size"), E(self.D["size"])),
                 (f'<span class="gl-dots">{dots}</span>', t("Colours"), self.f("n_colours", n=3))]
        if m["lists"]:
            ld = "".join(f'<i style="background:{self.D["lists"][l]["hex"]}"></i>' for l in m["lists"])
            cells.append((f'<span class="gl-dots">{ld}</span>', t("Lists"), E(" · ".join(self.list_name(l) for l in m["lists"]))))
        cells.append((ICON["hand"], t("Opening"), "R / L" + ("&#8202;†" if self.only_rows(m) else "")))
        out = "".join(f'<div class="gl"><div class="gl-ic">{ic}</div><div><div class="gl-k">{E(k)}</div><div class="gl-v">{v}</div></div></div>'
                      for ic, k, v in cells)
        return f'<div class="glance" style="grid-template-columns:repeat({len(cells)},auto)">{out}</div>'

    def notes_for(self, m):
        t = self.t
        out = []
        if m["code"] == "PT 111":
            out.append(t("The price list's own picture of the PT 111 shows the PT 113; these are the PT 111's photographs."))
        out += self.only_notes([m])
        if self.from_list(m):
            out.append(t("No photographs were supplied for this model: its pictures are the price list's own, which are small."))
        return out

    def feature(self, m):
        i = self.section_of(m)
        s, _ = self.sections[i]
        desc = self.x(m["short"])
        specs = "".join(f'<div><dt>{E(k)}</dt><dd>{v}</dd></div>' for k, v in self.specs(m))
        notes = "".join(f'<span>† {T(x)}</span>' for x in self.notes_for(m))
        cap = self.t("Pictures from the Wellup price list") if self.from_list(m) else self.t("As photographed")
        eyebrow = f'{i + 1:02d} · {self.x(s["title"])}'
        return f'''<section class="page feature dfeat vol-doors" id="{self.anchor(m)}">
  <div class="trim">
    {self.hero(m)}
    <div class="hero-cap">{E(cap)}</div>
    <div class="panel">
      <div class="ph-row"><div><p class="eyebrow">{E(eyebrow)}</p><h2 class="code">{E(m["name"])}</h2><p class="desc">{E(desc)}</p></div>
        <div class="d-src">{self.t("Wellup Price List 2026")}</div></div>
      {self.glance(m)}
      <div class="cols"><dl class="specs">{specs}</dl><div class="dcodes-w"><p class="label">{self.t("Product codes")}</p>{self.codes_table(m)}
        {f'<p class="d-notes">{notes}</p>' if notes else ''}</div></div>
    </div>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def codes_page(self):
        t = self.t
        cols = [(c, h) for c in self.D["colourOrder"] for h in ("R", "L")]
        head = (f'<tr><th>{t("Model")}</th><th>{t("List")}</th>' +
                "".join(f'<th>{E(self.colour(c))} {h}</th>' for c, h in cols) + f'<th class="r">{t("Page")}</th></tr>')
        rows = []
        for i, (s, ms) in enumerate(self.sections, 1):
            rows.append(f'<tr class="sec"><td colspan="{len(cols) + 3}">{i:02d} · {E(self.x(s["title"]))}</td></tr>')
            for m in ms:
                for l in (m["lists"] or [None]):
                    cells = []
                    for c, hid in cols:
                        r = self.row(m, c, l)
                        h = next((q for q in r["hands"] if q["id"] == hid), None)
                        cells.append(f'<td class="c">{E(h["code"])}</td>' if h else f'<td class="c none">—&#8202;†</td>')
                    rows.append(f'<tr><td class="m"><a href="#{self.anchor(m)}">{E(m["code"])}</a></td><td>{E(self.list_name(l)) if l else "—"}</td>'
                                f'{"".join(cells)}<td class="r">{{PAGE:{m["code"]}}}</td></tr>')
        n = sum(len(r["hands"]) for m in self.models for r in m["rows"])
        return f'''<section class="page index dallcodes vol-doors">
  <div class="trim">
    <div class="ix-head"><p class="eyebrow">{t("Product codes")}</p><h2 class="title-m" style="margin-top:3mm">{E(self.f("all_codes", n=n))}</h2>
      <p class="body">{T(t("Every code the Wellup Price List 2026 gives these doors, by model, colour and list, in R and in L."))}</p></div>
    <table><colgroup><col class="cm"><col class="cl">{"<col>" * len(cols)}<col class="cp"></colgroup>{head}{"".join(rows)}</table>
    <p class="body ac-note">{" ".join("† " + T(x) for x in self.only_notes())}</p>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def index_page(self):
        t = self.t
        head = "<tr>" + "".join(f"<th>{E(h)}</th>" for h in (t("Model"), t("Type, as printed"), t("Colours"), t("Lists"), t("Opening"))) + f'<th class="r">{t("Page")}</th></tr>'
        rows = []
        for i, (s, ms) in enumerate(self.sections, 1):
            rows.append(f'<tr class="sec"><td colspan="6">{i:02d} · {E(self.x(s["title"]))}</td></tr>')
            for m in ms:
                cols = " · ".join(self.colour(c) for c in self.D["colourOrder"])
                lists = " · ".join(self.list_name(l) for l in m["lists"]) if m["lists"] else "—"
                hands = "R / L" + ("&#8202;†" if self.only_rows(m) else "")
                rows.append(f'<tr><td class="m"><a href="#{self.anchor(m)}" style="color:inherit;text-decoration:none">{E(m["name"])}</a></td>'
                            f'<td>{E(m["typeAs"])}</td><td>{E(cols)}</td><td>{E(lists)}</td><td>{hands}</td><td class="r">{{PAGE:{m["code"]}}}</td></tr>')
        return f'''<section class="page index dindex vol-doors">
  <div class="trim">
    <div class="ix-head"><p class="eyebrow">{t("Index")}</p><h2 class="title-m" style="margin-top:3mm">{t("All Models")}</h2></div>
    <table>{head}{"".join(rows)}</table>
    <p class="body ac-note">{T(t("Every model is listed at 200 x 70 cm, 1.8mm, in White, Brown and Dark Grey, each in R and in L."))}
      {" ".join("† " + T(x) for x in self.only_notes())}</p>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def general_notes(self):
        notes = ["Specifications, product codes and types are as printed in the Wellup PRICE LIST 2026 (Door & Lock). Every door is listed at 200 x 70 cm, 1.8mm.",
                 "Each model is listed in R and in L, with a product code for each. The price list does not show which way R or L opens.",
                 "Not stated in the price list: stock, delivery, installation, warranty, whether the frame (kusen) is included, the handle and lock, and the opening a door needs. Contact us for details.",
                 "The doors are shown as photographed for the shop. No photographs were supplied for the PT 109, PT 409, PT 709, PT 809 and PT 909: their pictures are the price list's own.",
                 "The price list's own picture of the PT 111 shows the PT 113; the PT 111's photographs are used here.",
                 "The hallway on the cover and in the introduction is a visualisation, made from the supplied photograph of the PT 2602 in Dark Grey with a black list; the room and what stands in it are styling.",
                 "Prices are not printed in this catalogue. For prices, see the website or contact us.",
                 "Colours in print may differ slightly from the products.",
                 "† Marks information to be confirmed with the store."]
        return [self.t(x) for x in notes] + ["† " + x for x in self.only_notes()]

    def notes_page(self):
        notes = self.general_notes()
        half = (len(notes) + 1) // 2
        rows = [("Brand", "Wellup"), ("Material", "UPVC"), ("Size", "200 x 70 cm, 1.8mm — every model"),
                ("Colours", "White · Brown · Dark Grey"), ("Lists", "List Putih · List Hitam — PT 2601, PT 2602"),
                ("Opening", "R / L, each with its own product code"), ("Source", "Wellup PRICE LIST 2026 — Door & Lock")]
        mat = "".join(f'<div><b>{E(self.t(k))}</b><span>{T(self.t(v))}</span></div>' for k, v in rows)
        return f'''<section class="page notes-page vol-doors">
  <div class="trim"><div class="nt"><p class="eyebrow">{self.t("Notes")}</p><h2 class="title-m" style="margin-top:3mm">{self.t("About this catalogue")}</h2>
    <div class="nt-cols"><div>{"".join(f"<p>{T(x)}</p>" for x in notes[:half])}</div><div>{"".join(f"<p>{T(x)}</p>" for x in notes[half:])}</div></div>
    <p class="label" style="margin-top:12mm">{self.t("At a glance")}</p><div class="mat">{mat}</div></div>
    {folio(len(self.pages) + 1, self.title)}
  </div>
</section>'''

    def back(self):
        st = f' style="background-image:url(\'{self.A["stone"]}\')"' if self.A.get("stone") else ""
        return f'''<section class="page dark back stone vol-doors"{st}>
  <div class="trim"><div class="bk-center"><img class="bk-mark" src="{self.A["mark_light"]}" alt="">
    <img class="bk-logo" src="{self.A["logo_light"]}" alt="Maju Terus Jaya">
    <div class="bk-line">{E(self.title)}<br>{self.f("volume", vol=VOL)} · {EDITION}</div></div>
    <div class="bk-foot">{self.t("Specifications and images may change without notice. Colours and finishes in print may differ slightly from the products.")}</div>
  </div>
</section>'''

    def build(self):
        self.add(self.cover(), mark="Cover")
        self.add("{INTRO}", mark="Introduction and contents")
        self.add(self.collection(), key="#collection", mark="The collection")
        self.add(self.colours_page(), key="#colours", mark="Colours and lists")
        self.add(self.size_page(), key="#size", mark="Size and opening")
        spans = []
        for i, (s, ms) in enumerate(self.sections, 1):
            self.add(self.opener(i, s, ms), key="#s-" + s["id"], mark=self.x(s["title"]), said=True)
            first = len(self.pages)
            for m in ms:
                self.add(self.feature(m), key=m["code"], mark=m["name"], level=1)
            spans.append((self.x(s["title"]), first, len(self.pages)))
        self.add(self.codes_page(), key="#codes", mark="Product codes")
        self.add(self.index_page(), key="#index", mark="Index")
        self.add(self.notes_page(), key="#notes", mark="Notes")
        self.add(self.back(), mark="Back cover")
        P, t = self.page_of, self.t
        contents = [(t("The collection"), P["#collection"], f'{P["#collection"]:02d}'), (t("Colours and lists"), P["#colours"], f'{P["#colours"]:02d}'),
                    (t("Size and opening"), P["#size"], f'{P["#size"]:02d}')]
        contents += [(title, a, f"{a:02d} – {b:02d}") for title, a, b in spans]
        contents += [(t("Product codes"), P["#codes"], f'{P["#codes"]:02d}'), (t("Index"), P["#index"], f'{P["#index"]:02d}'), (t("Notes"), P["#notes"], f'{P["#notes"]:02d}')]
        self.pages[1] = self.intro(contents)
        assert len(self.pages) % 4 == 0, f"doors: {len(self.pages)} pages, not a multiple of four"
        out = "\n".join(self.pages)
        for key, p in self.page_of.items():
            out = out.replace("{PAGE:" + key + "}", f"{p:02d}")
        assert "{PAGE:" not in out, "a page number left unset"
        return out


def page_css(mode):
    bleed = 3 if mode == "print" else 0
    return (f"@page {{ size: {210 + 2 * bleed}mm {297 + 2 * bleed}mm; margin: 0; }}\n"
            f":root {{ --bleed: {bleed}mm; --pw: {210 + 2 * bleed}mm; --ph: {297 + 2 * bleed}mm; }}\n")


def document(vol, body, mode):
    return f'''<!doctype html>
<html lang="{vol.lang}"><head><meta charset="utf-8"><title>Maju Terus Jaya — {E(vol.title)} — Volume {VOL}</title>
<link rel="stylesheet" href="fonts.css"><link rel="stylesheet" href="catalogue.css"><link rel="stylesheet" href="doors.css">
<style>{page_css(mode)}</style></head>
<body class="vol-doors">
{body}
</body></html>'''


def main():
    data = json.load(open(sys.argv[1]))
    out_dir = sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else "screen"
    lang = sys.argv[4] if len(sys.argv) > 4 else "en"
    sfx = "" if lang == "en" else "-" + lang
    assets = json.load(open(os.path.join(out_dir, f"assets-doors-{mode}.json")))
    vol = DoorVolume(data, assets, mode, lang)
    body = vol.build()
    name = f"doors-{mode}{sfx}.html"
    open(os.path.join(out_dir, name), "w").write(document(vol, body, mode))
    json.dump([dict(title=t, page=p, level=lv) for t, p, lv in vol.outline], open(os.path.join(out_dir, f"doors-{mode}{sfx}.outline.json"), "w"), indent=1)
    print(name, len(vol.pages), "pages")


if __name__ == "__main__":
    main()

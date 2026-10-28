# Maju Terus Jaya — Kitchen Sink Catalogues, 2026

Two coordinated catalogue volumes, redesigned from the shop's two kitchen sink catalogues:

| Volume | Language | Presentation / screen (A4) | Print (A4 + 3 mm bleed) |
|---|---|---|---|
| **01 · Granite Kitchen Sink Collection**: 6 models, 16 pages | English | `pdf/MTJ_Granite_Kitchen_Sink_Collection_Vol01.pdf` | `pdf/MTJ_Granite_Kitchen_Sink_Collection_Vol01_PRINT.pdf` |
| | Bahasa Indonesia | `pdf/MTJ_Granite_Kitchen_Sink_Collection_Vol01_ID.pdf` | `pdf/MTJ_Granite_Kitchen_Sink_Collection_Vol01_ID_PRINT.pdf` |
| **02 · Stainless Steel Kitchen Sink Collection**: 25 models, 40 pages | English | `pdf/MTJ_Stainless_Steel_Kitchen_Sink_Collection_Vol02.pdf` | `pdf/MTJ_Stainless_Steel_Kitchen_Sink_Collection_Vol02_PRINT.pdf` |
| | Bahasa Indonesia | `pdf/MTJ_Stainless_Steel_Kitchen_Sink_Collection_Vol02_ID.pdf` | `pdf/MTJ_Stainless_Steel_Kitchen_Sink_Collection_Vol02_ID_PRINT.pdf` |

Both page counts are multiples of four, for saddle-stitched printing.

The **print** files are 216 × 303 mm sheets. Images and dark backgrounds run into the 3 mm bleed, and each page carries a TrimBox at A4 (210 × 297 mm). Photographs are placed at 235 ppi (kitchen pages) to 254 ppi (covers and full-page images). The files are RGB: the printer converts them with their own CMYK profile. The **presentation** files are trimmed A4 with lighter images, for screens, email and showroom tablets.

All eight files are PDF 1.4 with embedded TrueType fonts, document metadata (including the document language) and bookmarks (sections, ranges and every model).

**Before printing, read `CONFIRMATION_NOTES.md`.** It lists every item marked † in the catalogues: information that is unclear or inconsistent in the source and needs the supplier's confirmation.

## Bahasa Indonesia editions

The Indonesian editions have the same pages, page numbers, images and drawings as the English ones. All text is translated, including the specification labels, bookmarks and PDF metadata. Colour names follow the website: Hitam Mutiara, Putih Murni, Abu Titanium. Product and trade terms stay in English, as in the source records: Pressed, Hand Made, Inset Edge, Flat Edge, the finish names, the brands, and undermount and top-mount.

Where the English edition prints "TBC", the Indonesian prints "?" with the same † note, because "TBC" usually means tuberculosis in Indonesian.

**The translation was made with AI and has not been checked by a native speaker.** Have it proofread before printing.

## On the website

The website (`index.html`, published with GitHub Pages) offers the presentation editions in English and Indonesian from the `catalogue/` folder beside it. They are stored there under the file names the site expects, with three page images of each for its "Look inside" panel. `layout/publish_site.py` copies the files there. It also writes their page counts, file sizes and every model's page number into `index.html`, so "View in the catalogue" opens the right page. See `catalogue/HOW-TO-UPDATE.txt`.

## What's inside each volume

- **Cover.** A full-bleed kitchen image with the collection's title set large.
- **Introduction and contents.** Key figures and page references.
- **The collection.** Every model at a glance, with page numbers.
- **Colours (granite) or Finishes (stainless steel).** Each one is shown in one of the volume's kitchens and as photographed, with the models that come in it.
- **Pressed and Hand Made (stainless steel).** The two ranges side by side, as listed: brands, steel, thickness, edge, finishes, layouts, heights and included items.
- **Sizes and layouts.** Every model drawn to the same scale (1:15 for granite, 1:25 for stainless steel on the printed page), grouped by bowl layout, with a key to the marks on the drawings. Each drawing links to its model's page.
- **Installation (granite).** Undermount and top-mount, and which models are made for each.
- **Supplied with the sink (stainless steel).** The four Hand Made models that come with a listed accessory: the 5 Modes Spray, the 2 Tempered Glasses and the Tempered Glasses Wing.
- **Range openers (stainless steel).** Pressed and Hand Made.
- **One feature page per model.** A lifestyle image of the sink installed in a kitchen of its own, with:
  - the model code, the bowl configuration and the installation or range;
  - an at-a-glance row: layout, installation or edge, overall size, colours or finish, and anything included, each with an icon, so models compare page to page;
  - a specification panel;
  - the available colours or the finish, using the supplied product photographs;
  - a technical drawing: a plan view, plus a front view where the height is listed, with the listed overall dimensions.
- **Index.** Every model, its key data and its page.
- **Notes, a closing image and the back cover.**

## Images

`images/` holds the full-resolution images (JPEG, sRGB) so they can also be used on the website and in social posts:

- `images/granite/` and `images/stainless/`: one kitchen per model, 2000 × 1600 px, named by model code and the colour or finish shown (for example `GDU-8145_Pearl-Black.jpg`, `W-7646-USS_Satin.jpg`);
- `images/editorial/`: the covers, range openers and the two closing images (2160 × 3031 px), the introduction images (2400 × 1500 px) and the image strips (2400 × 1040 px).

About the kitchens:

- Each of the 31 models has its own kitchen. The settings differ in palette, materials, layout (wall run, window wall, island), light and camera. Most are lit by daylight from a side window, some with sun across the worktop; a few by low evening sun. The sink is always clearly lit, so its shape, colour and finish read.
- Every sink was rebuilt in 3D from its listed dimensions and the measurements taken from its supplied product photograph: bowl layout, corner radii, drainboard ribs and pads, drains and deck fittings. It is shown in its own colour or finish.
- The granite sinks are installed as listed, undermount or top-mount. The Pressed stainless sinks are shown inset, and the Hand Made ones top-mounted or undermounted following the T or U in their model codes, which the price list does not confirm (see S5 in `CONFIRMATION_NOTES.md`).
- Taps, wastes, worktops and props are styling. Each volume says so in its notes.
- Props come to rest on whatever is under them (`render/physics.py`), and every scene is checked before rendering for objects that pass through or hang above one another (`tools/audit_scenes.py`): a tap clear of shelves and walls, fruit resting in its bowl, nothing floating.
- The ambient light and reflections come from the "Lebombo" HDR image from Poly Haven, released CC0 (`render/hdri/CREDITS.txt`).

## Rebuilding

Everything is generated from source in `source/`. It needs Python 3.13 with Blender 5 as a module (`bpy`), Pillow and pypdf, and Node with Playwright (Chromium).

1. `tools/extract.js` and `tools/build_data.py` read the product records and photographs from `index.html` into `layout/data/data.json`.
2. `render/` holds the Blender (`bpy`, Cycles) scene code: the sink models (`granite.py`, `pressed.py`, `handmade.py`, built from `granite_data.py` and `steel_data.py`), the kitchens (`kitchen.py`, `kit.py`, `props.py`, `mats.py`) and one recipe per model (`scenes_granite.py`, `scenes_steel.py`). Render one image with `python -m render.scene <recipe> <out.png> final` (about 10 to 20 minutes on four CPU cores; `tools/queue_v2.sh` renders the recipes listed in `audit/queue_v2.txt` in turn, into `renders/v2/`). `render/physics.py` settles the props, and `python tools/audit_scenes.py [recipe ...]` builds scenes without rendering them and lists any objects that pass through or float above one another. `render/texture.py` renders the dark stone used on the text pages and back covers.
3. `layout/` holds the page generator: `prepare_assets.py` prepares the images, `build.py` builds the HTML pages from the data, `drawings.py` makes the SVG technical drawings, `catalogue.css` is the design system, and `export_pdf.js` prints the pages to PDF (Chromium / Playwright). `check_layout.js` stops the build if any text collides with other text or runs into the 5 mm safety margin. `build.py` makes either language (`en` or `id`); `i18n.py` holds the Indonesian text, and the build stops if any text has no translation. `make_catalogues.sh` runs these steps in order and makes all eight PDFs: `make_catalogues.sh <renders> <photos> <logos> <work> <pdf out>`. `export_images.py` writes the `images/` folder.
4. `layout/publish_site.py <pdf out> <work> <website>` puts the presentation editions on the website (see above). It also needs `pdftoppm` (poppler-utils).

Typefaces: Montserrat (display, matching the wordmark) and Inter (text), both under the SIL Open Font License (texts in `layout/fonts/`). The static TrueType files in `layout/fonts/` were instanced from the Google Fonts variable fonts, so the PDFs embed ordinary TrueType subsets, which prepress accepts.

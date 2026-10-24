# Maju Terus Jaya — Kitchen Sink Catalogues, 2026

Two coordinated catalogue volumes, redesigned from the shop's two kitchen sink catalogues:

| Volume | Presentation / screen (A4) | Print (A4 + 3 mm bleed) |
|---|---|---|
| **01 · Granite Kitchen Sink Collection**: 6 models, 12 pages | `pdf/MTJ_Granite_Kitchen_Sink_Collection_Vol01.pdf` | `pdf/MTJ_Granite_Kitchen_Sink_Collection_Vol01_PRINT.pdf` |
| **02 · Stainless Steel Kitchen Sink Collection**: 25 models, 36 pages | `pdf/MTJ_Stainless_Steel_Kitchen_Sink_Collection_Vol02.pdf` | `pdf/MTJ_Stainless_Steel_Kitchen_Sink_Collection_Vol02_PRINT.pdf` |

Both page counts are multiples of four, for saddle-stitched printing.

The **print** files are 216 × 303 mm sheets. Images and dark backgrounds run into the 3 mm bleed, and each page carries a TrimBox at A4 (210 × 297 mm). The files are RGB: the printer converts them with their own CMYK profile. The **presentation** files are trimmed A4 with lighter images, for screens, email and showroom tablets.

**Before printing, read `CONFIRMATION_NOTES.md`.** It lists every item marked † in the catalogues: information that is unclear or inconsistent in the source and needs the supplier's confirmation.

## What's inside each volume

- **Cover.** A full-bleed kitchen image with the collection's title set large.
- **Introduction and contents.** Key figures and page references.
- **The collection.** Every model at a glance, with page numbers.
- **Colours (granite) or Finishes (stainless steel).** Each one is shown in one of the volume's kitchens and as photographed, with the models that come in it.
- **Range openers (stainless steel).** Pressed and Hand Made.
- **One feature page per model.** A lifestyle image of the sink installed in a kitchen of its own, with:
  - the model code, the bowl configuration and the installation or range;
  - a specification panel;
  - the available colours or the finish, using the supplied product photographs;
  - a technical drawing: a plan view, plus a front view where the height is listed, with the listed overall dimensions.
- **Index.** Every model, its key data and its page.
- **Notes and back cover.**

## Images

`images/` holds the full-resolution kitchen images (JPEG, sRGB), named by model code, so they can also be used on the website and in social posts.

- Each of the 31 models has its own kitchen. The settings differ in palette, materials, layout (wall run, window wall, island), light (morning sun, soft north light, evening) and camera.
- Every sink was rebuilt in 3D from its listed dimensions and the measurements taken from its supplied product photograph: bowl layout, corner radii, drainboard ribs and pads, drains and deck fittings. It is shown in its own colour or finish.
- Undermount, top-mount and inset sinks are each installed the way they are made to be fitted.
- Taps, wastes, worktops and props are styling. Each volume says so in its notes.

## Rebuilding

Everything is generated from source in `source/`:

1. `tools/extract.js` and `tools/build_data.py` read the product records and photographs from `index.html` into `layout/data/data.json`.
2. `render/` holds the Blender (`bpy`, Cycles) scene code: the sink models (`granite.py`, `pressed.py`, `handmade.py`, built from `granite_data.py` and `steel_data.py`), the kitchens (`kitchen.py`, `kit.py`, `props.py`, `mats.py`) and one recipe per model (`scenes_granite.py`, `scenes_steel.py`). Render one image with `python -m render.scene <recipe> <out.png> final`.
3. `layout/` holds the page generator: `prepare_assets.py` prepares the images, `build.py` builds the HTML pages from the data, `drawings.py` makes the SVG technical drawings, `catalogue.css` is the design system, and `export_pdf.js` prints the pages to PDF (Chromium / Playwright). `make_catalogues.sh` runs these steps in order.

Rendering needs Python 3.13 with Blender as a module (`pip install bpy==5.2.3`); point `BPY` at that interpreter for the batch scripts in `tools/`. The layout needs Python 3 with Pillow and pypdf, and Node with Playwright (Chromium).

Typefaces: Montserrat (display, matching the wordmark) and Inter (text), both under the SIL Open Font License, embedded in the PDFs.

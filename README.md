# Maju Terus Jaya — the website

Published with GitHub Pages at <https://jasonvw808-create.github.io/MTJ/>.

## What is where

| | |
|---|---|
| `index.src.html` | **The website's source**: every page, text, price, style and script. This is the file to edit. |
| `index.html`, `assets/` | The page visitors get, **built** from the source. Made on `main` by the publish workflow. Never edit them by hand: the next build overwrites them. They are not kept on working branches (`.gitignore`). |
| `tools/build.mjs` | The build. |
| `lib/` | React and PDF.js, served from the site itself. |
| `img/` | The site's pictures. |
| `catalogue/` | The catalogues' PDFs as the site offers them (`catalogue/HOW-TO-UPDATE.txt`). |
| `catalogues/` | The catalogue generator, its full-size images and the print editions (`catalogues/README.md`). Not published. |
| `.github/workflows/publish-to-website.yml` | Publishes every change (below). |

## Changing the website

1. Edit `index.src.html` (and add pictures to `img/` if needed).
2. Push the change to a `claude/…` branch, or commit it on `main`.

That is all. The publish workflow merges the branch into `main`, builds `index.html` and `assets/` there, and GitHub
Pages publishes `main`. The change is live in about two minutes. If the source has a mistake that stops the build,
nothing is published: the website stays as it was, and the run under the repository's **Actions** tab says what is wrong
and on which line.

## Looking at it on a computer first

```
npm ci            # once: installs the build's two tools (esbuild, Tailwind)
npm run build     # index.src.html → index.html and assets/
python3 -m http.server 8000
```

Then open <http://localhost:8000/>. Run `npm run build` again after each change to the source.

`index.src.html` also opens in a browser as it is, with no build: it then compiles itself on every visit, which takes
several seconds and needs the internet (for React, Babel and Tailwind). The build exists so that visitors never wait
for that.

## What the build does

`tools/build.mjs` reads `index.src.html` and writes `index.html` with the work a browser would otherwise repeat on
every visit already done:

- the page's code (the `<script type="text/babel">` block) is compiled and minified into `assets/app.js`;
- the pictures that code carries inside itself (the logo, the sinks' photographs) become files in `assets/img/`;
- the Tailwind classes the page uses are compiled into a stylesheet set in the page, from the configuration the source
  itself carries (`tailwind.config = { … }`);
- React is loaded from `lib/react/` instead of a CDN.

Everything else is copied as it is. `assets/` belongs to the build: whatever it did not make is removed from it, so
nothing should be put there by hand. Its files are asked for with `?v=…` (a stamp of their contents), so a visitor's
browser fetches a changed file at once.

One rule follows from compiling Tailwind ahead of time: a class name must be written out whole somewhere in the source
(`"grid-cols-3"`, not `"grid-cols-" + n`), or its style is not in the built page.

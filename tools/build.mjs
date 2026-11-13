// The website's build: index.src.html (the source, which a browser can also open as it is) → index.html, the page
// visitors get, with everything a browser used to do on every visit done once here:
//
//   · the page's code (the <script type="text/babel"> block, JSX) is compiled and minified into assets/app.js, so no
//     browser has to load Babel and compile 1.9 MB of source before it can show anything;
//   · the pictures that code carries inside itself (the logo, the sinks' photographs, the granite's grain) become
//     files of their own in assets/img/, so the code is a fraction of the size and the pictures load as they are needed;
//   · the Tailwind classes the page uses are compiled into a stylesheet set in the page (after the page's own styles,
//     where the Tailwind CDN put its own), from the very configuration the source carries;
//   · React comes from lib/react/ beside the page rather than from a CDN.
//
// Nothing else is touched: the page's own styles, the showroom's engine and every other script are copied as they are.
// assets/ is this build's own folder: whatever it did not make this time is removed from it. Its files keep their
// names from one build to the next and are asked for with ?v=<a hash of their contents> (as the door pictures are):
// a changed file is fetched afresh at once, and a page a browser kept from before never asks for a file that is gone.
//
//   npm ci && npm run build            (the publish workflow does this on main; see .github/workflows)
//   node tools/build.mjs --check       builds in memory and says whether index.html and assets/ are up to date
import { readFileSync, writeFileSync, mkdirSync, readdirSync, rmSync, existsSync } from "node:fs";
import { createHash } from "node:crypto";
import { fileURLToPath } from "node:url";
import path from "node:path";
import * as esbuild from "esbuild";
import postcss from "postcss";
import tailwind from "tailwindcss";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const SRC = path.join(ROOT, "index.src.html"), OUT = path.join(ROOT, "index.html"), ASSETS = path.join(ROOT, "assets");
const check = process.argv.includes("--check");
const fail = (msg) => { console.error("build: " + msg); process.exit(1); };
const sha = (data) => createHash("sha256").update(data).digest("hex");
const kb = (n) => (n / 1024).toFixed(0) + " KB";
/* one, and only one, of a thing in the source: a build that guesses is worse than one that stops */
const once = (html, re, what) => {
  const m = html.match(new RegExp(re.source, re.flags.replace("g", "") + "g"));
  if (!m || m.length !== 1) fail("expected exactly one " + what + " in index.src.html, found " + (m ? m.length : 0));
  return html.match(re);
};

if (!existsSync(SRC)) fail("index.src.html is not here");
let html = readFileSync(SRC, "utf8");
const eol = html.includes("\r\n") ? "\r\n" : "\n";

// ── 1 · the pictures in the code: every data: URI of any size becomes a file, named after the constant or the key it
//       stands under (LOGO_INK → logo-ink.webp, "gdu-8145-pearl-black" → gdu-8145-pearl-black.webp) ───────────────
const app = once(html, /<script type="text\/babel" data-presets="react">([\s\S]*?)<\/script>/, "text/babel script");
const line0 = html.slice(0, app.index).split("\n").length;          // the line of index.src.html the code starts on
const EXT = { webp: "webp", jpeg: "jpg", png: "png", avif: "avif", gif: "gif" };
const pics = new Map(), byName = {};          // file → its bytes; constant → the address the page asks for it at
const jsx = app[1].replace(
  /((?:\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*|"([\w.-]+)"\s*:\s*)?)"data:image\/(webp|jpeg|png|avif|gif);base64,([A-Za-z0-9+\/]{1024,}={0,2})"/g,
  (all, lead, constant, key, type, b64) => {
    const bytes = Buffer.from(b64, "base64");
    const slug = (constant || key || "picture").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || "picture";
    /* two pictures under one name (the three "grain"s): the later ones are numbered, in the order they stand in */
    let file = "assets/img/" + slug + "." + EXT[type];
    for (let n = 2; pics.has(file) && !pics.get(file).equals(bytes); n++) file = "assets/img/" + slug + "-" + n + "." + EXT[type];
    pics.set(file, bytes);
    const url = file + "?v=" + sha(bytes).slice(0, 8);
    if (constant) byName[constant] = url;
    return lead + JSON.stringify(url);
  });
const left = jsx.match(/data:[a-z]+\/[a-z0-9.+-]+;base64,[A-Za-z0-9+\/]{1024,}/g);
if (left) console.warn("build: " + left.length + " data: URI(s) in the code were not in a plain \"…\" string and stay inside it");

// ── 2 · the page's code: JSX → JavaScript, minified; names at the top level are kept (other scripts and the page's
//       tests read them), as in a script Babel compiled in the browser ─────────────────────────────────────────────
const at = (loc) => (loc ? " (index.src.html, line " + (loc.line + line0 - 1) + ")" : "");
const js = await esbuild.transform(jsx, {
  loader: "jsx", jsx: "transform", jsxFactory: "React.createElement", jsxFragment: "React.Fragment",
  minify: true, target: "es2020", charset: "utf8", legalComments: "none", sourcefile: "index.src.html", logLevel: "silent",
}).catch((e) => fail("the page's code does not compile:\n" + (e.errors || []).map((x) => "  " + x.text + at(x.location)).join("\n") || e.message));
for (const w of js.warnings) console.warn("build: " + w.text + at(w.location));
const code = "/* Maju Terus Jaya — the website's code, compiled from index.src.html by tools/build.mjs. Edit the source, not this. */\n" + js.code;
const appFile = "assets/app.js", appUrl = appFile + "?v=" + sha(code).slice(0, 10);

// ── 3 · Tailwind: the classes the source uses, with the configuration the source itself carries ────────────────
const cdn = once(html, /<script src="https:\/\/cdn\.tailwindcss\.com"><\/script>\s*<script>\s*tailwind\.config\s*=\s*(\{[\s\S]*?\})\s*<\/script>/, "Tailwind CDN script with its configuration");
let config;
try { config = new Function("return (" + cdn[1] + ");")(); } catch (e) { fail("the Tailwind configuration in the source cannot be read: " + e.message); }
const tw = await postcss([tailwind({ ...config, content: [{ raw: html, extension: "html" }] })])
  .process("@tailwind base;\n@tailwind components;\n@tailwind utilities;\n", { from: undefined })
  .catch((e) => fail("Tailwind could not compile: " + e.message));
const css = (await esbuild.transform(tw.css, { loader: "css", minify: true, charset: "utf8", legalComments: "none" })).code.trim();

// ── 4 · the page ────────────────────────────────────────────────────────────────────────────────────────────────
const cdnjs = once(html, /<script src="https:\/\/cdnjs\.cloudflare\.com\/ajax\/libs\/react\/[^"]+\/umd\/react\.production\.min\.js"><\/script>\s*<script src="https:\/\/cdnjs\.cloudflare\.com\/ajax\/libs\/react-dom\/[^"]+\/umd\/react-dom\.production\.min\.js"><\/script>\s*<script src="https:\/\/cdnjs\.cloudflare\.com\/ajax\/libs\/babel-standalone\/[^"]+\/babel\.min\.js"><\/script>/, "set of React, ReactDOM and Babel script tags");
const REACT = ["lib/react/react.production.min.js", "lib/react/react-dom.production.min.js"];
for (const f of REACT) if (!existsSync(path.join(ROOT, f))) fail(f + " is missing");
html = html
  .replace(cdn[0], () => "<!-- Tailwind: compiled by tools/build.mjs, set at the end of the head -->")
  .replace(cdnjs[0], () => REACT.map((f) => '<script src="' + f + '"></script>').join(eol))
  .replace(app[0], () => '<script src="' + appUrl + '"></script>');
/* asked for from the head, so they are on their way while the rest of the page is still arriving: the scripts, and the
   logo the header opens with (the light drawing, whole and as the mark alone: the header carries both) */
const early = [...REACT, appUrl].map((f) => '<link rel="preload" as="script" href="' + f + '">')
  .concat(["LOGO_LIGHT", "LOGO_MARK_LIGHT"].filter((n) => byName[n]).map((n) => '<link rel="preload" as="image" href="' + byName[n] + '">'));
once(html, /<\/head>/, "</head>");
html = html.replace("</head>", () => early.join(eol) + eol + "<style data-tailwind>" + css + "</style>" + eol + "</head>");
once(html, /<!DOCTYPE html>/i, "doctype");
html = html.replace(/<!DOCTYPE html>/i, (d) => d + eol + "<!-- Built from index.src.html by tools/build.mjs. Edit the source, not this file. -->");
if (/text\/babel|cdn\.tailwindcss\.com|babel\.min\.js/.test(html)) fail("the built page still asks for Babel or the Tailwind CDN");

// ── 5 · written out; and assets/ holds nothing but what this build made ──────────────────────────────────────────
const made = new Map([[appFile, code], ...pics]);
const inAssets = (dir = ASSETS, rel = "assets/") => (existsSync(dir) ? readdirSync(dir, { withFileTypes: true }) : [])
  .flatMap((e) => (e.isDirectory() ? inAssets(path.join(dir, e.name), rel + e.name + "/") : [rel + e.name]));
if (check) {
  const there = new Set(inAssets());
  const same = existsSync(OUT) && readFileSync(OUT, "utf8") === html && there.size === made.size &&
    [...made].every(([f, data]) => there.has(f) && Buffer.from(data).equals(readFileSync(path.join(ROOT, f))));
  console.log(same ? "index.html and assets/ are up to date" : "index.html or assets/ is NOT up to date with index.src.html: run npm run build");
  process.exit(same ? 0 : 1);
}
for (const f of inAssets()) if (!made.has(f)) rmSync(path.join(ROOT, f));
for (const [f, data] of made) { mkdirSync(path.dirname(path.join(ROOT, f)), { recursive: true }); writeFileSync(path.join(ROOT, f), data); }
writeFileSync(OUT, html);
console.log("built index.html " + kb(Buffer.byteLength(html)) + " · " + appFile + " " + kb(Buffer.byteLength(code)) + " · Tailwind " + kb(Buffer.byteLength(css)) +
  " · " + pics.size + " pictures " + kb([...pics.values()].reduce((n, b) => n + b.length, 0)) + " (source " + kb(Buffer.byteLength(readFileSync(SRC))) + ")");

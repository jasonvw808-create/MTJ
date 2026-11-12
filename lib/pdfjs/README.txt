PDF.js, BESIDE THE WEBSITE
==========================

  pdf.min.mjs           PDF.js 5.7.284, its legacy build (an ES module, for older phones too)
  pdf.worker.min.mjs    its worker
  LICENSE               Apache License 2.0 (Mozilla Foundation)

From the npm package pdfjs-dist@5.7.284, legacy/build/, unchanged.

The Catalogue page (#/catalogue) uses it where a browser has no PDF viewer of its own (most Android phones, which
would only download a PDF): there a catalogue's cover opens the site's own reader, which draws the PDF's pages full
screen with it. It is loaded only then, is only ever given the site's own catalogues, and runs with eval turned off.
A browser that shows PDFs itself (a computer's; Safari on an iPhone) opens the file in a tab and never loads it.

To update it: take legacy/build/pdf.min.mjs and pdf.worker.min.mjs from a newer pdfjs-dist, put them here under
the same names, and check the Catalogue page on a phone. (Version 3, whose builds are not modules, cannot draw the
catalogues' gradients: their covers come out pink.)

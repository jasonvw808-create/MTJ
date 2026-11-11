PDF.js, BESIDE THE WEBSITE
==========================

  pdf.min.mjs           PDF.js 5.7.284, its legacy build (an ES module, for older phones too)
  pdf.worker.min.mjs    its worker
  LICENSE               Apache License 2.0 (Mozilla Foundation)

From the npm package pdfjs-dist@5.7.284, legacy/build/, unchanged.

The Catalogue page (#/catalogue) uses it on a phone, where a browser cannot show a PDF inside a page: it draws the
catalogue's pages from the PDF itself, one at a time, and, on a phone with no viewer of its own, full screen for
View Catalogue. It is loaded only there, is only ever given the site's own catalogues, and runs with eval turned off.
A computer's browser shows the PDF with its own viewer and never loads it.

To update it: take legacy/build/pdf.min.mjs and pdf.worker.min.mjs from a newer pdfjs-dist, put them here under
the same names, and check the Catalogue page on a phone. (Version 3, whose builds are not modules, cannot draw the
catalogues' gradients: their covers come out pink.)

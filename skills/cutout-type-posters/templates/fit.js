// fit.js: the shared layout pass. Include it as the LAST script in <body>.
//
// A page may set these before including it:
//   window.FACES    = ['900 100px "Archivo"', ...]  every font face the page uses (weight, any size, family)
//   window.afterFit = () => { ... }                   page-specific work once everything below is done
//
// Steps, in order:
//   1. Wait until every face in window.FACES has really loaded. Sizing text in a fallback font is wrong.
//   2. [data-fit="<px>"]: set font-size so the element's text is exactly <px> wide. The width is measured
//      over the text itself with a Range, not the element's box, so padding and block width don't count.
//   3. img[data-put="scale,srcX,srcY,dstX,dstY"]: show the whole photo at `scale` (width = naturalWidth *
//      scale) and move it so photo pixel (srcX,srcY), in the photo's own 1:1 pixels, lands at (dstX,dstY)
//      CSS px inside the image's positioned parent. Add data-cover to also check that the photo fills that
//      parent completely (for crops in a box); a gap is reported as an error.
//   4. window.afterFit(), then body.dataset.ready = '1'.
// Rotate or transform things in afterFit, never before: a Range over rotated text measures the rotated box.
//
// If anything fails (a {{PLACEHOLDER}} left in the copy, a font that didn't load, a missing image, a crop
// that leaves a gap, or a page that set body.dataset.error itself), a red banner with the reason is drawn over the poster, so a broken render
// can't pass for a good one, and body.dataset.error holds the message.
(async () => {
  const fail = (msg) => {
    console.error('fit.js: ' + msg);
    document.body.dataset.error = msg;
    const b = document.createElement('div');
    b.textContent = 'RENDER ERROR: ' + msg;
    b.style.cssText = 'position:fixed;left:0;top:0;width:1080px;box-sizing:border-box;padding:24px 32px;z-index:99999;' +
      'background:#E00000;color:#fff;font:700 28px/1.3 Arial,sans-serif;text-transform:none;white-space:normal';
    document.body.appendChild(b);
  };
  try {
    if (document.body.dataset.error) throw new Error(document.body.dataset.error);
    const unfilled = document.body.innerText.match(/\{\{[A-Z0-9_]+\}\}/g);
    if (unfilled) throw new Error('unfilled placeholders: ' + [...new Set(unfilled)].join(' '));

    // 1. fonts
    const faces = window.FACES || [];
    const loaded = await Promise.all(faces.map((f) => document.fonts.load(f).catch(() => [])));
    const missing = faces.filter((f, i) => loaded[i].length === 0);
    if (missing.length) throw new Error('font did not load (offline, or a family not linked in <head>?): ' + missing.join(', '));
    await document.fonts.ready;

    // 2. fit text widths
    for (const el of document.querySelectorAll('[data-fit]')) {
      el.style.fontSize = '100px';
      const r = document.createRange(); r.selectNodeContents(el);
      const w = r.getBoundingClientRect().width;
      if (!w) throw new Error('nothing to measure in a data-fit element (empty text?)');
      el.style.fontSize = (100 * parseFloat(el.dataset.fit) / w) + 'px';
    }

    // 3. place photos
    const imgs = [...document.querySelectorAll('img[data-put]')];
    await Promise.all(imgs.map((img) => img.decode().catch(() => {
      throw new Error('image did not load: ' + img.getAttribute('src') + ' (run prep.sh into assets/ first?)');
    })));
    for (const img of imgs) {
      const v = img.dataset.put.split(',').map(Number);
      if (v.length !== 5 || v.some(isNaN)) throw new Error('bad data-put "' + img.dataset.put + '" (want scale,srcX,srcY,dstX,dstY)');
      const [s, sx, sy, X, Y] = v;
      const left = X - sx * s, top = Y - sy * s, w = img.naturalWidth * s, h = img.naturalHeight * s;
      Object.assign(img.style, { position: 'absolute', width: w + 'px', height: h + 'px', left: left + 'px', top: top + 'px' });
      if (img.hasAttribute('data-cover')) {
        const p = img.parentElement, pw = p.clientWidth, ph = p.clientHeight, e = 0.5;
        if (left > e || top > e || left + w < pw - e || top + h < ph - e)
          throw new Error(`photo leaves a gap in its ${Math.round(pw)}x${Math.round(ph)} crop box ` +
            `(photo spans x ${left.toFixed(0)}..${(left + w).toFixed(0)}, y ${top.toFixed(0)}..${(top + h).toFixed(0)}): ` +
            'raise the scale or move the source point');
      }
    }

    // 4. page-specific finishing
    if (window.afterFit) await window.afterFit();
    if (document.body.dataset.error) throw new Error(document.body.dataset.error);
    document.body.dataset.ready = '1';
  } catch (err) {
    fail(err && err.message ? err.message : String(err));
  }
})();

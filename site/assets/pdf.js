/* A PDF writer, in about three hundred lines and with nothing behind it.
 *
 * The shopping list has to arrive as a PDF, and this site makes no external
 * requests — no CDN, no library, nothing to load. So the file is written here,
 * byte by byte, using the fourteen fonts every PDF reader already has. Nothing
 * is embedded and nothing is fetched.
 *
 * Two things about that are easy to get wrong and silent when you do:
 *
 *   1. A JavaScript string is not bytes. `new Blob([str])` encodes as UTF-8, so
 *      one `é` becomes two bytes, every byte offset after it is wrong, and the
 *      file is broken everywhere except Preview, which quietly repairs it while
 *      you are testing. Every byte here goes through `enc`, which throws on
 *      anything above 0xFF rather than letting it through.
 *   2. The cross-reference table is fixed-width. Each entry is exactly twenty
 *      bytes including a two-byte line ending, and one short entry misaligns
 *      every entry after it.
 *
 * Verified with `qpdf --check`, `mutool draw` and the CUPS filter chain, not
 * only by opening it.
 */
(() => {
  'use strict';

  const PAGE = { w: 595.28, h: 841.89 };          // A4
  const M = { l: 46, r: 46, t: 50, b: 58 };
  const GUTTER = 26;
  const COL_W = (PAGE.w - M.l - M.r - GUTTER) / 2;
  const COL_X = [M.l, M.l + COL_W + GUTTER];
  const RIGHT = PAGE.w - M.r;

  /* A4 is 50pt taller than US Letter. Anything below this line falls off the
     page when somebody prints at Actual Size on Letter, so nothing goes there. */
  const LETTER_FLOOR = 49.89;

  // ------------------------------------------------------------------ bytes

  function enc(byteStr) {
    const b = new Uint8Array(byteStr.length);
    for (let i = 0; i < byteStr.length; i++) {
      const c = byteStr.charCodeAt(i);
      if (c > 0xFF) {
        throw new Error('U+' + c.toString(16).toUpperCase() +
          ' reached the writer without being transliterated: ' +
          byteStr.slice(Math.max(0, i - 12), i + 12));
      }
      b[i] = c;
    }
    return b;
  }

  class Out {
    constructor() { this.parts = []; this.n = 0; }
    put(s) { return this.putBytes(enc(s)); }
    putBytes(b) { this.parts.push(b); this.n += b.length; return this; }
    get pos() { return this.n; }
    blob() { return new Blob(this.parts, { type: 'application/pdf' }); }
  }

  /* PDF has no exponent notation, so `1e-7` in a coordinate would end the
     content stream and take the rest of the page with it. */
  function num(v) {
    if (!Number.isFinite(v)) throw new Error('non-finite coordinate: ' + v);
    const s = v.toFixed(3).replace(/\.?0+$/, '');
    return (s === '' || s === '-0') ? '0' : s;
  }

  // --------------------------------------------------------------- encoding

  /* WinAnsi is Latin-1 for 0xA0-0xFF and differs above that. These are the
     characters this cookbook actually contains. */
  const WINANSI = new Map([
    [0x2018, 0x91], [0x2019, 0x92], [0x201C, 0x93], [0x201D, 0x94],
    [0x2022, 0x95], [0x2013, 0x96], [0x2014, 0x97], [0x2026, 0x85],
    [0x00A0, 0x20],
  ]);

  /* No base-14 font has a glyph for these, whatever encoding you choose, so
     they are spelled out instead of silently dropped. */
  const SPELLED = new Map([
    [0x2153, '1/3'], [0x2154, '2/3'], [0x215B, '1/8'], [0x215C, '3/8'],
    [0x215D, '5/8'], [0x215E, '7/8'], [0x2155, '1/5'], [0x2156, '2/5'],
    [0x2044, '/'], [0x2212, '-'], [0x00AD, '-'], [0x2010, '-'], [0x2011, '-'],
    [0x2009, ' '], [0x202F, ' '], [0x2032, "'"], [0x2033, '"'],
  ]);

  function winAnsi(str) {
    let out = '';
    // NFC first: a decomposed é from a file edited on a Mac would otherwise
    // arrive as e + a combining accent and lose the accent.
    for (const ch of String(str == null ? '' : str).normalize('NFC')) {
      const cp = ch.codePointAt(0);
      if (cp < 0x80) { out += ch; continue; }
      const b = WINANSI.get(cp);
      if (b !== undefined) { out += String.fromCharCode(b); continue; }
      if (cp >= 0xA0 && cp <= 0xFF) { out += ch; continue; }
      const spelled = SPELLED.get(cp);
      if (spelled === undefined) { out += '?'; continue; }
      // `2⅔ cups` is a mixed number. Splicing `2/3` straight in would make it
      // `22/3 cups`, which is a different amount, so the space goes back.
      if (/\d$/.test(out) && /^\d/.test(spelled)) out += ' ';
      out += winAnsi(spelled);
    }
    return out;
  }

  /* Only three characters have to be escaped inside a literal string, but
     everything outside printable ASCII is escaped too, so the content streams
     stay 7-bit and the byte-counting problem is confined to one function.
     The octal is always three digits: `\3` followed by a `5` would parse as
     the single character `\35`. */
  function lit(byteStr) {
    let s = '(';
    for (let i = 0; i < byteStr.length; i++) {
      const b = byteStr.charCodeAt(i);
      if (b === 0x28) s += '\\(';
      else if (b === 0x29) s += '\\)';
      else if (b === 0x5C) s += '\\\\';
      else if (b < 0x20 || b > 0x7E) s += '\\' + b.toString(8).padStart(3, '0');
      else s += String.fromCharCode(b);
    }
    return s + ')';
  }

  // ----------------------------------------------------------------- widths

  /* Helvetica advance widths in thousandths of an em, from the Adobe metrics.
     There is no way to measure text in a browser without a canvas, and a canvas
     measures the browser's Helvetica rather than the reader's, so the numbers
     have to be carried. Only Helvetica: everything that is measured — the
     quantity column, the page number, the wrapped item names — is set in it,
     and everything bold is left-aligned and short. */
  const HELV = {
    32: 278, 33: 278, 34: 355, 35: 556, 36: 556, 37: 889, 38: 667, 39: 191,
    40: 333, 41: 333, 42: 389, 43: 584, 44: 278, 45: 333, 46: 278, 47: 278,
    48: 556, 49: 556, 50: 556, 51: 556, 52: 556, 53: 556, 54: 556, 55: 556,
    56: 556, 57: 556, 58: 278, 59: 278, 60: 584, 61: 584, 62: 584, 63: 556,
    64: 1015, 65: 667, 66: 667, 67: 722, 68: 722, 69: 667, 70: 611, 71: 778,
    72: 722, 73: 278, 74: 500, 75: 667, 76: 556, 77: 833, 78: 722, 79: 778,
    80: 667, 81: 778, 82: 722, 83: 667, 84: 611, 85: 722, 86: 667, 87: 944,
    88: 667, 89: 667, 90: 611, 91: 278, 92: 278, 93: 278, 94: 469, 95: 556,
    96: 333, 97: 556, 98: 556, 99: 500, 100: 556, 101: 556, 102: 278, 103: 556,
    104: 556, 105: 222, 106: 222, 107: 500, 108: 222, 109: 833, 110: 556,
    111: 556, 112: 556, 113: 556, 114: 333, 115: 500, 116: 278, 117: 556,
    118: 500, 119: 722, 120: 500, 121: 500, 122: 500, 123: 334, 124: 260,
    125: 334, 126: 584,
    0x85: 1000, 0x91: 222, 0x92: 222, 0x93: 333, 0x94: 333, 0x95: 350,
    0x96: 556, 0x97: 1000, 0xB0: 400, 0xB7: 278, 0xBC: 834, 0xBD: 834,
    0xBE: 834, 0xC7: 722, 0xD7: 584, 0xE0: 556, 0xE1: 556, 0xE3: 556,
    0xE7: 500, 0xE8: 556, 0xE9: 556, 0xEC: 222, 0xED: 222, 0xEE: 222,
    0xEF: 222, 0xF1: 556, 0xF3: 556, 0xF6: 556, 0xF8: 556, 0xF9: 556,
    0xFC: 556,
  };

  const BOLD_FUDGE = 1.06;   // Helvetica-Bold runs a little wider than Helvetica

  function measure(byteStr, size, bold) {
    let w = 0;
    for (let i = 0; i < byteStr.length; i++) {
      w += HELV[byteStr.charCodeAt(i)] || 556;
    }
    return w * size / 1000 * (bold ? BOLD_FUDGE : 1);
  }

  /* Like wrap, but the first line may be narrower — for a paragraph that
     starts after a label sitting on the same line. */
  function wrapIndent(str, size, firstW, restW) {
    const words = String(str).split(/\s+/).filter(Boolean);
    const lines = [];
    let cur = '', width = firstW;
    for (const w of words) {
      const trial = cur ? cur + ' ' + w : w;
      if (measure(winAnsi(trial), size) <= width) { cur = trial; continue; }
      if (cur) { lines.push(cur); width = restW; }
      cur = w;
    }
    if (cur) lines.push(cur);
    return lines.length ? lines : [''];
  }

  function wrap(text, size, maxW) {
    const words = String(text).split(/\s+/).filter(Boolean);
    const lines = [];
    let cur = '';
    for (const w of words) {
      const trial = cur ? cur + ' ' + w : w;
      if (measure(winAnsi(trial), size) <= maxW) { cur = trial; continue; }
      if (cur) lines.push(cur);
      cur = w;
    }
    if (cur) lines.push(cur);
    return lines.length ? lines : [''];
  }

  // --------------------------------------------------------------- drawing

  /* The book's palette, so the sheet you print at home is recognisably the
     same object as the one on the shelf. `book/style.css` and `book/parse.py`
     are where these live; they are copied rather than derived because the
     stylesheet is not on the page that writes the PDF. */
  const C = {
    ink: '#1B201D', ink2: '#4B554E', ink3: '#828C84', ink4: '#A9B1A9',
    panel: '#F6F1E6', line: '#E2DACA', line2: '#EFE8D9',
    terracotta: '#C1502E', ochre: '#A5632A', green: '#5A7A48',
    tint: '#FAEDE7', white: '#FFFFFF',
  };

  function rgb(hex) {
    const n = parseInt(hex.slice(1), 16);
    return num(((n >> 16) & 255) / 255) + ' ' + num(((n >> 8) & 255) / 255) +
      ' ' + num((n & 255) / 255);
  }

  const F = { body: 'F1', bold: 'F2', serif: 'F3', serifBold: 'F4', italic: 'F5' };

  /* One text run. Colour is part of the call rather than a state left behind,
     because `rg` sets the fill for shapes and text alike and a rule drawn in
     grey would otherwise take the next paragraph with it. */
  function text(x, y, font, size, str, align, spacing, colour) {
    const bs = winAnsi(str);
    if (!bs) return '';
    const tc = spacing || 0;
    let w = 0;
    if (align) {
      w = measure(bs, size, font === F.bold) + tc * Math.max(0, bs.length - 1);
    }
    const tx = align === 'right' ? x - w : align === 'center' ? x - w / 2 : x;
    return 'BT\n/' + font + ' ' + num(size) + ' Tf\n' +
      (tc ? num(tc) + ' Tc\n' : '') +
      (colour ? rgb(colour) + ' rg\n' : '') +
      '1 0 0 1 ' + num(tx) + ' ' + num(y) + ' Tm\n' +
      lit(bs) + ' Tj\n' + (tc ? '0 Tc\n' : '') +
      (colour ? '0 0 0 rg\n' : '') + 'ET\n';
  }

  const widthOf = (str, size, bold, spacing) =>
    measure(winAnsi(str), size, bold) +
    (spacing || 0) * Math.max(0, winAnsi(str).length - 1);

  function rule(x1, x2, y, weight, colour) {
    return 'q\n' + num(weight) + ' w\n' + rgb(colour) + ' RG\n' +
      num(x1) + ' ' + num(y) + ' m ' + num(x2) + ' ' + num(y) + ' l S\nQ\n';
  }

  function box(x, y, w, h, colour) {
    return 'q\n' + rgb(colour) + ' rg\n' + num(x) + ' ' + num(y) + ' ' +
      num(w) + ' ' + num(h) + ' re\nf\nQ\n';
  }

  // A rounded rectangle, drawn as four bezier corners. 0.5523 is the constant
  // that makes a cubic curve indistinguishable from a quarter circle.
  function roundPath(x, y, w, h, r) {
    const k = r * 0.5523;
    const x2 = x + w, y2 = y + h;
    return num(x + r) + ' ' + num(y) + ' m\n' +
      num(x2 - r) + ' ' + num(y) + ' l\n' +
      num(x2 - r + k) + ' ' + num(y) + ' ' + num(x2) + ' ' + num(y + r - k) + ' ' +
      num(x2) + ' ' + num(y + r) + ' c\n' +
      num(x2) + ' ' + num(y2 - r) + ' l\n' +
      num(x2) + ' ' + num(y2 - r + k) + ' ' + num(x2 - r + k) + ' ' + num(y2) + ' ' +
      num(x2 - r) + ' ' + num(y2) + ' c\n' +
      num(x + r) + ' ' + num(y2) + ' l\n' +
      num(x + r - k) + ' ' + num(y2) + ' ' + num(x) + ' ' + num(y2 - r + k) + ' ' +
      num(x) + ' ' + num(y2 - r) + ' c\n' +
      num(x) + ' ' + num(y + r) + ' l\n' +
      num(x) + ' ' + num(y + r - k) + ' ' + num(x + r - k) + ' ' + num(y) + ' ' +
      num(x + r) + ' ' + num(y) + ' c\nh\n';
  }

  function roundBox(x, y, w, h, r, fill, strokeCol, weight) {
    let s = 'q\n';
    if (fill) s += rgb(fill) + ' rg\n';
    if (strokeCol) s += rgb(strokeCol) + ' RG\n' + num(weight || 0.8) + ' w\n';
    s += roundPath(x, y, w, h, r);
    s += (fill && strokeCol ? 'B\n' : fill ? 'f\n' : 'S\n') + 'Q\n';
    return s;
  }

  function circle(cx, cy, r, fill, strokeCol, weight) {
    const k = r * 0.5523;
    let s = 'q\n';
    if (fill) s += rgb(fill) + ' rg\n';
    if (strokeCol) s += rgb(strokeCol) + ' RG\n' + num(weight || 0.8) + ' w\n';
    s += num(cx - r) + ' ' + num(cy) + ' m\n' +
      num(cx - r) + ' ' + num(cy + k) + ' ' + num(cx - k) + ' ' + num(cy + r) + ' ' + num(cx) + ' ' + num(cy + r) + ' c\n' +
      num(cx + k) + ' ' + num(cy + r) + ' ' + num(cx + r) + ' ' + num(cy + k) + ' ' + num(cx + r) + ' ' + num(cy) + ' c\n' +
      num(cx + r) + ' ' + num(cy - k) + ' ' + num(cx + k) + ' ' + num(cy - r) + ' ' + num(cx) + ' ' + num(cy - r) + ' c\n' +
      num(cx - k) + ' ' + num(cy - r) + ' ' + num(cx - r) + ' ' + num(cy - k) + ' ' + num(cx - r) + ' ' + num(cy) + ' c\nh\n';
    s += (fill && strokeCol ? 'B\n' : fill ? 'f\n' : 'S\n') + 'Q\n';
    return s;
  }

  /* The book's method pill: filled with the method's own colour, the label in
     white small caps. The outlined variant carries `Vegetarian`. */
  const PILL_SIZE = 6.6, PILL_TRACK = 0.9, PILL_H = 12.5;

  function pill(x, y, label, fill, ink, border) {
    const w = widthOf(label.toUpperCase(), PILL_SIZE, true, PILL_TRACK) + 15;
    return {
      w,
      cs: roundBox(x, y - 3.6, w, PILL_H, PILL_H / 2, fill, border, 0.7) +
        text(x + 7.5, y, F.bold, PILL_SIZE, label.toUpperCase(), null, PILL_TRACK, ink),
    };
  }

  // The time dial from the recipe pages: minutes in a ring.
  function dial(cx, cy, minutes, colour) {
    return circle(cx, cy, 15.5, null, colour, 1.1) +
      text(cx, cy + 0.5, F.serifBold, 11, String(minutes), 'center', 0, colour) +
      text(cx, cy - 8, F.bold, 4.8, 'MIN', 'center', 1.1, colour);
  }

  // A section label: ochre small caps over a hairline, as in the book.
  function sectionLabel(x, y, w, label, colour) {
    return text(x, y, F.bold, 6.9, label.toUpperCase(), null, 1.05,
      colour || C.ochre) + rule(x, x + w, y - 5.5, 0.6, C.line);
  }

  function tickbox(x, baseline, size) {
    const s = Math.round(size * 0.78 * 2) / 2;
    return roundBox(x, baseline - 0.8, s, s, 1.6, C.white, C.ink4, 0.7);
  }

  // -------------------------------------------------------------- assembly

  const FONTS = [
    ['F1', 'Helvetica'], ['F2', 'Helvetica-Bold'], ['F3', 'Times-Roman'],
    ['F4', 'Times-Bold'], ['F5', 'Times-Italic'],
  ];

  function pdfDate(d) {
    const p = n => String(n).padStart(2, '0');
    const tz = -d.getTimezoneOffset();
    const sign = tz >= 0 ? '+' : '-';
    const a = Math.abs(tz);
    return 'D:' + d.getFullYear() + p(d.getMonth() + 1) + p(d.getDate()) +
      p(d.getHours()) + p(d.getMinutes()) + p(d.getSeconds()) +
      sign + p(Math.floor(a / 60)) + "'" + p(a % 60) + "'";
  }

  function assemble(streams, meta) {
    const objects = [];
    const FIRST_PAGE = 8;
    objects.push('<< /Type /Catalog /Pages 2 0 R >>');
    const kids = streams.map((_, i) => (FIRST_PAGE + 2 * i) + ' 0 R').join(' ');
    const fonts = FONTS.map((f, i) => '/' + f[0] + ' ' + (3 + i) + ' 0 R').join(' ');
    objects.push('<< /Type /Pages /Count ' + streams.length + ' /Kids [ ' + kids +
      ' ] /MediaBox [ 0 0 ' + num(PAGE.w) + ' ' + num(PAGE.h) + ' ] ' +
      '/Resources << /Font << ' + fonts + ' >> /ProcSet [ /PDF /Text ] >> >>');
    for (const [, base] of FONTS) {
      objects.push('<< /Type /Font /Subtype /Type1 /BaseFont /' + base +
        ' /Encoding /WinAnsiEncoding >>');
    }
    streams.forEach((cs, i) => {
      const pid = FIRST_PAGE + 2 * i;
      objects.push('<< /Type /Page /Parent 2 0 R /Contents ' + (pid + 1) + ' 0 R >>');
      const data = enc(cs);
      objects.push({ dict: '<< /Length ' + data.length + ' >>', data: data });
    });
    const infoId = objects.length + 1;
    objects.push('<< /Title ' + lit(winAnsi(meta.title)) +
      ' /Author ' + lit(winAnsi('The 20-Minute Table')) +
      ' /Producer ' + lit(winAnsi('The 20-Minute Table')) +
      ' /CreationDate ' + lit(pdfDate(new Date())) + ' >>');

    const out = new Out();
    out.put('%PDF-1.4\n');
    out.put('%âãÏÓ\n');   // four high bytes: this file is binary
    const offsets = new Array(objects.length + 1).fill(0);
    objects.forEach((o, i) => {
      const id = i + 1;
      offsets[id] = out.pos;
      out.put(id + ' 0 obj\n');
      if (typeof o === 'string') {
        out.put(o + '\n');
      } else {
        out.put(o.dict + '\nstream\n');
        out.putBytes(o.data);            // exactly /Length bytes, no more
        out.put('\nendstream\n');
      }
      out.put('endobj\n');
    });
    const xref = out.pos;
    const size = objects.length + 1;
    out.put('xref\n');
    out.put('0 ' + size + '\n');
    out.put('0000000000 65535 f\r\n');    // the head of the free list, twenty bytes
    for (let id = 1; id < size; id++) {
      out.put(String(offsets[id]).padStart(10, '0') + ' 00000 n\r\n');
    }
    out.put('trailer\n<< /Size ' + size + ' /Root 1 0 R /Info ' + infoId + ' 0 R >>\n');
    out.put('startxref\n' + xref + '\n%%EOF\n');
    return out.blob();
  }

  // ------------------------------------------------------------ the blocks

  /* A recipe is laid out as blocks — a heading, a paragraph, one ingredient,
     one step — rather than as one long string, so a column that runs out of
     room breaks between two of them instead of through the middle of a line.
     Every block knows its own height at a given width and draws itself.
     `k` is the fit scale: see fitRecipe. A block may name a `group`, which is
     how a tinted panel gets drawn behind a run of them however the run falls
     across the two columns. */

  function bGap(h) {
    return { h: () => h, draw: () => '' };
  }

  function bHead(label, k, colour) {
    return {
      h: () => 19 * k,
      // A heading alone at the foot of a column, with what it announces in the
      // next one, is the one break this layout must not make.
      keep: 2,
      draw: (x, y, w) => sectionLabel(x, y, w, label, colour),
    };
  }

  function bPara(str, font, size, lead, after, colour) {
    return {
      h: (w) => wrap(str, size, w).length * lead + (after || 0),
      draw: (x, y, w) => {
        const lines = wrap(str, size, w);
        return 'BT\n/' + font + ' ' + num(size) + ' Tf\n' + num(lead) + ' TL\n' +
          rgb(colour || C.ink2) + ' rg\n' +
          '1 0 0 1 ' + num(x) + ' ' + num(y) + ' Tm\n' +
          lines.map((l, i) => (i ? 'T*\n' : '') + lit(winAnsi(l)) + ' Tj\n').join('') +
          '0 0 0 rg\nET\n';
      },
    };
  }

  // An ingredient: a coloured dot, then the line, hanging so a wrapped second
  // line sits under the first rather than under the dot.
  function bItem(str, size, lead, colour, group) {
    const IND = 11;
    return {
      group,
      h: (w) => wrap(str, size, w - IND - 8).length * lead + 2.5,
      draw: (x, y, w) => {
        const lines = wrap(str, size, w - IND - 8);
        return circle(x + 3, y + size * 0.32, 1.7, colour) +
          'BT\n/' + F.body + ' ' + num(size) + ' Tf\n' + num(lead) + ' TL\n' +
          rgb(C.ink2) + ' rg\n1 0 0 1 ' + num(x + IND) + ' ' + num(y) + ' Tm\n' +
          lines.map((l, i) => (i ? 'T*\n' : '') + lit(winAnsi(l)) + ' Tj\n').join('') +
          '0 0 0 rg\nET\n';
      },
    };
  }

  function bGroupName(str, size, group) {
    return {
      group,
      h: () => size + 7,
      draw: (x, y) => text(x, y, F.bold, size * 0.82, str.toUpperCase(), null,
        0.9, C.ink3),
    };
  }

  // A method step: the book's filled numeral disc, then the text.
  function bStep(n, str, size, lead, colour) {
    const IND = 21;
    return {
      h: (w) => Math.max(wrap(str, size, w - IND).length * lead + 8, 20),
      draw: (x, y, w) => {
        const lines = wrap(str, size, w - IND);
        return circle(x + 6.4, y + size * 0.3, 6.6, colour) +
          text(x + 6.4, y + size * 0.3 - 2.3, F.bold, 6.6, String(n), 'center', 0, C.white) +
          'BT\n/' + F.body + ' ' + num(size) + ' Tf\n' + num(lead) + ' TL\n' +
          rgb(C.ink2) + ' rg\n1 0 0 1 ' + num(x + IND) + ' ' + num(y) + ' Tm\n' +
          lines.map((l, i) => (i ? 'T*\n' : '') + lit(winAnsi(l)) + ' Tj\n').join('') +
          '0 0 0 rg\nET\n';
      },
    };
  }

  /* A chef's note: the label in ochre small caps on its own line, the note
     under it, the way the book sets the four of them. */
  function bNote(label, str, size, lead) {
    return {
      h: (w) => wrap(str, size, w).length * lead + size + 9,
      draw: (x, y, w) => {
        const lines = wrap(str, size, w);
        return text(x, y, F.bold, size * 0.84, label.toUpperCase(), null, 0.95, C.ochre) +
          'BT\n/' + F.body + ' ' + num(size) + ' Tf\n' + num(lead) + ' TL\n' +
          rgb(C.ink2) + ' rg\n1 0 0 1 ' + num(x) + ' ' + num(y - size - 3) + ' Tm\n' +
          lines.map((l, i) => (i ? 'T*\n' : '') + lit(winAnsi(l)) + ' Tj\n').join('') +
          '0 0 0 rg\nET\n';
      },
    };
  }

  // The nutrition band: a tinted strip with hairline dividers, the figures in
  // terracotta serif with their unit tucked in beside them.
  function bMacros(macros, k) {
    const keys = ['calories', 'protein', 'carbs', 'fat', 'fibre'];
    const units = ['kcal', 'g', 'g', 'g', 'g'];
    return {
      h: () => 40 * k,
      draw: (x, y, w) => {
        const h = 36 * k;
        let out = roundBox(x, y - h + 11, w, h, 3, C.panel);
        const step = w / 5;
        macros.forEach((v, i) => {
          const cx = x + i * step + step / 2;
          const vw = widthOf(String(v), 12.5 * k, true);
          out += text(cx - vw / 2, y - 4, F.serifBold, 12.5 * k, String(v), null, 0, C.terracotta);
          out += text(cx - vw / 2 + vw + 1.5, y - 4, F.body, 5.6 * k, units[i], null, 0, C.ochre);
          out += text(cx, y - 15 * k, F.bold, 5.3 * k, keys[i].toUpperCase(), 'center', 1, C.ink3);
          if (i) out += box(x + i * step, y - h + 15, 0.6, h - 9, C.line);
        });
        return out;
      },
    };
  }

  /* Pour blocks into one column, stopping before the first that will not fit
     and handing the rest back. A block always gets one shot at an empty
     column, so nothing can loop for ever. Where a run of blocks shares a
     `group`, the span it occupied in this column is reported so a panel can
     be drawn behind it. */
  function fillColumn(blocks, x, top, w, bottom) {
    let cs = '', y = top, i = 0;
    const spans = {};
    for (; i < blocks.length; i++) {
      const b = blocks[i];
      let h = b.h(w);
      // A block that asks to be kept with what follows reserves their room too,
      // so a heading never ends a column with its first line in the next one.
      let need = h;
      for (let j = 1; b.keep && j <= b.keep && i + j < blocks.length; j++) {
        need += blocks[i + j].h(w);
      }
      if (y - need < bottom && y !== top) break;
      cs += b.draw(x, y, w);
      if (b.group) {
        const s = spans[b.group] || (spans[b.group] = { top: y, bottom: y });
        s.bottom = y - h;
      }
      y -= h;
    }
    return { cs, rest: blocks.slice(i), y, spans };
  }

  // ------------------------------------------------------------ the recipe

  function recipeBlocks(r, k, colour) {
    const b = [];
    const ing = 8.4 * k, ingL = 11 * k;
    const step = 8.5 * k, stepL = 11.5 * k;
    const body = 8.1 * k, bodyL = 10.6 * k;

    b.push(bHead('Ingredients', k));
    b.push(bGap(4 * k));
    for (const g of r.groups) {
      if (g.name) b.push(bGroupName(g.name, 8.4 * k, 'ing'));
      for (const item of g.items) b.push(bItem(item, ing, ingL, colour, 'ing'));
    }
    b.push(bGap(13 * k));
    b.push(bHead('Nutrition, a serving', k));
    b.push(bMacros(r.macros, k));
    b.push(bGap(6 * k));
    b.push(bHead('Why it works', k));
    b.push(bPara(r.why, F.body, body, bodyL, 13 * k));
    b.push(bHead('Method', k));
    b.push(bGap(3 * k));
    r.steps.forEach((s, i) => b.push(bStep(i + 1, s, step, stepL, colour)));
    b.push(bGap(7 * k));
    b.push(bHead('For the toddler', k, C.terracotta));
    b.push(bGap(4 * k));
    b.push(bPara(r.toddler, F.body, body, bodyL, 13 * k, C.ink2));
    b.push(bHead('Chef’s notes', k));
    b.push(bGap(4 * k));
    for (const [label, note] of r.notes) b.push(bNote(label, note, body, bodyL));
    b.push(bGap(6 * k));
    b.push(bHead('Washing up', k));
    b.push(bGap(3 * k));
    b.push(bPara(r.washing, F.body, body, bodyL, 0, C.ink3));
    return b;
  }

  /* The book's typesetter fits each recipe to its spread by searching one
     parameter that tightens the type until the page holds. This does the same,
     for the same reason: a recipe you cook from wants to be one sheet of
     paper, and a page and a fifth is the worst of both. */
  function fitRecipe(r, capacity, colour) {
    let k = 1;
    for (let i = 0; i < 10; i++) {
      const blocks = recipeBlocks(r, k, colour);
      let total = 0;
      for (const b of blocks) total += b.h(COL_W);
      if (total <= capacity || k <= 0.82) return { blocks, k };
      k = Math.round((k - 0.02) * 100) / 100;
    }
    return { blocks: recipeBlocks(r, k, colour), k };
  }

  const METHOD_COLOUR = {
    'Air Fryer': C.terracotta, 'One Pan': C.green, 'Wok': C.ochre,
    'No Cook': '#2C6B7B',
  };

  function recipePages(r, doc) {
    const colour = METHOD_COLOUR[r.ml] || C.terracotta;
    const TOP_BAND = 13;
    const BOTTOM = LETTER_FLOOR + 16;

    const hookLines = wrap(r.hook, 10.5, PAGE.w - M.l - M.r - 12);
    const ruleY = PAGE.h - 118 - hookLines.length * 14;
    const colTop = ruleY - 26;
    // Blocks do not split, and a heading reserves room for what follows it, so
    // the two column breaks each waste up to a heading and its first entries.
    // Ninety points of slack is what it takes for all fifty to hold one page.
    const capacity = (colTop - BOTTOM) * 2 - 90;

    const fit = fitRecipe(r, capacity, colour);
    const pages = [];
    let rest = fit.blocks;
    let first = true;

    const foot = () => {
      const bits = [r.ml, r.time, 'Serves ' + r.serves];
      return rule(M.l, RIGHT, LETTER_FLOOR + 22, 0.6, C.line) +
        fitted(M.l, LETTER_FLOOR + 12, F.bold, 6.4,
          bits.join('   ·   ').toUpperCase(), RIGHT - M.l - 70, 5, 'left', colour);
    };

    while (rest.length) {
      let cs = box(0, PAGE.h - TOP_BAND, PAGE.w, TOP_BAND, colour);
      let top;
      if (first) {
        const numW = widthOf(r.n, 30, true);
        cs += text(M.l, PAGE.h - 62, F.serifBold, 30, r.n, null, 0, colour);
        const tx = M.l + numW + 14;
        const titleW = RIGHT - tx - 44;
        cs += fitted(tx, PAGE.h - 58, F.serifBold, 19, r.t, titleW, 13, 'left', C.ink);

        // the meta row: the method pill, then the plain facts, then Vegetarian
        let mx = tx;
        const p = pill(mx, PAGE.h - 78, r.ml, colour, C.white);
        cs += p.cs; mx += p.w + 9;
        const facts = [r.c, r.time, 'Serves ' + r.serves].join('   ·   ').toUpperCase();
        cs += text(mx, PAGE.h - 78, F.body, 6.6, facts, null, 1, C.ink3);
        mx += widthOf(facts, 6.6, false, 1) + 9;
        if (r.veg) {
          cs += pill(mx, PAGE.h - 78, 'Vegetarian', null, C.green, C.green).cs;
        }
        cs += dial(RIGHT - 16, PAGE.h - 62, r.min || parseInt(r.time, 10), colour);

        let y = PAGE.h - 104;
        cs += box(M.l, ruleY + 8, 1.6, y - ruleY + 2, colour);
        for (const line of hookLines) {
          cs += text(M.l + 12, y, F.italic, 10.5, line, null, 0, colour);
          y -= 14;
        }
        cs += rule(M.l, RIGHT, ruleY, 0.7, C.line);
        top = colTop;
        first = false;
      } else {
        cs += text(M.l, PAGE.h - 40, F.bold, 6.6,
          (r.n + ' · ' + r.t + ' · continued').toUpperCase(), null, 1, C.ink3);
        top = PAGE.h - 62;
      }

      const a = fillColumn(rest, COL_X[0], top, COL_W, BOTTOM);
      const b = fillColumn(a.rest, COL_X[1], top, COL_W, BOTTOM);
      // Panels go behind the text, so they are composed before it.
      let panels = '';
      [[a, 0], [b, 1]].forEach(([col, i]) => {
        const s = col.spans.ing;
        if (s) {
          panels += roundBox(COL_X[i] - 7, s.bottom - 3, COL_W + 14,
            s.top - s.bottom + 16, 3, C.panel);
        }
      });
      cs += panels + a.cs + b.cs + foot();
      rest = b.rest;
      pages.push(cs);
      if (pages.length > 4) break;
    }
    return pages;
  }

  // ----------------------------------------------------- the shopping list

  const LEAD = 12.5;
  const SIZE = 9.5;
  const BOX_W = 15;
  const QTY_W = 54;
  const nameX = c => COL_X[c] + BOX_W + QTY_W + 7;
  const nameW = COL_W - BOX_W - QTY_W - 7;
  const qtyR = c => COL_X[c] + BOX_W + QTY_W;

  /* Text that has to end before a given point: the size comes down in quarter
     points until it does. Nothing is ever allowed to draw past its boundary. */
  function shrinkToFit(str, size, maxW, min) {
    let s = size;
    while (s > min && measure(winAnsi(str), s) > maxW) s -= 0.25;
    return s;
  }

  function fitted(x, y, font, size, str, maxW, min, align, colour, spacing) {
    return text(x, y, font, shrinkToFit(str, size, maxW, min), str,
      align || 'right', spacing || 0, colour);
  }

  /* A quantity can be two amounts joined — `6 × 200 g tins + 8 × 160 g tins` —
     and no size that is still readable will fit that on one line. It comes
     down to the floor first and then wraps, right-aligned, rather than
     overrunning into the tick box. */
  function qtyBlock(x, y, str, maxW, size, min, lead) {
    const s = shrinkToFit(str, size, maxW, min);
    // Two amounts joined by a plus break at the plus, not wherever the words
    // happen to fall.
    const lines = measure(winAnsi(str), s) <= maxW ? [str]
      : (str.includes(' + ')
        ? str.split(' + ').map((part, i, all) => i < all.length - 1 ? part + ' +' : part)
        : wrap(str, s, maxW));
    return {
      lines: lines.length,
      cs: lines.map((l, i) =>
        text(x, y - i * lead, F.body, s, l, 'right', 0, C.ink)).join(''),
    };
  }

  /* doc = { title, subtitle, standfirst, meals: [string], sections: [{name,
     note, items: [{qty, name, note}]}], recipes: [recipe], footnote } */
  function build(doc) {
    const pages = [];
    const hasList = (doc.sections || []).some(s => s.items && s.items.length);
    let cs = '', col = 0, y = 0, page = 1;

    const head = () => {
      let s = box(0, PAGE.h - 13, PAGE.w, 13, C.terracotta);
      s += text(M.l, PAGE.h - 48, F.serifBold, 17, doc.title, null, 0, C.ink);
      s += text(RIGHT, PAGE.h - 46, F.bold, 6.8,
        doc.subtitle.toUpperCase(), 'right', 1.3, C.ochre);
      s += rule(M.l, RIGHT, PAGE.h - 60, 0.7, C.line);
      return s;
    };

    const foot = () => (doc.footnote
      ? text(M.l, LETTER_FLOOR + 12, F.body, 6.4,
        doc.footnote.toUpperCase(), null, 1, C.ink4)
      : '');

    const TOP = PAGE.h - 84;
    const BOTTOM = LETTER_FLOOR + 26;

    let colTop = TOP;
    const newPage = () => {
      pages.push(cs + foot());
      page += 1; col = 0; colTop = TOP; y = TOP;
      cs = head();
    };

    const need = (h) => {
      if (y - h >= BOTTOM) return;
      if (col === 0) { col = 1; y = colTop; } else newPage();
    };

    cs = head();
    y = TOP;

    if (doc.standfirst) {
      for (const line of wrap(doc.standfirst, 9.2, PAGE.w - M.l - M.r)) {
        cs += text(M.l, y, F.body, 9.2, line, null, 0, C.ink2);
        y -= 12.5;
      }
      y -= 8;
    }
    if (doc.meals && doc.meals.length) {
      cs += sectionLabel(M.l, y, PAGE.w - M.l - M.r, 'This week');
      y -= 17;
      const half = Math.ceil(doc.meals.length / 2);
      const startY = y;
      let lowest = y;
      doc.meals.forEach((m, i) => {
        const c = i < half ? 0 : 1;
        const yy = startY - (i < half ? i : i - half) * 12.5;
        cs += fitted(COL_X[c], yy, F.body, 8.6, m, COL_W, 6.5, 'left', C.ink2);
        if (yy < lowest) lowest = yy;
      });
      y = lowest - 22;
    }

    colTop = y;

    for (const sec of doc.sections || []) {
      if (!sec.items.length) continue;
      need(28 + Math.min(sec.items.length, 3) * LEAD);
      cs += box(COL_X[col] - 6, y - 7, COL_W + 12, 18, C.panel);
      cs += text(COL_X[col], y, F.bold, 7.2, sec.name.toUpperCase(), null, 1.05, C.ochre);
      if (sec.note) {
        cs += text(COL_X[col] + COL_W, y, F.italic, 7.4, sec.note, 'right', 0, C.ink4);
      }
      y -= 24;

      for (const item of sec.items) {
        const lines = wrap(item.name, SIZE, nameW);
        const notes = item.note ? wrap(item.note, 7.4, nameW) : [];
        const qtyCount = item.qty
          ? wrap(item.qty, shrinkToFit(item.qty, SIZE, QTY_W - 2, 6.5), QTY_W - 2).length
          : 1;
        const h = Math.max(lines.length, qtyCount) * LEAD + 4 +
          (notes.length ? notes.length * 10 + 1 : 0);
        need(h);
        cs += tickbox(COL_X[col], y, SIZE);
        if (item.qty) {
          cs += qtyBlock(qtyR(col), y, item.qty, QTY_W - 2, SIZE, 6.5, LEAD).cs;
        }
        cs += 'BT\n/' + F.body + ' ' + num(SIZE) + ' Tf\n' + num(LEAD) + ' TL\n' +
          rgb(C.ink) + ' rg\n1 0 0 1 ' + num(nameX(col)) + ' ' + num(y) + ' Tm\n' +
          lines.map((l, i) => (i ? 'T*\n' : '') + lit(winAnsi(l)) + ' Tj\n').join('') +
          '0 0 0 rg\nET\n';
        y -= Math.max(lines.length, qtyCount) * LEAD + 4;
        if (notes.length) {
          cs += 'BT\n/' + F.italic + ' 7.4 Tf\n10 TL\n' + rgb(C.ink4) + ' rg\n' +
            '1 0 0 1 ' + num(nameX(col)) + ' ' + num(y + 2) + ' Tm\n' +
            notes.map((l, i) => (i ? 'T*\n' : '') + lit(winAnsi(l)) + ' Tj\n').join('') +
            '0 0 0 rg\nET\n';
          y -= notes.length * 10 + 1;
        }
      }
      y -= 14;
    }

    if (hasList) pages.push(cs + foot());

    // The recipes themselves, after the list.
    if (doc.recipes && doc.recipes.length) {
      for (const r of doc.recipes) {
        for (const p of recipePages(r, doc)) pages.push(p);
      }
    }

    // A page tree with no leaves is not a valid PDF, and an empty week can
    // reach here — untick everything, press the button, press download.
    if (!pages.length) {
      pages.push(head() + foot() +
        text(M.l, PAGE.h - 100, F.italic, 11,
          'Nothing is on this list. Pick a week first.', null, 0, C.ink3));
    }

    // Page numbers are stamped once the total is known, so they can read
    // `3 of 9` rather than counting up to a number nobody has yet.
    return assemble(pages.map((cs, i) =>
      cs + text(RIGHT, LETTER_FLOOR + 12, F.body, 6.8,
        (i + 1) + ' of ' + pages.length, 'right', 0.6, C.ink4)),
      { title: doc.title });
  }

  function download(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.rel = 'noopener';
    document.body.appendChild(a);
    a.click();
    a.remove();
    // Revoking straight away races the download and hands Safari an empty file.
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  }

  window.TMTPdf = { build, download, winAnsi, measure, wrap };
})();

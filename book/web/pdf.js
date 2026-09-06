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

  const F = { body: 'F1', bold: 'F2', serif: 'F3', serifBold: 'F4', italic: 'F5' };

  /* Text that has to end before a given point: the size comes down in quarter
     points until it does. Nothing here is ever allowed to draw past its
     boundary, because a shopping list with a quantity through the tick box is
     worse than one set a point smaller. */
  function shrinkToFit(str, size, maxW, min) {
    let s = size;
    while (s > min && measure(winAnsi(str), s) > maxW) s -= 0.25;
    return s;
  }

  function fitted(x, y, font, size, str, maxW, min, align) {
    return text(x, y, font, shrinkToFit(str, size, maxW, min), str, align || 'right');
  }

  /* A quantity can be two amounts joined — `6 × 200 g tins + 8 × 160 g tins` —
     and no size that is still readable will fit that on one line. It comes
     down to the floor first and then wraps, right-aligned, rather than
     overrunning into the tick box. */
  function qtyBlock(x, y, str, maxW, size, min, lead) {
    const s = shrinkToFit(str, size, maxW, min);
    // Two amounts joined by a plus break at the plus, not wherever the words
    // happen to fall: `6 × 200 g tins +` over `8 × 160 g tins` reads as two
    // amounts, and `6 × 200 g tins + 8` over `× 160 g tins` reads as neither.
    const lines = measure(winAnsi(str), s) <= maxW ? [str]
      : (str.includes(' + ')
        ? str.split(' + ').map((part, i, all) => i < all.length - 1 ? part + ' +' : part)
        : wrap(str, s, maxW));
    return {
      lines: lines.length,
      cs: lines.map((l, i) => text(x, y - i * lead, F.body, s, l, 'right')).join(''),
    };
  }

  function text(x, y, font, size, str, align, spacing) {
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
      '1 0 0 1 ' + num(tx) + ' ' + num(y) + ' Tm\n' +
      lit(bs) + ' Tj\n' + (tc ? '0 Tc\n' : '') + 'ET\n';
  }

  /* Every drawing block is wrapped in q/Q. `rg` sets the fill colour for text
     as well as for shapes, so a rule drawn in grey turns the next paragraph
     grey unless the state is restored. */
  function rule(x1, x2, y, weight, grey) {
    return 'q\n' + num(weight) + ' w\n' + num(grey) + ' ' + num(grey) + ' ' +
      num(grey) + ' RG\n' + num(x1) + ' ' + num(y) + ' m ' + num(x2) + ' ' +
      num(y) + ' l S\nQ\n';
  }

  function box(x, y, w, h, grey) {
    return 'q\n' + num(grey) + ' ' + num(grey) + ' ' + num(grey) + ' rg\n' +
      num(x) + ' ' + num(y) + ' ' + num(w) + ' ' + num(h) + ' re\nf\nQ\n';
  }

  /* Filled white and stroked, so the box reads as empty even over a tint. */
  function tickbox(x, baseline, size) {
    const s = Math.round(size * 0.76 * 2) / 2;
    return 'q\n0.7 w\n0.42 0.42 0.42 RG\n1 1 1 rg\n' +
      num(x) + ' ' + num(baseline - 0.5) + ' ' + num(s) + ' ' + num(s) +
      ' re\nB\nQ\n';
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

  // ------------------------------------------------------------ the layout

  const LEAD = 12.5;
  const SIZE = 9.5;
  const BOX_W = 15;
  const QTY_W = 54;
  const nameX = c => COL_X[c] + BOX_W + QTY_W + 7;
  const nameW = COL_W - BOX_W - QTY_W - 7;
  const qtyR = c => COL_X[c] + BOX_W + QTY_W;

  /* doc = { title, subtitle, standfirst, meals: [string], sections: [{name,
     note, items: [{qty, name, note}]}], footnote } */
  function build(doc) {
    const pages = [];
    const hasList = (doc.sections || []).some(s => s.items && s.items.length);
    let cs = '', col = 0, y = 0, page = 1;

    const head = (n) => {
      let s = '';
      s += text(M.l, PAGE.h - M.t - 12, F.serifBold, 15, doc.title);
      s += text(RIGHT, PAGE.h - M.t - 12, F.body, 8.5,
        doc.subtitle.toUpperCase(), 'right', 0.8);
      s += rule(M.l, RIGHT, PAGE.h - M.t - 24, 0.8, 0.55);
      if (doc.footnote) {
        s += text(M.l, LETTER_FLOOR + 6, F.italic, 8, doc.footnote);
      }
      return s;
    };

    const TOP = PAGE.h - M.t - 48;
    const BOTTOM = LETTER_FLOOR + M.b - 30;

    // Where a column starts. The first page carries the standfirst and the
    // list of meals across both columns, so its columns begin lower down.
    let colTop = TOP;

    const newPage = () => {
      pages.push(cs);
      page += 1; col = 0; colTop = TOP; y = TOP;
      cs = head(page);
    };

    // Reserve h points of column. Flows column, then column, then page.
    const need = (h) => {
      if (y - h >= BOTTOM) return;
      if (col === 0) { col = 1; y = colTop; } else newPage();
    };

    cs = head(page);
    y = TOP;

    // The standfirst and the meals it came from run across both columns.
    if (doc.standfirst) {
      for (const line of wrap(doc.standfirst, 9.5, PAGE.w - M.l - M.r)) {
        cs += text(M.l, y, F.body, 9.5, line);
        y -= 13;
      }
      y -= 6;
    }
    if (doc.meals && doc.meals.length) {
      cs += text(M.l, y, F.bold, 8.5, 'THIS WEEK', null, 0.8);
      y -= 14;
      const half = Math.ceil(doc.meals.length / 2);
      const startY = y;
      let lowest = y;
      doc.meals.forEach((m, i) => {
        const c = i < half ? 0 : 1;
        const yy = startY - (i < half ? i : i - half) * 12.5;
        cs += fitted(COL_X[c], yy, F.body, 9, m, COL_W, 6.5, 'left');
        if (yy < lowest) lowest = yy;
      });
      y = lowest - 20;
      cs += rule(M.l, RIGHT, y + 6, 0.5, 0.78);
      y -= 6;
    }

    colTop = y;

    for (const sec of doc.sections) {
      if (!sec.items.length) continue;
      // A heading alone at the foot of a column is worse than a short column.
      need(26 + Math.min(sec.items.length, 3) * LEAD);
      cs += box(COL_X[col] - 5, y - 6, COL_W + 10, 17, 0.925);
      cs += text(COL_X[col], y, F.bold, 8.5, sec.name.toUpperCase(), null, 0.7);
      if (sec.note) {
        cs += text(COL_X[col] + COL_W, y, F.italic, 8, sec.note, 'right');
      }
      y -= 23;

      for (const item of sec.items) {
        const lines = wrap(item.name, SIZE, nameW);
        const notes = item.note ? wrap(item.note, 7.5, nameW) : [];
        const qtyCount = item.qty
          ? wrap(item.qty, shrinkToFit(item.qty, SIZE, QTY_W - 2, 6.5), QTY_W - 2).length
          : 1;
        // Measured whole, so a note is never orphaned from its item and a
        // two-line quantity is never written over the row beneath it.
        const h = Math.max(lines.length, qtyCount) * LEAD + 3.5 +
          (notes.length ? notes.length * 10 + 1 : 0);
        need(h);
        cs += tickbox(COL_X[col], y, SIZE);
        if (item.qty) {
          cs += qtyBlock(qtyR(col), y, item.qty, QTY_W - 2, SIZE, 6.5, LEAD).cs;
        }
        cs += 'BT\n/' + F.body + ' ' + num(SIZE) + ' Tf\n' + num(LEAD) + ' TL\n' +
          '1 0 0 1 ' + num(nameX(col)) + ' ' + num(y) + ' Tm\n' +
          lines.map((l, i) => (i ? 'T*\n' : '') + lit(winAnsi(l)) + ' Tj\n').join('') +
          'ET\n';
        y -= Math.max(lines.length, qtyCount) * LEAD + 3.5;
        if (notes.length) {
          cs += 'BT\n/' + F.italic + ' 7.5 Tf\n10 TL\n0.45 0.45 0.45 rg\n' +
            '1 0 0 1 ' + num(nameX(col)) + ' ' + num(y + 2) + ' Tm\n' +
            notes.map((l, i) => (i ? 'T*\n' : '') + lit(winAnsi(l)) + ' Tj\n').join('') +
            '0 0 0 rg\nET\n';
          y -= notes.length * 10 + 1;
        }
      }
      y -= 12;
    }

    if (hasList) pages.push(cs);

    // The recipes themselves, after the list.
    if (doc.recipes && doc.recipes.length) {
      const headFor = () => {
        let s = text(M.l, PAGE.h - M.t - 12, F.serifBold, 15, doc.title);
        s += text(RIGHT, PAGE.h - M.t - 12, F.body, 8.5,
          doc.subtitle.toUpperCase(), 'right', 0.8);
        s += rule(M.l, RIGHT, PAGE.h - M.t - 24, 0.8, 0.55);
        if (doc.footnote) {
          s += text(M.l, LETTER_FLOOR + 6, F.italic, 8, doc.footnote);
        }
        return s;
      };
      for (const r of doc.recipes) {
        for (const p of recipePages(r, headFor)) pages.push(p);
      }
    }

    // A page tree with no leaves is not a valid PDF, and an empty week can
    // reach here — untick everything, press the button, press download.
    if (!pages.length) {
      pages.push(head(1) +
        text(M.l, PAGE.h - M.t - 70, F.italic, 11,
          'Nothing is on this list. Pick a week first.'));
    }

    // Page numbers are stamped once the total is known, so they can read
    // `3 of 9` rather than counting up to a number nobody has yet.
    return assemble(pages.map((cs, i) =>
      cs + text(PAGE.w / 2, LETTER_FLOOR + 6, F.body, 8,
        (i + 1) + ' of ' + pages.length, 'center')),
      { title: doc.title });
  }


  // ---------------------------------------------------------- recipe pages

  /* A recipe is laid out as blocks — a heading, a paragraph, one ingredient,
     one step — rather than as one long string, so a column that runs out of
     room breaks between two of them instead of through the middle of a line.
     Every block knows its own height at a given width and draws itself.
     `k` is the fit scale: see fitRecipe below. */

  const GREY = 0.42;

  function bGap(h) {
    return { h: () => h, draw: () => '' };
  }

  function bHead(label, k) {
    return {
      h: () => 18 * k,
      draw: (x, y, w) =>
        text(x, y, F.bold, 7.5, label.toUpperCase(), null, 0.65) +
        rule(x, x + w, y - 5.5, 0.5, 0.78),
    };
  }

  function bPara(str, font, size, lead, after, grey) {
    return {
      h: (w) => wrap(str, size, w).length * lead + (after || 0),
      draw: (x, y, w) => {
        const lines = wrap(str, size, w);
        const g = grey === undefined ? 0 : grey;
        return 'BT\n/' + font + ' ' + num(size) + ' Tf\n' + num(lead) + ' TL\n' +
          (g ? num(g) + ' ' + num(g) + ' ' + num(g) + ' rg\n' : '') +
          '1 0 0 1 ' + num(x) + ' ' + num(y) + ' Tm\n' +
          lines.map((l, i) => (i ? 'T*\n' : '') + lit(winAnsi(l)) + ' Tj\n').join('') +
          (g ? '0 0 0 rg\n' : '') + 'ET\n';
      },
    };
  }

  // An ingredient, hanging so a wrapped second line lines up under the first.
  function bItem(str, size, lead) {
    const IND = 10;
    return {
      h: (w) => wrap(str, size, w - IND).length * lead + 2,
      draw: (x, y, w) => {
        const lines = wrap(str, size, w - IND);
        return text(x, y, F.body, size, '–') +
          'BT\n/' + F.body + ' ' + num(size) + ' Tf\n' + num(lead) + ' TL\n' +
          '1 0 0 1 ' + num(x + IND) + ' ' + num(y) + ' Tm\n' +
          lines.map((l, i) => (i ? 'T*\n' : '') + lit(winAnsi(l)) + ' Tj\n').join('') +
          'ET\n';
      },
    };
  }

  function bStep(n, str, size, lead) {
    const IND = 17;
    return {
      h: (w) => wrap(str, size, w - IND).length * lead + 7,
      draw: (x, y, w) => {
        const lines = wrap(str, size, w - IND);
        return text(x, y - 0.5, F.serifBold, size + 2.5, String(n)) +
          'BT\n/' + F.body + ' ' + num(size) + ' Tf\n' + num(lead) + ' TL\n' +
          '1 0 0 1 ' + num(x + IND) + ' ' + num(y) + ' Tm\n' +
          lines.map((l, i) => (i ? 'T*\n' : '') + lit(winAnsi(l)) + ' Tj\n').join('') +
          'ET\n';
      },
    };
  }

  /* A chef's note: the label runs on into the note, as it does in the book.
     The label is set bold and dark, the note itself grey — including the part
     of it that shares the first line, which used to come out black while its
     own continuation lines were grey. The first line is wrapped against the
     room the label leaves it rather than against the full column, since it is
     measured in roman and drawn after something bold. */
  function bNote(label, str, size, lead) {
    const prefix = label + ':';
    const gap = () => measure(winAnsi(prefix), size, true) + size * 0.36;
    return {
      h: (w) => wrapIndent(str, size, w - gap(), w).length * lead + 5,
      draw: (x, y, w) => {
        const labelW = gap();
        const lines = wrapIndent(str, size, w - labelW, w);
        const g = num(GREY) + ' ' + num(GREY) + ' ' + num(GREY) + ' rg\n';
        let out = text(x, y, F.bold, size, prefix);
        out += 'BT\n/' + F.body + ' ' + num(size) + ' Tf\n' + num(lead) + ' TL\n' + g +
          '1 0 0 1 ' + num(x + labelW) + ' ' + num(y) + ' Tm\n' +
          lit(winAnsi(lines[0])) + ' Tj\n0 0 0 rg\nET\n';
        if (lines.length > 1) {
          out += 'BT\n/' + F.body + ' ' + num(size) + ' Tf\n' + num(lead) + ' TL\n' + g +
            '1 0 0 1 ' + num(x) + ' ' + num(y - lead) + ' Tm\n' +
            lines.slice(1).map((l, i) => (i ? 'T*\n' : '') +
              lit(winAnsi(l)) + ' Tj\n').join('') + '0 0 0 rg\nET\n';
        }
        return out;
      },
    };
  }

  function bMacros(macros, k) {
    const keys = ['kcal', 'protein', 'carbs', 'fat', 'fibre'];
    const units = ['', ' g', ' g', ' g', ' g'];
    return {
      h: () => 27 * k,
      draw: (x, y, w) => {
        let out = '';
        const step = w / 5;
        macros.forEach((v, i) => {
          out += text(x + i * step, y, F.serifBold, 10.5, String(v) + units[i]);
          out += text(x + i * step, y - 10, F.body, 6.5,
            keys[i].toUpperCase(), null, 0.5);
        });
        return out;
      },
    };
  }

  /* Pour blocks into one column, stopping before the first that will not fit
     and handing the rest back. A block always gets one shot at an empty
     column, so nothing can loop for ever. */
  function fillColumn(blocks, x, top, w, bottom) {
    let cs = '', y = top, i = 0;
    for (; i < blocks.length; i++) {
      const h = blocks[i].h(w);
      if (y - h < bottom && y !== top) break;
      cs += blocks[i].draw(x, y, w);
      y -= h;
    }
    return { cs, rest: blocks.slice(i), y };
  }

  /* One flow through both columns rather than two fixed halves. A full recipe
     is more than a single column holds, so splitting it left/right by kind
     would leave one column short and the other spilling onto a page of its
     own. Poured as one sequence it fills the left column and carries on into
     the right. */
  function recipeBlocks(r, k) {
    const b = [];
    const ing = 8.5 * k, ingL = 11 * k;
    const step = 8.5 * k, stepL = 11.5 * k;
    const body = 8 * k, bodyL = 10.5 * k;
    b.push(bHead('Ingredients', k));
    for (const g of r.groups) {
      if (g.name) {
        b.push(bGap(3 * k));
        b.push(bPara(g.name, F.serifBold, 9 * k, 11 * k, 3));
      }
      for (const item of g.items) b.push(bItem(item, ing, ingL));
    }
    b.push(bGap(10 * k));
    b.push(bHead('Nutrition, a serving', k));
    b.push(bMacros(r.macros, k));
    b.push(bGap(8 * k));
    b.push(bHead('Why it works', k));
    b.push(bPara(r.why, F.body, body, bodyL, 12 * k, GREY));
    b.push(bHead('Method', k));
    r.steps.forEach((s, i) => b.push(bStep(i + 1, s, step, stepL)));
    b.push(bGap(6 * k));
    b.push(bHead('For the toddler', k));
    b.push(bPara(r.toddler, F.body, body, bodyL, 12 * k, GREY));
    b.push(bHead('Chef’s notes', k));
    for (const [label, note] of r.notes) b.push(bNote(label, note, body, bodyL));
    b.push(bGap(8 * k));
    b.push(bHead('Washing up', k));
    b.push(bPara(r.washing, F.body, body, bodyL, 0, GREY));
    return b;
  }

  /* The book's own typesetter fits each recipe to its spread by searching one
     parameter that tightens the type until the page holds. This does the same,
     for the same reason: a recipe you cook from wants to be one sheet of
     paper, and a page and a fifth is the worst of both. The floor is 0.84,
     below which it would stop being comfortable to read across a hob, and a
     recipe that still does not fit is allowed its second page.
     Fifty of fifty fit at 0.90 or better. */
  function fitRecipe(r, capacity) {
    let k = 1;
    for (let i = 0; i < 9; i++) {
      const blocks = recipeBlocks(r, k);
      let total = 0;
      for (const b of blocks) total += b.h(COL_W);
      if (total <= capacity || k <= 0.84) return { blocks, k };
      k = Math.round((k - 0.02) * 100) / 100;
    }
    return { blocks: recipeBlocks(r, k), k };
  }

  function recipePages(r, head) {
    const TOP = PAGE.h - M.t - 46;
    const BOTTOM = LETTER_FLOOR + 12;

    // The title block runs across both columns, so measure it before deciding
    // how much room the recipe itself has.
    const hookLines = wrap(r.hook, 10, PAGE.w - M.l - M.r);
    const ruleY = PAGE.h - M.t - 104 - hookLines.length * 13 + 13 - 4;
    const colTop = ruleY - 22;
    // Blocks do not split, so whatever straddles the column break is pushed
    // whole into the next column and the room it would have used is lost. One
    // block's worth of slack is taken off the target before fitting.
    const capacity = (colTop - BOTTOM) * 2 - 40;

    const fit = fitRecipe(r, capacity);
    const pages = [];
    let rest = fit.blocks;
    let first = true;

    while (rest.length) {
      let cs = head();
      let top;
      if (first) {
        const meta = [r.ml, r.c, r.time, 'Serves ' + r.serves]
          .concat(r.veg ? ['Vegetarian'] : []).join('  ·  ');
        cs += text(M.l, PAGE.h - M.t - 74, F.serifBold, 32, r.n);
        const tx = M.l + measure(winAnsi(r.n), 32) + 13;
        // Times-Bold is narrower than the Helvetica table this measures with,
        // so the estimate is conservative and the title lands inside the rule
        // under it either way.
        cs += fitted(tx, PAGE.h - M.t - 68, F.serifBold, 20, r.t, RIGHT - tx, 14, 'left');
        cs += text(tx, PAGE.h - M.t - 85, F.body, 7.5, meta.toUpperCase(), null, 0.55);
        let y = PAGE.h - M.t - 104;
        for (const line of hookLines) {
          cs += text(M.l, y, F.italic, 10, line);
          y -= 13;
        }
        cs += rule(M.l, RIGHT, ruleY, 0.8, 0.55);
        top = colTop;
        first = false;
      } else {
        cs += text(M.l, PAGE.h - M.t - 62, F.body, 8,
          (r.n + ' · ' + r.t + ' · continued').toUpperCase(), null, 0.5);
        top = PAGE.h - M.t - 82;
      }
      const a = fillColumn(rest, COL_X[0], top, COL_W, BOTTOM);
      const b = fillColumn(a.rest, COL_X[1], top, COL_W, BOTTOM);
      cs += a.cs + b.cs;
      rest = b.rest;
      pages.push(cs);
      if (pages.length > 4) break;
    }
    return pages;
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

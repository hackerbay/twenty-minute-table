/* The meal planner.
 *
 * Everything the page needs was worked out at build time and embedded as JSON:
 * the eighty-five dinners, breakfasts and puddings, what protein each is built
 * on, which part of the world it comes from, and every ingredient line already
 * parsed into an amount, a unit and a thing you can buy. This file does five
 * jobs with that.
 *
 *   1. Filters by what the household eats and what it feels like washing up.
 *   2. Picks a week that spreads the protein, the pan and the region rather
 *      than shuffling. A uniform draw of seven from fifty puts the same protein
 *      family on four nights or more about a third of the time and leaves no
 *      meat-free night at all about a quarter of the time. Those are the two
 *      failures worth fixing, and they are what the score below is for.
 *   3. Lets a dinner be looked up by name, cuisine or ingredient and put in by
 *      hand, or taken out again — a week nobody can edit is a toy.
 *   4. Adds every ingredient of every meal up into one list, scaled to the
 *      number of servings and ordered the way a shop is walked.
 *   5. Writes that list out as a PDF, using the writer in pdf.js.
 *
 * What the page claims is held to what it can count: how many proteins, how
 * many regions, how much protein and fibre a serving carries by the book's own
 * estimates, and where the filters made something impossible. It is a cookbook,
 * not a dietitian, and the copy says so.
 */
(() => {
  'use strict';

  const DATA = window.PLAN;
  if (!DATA) return;

  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const BY_NUM = new Map(DATA.recipes.map(r => [r.n, r]));
  const AISLES = DATA.aisles;
  const BASE_SERVES = DATA.serves || 4;
  const ALL_TAGS = ['veg', 'chicken', 'redmeat', 'fish', 'shellfish'];
  const ALL_PANS = [...new Set(DATA.recipes.filter(r => r.sec === 'dinner').map(r => r.m))];
  // The three courses the planner picks from, in the order they are eaten.
  const COURSES = DATA.courses || [['dinner', 'Dinners']];
  const COURSE_LABEL = new Map(COURSES);

  const ORDINALS = ['First', 'Second', 'Third', 'Fourth', 'Fifth', 'Sixth',
    'Seventh', 'Eighth', 'Ninth', 'Tenth'];
  const WORDS = ['no', 'one', 'two', 'three', 'four', 'five', 'six', 'seven',
    'eight', 'nine', 'ten'];
  const word = n => (n >= 0 && n < WORDS.length ? WORDS[n] : String(n));
  const cap = s => s.charAt(0).toUpperCase() + s.slice(1);
  const isVeg = r => r.tg.length === 1 && r.tg[0] === 'veg';
  const sum = a => a.reduce((x, y) => x + y, 0);
  const distinct = (a, f) => new Set(a.map(f)).size;
  const clamp01 = x => (x < 0 ? 0 : x > 1 ? 1 : x);

  // ------------------------------------------------------------------ state

  const state = {
    serves: BASE_SERVES,
    eat: new Set(ALL_TAGS),
    pans: new Set(ALL_PANS),
    // How many of each course to pick, and what was picked. Breakfast and
    // pudding start at nought: they are something you ask for.
    want: { dinner: DATA.week.length, breakfast: 0, afters: 0 },
    picked: { dinner: DATA.week.slice(), breakfast: [], afters: [] },
    week: DATA.week.slice(),
    ticked: new Set(),
    hideTicked: false,
    cursors: new Map(),      // one shuffled queue of alternatives per slot
    hasPicked: false,        // whether the button has been pressed yet
  };

  /* The week lives in the address, not in storage. A picked week is then a
     link — bookmark it, or send it to whoever is going to the shop — and the
     page keeps the site's habit of storing nothing. The ticks are not in it:
     they last while the page is open, exactly as they do on the pantry page. */
  function readHash() {
    const h = new URLSearchParams(location.hash.replace(/^#/, ''));
    const week = (h.get('w') || '').split(',').filter(n => BY_NUM.has(n));
    if (!week.length) return false;
    // The address carries one list; the course each recipe belongs to is a
    // property of the recipe, so it does not have to be carried as well.
    for (const c of COURSES) state.picked[c[0]] = [];
    for (const n of week) {
      const r = BY_NUM.get(n);
      (state.picked[r.sec] || state.picked.dinner).push(n);
    }
    state.week = state.picked.dinner;
    for (const [key] of COURSES) state.want[key] = state.picked[key].length;
    state.hasPicked = true;
    const nights = parseInt(h.get('n'), 10);
    if (nights > 0 && nights <= 10) state.want.dinner = nights;
    const serves = parseInt(h.get('s'), 10);
    if (serves > 0 && serves <= 12) state.serves = serves;
    const eat = (h.get('eat') || '').split(',').filter(t => ALL_TAGS.includes(t));
    if (eat.length) state.eat = new Set(eat);
    const pans = (h.get('pan') || '').split(',').filter(m => ALL_PANS.includes(m));
    if (pans.length) state.pans = new Set(pans);
    return true;
  }

  const allPicked = () => COURSES.reduce((a, c) => a.concat(state.picked[c[0]]), []);

  function writeHash(push) {
    const h = 'n=' + state.want.dinner + '&s=' + state.serves +
      '&eat=' + [...state.eat].join(',') + '&pan=' + [...state.pans].join(',') +
      '&w=' + allPicked().join(',');
    if (location.hash.slice(1) === h) return;
    // Pushing on a pick makes Back an undo. Swapping and changing the servings
    // replace instead, so eight swaps do not cost nine presses of Back.
    if (push) history.pushState(null, '', '#' + h);
    else history.replaceState(null, '', '#' + h);
  }

  // ------------------------------------------------------------- the score

  /* Weights come from where a plain shuffle actually fails on this book rather
     than from what sounds important. Protein and calories barely move across
     the fifty dinners — every one carries between 31 g and 59 g of protein and
     the whole book spans 160 kcal — so there is nothing there to optimise.
     Repeating a protein and ending up with no meat-free night are the real
     failures, and that is where the weight goes. */
  const W = { source: 24, cuisine: 18, fibre: 18, method: 16, veg: 12, kcal: 8, protein: 4 };
  const T = {
    vegShare: 2 / 7, fibreWeekMin: 10, fibreLowNight: 7, lowFibreShare: 1 / 3,
    kcalRich: 750, richShare: 0.3, kcalWeekMax: 725, kcalSd: 45,
    proteinFloor: 30, proteinWeekMin: 40,
  };

  /* The smallest "largest category" a pool of this shape can reach. With only
     fish ticked there is one protein family and seven nights to fill, so the
     answer is seven and the repeat penalty switches itself off. This is how a
     narrow filter gets judged against what it can do rather than against an
     ideal it was never able to meet. */
  function minPossibleMax(pool, n, f) {
    const sizes = new Map();
    for (const r of pool) sizes.set(f(r), (sizes.get(f(r)) || 0) + 1);
    const list = [...sizes.values()];
    for (let m = 1; m <= n; m++) {
      if (sum(list.map(s => Math.min(s, m))) >= n) return m;
    }
    return n;
  }

  function poolCaps(pool, n) {
    const topMean = f => {
      const v = pool.map(f).sort((a, b) => b - a).slice(0, Math.min(n, pool.length));
      return v.length ? sum(v) / v.length : 0;
    };
    return {
      n: Math.min(n, pool.length),
      sources: Math.min(n, distinct(pool, r => r.src)),
      methods: Math.min(n, distinct(pool, r => r.m)),
      regions: Math.min(n, distinct(pool, r => r.g)),
      cuisines: Math.min(n, distinct(pool, r => r.c)),
      veg: Math.min(Math.round(n * T.vegShare), pool.filter(isVeg).length),
      minFamilyMax: minPossibleMax(pool, n, r => r.fam),
      minMethodMax: minPossibleMax(pool, n, r => r.m),
      bestFibre: topMean(r => r.fb),
      bestProtein: topMean(r => r.pr),
      minRich: Math.max(0, n - pool.filter(r => r.kc < T.kcalRich).length),
    };
  }

  /* Nought to a hundred, and only comparable within one pool. It says "as
     varied as your filters allow", never "this is a good diet". */
  function scoreWeek(set, C) {
    const n = set.length;
    if (!n) return 0;
    const seenS = new Set(), seenG = new Set(), seenC = new Set();
    const cntM = new Map(), cntF = new Map();
    let maxF = 0, maxM = 0, dm = 0;
    let kcal = 0, prot = 0, fib = 0, veg = 0, low = 0, rich = 0, under = 0;
    for (const r of set) {
      seenS.add(r.src); seenG.add(r.g); seenC.add(r.c);
      if (!cntM.has(r.m)) dm++;
      const m = cntM.set(r.m, (cntM.get(r.m) || 0) + 1).get(r.m);
      if (m > maxM) maxM = m;
      const f = cntF.set(r.fam, (cntF.get(r.fam) || 0) + 1).get(r.fam);
      if (f > maxF) maxF = f;
      kcal += r.kc; prot += r.pr; fib += r.fb;
      if (isVeg(r)) veg++;
      if (r.fb <= T.fibreLowNight) low++;
      if (r.kc >= T.kcalRich) rich++;
      if (r.pr < T.proteinFloor) under++;
    }

    const famAllow = Math.max(Math.ceil(n / 3), C.minFamilyMax);
    const source = W.source * (
      0.6 * (C.sources ? clamp01(seenS.size / C.sources) : 1) +
      0.4 * (1 - clamp01(Math.max(0, maxF - famAllow) / Math.max(1, n - famAllow))));

    const dupAllow = Math.max(0, n - C.cuisines);
    const cuisine = W.cuisine * (
      0.65 * (C.regions ? clamp01(seenG.size / C.regions) : 1) +
      0.35 * (1 - clamp01(((n - seenC.size) - dupAllow) / Math.max(1, n - 1 - dupAllow))));

    const fibreGoal = Math.max(1, Math.min(T.fibreWeekMin, C.bestFibre || T.fibreWeekMin));
    const lowAllow = Math.floor(n * T.lowFibreShare);
    const fibre = W.fibre * (
      0.7 * clamp01((fib / n) / fibreGoal) +
      0.3 * (1 - clamp01((low - lowAllow) / Math.max(1, n - lowAllow))));

    const methAllow = Math.max(Math.ceil(n / 2), C.minMethodMax);
    const method = W.method * (
      0.7 * (C.methods ? clamp01(dm / C.methods) : 1) +
      0.3 * (1 - clamp01(Math.max(0, maxM - methAllow) / Math.max(1, n - methAllow))));

    // Overshoot is never punished. If the filters leave mostly vegetarian
    // dinners then a vegetarian week is the right answer, not a shortfall.
    const vegPart = W.veg * (C.veg > 0 ? clamp01(veg / C.veg) : 1);

    const richAllow = Math.max(Math.round(n * T.richShare), C.minRich);
    const kcalPart = W.kcal * (
      1 - 0.6 * clamp01((rich - richAllow) / Math.max(1, n - richAllow))
        - 0.4 * clamp01((kcal / n - T.kcalWeekMax) / T.kcalSd));

    const pGoal = Math.min(T.proteinWeekMin, C.bestProtein || T.proteinWeekMin);
    const protein = W.protein * clamp01((prot / n) / pGoal) * (1 - under / n);

    return source + cuisine + fibre + method + vegPart + kcalPart + protein;
  }

  // ------------------------------------------------------------- the picker

  /* The ticks govern every course: somebody who does not eat fish should not
     be handed a smoked mackerel breakfast either. The pan ticks are read only
     against the dinners, because they are a question about the evening and
     nobody unticks the wok to rule out a bowl of yoghurt. */
  const poolFor = (course) => DATA.recipes.filter(r =>
    r.sec === course && r.tg.every(t => state.eat.has(t)) &&
    (course !== 'dinner' || state.pans.has(r.m)));

  const pool = () => poolFor('dinner');

  /* Softmax over the marginal gain of each candidate. Pure greedy would return
     the same week every time and a uniform draw would return a poor one, so the
     randomness sits in three places: the first dinner is drawn uniformly, the
     rest in proportion to how much they improve the week, and the final answer
     is drawn uniformly from everything within a point and a half of the best. */
  function buildGreedy(p, n, C, tau) {
    const set = [p[Math.floor(Math.random() * p.length)]];
    while (set.length < n) {
      const items = [], gains = [];
      let best = -Infinity;
      for (const r of p) {
        if (set.includes(r)) continue;
        set.push(r);
        const g = scoreWeek(set, C);
        set.pop();
        items.push(r); gains.push(g);
        if (g > best) best = g;
      }
      if (!items.length) break;
      let total = 0;
      const w = gains.map(x => { const e = Math.exp((x - best) / tau); total += e; return e; });
      let t = Math.random() * total, k = 0;
      while (k < w.length - 1 && (t -= w[k]) > 0) k++;
      set.push(items[k]);
    }
    return set;
  }

  // One steepest-ascent pass, which undoes what the greedy committed to early.
  function repair(set, p, C) {
    const cur = set.slice();
    let best = scoreWeek(cur, C);
    for (let i = 0; i < cur.length; i++) {
      for (const cand of p) {
        if (cur.includes(cand)) continue;
        const old = cur[i];
        cur[i] = cand;
        const s = scoreWeek(cur, C);
        if (s > best + 1e-9) best = s; else cur[i] = old;
      }
    }
    return cur;
  }

  function combinations(p, n) {
    const out = [], idx = [];
    (function rec(start) {
      if (idx.length === n) { out.push(idx.map(i => p[i])); return; }
      for (let i = start; i <= p.length - (n - idx.length); i++) {
        idx.push(i); rec(i + 1); idx.pop();
      }
    })(0);
    return out;
  }

  const choose = (N, k) => {
    let r = 1;
    for (let i = 0; i < k; i++) r = r * (N - i) / (i + 1);
    return r;
  };

  // A week that reads chicken, chicken, fish, fish feels wrong even when it
  // scores well, so the nights are ordered to alternate.
  function orderNights(set) {
    const rest = set.slice(1), out = [set[0]];
    while (rest.length) {
      const prev = out[out.length - 1];
      let bi = 0, bs = -1;
      rest.forEach((r, i) => {
        const s = (r.fam !== prev.fam ? 2 : 0) + (r.m !== prev.m ? 1 : 0);
        if (s > bs) { bs = s; bi = i; }
      });
      out.push(rest.splice(bi, 1)[0]);
    }
    return out;
  }

  function pickWeek(n, avoid, course) {
    const p = poolFor(course || 'dinner');
    const C = poolCaps(p, n);
    if (!C.n) return { set: [], caps: C, alternatives: 0 };

    let cands;
    if (choose(p.length, C.n) <= 12000) {
      // A tight filter gets the provably best week rather than a heuristic's
      // guess at it: seven from twelve is 792 combinations, which is nothing.
      cands = combinations(p, C.n).map(s => ({ s, v: scoreWeek(s, C) }));
    } else {
      const seen = new Map();
      for (let i = 0; i < 12; i++) {
        const s = repair(buildGreedy(p, C.n, C, 1.2), p, C);
        seen.set(s.map(r => r.n).sort().join(','), { s, v: scoreWeek(s, C) });
      }
      cands = [...seen.values()];
    }
    const top = Math.max(...cands.map(c => c.v));
    let band = cands.filter(c => c.v >= top - 1.5);
    const avoidSet = new Set(avoid || []);
    const fresh = band.filter(c => !c.s.some(r => avoidSet.has(r.n)));
    if (fresh.length) band = fresh;
    const chosen = band[Math.floor(Math.random() * band.length)].s;
    return { set: orderNights(chosen), caps: C, alternatives: band.length };
  }

  /* Swapping one night keeps the other nights exactly as they are. Each slot
     holds its own queue, ordered by how well the candidate would keep the
     week's spread and shuffled a little, so pressing Swap three times gives
     three different dinners rather than the same second-best one. */
  function nextForSlot(course, slot) {
    const p = poolFor(course);
    const list = state.picked[course];
    const week = list.map(n => BY_NUM.get(n));
    const inWeek = new Set(allPicked());
    const key = course + ':' + slot;
    let queue = state.cursors.get(key);
    if (!queue) {
      const C = poolCaps(p, week.length);
      queue = p
        .filter(r => r.n !== list[slot])
        .map(r => {
          const trial = week.slice();
          trial[slot] = r;
          return { r, v: scoreWeek(trial, C) + Math.random() * 1.2 };
        })
        .sort((a, b) => b.v - a.v)
        .map(x => x.r.n);
      state.cursors.set(key, queue);
    }
    // A rotation, not a drain: a candidate that happens to be in the week now
    // goes to the back rather than being thrown away, and the slot's own
    // current dinner rejoins the queue so it can come round again. Only a full
    // pass that finds nothing outside the week means there is nothing left.
    if (!queue.includes(list[slot])) queue.push(list[slot]);
    for (let i = 0; i < queue.length; i++) {
      const n = queue.shift();
      queue.push(n);
      if (!inWeek.has(n)) return BY_NUM.get(n);
    }
    return null;
  }

  // --------------------------------------------------------- shopping list

  const UNIT_FAMILY = { g: 'mass', kg: 'mass', ml: 'vol', l: 'vol',
    litre: 'vol', litres: 'vol', tsp: 'spoon', tbsp: 'spoon', cm: 'cm' };
  const TO_BASE = { g: 1, kg: 1000, ml: 1, l: 1000, litre: 1000, litres: 1000,
    tsp: 1, tbsp: 3, cm: 1 };
  const VAGUE = new Set(['pinch', 'handful', 'little', 'scrape', 'splash',
    'drizzle', 'squeeze', 'few sprigs']);

  function familyOf(e) {
    const noQty = e.q === null || e.q === undefined;
    if (VAGUE.has(e.u)) return 'vague:' + e.u;
    if (noQty) return 'some';
    if (e.u === '') return 'count';
    if (UNIT_FAMILY[e.u]) return UNIT_FAMILY[e.u];
    return 'pack:' + e.u + ':' + (e.p || '');
  }

  const FRACTIONS = [[0.125, '⅛'], [0.25, '¼'], [1 / 3, '⅓'], [0.375, '⅜'],
    [0.5, '½'], [0.625, '⅝'], [2 / 3, '⅔'], [0.75, '¾'], [0.875, '⅞']];

  // Vulgar fractions round-trip: the recipe files are written with them, and
  // the list gives them back rather than printing 0.5.
  function fraction(x) {
    const whole = Math.floor(x + 1e-9);
    const rest = x - whole;
    if (rest < 0.06) return String(whole);
    let best = '', bestD = 1;
    for (const [v, s] of FRACTIONS) {
      const d = Math.abs(rest - v);
      if (d < bestD) { bestD = d; best = s; }
    }
    if (bestD > 0.08) return String(Math.round(x * 10) / 10);
    return (whole ? whole : '') + best;
  }

  const roundTo = (x, step) => Math.round(x / step) * step;

  function amountText(fam, value) {
    if (fam === 'mass' || fam === 'vol') {
      const big = fam === 'mass' ? 'kg' : 'litres';
      const small = fam === 'mass' ? 'g' : 'ml';
      if (value >= 1000) return (roundTo(value, 50) / 1000) + ' ' + big;
      if (value >= 250) return roundTo(value, 25) + ' ' + small;
      if (value >= 60) return roundTo(value, 10) + ' ' + small;
      return Math.max(5, roundTo(value, 5)) + ' ' + small;
    }
    if (fam === 'spoon') {
      const tsp = Math.max(0.5, roundTo(value, 0.5));
      const tbsp = Math.floor(tsp / 3 + 1e-9);
      const rest = tsp - tbsp * 3;
      const parts = [];
      if (tbsp) parts.push(tbsp + ' tbsp');
      if (rest > 0.05) parts.push(fraction(rest) + ' tsp');
      return parts.join(' ') || '½ tsp';
    }
    // You cannot buy one and a half peppers or two-thirds of a tin.
    if (fam === 'count') return String(Math.max(1, Math.ceil(value - 1e-9)));
    if (fam === 'cm') return fraction(Math.max(0.5, roundTo(value, 0.5))) + ' cm';
    if (fam.startsWith('pack:')) {
      const parts = fam.split(':');
      const unit = parts[1], size = parts[2];
      const n = Math.max(1, Math.ceil(value - 1e-9));
      const plural = n === 1 ? unit
        : (unit === 'bunch' ? 'bunches' : unit === 'box' ? 'boxes' : unit + 's');
      return size ? n + ' × ' + size + ' ' + plural : n + ' ' + plural;
    }
    if (fam.startsWith('vague:')) {
      const u = fam.slice(6);
      if (u === 'little') return 'a little';
      if (u === 'few sprigs') return 'a few sprigs';
      return 'a ' + u;
    }
    return '';
  }

  /* Every ingredient of every dinner, added up. Amounts only combine within
     their own family: six tablespoons of oil and 100 ml of oil stay two lines,
     because turning one into the other would claim a precision the recipes do
     not have. Nothing is ever dropped — a line the parser could not read keeps
     its own words and still lands on the list. */
  function shoppingList() {
    const scale = state.serves / BASE_SERVES;
    const items = new Map();
    for (const num of allPicked()) {
      const r = BY_NUM.get(num);
      if (!r) continue;
      for (const e of r.ing) {
        let it = items.get(e.k);
        if (!it) {
          it = { key: e.k, names: new Map(), aisle: e.a, staple: !!e.s,
            amounts: new Map(), from: new Set() };
          items.set(e.k, it);
        }
        it.names.set(e.n, (it.names.get(e.n) || 0) + 1);
        it.from.add(r.n);
        const fam = familyOf(e);
        if (e.q === null || e.q === undefined) {
          if (!it.amounts.has(fam)) it.amounts.set(fam, null);
        } else {
          const base = TO_BASE[e.u] ? e.q * TO_BASE[e.u] : e.q;
          it.amounts.set(fam, (it.amounts.get(fam) || 0) + base * scale);
        }
      }
    }

    const out = [];
    for (const it of items.values()) {
      // The name most of the recipes use for it, and the shortest of those.
      const name = [...it.names.entries()]
        .sort((a, b) => b[1] - a[1] || a[0].length - b[0].length)[0][0];
      const qty = [...it.amounts.entries()]
        .map(([fam, v]) => (v === null ? amountText(fam, 1) : amountText(fam, v)))
        .filter(Boolean).join(' + ');
      out.push({ name, qty, aisle: it.aisle, staple: it.staple,
        from: [...it.from].sort(), key: it.key });
    }
    out.sort((a, b) => a.name.localeCompare(b.name, 'en'));
    return out;
  }

  function grouped(list) {
    const groups = [];
    for (const [key, label] of AISLES) {
      const items = list.filter(i => i.aisle === key && !i.staple);
      if (items.length) groups.push({ key, label, items });
    }
    return groups;
  }

  const cupboard = list => list.filter(i => i.staple);

  // ------------------------------------------------------------- rendering

  const esc = s => String(s).replace(/[&<>"]/g,
    c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

  /* The kind of dinner it is, said in the words somebody would use. The first
     tag is what the dish is built on — beef, prawns, vegetarian. Any further
     one is a protein the dish carries without being about it, which is exactly
     what the filters act on, so it is shown rather than left to surprise
     anybody. Mirrors night_tags() in site.py. */
  const EXTRA_TAG = { fish: 'fish', shellfish: 'shellfish', chicken: 'chicken',
    redmeat: 'red meat' };
  const OWN_TAGS = { seafood: ['fish', 'shellfish'], poultry: ['chicken'],
    'red meat': ['redmeat'] };

  function nightTags(r) {
    const own = OWN_TAGS[r.fam] || [];
    const out = [isVeg(r)
      ? '<span class="ntag ntag-veg">Vegetarian</span>'
      : `<span class="ntag">${esc(r.src)}</span>`];
    for (const t of r.tg) {
      if (EXTRA_TAG[t] && own.indexOf(t) === -1) {
        out.push(`<span class="ntag ntag-also">also ${EXTRA_TAG[t]}</span>`);
      }
    }
    return out.join('');
  }

  function nightRow(r, i, course) {
    return `
      <li class="night" data-num="${r.n}" data-course="${course}" style="--c:${r.col}">
        <span class="n-ord">${course === 'dinner' ? (ORDINALS[i] || i + 1) : (COURSE_ORD[course] || '')}</span>
        <span class="cnum d">${r.n}</span>
        <div class="n-body">
          <a class="n-title d" href="r/${r.s}.html">${esc(r.t)}</a>
          <p class="n-tags">${nightTags(r)}</p>
          <p class="n-meta"><span>${esc(r.ml)}</span><span class="dot"></span>
            <span>${esc(r.c)}</span><span class="dot"></span>
            <span>${r.pr} g protein a serving</span></p>
        </div>
        <div class="n-right">
          <span class="cmin d">${r.min}<i>min</i></span>
          <button class="swap" type="button" data-slot="${i}" data-course="${course}"
            aria-label="Swap ${esc(r.t)}">Swap</button>
          <button class="drop" type="button" data-drop="${i}" data-course="${course}"
            aria-label="Take ${esc(r.t)} out of the week"><span aria-hidden="true">×</span></button>
        </div>
      </li>`;
  }

  // Breakfast and pudding rows are labelled by course rather than by ordinal:
  // `First, Second, Third` belongs to the run of dinners, and repeating it
  // down a second list would read as a second week.
  const COURSE_ORD = { breakfast: 'Breakfast', afters: 'Afterwards' };

  function renderWeek() {
    const week = state.picked.dinner.map(n => BY_NUM.get(n)).filter(Boolean);
    const others = COURSES.slice(1).filter(([k]) => state.picked[k].length);
    $('#plan-empty').hidden = week.length > 0 || others.length > 0;
    $('#weeklist').innerHTML = week.map((r, i) => nightRow(r, i, 'dinner')).join('');
    $('#weeklist').hidden = !week.length;
    $('#course-extra').innerHTML = others.map(([key, label]) => {
      const rows = state.picked[key].map(n => BY_NUM.get(n)).filter(Boolean);
      return `<h2 class="sect d sect-sub">${esc(label)}<span>${cap(word(rows.length))}</span></h2>` +
        `<ol class="week">${rows.map((r, i) => nightRow(r, i, key)).join('')}</ol>`;
    }).join('');
    $('#wkcount').textContent = week.length
      ? cap(word(week.length)) + (week.length === 1 ? ' night' : ' nights') : 'Nothing yet';
  }

  /* The same five figures the build put here, recomputed. Every one is read
     straight off the recipes, so nothing on this band depends on the shopping
     list having been worked out yet. */
  /* `all` is everything picked, `dinners` only the evening meals. The counts
     cover everything; the protein and fibre averages cover the dinners alone
     and say so, because averaging a bowl of yoghurt into a protein-a-serving
     figure would drag it somewhere it does not describe. */
  function bandCells(all) {
    const dinner = all.filter(r => r.sec === 'dinner');
    const n = dinner.length || 1;
    const extra = all.length - dinner.length;
    return [
      [all.length, extra ? 'Meals' : (all.length === 1 ? 'Dinner' : 'Dinners')],
      [sum(all.map(r => r.min)), 'Minutes, all in'],
      [Math.round(sum(dinner.map(r => r.pr)) / n) + ' g',
        extra ? 'Protein a dinner, average' : 'Protein a serving, average'],
      [Math.round(sum(dinner.map(r => r.fb)) / n) + ' g',
        extra ? 'Fibre a dinner, average' : 'Fibre a serving, average'],
      [state.serves, 'Serves'],
    ];
  }

  function renderBand() {
    const week = allPicked().map(n => BY_NUM.get(n)).filter(Boolean);
    $('#wkband').innerHTML = bandCells(week).map(([v, k]) =>
      `<div><b class="d">${v}</b><span>${esc(k)}</span></div>`).join('');
    // Both of these are written into the HTML at build time from the week the
    // page ships with, and both are wrong the moment somebody picks another.
    // The first is invisible on screen until it prints, which is exactly how
    // it would go unnoticed.
    const head = $('.printhead');
    if (head) head.textContent = 'The 20-Minute Table — ' + planTitle().toLowerCase();
    const note = $('.plan-note');
    if (note && week.length) {
      note.innerHTML = 'The first is the shopping list and then every recipe in full, ' +
        'laid out to print &mdash; about ' + word(week.length + 2) +
        ' sheets of paper, and the week is on the fridge door. The second is the ' +
        'list on its own.';
    }
  }

  /* What the week is, in numbers the page can stand behind — and the misses
     alongside the hits. No comparison with anybody's requirement: nothing here
     knows how old you are, how big you are or what else you ate today. */
  function renderReport(caps, alternatives) {
    const week = state.picked.dinner.map(n => BY_NUM.get(n)).filter(Boolean);
    const el = $('#report');
    if (!week.length) { el.innerHTML = ''; return; }
    const n = week.length;
    const srcs = [...new Set(week.map(r => r.src))];
    const regions = [...new Set(week.map(r => r.g))];
    const methods = [...new Set(week.map(r => r.ml))];
    const fam = new Map();
    for (const r of week) fam.set(r.fam, (fam.get(r.fam) || 0) + 1);
    const worst = [...fam.entries()].sort((a, b) => b[1] - a[1])[0];
    const veg = week.filter(isVeg).length;
    const prot = week.map(r => r.pr);
    const kcal = week.map(r => r.kc);
    const lowFibre = week.filter(r => r.fb <= T.fibreLowNight).length;
    const repeats = n - new Set(week.map(r => r.c)).size;

    const lines = [];
    lines.push(`<b>${cap(word(srcs.length))} protein${srcs.length === 1 ? '' : 's'}</b> over ${word(n)} night${n === 1 ? '' : 's'} — ${srcs.join(', ').toLowerCase()}.`);
    lines.push(`<b>${cap(word(regions.length))} part${regions.length === 1 ? '' : 's'} of the world</b>, and ${repeats ? word(repeats) + ' repeated cuisine' + (repeats === 1 ? '' : 's') : 'no cuisine twice'}.`);
    lines.push(methods.length === 1
      ? `<b>One way of cooking</b> — ${methods[0].toLowerCase()} every night, which is what your ticks left.`
      : `<b>${cap(word(methods.length))} ways of cooking</b> — ${methods.join(', ').toLowerCase()} — so it is not the same washing up every night.`);
    lines.push(veg
      ? `<b>${cap(word(veg))} meat-free night${veg === 1 ? '' : 's'}.</b>`
      : `<b>No meat-free night</b>${caps.veg ? '.' : ', because the ticks above leave none to pick from.'}`);
    lines.push(`<b>Protein ${Math.min(...prot)}&ndash;${Math.max(...prot)} g a serving</b>, ${Math.round(sum(prot) / n)} g on average, and every night above ${Math.min(...prot) >= 30 ? '30' : '25'} g.`);
    lines.push(`<b>${Math.min(...kcal)}&ndash;${Math.max(...kcal)} kcal a serving</b>, and ${lowFibre ? word(lowFibre) + ' night' + (lowFibre === 1 ? '' : 's') : 'no night'} at or below ${T.fibreLowNight} g of fibre.`);

    const notes = [];
    if (worst && worst[1] > Math.ceil(n / 3)) {
      // `minFamilyMax` is the provably smallest largest-family this pool can
      // reach. Only when the week has hit that floor is the repeat genuinely
      // the filter's doing rather than this particular pick's.
      notes.push(caps.minFamilyMax && worst[1] <= caps.minFamilyMax
        ? `${cap(worst[0])} comes round ${word(worst[1])} times, which is as few as these ticks allow.`
        : `${cap(worst[0])} comes round ${word(worst[1])} times. Picking again would spread it.`);
    }
    if (caps.sources && caps.sources < 3) {
      notes.push(`Your ticks leave ${word(caps.sources)} protein${caps.sources === 1 ? '' : 's'} to choose between, so that is what the week has.`);
    }
    const extra = COURSES.slice(1).reduce((a, c) => a + state.picked[c[0]].length, 0);
    if (extra) {
      notes.push(`These figures are the ${word(n)} dinner${n === 1 ? '' : 's'} alone. The ${word(extra)} other meal${extra === 1 ? '' : 's'} you picked ${extra === 1 ? 'is' : 'are'} on the shopping list but not in the count.`);
    }
    const others = Math.max(0, (alternatives || 0) - 1);
    if (others) {
      notes.push(`${cap(word(others))} other week${others === 1 ? '' : 's'} came out within a point and a half of this one. Pick again to see one.`);
    }
    el.innerHTML = `<ul class="rlist">${lines.map(g => `<li>${g}</li>`).join('')}</ul>` +
      (notes.length ? `<p class="rnote">${notes.join(' ')}</p>` : '');
  }

  function row(i) {
    return `<li data-k="${esc(i.key)}"${state.hideTicked && state.ticked.has(i.key) ? ' hidden' : ''}>
      <label><input type="checkbox" data-key="${esc(i.key)}"${state.ticked.has(i.key) ? ' checked' : ''}>
      <span>${esc(i.name)}</span>${i.qty ? `<b class="gqty">${esc(i.qty)}</b>` : ''}${
        i.from.length > 1 ? `<em>${i.from.length} dinners</em>` : ''}</label></li>`;
  }

  /* The week's shape, drawn as one square a night grouped by what it is.
     Identity is carried by the label beside each group rather than by colour:
     the book's four method colours are quiet earth tones chosen to sit under
     text, and a bar made of them fails a colourblind-separation check — two of
     them are 4 ΔE apart under protanopia. Squares and words do not have that
     problem, and five nights is a small enough number to count. */
  const SPREADS = [
    ['Protein', r => r.fam],
    ['The pan', r => r.ml],
    ['Where it is from', r => r.g],
  ];

  function renderSpread() {
    const week = state.week.map(n => BY_NUM.get(n)).filter(Boolean);
    const el = $('#spread');
    if (!week.length) { el.innerHTML = ''; return; }
    el.innerHTML = SPREADS.map(([label, key]) => {
      const counts = new Map();
      for (const r of week) counts.set(key(r), (counts.get(key(r)) || 0) + 1);
      const groups = [...counts.entries()]
        .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
      const cells = groups.map(([name, n]) =>
        `<span class="spg"><span class="spd" role="img" aria-label="${word(n)} night${n === 1 ? '' : 's'}">` +
        `${'<i></i>'.repeat(n)}</span><b>${esc(cap(name))}</b></span>`).join('');
      return `<div class="sprow"><span class="spk">${label}</span>` +
        `<div class="spgs">${cells}</div></div>`;
    }).join('');
  }

  function renderShop() {
    const list = shoppingList();
    const groups = grouped(list);
    const staples = cupboard(list);
    const total = sum(groups.map(g => g.items.length));
    $('#shopcount').textContent = total + (total === 1 ? ' thing' : ' things');
    $('#glist').innerHTML = groups.map(g => `
      <div class="shelf gaisle">
        <h3>${esc(g.label)}<span>${g.items.length}</span></h3>
        <ul>${g.items.map(row).join('')}</ul>
      </div>`).join('');
    const cup = $('#cupboard');
    cup.hidden = !staples.length;
    if (staples.length) {
      $('#cupcount').textContent = staples.length +
        (staples.length === 1 ? ' thing' : ' things');
      $('#cuplist').innerHTML = `<div class="shelf"><ul>${staples.map(row).join('')}</ul></div>`;
    }
    updateCount();
  }

  function updateCount() {
    const boxes = $$('#glist input[type=checkbox]');
    const done = boxes.filter(b => b.checked).length;
    $('#gcount').textContent = boxes.length
      ? `${done} of ${boxes.length} in the trolley`
      : 'Nothing to buy';
  }

  function applyHide() {
    for (const li of $$('#glist li, #cuplist li')) {
      const box = li.querySelector('input');
      li.hidden = state.hideTicked && box && box.checked;
    }
  }

  function poolLine() {
    const size = pool().length;
    const el = $('#pool');
    const total = DATA.recipes.filter(r => r.sec === 'dinner').length;
    let text;
    if (!size) {
      text = state.eat.size === 0 ? 'Nothing matches. Tick at least one thing you eat.'
        : state.pans.size === 0 ? 'Nothing matches. Tick at least one pan.'
        : 'Nothing matches those ticks together. Put one of them back.';
    } else if (size < state.want.dinner) {
      text = `${size} of the ${total} dinners match — ${word(state.want.dinner - size)} short of ${word(state.want.dinner)}.`;
    } else if (size === state.want.dinner) {
      text = `${size} of the ${total} dinners match. Exactly ${word(state.want.dinner)}, with nothing spare to swap in.`;
    } else {
      text = `${size} of the ${total} dinners match. Enough for ${word(state.want.dinner)}.`;
    }
    el.textContent = text;
    el.classList.toggle('warn', size < state.want.dinner);
    $('#pick').textContent = state.hasPicked ? 'Pick a different week' : 'Pick these meals';
  }

  function renderAll(caps, alternatives) {
    const c = caps || poolCaps(pool(), state.picked.dinner.length || state.want.dinner);
    renderWeek();
    renderBand();
    renderSpread();
    renderReport(c, alternatives || 0);
    renderShop();
    poolLine();
    if ($('#find') && $('#find').value) renderFind();
    const short = $('#short');
    const size = pool().length;
    // Only when the pool is genuinely the limit. Turning the Dinners chip up
    // without picking again also leaves a short week, and blaming the diet
    // ticks for that would be a lie.
    const dn = state.picked.dinner.length;
    if (dn && size && size < state.want.dinner && dn < state.want.dinner) {
      short.hidden = false;
      short.innerHTML = `<b>${cap(word(dn))} night${dn === 1 ? '' : 's'}, not ${word(state.want.dinner)}.</b> Only ${word(size)} dinner${size === 1 ? '' : 's'} match those ticks, and a week is never padded out with a repeat. Untick something above, or cook fewer nights.`;
    } else {
      short.hidden = true;
    }
  }

  const say = msg => { $('#say').textContent = msg; };

  /* Looking a dinner up rather than being handed one. The index is built once
     from everything the planner can pick — the title, the cuisine, the region,
     the protein, the pan and every ingredient the recipe lists — so `anchovy`
     and `Peruvian` and `air fryer` all find their way there. It is the same
     material the recipe index searches, and it is searched the same way. */
  const FIND_INDEX = DATA.recipes.map(r => ({
    r,
    hay: [r.n, r.t, r.c, r.g, r.src, r.ml, COURSE_LABEL.get(r.sec) || '',
      r.ing.map(e => e.n).join(' ')].join(' ').toLowerCase(),
  }));

  function findMatches(q) {
    const needle = q.trim().toLowerCase();
    if (needle.length < 2) return [];
    const words = needle.split(/\s+/);
    return FIND_INDEX
      .filter(x => words.every(w => x.hay.includes(w)))
      // A title match is what somebody typing a dish name wants first.
      .sort((a, b) => {
        const at = a.r.t.toLowerCase().includes(needle) ? 0 : 1;
        const bt = b.r.t.toLowerCase().includes(needle) ? 0 : 1;
        return at - bt || a.r.n.localeCompare(b.r.n);
      })
      .slice(0, 8)
      .map(x => x.r);
  }

  function renderFind() {
    const box = $('#find');
    const list = $('#find-results');
    const matches = findMatches(box.value);
    $('#find-clear').hidden = !box.value;
    if (!box.value.trim()) {
      list.hidden = true; list.innerHTML = '';
      box.setAttribute('aria-expanded', 'false');
      return;
    }
    const inWeek = new Set(allPicked());
    list.hidden = false;
    box.setAttribute('aria-expanded', 'true');
    if (!matches.length) {
      list.innerHTML = '<li class="find-none">Nothing matches that.</li>';
      return;
    }
    list.innerHTML = matches.map(r => {
      const has = inWeek.has(r.n);
      return `<li role="option" aria-selected="false">
        <button class="find-hit" type="button" data-add="${r.n}"${has ? ' disabled' : ''}>
          <span class="find-num d" style="color:${r.col}">${r.n}</span>
          <span class="find-t d">${esc(r.t)}</span>
          <span class="find-meta">${esc(COURSE_LABEL.get(r.sec) || '')} · ${esc(r.ml)} · ${esc(r.c)}</span>
          <span class="find-add">${has ? 'Already in' : 'Add'}</span>
          <span class="cmin d">${r.min}<i>min</i></span>
        </button></li>`;
    }).join('');
  }

  function addRecipe(numStr) {
    const r = BY_NUM.get(numStr);
    if (!r || allPicked().includes(numStr)) return;
    const course = state.picked[r.sec] ? r.sec : 'dinner';
    state.picked[course].push(numStr);
    state.want[course] = state.picked[course].length;
    state.week = state.picked.dinner;
    state.cursors.clear();
    state.hasPicked = true;
    syncControls();
    writeHash(false);
    renderAll();
    say(`${r.t} added. The list has been updated.`);
  }

  function dropRecipe(course, slot) {
    const list = state.picked[course];
    const r = BY_NUM.get(list[slot]);
    list.splice(slot, 1);
    state.want[course] = list.length;
    state.week = state.picked.dinner;
    state.cursors.clear();
    syncControls();
    writeHash(false);
    renderAll();
    say(`${r ? r.t : 'That meal'} taken out. The list has been updated.`);
  }

  // ------------------------------------------------------------ the actions

  function pick() {
    let res = { caps: null, alternatives: 0 };
    for (const [key] of COURSES) {
      const n = state.want[key] || 0;
      if (!n) { state.picked[key] = []; continue; }
      const r = pickWeek(n, state.picked[key], key);
      state.picked[key] = r.set.map(x => x.n);
      if (key === 'dinner') res = r;
    }
    state.week = state.picked.dinner;
    state.ticked.clear();
    state.cursors.clear();
    state.hasPicked = true;
    writeHash(true);
    renderAll(res.caps, res.alternatives);
    const total = allPicked().length;
    say(`${cap(word(total))} meal${total === 1 ? '' : 's'} picked. The list has been rewritten.`);
    if (!matchMedia('(prefers-reduced-motion: reduce)').matches) {
      $('#week').scrollIntoView({ block: 'start' });
    }
  }

  function planTitle() {
    const d = state.picked.dinner.length;
    const extra = COURSES.slice(1).reduce((a, c) => a + state.picked[c[0]].length, 0);
    const head = d ? `${cap(word(d))} dinner${d === 1 ? '' : 's'}` : 'A week';
    const tail = extra ? ` and ${word(extra)} other meal${extra === 1 ? '' : 's'}` : '';
    return `${head}${tail} for ${word(state.serves)}`;
  }


  /* The recipes in full are a separate asset, because they are twice the size
     of everything else the page needs and most visits never ask for them. It
     is a script rather than a fetch, so a copy of the site opened from a
     folder works the same as one on a server. */
  let packLoading = null;

  function loadRecipes() {
    if (window.PLAN_RECIPES) return Promise.resolve(window.PLAN_RECIPES);
    if (packLoading) return packLoading;
    packLoading = new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = 'assets/recipes.js' + (DATA.v ? '?v=' + DATA.v : '');
      s.onload = () => resolve(window.PLAN_RECIPES);
      s.onerror = () => reject(new Error('assets/recipes.js did not load'));
      document.head.appendChild(s);
    });
    return packLoading;
  }

  function pdfDoc(recipes) {
    const list = shoppingList();
    const groups = grouped(list);
    const staples = cupboard(list);
    const week = allPicked().map(n => BY_NUM.get(n)).filter(Boolean);
    const scaleNote = state.serves === BASE_SERVES
      ? `Every recipe serves ${word(BASE_SERVES)}, and these amounts are the sum of all ${word(week.length)}.`
      : `Every recipe is written for ${word(BASE_SERVES)}; the amounts on the list are scaled to ${word(state.serves)} — whole things and tins rounded up, weights to the nearest sensible figure. The recipes themselves are printed as written, for ${word(BASE_SERVES)}.`;
    const section = g => ({
      name: g.label,
      note: g.note || '',
      items: g.items.map(i => ({
        qty: i.qty, name: i.name,
        note: i.from.length > 1 ? 'for ' + i.from.join(', ') : '',
      })),
    });
    return {
      title: recipes ? 'A week of dinners' : 'Shopping list',
      subtitle: 'The 20-Minute Table',
      standfirst: planTitle() + '. ' + scaleNote,
      meals: week.map(r => `${r.n} · ${r.t} · ${r.min} min`),
      sections: groups.map(section).concat(staples.length
        ? [section({ label: 'From the cupboard', note: 'check before you buy',
          items: staples })]
        : []),
      recipes: recipes || null,
      footnote: 'twentyminutetable.hackerbay.io',
    };
  }

  function writePdf(doc, filename, label, was) {
    try {
      window.TMTPdf.download(window.TMTPdf.build(doc), filename);
      label.textContent = was;
      say('The PDF has been downloaded.');
    } catch (err) {
      label.textContent = 'The PDF would not write';
      console.error(err);
    }
  }

  function asText() {
    const list = shoppingList();
    const week = allPicked().map(n => BY_NUM.get(n)).filter(Boolean);
    const lines = ['The 20-Minute Table — ' + planTitle().toLowerCase(), ''];
    for (const r of week) lines.push(`${r.n}  ${r.t}  (${r.min} min)`);
    lines.push('');
    const blocks = grouped(list).concat(
      cupboard(list).length
        ? [{ label: 'From the cupboard — check before you buy', items: cupboard(list) }]
        : []);
    for (const g of blocks) {
      lines.push(g.label.toUpperCase());
      for (const i of g.items) {
        lines.push('  [ ] ' + i.name + (i.qty ? '  —  ' + i.qty : ''));
      }
      lines.push('');
    }
    lines.push('twentyminutetable.hackerbay.io');
    return lines.join('\n');
  }

  // ------------------------------------------------------------------ wire

  function syncControls() {
    // A hand-written address, or a dinner added by hand, can name a number the
    // control does not offer. Rather than leaving a row with nothing selected,
    // the nearest value it does offer is chosen.
    for (const [key] of COURSES) {
      const name = key === 'dinner' ? 'nights' : key;
      const inputs = $$('.pctl input[name=' + name + ']');
      if (!inputs.length) continue;
      const offered = inputs.map(el => +el.value);
      if (!offered.includes(state.want[key])) {
        state.want[key] = offered.reduce((best, v) =>
          Math.abs(v - state.want[key]) < Math.abs(best - state.want[key]) ? v : best,
          offered[0]);
      }
      inputs.forEach(el => { el.checked = +el.value === state.want[key]; });
    }
    $$('.pctl input[name=serves]').forEach(el => { el.checked = +el.value === state.serves; });
    $$('.pctl input[name=eat]').forEach(el => { el.checked = state.eat.has(el.value); });
    $$('.pctl input[name=pan]').forEach(el => { el.checked = state.pans.has(el.value); });
  }

  function wire() {
    $('#pctl').addEventListener('submit', e => { e.preventDefault(); pick(); });
    $('#pctl').addEventListener('change', e => {
      const el = e.target;
      if (el.name === 'nights' || el.name === 'breakfast' || el.name === 'afters') {
        state.want[el.name === 'nights' ? 'dinner' : el.name] = +el.value;
        writeHash(false);
        poolLine();
      }
      else if (el.name === 'serves') {
        state.serves = +el.value; writeHash(false); renderBand(); renderShop();
      } else if (el.name === 'eat' || el.name === 'pan') {
        const set = el.name === 'eat' ? state.eat : state.pans;
        if (el.checked) set.add(el.value); else set.delete(el.value);
        state.cursors.clear();
        writeHash(false);
        poolLine();
      }
    });

    $('#plan-all').addEventListener('click', () => {
      state.eat = new Set(ALL_TAGS);
      state.pans = new Set(ALL_PANS);
      syncControls();
      pick();
    });

    const onWeekClick = e => {
      const drop = e.target.closest('[data-drop]');
      if (drop) { dropRecipe(drop.dataset.course, +drop.dataset.drop); return; }
      const btn = e.target.closest('[data-slot]');
      if (!btn) return;
      const course = btn.dataset.course || 'dinner';
      const slot = +btn.dataset.slot;
      const next = nextForSlot(course, slot);
      if (!next) {
        const none = document.createElement('span');
        none.className = 'n-none';
        none.textContent = 'Nothing else matches';
        btn.replaceWith(none);
        say('There is nothing else to put in that place.');
        return;
      }
      state.picked[course][slot] = next.n;
      state.week = state.picked.dinner;
      writeHash(false);
      renderAll();
      say(`That ${course === 'dinner' ? 'dinner' : 'one'} is now ${next.t}. The list has been updated.`);
      const b = $(`[data-course="${course}"][data-slot="${slot}"]`);
      if (b) b.focus();
    };
    $('#weeklist').addEventListener('click', onWeekClick);
    $('#course-extra').addEventListener('click', onWeekClick);

    let findTimer;
    $('#find').addEventListener('input', () => {
      clearTimeout(findTimer);
      findTimer = setTimeout(renderFind, 90);
    });
    $('#find').addEventListener('keydown', e => {
      if (e.key === 'Escape') { $('#find').value = ''; renderFind(); }
      if (e.key === 'ArrowDown') {
        const first = $('#find-results .find-hit:not([disabled])');
        if (first) { e.preventDefault(); first.focus(); }
      }
    });
    $('#find-clear').addEventListener('click', () => {
      $('#find').value = ''; renderFind(); $('#find').focus();
    });
    $('#find-results').addEventListener('click', e => {
      const hit = e.target.closest('[data-add]');
      if (!hit) return;
      addRecipe(hit.dataset.add);
      $('#find').value = '';
      renderFind();
      $('#find').focus();
    });
    $('#find-results').addEventListener('keydown', e => {
      const hits = $$('#find-results .find-hit:not([disabled])');
      const i = hits.indexOf(document.activeElement);
      if (e.key === 'ArrowDown' && i > -1 && hits[i + 1]) { e.preventDefault(); hits[i + 1].focus(); }
      if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (i > 0) hits[i - 1].focus(); else $('#find').focus();
      }
      if (e.key === 'Escape') { $('#find').value = ''; renderFind(); $('#find').focus(); }
    });

    const onTick = e => {
      const box = e.target.closest('input[type=checkbox]');
      if (!box) return;
      if (box.checked) state.ticked.add(box.dataset.key);
      else state.ticked.delete(box.dataset.key);
      updateCount();
      if (!state.hideTicked) return;
      // The row is about to disappear from under the cursor. Hiding an element
      // that holds the focus sends the focus to the body, which sends somebody
      // working down the list by keyboard back to the top of the page.
      const boxes = $$('#glist input[type=checkbox], #cuplist input[type=checkbox]');
      const next = boxes.slice(boxes.indexOf(box) + 1).find(b => !b.checked);
      applyHide();
      (next || $('#hide-ticked')).focus();
    };
    $('#glist').addEventListener('change', onTick);
    $('#cuplist').addEventListener('change', onTick);

    $('#hide-ticked').addEventListener('click', e => {
      state.hideTicked = !state.hideTicked;
      e.currentTarget.setAttribute('aria-pressed', String(state.hideTicked));
      applyHide();
    });

    // The original wording is remembered on the element, so pressing a button
    // twice in quick succession cannot leave `Gathering the recipes…` behind.
    const restingLabel = btn => {
      const el = btn.querySelector('span') || btn;
      if (!el.dataset.was) el.dataset.was = el.textContent;
      return el;
    };

    $('#plan-pdf').addEventListener('click', e => {
      const label = restingLabel(e.currentTarget);
      const was = label.dataset.was;
      if (!window.TMTPdf) { label.textContent = 'The PDF writer did not load'; return; }
      writePdf(pdfDoc(null), 'shopping-list.pdf', label, was);
    });

    $('#plan-pack').addEventListener('click', async e => {
      const label = restingLabel(e.currentTarget);
      const was = label.dataset.was;
      if (!window.TMTPdf) { label.textContent = 'The PDF writer did not load'; return; }
      label.textContent = 'Gathering the recipes…';
      try {
        const pack = await loadRecipes();
        const recipes = allPicked().map(n => pack[n]).filter(Boolean);
        writePdf(pdfDoc(recipes), 'a-week-of-dinners.pdf', label, was);
      } catch (err) {
        label.textContent = 'The recipes would not load';
        console.error(err);
        setTimeout(() => { label.textContent = was; }, 2500);
      }
    });
    $('#plan-copy').addEventListener('click', async e => {
      const label = restingLabel(e.currentTarget);
      const was = label.dataset.was;
      try {
        await navigator.clipboard.writeText(asText());
        label.textContent = 'Copied';
      } catch (err) {
        label.textContent = 'Could not copy';
      }
      setTimeout(() => { label.textContent = was; }, 1800);
    });

    // The cupboard is collapsed on screen and has to be open to print.
    window.addEventListener('beforeprint', () => {
      const d = $('#cupboard');
      if (d && !d.open) { d.dataset.wasShut = '1'; d.open = true; }
    });
    window.addEventListener('afterprint', () => {
      const d = $('#cupboard');
      if (d && d.dataset.wasShut) { d.open = false; delete d.dataset.wasShut; }
    });

    window.addEventListener('hashchange', () => {
      if (readHash()) { syncControls(); state.cursors.clear(); renderAll(); }
    });
  }

  readHash();
  syncControls();
  wire();
  writeHash(false);
  renderAll();
})();

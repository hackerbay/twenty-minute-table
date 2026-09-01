(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];

  /* ---------------- index filtering ---------------- */
  const results = $('#results');
  if (results) {
    const cards = $$('.card', results);
    const chips = $$('.chip[data-filter]');
    const q = $('#q'), count = $('#count'), clear = $('#clear'), empty = $('#empty');
    const state = { method: new Set(), section: new Set(), veg: false, max: 0, q: '' };

    function apply() {
      let shown = 0;
      for (const c of cards) {
        const ok =
          (!state.method.size || state.method.has(c.dataset.method)) &&
          (!state.section.size || state.section.has(c.dataset.section)) &&
          (!state.veg || c.dataset.veg === '1') &&
          (!state.max || +c.dataset.min <= state.max) &&
          (!state.q || c.dataset.search.includes(state.q));
        c.hidden = !ok;
        if (ok) shown++;
      }
      for (const h of $$('.sect', results)) {
        const grid = h.nextElementSibling;
        const any = $$('.card', grid).some(c => !c.hidden);
        h.hidden = !any; grid.hidden = !any;
      }
      const active = state.method.size || state.section.size || state.veg || state.max || state.q;
      count.textContent = shown === cards.length
        ? `${cards.length} recipes`
        : `${shown} of ${cards.length} recipes`;
      clear.hidden = !active;
      empty.hidden = shown !== 0;
    }

    chips.forEach(ch => ch.addEventListener('click', () => {
      const { filter, value } = ch.dataset;
      const on = ch.getAttribute('aria-pressed') === 'true';
      if (filter === 'veg') state.veg = !on;
      else if (filter === 'max') state.max = on ? 0 : +value;
      else { const set = state[filter]; on ? set.delete(value) : set.add(value); }
      ch.setAttribute('aria-pressed', String(!on));
      apply();
    }));

    let t;
    q.addEventListener('input', () => {
      clearTimeout(t);
      t = setTimeout(() => { state.q = q.value.trim().toLowerCase(); apply(); }, 110);
    });

    function reset() {
      state.method.clear(); state.section.clear(); state.veg = false; state.max = 0; state.q = '';
      q.value = ''; chips.forEach(c => c.setAttribute('aria-pressed', 'false')); apply();
    }
    clear.addEventListener('click', reset);
    $$('[data-clear]').forEach(b => b.addEventListener('click', reset));
    chips.forEach(c => c.setAttribute('aria-pressed', 'false'));
    apply();
  }

  /* ---------------- recipe page ---------------- */
  $$('.sdone').forEach(b => b.addEventListener('click', () => {
    b.closest('.step').classList.toggle('done');
  }));
  const resetIngs = $('#reset-ings');
  if (resetIngs) resetIngs.addEventListener('click',
    () => $$('.inglist input').forEach(i => { i.checked = false; }));
  const resetPantry = $('#reset-pantry');
  if (resetPantry) resetPantry.addEventListener('click',
    () => $$('.shelf input').forEach(i => { i.checked = false; }));

  /* ---------------- download menu ---------------- */
  /* <details> already opens, closes and handles the keyboard by itself. All this
     adds is the two things it does not do: shut when you click away, and shut on
     Escape. With scripting off the menu still works, it just stays open. */
  const dlm = $('.dlm');
  if (dlm) {
    document.addEventListener('click', e => {
      if (dlm.open && !dlm.contains(e.target)) dlm.open = false;
    });
    document.addEventListener('keydown', e => {
      if (e.key === 'Escape' && dlm.open) {
        dlm.open = false;
        $('summary', dlm).focus();
      }
    });
  }
})();

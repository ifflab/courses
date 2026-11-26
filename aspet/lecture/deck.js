// Slide engine: 1920×1080 stage scaled to the window, build steps, keyboard/pointer control.
// Slides may hook their own animations:
//   slide.addEventListener('step', e => { e.detail.step, e.detail.dir })  // fired on every step change and on entering
// <section class="slide" data-hidden>: skipped by sequential navigation, unnumbered, absent from the overview;
//   reachable only by direct link (#N) or typing its number.
(() => {
  const deck = document.getElementById('deck');
  if (location.search.includes('shot')) document.body.classList.add('no-anim');
  const slides = [...deck.querySelectorAll(':scope > section.slide')];
  const N = slides.length;
  const isHidden = i => slides[i].hasAttribute('data-hidden');
  const vis = slides.filter((s, i) => !isHidden(i));
  const nextVis = (i, d) => { for (let j = i + d; j >= 0 && j < N; j += d) if (!isHidden(j)) return j; return -1; };
  let cur = 0, step = 0, typed = '';

  // collect steps per slide
  for (const s of slides) {
    const frags = [...s.querySelectorAll('.f, [data-f-out]')];
    let auto = 0;
    for (const f of frags) {
      if (!f.classList.contains('f')) continue;
      if (f.dataset.f) auto = Math.max(auto, +f.dataset.f);
      else f.dataset.f = ++auto;
    }
    const outs = frags.map(f => +f.dataset.fOut || 0);
    s._steps = Math.max(+s.dataset.steps || 0, auto, ...outs, 0);
    s._frags = frags;
  }

  // chrome + numbering
  const title = document.body.dataset.footer || '';
  slides.forEach((s, i) => {
    const c = document.createElement('div');
    c.className = 'chrome';
    c.innerHTML = `<span>${title}</span><span>${isHidden(i) ? '' : `${vis.indexOf(s) + 1} / ${vis.length}`}</span>`;
    s.appendChild(c);
  });
  const prog = document.createElement('div'); prog.id = 'progress'; deck.appendChild(prog);
  const blank = document.createElement('div'); blank.id = 'blank'; document.body.appendChild(blank);
  const gotoBox = document.createElement('div'); gotoBox.id = 'goto'; document.body.appendChild(gotoBox);

  function fit() {
    if (document.body.classList.contains('overview')) return;
    const k = Math.min(innerWidth / 1920, innerHeight / 1080);
    deck.style.transform = `scale(${k}) translate(-50%, -50%)`;
    deck.style.transformOrigin = '0 0';
    deck.style.left = '50%'; deck.style.top = '50%';
  }

  function render(dir = 0) {
    slides.forEach((s, i) => s.classList.toggle('active', i === cur));
    const s = slides[cur];
    s.dataset.step = step;
    for (const f of s._frags) {
      const a = +f.dataset.f || 0, o = +f.dataset.fOut || Infinity;
      f.classList.toggle('on', f.classList.contains('f') ? step >= a : true);
      f.classList.toggle('gone', step >= o);
    }
    prog.style.width = `${isHidden(cur) ? 100 : (100 * (vis.indexOf(s) + 1)) / vis.length}%`;
    history.replaceState(null, '', `#${cur + 1}` + (step ? `.${step}` : ''));
    s.dispatchEvent(new CustomEvent('step', { detail: { step, dir } }));
  }

  function go(i, k = 0, dir = 0) {
    cur = Math.max(0, Math.min(N - 1, i));
    step = k === 'end' ? slides[cur]._steps : Math.max(0, Math.min(slides[cur]._steps, k));
    // entering a slide: jump to its state with no transitions (else it animates from the state it was left in)
    slides[cur].classList.add('snap');
    render(dir);
    requestAnimationFrame(() => requestAnimationFrame(() => slides[cur].classList.remove('snap')));
  }
  const next = () => step < slides[cur]._steps ? (step++, render(1)) : nextVis(cur, 1) >= 0 && go(nextVis(cur, 1), 0, 1);
  const prev = () => step > 0 ? (step--, render(-1)) : nextVis(cur, -1) >= 0 && go(nextVis(cur, -1), 'end', -1);

  function toggleOverview() {
    const on = document.body.classList.toggle('overview');
    if (on) { deck.style.transform = 'none'; slides[cur].scrollIntoView({ block: 'center' }); }
    else fit();
  }

  addEventListener('keydown', e => {
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key;
    if (/^[0-9]$/.test(k)) { typed += k; gotoBox.textContent = `→ ${typed}`; gotoBox.style.display = 'block'; return; }
    if (typed && (k === 'Enter' || k === 'g')) { go(+typed - 1); typed = ''; gotoBox.style.display = 'none'; e.preventDefault(); return; }
    typed = ''; gotoBox.style.display = 'none';
    if (blank.className && !['b', '.', 'w', 'B'].includes(k)) { blank.className = ''; }
    switch (k) {
      case 'ArrowRight': case 'ArrowDown': case 'PageDown': case ' ': case 'Enter': case 'n':
        if (e.shiftKey && k === 'ArrowRight') { if (nextVis(cur, 1) >= 0) go(nextVis(cur, 1)); } else next(); break;
      case 'ArrowLeft': case 'ArrowUp': case 'PageUp': case 'Backspace': case 'p':
        if (e.shiftKey && k === 'ArrowLeft') { if (nextVis(cur, -1) >= 0) go(nextVis(cur, -1)); } else prev(); break;
      case 'Home': go(nextVis(-1, 1)); break;
      case 'End': go(nextVis(N, -1), 'end'); break;
      case 'f':
        document.fullscreenElement ? document.exitFullscreen() : document.documentElement.requestFullscreen(); break;
      case 'b': case 'B': case '.': blank.className = blank.className === 'black' ? '' : 'black'; break;
      case 'w': blank.className = blank.className === 'white' ? '' : 'white'; break;
      case 'o': case 'Escape': if (k === 'o' || document.body.classList.contains('overview')) toggleOverview(); break;
      default: return;
    }
    e.preventDefault();
  });
  deck.addEventListener('click', e => {
    if (!document.body.classList.contains('overview')) return;
    const s = e.target.closest('.slide'); if (!s) return;
    toggleOverview(); go(slides.indexOf(s));
  });

  addEventListener('resize', fit);
  const m = location.hash.match(/^#(\d+)(?:\.(\d+))?/);
  fit();
  if (m) go(+m[1] - 1, +(m[2] || 0)); else go(nextVis(-1, 1));

  if (window.renderMathInElement) renderMathInElement(deck, {
    delimiters: [{ left: '$$', right: '$$', display: true }, { left: '\\(', right: '\\)', display: false }, { left: '$', right: '$', display: false }],
    throwOnError: false,
  });
})();

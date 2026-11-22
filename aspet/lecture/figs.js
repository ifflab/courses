// Shared figure helpers, run before deck.js.
// <g class="charges" data-cx="0" data-cy="0" data-r0="150" data-r1="300" data-n="40" data-seed="1" data-sy="1"></g>
// fills the group with ± MM point charges scattered in an annulus (r0..r1, y squashed by sy).
// Each charge is <g class="q pos|neg"> so slides can style or animate them.
(() => {
  const NS = 'http://www.w3.org/2000/svg';
  for (const g of document.querySelectorAll('g.charges')) {
    const d = g.dataset, cx = +(d.cx || 0), cy = +(d.cy || 0), r0 = +(d.r0 || 150), r1 = +(d.r1 || 300);
    const n = +(d.n || 40), sy = +(d.sy || 1), qr = +(d.qr || 13), signs = d.signs !== 'no';
    let s = +(d.seed || 1);
    const rnd = () => (s = (s * 16807) % 2147483647) / 2147483647;
    const pts = [];
    for (let tries = 0; pts.length < n && tries < 20000; tries++) {
      const a = 2 * Math.PI * rnd(), r = Math.sqrt(r0 * r0 + (r1 * r1 - r0 * r0) * rnd());
      const x = cx + r * Math.cos(a), y = cy + sy * r * Math.sin(a);
      if (pts.every(p => (p[0] - x) ** 2 + (p[1] - y) ** 2 > (3.2 * qr) ** 2)) pts.push([x, y]);
    }
    pts.forEach(([x, y], i) => {
      const pos = rnd() < 0.5;
      const q = document.createElementNS(NS, 'g');
      q.setAttribute('class', 'q ' + (pos ? 'pos' : 'neg'));
      q.setAttribute('transform', `translate(${x.toFixed(1)} ${y.toFixed(1)})`);
      q.style.setProperty('--i', i);
      q.innerHTML = `<circle r="${qr}"/>` + (signs ? `<path d="M${-qr * .5} 0H${qr * .5}${pos ? `M0 ${-qr * .5}V${qr * .5}` : ''}"/>` : '');
      g.appendChild(q);
    });
  }
})();

#!/usr/bin/env python3
"""Generate the inline SVG figures of the hands-on deck (figs/*.svg) from data/ (outputs of the reference run).
Colours are CSS variables of ../lecture/deck.css, so the figures follow the deck palette.
Usage: python3 plots.py"""
import glob, math, pathlib
import numpy as np

here = pathlib.Path(__file__).parent
out = here / 'figs'
out.mkdir(exist_ok=True)
F = lambda v: f'{v:.1f}'
M = lambda v: f'{v:g}'.replace('-', '−')    # tick label with a real minus sign


class Frame:
    """Plot frame: data (x, y) -> pixel coordinates inside an svg of size W x H."""
    def __init__(s, W, H, xlim, ylim, m=(90, 40, 30, 80)):  # margins left, right, top, bottom
        s.W, s.H, s.xlim, s.ylim = W, H, xlim, ylim
        s.l, s.r, s.t, s.b = m

    def x(s, v): return s.l + (v - s.xlim[0]) / (s.xlim[1] - s.xlim[0]) * (s.W - s.l - s.r)
    def y(s, v): return s.H - s.b - (v - s.ylim[0]) / (s.ylim[1] - s.ylim[0]) * (s.H - s.t - s.b)

    def path(s, xs, ys):
        return 'M' + 'L'.join(f'{F(s.x(a))},{F(s.y(b))}' for a, b in zip(xs, ys))

    def axes(s, xticks, yticks, xlabel, ylabel, fs=26):
        o = [f'<g class="axes" font-size="{fs}" fill="var(--muted)">']
        y0, x0 = s.H - s.b, s.l
        o.append(f'<path d="M{x0},{s.t}V{y0}H{s.W - s.r}" fill="none" stroke="var(--fg)" stroke-width="2"/>')
        for v in xticks:
            o.append(f'<path d="M{F(s.x(v))},{y0}v10" stroke="var(--fg)" stroke-width="2"/>'
                     f'<text x="{F(s.x(v))}" y="{y0 + 40}" text-anchor="middle">{M(v)}</text>')
        for v in yticks:
            o.append(f'<path d="M{x0},{F(s.y(v))}h-10" stroke="var(--fg)" stroke-width="2"/>'
                     f'<text x="{x0 - 18}" y="{F(s.y(v) + 9)}" text-anchor="end">{v:g}</text>')
        o.append(f'<text x="{F((s.l + s.W - s.r) / 2)}" y="{s.H - 8}" text-anchor="middle" fill="var(--fg)">{xlabel}</text>')
        o.append(f'<text transform="translate(26 {F((s.t + s.H - s.b) / 2)}) rotate(-90)" text-anchor="middle" fill="var(--fg)">{ylabel}</text>')
        o.append('</g>')
        return '\n'.join(o)


def svg(W, H, body, cls=''):
    return f'<svg class="{cls}" viewBox="0 0 {W} {H}" width="{W}" height="{H}">\n{body}\n</svg>\n'


# ---------- data ----------
# pmf.dat (xi, F) from pmf.py (WHAM, no error estimate); us/win_NN.npz with xi (A), xi0 (A), k (kcal/mol/A^2)
xs, Fs = np.loadtxt(here / 'data/pmf.dat').T
wins = [(float(w['xi0']), w['xi']) for w in map(np.load, sorted(glob.glob(str(here / 'data/us/win_*.npz'))))]
k = k_us = float(np.load(sorted(glob.glob(str(here / 'data/us/win_*.npz')))[0])['k'])   # umbrella force constant (kcal/mol/A^2)


def smooth(x, y, n=400):
    """Monotone-ish smooth curve through points (Catmull-Rom on a dense grid)."""
    t = np.linspace(0, len(x) - 1, n)
    i = np.clip(t.astype(int), 0, len(x) - 2)
    u = t - i
    P = lambda a, j: a[np.clip(j, 0, len(a) - 1)]
    def cr(a):
        p0, p1, p2, p3 = P(a, i - 1), P(a, i), P(a, i + 1), P(a, i + 2)
        return 0.5 * (2 * p1 + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3)
    return cr(x), cr(y)


# ---------- PMF (step 4 result) ----------
# same definitions as pmf.py: TS = highest point, barrier from the reactant minimum (left of the TS)
ts = np.argmax(Fs)
mn = np.argmin(Fs[:ts])                          # reactant minimum
bar = Fs[ts] - Fs[mn]
dG = Fs[ts:].min() - Fs[mn]                      # reaction free energy
fr = Frame(1040, 640, (-1.6, 1.6), (0, 10 * math.ceil((Fs.max() + 1) / 10)), m=(100, 30, 30, 90))
o = [fr.axes([-1.5, -1, -0.5, 0, 0.5, 1, 1.5], range(0, int(fr.ylim[1]) + 1, 10), 'ξ = d(C–Cl₁) − d(C–Cl₂)  (Å)', 'F  (kcal/mol)')]
# barrier arrow on the reactant side: dashed guides at the TS and reactant-minimum heights
ax = fr.x(xs[mn]); tx = ax + 16                  # vertical arrow straight up from the reactant minimum
o.append(f'<path d="M{F(ax)},{F(fr.y(Fs[ts]))}H{F(fr.x(xs[ts]))}" stroke="var(--muted)" stroke-width="2" stroke-dasharray="8 8"/>')
o.append(f'<path d="M{F(ax)},{F(fr.y(Fs[mn]) - 4)}V{F(fr.y(Fs[ts]) + 4)}" stroke="var(--neg)" stroke-width="3" marker-start="url(#hs-ar)" marker-end="url(#hs-ar)"/>')
ym = fr.y(Fs[mn] + 0.78 * bar)                   # label in the empty corner under the barrier line
o.append(f'<text x="{F(tx)}" y="{F(ym)}" font-size="30" fill="var(--neg)" font-weight="600">ΔF‡ ≈ {bar:.0f}</text>')
o.append(f'<text x="{F(tx)}" y="{F(ym + 30)}" font-size="24" fill="var(--neg)">kcal/mol</text>')
sx, sy = smooth(xs, Fs)
o.append(f'<path d="{fr.path(sx, sy)}" fill="none" stroke="var(--accent)" stroke-width="4"/>')
for x, f_ in zip(xs, Fs):
    o.append(f'<circle cx="{F(fr.x(x))}" cy="{F(fr.y(f_))}" r="4.5" fill="var(--bg)" stroke="var(--accent-2)" stroke-width="2.5"/>')
defs = ('<defs><marker id="hs-ar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
        '<path d="M0,0L10,5L0,10z" fill="var(--neg)"/></marker></defs>')
(out / 'pmf.svg').write_text(svg(fr.W, fr.H, defs + '\n'.join(o), 'plot'))
# what pmf.py prints, for the terminal block on the PMF slide
(out / 'pmf_out.html').write_text(f'<span class="o">barrier = {bar:.1f} kcal/mol, reaction free energy = {dG:.1f} kcal/mol</span>')


# ---------- umbrella sampling: bias potentials + sampled histograms (slide "Run ... all windows") ----------
fs = 22
fr = Frame(820, 330, (-1.6, 1.6), (0, 1), m=(16, 16, 10, 58))
o = [f'<path d="M{fr.l},{fr.H - fr.b}H{fr.W - fr.r}" stroke="var(--fg)" stroke-width="2"/>']
for v in [-1.5, -1, -0.5, 0, 0.5, 1, 1.5]:
    o.append(f'<path d="M{F(fr.x(v))},{fr.H - fr.b}v10" stroke="var(--fg)" stroke-width="2"/>'
             f'<text x="{F(fr.x(v))}" y="{fr.H - fr.b + 34}" text-anchor="middle" font-size="{fs}" fill="var(--muted)">{M(v)}</text>')
o.append(f'<text x="{F(fr.x(1.25))}" y="{fr.H - fr.b + 34}" text-anchor="middle" font-size="{fs}" fill="var(--fg)">ξ (Å)</text>')
# free-energy profile on top, to show what the windows climb
sx, sy = smooth(xs, Fs)
o.append(f'<g class="f" data-f="3"><path d="{fr.path(sx, 0.06 + 0.9 * sy / Fs.max())}" fill="none" stroke="var(--neg)" stroke-width="4" stroke-dasharray="10 8" opacity=".7"/>'
         f'<text x="{F(fr.x(0.12))}" y="{F(fr.y(0.97))}" font-size="{fs + 2}" fill="var(--neg)">F(ξ)</text></g>')
# bias potentials 0.5 k (xi - xi0)^2, drawn up to 8 kcal/mol (= 0.9 of the plot height)
g = ['<g class="f" data-f="1">']
for i, (xi0, _) in enumerate(wins):
    d = math.sqrt(2 * 3 / k)
    x = np.linspace(xi0 - d, xi0 + d, 60)
    g.append(f'<path d="{fr.path(x, 0.4 * 0.5 * k * (x - xi0) ** 2 / 3)}" fill="none" stroke="var(--mm)" stroke-width="2.5"/>')
g.append('</g>')
o += g
# histograms (Gaussian KDE), normalised to equal peak height
g = ['<g class="f" data-f="2">']
grid = np.linspace(-1.6, 1.6, 700)
for i, (xi0, x) in enumerate(wins):
    bw = 1.6 * x.std() * len(x) ** -0.2
    p = np.exp(-0.5 * ((grid[:, None] - x[None, :]) / bw) ** 2).sum(1)
    p = 0.55 * p / p.max()
    m = p > 0.004
    gx, gp = grid[m], p[m]
    d = fr.path(gx, gp) + f'L{F(fr.x(gx[-1]))},{F(fr.y(0))}L{F(fr.x(gx[0]))},{F(fr.y(0))}Z'
    g.append(f'<path d="{d}" fill="var(--accent)" fill-opacity=".15" stroke="var(--accent)" stroke-width="2"/>')
g.append('</g>')
o += g
(out / 'us.svg').write_text(svg(fr.W, fr.H, '\n'.join(o), 'plot'))


# ---------- molecules ----------
COL = {'C': '#B4B4B4', 'H': '#FFFFFF', 'Cl': '#A9E9AB', 'O': '#F2A0A0', 'N': '#A9BDF2'}
RAD = {'C': 0.26, 'H': 0.17, 'Cl': 0.34, 'O': 0.26, 'N': 0.25}


def molecule(cx, cy, s, state, labels=True, psi=0.45):
    """Cl1-C-Cl2 along x; state: 'R' (xi=-1.4), 'TS' (xi=0), 'P' (xi=+1.4). s = px per Angstrom."""
    d1, d2, hx = {'R': (1.8, 3.2, 0.36), 'TS': (2.3, 2.3, 0.0), 'P': (3.2, 1.8, -0.36)}[state]
    at = [('Cl', -d1, 0, 0, 'Cl₁'), ('C', 0, 0, 0, ''), ('Cl', d2, 0, 0, 'Cl₂')]
    for th in (90, 210, 330):
        t = math.radians(th)
        at.append(('H', hx, 1.03 * math.sin(t), 1.03 * math.cos(t), ''))
    # view rotated by psi about the vertical axis, so the H umbrella reads as 3D
    P = []
    for e, x, y, z, lab in at:
        sx = x * math.cos(psi) + z * math.sin(psi)
        zz = -x * math.sin(psi) + z * math.cos(psi)
        P.append((e, cx + s * sx, cy - s * y, zz, lab))
    o = []
    C = P[1]
    for j in (3, 4, 5):
        o.append(f'<path d="M{F(C[1])},{F(C[2])}L{F(P[j][1])},{F(P[j][2])}" stroke="#000" stroke-width="{0.05 * s:.1f}"/>')
    for j, d in ((0, d1), (2, d2)):
        if d < 2.0:
            o.append(f'<path d="M{F(C[1])},{F(C[2])}L{F(P[j][1])},{F(P[j][2])}" stroke="#000" stroke-width="{0.05 * s:.1f}"/>')
        elif d < 2.6:
            o.append(f'<path d="M{F(C[1])},{F(C[2])}L{F(P[j][1])},{F(P[j][2])}" stroke="#000" stroke-width="{0.04 * s:.1f}" stroke-dasharray="{0.08 * s:.1f} {0.07 * s:.1f}"/>')
    for e, x, y, z, lab in sorted(P, key=lambda a: a[3]):
        r = RAD[e] * s * (1 + 0.08 * z)
        o.append(f'<circle cx="{F(x)}" cy="{F(y)}" r="{F(r)}" fill="{COL[e]}" stroke="#000" stroke-width="{max(2, 0.025 * s):.1f}"/>')
    if labels:
        for e, x, y, z, lab in P:
            if lab:
                o.append(f'<text x="{F(x)}" y="{F(y + RAD[e] * s + 34)}" text-anchor="middle" font-size="26" fill="var(--fg)">{lab}</text>')
    return '\n'.join(o), P


# reaction R -> TS -> P with xi = d1 - d2 (dimension arrows C-Cl1, C-Cl2 under each structure)
W, H, s = 1700, 300, 66
o = []
# lay the three molecules out with equal gaps; an arrow centred in each gap
G, A = 190, 80                                   # gap width, arrow length
mols = []
for st, xi in (('R', '−1.4'), ('TS', '0'), ('P', '+1.4')):
    m, P = molecule(0, 115, s, st)
    lo = min(x - RAD[e] * s for e, x, y, z, lab in P)
    hi = max(x + RAD[e] * s for e, x, y, z, lab in P)
    ya = 192                                     # dimension-arrow row, below the atom labels
    for (a, b), lab in (((P[0][1], P[1][1]), 'd₁'), ((P[1][1], P[2][1]), 'd₂')):
        m += (f'<path d="M{F(a + 3)},{ya}H{F(b - 3)}" stroke="var(--accent-2)" stroke-width="2.5" marker-start="url(#rx-d)" marker-end="url(#rx-d)"/>'
              f'<text x="{F((a + b) / 2)}" y="{ya + 30}" text-anchor="middle" font-size="24" fill="var(--accent-2)">{lab}</text>')
    mols.append((st, xi, m, lo, hi))
x = (W - sum(hi - lo for *_, lo, hi in mols) - 2 * G) / 2
for i, (st, xi, m, lo, hi) in enumerate(mols):
    dx = x - lo
    o.append(f'<g class="mol-{st}" transform="translate({F(dx)} 0)">{m}')
    o.append(f'<text x="{F((lo + hi) / 2)}" y="{H - 8}" text-anchor="middle" font-size="30" fill="var(--accent-2)" font-family="var(--mono)">ξ = d₁ − d₂ = {xi} Å</text></g>')
    x += hi - lo
    if i < 2:
        o.append(f'<path d="M{F(x + (G - A) / 2)},115h{A - 8}" stroke="var(--muted)" stroke-width="4" marker-end="url(#rx-ar)"/>')
        x += G
defs = ('<defs><marker id="rx-ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto">'
        '<path d="M0,0L10,5L0,10z" fill="var(--muted)"/></marker>'
        '<marker id="rx-d" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
        '<path d="M0,0L10,5L0,10z" fill="var(--accent-2)"/></marker></defs>')
(out / 'reaction.svg').write_text(svg(W, H, defs + '\n'.join(o), 'mol'))


# homework: Menshutkin reaction NH3 + CH3Cl -> CH3NH3+ + Cl-, same drawing style as the SN2 scheme
def mensh(cx, cy, s, state, psi=0.45):
    """Cl-C...N along x; state 'R' (xi = -1.7) or 'P' (xi = +1.9). Returns svg, projected atoms."""
    d1, d2, hc = {'R': (1.8, 3.5, 0.36), 'P': (3.4, 1.5, -0.36)}[state]
    at = [('Cl', -d1, 0, 0, 'Cl'), ('C', 0, 0, 0, 'C'), ('N', d2, 0, 0, 'N')]
    for th in (90, 210, 330):                      # H on C: umbrella opens away from the bonded partner
        t_ = math.radians(th); at.append(('H', hc, 1.03 * math.sin(t_), 1.03 * math.cos(t_), ''))
    for th in (90, 210, 330):                      # H on N: umbrella pointing away from C
        t_ = math.radians(th); at.append(('H', d2 + 0.36, 0.97 * math.sin(t_), 0.97 * math.cos(t_), ''))
    P = [(e, cx + s * (x * math.cos(psi) + z * math.sin(psi)), cy - s * y, -x * math.sin(psi) + z * math.cos(psi), lab) for e, x, y, z, lab in at]
    line = lambda a, b, w=0.05: f'<path d="M{F(a[1])},{F(a[2])}L{F(b[1])},{F(b[2])}" stroke="#000" stroke-width="{w * s:.1f}"/>'
    o = [line(P[1], P[j]) for j in (3, 4, 5)] + [line(P[2], P[j]) for j in (6, 7, 8)]
    o.append(line(P[1], P[0] if state == 'R' else P[2]))   # C-Cl in the reactant, C-N in the product
    for e, x, y, z, lab in sorted(P, key=lambda a: a[3]):
        o.append(f'<circle cx="{F(x)}" cy="{F(y)}" r="{F(RAD[e] * s * (1 + 0.08 * z))}" fill="{COL[e]}" stroke="#000" stroke-width="{max(2, 0.025 * s):.1f}"/>')
    for e, x, y, z, lab in P[:3]:
        dy = RAD[e] * s + (34 if e == 'Cl' else 62)   # N label below its lower H atoms
        if e != 'C': o.append(f'<text x="{F(x)}" y="{F(y + dy)}" text-anchor="middle" font-size="26" fill="var(--fg)">{lab}</text>')
    if state == 'P':                               # ion charges
        o.append(f'<text x="{F(P[0][1] + 0.3 * s)}" y="{F(P[0][2] - 0.3 * s)}" font-size="30" font-weight="700" fill="var(--neg)">−</text>')
        o.append(f'<text x="{F(P[2][1] + 0.55 * s)}" y="{F(P[2][2] - 0.75 * s)}" font-size="30" font-weight="700" fill="var(--neg)">+</text>')
    return '\n'.join(o), P


W, H, s = 1500, 250, 58
o, mols = [], []
for st, xi, lab in (('R', '−1.7', 'NH₃ + CH₃Cl'), ('P', '+1.9', 'CH₃NH₃⁺ + Cl⁻')):
    m, P = mensh(0, 105, s, st)
    lo = min(x - RAD[e] * s for e, x, y, z, _ in P); hi = max(x + RAD[e] * s for e, x, y, z, _ in P)
    mols.append((xi, lab, m, lo, hi))
G, A = 260, 110
x = (W - sum(hi - lo for *_, lo, hi in mols) - G) / 2
for i, (xi, lab, m, lo, hi) in enumerate(mols):
    o.append(f'<g transform="translate({F(x - lo)} 0)">{m}'
             f'<text x="{F((lo + hi) / 2)}" y="{H - 10}" text-anchor="middle" font-size="28" fill="var(--accent-2)" font-family="var(--mono)">ξ = {xi} Å</text></g>')
    x += hi - lo
    if i == 0:
        o.append(f'<path d="M{F(x + (G - A) / 2)},105h{A - 8}" stroke="var(--muted)" stroke-width="4" marker-end="url(#mh-ar)"/>')
        x += G
defs = ('<defs><marker id="mh-ar" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="5" markerHeight="5" orient="auto">'
        '<path d="M0,0L10,5L0,10z" fill="var(--muted)"/></marker></defs>')
(out / 'mensh.svg').write_text(svg(W, H, defs + '\n'.join(o), 'mol'))


# ML/MM system: solute in a box of TIP3P water (schematic)
W, H = 760, 620
rng = np.random.default_rng(3)
o = [f'<rect x="10" y="10" width="{W - 20}" height="{H - 20}" rx="26" fill="var(--mm-bg)" stroke="var(--mm)" stroke-width="3"/>']
pts = []
for _ in range(5000):
    x, y = rng.uniform(55, W - 55), rng.uniform(55, H - 55)
    if ((x - W / 2) / 290) ** 2 + ((y - H / 2) / 180) ** 2 < 1: continue  # keep waters (with their H) outside the ML ellipse
    if x < 170 and y > H - 110: continue  # room for the MM label
    if all((x - a) ** 2 + (y - b) ** 2 > 72 ** 2 for a, b in pts): pts.append((x, y))
for x, y in pts:
    a = rng.uniform(0, 2 * math.pi)
    sw = 13
    hs = [(x + 24 * math.cos(a + d), y + 24 * math.sin(a + d)) for d in (-0.91, 0.91)]
    o.append(''.join(f'<path d="M{F(x)},{F(y)}L{F(hx)},{F(hy)}" stroke="#000" stroke-width="3"/>' for hx, hy in hs)
             + f'<circle cx="{F(x)}" cy="{F(y)}" r="{sw}" fill="{COL["O"]}" stroke="#000" stroke-width="2"/>'
             + ''.join(f'<circle cx="{F(hx)}" cy="{F(hy)}" r="8" fill="#fff" stroke="#000" stroke-width="2"/>' for hx, hy in hs))
o.append(f'<ellipse cx="{W / 2}" cy="{H / 2}" rx="235" ry="125" fill="var(--ml-bg)" stroke="var(--ml)" stroke-width="3.5"/>')
m, _ = molecule(W / 2 - 18, H / 2 + 8, 70, 'R', labels=False)
o.append(m)
o.append(f'<text x="{W / 2}" y="{H / 2 - 82}" text-anchor="middle" font-size="30" font-family="var(--mono)" font-weight="700" fill="var(--accent-2)">ML</text>')
o.append(f'<text x="44" y="{H - 30}" font-size="30" font-family="var(--mono)" font-weight="700" fill="var(--mm)">MM</text>')
(out / 'box.svg').write_text(svg(W, H, '\n'.join(o), 'box'))


# title panel: PMF curve with R, TS, P inside a circle (r 330 at 360, 540)
fr = Frame(720, 1080, (-1.75, 1.75), (0, max(40, Fs.max() + 5)), m=(90, 90, 330, 330))
sx, sy = smooth(xs, Fs)
o = [f'<path d="{fr.path(sx, sy)}" fill="none" stroke="var(--accent)" stroke-width="7" stroke-linecap="round"/>']
for st, x, y, s in (('TS', 0, fr.y(Fs.max()) - 80, 32), ('R', -1.3, fr.y(0) - 220, 26), ('P', 1.3, fr.y(0) - 220, 26)):
    o.append(molecule(fr.x(x), y, s, st, labels=False)[0])
(out / 'title.svg').write_text('\n'.join(o))
print('figs:', sorted(p.name for p in out.glob('*.svg')))


# ---------- one extXYZ frame, colour-coded (slide "What is in sn2.extxyz") ----------
import html, re, shlex
lines = (here / 'data/frame0.extxyz').read_text().splitlines()
COLS = [('species', 1, 'sp'), ('pos', 3, 'pos'), ('q_core', 1, 'q'), ('q_val', 1, 'q'), ('q', 1, 'q'), ('mu', 3, 'mu'), ('s', 1, 's')]
W = 12                                            # column width (whitespace-separated, so re-spacing keeps the file valid)
head = lines[1]
# comment line: colour Properties sub-fields like the columns, molecular keys as such
props = re.match(r'Properties=(\S+)', head).group(1)
cls = {name: c for name, _, c in COLS}
pp = props.split(':')
ptxt = ':'.join(f'<span class="{cls[pp[i]]}">{":".join(pp[i:i + 3])}</span>' for i in range(0, len(pp), 3))
rest = head[len('Properties=') + len(props):]
def mol(m):
    k = m.group(1)
    c = 'mol' if k in ('energy_dft', 'total_charge', 'alpha') else 'meta'
    return f'<span class="{c}">{html.escape(m.group(0))}</span>'
rest = re.sub(r'(\w+)=("[^"]*"|\S+)', mol, rest)
o = [f'<div class="xl"><span class="tag">number of atoms</span><pre class="xyz">{lines[0]}</pre></div>',
     f'<div class="xl"><span class="tag">molecular properties</span><pre class="xyz wrap"><span class="meta">Properties=</span>{ptxt}{rest}</pre></div>']
labs = ['', 'x', 'y', 'z', 'q_core', 'q_val', 'q', 'μx', 'μy', 'μz', 's']
lc = ['sp', 'pos', 'pos', 'pos', 'q', 'q', 'q', 'mu', 'mu', 'mu', 's']
hdr = ''.join(f'<span class="{c}">{l:>{W if i else 3}}</span>' for i, (l, c) in enumerate(zip(labs, lc)))
rows = []
for ln in lines[2:]:
    f = ln.split()
    rows.append(''.join(f'<span class="{c}">{v:<3}</span>' if i == 0 else f'<span class="{c}">{v:>{W}}</span>'
                        for i, (v, c) in enumerate(zip(f, lc))))
o.append(f'<div class="xl"><span class="tag">atomic properties,<br>one line per atom</span><pre class="xyz">' + '\n'.join(rows) + '</pre></div>')
# column names are not in the file: they go under the card, as an annotation aligned with the columns
o.append(f'<div class="xl colrow"><span></span><pre class="xyz colh">{hdr}</pre></div>')
(out / 'extxyz.html').write_text('\n'.join(o))


# ---------- emle-train: log fragment + RMSE-vs-epoch sparklines (slide "Train EMLE") ----------
log = (here / 'data/train.log').read_text().splitlines()
stages, cur = [], None
for ln in log:
    if ln.startswith('Fitting'):
        cur = []; stages.append((ln, cur))
    m = re.match(r'Epoch\s+(\d+): Loss =\s*([\d.]+)\s+RMSE =\s*([\d.]+)', ln)
    if m and cur is not None:
        cur.append((int(m.group(1)), float(m.group(3))))
def spark(series, unit, W=290, H=150):
    """RMSE vs epoch; several series are drawn one after another, separated by a dashed line."""
    pts = [p for s in series for p in s]
    n = len(pts)
    ymax = max(r for _, r in pts)
    fr = Frame(W, H, (0, n - 1), (0, ymax * 1.05), m=(8, 8, 10, 30))
    o = [f'<path d="M{fr.l},{fr.H - fr.b}H{fr.W - fr.r}" stroke="var(--border)" stroke-width="2"/>']
    i0 = 0
    for k, s in enumerate(series):
        xs_ = list(range(i0, i0 + len(s)))
        o.append(f'<path d="{fr.path(xs_, [r for _, r in s])}" fill="none" stroke="var(--accent)" stroke-width="3.5" stroke-linejoin="round"/>')
        if k:
            o.append(f'<path d="M{F(fr.x(i0 - 0.5))},{fr.t}V{fr.H - fr.b}" stroke="var(--muted)" stroke-width="1.5" stroke-dasharray="5 5"/>')
        i0 += len(s)
    a, b = pts[0][1], pts[-1][1]
    o.append(f'<text x="{F(fr.x(0) + 14)}" y="{F(fr.y(a) + 8)}" font-size="20" fill="var(--muted)">{a:g}</text>')
    o.append(f'<text x="{fr.W - fr.r}" y="{F(fr.y(b) - 12)}" font-size="22" fill="var(--accent-2)" text-anchor="end" font-weight="600">{b:g} {unit}</text>')
    o.append(f'<text x="{fr.W / 2}" y="{H - 4}" font-size="18" fill="var(--muted)" text-anchor="middle">epoch →</text>')
    return svg(W, H, '\n'.join(o), 'plot')
(out / 'train_q.svg').write_text(spark([stages[0][1]], 'e'))
(out / 'train_a.svg').write_text(spark([stages[1][1], stages[2][1]], 'bohr³'))

# log fragment: IVM block, then first/last epochs of each fit (segments s1..s3 are highlighted step by step)
def ep(ln):  # Epoch lines are kept verbatim
    return html.escape(ln)
ivm = [l for l in log if l.startswith('Performing IVM') or l.startswith('IVM done') or re.match(r'\s*\d+:\s+\d+$', l)]
seg = [f'<span class="seg s1">' + '\n'.join(html.escape(l) for l in ivm) + '</span>']
keep = {0: [10, 20, 30, 100], 1: [10, 20, 30, 100], 2: [10, 100]}
for k, (title, _) in enumerate(stages):
    body = [l for l in log[log.index(title) + 1:] if l.startswith('Epoch')][:10]
    shown = []
    for l in body:
        e = int(l.split()[1].rstrip(':'))
        if e in keep[k]:
            if e == 100 and shown and int(shown[-1].split()[1].rstrip(':')) != 90:
                shown.append('…')
            shown.append(l)
    cls = 's2' if k == 0 else 's3'
    seg.append(f'<span class="seg {cls}">' + html.escape(title) + '\n' + '\n'.join(ep(l) for l in shown) + '</span>')
(out / 'train_log.html').write_text(''.join(seg))


# ---------- us_window.py, syntax-coloured, in three parts (slides "Run the windows" 1-3) ----------
code = (here / 'data/us_window.py').read_text().splitlines()
def py(l):
    h = html.escape(l)
    h = re.sub(r'(f?&quot;.*?&quot;)', r'<span class="s">\1</span>', h)
    h = re.sub(r'(#.*)$', r'<span class="n">\1</span>', h)
    h = re.sub(r'^(\s*)(for)\b(.*?)\b(in)\b', r'\1<span class="k">\2</span>\3<span class="k">\4</span>', h)
    h = re.sub(r'\b(True)\b', r'<span class="k">\1</span>', h)
    h = re.sub(r'^(from)\b(.*?)\b(import)\b', r'<span class="k">\1</span>\2<span class="k">\3</span>', h)
    h = re.sub(r'^(import)\b', r'<span class="k">\1</span>', h)
    return h
def part(first, stop):
    """Lines from the one starting with `first` up to (not including) the one starting with `stop`."""
    i0 = next(i for i, l in enumerate(code) if l.startswith(first))
    i1 = next(i for i in range(i0 + 1, len(code)) if code[i].startswith(stop))
    ls = code[i0:i1]
    while ls and not ls[-1].strip(): ls.pop()
    return '\n'.join(py(l) for l in ls)
(out / 'us_setup.html').write_text(part('import', '# Reaction coordinate'))  # imports, parameters, ML/MM system
(out / 'us_bias.html').write_text(part('# Reaction coordinate', '# Run'))   # xi, umbrella, walls
(out / 'us_run.html').write_text(part('# Run', 'print('))                   # MD loop + npz


# bias shapes: umbrella in xi (one window) and the flat-bottom wall on each C-Cl distance (slide "Reaction coordinate and bias")
def mini(f, xlim, ylim, xt, xlabel, mark, W=330, H=250):
    fr = Frame(W, H, xlim, ylim, m=(20, 14, 16, 64))
    x = np.linspace(*xlim, 400)
    y = f(x)
    x, y = x[y <= ylim[1]], y[y <= ylim[1]]       # stop where the curve leaves the frame (no flat top: both potentials keep rising)
    o = [f'<path d="M{fr.l},{fr.t}V{fr.H - fr.b}H{fr.W - fr.r}" fill="none" stroke="var(--fg)" stroke-width="2"/>',
         f'<path d="{fr.path(x, y)}" fill="none" stroke="var(--mm)" stroke-width="4"/>']
    for v, lab in xt:
        o.append(f'<path d="M{F(fr.x(v))},{fr.H - fr.b}v8" stroke="var(--fg)" stroke-width="2"/>'
                 f'<text x="{F(fr.x(v))}" y="{fr.H - fr.b + 30}" text-anchor="middle" font-size="22" fill="var(--muted)">{lab}</text>')
    o.append(f'<text x="{F((fr.l + fr.W - fr.r) / 2)}" y="{H - 4}" text-anchor="middle" font-size="22" fill="var(--fg)">{xlabel}</text>')
    o.append(f'<text x="{fr.l + 12}" y="{fr.t + 18}" font-size="22" fill="var(--mm)">{mark}</text>')
    return svg(W, H, '\n'.join(o), 'plot')
(out / 'bias_us.svg').write_text(mini(lambda x: 0.5 * k_us * x ** 2, (-0.35, 0.35), (0, 20), [(0, 'ξ₀')], 'ξ', '½k(ξ − ξ₀)²'))
(out / 'bias_wall.svg').write_text(mini(lambda r: np.where(r > 3, 0.5 * 600 * (r - 3) ** 2, 0), (1.5, 3.4), (0, 20),
                                        [(1.8, '1.8'), (3.0, '3 Å')], 'd(C–Cl)', 'wall'))


# ---------- the wham() function of pmf.py (slide "Combine the windows") ----------
src = (here / 'data/pmf.py').read_text().splitlines()
i0 = next(i for i, l in enumerate(src) if l.startswith('def wham'))
i1 = next(i for i in range(i0 + 1, len(src)) if src[i] and not src[i].startswith(' '))
fn = [l for l in src[i0:i1] if l.strip()]
doc = [i for i, l in enumerate(fn) if '"""' in l]
doc = set(range(doc[0], doc[-1] + 1)) if doc else set()   # docstring lines are shown as one string
(out / 'wham.html').write_text('\n'.join(f'<span class="s">{html.escape(l)}</span>' if i in doc else
                                         py(l).replace('def ', '<span class="k">def</span> ', 1).replace('return', '<span class="k">return</span>')
                                         for i, l in enumerate(fn)))


# reaction coordinate: reactant complex with atom indices and the two distances
W, H, s_ = 720, 300, 80
m, P = molecule(250, 175, s_, 'R', labels=False)
C_, Cl1, Cl2 = P[1], P[0], P[2]
o = [m]
for (e, x, y, z, lab), txt in ((Cl1, 'Cl₁ (4)'), (C_, 'C (0)'), (Cl2, 'Cl₂ (5)')):
    o.append(f'<text x="{F(x)}" y="{F(y + 90)}" text-anchor="middle" font-size="24" fill="var(--fg)" font-family="var(--mono)">{txt}</text>')
for a, b, lab, yy in ((Cl1, C_, 'd₁', 46), (C_, Cl2, 'd₂', 46)):
    o.append(f'<path d="M{F(a[1])},{yy}H{F(b[1])}" stroke="var(--accent-2)" stroke-width="2.5" marker-start="url(#xi-ar)" marker-end="url(#xi-ar)"/>'
             f'<text x="{F((a[1] + b[1]) / 2)}" y="{yy - 12}" text-anchor="middle" font-size="26" fill="var(--accent-2)">{lab}</text>')
o.append(f'<text x="{W - 10}" y="{H - 12}" text-anchor="end" font-size="28" fill="var(--accent-2)">ξ = d₁ − d₂</text>')
defs = ('<defs><marker id="xi-ar" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="5" markerHeight="5" orient="auto-start-reverse">'
        '<path d="M0,0L10,5L0,10z" fill="var(--accent-2)"/></marker></defs>')
(out / 'xi.svg').write_text(svg(W, H, defs + '\n'.join(o), 'mol'))


# ---------- solvated system for the 3Dmol viewer (slide "Parameters and the ML/MM system") ----------
# data/box_ts.pdb = box.prm7 + start/win_14.rst7 (TS window) written by Sire; served as a JS string so it also works from file://
import json
(out / 'box_pdb.js').write_text('window.BOX_PDB = ' + json.dumps((here / 'data/box_ts.pdb').read_text()) + ';\n')


# ---------- gas-phase solute snapshot for the "AIMNet2 MD" card (slide "Where the DFT data come from") ----------
# first training geometry (data/frame0.extxyz), turned so Cl1 -> Cl2 runs along x and all three H are visible
fr0 = (here / 'data/frame0.extxyz').read_text().splitlines()
el = [l.split()[0] for l in fr0[2:2 + int(fr0[0])]]
X = np.array([[float(v) for v in l.split()[1:4]] for l in fr0[2:2 + int(fr0[0])]])
X -= X[0]                                         # C at the origin
ex = X[5] - X[4]; ex /= np.linalg.norm(ex)        # Cl1 -> Cl2
h = X[1] - (X[1] @ ex) * ex; ey = h / np.linalg.norm(h)
R = np.array([ex, ey, np.cross(ex, ey)])
psi, tx = 0.25, -0.65                             # turn about y, then x: chosen so no H hides behind C (min projected H-atom gap 0.84 A)
Ry = np.array([[math.cos(psi), 0, math.sin(psi)], [0, 1, 0], [-math.sin(psi), 0, math.cos(psi)]])
Rx = np.array([[1, 0, 0], [0, math.cos(tx), -math.sin(tx)], [0, math.sin(tx), math.cos(tx)]])
X = X @ R.T @ Ry.T @ Rx.T
xyz = f'{len(el)}\nsolute\n' + ''.join(f'{e} {a:.4f} {b:.4f} {c:.4f}\n' for e, (a, b, c) in zip(el, X))
(out / 'solute_xyz.js').write_text('window.SOLUTE_XYZ = ' + json.dumps(xyz) + ';\n')

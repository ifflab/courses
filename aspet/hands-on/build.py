#!/usr/bin/env python3
"""Concatenate slides/NN.html into index.html. Engine, palette and fonts are shared with ../lecture/.
<!--include figs/NAME.svg--> in a slide is replaced by that file (run plots.py first)."""
import glob, pathlib, re, time
here = pathlib.Path(__file__).parent
L = '../lecture/'
v = int(time.time())
body = '\n\n'.join(pathlib.Path(f).read_text() for f in sorted(glob.glob(str(here / 'slides' / '[0-9][0-9]*.html'))))
body = re.sub(r'<!--include (\S+)-->', lambda m: (here / m.group(1)).read_text(), body)
html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hands-on: ML/MM free-energy profile</title>
<link rel="stylesheet" href="{L}vendor/katex/dist/katex.min.css">
<link rel="stylesheet" href="{L}deck.css?v={v}">
<link rel="stylesheet" href="handson.css?v={v}">
<script defer src="{L}vendor/katex/dist/katex.min.js"></script>
<script defer src="{L}vendor/katex/dist/contrib/auto-render.min.js"></script>
<script defer src="vendor/3dmol/3Dmol-min.js"></script>
<script defer src="{L}deck.js?v={v}"></script>
</head>
<body data-footer="K. Zinovjev · Hybrid ML/MM simulations · Hands-on · Aspet 2026">
<div id="deck">
{body}
</div>
</body>
</html>
'''
(here / 'index.html').write_text(html)
print('slides:', body.count('<section class="slide'))

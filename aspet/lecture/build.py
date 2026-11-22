#!/usr/bin/env python3
"""Concatenate slides/NN.html (in name order) into index.html, or a subset into a preview file."""
import glob, pathlib, argparse, time
ap = argparse.ArgumentParser()
ap.add_argument('--from', dest='a', type=int, default=0)
ap.add_argument('--to', dest='b', type=int, default=999)
ap.add_argument('--out', default='index.html', help='file name in the lecture folder')
args = ap.parse_args()
here = pathlib.Path(__file__).parent
files = [f for f in sorted(glob.glob(str(here / 'slides' / '[0-9][0-9]*.html')))
         if args.a <= int(pathlib.Path(f).name[:2]) <= args.b]
v = int(time.time())  # cache-buster: browsers keep stale deck.js/css on file://
body = '\n\n'.join(pathlib.Path(f).read_text() for f in files)
html = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>From QM/MM to ML/MM</title>
<link rel="stylesheet" href="vendor/katex/dist/katex.min.css">
<link rel="stylesheet" href="deck.css?v={v}">
<script defer src="vendor/katex/dist/katex.min.js"></script>
<script defer src="vendor/katex/dist/contrib/auto-render.min.js"></script>
<script defer src="figs.js?v={v}"></script>
<script defer src="deck.js?v={v}"></script>
</head>
<body data-footer="K. Zinovjev · Hybrid ML/MM simulations · Aspet 2026">
<div id="deck">
{body}
</div>
</body>
</html>
'''
(here / args.out).write_text(html)
print('slides:', body.count('<section class="slide'))

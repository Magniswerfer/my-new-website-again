"""Slice the pose sheets (poses on transparency, made in ChatGPT) into one shared
frame per pose, and split the ink marks (ticks, z's, the thought
bubble) into their own layer so the site can recolour them in dark mode.

  python3 design/avatar/cutout.py
"""
import pathlib
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parents[1] / 'src/assets/avatar'
# Each sheet: file, grid of names (None = skip), upsampling factor.
# Sheet 1 has the plain standing pose the homepage's idle/blink/wave/sleep loop needs.
SHEETS = [
    ('poses-sheet.png', [['stand', 'wave', None, None],
                         [None, None, None, 'sleep'],
                         [None, None, None, None]], 2),
    ('poses-sheet-2.png', [['hello', 'walk', 'cheer', 'laptop', 'read', 'nap'],
                           ['think', 'solder', 'game', 'backpack', 'coffee', 'binoculars'],
                           ['magnify', 'screwdriver', 'books', 'headphones', 'idea', 'camera'],
                           ['box', 'tablet', 'd20', 'terminal', 'lie-read', 'beanbag']], 3),
]


def split(cell):
    """Return (figure, marks) RGBA images. Marks are dark islands away from the figure."""
    a = np.asarray(cell)[:, :, 3]
    lab, n = ndimage.label(a > 24)
    sizes = ndimage.sum(np.ones_like(a), lab, range(1, n + 1))
    main = 1 + int(np.argmax(sizes))
    body = ndimage.binary_dilation(lab == main, iterations=6)
    rgb = np.asarray(cell)[:, :, :3].astype(int)
    # Drop bits of neighbouring poses that reach into this cell (they touch its edge).
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0, main}
    arr0 = np.asarray(cell).copy()
    for i in edge:
        arr0[ndimage.binary_dilation(lab == i, iterations=3), 3] = 0
    cell = Image.fromarray(arr0); a = arr0[:, :, 3]
    for i in edge: lab[lab == i] = 0
    marks = np.zeros(a.shape, bool)
    for i in range(1, n + 1):
        if i == main: continue
        m = lab == i
        if not m.any() or (m & body).any(): continue   # gone, or touches the figure (a prop)
        if rgb[m].mean() > 110: continue         # not ink (a glow, a sparkle, a speech bubble)
        marks |= m
    marks = ndimage.binary_dilation(marks, iterations=2) & (a > 0) & ~(lab == main)
    arr = np.asarray(cell).copy()
    fig = arr.copy(); fig[marks, 3] = 0
    mk = arr.copy(); mk[~marks, 3] = 0
    return Image.fromarray(fig), (Image.fromarray(mk) if marks.any() else None)


def blink(fig):
    """Close the standing pose's eyes: paint the eyes out with the surrounding
    plastic, then draw a short closed-lid line."""
    arr = np.asarray(fig).astype(float)
    rgb, a = arr[:, :, :3], arr[:, :, 3]
    lum = rgb.mean(2)
    h = arr.shape[0]
    dark = (lum < 70) & (a > 200)
    dark[int(h * 0.55):] = False
    lab, n = ndimage.label(dark)
    sizes = ndimage.sum(np.ones_like(lum), lab, range(1, n + 1))
    # the two eyes are the two largest tall blobs in the upper half
    cands = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) < 20: continue
        hgt, wid = np.ptp(ys) + 1, np.ptp(xs) + 1
        if hgt > wid * 1.2: cands.append((len(ys), i, ys, xs))
    cands.sort(reverse=True)
    P = 9
    for _, i, ys, xs in cands[:2]:
        y0, y1, x0, x1 = ys.min() - P, ys.max() + P, xs.min() - P, xs.max() + P
        # Coons patch from the border of a padded box: a smooth plastic surface.
        top, bot = rgb[y0, x0:x1 + 1].copy(), rgb[y1, x0:x1 + 1].copy()
        lef, rig = rgb[y0:y1 + 1, x0].copy(), rgb[y0:y1 + 1, x1].copy()
        for y in range(y0, y1 + 1):
            v = (y - y0) / (y1 - y0)
            for x in range(x0, x1 + 1):
                u = (x - x0) / (x1 - x0)
                c = ((1 - v) * top[x - x0] + v * bot[x - x0] + (1 - u) * lef[y - y0] + u * rig[y - y0]
                     - ((1 - u) * (1 - v) * rgb[y0, x0] + u * (1 - v) * rgb[y0, x1] + (1 - u) * v * rgb[y1, x0] + u * v * rgb[y1, x1]))
                # feather into the original near the edge of the box
                e = min(x - x0, x1 - x, y - y0, y1 - y) / 4
                k = min(1.0, e)
                arr[y, x, :3] = k * c + (1 - k) * arr[y, x, :3]
    out = Image.fromarray(arr.astype(np.uint8))
    d = ImageDraw.Draw(out)
    for _, i, ys, xs in cands[:2]:
        cx, cy, w = (xs.min() + xs.max()) / 2, ys.min() + (ys.max() - ys.min()) * 0.55, (xs.max() - xs.min()) * 1.5
        d.arc([cx - w / 2, cy - w * 0.4, cx + w / 2, cy + w * 0.4], 25, 155, fill=(22, 23, 26, 255), width=max(3, int(w * 0.2)))
    return out


def figures(sheet, rows, cols):
    """Find each pose on the sheet as a group of pieces (body, props, marks, shadow),
    by which grid cell each piece's centre falls in. Nothing is cut at a cell line:
    a pose that spills into its neighbour's cell keeps all of itself."""
    a = np.asarray(sheet)[:, :, 3]
    lab, n = ndimage.label(ndimage.binary_dilation(a > 8, iterations=2))
    cw, ch = sheet.width / cols, sheet.height / rows
    groups = {}
    for i, sl in enumerate(ndimage.find_objects(lab), start=1):
        m = lab[sl] == i
        if m.sum() < 40: continue
        ys, xs = np.nonzero(m)
        cy, cx = ys.mean() + sl[0].start, xs.mean() + sl[1].start
        groups.setdefault((int(cy // ch), int(cx // cw)), []).append((i, m.sum(), sl))
    return lab, groups


OUT.mkdir(parents=True, exist_ok=True)
for f in OUT.glob('*.webp'): f.unlink()
PAD = 24
for file, names, scale in SHEETS:
    sheet = Image.open(HERE / file).convert('RGBA')
    arr = np.asarray(sheet)
    lab, groups = figures(sheet, len(names), len(names[0]))
    cuts = {}
    for (r, c), parts in groups.items():
        if r >= len(names) or c >= len(names[0]) or not names[r][c]: continue
        ids = [i for i, _, _ in parts]
        mask = np.isin(lab, ids)
        ys, xs = np.nonzero(mask)
        y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
        piece = arr[y0:y1, x0:x1].copy(); piece[~mask[y0:y1, x0:x1], 3] = 0
        # Anchor on the largest piece (the figure itself): its centre and its bottom.
        main = max(parts, key=lambda p: p[1])
        my, mx = np.nonzero(lab == main[0])
        cuts[names[r][c]] = (piece, (mx.min() + mx.max()) / 2 - x0, my.max() + 1 - y0)
    # One canvas per sheet, big enough for every pose standing on the same baseline.
    left = max(ax for _, ax, _ in cuts.values()); right = max(p.shape[1] - ax for p, ax, _ in cuts.values())
    up = max(by for _, _, by in cuts.values()); down = max(p.shape[0] - by for p, _, by in cuts.values())
    half = int(max(left, right)) + PAD
    W, H = 2 * half, int(up + down) + 2 * PAD
    base = int(up) + PAD
    for name, (piece, ax, by) in cuts.items():
        canvas = Image.new('RGBA', (W, H))
        canvas.alpha_composite(Image.fromarray(piece), (int(round(half - ax)), int(round(base - by))))
        canvas = canvas.resize((W * scale, H * scale), Image.LANCZOS)
        canvas = canvas.filter(ImageFilter.UnsharpMask(radius=1.6, percent=40, threshold=2))
        fig, marks = split(canvas)
        fig.save(OUT / f'{name}.webp', 'WEBP', quality=90, method=4)
        if marks: marks.save(OUT / f'{name}-marks.webp', 'WEBP', quality=90, method=4)
        if name == 'stand':
            blink(fig).save(OUT / 'blink.webp', 'WEBP', quality=90, method=4)
        print(name, fig.size, 'marks' if marks else '')
    missing = [n for row in names for n in row if n and n not in cuts]
    if missing: print('MISSING', missing)

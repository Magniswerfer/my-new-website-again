"""Slice the pose sheet (design/avatar/poses-sheet.png, 4 x 3 poses on transparency)
into one shared frame per pose, and split the ink marks (ticks, z's, the thought
bubble) into their own layer so the site can recolour them in dark mode.

  python3 design/avatar/cutout.py
"""
import pathlib
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
from scipy import ndimage

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parents[1] / 'src/assets/avatar'
NAMES = [['stand', 'wave', 'walk', 'read'],
         ['game', 'solder', 'think', 'sleep'],
         ['backpack', 'cheer', 'laptop', 'coffee']]
SCALE = 2  # the sheet is small; upsample once so retina screens get enough pixels

sheet = Image.open(HERE / 'poses-sheet.png').convert('RGBA')
W, H = sheet.size
cw, ch = W / 4, H / 3


def split(cell):
    """Return (figure, marks) RGBA images. Marks are dark islands away from the figure."""
    a = np.asarray(cell)[:, :, 3]
    lab, n = ndimage.label(a > 24)
    sizes = ndimage.sum(np.ones_like(a), lab, range(1, n + 1))
    main = 1 + int(np.argmax(sizes))
    body = ndimage.binary_dilation(lab == main, iterations=6)
    rgb = np.asarray(cell)[:, :, :3].astype(int)
    marks = np.zeros(a.shape, bool)
    for i in range(1, n + 1):
        if i == main: continue
        m = lab == i
        if (m & body).any(): continue          # touches the figure: a prop, keep it
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


OUT.mkdir(parents=True, exist_ok=True)
for f in OUT.glob('*.webp'): f.unlink()
for r, row in enumerate(NAMES):
    for c, name in enumerate(row):
        cell = sheet.crop((round(c * cw), round(r * ch), round((c + 1) * cw), round((r + 1) * ch)))
        cell = cell.resize((cell.width * SCALE, cell.height * SCALE), Image.LANCZOS)
        cell = cell.filter(ImageFilter.UnsharpMask(radius=1.6, percent=40, threshold=2))
        fig, marks = split(cell)
        fig.save(OUT / f'{name}.webp', 'WEBP', quality=90, method=6)
        if marks: marks.save(OUT / f'{name}-marks.webp', 'WEBP', quality=90, method=6)
        if name == 'stand':
            blink(fig).save(OUT / 'blink.webp', 'WEBP', quality=90, method=6)
        print(name, fig.size, 'marks' if marks else '')

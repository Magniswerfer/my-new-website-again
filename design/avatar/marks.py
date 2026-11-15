"""Header mark and favicons from a render of the model.

  python3 design/avatar/build.py --pose front --view -14 --elev 5 --lens 85 --dist 9 --target 1.45 \\
      --size 1000 --samples 64 --out portrait.png
  python3 design/avatar/marks.py portrait.png

Writes public/avatar/mark.webp (+ @2x/@3x; the whole figure, for next to the name), favicon-32.png,
favicon-48.png, icon-192.png (head and chest, transparent) and apple-touch-icon.png (on the page colour).
"""
import sys, pathlib
import numpy as np
from PIL import Image

src = Image.open(sys.argv[1]).convert('RGBA')
pub = pathlib.Path(__file__).resolve().parents[2] / 'public'
a = np.asarray(src).astype(float)
floor = (a[:, :, :3].max(2) < 10) & (a[:, :, 3] < 250)          # the shadow catcher's wash and shadow
a[:, :, 3] = np.where(floor, 0, a[:, :, 3])                      # marks carry no floor shadow
im = Image.fromarray(a.astype(np.uint8))
ys, xs = np.where(a[:, :, 3] > 24)
fig = im.crop((xs.min() - 2, ys.min() - 2, xs.max() + 3, ys.max() + 3))

H = 30                                                           # the mark's height next to the name
for k, suf in ((1, ''), (2, '@2x'), (3, '@3x')):
    h = H * k; w = round(fig.width * h / fig.height)
    fig.resize((w, h), Image.LANCZOS).save(pub / 'avatar' / f'mark{suf}.webp', 'WEBP', quality=90, method=6)
print('mark', round(fig.width * H / fig.height), 'x', H)

# Favicon: the head and chest, square, a little padding.
top = ys.min(); H_ = ys.max() - top
band = (ys < top + 0.35 * H_)                                    # the dome: centre and width from it alone
hx = xs[band]; cx = (hx.min() + hx.max()) / 2
side = int((hx.max() - hx.min()) * 1.12)
head = im.crop((int(cx - side / 2), top - int(side * 0.04), int(cx + side / 2), top - int(side * 0.04) + side))
for n in (32, 48, 192):
    head.resize((n, n), Image.LANCZOS).save(pub / (f'favicon-{n}.png' if n < 100 else f'icon-{n}.png'))
bg = Image.new('RGBA', (180, 180), (237, 236, 231, 255))
t = head.resize((160, 160), Image.LANCZOS); bg.alpha_composite(t, (10, 14))
bg.convert('RGB').save(pub / 'apple-touch-icon.png')
print('favicons done')

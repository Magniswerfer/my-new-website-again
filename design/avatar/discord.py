"""The Discord avatar: a looping GIF of the gaming idle, and a still PNG for accounts without Nitro.

  python3 design/avatar/scenes.py --scene gaming --step 2 --view -12 --elev 6 --size 720 \
      --samples 16 --dist 6.2 --target 1.55 --out "frames/f#.png"
  python3 design/avatar/discord.py frames OUT_DIR

Square, 512 px, on the site's page colour (a GIF can only do hard-edged transparency, which would
leave a jagged outline), centred so Discord's round crop keeps his face, headset and controller.
"""
import sys, pathlib
import numpy as np
from PIL import Image

src, out = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
BG = (237, 236, 231)
S = 512
files = sorted(src.glob('f*.png'))
files = [f for f in files if f.stem != 'f097']                    # frame 97 repeats frame 1

# One crop for every frame: around everything he does, made square, with a little room for the circle.
box = None
for f in files:
    a = np.asarray(Image.open(f).convert('RGBA'))[:, :, 3]
    ys, xs = np.where(a > 60)
    b = [xs.min(), ys.min(), xs.max(), ys.max()]
    box = b if box is None else [min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3])]
# Keep the top `KEEP` of everything (the chair's base can run off the bottom: the face matters most).
KEEP = float(sys.argv[3]) if len(sys.argv) > 3 else 1.0
box[3] = box[1] + (box[3] - box[1]) * KEEP
cx, cy = (box[0] + box[2]) / 2, (box[1] + box[3]) / 2 - 0.04 * (box[3] - box[1])   # a touch above centre: the face
side = max(box[2] - box[0], box[3] - box[1]) * (1.18 if KEEP == 1.0 else 1.04)
crop = (int(cx - side / 2), int(cy - side / 2), int(cx + side / 2), int(cy + side / 2))

frames = []
for f in files:
    im = Image.open(f).convert('RGBA')
    # The square can reach past the render's edges: lay the frame on a page-coloured canvas first.
    pad = int(side)
    bg = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), BG + (255,)); bg.alpha_composite(im, (pad, pad))
    c = (crop[0] + pad, crop[1] + pad, crop[2] + pad, crop[3] + pad)
    frames.append(bg.crop(c).resize((S, S), Image.LANCZOS).convert('RGB'))

frames[0].save(out / 'magnus-discord.png', optimize=True)
# One shared palette for all frames, so colours don't shimmer from frame to frame.
pal = frames[0].quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
q = [fr.quantize(palette=pal, dither=Image.Dither.FLOYDSTEINBERG) for fr in frames]
q[0].save(out / 'magnus-discord.gif', save_all=True, append_images=q[1:], duration=83, loop=0, optimize=False, disposal=1)
print('frames', len(frames), 'gif', (out / 'magnus-discord.gif').stat().st_size // 1024, 'KB',
      'png', (out / 'magnus-discord.png').stat().st_size // 1024, 'KB')

"""Pack rendered frames into the homepage sprite sheets.

  python3 design/avatar/sheets.py <render dir>

<render dir> holds idle/f###.png, wave/f###.png and sleep.png, rendered with the same camera, e.g.
  CAM="--view -18 --elev 7 --lens 60 --dist 7.6 --target 1.55 --size 760 --samples 18"
  python3 design/avatar/build.py --anim idle --step 2 $CAM --out "<dir>/idle/f#.png"   # 12 fps
  python3 design/avatar/build.py --anim wave $CAM --out "<dir>/wave/f#.png"            # 24 fps
  python3 design/avatar/build.py --pose sleep $CAM --out "<dir>/sleep.png"

Every frame is cropped to one shared box (the union over all frames), scaled to SIZE px tall, and
laid out in a grid; public/avatar/meta.json describes the sheets for HeroAvatar.astro.
"""
import json, sys, pathlib
import numpy as np
from PIL import Image

if len(sys.argv) > 1 and sys.argv[1] == '--scene':
    # A page scene: python3 sheets.py --scene NAME DIR [SIZE] [WAVE_DIR]
    # DIR holds f###.png (the loop on twos, from scenes.py). Writes public/avatar/scenes/NAME/:
    # loop.webp (+ wave.webp), still.webp and meta.json.
    name, sdir = sys.argv[2], pathlib.Path(sys.argv[3])
    size = int(sys.argv[4]) if len(sys.argv) > 4 else 420
    wdir = pathlib.Path(sys.argv[5]) if len(sys.argv) > 5 else None
    out = pathlib.Path(__file__).resolve().parents[2] / 'public/avatar/scenes' / name
    out.mkdir(parents=True, exist_ok=True)
    loop = sorted(sdir.glob('f*.png'))
    if loop and loop[-1].stem == 'f097': loop = loop[:-1]
    wave = sorted(wdir.glob('f*.png')) if wdir else []
    def floor(p):
        im = np.asarray(Image.open(p).convert('RGBA')).astype(float)
        fl = (im[:, :, :3].max(2) < 10) & (im[:, :, 3] < 250)
        im[:, :, 3] = np.where(fl, np.clip((im[:, :, 3] - 34) * 1.35, 0, 255), im[:, :, 3])
        return im
    box = None
    for p in loop + wave:
        a = floor(p)[:, :, 3]; ys, xs = np.where(a > 40)
        b = [xs.min(), ys.min(), xs.max() + 1, ys.max() + 1]
        box = b if box is None else [min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3])]
    pad = 8; box = (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)
    bw, bh = box[2] - box[0], box[3] - box[1]; H = size; W = round(bw * H / bh)
    def cell(p):
        im = Image.fromarray(floor(p).astype(np.uint8)).crop(box).resize((W, H), Image.LANCZOS)
        o = np.asarray(im).astype(float); h, w = o.shape[:2]
        ex = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / (0.1 * w), 0, 1)
        ey = np.clip((h - 1 - np.arange(h)) / (0.06 * h), 0, 1)
        sh = (o[:, :, :3].max(2) < 12) & (o[:, :, 3] < 250)
        o[:, :, 3] = np.where(sh, o[:, :, 3] * np.minimum(ey[:, None], ex[None, :]), o[:, :, 3])
        return Image.fromarray(o.astype(np.uint8))
    meta = {'ratio': round(W / H, 4)}
    for key, files, fps in (('loop', loop, 12), ('wave', wave, 24)):
        if not files: continue
        cols = max(1, 8192 // W); rows = -(-len(files) // cols)
        sheet = Image.new('RGBA', (cols * W, rows * H))
        for i, p in enumerate(files): sheet.paste(cell(p), ((i % cols) * W, (i // cols) * H))
        sheet.save(out / f'{key}.webp', 'WEBP', quality=72, method=6)
        meta[key] = {'sheet': f'{key}.webp', 'w': W, 'h': H, 'cols': cols, 'frames': len(files), 'fps': fps}
        print(name, key, len(files), (out / f'{key}.webp').stat().st_size // 1024, 'KB')
    cell(loop[0]).save(out / 'still.webp', 'WEBP', quality=86, method=6)
    (out / 'meta.json').write_text(json.dumps(meta))
    sys.exit()

SIZE = 512                                   # frame height in the sheets
src = pathlib.Path(sys.argv[1])
out = pathlib.Path(__file__).resolve().parents[2] / 'public/avatar'
out.mkdir(parents=True, exist_ok=True)

moves = {'idle': (sorted((src / 'idle').glob('f*.png')), 12), 'wave': (sorted((src / 'wave').glob('f*.png')), 24)}
# The walk-in (optional): rendered on twos with --follow, so each frame is centred on him and
# offsets.json says how far (in render frame widths) each frame sits from his resting spot.
OFFS = {}
wfiles = sorted(src.glob('walkin/*/f*.png'), key=lambda p: int(p.stem[1:]))
for j in src.glob('walkin/*/offsets.json'):
    OFFS.update(json.loads(j.read_text()))
if wfiles:
    moves['walkin'] = (wfiles, 12)
everything = [p for files, _ in moves.values() for p in files] + [src / 'sleep.png']
box = None
for p in everything:
    a = np.asarray(Image.open(p).convert('RGBA'))[:, :, 3]
    ys, xs = np.where(a > 40)                 # ignore the floor's faint wash when finding his bounds
    b = [xs.min(), ys.min(), xs.max() + 1, ys.max() + 1]
    box = b if box is None else [min(box[0], b[0]), min(box[1], b[1]), max(box[2], b[2]), max(box[3], b[3])]
pad = 6
box = (box[0] - pad, box[1] - pad, box[2] + pad, box[3] + pad)
bw, bh = box[2] - box[0], box[3] - box[1]
H = SIZE; W = round(bw * H / bh)


def frame(p, shadow=1.0):
    im = np.asarray(Image.open(p).convert('RGBA')).astype(float)
    # The floor is a shadow catcher: it leaves a faint grey wash (alpha ~10-35) everywhere, whose edge
    # would show as a rectangle. Keep only the real contact shadow under him.
    floor = (im[:, :, :3].max(2) < 10) & (im[:, :, 3] < 250)
    im[:, :, 3] = np.where(floor, np.clip((im[:, :, 3] - 34) * 1.35, 0, 255), im[:, :, 3])
    out = np.asarray(Image.fromarray(im.astype(np.uint8)).crop(box).resize((W, H), Image.LANCZOS)).astype(float)
    # Feather the shadow toward the frame's edges, so a long shadow never ends in a hard line.
    h, w = out.shape[:2]
    ex = np.clip(np.minimum(np.arange(w), w - 1 - np.arange(w)) / (0.12 * w), 0, 1)
    ey = np.clip((h - 1 - np.arange(h)) / (0.06 * h), 0, 1)
    ramp = np.minimum(ey[:, None], ex[None, :])
    shade = (out[:, :, :3].max(2) < 12) & (out[:, :, 3] < 250)
    out[:, :, 3] = np.where(shade, out[:, :, 3] * ramp * shadow, out[:, :, 3])
    return Image.fromarray(out.astype(np.uint8))


meta = {'ratio': round(W / H, 4)}
for name, (files, fps) in moves.items():
    cols = max(1, 8192 // W)
    rows = -(-len(files) // cols)
    sheet = Image.new('RGBA', (cols * W, rows * H))
    far = max([abs(OFFS[str(int(q.stem[1:]))][0]) for q in files] or [1]) if name == 'walkin' else 1
    for i, p in enumerate(files):
        # Far from his spot the studio light is low on him and his shadow stretches; soften it
        # while he's out there, easing to the normal shadow as he arrives.
        k = 1.0 if name != 'walkin' else 1 - 0.65 * abs(OFFS[str(int(p.stem[1:]))][0]) / far
        sheet.paste(frame(p, k), ((i % cols) * W, (i // cols) * H))
    sheet.save(out / f'{name}.webp', 'WEBP', quality=72, method=6)
    meta[name] = {'sheet': f'{name}.webp', 'w': W, 'h': H, 'cols': cols, 'frames': len(files), 'fps': fps}
    if name == 'walkin':
        rw = Image.open(files[0]).width; k = W / bw                  # render px -> sheet px
        meta[name]['dx'] = [round(OFFS[str(int(p.stem[1:]))][0] * rw * k, 1) for p in files]
        meta[name]['dy'] = [round(OFFS[str(int(p.stem[1:]))][1] * rw * k, 1) for p in files]
    print(name, len(files), 'frames', sheet.size, (out / f'{name}.webp').stat().st_size // 1024, 'KB')
frame(moves['idle'][0][0]).save(out / 'still.webp', 'WEBP', quality=88, method=6)
frame(src / 'sleep.png').save(out / 'sleep.webp', 'WEBP', quality=88, method=6)
(out / 'meta.json').write_text(json.dumps(meta))
print(meta)

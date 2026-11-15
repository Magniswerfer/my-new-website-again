"""
The site character as a Blender model, built to the model sheet (design/avatar/model-sheet.png).

  pip install bpy scipy
  python3 design/avatar/build.py --view 0 --out front.png           # render a view (degrees of turn)
  python3 design/avatar/build.py --pose wave --view -15 --out wave.png
  python3 design/avatar/build.py --export design/avatar/avatar.glb   # rigged GLB + .blend

All measurements come from the sheet's turnaround, in units of the body's half-width
W (52.5 px on the sheet). Front faces -Y, Z is up, the ground is z = 0.

Model: a turned body (quads, three grooves) on two capsule legs, round arms on the
groove band, glossy capsule eyes and smile, a centred green LED and a raised pill key.
Rig: root > body > arm.L / arm.R, and leg.L / leg.R; every part is bound rigidly to
one bone, so poses are just bone rotations. UVs: smart-projected. Materials: PBR.
"""
import bpy, bmesh, math, sys, argparse
import numpy as np
from mathutils import Vector, Matrix, Euler

EXPO = -0.9
PX = 52.5                    # sheet pixels per unit
DEPTH = 0.91                 # body depth / width
LEG_H = 27 / PX              # visible leg below the body
BODY_H = 2.44                # body height in half-widths (height / width = 1.22)
Z0 = LEG_H
ZT = Z0 + BODY_H

# Half-width of the body, s sheet-pixels down from the top (back and side views).
PROFILE = [(0, 0.0), (1, 0.12), (3, 0.34), (6, 0.47), (9, 0.55), (12, 0.62), (15, 0.68), (18, 0.73),
           (21, 0.775), (24, 0.815), (27, 0.85), (30, 0.88), (33, 0.905), (36, 0.925), (39, 0.943),
           (42, 0.958), (48, 0.978), (54, 0.99), (62, 1.0), (78, 1.0), (86, 0.995), (94, 0.978),
           (100, 0.955), (105, 0.93), (110, 0.9), (114, 0.865), (117, 0.825), (120, 0.76), (122.5, 0.67),
           (124.2, 0.57), (125, 0.44)]
GROOVES = [0.642, 0.714, 0.786, 0.855]   # share of body height from the top: four grooves, three ribs

FACE = dict(eye_x=0.34, eye_s=0.305, eye_w=0.16, eye_h=0.264,
            smile_w=0.125, smile_end=0.36, smile_bot=0.392, smile_r=0.024,
            led_x=0.0, led_s=0.53, led_r=0.072,
            key_x=0.4, key_s=0.53, key_w=0.42, key_h=0.17)
# Arms: short plump mittens. The shoulder pivot sits at the arm's upper inner end, just inside the
# shell near the top of the ribs; at rest the arm hangs beside the lower body, angled slightly forward.
NECK, HIP = 0.6, 0.84     # joints: share of body height from the top
ARM = dict(x=0.93, y=-0.12, s=0.6, length=0.76, radius=0.27, flat=0.88, root=0.12,
           out=16.0, fwd=10.0)   # rest angles (degrees): away from the body, and forward
LEG = dict(x=0.42, y=-0.06, r=0.33, ry=0.37)


def pchip(xs, ys, x):
    from scipy.interpolate import PchipInterpolator
    return float(PchipInterpolator(xs, ys)(x))


# Front outline from the body sheet: (share of height from the top, half-width).
OUTLINE = [(0.0, 0.0), (0.004, 0.2), (0.015, 0.4), (0.035, 0.55), (0.06, 0.655), (0.09, 0.74), (0.12, 0.8),
           (0.15, 0.845), (0.18, 0.88), (0.21, 0.908), (0.24, 0.93), (0.27, 0.948), (0.3, 0.962), (0.33, 0.973),
           (0.36, 0.982), (0.4, 0.99), (0.45, 0.997), (0.5, 1.0),
           (0.6, 1.0), (0.85, 1.0), (0.875, 0.99), (0.9, 0.97), (0.925, 0.938), (0.95, 0.89), (0.97, 0.83),
           (0.986, 0.75), (0.996, 0.66), (1.0, 0.57)]   # a bullet: dome, parallel sides, tucking in below the last ridge


def half_width(s):
    """Half-width at s sheet-pixels (0..125) down from the top: the measured outline, with
    narrow shallow grooves between broad ribs whose edges are softly rounded."""
    f = min(max(s / 125, 0), 1)
    xs, ys = zip(*OUTLINE)
    r = pchip(xs, ys, f)
    for g in GROOVES:
        d = f - g
        r -= 0.018 * math.exp(-(d / 0.0045) ** 2) + 0.012 * math.exp(-(d / 0.016) ** 2)
    return r


def lathe(name, rings, segs=128, sy=1.0, angles=None):
    """rings: (z, r) from top to bottom. Quads all round; the poles close with fans."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    grid = []
    angles = angles if angles is not None else [2 * math.pi * i / segs for i in range(segs)]
    segs = len(angles)
    for z, r in rings:
        grid.append([bm.verts.new((r * math.cos(t), r * math.sin(t) * sy, z)) for t in angles])
    for j in range(len(grid) - 1):
        for i in range(segs):
            bm.faces.new((grid[j][i], grid[j + 1][i], grid[j + 1][(i + 1) % segs], grid[j][(i + 1) % segs]))
    top = bm.verts.new((0, 0, rings[0][0] + 0.0)); bot = bm.verts.new((0, 0, rings[-1][0]))
    for i in range(segs):
        bm.faces.new((top, grid[0][(i + 1) % segs], grid[0][i]))
        bm.faces.new((bot, grid[-1][i], grid[-1][(i + 1) % segs]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth = True
    return ob


def make_body():
    rings = []
    # Dense rings round the grooves, looser elsewhere.
    ss = sorted(set([0.15 * k for k in range(1, 30)] + list(np.arange(4.5, 22, 0.55)) + list(np.arange(22, 82, 0.28))
                    + list(np.arange(82, 125, 0.4)) + [g * 125 + k for g in GROOVES for k in np.arange(-2.5, 2.5, 0.12)]))
    for s in ss:
        rings.append((ZT - s / 125 * BODY_H, half_width(s)))
    rb = rings[-1][1]
    for t in (0.5, 0.75, 0.9):
        rings.append((Z0 - 0.002 * t, rb * (1 - t)))
    # Fine angular steps across the face (front is -90 degrees), coarse round the back.
    front = -math.pi / 2
    angles = list(np.arange(front - 1.0, front + 1.0, 0.0055))
    angles += list(np.arange(front + 1.0, front + 2 * math.pi - 1.0, 0.035))
    return lathe('Body', rings, sy=DEPTH, angles=angles)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def carve(body, feats):
    """Press sockets into the body: each feature is a 2D shape on the front (x, z) with a depth;
    the floor is flat and the lip is a soft S-curve, like a moulded part. Features with a 'blink'
    variant also give a 'blink' shape key, where the socket closes with the eye."""
    me = body.data
    n = len(me.vertices)
    co0 = np.empty(n * 3); me.vertices.foreach_get('co', co0); co0 = co0.reshape(n, 3)
    nor = np.empty(n * 3); me.vertices.foreach_get('normal', nor); nor = nor.reshape(n, 3)
    open_co = _carve(co0.copy(), nor, feats)
    me.vertices.foreach_set('co', open_co.ravel()); me.update()
    if any('blink' in f for f in feats):
        shut = _carve(co0.copy(), nor, [f.get('blink', f) for f in feats])
        body.shape_key_add(name='Basis'); sk = body.shape_key_add(name='blink', from_mix=False)
        sk.data.foreach_set('co', shut.ravel())


def _carve(co, nor, feats):
    n = len(co)
    x, z = co[:, 0], co[:, 2]
    disp = np.zeros(n); raise_ = np.zeros(n)
    front = co[:, 1] < -0.2
    for f in feats:
        if 'frame' in f:
            # Measured in the part's own frame (tangent x, tangent y, normal z), so the pocket is cut
            # at exactly the angle the part sits at, and its floor is flat in that frame.
            o, ex, ey, ez = f['frame']
            d = co - o; u, v, w = d @ ex, d @ ey, d @ ez
            if f['kind'] == 'ellipse':
                sdf = (np.sqrt((u / f['a']) ** 2 + (v / f['b']) ** 2) - 1) * min(f['a'], f['b'])
            elif f['kind'] == 'circle':
                sdf = np.hypot(u, v) - f['r']
            else:  # 'slot': a pill along local x
                t = np.clip(u, -f['half'], f['half']); sdf = np.hypot(u - t, v) - f['r']
            rho = f.get('rho', 0.004)
            dd = np.minimum(0, -f['depth'] - w) * (1 - smoothstep(-rho, rho, sdf))
            near = front & (np.abs(u) < 1) & (np.abs(v) < 1)
            disp = np.where(near, np.minimum(disp, dd), disp)
            continue
        if f['kind'] == 'poly3':
            P = np.array(f['pts']); d = np.full(n, 1e9)
            for p0, p1 in zip(P[:-1], P[1:]):
                vv = p1 - p0; t = np.clip(((co - p0) @ vv) / (vv @ vv), 0, 1)
                d = np.minimum(d, np.linalg.norm(co - p0 - t[:, None] * vv, axis=1))
            sdf = d - f['r']
        elif f['kind'] == 'ellipse':
            k = np.sqrt(((x - f['cx']) / f['a']) ** 2 + ((z - f['cz']) / f['b']) ** 2)
            sdf = (k - 1) * min(f['a'], f['b'])
        elif f['kind'] == 'circle':
            sdf = np.hypot(x - f['cx'], z - f['cz']) - f['r']
        else:  # 'poly': a stroke along points, round-ended
            P = np.array(f['pts']); d = np.full(n, 1e9)
            for p0, p1 in zip(P[:-1], P[1:]):
                v = p1 - p0; L2 = v @ v
                t = np.clip(((x - p0[0]) * v[0] + (z - p0[1]) * v[1]) / L2, 0, 1)
                d = np.minimum(d, np.hypot(x - p0[0] - t * v[0], z - p0[1] - t * v[1]))
            sdf = d - f['r']
        if f.get('rim'):
            h, w = f['rim']
            raise_ += np.where(front, h * np.exp(-((sdf - w) / w) ** 2), 0)
            continue
        rho = f.get('rho', 0.018)
        dd = -f['depth'] * (1 - smoothstep(-rho, rho, sdf))
        disp = np.where(front, np.minimum(disp, dd), disp)
    co += nor * (disp + raise_)[:, None]
    return co


def make_leg(side):
    """A short plump stub with a softly flattened sole; its root sits inside the underside of the body.
    Two vertex groups: the hip holds the top, the foot the bottom, blended through the middle so the
    leg bends softly between a moving body and a planted foot. A 'squash' key widens it as it compresses."""
    R, c = LEG['r'], 0.42
    top = Z0 + 0.42
    zc = R * c
    rings = [(top - (top - zc) * k / 24, R * (0.92 + 0.08 * math.sin(math.pi / 2 * k / 24))) for k in range(0, 25)]
    for k in range(1, 20):
        t = k / 19 * math.pi / 2
        rings.append((zc - zc * math.sin(t), R * ((1 - c) + c * math.cos(t))))
    sx = 1 if side == 'L' else -1
    ob = lathe(f'Leg.{side}', rings, segs=64, sy=LEG['ry'] / R)
    me = ob.data
    for v in me.vertices:
        v.co.x += sx * LEG['x']; v.co.y += LEG['y']
    gh = ob.vertex_groups.new(name=f'hip.{side}'); gf = ob.vertex_groups.new(name=f'foot.{side}')
    for v in me.vertices:
        t = min(1.0, max(0.0, (v.co.z - 0.08) / (Z0 * 0.9))); wh = t * t * (3 - 2 * t)
        gh.add([v.index], wh, 'REPLACE'); gf.add([v.index], 1 - wh, 'REPLACE')
    ob.shape_key_add(name='Basis')
    sq = ob.shape_key_add(name='squash', from_mix=False)
    cx, cy = sx * LEG['x'], LEG['y']
    for i, v in enumerate(me.vertices):
        k = 1.0 if v.co.z < Z0 else max(0.0, 1 - (v.co.z - Z0) / 0.2)
        sq.data[i].co = Vector((cx + (v.co.x - cx) * (1 + 0.05 * k), cy + (v.co.y - cy) * (1 + 0.05 * k),
                                v.co.z * (1 - 0.05 * k)))
    return ob


def arm_rest(side):
    """Shoulder pivot P and the arm's rest direction d (unit) for one side."""
    sx = 1 if side == 'L' else -1
    P = Vector((sx * ARM['x'], ARM['y'], ZT - ARM['s'] * BODY_H))
    d = Vector((0, 0, -1))
    d.rotate(Matrix.Rotation(math.radians(-sx * ARM['out']), 3, 'Y'))   # away from the body
    d.rotate(Matrix.Rotation(math.radians(-ARM['fwd']), 3, 'X'))        # a little forward
    return P, d.normalized()


def make_arm(side):
    """A mitten: an egg that is narrow at the buried root and fullest towards its round tip,
    built in rings along the arm so it bends smoothly. Two vertex groups blend through the middle."""
    sx = 1 if side == 'L' else -1
    P, d = arm_rest(side)
    out = Vector((sx, 0, 0)); out = (out - d * out.dot(d)).normalized()
    fwd = d.cross(out).normalized() * (-sx)
    if fwd.y > 0: fwd = -fwd
    L, R, root = ARM['length'], ARM['radius'], ARM['root']
    me = bpy.data.meshes.new(f'Arm.{side}'); bm = bmesh.new()
    rings, segs = 56, 48
    grid = []; us = []
    for i in range(1, rings):
        u = i / rings
        r = R * math.sqrt(max(0.0, 1 - (2 * u - 1) ** 2)) * (0.78 + 0.32 * u)
        c = P - d * root + d * (L + root) * u
        row = []
        for j in range(segs):
            a = 2 * math.pi * j / segs
            row.append(bm.verts.new(c + out * (r * math.cos(a)) + fwd * (r * ARM['flat'] * math.sin(a))))
        grid.append(row); us.append(u)
    for i in range(len(grid) - 1):
        for j in range(segs):
            bm.faces.new((grid[i][j], grid[i][(j + 1) % segs], grid[i + 1][(j + 1) % segs], grid[i + 1][j]))
    top = bm.verts.new(P - d * root); tip = bm.verts.new(P - d * root + d * (L + root))
    for j in range(segs):
        bm.faces.new((top, grid[0][(j + 1) % segs], grid[0][j]))
        bm.faces.new((tip, grid[-1][j], grid[-1][(j + 1) % segs]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(f'Arm.{side}', me); bpy.context.collection.objects.link(ob)
    for p_ in me.polygons: p_.use_smooth = True
    # Weights: the upper bone holds the root half, the lower bone the tip, blended through the middle.
    gu = ob.vertex_groups.new(name=f'arm_upper.{side}'); gl = ob.vertex_groups.new(name=f'arm_lower.{side}')
    for v in me.vertices:
        u = max(0.0, min(1.0, (v.co - (P - d * root)).dot(d) / (L + root)))
        t = max(0.0, min(1.0, (u - 0.35) / 0.4)); wl = t * t * (3 - 2 * t)
        gu.add([v.index], 1 - wl, 'REPLACE'); gl.add([v.index], wl, 'REPLACE')
    # Contact squash: the front of the mitten's tip flattens a little and spreads to keep its volume.
    ob.shape_key_add(name='Basis')
    sq = ob.shape_key_add(name='squash', from_mix=False)
    for i, v in enumerate(me.vertices):
        rel = v.co - P
        u = max(0.0, min(1.0, (rel.dot(d) + root) / (L + root)))
        k = max(0.0, (u - 0.45) / 0.55)
        f = rel.dot(fwd)
        o = rel.dot(out)
        new = v.co - fwd * (max(0.0, f) * 0.22 * k) + out * (o * 0.06 * k)
        sq.data[i].co = new
    return ob, P, d


def surface(body, x, s):
    """Point and normal on the front of the body at x, s (share of body height from the top)."""
    deps = bpy.context.evaluated_depsgraph_get()
    z = ZT - s * BODY_H
    hit, loc, nor, *_ = body.ray_cast(Vector((x, -5, z)), Vector((0, 1, 0)), depsgraph=deps)
    assert hit, (x, s)
    return loc, nor


def orient(ob, loc, nor, lift=0.0, spin=0.0):
    z = nor.normalized(); x = Vector((0, 0, 1)).cross(z).normalized(); y = z.cross(x)
    m = Matrix((x, y, z)).transposed().to_4x4()
    if spin: m = m @ Matrix.Rotation(spin, 4, 'Z')
    m.translation = loc + nor * lift
    ob.matrix_world = m


def eye_mesh(w, h, d, r):
    """An upright pill w x h, d deep, with a 'closed' shape key: a horizontal bar w long and 2r thick
    (the mouth's thickness), round-ended. Both shapes come from the same sphere, so the morph is clean."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=48, radius=1)
    ob = bpy.context.object; ob.name = 'Eye'
    sph = [v.co.copy() for v in ob.data.vertices]
    def pill(p, long_y, w_, h_, d_):
        x, y, z = p
        if long_y:
            half = max(0.0, (h_ - w_) / 2)
            return Vector((x * w_ / 2, y * w_ / 2 + math.copysign(half, y) * (y != 0), z * d_ / 2))
        half = max(0.0, (w_ - h_) / 2)
        return Vector((x * h_ / 2 + math.copysign(half, x) * (x != 0), y * h_ / 2, z * d_ / 2))
    for v, p in zip(ob.data.vertices, sph): v.co = pill(p, True, w, h, d)
    for pg in ob.data.polygons: pg.use_smooth = True
    ob.shape_key_add(name='Basis'); k = ob.shape_key_add(name='closed', from_mix=False)
    for i, p in enumerate(sph): k.data[i].co = pill(p, False, w, 2 * r, 2 * r)
    return ob


def frame(loc, nor, spin=0.0):
    """The same axes orient() gives a part: x and y along the surface, z out of it."""
    z = nor.normalized(); x = Vector((0, 0, 1)).cross(z).normalized(); y = z.cross(x)
    if spin:
        x, y = x * math.cos(spin) + y * math.sin(spin), -x * math.sin(spin) + y * math.cos(spin)
    return tuple(np.array(a) for a in (loc, x, y, z))


def capsule(name, w, h, d, segs=48, flat=1.0):
    """A pill w wide, h long, d deep. flat < 1 squares the depth profile off into a soft-edged slab."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=48, radius=1)
    ob = bpy.context.object; ob.name = name
    half = max(0.0, (h - w) / 2)
    for v in ob.data.vertices:
        x, y, z = v.co
        z = math.copysign(abs(z) ** flat, z)
        v.co = Vector((x * w / 2, y * w / 2 + (half if y > 0 else -half if y < 0 else 0), z * d / 2))
    for p in ob.data.polygons: p.use_smooth = True
    return ob


def curve_on(body, name, pts, radius, mat, lift=0.004):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, (x, s) in enumerate(pts):
        loc, nor = surface(body, x, s)
        p = loc + nor * lift
        sp.points[i].co = (p.x, p.y, p.z, 1)
    cu.bevel_depth = radius; cu.bevel_resolution = 6; cu.use_fill_caps = True
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


def materials():
    def mat(name, color, rough, **kw):
        m = bpy.data.materials.new(name)
        p = m.node_tree.nodes['Principled BSDF']
        p.inputs['Base Color'].default_value = (*color, 1)
        p.inputs['Roughness'].default_value = rough
        for k, v in kw.items(): p.inputs[k].default_value = v
        return m, p
    plastic, p = mat('Plastic', (0.585, 0.54, 0.515), 0.66, **{'Subsurface Weight': 0.1, 'Subsurface Scale': 0.05,
                                                              'Specular IOR Level': 0.3, 'Sheen Weight': 0.35,
                                                              'Sheen Roughness': 0.45})
    nt = plastic.node_tree   # soft-touch: a faint noise bump
    tex = nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = 260; tex.inputs['Detail'].default_value = 4
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.06; bump.inputs['Distance'].default_value = 0.002
    nt.links.new(tex.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    gloss, _ = mat('Gloss', (0.0086, 0.0086, 0.0086), 0.23, **{'IOR': 1.46})   # #171717
    ink, _ = mat('Ink', (0.006, 0.006, 0.007), 0.5)
    led, _ = mat('LED', (0.028, 0.451, 0.084), 0.08, **{'Emission Color': (0.028, 0.451, 0.084, 1), 'Emission Strength': 3.5,
                                                       'Coat Weight': 1.0, 'Coat Roughness': 0.05})
    ledoff, _ = mat('LEDOff', (0.53, 0.53, 0.52), 0.12, **{'Coat Weight': 1.0, 'Coat Roughness': 0.05})
    keycap, _ = mat('Keycap', (0.61, 0.59, 0.56), 0.58, **{'Sheen Weight': 0.25, 'Sheen Roughness': 0.5})
    slot, _ = mat('Slot', (0.30, 0.28, 0.26), 0.6)
    shine, _ = mat('Shine', (1, 1, 1), 0.3, **{'Emission Color': (1, 1, 1, 1), 'Emission Strength': 0.6})
    pocket, _ = mat('Pocket', (0.36, 0.34, 0.32), 0.6)
    housing, _ = mat('Housing', (0.42, 0.4, 0.38), 0.55)
    ball, _ = mat('Ball', (0.8, 0.55, 0.2), 0.6)
    return dict(ball=ball, housing=housing, pocket=pocket, shine=shine, plastic=plastic, gloss=gloss, ink=ink, led=led, ledoff=ledoff, keycap=keycap, slot=slot)


FACES = {   # name: ((his left eye, his right eye), mouth)
    'smile': (('open', 'open'), 'smile'), 'happy': (('happy', 'happy'), 'smile'),
    'content': (('content', 'content'), 'smile'), 'sip': (('content', 'content'), 'o'),
    'wink': (('open', 'happy'), 'smile'), 'muse': (('open', 'open'), 'o'), 'shout': (('happy', 'happy'), 'shout'),
    'surprised': (('open', 'open'), 'shout'), 'closed': (('content', 'content'), 'smile'), 'o': (('open', 'open'), 'o'),
}

POSES = {
    # face: smile | closed | o ; led on/off ; anim: (action, frame) to pose from
    'front': {}, 'rest': {},
    'wave': {'anim': ('wave', 15)},
    'reach': {'anim': ('reach', 30), 'ball': True},
    'sleep': {'face': 'closed', 'led': False, 'tilt': (6, 0)},
    'sit': {'sit': True},
    'walk': {'anim': ('walk', 8)},
    'jump': {'anim': ('jump', 7)},
    'surprised': {'face': 'surprised'},
    'face_smile': {'face': 'smile'},
    'face_happy': {'face': 'happy'},
    'face_content': {'face': 'content'},
    'face_sip': {'face': 'sip'},
    'face_wink': {'face': 'wink'},
    'face_muse': {'face': 'muse'},
    'face_shout': {'face': 'shout'},
}

FPS = 24


def wq(pb, rot_world):
    """A pose-bone rotation from a world-space rotation (3x3) about the bone's rest frame."""
    Mr = pb.bone.matrix_local.to_3x3()
    return (Mr.inverted() @ rot_world @ Mr).to_quaternion()


def arm_rot(sx, out=0.0, fwd=0.0, inward=0.0):
    """Swing an arm: `out` raises it sideways, `fwd` raises it forwards, `inward` turns it toward the middle."""
    return (Matrix.Rotation(math.radians(-fwd), 3, 'X') @ Matrix.Rotation(math.radians(-sx * out), 3, 'Y')
            @ Matrix.Rotation(math.radians(sx * inward), 3, 'Z'))


def key_arm(rig, side, frame, out=0.0, fwd=0.0, inward=0.0, curl=0.0, hug=0.0, slide=0.0):
    """Key one arm: shoulder swing, a soft bend through the lower bone, and the attachment travelling
    round the shell (slide, in degrees; forward is positive), turning with the surface as it goes."""
    sx = 1 if side == 'L' else -1
    att, sh, lo = (rig.pose.bones[f'{n}.{side}'] for n in ('attach', 'shoulder', 'arm_lower'))
    Mr = att.bone.matrix_local.to_3x3()
    # slide: degrees around the shell; positive carries the shoulder forward along the round edge
    att.rotation_quaternion = wq(att, Matrix.Rotation(math.radians(-sx * slide), 3, 'Z'))
    sh.rotation_quaternion = wq(sh, arm_rot(sx, out, fwd, inward))
    lo.rotation_quaternion = wq(lo, Matrix.Rotation(math.radians(-curl), 3, 'X') @ Matrix.Rotation(math.radians(sx * hug), 3, 'Y'))
    for b in (att, sh, lo):
        b.keyframe_insert('rotation_quaternion', frame=frame)


def key_body(rig, frame, lean_x=0.0, lean_y=0.0, bob=0.0):
    b = rig.pose.bones['body']
    b.rotation_quaternion = wq(b, Matrix.Rotation(math.radians(lean_x), 3, 'X') @ Matrix.Rotation(math.radians(lean_y), 3, 'Y'))
    b.location = b.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, bob))
    b.keyframe_insert('rotation_quaternion', frame=frame); b.keyframe_insert('location', frame=frame)


def bone_loc(pb, v):
    """Set a pose bone's location from an armature-space offset."""
    pb.location = pb.bone.matrix_local.to_3x3().inverted() @ Vector(v)


def key(pb, f, loc=True, rot=True, scale=False):
    if loc: pb.keyframe_insert('location', frame=f)
    if rot: pb.keyframe_insert('rotation_quaternion', frame=f)
    if scale: pb.keyframe_insert('scale', frame=f)


def squash_body(pb, k):
    """Squash (k < 1) or stretch (k > 1) along the bone, keeping the volume: the sides take 1/sqrt(k)."""
    w = 1 / math.sqrt(k); pb.scale = (w, k, w)   # bone y runs up the body


def neutral(rig, frame=1):
    """Key every bone at rest on `frame`, so channels a move leaves alone don't inherit another move."""
    for pb in rig.pose.bones:
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
        pb.keyframe_insert('location', frame=frame); pb.keyframe_insert('rotation_quaternion', frame=frame)
        pb.keyframe_insert('scale', frame=frame)


BODY = []       # the shell, when it has a 'blink' shape key
LIMBS = []      # arm and leg meshes, set by build(); each move gets its own shape-key action for them
EYES = []       # eye meshes, for blinks


def new_action(rig, name):
    act = bpy.data.actions.new(name); rig.animation_data.action = act; neutral(rig)
    for ob in LIMBS:
        sk = ob.data.shape_keys; sk.animation_data_create()
        sk.animation_data.action = bpy.data.actions.new(f'{name}|{ob.name}')
        sk.key_blocks['squash'].value = 0; sk.key_blocks['squash'].keyframe_insert('value', frame=1)
    for ob, kn in [(o, 'blink') for o in BODY] + [(o, 'closed') for o in EYES]:
        sk = ob.data.shape_keys; sk.animation_data_create()
        sk.animation_data.action = bpy.data.actions.new(f'{name}|{ob.name}')
        sk.key_blocks[kn].value = 0; sk.key_blocks[kn].keyframe_insert('value', frame=1)
    return act


def use_move(name):
    """Play a move: the rig's action plus that move's shape-key and eye actions."""
    rig = bpy.data.objects['Rig']; rig.animation_data.action = bpy.data.actions[name]
    for ob in LIMBS:
        sk = ob.data.shape_keys; sk.animation_data_create()
        sk.animation_data.action = bpy.data.actions.get(f'{name}|{ob.name}')
        if sk.animation_data.action is None: sk.key_blocks['squash'].value = 0
    for ob, kn in [(o, 'blink') for o in BODY] + [(o, 'closed') for o in EYES]:
        sk = ob.data.shape_keys; sk.animation_data_create()
        sk.animation_data.action = bpy.data.actions.get(f'{name}|{ob.name}')
        if sk.animation_data.action is None: sk.key_blocks[kn].value = 0


def heel_toe(tilt):
    """Height to raise a tilted foot so it pivots on its heel or toe edge instead of sinking."""
    return 0.36 * math.sin(math.radians(abs(tilt)))


def joint(rig, name, f, x=0.0, y=0.0, z=0.0):
    """Key a joint: x nods forward, y tilts toward +x (his left), z turns to his left."""
    pb = rig.pose.bones[name]
    pb.rotation_quaternion = wq(pb, Matrix.Rotation(math.radians(z), 3, 'Z') @ Matrix.Rotation(math.radians(y), 3, 'Y')
                                @ Matrix.Rotation(math.radians(x), 3, 'X'))
    pb.keyframe_insert('rotation_quaternion', frame=f)


def stash(rig, act, name):
    act.use_fake_user = True
    trk = rig.animation_data.nla_tracks.new(); trk.name = name; trk.strips.new(name, 1, act); trk.mute = True


def walk(rig, legs, T=28, S=0.58, lift=0.14):
    """A travelling walk, T = 28 frames for left + right at 24 fps.

    Frame 1 contact (left foot down ahead, shell between the feet, moving left), 4 down (left takes the
    weight, shell lowest, right foot releases), 8 passing (right swings past, shell over the left foot,
    rising), 12 up (shell highest, left rolls to its front edge), 15 the same on the right, 29 = frame 1
    one stride on. Feet hold their world position from contact to push-off. The shell leans forward a
    little, shifts and tilts toward the supporting foot, and travels ~2.5% of its height up and down."""
    act = new_action(rig, 'walk')
    pb = rig.pose.bones; root, body = pb['root'], pb['body']
    STANCE = 17; SWING = T - STANCE
    v = S / (T / 2); half = v * STANCE / 2
    A = 0.025 * BODY_H                              # vertical travel, lowest to highest
    BOB = {0: -0.25, 3: -0.5, 7: 0.05, 11: 0.5, 14: -0.25}   # in units of A, over half a cycle
    contact = {'L': 0, 'R': T // 2}; hist = []
    for f in range(1, T + 2):
        t = f - 1
        bone_loc(root, (0, -v * t, 0)); key(root, f, rot=False)
        rels = {}
        for side in 'LR':
            w = (t - contact[side]) % T
            foot, hip = pb[f'foot.{side}'], pb[f'hip_attach.{side}']
            if w < STANCE:                          # planted: settle, carry the weight, roll onto the front
                k = w / STANCE
                rel = -half + 2 * half * k
                tilt = -8 * max(0.0, 1 - w / 3) + 16 * max(0.0, (w - 12) / 5)    # toe up on landing; heel up at push-off
                z = 0.03 * max(0.0, (w - 12) / 5)
                squash = max(0.0, 1 - abs(w - 3) / 4) + 0.2 * (3 < w < 12)       # compress most at 'down'
            else:                                   # swing: a short, low arc forward
                u = (w - STANCE) / SWING; e = u * u * (3 - 2 * u)
                rel = half - 2 * half * e; z = lift * math.sin(math.pi * u)
                tilt = 16 * (1 - u) ** 2 - 8 * max(0.0, (u - 0.6) / 0.4)
                squash = 0.0
            rels[side] = rel
            bone_loc(foot, (0, rel, z + heel_toe(tilt)))
            foot.rotation_quaternion = wq(foot, Matrix.Rotation(math.radians(tilt), 3, 'X'))
            key(foot, f)
            bone_loc(hip, (0, -0.3 * rel, 0)); key(hip, f, rot=False)      # the hip helps the reach
            sk = legs[side].data.shape_keys.key_blocks['squash']; sk.value = min(1.0, squash); sk.keyframe_insert('value', frame=f)
        # Shell: lean forward, shift + tilt toward the supporting foot (left until ~frame 15), bob.
        side_w = math.cos(2 * math.pi * (t - 7) / T)                       # +1 over the left foot at 'passing'
        hc = t % (T // 2); ks = sorted(BOB)
        for a_, b_ in zip(ks, ks[1:]):
            if a_ <= hc <= b_:
                x = (hc - a_) / (b_ - a_); x = x * x * (3 - 2 * x)
                bob = (BOB[a_] + (BOB[b_] - BOB[a_]) * x) * A
        body.rotation_quaternion = wq(body, Matrix.Rotation(math.radians(3 * side_w), 3, 'Y')
                                      @ Matrix.Rotation(math.radians(4), 3, 'X'))
        bone_loc(body, (0.035 * side_w, 0, bob))
        squash_body(body, 1 + 0.025 * bob / A)          # a little squash at 'down', stretch at 'up'
        key(body, f, scale=True)
        hist.append(dict(rels))
    for f in range(1, T + 2):
        t = f - 1
        sw = math.cos(2 * math.pi * (t - 7) / T); swd = math.cos(2 * math.pi * (t - 9) / T)
        joint(rig, 'hips', f, y=-1.5 * sw, z=4 * math.sin(2 * math.pi * (t - 7) / T))
        hc = t % (T // 2)
        joint(rig, 'head', f, x=1.5 * math.exp(-((hc - 5) / 2.5) ** 2), y=-2 * swd)
    for f in range(1, T + 2):                        # arms swing opposite the feet, trailing by two frames
        r = hist[(f - 1 - 2) % T]
        for side in 'LR':
            key_arm(rig, side, f, fwd=12 * r[side] / half, out=3)
    stash(rig, act, 'walk')


def jump(rig, legs):
    """A jump built on the animation principles: a slow anticipation crouch with a moving hold, squash
    and stretch on the shell (volume kept), eased arcs, a tuck of the feet at the apex, feet landing
    first, then a squashed dip, an overshoot and a settle; the arms trail the body by a couple of
    frames and flop through on landing (follow-through and overlap)."""
    act = new_action(rig, 'jump')
    pb = rig.pose.bones; root, body = pb['root'], pb['body']
    # frame: root z (feet), shell z, shell squash/stretch, forward lean, leg squash, feet tuck
    shell = [(1, 0, 0, 1.0, 0, 0, 0), (5, 0, 0.012, 1.02, -1, 0, 0),          # a small rise before the dip
             (11, 0, -0.12, 0.9, 7, 1.0, 0), (14, 0, -0.13, 0.89, 8, 1.0, 0),  # crouch, then a moving hold
             (17, 0, 0.07, 1.12, -2, 0, 0),                                   # launch: stretched, feet still down
             (19, 0.14, 0.05, 1.1, -3, 0, 0.3),                               # feet leave the floor
             (25, 0.5, 0.0, 0.98, 0, 0, 1.0),                                 # apex: round again, feet tucked
             (29, 0.3, 0.01, 1.05, 2, 0, 0.6),                                # falling: stretching into the drop
             (32, 0.0, 0.03, 1.06, 3, 0.3, 0),                                # feet touch first
             (34, 0, -0.11, 0.88, 6, 1.0, 0),                                 # the shell lands into them
             (38, 0, 0.025, 1.035, -1.5, 0, 0),                               # overshoot
             (42, 0, -0.008, 0.99, 0.5, 0.15, 0), (47, 0, 0, 1.0, 0, 0, 0)]   # settle
    for f, rz, bz, k, lean, sq, tuck in shell:
        bone_loc(root, (0, 0, rz)); key(root, f, rot=False)
        bone_loc(body, (0, 0, bz)); squash_body(body, k)
        body.rotation_quaternion = wq(body, Matrix.Rotation(math.radians(lean), 3, 'X'))
        key(body, f, scale=True)
        for side in 'LR':
            sk = legs[side].data.shape_keys.key_blocks['squash']; sk.value = sq; sk.keyframe_insert('value', frame=f)
            fb = pb[f'foot.{side}']
            bone_loc(fb, (0, 0.03 * tuck, 0.08 * tuck))
            fb.rotation_quaternion = wq(fb, Matrix.Rotation(math.radians(18 * tuck), 3, 'X')); key(fb, f)
    for f, hx in ((1, 0), (13, 7), (16, 8), (19, -7), (23, -3), (27, 1), (31, -2), (36, 9), (40, -3), (44, 1), (48, 0)):
        joint(rig, 'head', f, x=hx)
    for f, px in ((1, 0), (11, -5), (14, -6), (17, 3), (21, 0), (34, -5), (38, 1), (47, 0)):
        joint(rig, 'hips', f, x=px)
    # Arms trail: back and down in the crouch, swung up with the launch, still lifting at the apex,
    # dragging high as he falls, flopping down past rest on landing, then a small bounce.
    arms = [(1, 0, 0), (7, 4, 2), (13, -6, -28), (16, -4, -32), (20, 40, 22), (26, 62, 18), (31, 58, 10),
            (35, -12, -6), (39, 8, 3), (44, -2, 0), (47, 0, 0)]
    for f, out, fwd in arms:
        for side, lag in (('L', 0), ('R', 1)):                   # one arm a frame behind the other
            key_arm(rig, side, f + lag, out=out, fwd=fwd, curl=max(0, out) * 0.12)
    stash(rig, act, 'jump')


def smooth_track(keys, f):
    """Value at frame f from (frame, value) keys, eased between neighbours (values may be tuples)."""
    if f <= keys[0][0]: return keys[0][1]
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f0 <= f <= f1:
            x = (f - f0) / (f1 - f0); x = x * x * (3 - 2 * x)
            if isinstance(v0, tuple): return tuple(a + (b - a) * x for a, b in zip(v0, v1))
            return v0 + (v1 - v0) * x
    return keys[-1][1]


def foot_rest(side, yaw=0.0, at=(0.0, 0.0)):
    """Where a foot stands at rest, for a body facing `yaw` (degrees) standing at `at`."""
    sx = 1 if side == 'L' else -1
    v = Vector((sx * LEG['x'], LEG['y'], 0)); v.rotate(Matrix.Rotation(math.radians(yaw), 3, 'Z'))
    return (at[0] + v.x, at[1] + v.y)


def steps(rig, legs, name, n, root, feet, shell, arms=None, head_track=None, hips_track=None):
    """Key a stepping move frame by frame from world-space targets, so planted feet hold still in the
    world even while the root turns or travels.
      root:  [(frame, (x, y, yaw))]
      feet:  {side: [(frame, (x, y, yaw, lift, tilt))]}   world space; lift/tilt in units / degrees
      shell: [(frame, (shift, bob, side_tilt, lean))]       relative to the root
      squash: derived from lift (compresses just after a foot lands)"""
    act = new_action(rig, name)
    pb = rig.pose.bones; rb, body = pb['root'], pb['body']
    landed = {s_: -99 for s_ in 'LR'}
    for f in range(1, n + 1):
        rx, ry, ryaw = smooth_track(root, f)
        R = Matrix.Rotation(math.radians(ryaw), 3, 'Z'); Ri = R.inverted()
        bone_loc(rb, (rx, ry, 0)); rb.rotation_quaternion = wq(rb, R); key(rb, f)
        for s_ in 'LR':
            x, y, yaw, lift, tilt = smooth_track(feet[s_], f)
            fb = pb[f'foot.{s_}']; head = fb.bone.head_local
            local = Ri @ Vector((x - rx, y - ry, lift + heel_toe(tilt))) - Vector((head.x, head.y, 0))
            bone_loc(fb, local)
            fb.rotation_quaternion = wq(fb, Ri @ Matrix.Rotation(math.radians(yaw), 3, 'Z') @ Matrix.Rotation(math.radians(tilt), 3, 'X'))
            key(fb, f)
            prev = smooth_track(feet[s_], f - 1)[3]
            if prev > 0.004 and lift <= 0.004: landed[s_] = f
            sq = max(0.0, 1 - abs(f - landed[s_] - 2) / 4) if lift <= 0.004 else 0.0
            sk = legs[s_].data.shape_keys.key_blocks['squash']; sk.value = sq; sk.keyframe_insert('value', frame=f)
        shift, bob, tilt, lean = smooth_track(shell, f)
        body.rotation_quaternion = wq(body, R @ Matrix.Rotation(math.radians(tilt), 3, 'Y') @ Matrix.Rotation(math.radians(lean), 3, 'X') @ Ri)
        bone_loc(body, R @ Vector((shift, 0, bob)) if False else (shift, 0, bob))
        key(body, f)
        for s_ in 'LR':
            fw = smooth_track(arms[s_], f) if arms else 0.0
            key_arm(rig, s_, f, fwd=fw, out=3)
        if head_track: joint(rig, 'head', f, *smooth_track(head_track, f))
        if hips_track: joint(rig, 'hips', f, *smooth_track(hips_track, f))
    stash(rig, act, name)


def start_stop_turn(rig, legs, S=0.58):
    """Start (rest into the walk's first contact), stop (a short last step, dip, settle) and a 90 degree
    turn to the left in two steps, all keyed from world-space foot targets."""
    T = 28; v = S / (T / 2); half = v * 17 / 2; A = 0.025 * BODY_H
    L0, R0 = foot_rest('L'), foot_rest('R')
    # Start: weight onto the right foot, the left steps out; ends on the walk's frame 1, root at -half.
    steps(rig, legs, 'walk_start', 20,
          root=[(1, (0, 0, 0)), (8, (0, 0, 0)), (20, (0, -half, 0))],
          feet={'L': [(1, (L0[0], L0[1], 0, 0, 0)), (7, (L0[0], L0[1], 0, 0, 10)), (13, (L0[0], -half * 1.1, 0, 0.12, 0)),
                      (19, (L0[0], L0[1] - 2 * half, 0, 0, -8)), (20, (L0[0], L0[1] - 2 * half, 0, 0, -8))],
                'R': [(1, (R0[0], R0[1], 0, 0, 0)), (20, (R0[0], R0[1], 0, 0, 0))]},
          shell=[(1, (0, 0, 0, 0)), (7, (-0.04, -0.2 * A, -3, 1)), (14, (-0.03, 0.4 * A, -2, 3)), (20, (0.0, -0.25 * A, 0, 4))],
          arms={'L': [(1, 0), (20, -12)], 'R': [(1, 0), (20, 12)]})
    # Stop: from the walk's frame 1 (left ahead, right behind), the right makes a short step to land
    # beside the left; the shell dips as it lands, then settles upright between both feet.
    yL = L0[1] - half; yR = R0[1] + half
    steps(rig, legs, 'walk_stop', 26,
          root=[(1, (0, 0, 0)), (12, (0, -half, 0)), (26, (0, -half, 0))],
          feet={'L': [(1, (L0[0], yL, 0, 0, -8)), (4, (L0[0], yL, 0, 0, 0)), (26, (L0[0], yL, 0, 0, 0))],
                'R': [(1, (R0[0], yR, 0, 0, 10)), (4, (R0[0], yR, 0, 0.02, 14)), (8, (R0[0], (yR + yL) / 2, 0, 0.09, 4)),
                      (12, (R0[0], yL, 0, 0, -5)), (14, (R0[0], yL, 0, 0, 0)), (26, (R0[0], yL, 0, 0, 0))]},
          shell=[(1, (0.02, -0.25 * A, 1, 4)), (8, (0.03, 0.3 * A, 2, 3)), (12, (0, -0.2 * A, 0, 2)),
                 (15, (0, -0.7 * A, 0, 1)), (20, (0, 0.1 * A, 0, 0)), (26, (0, 0, 0, 0))],
          arms={'L': [(1, -12), (14, 3), (20, -1), (26, 0)], 'R': [(1, 12), (14, -3), (20, 1), (26, 0)]},
          head_track=[(1, (0, 0, 0)), (13, (0, 0, 0)), (17, (5, 0, 0)), (21, (-2, 0, 0)), (26, (0, 0, 0))])
    # Turn 90 degrees left in place: the shell starts to face the new way as the left foot steps into
    # it; weight transfers onto that foot before the right comes round; the left squares up last.
    L45, R90, L90 = foot_rest('L', 45), foot_rest('R', 90), foot_rest('L', 90)
    steps(rig, legs, 'turn', 36,
          root=[(1, (0, 0, 0)), (5, (0, 0, 0)), (15, (0, 0, 45)), (27, (0, 0, 90)), (36, (0, 0, 90))],
          feet={'L': [(1, (L0[0], L0[1], 0, 0, 0)), (6, (L0[0], L0[1], 0, 0, 8)), (10, ((L0[0] + L45[0]) / 2, (L0[1] + L45[1]) / 2, 22, 0.1, 0)),
                      (14, (L45[0], L45[1], 45, 0, -6)), (15, (L45[0], L45[1], 45, 0, 0)), (28, (L45[0], L45[1], 45, 0, 0)),
                      (31, ((L45[0] + L90[0]) / 2, (L45[1] + L90[1]) / 2, 68, 0.05, 0)), (34, (L90[0], L90[1], 90, 0, 0)),
                      (36, (L90[0], L90[1], 90, 0, 0))],
                'R': [(1, (R0[0], R0[1], 0, 0, 0)), (17, (R0[0], R0[1], 0, 0, 8)), (21, ((R0[0] + R90[0]) / 2, (R0[1] + R90[1]) / 2, 45, 0.1, 0)),
                      (26, (R90[0], R90[1], 90, 0, -6)), (27, (R90[0], R90[1], 90, 0, 0)), (36, (R90[0], R90[1], 90, 0, 0))]},
          shell=[(1, (0, 0, 0, 0)), (5, (-0.04, -0.2 * A, -3, 1)), (12, (-0.01, 0.3 * A, -1, 2)), (16, (0.04, -0.4 * A, 3, 2)),
                 (22, (0.03, 0.3 * A, 2, 2)), (27, (0, -0.4 * A, 0, 1)), (31, (-0.015, 0, -1, 0)), (36, (0, 0, 0, 0))],
          head_track=[(1, (0, 0, 0)), (4, (1, 0, 18)), (12, (0, 2, 14)), (20, (0, -1, 12)), (27, (1, 0, -4)), (32, (0, 0, 2)), (36, (0, 0, 0))],
          hips_track=[(1, (0, 0, 0)), (8, (0, 0, -6)), (15, (0, 1, 3)), (20, (0, 0, -6)), (27, (0, 0, 2)), (36, (0, 0, 0))])


BLINK = ((1, 0), (71, 0), (73, 1), (74, 1), (78, 0), (97, 0))   # frame, how closed


def idle(rig):
    """A 96-frame (4 s) idle loop that begins and ends at rest, so any move can start from it. Calm:
    one slow breath (a hint of stretch on the in-breath), a small weight shift from foot to foot, a curious look toward the viewer with a moving hold, a little head tilt, arms drifting a
    beat behind the body, and one blink (fast close, slower open)."""
    act = new_action(rig, 'idle'); N = 96
    pb = rig.pose.bones; body = pb['body']
    for f in range(1, N + 2):
        t = (f - 1) / N
        breath = math.sin(2 * math.pi * t)                           # one slow breath per loop
        shift = math.sin(2 * math.pi * t)                            # one gentle weight shift each way
        squash_body(body, 1 + 0.008 * max(0.0, breath) - 0.003 * max(0.0, -breath))
        body.rotation_quaternion = wq(body, Matrix.Rotation(math.radians(0.6 * shift), 3, 'Y'))
        bone_loc(body, (0.006 * shift, 0, 0.004 * breath))
        key(body, f, scale=True)
        joint(rig, 'hips', f, y=-0.3 * shift)
        # Look toward the viewer and hold (moving hold), tilt, then come back.
        look = smooth_track([(1, 0.0), (22, 0.0), (32, 1.0), (54, 1.08), (64, 0.0), (97, 0.0)], f)
        tilt = smooth_track([(1, 0.0), (40, 0.0), (48, 1.0), (60, 1.0), (70, 0.0), (97, 0.0)], f)
        joint(rig, 'head', f, x=-1.0 * look + 0.4 * breath, y=2.5 * tilt, z=-5 * look)
        drag = math.sin(2 * math.pi * (t - 0.04))                    # arms a beat behind the shift
        for s_, sx in (('L', 1), ('R', -1)):
            key_arm(rig, s_, f, out=1.5 + 0.7 * math.sin(2 * math.pi * (t - 0.03)), fwd=0.8 * sx * drag)
    # One blink, close in 2 frames and open in 4; the sockets close with the eyes.
    for ob, kn in [(o, 'closed') for o in EYES] + [(o, 'blink') for o in BODY]:
        sk = ob.data.shape_keys.key_blocks[kn]
        for f, c in BLINK:
            sk.value = c; sk.keyframe_insert('value', frame=f)
        sk.value = 0
    stash(rig, act, 'idle')


def walk_in(rig, legs, view=-18.0, D=3.0, F=12, swing=8, cheat=25.0):
    """Walk in from the right of the frame toward the page's text, a last short step, turn to face the
    viewer (the head leads), and end exactly at rest so the idle can follow.
    `view` is the rig's turn in the hero render; the path is laid out so it runs straight across the
    screen (world -x) from D units to the right."""
    A = 0.025 * BODY_H
    a = math.radians(view)
    # Straight across the screen (world -x), at a constant distance from the camera so he doesn't
    # change size; his body is cheated `cheat` degrees toward the camera so his face stays readable.
    travel = Matrix.Rotation(-a, 3, 'Z') @ Vector((-1, 0, 0))
    yaw = math.degrees(math.atan2(-travel.x, travel.y)) + 180    # facing along the travel
    yaw = (yaw + 180) % 360 - 180 + cheat
    start = -travel * D
    n = int(round(D / 0.5))                                      # steps of about 0.5
    t_walk = 1 + n * F                                           # last walking step lands here
    def root_at(f):
        u = min(1.0, max(0.0, (f - 1) / (t_walk - 1)))
        u = u * u * (3 - 2 * u) if False else u                  # constant pace; the steps carry the ease
        return start + (Vector((0, 0, 0)) - start) * u
    feet = {'L': [], 'R': []}
    side = ['L', 'R']
    # Both feet start planted at rest around the start point.
    for s_ in 'LR':
        x, y = foot_rest(s_, yaw, (start.x, start.y)); feet[s_].append((1, (x, y, yaw, 0, 0)))
    last = {s_: feet[s_][0][1] for s_ in 'LR'}
    shell = [(1, (0, 0, 0, 2))]
    arms = {'L': [(1, 0)], 'R': [(1, 0)]}
    for k in range(n):
        s_ = side[k % 2]; land = 1 + (k + 1) * F; lift = land - swing
        if k == n - 1:
            tgt = foot_rest(s_, yaw, (0, 0))                     # the last step lands at rest
        else:
            r = root_at(land) + travel * 0.25
            tgt = foot_rest(s_, yaw, (r.x, r.y))
        lx, ly = last[s_][0], last[s_][1]
        feet[s_] += [(lift, (lx, ly, yaw, 0, 10)), (lift + swing // 2, ((lx + tgt[0]) / 2, (ly + tgt[1]) / 2, yaw, 0.1, 2)),
                     (land, (tgt[0], tgt[1], yaw, 0, -6)), (land + 2, (tgt[0], tgt[1], yaw, 0, 0))]
        last[s_] = (tgt[0], tgt[1])
        sup = 1 if s_ == 'L' else -1                              # weight moves onto the landing foot
        shell += [(land - 3, (0.0, 0.3 * A, -1.5 * sup, 4)), (land + 2, (0.03 * sup, -0.5 * A, 2.5 * sup, 4))]
        arms[s_] += [(land, -12)]; arms['L' if s_ == 'R' else 'R'] += [(land, 12)]
    # The trailing foot closes in beside the other.
    o = side[n % 2]; tgt = foot_rest(o, yaw, (0, 0)); lx, ly = last[o]; t = t_walk
    feet[o] += [(t + 1, (lx, ly, yaw, 0, 8)), (t + 5, ((lx + tgt[0]) / 2, (ly + tgt[1]) / 2, yaw, 0.06, 0)),
                (t + 9, (tgt[0], tgt[1], yaw, 0, 0))]
    shell += [(t + 4, (0, 0.2 * A, 0, 2)), (t + 10, (0, -0.6 * A, 0, 1)), (t + 15, (0, 0.1 * A, 0, 0))]
    arms['L'] += [(t + 6, 3), (t + 12, -1), (t + 16, 0)]; arms['R'] += [(t + 6, -3), (t + 12, 1), (t + 16, 0)]
    # Turn to face the viewer: the head looks first, then two small steps bring the body round.
    t = t + 14
    mid = yaw / 2
    for s_, t_land, y_ in (('R', t + 8, mid), ('L', t + 14, 0.0), ('R', t + 20, 0.0)):
        x0, y0 = feet[s_][-1][1][:2]; x1, y1 = foot_rest(s_, y_, (0, 0))
        feet[s_] += [(t_land - 5, (x0, y0, feet[s_][-1][1][2], 0, 6)), (t_land - 2, ((x0 + x1) / 2, (y0 + y1) / 2, y_, 0.06, 0)),
                     (t_land, (x1, y1, y_, 0, 0))]
    end = t + 30
    for s_ in 'LR':
        feet[s_].append((end, (*foot_rest(s_, 0, (0, 0)), 0, 0, 0)))
    shell += [(t + 8, (-0.02, -0.3 * A, -1.5, 0)), (t + 14, (0.02, -0.4 * A, 1.5, 0)), (t + 21, (0, -0.2 * A, 0, 0)), (end, (0, 0, 0, 0))]
    arms['L'] += [(end, 0)]; arms['R'] += [(end, 0)]
    root = [(1, (start.x, start.y, yaw)), (t_walk, (0, 0, yaw)), (t + 3, (0, 0, yaw)), (t + 9, (0, 0, mid)),
            (t + 17, (0, 0, -4)), (t + 22, (0, 0, 0)), (end, (0, 0, 0))]
    # Root travels at constant pace while walking.
    root = [(f, (*root_at(f)[:2], yaw)) for f in range(1, t_walk + 1, 2)] + root[2:]
    head = [(1, (0, 0, 0)), (t_walk - 10, (0, 0, 0)), (t - 4, (1, 0, -0.55 * yaw)), (t + 6, (0, 2, -0.35 * yaw)),
            (t + 16, (0, 1, 4)), (t + 22, (0, 0, -1.5)), (end, (0, 0, 0))]
    steps(rig, legs, 'walk_in', end, root=root, feet=feet, shell=shell, arms=arms, head_track=head)


def animations(rig, arms, legs=None):
    """Wave and reach, at 24 fps, stashed as NLA strips so the GLB carries both."""
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    rig.animation_data_create()

    # Wave (left arm): 4 frames of anticipation, 8 to raise, three shrinking arcs, 12 to settle.
    act = new_action(rig, 'wave')
    key_arm(rig, 'L', 1); key_arm(rig, 'R', 1); key_body(rig, 1)
    key_arm(rig, 'L', 5, out=-6, curl=-4)                                 # dip first
    key_arm(rig, 'L', 13, out=128, fwd=20, inward=-6, curl=6, hug=-10, slide=14)    # up beside the head
    key_body(rig, 13, lean_y=-3.5)
    joint(rig, 'head', 1); joint(rig, 'head', 9, y=2); joint(rig, 'head', 15, y=6, x=-2)
    swings = [(-22, 18), (16, 11), (-11, 5), (7, 0)]                      # arc, frames apart; shrinking
    f = 13
    for i, (arc, _) in enumerate(swings):
        f += 7
        key_arm(rig, 'L', f, out=128 + arc, fwd=20, inward=-6, curl=6, hug=-10 - arc * 0.5, slide=14)
    key_arm(rig, 'L', f + 4, out=124, fwd=18, inward=-4, curl=5, hug=-9, slide=12)
    key_body(rig, f + 4, lean_y=-2.5)
    joint(rig, 'head', f, y=5, x=-1); joint(rig, 'head', f + 16, y=-1); joint(rig, 'head', f + 22)
    key_arm(rig, 'L', f + 14, out=-3, curl=-2, slide=-3)                            # overshoot on the way down
    key_arm(rig, 'L', f + 18); key_body(rig, f + 18)
    key_arm(rig, 'R', 4); key_arm(rig, 'R', 16, out=5, fwd=3); key_arm(rig, 'R', f + 6, out=4, fwd=2)
    key_arm(rig, 'R', f + 20)
    act.use_fake_user = True
    trk = rig.animation_data.nla_tracks.new(); trk.name = 'wave'; trk.strips.new('wave', 1, act); trk.mute = True

    # Reach: slide forward, swing and bend toward the target, lean in, flatten on contact, settle, return.
    act = new_action(rig, 'reach')
    for side in 'LR': key_arm(rig, side, 1)
    key_body(rig, 1)
    for side, lag in (('L', 0), ('R', 2)):                              # the arms a beat apart
        key_arm(rig, side, 6 + lag, out=-4, fwd=-8, slide=-6)
        key_arm(rig, side, 18 + lag, out=-4, fwd=50, inward=40, curl=30, hug=32, slide=38)
        key_arm(rig, side, 21 + lag, out=-5, fwd=53, inward=43, curl=33, hug=35, slide=41)   # overshoot
        key_arm(rig, side, 25 + lag, out=-4, fwd=49, inward=40, curl=31, hug=33, slide=38)
        key_arm(rig, side, 44 + lag, out=-4, fwd=49, inward=40, curl=31, hug=33, slide=38)
        key_arm(rig, side, 56 + lag, out=-2, fwd=-3, slide=-4)
        key_arm(rig, side, 62 + lag)
    key_body(rig, 6, lean_x=-2); key_body(rig, 20, lean_x=6, bob=-0.01); key_body(rig, 26, lean_x=4.5)
    key_body(rig, 44, lean_x=4.5); key_body(rig, 58, lean_x=-1); key_body(rig, 64)
    act.use_fake_user = True
    trk = rig.animation_data.nla_tracks.new(); trk.name = 'reach'; trk.strips.new('reach', 1, act); trk.mute = True
    for ob in arms:                                                       # contact squash on the shape key
        sk = ob.data.shape_keys.key_blocks['squash']
        for fr, v in ((1, 0), (21, 0), (25, 0.8), (44, 0.8), (50, 0), (64, 0)):
            sk.value = v; sk.keyframe_insert('value', frame=fr)
    if legs:
        walk(rig, legs); jump(rig, legs); start_stop_turn(rig, legs); idle(rig); walk_in(rig, legs)
    for pb in rig.pose.bones:                         # back to rest once the moves are built
        pb.location = (0, 0, 0); pb.rotation_quaternion = (1, 0, 0, 0); pb.scale = (1, 1, 1)
    for ob in arms + (list(legs.values()) if legs else []):
        if ob.data.shape_keys: ob.data.shape_keys.key_blocks['squash'].value = 0
    rig.animation_data.action = None


def build(pose='front', with_anims=True):
    P = POSES[pose]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = materials()
    body = make_body(); body.data.materials.append(M['plastic'])
    legs = {s: make_leg(s) for s in 'LR'}
    made = {s: make_arm(s) for s in 'LR'}
    arms = {s: m[0] for s, m in made.items()}
    for o in [*legs.values(), *arms.values()]: o.data.materials.append(M['plastic'])
    bpy.context.view_layer.update()

    F = FACE; face = P.get('face', 'smile'); parts = []; feats = []
    zf = lambda s_: ZT - s_ * BODY_H

    def sphere(name, rx, ry, rz, mat, segs=64):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=40, radius=1)
        ob = bpy.context.object; ob.name = name; ob.scale = (rx, ry, rz)
        bpy.ops.object.transform_apply(scale=True)
        for p in ob.data.polygons: p.use_smooth = True
        ob.data.materials.append(mat); parts.append(ob)
        return ob

    def bar(name, pts, r, lift, mat):
        """A graphite bar along a curve on the surface, with round ends, sitting in its groove."""
        cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
        sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
        ends = []; line = []
        for i, (x, s_) in enumerate(pts):
            loc, nor = surface(body, x, s_); q = loc + nor * lift; line.append(tuple(loc))
            sp.points[i].co = (q.x, q.y, q.z, 1)
            if i in (0, len(pts) - 1): ends.append(q)
        cu.bevel_depth = r; cu.bevel_resolution = 8; cu.use_fill_caps = False
        ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
        ob.data.materials.append(mat); parts.append(ob)
        for q in ends:
            e = sphere(name + 'End', r, r, r, mat, segs=32); e.location = q
        feats.append(dict(kind='poly3', pts=line, r=r + 0.0035, depth=0.012, rho=0.003))

    # Expressions. Eyes per side: open (glossy pill in its socket), happy (an upward arc, like a
    # beaming squint), content (a downward arc, eyes softly shut), shut (a straight bar, the blink's end
    # pose). Every closed eye is a round-ended bar exactly as thick as the mouth, set in a matching
    # groove. Mouths: smile, o (small, sipping or musing), shout (a big open oval: cheering, surprise).
    eyes = FACES[face][0]; mouth = FACES[face][1]
    eye_s = F['eye_s']; ew, eh = F['eye_w'], F['eye_h']; R_ = F['smile_r']
    for sx, kind in ((1, eyes[0]), (-1, eyes[1])):            # (his left, his right)
        cx = sx * F['eye_x']
        if kind == 'open':
            D = 0.016
            loc, nor = surface(body, cx, eye_s)
            hb = 2 * R_
            feats.append(dict(kind='slot', frame=frame(loc, nor, spin=math.pi / 2), half=(eh - ew) / 2,
                              r=ew / 2 + 0.0035, depth=D, rho=0.0035,
                              blink=dict(kind='slot', frame=frame(loc, nor), half=(ew - hb) / 2,
                                         r=hb / 2 + 0.0035, depth=D, rho=0.0035)))
            e = eye_mesh(ew, eh, ew * 0.52, R_); e.data.materials.append(M['gloss']); parts.append(e)
            orient(e, loc, nor, lift=-D - 0.003)
        else:
            half_w, rise = ew * 0.62, {'happy': -0.055, 'content': 0.045, 'shut': 0.0}[kind]
            T = 1.15
            pts = [(cx + half_w * math.sin(t) / math.sin(T),
                    eye_s + 0.01 + rise * (math.cos(t) - math.cos(T)) / (1 - math.cos(T))) for t in np.linspace(-T, T, 32)]
            bar('Lid', pts, R_, -0.014, M['gloss'])
    if mouth == 'smile':
        T = 1.2
        pts = [(F['smile_w'] * math.sin(t) / math.sin(T),
                F['smile_bot'] - (F['smile_bot'] - F['smile_end']) * (1 - math.cos(t)) / (1 - math.cos(T))) for t in np.linspace(-T, T, 44)]
        bar('Smile', pts, R_, -0.014, M['gloss'])
    else:
        w_, h_ = (0.074, 0.084) if mouth == 'o' else (0.15, 0.19)
        loc, nor = surface(body, 0, F['smile_end'] + 0.012)
        feats.append(dict(kind='slot', frame=frame(loc, nor, spin=math.pi / 2), half=(h_ - w_) / 2,
                          r=w_ / 2 + 0.0035, depth=0.016 if mouth == 'o' else 0.03, rho=0.0035))
        if mouth == 'o':                                    # a small glossy bead, like the eyes
            m = capsule('Mouth', w_, h_, w_ * 0.6); m.data.materials.append(M['gloss']); parts.append(m)
            orient(m, loc, nor, lift=-0.019)
        else:                                               # a dark recessed opening
            m = capsule('Mouth', w_, h_, 0.012, flat=0.4); m.data.materials.append(M['ink']); parts.append(m)
            orient(m, loc, nor, lift=-0.028)

    led_on = P.get('led', True)
    loc, nor = surface(body, F['led_x'], F['led_s'])
    lr = F['led_r']
    feats.append(dict(kind='circle', frame=frame(loc, nor), r=lr + 0.016, depth=0.03, rho=0.006))
    housing = capsule('LEDHousing', 2 * lr + 0.022, 2 * lr + 0.022, 0.03, segs=64, flat=0.35)
    housing.data.materials.append(M['housing']); orient(housing, loc, nor, lift=-0.03); parts.append(housing)
    lens = sphere('LEDLens', lr, lr, lr * 0.55, M['led' if led_on else 'ledoff'], segs=64)
    orient(lens, loc, nor, lift=-0.022)
    if led_on:
        bpy.ops.object.light_add(type='POINT', radius=0.02)
        gl = bpy.context.object; gl.data.energy = 0.9; gl.data.color = (0.18, 0.7, 0.32)
        gl.location = loc + nor * 0.08; parts.append(gl)

    # The button: a matte pill with a softly bevelled face, standing in a narrow shadow gap.
    loc, nor = surface(body, F['key_x'], F['key_s'])
    half = (F['key_w'] - F['key_h']) / 2
    feats.append(dict(kind='slot', frame=frame(loc, nor), half=half, r=F['key_h'] / 2 + 0.007, depth=0.035, rho=0.003))
    key = capsule('Button', F['key_h'], F['key_w'], 0.09, segs=96, flat=0.32); key.data.materials.append(M['keycap'])
    orient(key, loc, nor, lift=-0.012, spin=math.pi / 2); parts.append(key)

    carve(body, feats)

    # Rig. The body and its parts follow the body bone. Each arm: attach (slides along the shell)
    # > shoulder (swings) > arm_upper > arm_lower (deform, blended weights). Legs on root.
    arm_data = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', arm_data)
    bpy.context.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones
    root = eb.new('root'); root.head = (0, 0, 0); root.tail = (0, 0.4, 0)
    b = eb.new('body'); b.head = (0, 0, Z0 + 0.22); b.tail = (0, 0, ZT); b.parent = root   # pivots low, above the hips
    # Joints in the one-piece shell: the neck sits just above the ribs and carries the dome and face;
    # the hip sits at the bottom of the ribs and carries the base and the leg attachments.
    hd = eb.new('head'); hd.head = (0, 0, ZT - NECK * BODY_H); hd.tail = (0, 0, ZT); hd.parent = b
    hb_ = eb.new('hips'); hb_.head = (0, 0, ZT - HIP * BODY_H); hb_.tail = (0, 0, Z0); hb_.parent = b
    for s_, sx in (('L', 1), ('R', -1)):
        _, pv, d = made[s_]
        at = eb.new(f'attach.{s_}'); at.head = Vector((0, 0, pv.z)); at.tail = Vector((pv.x, pv.y, pv.z)); at.roll = 0
        at.parent = b; at.use_deform = False
        sh = eb.new(f'shoulder.{s_}'); sh.head = pv; sh.tail = pv + d * 0.2; sh.parent = at; sh.use_deform = False
        up = eb.new(f'arm_upper.{s_}'); up.head = pv; up.tail = pv + d * 0.33; up.parent = sh
        lo = eb.new(f'arm_lower.{s_}'); lo.head = pv + d * 0.33; lo.tail = pv + d * ARM['length']; lo.parent = up
        lo.use_connect = True
        hp = Vector((sx * LEG['x'], LEG['y'], Z0 + 0.12))
        ha = eb.new(f'hip_attach.{s_}'); ha.head = hp; ha.tail = hp + Vector((0, 0, 0.15)); ha.parent = hb_; ha.use_deform = False
        hb = eb.new(f'hip.{s_}'); hb.head = hp; hb.tail = Vector((hp.x, hp.y, 0.3)); hb.parent = ha
        fb = eb.new(f'foot.{s_}'); fb.head = Vector((hp.x, hp.y, 0.02)); fb.tail = Vector((hp.x, hp.y - 0.25, 0.02)); fb.parent = root
    bpy.ops.object.mode_set(mode='OBJECT')
    for pb in rig.pose.bones: pb.rotation_mode = 'QUATERNION'
    for s_ in 'LR':
        c = rig.pose.bones[f'hip.{s_}'].constraints.new('DAMPED_TRACK')
        c.target = rig; c.subtarget = f'foot.{s_}'; c.track_axis = 'TRACK_Y'; c.influence = 0.8

    def bind(ob, bone):
        mw = ob.matrix_world.copy()
        ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = bone
        ob.matrix_world = mw
    # The shell deforms with body, head and hips, blended so the ribs stay firm; the face rides the head.
    gb, gh, gp = (body.vertex_groups.new(name=n) for n in ('body', 'head', 'hips'))
    for v in body.data.vertices:
        sh_ = (ZT - v.co.z) / BODY_H
        a = min(1.0, max(0.0, (NECK + 0.07 - sh_) / 0.16)); wh = a * a * (3 - 2 * a)
        c = min(1.0, max(0.0, (sh_ - (HIP - 0.04)) / 0.12)); wp = c * c * (3 - 2 * c)
        wb = max(0.0, 1 - wh - wp)
        gb.add([v.index], wb, 'REPLACE'); gh.add([v.index], wh, 'REPLACE'); gp.add([v.index], wp, 'REPLACE')
    body.parent = rig; body.parent_type = 'OBJECT'
    md = body.modifiers.new('Armature', 'ARMATURE'); md.object = rig
    for o in parts: bind(o, 'head')
    for s_ in 'LR':
        lg = legs[s_]; lg.parent = rig; lg.parent_type = 'OBJECT'
        md = lg.modifiers.new('Armature', 'ARMATURE'); md.object = rig
        ob = arms[s_]; ob.parent = rig; ob.parent_type = 'OBJECT'
        md = ob.modifiers.new('Armature', 'ARMATURE'); md.object = rig

    LIMBS[:] = list(arms.values()) + list(legs.values())
    BODY[:] = [body] if body.data.shape_keys else []
    EYES[:] = [o for o in parts if o.name.startswith('Eye') and not o.name.startswith(('EyeL', 'EyeP'))]
    if with_anims:
        animations(rig, list(arms.values()), legs)
    if 'anim' in P:
        name, fr = P['anim']
        use_move(name)
        bpy.context.scene.frame_set(fr)
    if P.get('sit'):
        # Sit: body down, hips slid forward, each leg swung forward from the hip with its foot carried
        # along (so the stub keeps its shape), feet turned a little outward.
        pb = rig.pose.bones
        bone_loc(pb['body'], (0, 0, -Z0 * 0.86))
        pb['body'].rotation_quaternion = wq(pb['body'], Matrix.Rotation(math.radians(-5), 3, 'X'))   # sits back a touch
        for s_, sx in (('L', 1), ('R', -1)):
            rig.pose.bones[f'hip.{s_}'].constraints[0].mute = True
            bone_loc(pb[f'hip_attach.{s_}'], (0, -0.08, 0))
            pb[f'hip.{s_}'].rotation_quaternion = wq(pb[f'hip.{s_}'],
                Matrix.Rotation(math.radians(sx * 14), 3, 'Z') @ Matrix.Rotation(math.radians(-78), 3, 'X'))
        bpy.context.view_layer.update()
        for s_ in 'LR':
            h, f_ = pb[f'hip.{s_}'], pb[f'foot.{s_}']
            D = h.matrix @ h.bone.matrix_local.inverted()
            f_.matrix = D @ f_.bone.matrix_local
            bpy.context.view_layer.update()
    if 'tilt' in P:
        pb = rig.pose.bones['body']
        pb.rotation_quaternion = wq(pb, Matrix.Rotation(math.radians(P['tilt'][0]), 3, 'X'))
    if P.get('ball'):
        bpy.context.view_layer.update()
        tips = [rig.matrix_world @ rig.pose.bones[f'arm_lower.{s_}'].tail for s_ in 'LR']
        c = (tips[0] + tips[1]) / 2 + Vector((0, -0.12, 0.04))
        ball = sphere('Ball', 0.32, 0.32, 0.32, M['ball']); ball.location = c
    bpy.context.view_layer.update()
    return rig


def uv_unwrap():
    for ob in bpy.data.objects:
        if ob.type != 'MESH': continue
        bpy.context.view_layer.objects.active = ob; ob.select_set(True)
        bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.uv.smart_project(angle_limit=math.radians(66), island_margin=0.01)
        bpy.ops.object.mode_set(mode='OBJECT'); ob.select_set(False)


def stage(yaw, elev=8.0, size=700, samples=48, dark=True, lens=100, dist=13.0, target=None):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'
    sc.cycles.samples = samples; sc.cycles.use_denoising = True
    sc.render.resolution_x = size; sc.render.resolution_y = size
    sc.render.film_transparent = True
    sc.view_settings.view_transform = 'Khronos PBR Neutral'
    sc.view_settings.exposure = EXPO
    world = bpy.data.worlds.new('W'); sc.world = world
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.05, 0.05, 0.055, 1) if dark else (0.9, 0.88, 0.85, 1)
    bg.inputs['Strength'].default_value = 1.0 if dark else 0.35

    def area(name, loc, energy, size, color=(1, 0.97, 0.93), aim=(0, 0, 1.3)):
        bpy.ops.object.light_add(type='AREA', location=loc)
        L = bpy.context.object; L.name = name; L.data.energy = energy; L.data.size = size; L.data.color = color
        L.rotation_euler = (Vector(aim) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    area('Key', (-3.4, -4.6, 6.0), 1300, 7.0)
    area('Fill', (5.0, -3.5, 2.5), 90, 6.0, (0.95, 0.97, 1.0))
    area('Rim', (3.5, 5.0, 4.0), 700, 4.0)
    area('Rim2', (-4.0, 4.0, 3.0), 400, 4.0)
    area('Top', (0, 0, 8), 150, 6.0)
    # The eye light: small, just above the camera's left, so each eye catches a dot in its upper-left.
    e = math.radians(elev); tz = target if target is not None else ZT * 0.5 + 0.05
    area('EyeLight', (-1.1, -4.6, ZT - 0.33 * BODY_H + 2.4), 70, 0.12, (1, 1, 1), aim=(0, -1, ZT - 0.33 * BODY_H))
    bpy.data.objects['EyeLight'].data.shape = 'DISK'

    bpy.ops.mesh.primitive_plane_add(size=60)
    gp = bpy.context.object
    gp.is_shadow_catcher = True

    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('C')); cam.data.lens = lens
    sc.collection.objects.link(cam); sc.camera = cam
    e = math.radians(elev); target = Vector((0, 0, target if target is not None else ZT * 0.5 + 0.05))
    cam.location = target + Vector((0, -dist * math.cos(e), dist * math.sin(e)))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    rig = bpy.data.objects['Rig']; rig.rotation_euler = (0, 0, math.radians(yaw))


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--frame', type=int); ap.add_argument('--anim'); ap.add_argument('--step', type=int, default=1); ap.add_argument('--first', type=int, default=1); ap.add_argument('--follow', action='store_true'); ap.add_argument('--last', type=int, default=0);
    ap.add_argument('--pose', default='front'); ap.add_argument('--view', type=float, default=0)
    ap.add_argument('--elev', type=float, default=3); ap.add_argument('--lens', type=float, default=100)
    ap.add_argument('--dist', type=float, default=13); ap.add_argument('--size', type=int, default=700)
    ap.add_argument('--samples', type=int, default=48); ap.add_argument('--light', action='store_true')
    ap.add_argument('--target', type=float); ap.add_argument('--out'); ap.add_argument('--export'); ap.add_argument('--expo', type=float, default=EXPO)
    a = ap.parse_args(argv)
    EXPO = a.expo
    build(a.pose)
    if a.export:
        uv_unwrap()
        bpy.ops.wm.save_as_mainfile(filepath=a.export.replace('.glb', '.blend'))
        bpy.ops.export_scene.gltf(filepath=a.export, export_format='GLB', export_apply=False, export_lights=False,
                                  export_animations=True, export_animation_mode='NLA_TRACKS', export_morph=True)
    if a.out:
        stage(a.view, a.elev, a.size, a.samples, dark=not a.light, lens=a.lens, dist=a.dist, target=a.target)
        sc = bpy.context.scene; rig = bpy.data.objects['Rig']
        if a.anim:   # render frames of an animation: --anim wave --frame N (one) or all, every 2nd
            use_move(a.anim)
            end = a.last or int(rig.animation_data.action.frame_range[1])
            fr = [a.frame] if a.frame else range(a.first, end + 1, a.step)
            offsets = {}
            if a.follow:
                # Keep him centred in every frame (the camera's lens shift), relative to where he
                # stands at the end, and record how far the frame moved, so a player can draw each
                # frame at his real place on screen. The shift is the same as cropping a bigger shot.
                from bpy_extras.object_utils import world_to_camera_view
                import json
                def at(f_):
                    sc.frame_set(f_); bpy.context.view_layer.update()
                    p_ = rig.matrix_world @ rig.pose.bones['body'].head
                    return world_to_camera_view(sc, sc.camera, p_)
                end_uv = at(int(rig.animation_data.action.frame_range[1]))
            for f_ in fr:
                if a.follow:
                    sc.camera.data.shift_x = 0; sc.camera.data.shift_y = 0
                    uv = at(f_)
                    dx, dy = uv.x - end_uv.x, uv.y - end_uv.y
                    sc.camera.data.shift_x = dx; sc.camera.data.shift_y = dy
                    offsets[f_] = (dx, -dy)                     # in frame widths; y down, like a page
                sc.frame_set(f_); sc.render.filepath = a.out.replace('#', f'{f_:03d}')
                bpy.ops.render.render(write_still=True)
            if a.follow:
                import os, json
                path = os.path.join(os.path.dirname(a.out), 'offsets.json')
                old = json.load(open(path)) if os.path.exists(path) else {}
                old.update({str(k): v for k, v in offsets.items()}); json.dump(old, open(path, 'w'))
        else:
            sc.render.filepath = a.out
            bpy.ops.render.render(write_still=True)

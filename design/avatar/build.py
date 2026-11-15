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
DEPTH = 0.97                 # body depth / width
LEG_H = 16 / PX              # visible leg below the body
BODY_H = 125 / PX
Z0 = LEG_H
ZT = Z0 + BODY_H

# Half-width of the body, s sheet-pixels down from the top (back and side views).
PROFILE = [(0, 0.0), (1, 0.12), (3, 0.34), (6, 0.47), (9, 0.55), (12, 0.62), (15, 0.68), (18, 0.73),
           (21, 0.775), (24, 0.815), (27, 0.85), (30, 0.88), (33, 0.905), (36, 0.925), (39, 0.943),
           (42, 0.958), (48, 0.978), (54, 0.99), (62, 1.0), (78, 1.0), (86, 0.995), (94, 0.978),
           (100, 0.955), (105, 0.93), (110, 0.9), (114, 0.865), (117, 0.825), (120, 0.76), (122.5, 0.67),
           (124.2, 0.57), (125, 0.44)]
GROOVES = [92.5, 101.8, 110.8]

FACE = dict(eye_x=0.36, eye_s=0.335, eye_w=0.155, eye_h=0.255,
            smile_w=0.125, smile_end=0.392, smile_bot=0.424, smile_r=0.024,
            led_x=0.0, led_s=0.615, led_r=0.072,
            key_x=0.4, key_s=0.615, key_w=0.42, key_h=0.17)
ARM = dict(x=0.95, y=-0.12, s=0.725, rx=0.34, ry=0.35, rz=0.38)
LEG = dict(x=0.42, y=-0.06, r=0.33, ry=0.37)


def pchip(xs, ys, x):
    from scipy.interpolate import PchipInterpolator
    return float(PchipInterpolator(xs, ys)(x))


def half_width(s):
    """Half-width s sheet-pixels down from the top: a superellipse dome (round shoulders),
    straight sides, and a rounded base like a moulded part, not an egg."""
    s = min(max(s, 0), 125)
    DOME, BASE, R = 60.0, 109.0, 0.3      # dome height (px), where the base fillet starts, fillet radius (W)
    if s < DOME:
        t = (DOME - s) / DOME
        r = (1 - t ** 2.1) ** (1 / 2.1)
    elif s < BASE:
        r = 1.0
    else:
        t = min(1.0, (s - BASE) / (125 - BASE))
        r = (1 - R) + R * math.sqrt(max(0.0, 1 - t * t))
    for g in GROOVES:
        d = s - g
        r -= 0.028 * math.exp(-(d / 0.6) ** 2) + 0.004 * math.exp(-(d / 2.0) ** 2)
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
                    + list(np.arange(82, 125, 0.55))))
    for s in ss:
        rings.append((ZT - s / PX, half_width(s)))
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
    the floor is flat and the lip is a soft S-curve, like a moulded part."""
    me = body.data
    n = len(me.vertices)
    co = np.empty(n * 3); me.vertices.foreach_get('co', co); co = co.reshape(n, 3)
    nor = np.empty(n * 3); me.vertices.foreach_get('normal', nor); nor = nor.reshape(n, 3)
    x, z = co[:, 0], co[:, 2]
    disp = np.zeros(n)
    front = co[:, 1] < -0.2
    for f in feats:
        if f['kind'] == 'ellipse':
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
        rho = f.get('rho', 0.018)
        dd = -f['depth'] * (1 - smoothstep(-rho, rho, sdf))
        disp = np.where(front, np.minimum(disp, dd), disp)
    co += nor * disp[:, None]
    me.vertices.foreach_set('co', co.ravel()); me.update()


def make_leg(side):
    R, c = LEG['r'], 0.55          # radius, corner rounding as a share of the radius
    top = Z0 + 0.45
    rings = [(top - 0.6 * k / 20, R) for k in range(0, 20)]
    zc = R * c
    for k in range(1, 24):
        t = k / 23 * math.pi / 2
        rings.append((zc - zc * math.sin(t), R * ((1 - c) + c * math.cos(t))))
    ob = lathe(f'Leg.{side}', rings, segs=64, sy=LEG['ry'] / R)
    ob.location = (LEG['x'] * (1 if side == 'L' else -1), LEG['y'], 0)
    return ob


def make_arm(side):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=40, radius=1)
    ob = bpy.context.object; ob.name = f'Arm.{side}'
    for v in ob.data.vertices:
        k = 1 - 0.06 * v.co.z          # a touch narrower at the top
        v.co = Vector((v.co.x * ARM['rx'] * k, v.co.y * ARM['ry'] * k, v.co.z * ARM['rz']))
    for p in ob.data.polygons: p.use_smooth = True
    sx = 1 if side == 'L' else -1
    ob.location = (sx * ARM['x'], ARM['y'], ZT - ARM['s'] * BODY_H)
    return ob


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
    gloss, _ = mat('Gloss', (0.012, 0.012, 0.014), 0.32, **{'Coat Weight': 0.6, 'Coat Roughness': 0.14, 'Specular IOR Level': 0.4})
    ink, _ = mat('Ink', (0.006, 0.006, 0.007), 0.5)
    led, _ = mat('LED', (0.028, 0.451, 0.084), 0.08, **{'Emission Color': (0.028, 0.451, 0.084, 1), 'Emission Strength': 3.5,
                                                       'Coat Weight': 1.0, 'Coat Roughness': 0.05})
    ledoff, _ = mat('LEDOff', (0.53, 0.53, 0.52), 0.12, **{'Coat Weight': 1.0, 'Coat Roughness': 0.05})
    keycap, _ = mat('Keycap', (0.61, 0.59, 0.56), 0.58, **{'Sheen Weight': 0.25, 'Sheen Roughness': 0.5})
    slot, _ = mat('Slot', (0.30, 0.28, 0.26), 0.6)
    shine, _ = mat('Shine', (1, 1, 1), 0.3, **{'Emission Color': (1, 1, 1, 1), 'Emission Strength': 0.6})
    pocket, _ = mat('Pocket', (0.36, 0.34, 0.32), 0.6)
    housing, _ = mat('Housing', (0.42, 0.4, 0.38), 0.55)
    return dict(housing=housing, pocket=pocket, shine=shine, plastic=plastic, gloss=gloss, ink=ink, led=led, ledoff=ledoff, keycap=keycap, slot=slot)


POSES = {
    # bone rotations in degrees (x, y, z); face: smile | closed | o ; led on/off
    'front': {},
    'wave': {'arm.L': (0, -150, 0)},
    'cheer': {'arm.L': (0, -140, 0), 'arm.R': (0, 140, 0), 'face': 'closed'},
    'sleep': {'body': (8, 0, 0), 'face': 'closed', 'led': False},
    'surprised': {'body': (-5, 0, 0), 'face': 'o'},
}


def build(pose='front'):
    P = POSES[pose]
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = materials()
    body = make_body(); body.data.materials.append(M['plastic'])
    legs = {s: make_leg(s) for s in 'LR'}
    arms = {s: make_arm(s) for s in 'LR'}
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
        ends = []
        for i, (x, s_) in enumerate(pts):
            loc, nor = surface(body, x, s_); q = loc + nor * lift
            sp.points[i].co = (q.x, q.y, q.z, 1)
            if i in (0, len(pts) - 1): ends.append(q)
        cu.bevel_depth = r; cu.bevel_resolution = 8; cu.use_fill_caps = False
        ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
        ob.data.materials.append(mat); parts.append(ob)
        for q in ends:
            e = sphere(name + 'End', r, r, r, mat, segs=32); e.location = q
        feats.append(dict(kind='poly', pts=[(x, zf(s_)) for x, s_ in pts], r=r + 0.011, depth=0.02, rho=0.008))

    eye_s = F['eye_s'] - (0.02 if face == 'o' else 0)
    if face == 'closed':
        for sx in (-1, 1):
            T = 1.1
            pts = [(sx * F['eye_x'] + 0.085 * math.sin(t) / math.sin(T),
                    eye_s + 0.02 + 0.045 * (math.cos(t) - math.cos(T)) / (1 - math.cos(T))) for t in np.linspace(-T, T, 28)]
            bar('Lid', pts, 0.02, -0.02, M['gloss'])
    else:
        big = 1.12 if face == 'o' else 1.0
        ew, eh = F['eye_w'] * big, F['eye_h'] * big
        for sx in (-1, 1):
            # A pocket a little larger than the eye; the eye is a shallow convex lens inside it.
            feats.append(dict(kind='ellipse', cx=sx * F['eye_x'], cz=zf(eye_s), a=ew / 2 + 0.011, b=eh / 2 + 0.011, depth=0.022, rho=0.008))
            e = sphere('Eye', ew / 2, eh / 2, 0.03, M['gloss'])
            orient(e, *surface(body, sx * F['eye_x'], eye_s), lift=-0.034)
    if face == 'smile':
        T = 1.2
        pts = [(F['smile_w'] * math.sin(t) / math.sin(T),
                F['smile_bot'] - (F['smile_bot'] - F['smile_end']) * (1 - math.cos(t)) / (1 - math.cos(T))) for t in np.linspace(-T, T, 44)]
        bar('Smile', pts, F['smile_r'], -0.022, M['gloss'])
    elif face == 'o':
        feats.append(dict(kind='circle', cx=0, cz=zf(0.365), r=0.055, depth=0.04))
        m = sphere('Mouth', 0.035, 0.045, 0.03, M['gloss']); orient(m, *surface(body, 0, 0.365), lift=-0.035)

    led_on = P.get('led', True)
    loc, nor = surface(body, F['led_x'], F['led_s'])
    lr = F['led_r']
    feats.append(dict(kind='circle', cx=F['led_x'], cz=zf(F['led_s']), r=lr + 0.016, depth=0.03, rho=0.006))
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
    feats.append(dict(kind='poly', pts=[(F['key_x'] - half, zf(F['key_s'])), (F['key_x'] + half, zf(F['key_s']))],
                      r=F['key_h'] / 2 + 0.007, depth=0.035, rho=0.003))
    key = capsule('Button', F['key_h'], F['key_w'], 0.09, segs=96, flat=0.32); key.data.materials.append(M['keycap'])
    orient(key, loc, nor, lift=-0.012, spin=math.pi / 2); parts.append(key)

    carve(body, feats)

    # Rig: bind every part rigidly to a bone.
    arm_data = bpy.data.armatures.new('Rig'); rig = bpy.data.objects.new('Rig', arm_data)
    bpy.context.collection.objects.link(rig); bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode='EDIT')
    eb = arm_data.edit_bones
    root = eb.new('root'); root.head = (0, 0, 0); root.tail = (0, 0.4, 0)
    b = eb.new('body'); b.head = (0, 0, Z0); b.tail = (0, 0, ZT); b.parent = root
    for s, sx in (('L', 1), ('R', -1)):
        a = eb.new(f'arm.{s}'); a.head = (sx * (ARM['x'] - 0.12), ARM['y'], ZT - ARM['s'] * BODY_H + 0.15)
        a.tail = (sx * ARM['x'], ARM['y'], ZT - ARM['s'] * BODY_H - 0.2); a.parent = b
        l = eb.new(f'leg.{s}'); l.head = (sx * LEG['x'], LEG['y'], Z0 + 0.2); l.tail = (sx * LEG['x'], LEG['y'], 0); l.parent = root
    bpy.ops.object.mode_set(mode='OBJECT')

    def bind(ob, bone):
        mw = ob.matrix_world.copy()
        ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = bone
        ob.matrix_world = mw
    bind(body, 'body')
    for o in parts: bind(o, 'body')
    for s in 'LR':
        bind(arms[s], f'arm.{s}'); bind(legs[s], f'leg.{s}')

    for bone, rot in P.items():
        if bone in rig.pose.bones:
            pb = rig.pose.bones[bone]; pb.rotation_mode = 'XYZ'
            pb.rotation_euler = tuple(math.radians(v) for v in rot)
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

    def area(name, loc, energy, size, color=(1, 0.97, 0.93)):
        bpy.ops.object.light_add(type='AREA', location=loc)
        L = bpy.context.object; L.name = name; L.data.energy = energy; L.data.size = size; L.data.color = color
        L.rotation_euler = (Vector((0, 0, 1.3)) - Vector(loc)).to_track_quat('-Z', 'Y').to_euler()
    area('Key', (-3.4, -4.6, 6.0), 1300, 7.0)
    area('Fill', (5.0, -3.5, 2.5), 90, 6.0, (0.95, 0.97, 1.0))
    area('Rim', (3.5, 5.0, 4.0), 700, 4.0)
    area('Rim2', (-4.0, 4.0, 3.0), 400, 4.0)
    area('Top', (0, 0, 8), 150, 6.0)

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
        bpy.ops.export_scene.gltf(filepath=a.export, export_format='GLB', export_apply=True, export_lights=False)
    if a.out:
        stage(a.view, a.elev, a.size, a.samples, dark=not a.light, lens=a.lens, dist=a.dist, target=a.target)
        bpy.context.scene.render.filepath = a.out
        bpy.ops.render.render(write_still=True)

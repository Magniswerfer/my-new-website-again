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

FACE = dict(eye_x=0.33, eye_s=0.283, eye_w=0.175, eye_h=0.29,
            smile_w=0.15, smile_end=0.335, smile_bot=0.375, smile_r=0.033,
            led_x=0.0, led_s=0.563, led_r=0.085,
            key_x=0.42, key_s=0.563, key_w=0.46, key_h=0.2)
ARM = dict(x=0.95, y=-0.12, s=0.725, rx=0.34, ry=0.35, rz=0.38)
LEG = dict(x=0.42, y=-0.06, r=0.33, ry=0.37)


def pchip(xs, ys, x):
    from scipy.interpolate import PchipInterpolator
    return float(PchipInterpolator(xs, ys)(x))


def half_width(s):
    xs, ys = zip(*PROFILE)
    r = pchip(xs, ys, min(max(s, 0), 125))
    # The dome: the measured rows fit r = 0.215 * s^0.413 closely; use the fit for a smooth top.
    if s < 34:
        fit = 0.215 * max(s, 0) ** 0.413
        w = min(1.0, max(0.0, (34 - s) / 8))
        r = fit * w + r * (1 - w)
    for g in GROOVES:
        d = s - g
        r -= 0.042 * math.exp(-(d / 0.75) ** 2) + 0.01 * math.exp(-(d / 2.4) ** 2)
    return r


def lathe(name, rings, segs=128, sy=1.0):
    """rings: (z, r) from top to bottom. Quads all round; the poles close with fans."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    grid = []
    for z, r in rings:
        grid.append([bm.verts.new((r * math.cos(2 * math.pi * i / segs), r * math.sin(2 * math.pi * i / segs) * sy, z))
                     for i in range(segs)])
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
    ss = sorted(set([0.15 * k for k in range(1, 30)] + list(np.arange(4.5, 125, 0.55))))
    for s in ss:
        rings.append((ZT - s / PX, half_width(s)))
    rb = rings[-1][1]
    for t in (0.5, 0.75, 0.9):
        rings.append((Z0 - 0.002 * t, rb * (1 - t)))
    return lathe('Body', rings, segs=160, sy=DEPTH)


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


def capsule(name, w, h, d, segs=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=32, radius=1)
    ob = bpy.context.object; ob.name = name
    half = max(0.0, (h - w) / 2)
    for v in ob.data.vertices:
        x, y, z = v.co
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
    plastic, p = mat('Plastic', (0.585, 0.54, 0.515), 0.55, **{'Subsurface Weight': 0.1, 'Subsurface Scale': 0.05,
                                                              'Specular IOR Level': 0.35})
    nt = plastic.node_tree   # soft-touch: a faint noise bump
    tex = nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = 160; tex.inputs['Detail'].default_value = 4
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.03; bump.inputs['Distance'].default_value = 0.002
    nt.links.new(tex.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    gloss, _ = mat('Gloss', (0.003, 0.003, 0.004), 0.5, **{'Coat Weight': 0.35, 'Coat Roughness': 0.22, 'Specular IOR Level': 0.0})
    ink, _ = mat('Ink', (0.006, 0.006, 0.007), 0.5)
    led, _ = mat('LED', (0.2, 0.9, 0.05), 0.15, **{'Emission Color': (0.3, 1.0, 0.0, 1), 'Emission Strength': 4.0})
    ledoff, _ = mat('LEDOff', (0.32, 0.33, 0.31), 0.3)
    keycap, _ = mat('Keycap', (0.86, 0.83, 0.79), 0.4, **{'Coat Weight': 0.25})
    slot, _ = mat('Slot', (0.30, 0.28, 0.26), 0.6)
    shine, _ = mat('Shine', (1, 1, 1), 0.3, **{'Emission Color': (1, 1, 1, 1), 'Emission Strength': 0.6})
    pocket, _ = mat('Pocket', (0.36, 0.34, 0.32), 0.6)
    return dict(pocket=pocket, shine=shine, plastic=plastic, gloss=gloss, ink=ink, led=led, ledoff=ledoff, keycap=keycap, slot=slot)


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

    F = FACE; face = P.get('face', 'smile'); parts = []
    if face == 'closed':
        for sx in (-1, 1):
            T = 1.1
            pts = [(sx * F['eye_x'] + 0.085 * math.sin(t) / math.sin(T),
                    F['eye_s'] + 0.02 + 0.045 * (math.cos(t) - math.cos(T)) / (1 - math.cos(T))) for t in np.linspace(-T, T, 28)]
            parts.append(curve_on(body, 'Lid', pts, 0.02, M['ink']))
    else:
        big = 1.12 if face == 'o' else 1.0
        for sx in (-1, 1):
            e = capsule('Eye', F['eye_w'] * big, F['eye_h'] * big, 0.07); e.data.materials.append(M['gloss'])
            orient(e, *surface(body, sx * F['eye_x'], F['eye_s'] - (0.02 if face == 'o' else 0)), lift=-0.014)
            parts.append(e)
            pk = capsule('EyePocket', F['eye_w'] * big + 0.022, F['eye_h'] * big + 0.022, 0.05); pk.data.materials.append(M['pocket'])
            orient(pk, *surface(body, sx * F['eye_x'], F['eye_s'] - (0.02 if face == 'o' else 0)), lift=-0.016)
            parts.append(pk)
            hl = capsule('EyeLight', 0.035 * big, 0.055 * big, 0.02); hl.data.materials.append(M['shine'])
            orient(hl, *surface(body, sx * F['eye_x'] - 0.022, F['eye_s'] - 0.04 - (0.02 if face == 'o' else 0)), lift=0.019)
            parts.append(hl)
    if face == 'smile':
        T = 1.2
        pts = [(F['smile_w'] * math.sin(t) / math.sin(T),
                F['smile_bot'] - (F['smile_bot'] - F['smile_end']) * (1 - math.cos(t)) / (1 - math.cos(T))) for t in np.linspace(-T, T, 44)]
        parts.append(curve_on(body, 'Smile', pts, F['smile_r'], M['ink']))
    elif face == 'o':
        m = capsule('Mouth', 0.07, 0.09, 0.05); m.data.materials.append(M['gloss'])
        orient(m, *surface(body, 0, 0.365), lift=-0.01); parts.append(m)

    led_on = P.get('led', True)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=F['led_r'])
    led = bpy.context.object; led.name = 'LED'
    for p in led.data.polygons: p.use_smooth = True
    led.data.materials.append(M['led' if led_on else 'ledoff'])
    loc, nor = surface(body, F['led_x'], F['led_s'])
    orient(led, loc, nor, lift=-0.022); parts.append(led)
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=F['led_r'] * 1.3)
    ring = bpy.context.object; ring.name = 'LEDRing'; ring.data.materials.append(M['slot'])
    for p in ring.data.polygons: p.use_smooth = True
    orient(ring, loc, nor, lift=-0.026); ring.scale = (1, 1, 0.35); parts.append(ring)
    if led_on:
        bpy.ops.object.light_add(type='POINT', radius=0.03)
        gl = bpy.context.object; gl.data.energy = 1.2; gl.data.color = (0.4, 1.0, 0.2)
        gl.location = loc + nor * 0.12; parts.append(gl)

    loc, nor = surface(body, F['key_x'], F['key_s'])
    key = capsule('Key', F['key_h'], F['key_w'], 0.13, segs=64); key.data.materials.append(M['keycap'])
    orient(key, loc, nor, lift=0.025, spin=math.pi / 2); parts.append(key)
    slot = capsule('Slot', F['key_h'] + 0.04, F['key_w'] + 0.045, 0.06, segs=64); slot.data.materials.append(M['slot'])
    orient(slot, loc, nor, lift=-0.012, spin=math.pi / 2); parts.append(slot)

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


def stage(yaw, elev=8.0, size=700, samples=48, dark=True, lens=100, dist=13.0):
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
    area('Key', (-3.4, -4.6, 6.0), 1300, 4.0)
    area('Fill', (5.0, -3.5, 2.5), 90, 6.0, (0.95, 0.97, 1.0))
    area('Rim', (3.5, 5.0, 4.0), 700, 4.0)
    area('Rim2', (-4.0, 4.0, 3.0), 400, 4.0)
    area('Top', (0, 0, 8), 150, 6.0)

    bpy.ops.mesh.primitive_plane_add(size=60)
    gp = bpy.context.object
    gp.is_shadow_catcher = True

    cam = bpy.data.objects.new('Cam', bpy.data.cameras.new('C')); cam.data.lens = lens
    sc.collection.objects.link(cam); sc.camera = cam
    e = math.radians(elev); target = Vector((0, 0, (ZT) * 0.5 + 0.05))
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
    ap.add_argument('--out'); ap.add_argument('--export'); ap.add_argument('--expo', type=float, default=EXPO)
    a = ap.parse_args(argv)
    EXPO = a.expo
    build(a.pose)
    if a.export:
        uv_unwrap()
        bpy.ops.wm.save_as_mainfile(filepath=a.export.replace('.glb', '.blend'))
        bpy.ops.export_scene.gltf(filepath=a.export, export_format='GLB', export_apply=True, export_lights=False)
    if a.out:
        stage(a.view, a.elev, a.size, a.samples, dark=not a.light, lens=a.lens, dist=a.dist)
        bpy.context.scene.render.filepath = a.out
        bpy.ops.render.render(write_still=True)

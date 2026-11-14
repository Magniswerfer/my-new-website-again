"""
Builds the site character in Blender and renders him with Cycles.

  python3 design/avatar/build.py --view front --out out.png [--size 600] [--samples 64] [--pose wave]

Measurements are taken from the reference sheet (design/avatar/reference.png), in units of
the body's half-width (1.0). The body is a turned profile; depth is 0.885 of width.
Front faces -Y; Z is up; the ground is z = 0.
"""
import bpy, bmesh, math, sys, argparse
import numpy as np
from mathutils import Vector, Matrix, Euler

PX = 111.0                  # reference pixels per unit (half-width of the body)
VT, EXPO, WORLD, KEYE = 'Khronos PBR Neutral', -0.3, 0.25, 700
BASE = (0.78, 0.74, 0.70, 1)
DEPTH = 0.885               # front-to-back / side-to-side
LEG_H = 0.43                # visible leg height below the body
BODY_H = 266 / PX           # body height
Z0 = LEG_H                  # body bottom
ZT = Z0 + BODY_H            # body top

# Half-width of the body, s pixels down from the top (read off the back and side views).
PROFILE = [(0, 0), (1.2, 0.14), (4, 0.25), (10, 0.43), (16, 0.545), (22, 0.63), (28, 0.69), (34, 0.74),
           (40, 0.785), (46, 0.82), (52, 0.85), (58, 0.875), (64, 0.897), (70, 0.915), (76, 0.932), (88, 0.952),
           (100, 0.963), (112, 0.976), (130, 0.99), (160, 1.0), (205, 1.0), (214, 0.995), (220, 0.982),
           (226, 0.962), (232, 0.94), (238, 0.91), (244, 0.875), (250, 0.83), (255, 0.77), (259, 0.70),
           (262, 0.63), (264.5, 0.56), (266, 0.47)]
GROOVES = [199, 218, 237]   # px from the top


def pchip(xs, ys, x):
    from scipy.interpolate import PchipInterpolator
    return PchipInterpolator(xs, ys)(x)


def body_radius_px(s):
    xs, ys = zip(*PROFILE)
    r = float(pchip(xs, ys, min(max(s, 0), 266)))
    for g in GROOVES:
        d = s - g
        r -= 0.04 * math.exp(-(d / 0.95) ** 2) + 0.007 * math.exp(-(d / 3.2) ** 2)
    return r


def lathe(name, rings, segs=160, sy=1.0):
    """rings: list of (z, r) from top to bottom; closes both ends with poles."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    grid = []
    for z, r in rings:
        row = []
        for i in range(segs):
            a = 2 * math.pi * i / segs
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a) * sy, z)))
        grid.append(row)
    for j in range(len(grid) - 1):
        for i in range(segs):
            a, b = grid[j][i], grid[j][(i + 1) % segs]
            c, d = grid[j + 1][(i + 1) % segs], grid[j + 1][i]
            bm.faces.new((a, d, c, b))
    top = bm.verts.new((0, 0, rings[0][0])); bot = bm.verts.new((0, 0, rings[-1][0]))
    for i in range(segs):
        bm.faces.new((top, grid[0][i], grid[0][(i + 1) % segs]))
        bm.faces.new((bot, grid[-1][(i + 1) % segs], grid[-1][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me); bm.free()
    ob = bpy.data.objects.new(name, me)
    bpy.context.collection.objects.link(ob)
    for p in me.polygons: p.use_smooth = True
    return ob


def body():
    rings = []
    n = 520
    for k in range(1, n):
        s = 266 * (k / n) ** 1.0
        rings.append((ZT - s / PX, body_radius_px(s)))
    # Flat underside with a small fillet.
    zb = Z0
    rb = rings[-1][1]
    for t in np.linspace(0.15, 1, 6):
        rings.append((zb - 0.004 * t, rb * (1 - t) + 0.0 * t + 0.0))
    # make first ring tiny near top pole for smoothness
    return lathe('Body', rings, segs=192, sy=DEPTH)


def leg(x):
    R, RY, H = 0.32, 0.35, 0.75
    rings = []
    for k in range(0, 40):
        z = LEG_H + 0.32 - (LEG_H + 0.32) * k / 39 * 0.72
        rings.append((z, 1.0))
    # Rounded foot: superellipse corner.
    c = 0.62
    for k in range(1, 30):
        t = k / 29 * (math.pi / 2)
        rr = (1 - c) + c * math.cos(t)
        z = rings[-1][0] if k == 1 else None
        rings.append((None, rr, t))
    zc = (LEG_H + 0.32) * (1 - 0.72)  # height where the corner starts
    out = []
    for item in rings:
        if len(item) == 2: out.append((item[0], R * item[1]))
        else:
            _, rr, t = item
            out.append((zc - zc * math.sin(t), R * rr))
    out[-1] = (0.0, R * (1 - c) * 0.6)
    ob = lathe('Leg', out, segs=96, sy=RY / R)
    ob.location.x = x
    return ob


def arm(side, place=None):
    """An egg: narrower at the top, tilted out at the bottom."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=1)
    ob = bpy.context.object; ob.name = f'Arm{side}'
    me = ob.data
    for v in me.vertices:
        z = v.co.z
        k = 1 - 0.13 * z          # egg taper: top narrower
        v.co.x *= 0.23 * k; v.co.y *= 0.305 * k; v.co.z *= 0.385
    for p in me.polygons: p.use_smooth = True
    if place:
        loc, rot = place
        ob.location = (side * loc[0], loc[1], ZT - loc[2])
        ob.rotation_euler = tuple(math.radians(r) * (side if i > 0 else 1) for i, r in enumerate(rot))
    else:
        ob.location = (side * 1.07, -0.2, ZT - 180 / PX)
        ob.rotation_euler = (0, side * math.radians(-14), side * math.radians(-8))
    return ob


def surface_point(body_ob, x, z):
    """Where a ray along +Y at (x, z) meets the front of the body, and the normal there."""
    deps = bpy.context.evaluated_depsgraph_get()
    hit, loc, nor, *_ = body_ob.ray_cast(Vector((x, -5, z)), Vector((0, 1, 0)), depsgraph=deps)
    assert hit, (x, z)
    return loc, nor


def orient(ob, nor):
    # local +Z along the normal, local +Y stays as up as possible
    zax = nor.normalized()
    up = Vector((0, 0, 1))
    xax = up.cross(zax).normalized()
    yax = zax.cross(xax)
    ob.matrix_world = Matrix((xax, yax, zax)).transposed().to_4x4() @ Matrix.Identity(4)


def capsule(name, w, h, d, segs=48):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segs, ring_count=32, radius=1)
    ob = bpy.context.object; ob.name = name
    me = ob.data
    half = (h - w) / 2
    for v in me.vertices:
        x, y, z = v.co
        v.co = Vector((x * w / 2, y * w / 2 + (half if y > 0 else -half if y < 0 else 0), z * d / 2))
    for p in me.polygons: p.use_smooth = True
    return ob


def place(ob, body_ob, x, z, sink=0.0):
    loc, nor = surface_point(body_ob, x, z)
    m = ob.matrix_world.copy()
    orient(ob, nor)
    ob.location = loc + nor * sink
    return loc, nor


def materials():
    def mat(name):
        m = bpy.data.materials.new(name); m.use_nodes = True
        return m, m.node_tree.nodes['Principled BSDF']
    plastic, p = mat('Plastic')
    p.inputs['Base Color'].default_value = BASE
    p.inputs['Roughness'].default_value = 0.52
    p.inputs['Subsurface Weight'].default_value = 0.12
    p.inputs['Subsurface Radius'].default_value = (0.3, 0.2, 0.15)
    p.inputs['Subsurface Scale'].default_value = 0.08
    p.inputs['Specular IOR Level'].default_value = 0.35
    gloss, g = mat('Gloss')
    g.inputs['Base Color'].default_value = (0.008, 0.008, 0.009, 1)
    g.inputs['Roughness'].default_value = 0.25
    g.inputs['Coat Weight'].default_value = 1.0
    g.inputs['Coat Roughness'].default_value = 0.05
    led, l = mat('LED')
    l.inputs['Base Color'].default_value = (0.1, 0.9, 0.0, 1)
    l.inputs['Emission Color'].default_value = (0.32, 1.0, 0.0, 1)
    l.inputs['Emission Strength'].default_value = 4.5
    l.inputs['Roughness'].default_value = 0.15
    ledoff, lo = mat('LEDOff')
    lo.inputs['Base Color'].default_value = (0.35, 0.36, 0.34, 1)
    lo.inputs['Roughness'].default_value = 0.3
    halo, h = mat('Halo')
    h.inputs['Base Color'].default_value = (0, 0, 0, 1)
    h.inputs['Emission Color'].default_value = (0.3, 1.0, 0.2, 1)
    h.inputs['Emission Strength'].default_value = 0.0
    keycap, kc = mat('Keycap')
    kc.inputs['Base Color'].default_value = (0.93, 0.91, 0.88, 1)
    kc.inputs['Roughness'].default_value = 0.35
    kc.inputs['Coat Weight'].default_value = 0.3
    slot, sl = mat('Slot')
    sl.inputs['Base Color'].default_value = (0.36, 0.33, 0.3, 1)
    sl.inputs['Roughness'].default_value = 0.6
    # soft-touch texture: faint noise bump on the plastic
    nt = plastic.node_tree
    tex = nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = 140; tex.inputs['Detail'].default_value = 4
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.035; bump.inputs['Distance'].default_value = 0.002
    nt.links.new(tex.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    smile, sm = mat('Smile')
    sm.inputs['Base Color'].default_value = (0.01, 0.01, 0.012, 1)
    sm.inputs['Roughness'].default_value = 0.4
    orange, o = mat('Orange')
    o.inputs['Base Color'].default_value = (0.95, 0.45, 0.03, 1); o.inputs['Roughness'].default_value = 0.3
    o.inputs['Coat Weight'].default_value = 0.5
    steel, st = mat('Steel')
    st.inputs['Base Color'].default_value = (0.32, 0.33, 0.35, 1); st.inputs['Metallic'].default_value = 1.0
    st.inputs['Roughness'].default_value = 0.35
    navy, nv = mat('Navy')
    nv.inputs['Base Color'].default_value = (0.07, 0.11, 0.24, 1); nv.inputs['Roughness'].default_value = 0.55
    paper, pp = mat('Paper')
    pp.inputs['Base Color'].default_value = (0.85, 0.83, 0.78, 1); pp.inputs['Roughness'].default_value = 0.7
    return dict(plastic=plastic, gloss=gloss, led=led, ledoff=ledoff, keycap=keycap, slot=slot,
                smile=smile, orange=orange, steel=steel, navy=navy, paper=paper)


# Pose table. Arm placement: (x, y, depth below the top), (rx, ry, rz) in degrees; ry/rz mirror per side.
POSES = {
    'front': dict(),
    'wave': dict(arms={1: ((1.13, -0.12, 0.74), (0, 28, 0))}),
    'screwdriver': dict(arms={1: ((0.98, -0.42, 1.02), (-10, 2, 0))}, prop='screwdriver'),
    'book': dict(arms={-1: ((0.92, -1.08, 1.58), (-30, -22, 0)), 1: ((0.92, -1.08, 1.58), (-30, -22, 0))}, prop='book'),
    'controller': dict(arms={-1: ((0.74, -1.02, 1.74), (-40, -42, 0)), 1: ((0.74, -1.02, 1.74), (-40, -42, 0))}, prop='controller'),
    'blink': dict(face='closed'),
    'sleep': dict(face='closed', led=False, tilt=(4, -7)),
    'surprised': dict(face='o', tilt=(-3, 0)),
}


def build(pose='front', asleep=False):
    P = POSES[pose]
    face = 'closed' if asleep else P.get('face', 'smile')
    led_on = P.get('led', True) and not asleep
    bpy.ops.wm.read_factory_settings(use_empty=True)
    M = materials()
    b = body(); b.data.materials.append(M['plastic'])
    for x in (-0.395, 0.395):
        l = leg(x); l.data.materials.append(M['plastic'])
    arms = {}
    for side in (-1, 1):
        a = arm(side, P.get('arms', {}).get(side)); a.data.materials.append(M['plastic']); arms[side] = a
    bpy.context.view_layer.update()

    def surface_curve(name, pts2d, radius, mat, lift=0.006):
        cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
        sp = cu.splines.new('POLY'); sp.points.add(len(pts2d) - 1)
        for i, (x, z) in enumerate(pts2d):
            loc, nor = surface_point(b, x, z)
            p = loc + nor * lift
            sp.points[i].co = (p.x, p.y, p.z, 1)
        cu.bevel_depth = radius; cu.bevel_resolution = 6; cu.use_fill_caps = True
        ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob)
        ob.data.materials.append(mat)
        return ob

    ez = ZT - 0.278 * BODY_H
    if face == 'closed':
        # Closed, content eyes: two little downward arcs.
        for x in (-0.335, 0.335):
            T = 1.15
            arc = [(x + 0.1 * math.sin(t) / math.sin(T), ez - 0.06 + 0.05 * (1 - math.cos(t)) / (1 - math.cos(T)) - 0.05)
                   for t in np.linspace(-T, T, 32)]
            arc = [(px, ez - 0.02 - 0.055 * math.cos(t) + 0.055 * math.cos(T)) for (px, _), t in zip(arc, np.linspace(-T, T, 32))]
            surface_curve('Lid', arc, 0.022, M['smile'])
    else:
        big = 1.12 if face == 'o' else 1.0
        for x in (-0.335, 0.335):
            e = capsule('Eye', 0.155 * big, 0.29 * big, 0.07)
            e.data.materials.append(M['gloss'])
            place(e, b, x, ez + (0.03 if face == 'o' else 0), sink=-0.012)
    if face == 'smile':
        z_end, z_bot = ZT - 0.318 * BODY_H, ZT - 0.352 * BODY_H
        T = 1.25
        arc = [(0.118 * math.sin(t) / math.sin(T), z_bot + (z_end - z_bot) * (1 - math.cos(t)) / (1 - math.cos(T)))
               for t in np.linspace(-T, T, 48)]
        surface_curve('Smile', arc, 0.036, M['smile'])
    elif face == 'o':
        m = capsule('Mouth', 0.075, 0.095, 0.05)
        m.data.materials.append(M['gloss'])
        place(m, b, 0.0, ZT - 0.355 * BODY_H, sink=-0.01)

    # LED and the pill key on the chest.
    cz = ZT - 0.537 * BODY_H
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=0.08)
    led = bpy.context.object; led.name = 'LED'
    for p in led.data.polygons: p.use_smooth = True
    led.data.materials.append(M['led' if led_on else 'ledoff'])
    place(led, b, -0.06, cz, sink=-0.03)
    if led_on:
        bpy.ops.object.light_add(type='POINT', radius=0.03)
        gl = bpy.context.object; gl.data.energy = 0.9; gl.data.color = (0.35, 1.0, 0.25)
        loc, nor = surface_point(b, -0.06, cz); gl.location = loc + nor * 0.12
    key = capsule('Key', 0.215, 0.49, 0.12, segs=64)
    key.data.materials.append(M['keycap'])
    loc, nor = surface_point(b, 0.41, cz)
    orient(key, nor)
    key.matrix_world = key.matrix_world @ Matrix.Rotation(math.pi / 2, 4, 'Z')
    key.location = loc + nor * 0.02
    slot = capsule('Slot', 0.265, 0.54, 0.06, segs=64)
    slot.data.materials.append(M['slot'])
    orient(slot, nor); slot.matrix_world = slot.matrix_world @ Matrix.Rotation(math.pi / 2, 4, 'Z')
    slot.location = loc - nor * 0.012
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=0.098)
    ring = bpy.context.object; ring.name = 'LEDRing'
    for p in ring.data.polygons: p.use_smooth = True
    ring.data.materials.append(M['slot'])
    lloc, lnor = surface_point(b, -0.06, cz); orient(ring, lnor); ring.scale = (1, 1, 0.4); ring.location = lloc - lnor * 0.022

    prop = P.get('prop')
    if prop: PROPS[prop](M, arms)
    return b, arms, P


def rounded_box(name, size, bevel, mat, segs=6):
    bpy.ops.mesh.primitive_cube_add(size=1)
    ob = bpy.context.object; ob.name = name; ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    md = ob.modifiers.new('B', 'BEVEL'); md.width = bevel; md.segments = segs
    for p in ob.data.polygons: p.use_smooth = True
    ob.data.materials.append(mat)
    return ob


def prop_screwdriver(M, arms):
    hand = arms[1]
    # Handle: fluted orange grip through the fist; shaft and flat tip pointing up.
    rings = []
    L, R = 0.62, 0.085
    for k in range(80):
        z = L / 2 - L * k / 79
        u = abs(z) / (L / 2)
        r = R * (1 - 0.35 * u ** 6)
        rings.append((z, r))
    h = lathe('Handle', rings, segs=96)
    for v in h.data.vertices:
        a = math.atan2(v.co.y, v.co.x)
        f = 1 - 0.09 * max(0, math.cos(6 * a)) ** 8
        v.co.x *= f; v.co.y *= f
    h.data.materials.append(M['orange'])
    sh = lathe('Shaft', [(0.5, 0.0005), (0.495, 0.018), (0.44, 0.026), (0.0, 0.026), (-0.01, 0.0005)], segs=48)
    for v in sh.data.vertices:
        if v.co.z > 0.42: v.co.y *= 0.35; v.co.x *= 1.25   # flat blade
    sh.location.z = L / 2 - 0.02
    sh.data.materials.append(M['steel'])
    root = bpy.data.objects.new('Screwdriver', None); bpy.context.collection.objects.link(root)
    h.parent = root; sh.parent = root
    root.scale = (1.55, 1.55, 1.55)
    root.location = hand.location + Vector((-0.02, 0.02, 0.22))
    root.rotation_euler = (math.radians(-6), math.radians(-12), 0)


def prop_book(M, arms):
    root = bpy.data.objects.new('Book', None); bpy.context.collection.objects.link(root)
    W, H, T = 0.74, 0.95, 0.04
    for side in (-1, 1):
        half = bpy.data.objects.new('Half', None); bpy.context.collection.objects.link(half); half.parent = root
        c = rounded_box('Cover', (W, T, H), 0.012, M['navy']); c.parent = half; c.location = (side * W / 2, 0, 0)
        pg = rounded_box('Pages', (W - 0.03, 0.07, H - 0.02), 0.006, M['paper'], segs=2)
        pg.parent = half; pg.location = (side * (W / 2 - 0.01), 0.05, 0.012)
        half.rotation_euler = (0, 0, side * math.radians(24))
    sp = lathe('Spine', [(H / 2 + 0.005, 0.0005), (H / 2, 0.035), (-H / 2, 0.035), (-H / 2 - 0.005, 0.0005)], segs=32)
    sp.data.materials.append(M['navy']); sp.parent = root
    root.location = (0.04, -1.3, ZT - 1.42)
    root.rotation_euler = (math.radians(-34), 0, math.radians(3))


def prop_controller(M, arms):
    root = bpy.data.objects.new('Pad', None); bpy.context.collection.objects.link(root)
    body_ = rounded_box('PadBody', (0.62, 0.17, 0.24), 0.08, M['navy'], segs=8); body_.parent = root
    for side in (-1, 1):
        g = capsule('Grip', 0.2, 0.34, 0.17); g.data.materials.append(M['navy']); g.parent = root
        g.location = (side * 0.27, 0, -0.08); g.rotation_euler = (0, side * math.radians(-28), 0)
        g.rotation_euler = (math.radians(90), 0, side * math.radians(0))
        g.rotation_mode = 'XYZ'; g.rotation_euler = (math.radians(90), side * math.radians(30), 0)
    # D-pad (a plus) and four buttons, on the face toward the viewer.
    for (sx, sz) in ((0.11, 0.035), (0.035, 0.11)):
        d = rounded_box('Dpad', (sx, 0.03, sz), 0.01, M['paper'], segs=3); d.parent = root; d.location = (-0.17, -0.09, 0.0)
    for (bx, bz) in ((0.17, 0.045), (0.17, -0.045), (0.125, 0), (0.215, 0)):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=0.03, rotation=(math.radians(90), 0, 0))
        bt = bpy.context.object; bt.data.materials.append(M['paper']); bt.parent = root; bt.location = (bx, -0.09, bz)
    root.scale = (1.45, 1.45, 1.45)
    root.location = (0.0, -1.2, ZT - 1.72)
    root.rotation_euler = (math.radians(-12), 0, 0)


PROPS = dict(screwdriver=prop_screwdriver, book=prop_book, controller=prop_controller)


def stage(view_deg, elev_deg=7.0, size=600, samples=64, dist=15.0, lens=110):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    sc.cycles.device = 'CPU'
    sc.cycles.samples = samples
    sc.cycles.use_denoising = True
    sc.render.resolution_x = size; sc.render.resolution_y = size
    sc.render.film_transparent = True
    sc.view_settings.view_transform = VT
    sc.view_settings.look = 'None'
    sc.view_settings.exposure = EXPO

    world = bpy.data.worlds.new('W'); sc.world = world; world.use_nodes = True
    bg = world.node_tree.nodes['Background']
    bg.inputs['Color'].default_value = (0.93, 0.90, 0.87, 1); bg.inputs['Strength'].default_value = WORLD

    # Big soft key from upper left front, a fill from the right, a top light.
    def area(name, loc, energy, size, color=(1, 0.98, 0.95)):
        bpy.ops.object.light_add(type='AREA', location=loc)
        L = bpy.context.object; L.name = name
        L.data.energy = energy; L.data.size = size; L.data.color = color
        d = Vector((0, 0, 1.4)) - Vector(loc)
        L.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
        return L
    area('Key', (-2.2, -5.5, 6.5), KEYE, 9.0)
    area('Fill', (4.5, -4.0, 2.5), 55, 6.0)
    area('Top', (0.0, 0.0, 8.0), 260, 7.0)
    area('Spec', (-1.2, -7.0, 6.0), 60, 0.6, (1, 1, 1))

    bpy.ops.mesh.primitive_plane_add(size=40)
    gp = bpy.context.object; gp.is_shadow_catcher = True
    m = bpy.data.materials.new('G'); m.use_nodes = True; gp.data.materials.append(m)

    # Rotate the character, not the camera, so lighting stays fixed like a studio turntable.
    cam_data = bpy.data.cameras.new('C'); cam_data.lens = lens
    cam = bpy.data.objects.new('Cam', cam_data); sc.collection.objects.link(cam); sc.camera = cam
    e = math.radians(elev_deg)
    target = Vector((0, 0, 1.45))
    cam.location = target + Vector((0, -dist * math.cos(e), dist * math.sin(e)))
    cam.rotation_euler = (target - cam.location).to_track_quat('-Z', 'Y').to_euler()
    return sc


def turn(objs_root_yaw):
    pass


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--yaw', type=float, default=0)
    ap.add_argument('--elev', type=float, default=7)
    ap.add_argument('--out', default='out.png')
    ap.add_argument('--size', type=int, default=600)
    ap.add_argument('--samples', type=int, default=64)
    ap.add_argument('--asleep', action='store_true')
    ap.add_argument('--pose', default='front')
    ap.add_argument('--lens', type=float, default=110); ap.add_argument('--dist', type=float, default=15)
    ap.add_argument('--vt', default=VT); ap.add_argument('--expo', type=float, default=EXPO)
    ap.add_argument('--world', type=float, default=WORLD); ap.add_argument('--keye', type=float, default=KEYE)
    a = ap.parse_args(argv)
    VT, EXPO, WORLD, KEYE = a.vt, a.expo, a.world, a.keye
    _, _, P = build(a.pose, asleep=a.asleep)
    # parent everything to an empty and turn it
    root = bpy.data.objects.new('Root', None); bpy.context.collection.objects.link(root)
    for ob in list(bpy.context.collection.objects):
        if ob is not root and ob.parent is None and ob.type in ('MESH', 'CURVE', 'LIGHT', 'EMPTY'):
            ob.parent = root
    lean, roll = P.get('tilt', (0, 0))
    # pivot at the feet
    root.rotation_euler = (math.radians(lean), math.radians(roll), math.radians(a.yaw))
    stage(a.yaw, a.elev, a.size, a.samples, dist=a.dist, lens=a.lens)
    bpy.context.scene.render.filepath = a.out
    bpy.ops.render.render(write_still=True)

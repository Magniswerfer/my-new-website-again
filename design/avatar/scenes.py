"""
The character's page scenes: props, the moves that use them, and the face for each page.
Built on the model and rig in build.py; the plan is in PAGES.md, the rules in ANIMATION.md.

  python3 design/avatar/scenes.py --scene weeks --frame 40 --out still.png [camera options]
  python3 design/avatar/scenes.py --scene weeks --step 2 --out "frames/f#.png"         # the loop, on twos
  python3 design/avatar/scenes.py --list

Each scene: a face preset, the props it needs (bound to the bone that carries them: a mitten, the
head, the body or the floor), and one looping move of 96 frames (4 s at 24 fps) that starts and
ends on the same pose. Props are placed while the rig is in the move's holding pose, so held things
sit in the mittens and follow them.
"""
import sys, math, argparse, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import bpy, bmesh
import numpy as np
from mathutils import Vector, Matrix, Euler
import build as B

N = 96                     # frames per loop


# ---------- materials ----------

def mat(name, color, rough=0.5, **kw):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    p = m.node_tree.nodes['Principled BSDF']
    p.inputs['Base Color'].default_value = (*color, 1)
    p.inputs['Roughness'].default_value = rough
    for k, v in kw.items(): p.inputs[k].default_value = v
    return m


def speckled(name, color, dots=(0.25, 0.22, 0.2), scale=90.0):
    """A ceramic glaze with fine dark speckles."""
    m = mat(name, color, 0.45, **{'Coat Weight': 0.4, 'Coat Roughness': 0.2})
    nt = m.node_tree; p = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value = scale; tex.inputs['Detail'].default_value = 2
    ramp = nt.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position = 0.68; ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[0].color = (*color, 1); ramp.color_ramp.elements[1].color = (*dots, 1)
    nt.links.new(tex.outputs['Fac'], ramp.inputs['Fac']); nt.links.new(ramp.outputs['Color'], p.inputs['Base Color'])
    return m


def fabric(name, color):
    """Soft cloth: rough, a sheen, a faint weave bump."""
    m = mat(name, color, 0.85, **{'Sheen Weight': 0.6, 'Sheen Roughness': 0.4})
    nt = m.node_tree; p = nt.nodes['Principled BSDF']
    tex = nt.nodes.new('ShaderNodeTexWave'); tex.inputs['Scale'].default_value = 140
    bump = nt.nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value = 0.08
    nt.links.new(tex.outputs['Fac'], bump.inputs['Height']); nt.links.new(bump.outputs['Normal'], p.inputs['Normal'])
    return m


def mats():
    return dict(
        cream=mat('PropCream', (0.75, 0.72, 0.66), 0.55),
        mug=speckled('Mug', (0.78, 0.74, 0.68)),
        coffee=mat('Coffee', (0.06, 0.03, 0.015), 0.15),
        graphite=mat('Graphite', (0.05, 0.05, 0.055), 0.45),
        metal=mat('Steel', (0.6, 0.6, 0.62), 0.3, **{'Metallic': 1.0}),
        orange=mat('Orange', (0.9, 0.42, 0.04), 0.35, **{'Coat Weight': 0.4}),
        pcb=mat('PCB', (0.06, 0.28, 0.12), 0.45),
        gold=mat('Gold', (0.85, 0.62, 0.2), 0.3, **{'Metallic': 1.0}),
        navy=mat('Navy', (0.06, 0.09, 0.2), 0.5),
        brown=mat('BookBrown', (0.35, 0.18, 0.09), 0.6),
        paper=mat('Paper', (0.86, 0.83, 0.76), 0.75),
        screen=mat('Screen', (0.02, 0.025, 0.03), 0.25, **{'Emission Color': (0.03, 0.05, 0.06, 1), 'Emission Strength': 1.0}),
        prompt=mat('Prompt', (0.2, 0.9, 0.3), 0.3, **{'Emission Color': (0.25, 1.0, 0.35, 1), 'Emission Strength': 4.0}),
        bean=fabric('Beanbag', (0.36, 0.25, 0.16)),
        bulb=mat('Bulb', (1.0, 0.85, 0.5), 0.1, **{'Emission Color': (1.0, 0.75, 0.35, 1), 'Emission Strength': 6.0,
                                                    'Transmission Weight': 0.3}),
        ink=bpy.data.materials['Ink'],
        lens=mat('Lens', (0.02, 0.03, 0.035), 0.05, **{'Coat Weight': 1.0}),
    )


# ---------- geometry helpers ----------

def smooth(ob):
    for p in ob.data.polygons: p.use_smooth = True
    return ob


def rbox(name, size, bevel, m, segs=5):
    bpy.ops.mesh.primitive_cube_add(size=1); ob = bpy.context.object; ob.name = name; ob.scale = size
    bpy.ops.object.transform_apply(scale=True)
    bv = ob.modifiers.new('B', 'BEVEL'); bv.width = bevel; bv.segments = segs; bv.limit_method = 'NONE'
    ob.data.materials.append(m); return smooth(ob)


def cyl(name, r, h, m, verts=48, bevel=0.0):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=h); ob = bpy.context.object; ob.name = name
    if bevel:
        bv = ob.modifiers.new('B', 'BEVEL'); bv.width = bevel; bv.segments = 4; bv.limit_method = 'ANGLE'
    ob.data.materials.append(m); return smooth(ob)


def ball(name, r, m, scale=(1, 1, 1)):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=r); ob = bpy.context.object; ob.name = name
    ob.scale = scale; bpy.ops.object.transform_apply(scale=True)
    ob.data.materials.append(m); return smooth(ob)


def tube(name, pts, r, m):
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, p in enumerate(pts): sp.points[i].co = (*p, 1)
    cu.bevel_depth = r; cu.bevel_resolution = 6; cu.use_fill_caps = True
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(m)
    return ob


def text(name, s, size, m):
    cu = bpy.data.curves.new(name, 'FONT'); cu.body = s; cu.size = size; cu.align_x = 'CENTER'; cu.align_y = 'CENTER'
    cu.extrude = 0.004
    ob = bpy.data.objects.new(name, cu); bpy.context.collection.objects.link(ob); ob.data.materials.append(m)
    return ob


def group(name, parts):
    root = bpy.data.objects.new(name, None); bpy.context.collection.objects.link(root)
    for p in parts: p.parent = root
    return root


# ---------- props (each built around its own origin; +z up, -y toward him... built facing the viewer: -y) ----------

def mug(M):
    body = cyl('MugBody', 0.13, 0.27, M['mug'], bevel=0.02)
    inner = cyl('MugCoffee', 0.112, 0.005, M['coffee']); inner.location.z = 0.105
    handle = bpy.data.objects.new('MugHandle', bpy.data.curves.new('MH', 'CURVE')); bpy.context.collection.objects.link(handle)
    sp = handle.data.splines.new('BEZIER'); sp.bezier_points.add(2); handle.data.dimensions = '3D'
    for i, (x, z) in enumerate(((0.12, 0.07), (0.21, 0.0), (0.12, -0.07))):
        bp = sp.bezier_points[i]; bp.co = (x, 0, z); bp.handle_left_type = bp.handle_right_type = 'AUTO'
    handle.data.bevel_depth = 0.024; handle.data.bevel_resolution = 6; handle.data.materials.append(M['mug'])
    steam = []
    for i, x in enumerate((-0.04, 0.05)):
        pts = [(x + 0.03 * math.sin(t * 2.2 + i), 0, 0.2 + t * 0.1) for t in np.linspace(0, 2.2, 22)]
        st = tube(f'Steam{i}', pts, 0.009, M['ink']); st.scale = (0.7, 0.7, 0.6); steam.append(st)
    g = group('Mug', [body, inner, handle] + steam)
    return g, steam


def laptop(M):
    base = rbox('LapBase', (0.56, 0.38, 0.035), 0.016, M['graphite'])
    keys = rbox('LapKeys', (0.46, 0.2, 0.006), 0.003, M['metal']); keys.location = (0, 0.02, 0.019)
    lid = rbox('LapLid', (0.56, 0.025, 0.36), 0.014, M['graphite'])
    scr = rbox('LapScreen', (0.5, 0.004, 0.3), 0.004, M['screen']); scr.location = (0, -0.0135, 0)
    t = text('LapPrompt', '>_', 0.11, M['prompt']); t.rotation_euler = (math.radians(90), 0, 0); t.location = (-0.12, -0.018, 0.06)
    hinge = bpy.data.objects.new('LapHinge', None); bpy.context.collection.objects.link(hinge)
    hinge.location = (0, -0.19, 0.018)                            # the hinge on the far side from him
    for o in (lid, scr, t):
        o.parent = hinge; o.location.z += 0.18
    lid.rotation_euler = scr.rotation_euler = (0, 0, math.radians(180))   # screen faces him
    t.rotation_euler = (math.radians(90), 0, math.radians(180)); t.location.y = 0.018
    scr.location.y = 0.0135
    hinge.rotation_euler = (math.radians(14), 0, 0)               # lid open, leaning away from him
    return group('Laptop', [base, keys, hinge])


def headphones(M):
    """Fitted to his dome: a band over the top, cups on the sides at eye height."""
    cups = []
    for sx in (1, -1):
        c = cyl(f'Cup{sx}', 0.17, 0.11, M['graphite'], bevel=0.03); c.rotation_euler = (0, math.radians(90), 0)
        c.location = (sx * 1.1, 0, 0); cups.append(c)
        pad = ball(f'Pad{sx}', 0.15, M['graphite'], (0.4, 1, 1)); pad.location = (sx * 1.03, 0, 0); cups.append(pad)
    band = tube('Band', [(1.1 * math.cos(a), 0, 0.12 + 0.95 * math.sin(a)) for a in np.linspace(0, math.pi, 40)], 0.05, M['graphite'])
    return group('Headphones', cups + [band])


def soldering(M):
    grip = cyl('IronGrip', 0.045, 0.3, M['orange'], bevel=0.01)
    shaft = cyl('IronShaft', 0.012, 0.22, M['metal']); shaft.location.z = -0.25
    tip = ball('IronTip', 0.014, M['metal'], (1, 1, 2.2)); tip.location.z = -0.37
    iron = group('Iron', [grip, shaft, tip])
    board = rbox('Board', (0.42, 0.03, 0.32), 0.01, M['pcb'])
    pads = []
    for i in range(4):
        for j in range(3):
            p = cyl(f'Pad{i}{j}', 0.014, 0.012, M['gold'], verts=16); p.rotation_euler = (math.radians(90), 0, 0)
            p.location = (-0.14 + 0.093 * i, -0.017, -0.09 + 0.09 * j); pads.append(p)
    chip = rbox('Chip', (0.12, 0.025, 0.08), 0.006, M['graphite']); chip.location = (0.08, -0.025, 0.06)
    cap = cyl('Cap', 0.03, 0.07, M['navy'], bevel=0.008); cap.rotation_euler = (math.radians(90), 0, 0); cap.location = (-0.1, -0.05, 0.06)
    pcb = group('Board', [board, chip, cap] + pads)
    smoke = tube('Smoke', [(0.02 * math.sin(t * 3), 0, t * 0.12) for t in np.linspace(0, 1.4, 16)], 0.01, M['ink'])
    return iron, pcb, smoke


def camera(M):
    body = rbox('CamBody', (0.42, 0.16, 0.26), 0.035, M['graphite'])
    top = rbox('CamTop', (0.36, 0.14, 0.04), 0.012, M['metal']); top.location.z = 0.14
    lens = cyl('CamLens', 0.09, 0.12, M['graphite'], bevel=0.01); lens.rotation_euler = (math.radians(90), 0, 0); lens.location = (0.04, -0.12, -0.01)
    glass = ball('CamGlass', 0.07, M['lens'], (1, 0.35, 1)); glass.location = (0.04, -0.18, -0.01)
    btn = cyl('CamButton', 0.025, 0.03, M['metal']); btn.location = (-0.12, 0, 0.17)
    return group('Camera', [body, top, lens, glass, btn])


def d20(M):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.17); ob = bpy.context.object; ob.name = 'D20'
    bv = ob.modifiers.new('B', 'BEVEL'); bv.width = 0.012; bv.segments = 3
    ob.data.materials.append(M['navy'])
    t = text('D20Num', '20', 0.08, M['paper']); t.rotation_euler = (math.radians(90), 0, 0); t.location = (0, -0.152, 0)
    return group('Die', [ob, t])


def beanbag(M):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64, ring_count=40, radius=1); ob = bpy.context.object; ob.name = 'Beanbag'
    rng = np.random.default_rng(3)
    for v in ob.data.vertices:
        x, y, z = v.co
        k = 1 + 0.05 * math.sin(5 * x + 2 * y) * math.cos(4 * z) + 0.03 * math.sin(9 * y + 3 * z)
        z2 = z * 0.5 if z > -0.2 else z * 0.42
        v.co = Vector((x * 1.25 * k, y * 1.05 * k, (z2 + 0.08 * max(0.0, -y)) * k))
    ob.data.materials.append(M['bean']); smooth(ob)
    sub = ob.modifiers.new('S', 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    return ob


def book_open(M, cover):
    halves = []
    for sx in (1, -1):
        h = bpy.data.objects.new(f'Half{sx}', None); bpy.context.collection.objects.link(h)
        c = rbox(f'Cover{sx}', (0.28, 0.02, 0.38), 0.008, M[cover]); c.parent = h; c.location = (sx * 0.14, 0, 0)
        pg = rbox(f'Pages{sx}', (0.26, 0.035, 0.36), 0.004, M['paper'], segs=2); pg.parent = h; pg.location = (sx * 0.135, -0.025, 0)
        h.rotation_euler = (0, 0, sx * math.radians(-24)); halves.append(h)
    return group('Book', halves)


def book_stack(M):
    books = []
    for i, (m, w, rot) in enumerate((('navy', 0.5, 2), ('brown', 0.46, -4), ('paper', 0.44, 3))):
        b = rbox(f'StackBook{i}', (w, 0.34, 0.09), 0.012, M[m]); b.location.z = 0.095 * i
        b.rotation_euler = (0, 0, math.radians(rot)); books.append(b)
    return group('Books', books)


def terminal(M):
    case = rbox('TermCase', (0.6, 0.55, 0.5), 0.05, M['cream'])
    scr = rbox('TermScreen', (0.46, 0.02, 0.34), 0.04, M['screen']); scr.location = (0, -0.28, 0.03)
    t = text('TermPrompt', '>_', 0.12, M['prompt']); t.rotation_euler = (math.radians(90), 0, 0); t.location = (-0.1, -0.295, 0.06)
    kb = rbox('TermKeys', (0.62, 0.24, 0.06), 0.02, M['cream']); kb.location = (0, -0.55, -0.22)
    keys = rbox('TermKeyTops', (0.54, 0.16, 0.012), 0.004, M['paper']); keys.location = (0, -0.55, -0.186)
    return group('Terminal', [case, scr, t, kb, keys])


def bulb(M):
    glass = ball('BulbGlass', 0.13, M['bulb'], (1, 1, 1.1))
    base = cyl('BulbBase', 0.06, 0.1, M['gold'], bevel=0.01); base.location.z = -0.16
    rays = [tube(f'Ray{i}', [(0.2 * math.cos(a), 0, 0.2 * math.sin(a)), (0.3 * math.cos(a), 0, 0.3 * math.sin(a))], 0.012, M['ink'])
            for i, a in enumerate(np.radians([30, 60, 90, 120, 150]))]
    return group('Bulb', [glass, base] + rays)


# ---------- binding ----------

def bind_to(rig, ob, bone):
    """Parent `ob` to a bone, keeping where it is now (in the current pose)."""
    bpy.context.view_layer.update()
    mw = ob.matrix_world.copy()
    ob.parent = rig; ob.parent_type = 'BONE'; ob.parent_bone = bone
    ob.matrix_world = mw


def tip(rig, side):
    return rig.matrix_world @ rig.pose.bones[f'arm_lower.{side}'].tail


def both_tips(rig):
    return (tip(rig, 'L') + tip(rig, 'R')) / 2


# ---------- poses used inside moves ----------

def sit(rig, f, back=-10.0, drop=0.86, lean=0.0):
    """Key a sitting pose at frame f: shell down to the floor, hips forward, legs out in front."""
    pb = rig.pose.bones
    B.bone_loc(pb['body'], (0, 0, -B.Z0 * drop)); pb['body'].keyframe_insert('location', frame=f)
    B.joint(rig, 'body', f, x=back + lean)
    for s_, sx in (('L', 1), ('R', -1)):
        B.bone_loc(pb[f'hip_attach.{s_}'], (0, -0.08, 0)); pb[f'hip_attach.{s_}'].keyframe_insert('location', frame=f)
        fb = pb[f'foot.{s_}']; head = fb.bone.head_local
        B.bone_loc(fb, (sx * 0.3, -0.62, 0.18 - head.z))
        fb.rotation_quaternion = B.wq(fb, Matrix.Rotation(math.radians(sx * 34), 3, 'Z') @ Matrix.Rotation(math.radians(-72), 3, 'X'))
        fb.keyframe_insert('location', frame=f); fb.keyframe_insert('rotation_quaternion', frame=f)


def breathe(rig, f, depth=0.008, period=N):
    k = math.sin(2 * math.pi * (f - 1) / period)
    pb = rig.pose.bones['body']; B.squash_body(pb, 1 + depth * max(0.0, k) - depth * 0.35 * max(0.0, -k))
    pb.keyframe_insert('scale', frame=f)


def blink(frames=(70,)):
    for ob, kn in [(o, 'closed') for o in B.EYES] + [(o, 'blink') for o in B.BODY]:
        sk = ob.data.shape_keys.key_blocks[kn]
        for f0 in frames:
            for f, c in ((f0, 0), (f0 + 2, 1), (f0 + 3, 1), (f0 + 7, 0)):
                sk.value = c; sk.keyframe_insert('value', frame=f)
        sk.value = 0


def obj_action(ob, name):
    ob.animation_data_create(); ob.animation_data.action = bpy.data.actions.new(f'{name}|{ob.name}')


# ---------- scenes ----------

def hold(rig, f, side, **k):
    B.key_arm(rig, side, f, **k)


def scene_weeks(rig, M):
    """Holding a mug in both mittens; lifts it for a sip, a small exhale, lowers it. Steam drifts up."""
    act = B.new_action(rig, 'weeks')
    HOLD = dict(fwd=48, inward=40, curl=30, hug=26, slide=30)
    SIP = dict(fwd=70, inward=46, curl=40, hug=30, slide=34)
    for side, lag in (('L', 0), ('R', 2)):
        for f, p in ((1, HOLD), (26 + lag, HOLD), (36 + lag, SIP), (54 + lag, SIP), (66 + lag, HOLD), (N + 1, HOLD)):
            hold(rig, f, side, **p)
    for f, x in ((1, 0), (30, 1), (40, -5), (54, -5), (64, 2), (72, 0), (N + 1, 0)):
        B.joint(rig, 'head', f, x=x, y=1.5 if 36 < f < 60 else 0)
    for f in range(1, N + 2, 4): breathe(rig, f)
    blink((84,))
    B.stash(rig, act, 'weeks')
    B.use_move('weeks'); bpy.context.scene.frame_set(1)
    g, steam = mug(M); g.scale = (2.0, 2.0, 2.0)
    g.location = both_tips(rig) + Vector((0.04, -0.3, -0.05))
    bind_to(rig, g, 'arm_lower.L')
    for i, st in enumerate(steam):                                  # steam drifts up and fades back in
        obj_action(st, 'weeks')
        for f, z, s in ((1, 0, 0.6), (48, 0.06, 1.0), (N + 1, 0, 0.6)):
            st.location.z = z + i * 0.01; st.scale = (1, 1, s)
            st.keyframe_insert('location', frame=f); st.keyframe_insert('scale', frame=f)
    return [g] + steam


def scene_blog(rig, M):
    """Sitting with a laptop on the floor in front of him: bursts of typing, a pause and a glance up."""
    act = B.new_action(rig, 'blog')
    for f in (1, N + 1): sit(rig, f)
    TYPE = dict(fwd=44, inward=22, curl=18, hug=10, slide=26)
    for f in range(1, N + 2, 3):
        pause = 40 <= f <= 62
        for side, ph in (('L', 0), ('R', 1)):
            tap = 0 if pause else 4 * ((f // 3 + ph) % 2)
            hold(rig, f, side, **{**TYPE, 'fwd': TYPE['fwd'] - tap})
    for f, x, z in ((1, 7, 0), (38, 7, 0), (46, -3, -10), (58, -3, -10), (66, 7, 0), (N + 1, 7, 0)):
        B.joint(rig, 'head', f, x=x, z=z)
    for f in range(1, N + 2, 4): breathe(rig, f)
    blink((50,))
    B.stash(rig, act, 'blog')
    B.use_move('blog'); bpy.context.scene.frame_set(1)
    lap = laptop(M); lap.scale = (1.6, 1.6, 1.6); lap.location = (0, -0.82, 0.3); lap.rotation_euler = (math.radians(8), 0, 0)
    bind_to(rig, lap, 'root')
    return [lap]


def scene_projects(rig, M):
    """Soldering: the board in one mitten, the iron in the other; three little dabs, a wisp of smoke,
    then he looks up, pleased."""
    act = B.new_action(rig, 'projects')
    BOARD = dict(fwd=46, inward=44, curl=28, hug=20, slide=28)
    IRON = dict(fwd=58, inward=24, curl=26, hug=14, slide=22)
    for f in (1, N + 1): hold(rig, f, 'R', **BOARD)
    for f in (30, 70): hold(rig, f, 'R', **{**BOARD, 'fwd': 47})
    dabs = [(1, 0), (10, 5), (14, 0), (22, 5), (26, 0), (34, 5), (38, 0), (60, -6), (84, -6), (N + 1, 0)]
    for f, d in dabs: hold(rig, f, 'L', **{**IRON, 'fwd': IRON['fwd'] + d})
    for f, x, z in ((1, 9, 0), (40, 9, 0), (52, -2, -9), (78, -2, -9), (90, 9, 0), (N + 1, 9, 0)):
        B.joint(rig, 'head', f, x=x, z=z)
    for f in range(1, N + 2, 4): breathe(rig, f)
    blink((56,))
    B.stash(rig, act, 'projects')
    B.use_move('projects'); bpy.context.scene.frame_set(1)
    iron, pcb, smoke = soldering(M)
    pcb.scale = (1.8, 1.8, 1.8)
    pcb.location = tip(rig, 'R') + Vector((0.22, -0.26, 0.06)); pcb.rotation_euler = (math.radians(-35), 0, math.radians(-10))
    bind_to(rig, pcb, 'arm_lower.R')
    iron.scale = (1.6, 1.6, 1.6)
    iron.location = tip(rig, 'L') + Vector((-0.02, -0.12, 0.2)); iron.rotation_euler = (math.radians(30), math.radians(-35), 0)
    bind_to(rig, iron, 'arm_lower.L')
    smoke.location = pcb.matrix_world.translation + Vector((0.0, -0.08, 0.16)); bind_to(rig, smoke, 'arm_lower.R')
    obj_action(smoke, 'projects')
    for f, s in ((1, 0.01), (12, 0.01), (20, 1.0), (40, 1.0), (48, 0.01), (N + 1, 0.01)):
        smoke.scale = (s, s, s); smoke.keyframe_insert('scale', frame=f)
    return [iron, pcb, smoke]


def scene_photos(rig, M):
    """Camera up to his face, a click (a little nudge), down to check the shot, up again."""
    act = B.new_action(rig, 'photos')
    UP = dict(fwd=78, inward=58, curl=30, hug=24, slide=36)
    DOWN = dict(fwd=56, inward=50, curl=32, hug=26, slide=34)
    for side, lag in (('L', 0), ('R', 1)):
        for f, p in ((1, UP), (36 + lag, UP), (40 + lag, {**UP, 'fwd': 74}), (44 + lag, UP), (58 + lag, UP),
                     (70 + lag, DOWN), (82 + lag, DOWN), (N + 1, UP)):
            hold(rig, f, side, **p)
    for f, x in ((1, -2), (38, -2), (40, -4), (44, -2), (60, -2), (72, 9), (84, 9), (N + 1, -2)):
        B.joint(rig, 'head', f, x=x)
    for f in range(1, N + 2, 4): breathe(rig, f)
    B.stash(rig, act, 'photos')
    B.use_move('photos'); bpy.context.scene.frame_set(1)
    cam = camera(M); cam.scale = (1.9, 1.9, 1.9); cam.location = both_tips(rig) + Vector((0, -0.3, 0.04))
    # Held at his face, but carried by the body (not a mitten), so lowering it can't tip it over:
    # it moves down to his chest and tilts its back up toward him to check the shot.
    bind_to(rig, cam, 'body')
    obj_action(cam, 'photos'); z0 = cam.location.z; y0 = cam.location.y
    for f, dz, dy, rx in ((1, 0, 0, 0), (38, 0, 0, 0), (40, 0, 0.02, 0), (44, 0, 0, 0), (60, 0, 0, 0),
                          (70, -0.3, 0.06, 28), (82, -0.3, 0.06, 28), (N + 1, 0, 0, 0)):
        cam.location.z = z0 + dz; cam.location.y = y0 + dy; cam.rotation_euler = (math.radians(rx), 0, 0)
        cam.keyframe_insert('location', frame=f); cam.keyframe_insert('rotation_euler', frame=f)
    return [cam]


def scene_rotation(rig, M):
    """Headphones on, eyes shut, bobbing to the beat (96 bpm: a beat every 15 frames)."""
    act = B.new_action(rig, 'rotation')
    beat = 15
    for f in range(1, N + 2, 3):
        ph = ((f - 1) % beat) / beat
        nod = 3.5 * math.exp(-((ph - 0.1) / 0.18) ** 2)
        sway = math.sin(2 * math.pi * (f - 1) / (2 * beat * 3.2))
        B.joint(rig, 'head', f, x=nod, y=2.5 * sway)
        B.key_body(rig, f, lean_y=1.5 * sway, bob=-0.01 * math.exp(-((ph - 0.12) / 0.2) ** 2))
        for side, sx in (('L', 1), ('R', -1)):
            hold(rig, f, side, out=4 + 2 * sway * sx, fwd=4 * sway * sx)
    B.stash(rig, act, 'rotation')
    B.use_move('rotation'); bpy.context.scene.frame_set(1)
    hp = headphones(M); bpy.context.view_layer.update()
    hp.location = (0, -0.02, B.ZT - 0.42 * B.BODY_H); hp.scale = (1.02, 0.97, 1.0)
    bind_to(rig, hp, 'head')
    return [hp]


def scene_contact(rig, M):
    """Turning a d20 over in his mittens, looking at it, a little toss and catch."""
    act = B.new_action(rig, 'contact')
    HOLD = dict(fwd=50, inward=50, curl=34, hug=28, slide=34)
    for side, lag in (('L', 0), ('R', 1)):
        for f, p in ((1, HOLD), (40 + lag, HOLD), (46 + lag, {**HOLD, 'fwd': 60}), (54 + lag, {**HOLD, 'fwd': 46}),
                     (60 + lag, HOLD), (N + 1, HOLD)):
            hold(rig, f, side, **p)
    for f, x in ((1, 8), (44, 8), (50, -4), (58, 6), (N + 1, 8)):
        B.joint(rig, 'head', f, x=x)
    for f in range(1, N + 2, 4): breathe(rig, f)
    blink((76,))
    B.stash(rig, act, 'contact')
    B.use_move('contact'); bpy.context.scene.frame_set(1)
    die = d20(M); die.scale = (1.8, 1.8, 1.8); die.location = both_tips(rig) + Vector((0, -0.3, 0.12))
    bind_to(rig, die, 'arm_lower.L')
    obj_action(die, 'contact')
    for f, z, r in ((1, 0, 0), (44, 0, 40), (52, 0.28, 160), (58, 0, 280), (N + 1, 0, 360)):
        die.location.z = die.location.z * 0 + z; die.rotation_euler = (0, 0, math.radians(r))
        die.keyframe_insert('location', index=2, frame=f); die.keyframe_insert('rotation_euler', frame=f)
    return [die]


def scene_404(rig, M):
    """Sitting at a little retro terminal, typing, then he turns to the viewer: oh."""
    act = B.new_action(rig, '404')
    for f in (1, N + 1): sit(rig, f)
    TYPE = dict(fwd=50, inward=18, curl=16, hug=8, slide=28)
    for f in range(1, N + 2, 3):
        pause = f >= 52
        for side, ph in (('L', 0), ('R', 1)):
            tap = 0 if pause else 4 * ((f // 3 + ph) % 2)
            hold(rig, f, side, **{**TYPE, 'fwd': TYPE['fwd'] - tap})
    for f, x, z in ((1, 6, 6), (48, 6, 6), (56, -4, -16), (86, -4, -16), (N + 1, 6, 6)):
        B.joint(rig, 'head', f, x=x, z=z)
    for f in range(1, N + 2, 4): breathe(rig, f)
    B.stash(rig, act, '404')
    B.use_move('404'); bpy.context.scene.frame_set(1)
    t = terminal(M); t.scale = (1.4, 1.4, 1.4); t.location = (-0.75, -1.25, 0.35); t.rotation_euler = (0, 0, math.radians(28))
    bind_to(rig, t, 'root')
    return [t]


def scene_empty(rig, M):
    """Lounging in a beanbag, eyes happily shut, breathing slowly; the LED glows on."""
    act = B.new_action(rig, 'empty')
    for f in (1, N + 1): sit(rig, f, back=-16, drop=0.55)
    for side, sx in (('L', 1), ('R', -1)):
        for f in (1, N + 1): hold(rig, side=side, f=f, out=42, fwd=-6, curl=6)
        hold(rig, 48, side, out=44, fwd=-5, curl=6)
    for f in range(1, N + 2, 4): breathe(rig, f, depth=0.012)
    for f, y in ((1, 3), (48, 5), (N + 1, 3)):
        B.joint(rig, 'head', f, x=-3, y=y)
    B.stash(rig, act, 'empty')
    B.use_move('empty'); bpy.context.scene.frame_set(1)
    bag = beanbag(M); bag.location = (0, 0.6, 0.45); bag.scale = (1.4, 1.3, 1.35)
    bind_to(rig, bag, 'root')
    return [bag]


def scene_essay(rig, M):
    """Sitting, reading an open book held in both mittens; small nods as he reads."""
    act = B.new_action(rig, 'essay')
    for f in (1, N + 1): sit(rig, f)
    HOLD = dict(fwd=50, inward=50, curl=30, hug=26, slide=34)
    for side in 'LR':
        for f in (1, 48, N + 1): hold(rig, f, side, **({**HOLD, 'fwd': 52} if f == 48 else HOLD))
    for f, x in ((1, 9), (24, 10), (48, 8), (72, 10), (N + 1, 9)):
        B.joint(rig, 'head', f, x=x)
    for f in range(1, N + 2, 4): breathe(rig, f)
    blink((60,))
    B.stash(rig, act, 'essay')
    B.use_move('essay'); bpy.context.scene.frame_set(1)
    bk = book_open(M, 'navy'); bk.scale = (1.7, 1.7, 1.7); bk.location = both_tips(rig) + Vector((0, -0.3, 0.2)); bk.rotation_euler = (math.radians(-25), 0, 0)
    bind_to(rig, bk, 'arm_lower.L')
    return [bk]


def scene_sent(rig, M):
    """Message sent: he holds a lit lightbulb up beside his head by its base, and beams. It bobs up
    a little on each beat of pride, held the whole time (nothing floats)."""
    act = B.new_action(rig, 'sent')
    for f in (1, N + 1): hold(rig, f, 'R', out=6)
    for f, y in ((1, 4), (48, 6), (N + 1, 4)): B.joint(rig, 'head', f, y=y)
    for f in range(1, N + 2, 4): breathe(rig, f)
    b = bulb(M); b.scale = (1.6, 1.6, 1.6)
    zs = shoulder_z(); c = (1.18, -0.32, zs + 0.86)
    up = lambda dz: ((c[0], c[1], c[2] + dz), (0, -8, 0))
    track = [(1, up(0)), (20, up(0.06)), (30, up(0)), (60, up(0)), (70, up(0.06)), (80, up(0)), (N + 1, up(0))]
    held(rig, 'sent', b, track, {'L': ((0.0, 0.0, -0.34), (0.0, 0.0, -1.0))}, curl=34, hug=10)
    B.stash(rig, act, 'sent')
    return [b]


def scene_rotation_empty(rig, M):
    """Carrying a stack of books that wobbles as he shifts his weight."""
    act = B.new_action(rig, 'rotation_empty')
    HOLD = dict(fwd=46, inward=50, curl=34, hug=30, slide=34)
    for side in 'LR':
        for f in (1, 48, N + 1): hold(rig, f, side, **HOLD)
    for f in range(1, N + 2, 4):
        s = math.sin(2 * math.pi * (f - 1) / N)
        B.key_body(rig, f, lean_y=1.2 * s); breathe(rig, f)
    for f, x, z in ((1, 2, -4), (48, 3, 4), (N + 1, 2, -4)): B.joint(rig, 'head', f, x=x, z=z)
    B.stash(rig, act, 'rotation_empty')
    B.use_move('rotation_empty'); bpy.context.scene.frame_set(1)
    st = book_stack(M); st.scale = (1.7, 1.7, 1.7); st.location = both_tips(rig) + Vector((0, -0.32, -0.05))
    bind_to(rig, st, 'arm_lower.L')
    return [st]


# ====================================================================================================
# Holding things properly. Props are keyed in the world (parented to the rig's root, so they follow
# the scene's turn), and each mitten that holds one is solved onto its grip point every few frames, so
# the mitten sits against the prop instead of floating near it. When a prop is out of reach, the prop
# moves to the mitten (a held thing goes where the hand is), never the other way round.
# ====================================================================================================
from scipy.optimize import minimize

STANDOFF = 0.2          # palm centre to the surface it touches (the mitten's half-thickness)


def pose_arm(rig, side, out=0.0, fwd=0.0, inward=0.0, curl=0.0, hug=0.0, slide=0.0):
    sx = 1 if side == 'L' else -1
    pb = rig.pose.bones
    att, sh, lo = (pb[f'{n}.{side}'] for n in ('attach', 'shoulder', 'arm_lower'))
    att.rotation_quaternion = B.wq(att, Matrix.Rotation(math.radians(-sx * slide), 3, 'Z'))
    sh.rotation_quaternion = B.wq(sh, B.arm_rot(sx, out, fwd, inward))
    lo.rotation_quaternion = B.wq(lo, Matrix.Rotation(math.radians(-curl), 3, 'X') @ Matrix.Rotation(math.radians(sx * hug), 3, 'Y'))


def palm(rig, side):
    lo = rig.pose.bones[f'arm_lower.{side}']
    return rig.matrix_world @ (lo.head + (lo.tail - lo.head) * 0.6)


def solve_arm(rig, side, target, curl, hug, x0):
    """out, fwd, inward, slide that put the palm on `target` (world)."""
    def cost(x):
        out, fwd, inward, slide = x
        pose_arm(rig, side, out, fwd, inward, curl, hug, slide)
        bpy.context.view_layer.update()
        d = (palm(rig, side) - target).length
        pen = max(0, slide - 45) ** 2 + max(0, -8 - slide) ** 2 + max(0, fwd - 140) ** 2 + max(0, -40 - fwd) ** 2
        return 100 * d * d + 1e-4 * pen + 1e-6 * (out * out + inward * inward)
    r = minimize(cost, x0, method='Nelder-Mead', options=dict(maxiter=400, xatol=0.05, fatol=1e-7))
    cost(r.x)
    return list(r.x), (palm(rig, side) - target)


def trs(loc, rot):
    return Matrix.Translation(Vector(loc)) @ Euler(tuple(math.radians(a) for a in rot), 'XYZ').to_matrix().to_4x4()


def key_world(ob, f, M):
    sc = getattr(ob, '_scale', None) or ob.get('scale0') or tuple(ob.scale)
    ob['scale0'] = tuple(sc)
    ob.matrix_world = M @ Matrix.Diagonal((*sc, 1.0))
    ob.keyframe_insert('location', frame=f); ob.keyframe_insert('rotation_euler', frame=f)


def held(rig, name, prop, track, grips, curl=24, hug=22, free=None, step=4, lag=None):
    """Animate `prop` along `track` [(frame, ((x, y, z), (rx, ry, rz)))] in the world, with each mitten
    in `grips` {side: ((px, py, pz), (nx, ny, nz))} (a point on the prop and its outward normal, in the
    prop's own frame) solved onto it every `step` frames. `free` keys the other arm: {side: dict}."""
    bind_to(rig, prop, 'root')
    prop.rotation_mode = 'XYZ'
    guess = {s: [4.0, 40.0, 30.0, 25.0] for s in grips}
    frames = sorted(set(list(range(1, N + 2, step)) + [k[0] for k in track]))
    worst = 0.0
    for f in frames:
        loc, rot = B.smooth_track([(k[0], (*k[1][0], *k[1][1])) for k in track], f)[:3], \
                   B.smooth_track([(k[0], (*k[1][0], *k[1][1])) for k in track], f)[3:]
        M = trs(loc, rot)
        miss = Vector((0, 0, 0))
        for side, (p, n) in grips.items():
            target = M @ (Vector(p) + Vector(n) * STANDOFF)
            x, err = solve_arm(rig, side, target, curl, hug, guess[side])
            guess[side] = x
            B.key_arm(rig, side, f, out=x[0], fwd=x[1], inward=x[2], curl=curl, hug=hug, slide=x[3])
            miss += err
        miss /= max(1, len(grips))
        worst = max(worst, miss.length)
        key_world(prop, f, Matrix.Translation(miss) @ M)          # the prop sits where the hands are
        if free:
            for side, k in free.items():
                B.key_arm(rig, side, f, **(k(f) if callable(k) else k))
    print(f'[{name}] largest move of the prop to meet the hands: {worst:.3f}')


def shoulder_z():
    return B.ZT - B.ARM['s'] * B.BODY_H


def front_y(s):
    """The front surface of the shell at s (share of body height from the top), as a y coordinate."""
    return -B.half_width(s * 125) * B.DEPTH


def scene_weeks(rig, M):
    """Mug in his right mitten; lifts it, nods into a sip, lowers it. Steam drifts up."""
    act = B.new_action(rig, 'weeks')
    for f in range(1, N + 2, 4): breathe(rig, f)
    for f, x in ((1, 0), (28, 0), (38, 9), (54, 9), (64, 2), (72, 0), (N + 1, 0)):
        B.joint(rig, 'head', f, x=x, y=2 if 36 < f < 60 else 0)
    blink((84,))
    g, steam = mug(M); g.scale = (2.0, 2.0, 2.0)
    zs = shoulder_z(); yf = front_y(0.62)
    HOLD = ((-0.42, yf - 0.4, zs - 0.05), (0, 0, -40))
    SIP = ((-0.26, yf - 0.3, zs + 0.3), (-22, 0, -30))
    track = [(1, HOLD), (26, HOLD), (36, SIP), (54, SIP), (66, HOLD), (N + 1, HOLD)]
    held(rig, 'weeks', g, track, {'R': ((-0.26, 0, -0.03), (-1, 0, 0))}, curl=26, hug=24,
         free={'L': lambda f: dict(out=5, fwd=10 + 3 * math.sin(2 * math.pi * f / N), curl=6)})
    B.stash(rig, act, 'weeks')
    for i, st in enumerate(steam):
        obj_action(st, 'weeks')
        # Rising while he holds it; gone while it's at his mouth (he's drinking it), back after.
        for f, z, s in ((1, 0, 0.8), (24, 0.04, 1.0), (32, 0.05, 0.0), (60, 0.0, 0.0), (70, 0.0, 0.6), (N + 1, 0, 0.8)):
            st.location.z = 0.2 + z + i * 0.01; st.scale = (0.7 * max(s, 0.01), 0.7 * max(s, 0.01), 0.6 * max(s, 0.01))
            st.keyframe_insert('location', frame=f); st.keyframe_insert('scale', frame=f)
    return [g] + steam


def scene_contact(rig, M):
    """The d20 cupped in both mittens; he looks at it, tosses it up a little, catches it."""
    act = B.new_action(rig, 'contact')
    for f in range(1, N + 2, 4): breathe(rig, f)
    for f, x in ((1, 8), (44, 8), (50, -4), (58, 6), (N + 1, 8)):
        B.joint(rig, 'head', f, x=x)
    blink((76,))
    die = d20(M); die.scale = (1.8, 1.8, 1.8)
    zs = shoulder_z(); yf = front_y(0.62); c = (0, yf - 0.42, zs + 0.02)
    track = [(1, (c, (0, 0, 0))), (40, (c, (0, 0, 40))), (44, ((c[0], c[1], c[2] + 0.04), (0, 0, 60))),
             (50, ((c[0], c[1], c[2] + 0.42), (40, 0, 200))), (56, ((c[0], c[1], c[2] + 0.02), (0, 0, 320))),
             (58, (c, (0, 0, 330))), (N + 1, (c, (0, 0, 360)))]
    die.rotation_mode = 'XYZ'
    # The mittens hold it below its equator; while it's in the air they stay where they caught it.
    bind_to(rig, die, 'root')
    hold_track = [(1, track[0][1]), (40, track[1][1]), (44, track[2][1]), (47, ((c[0], c[1], c[2] + 0.06), (0, 0, 80))),
                  (54, ((c[0], c[1], c[2] + 0.05), (0, 0, 300))), (58, track[5][1]), (N + 1, track[6][1])]
    held(rig, 'contact', die, hold_track, {'L': ((0.28, 0, -0.06), (1, 0, 0)), 'R': ((-0.28, 0, -0.06), (-1, 0, 0))},
         curl=30, hug=26)
    die.animation_data.action = bpy.data.actions.new('contact|Die')       # the die's own flight
    for f, (loc, rot) in track: key_world(die, f, trs(loc, rot))
    B.stash(rig, act, 'contact')
    return [die]


def scene_photos(rig, M):
    """Camera in both mittens, lens to the viewer; a click; lowered and tilted to check the shot."""
    act = B.new_action(rig, 'photos')
    for f in range(1, N + 2, 4): breathe(rig, f)
    for f, x in ((1, -2), (38, -2), (40, -4), (44, -2), (60, -2), (72, 10), (84, 10), (N + 1, -2)):
        B.joint(rig, 'head', f, x=x)
    cam = camera(M); cam.scale = (1.9, 1.9, 1.9)
    zs = shoulder_z(); yf = front_y(0.55)
    UP = ((0, yf - 0.38, zs + 0.22), (0, 0, 0)); CLICK = ((0, yf - 0.4, zs + 0.2), (-3, 0, 0))
    CHECK = ((0, yf - 0.36, zs - 0.08), (38, 0, 0))
    track = [(1, UP), (37, UP), (40, CLICK), (44, UP), (58, UP), (70, CHECK), (82, CHECK), (N + 1, UP)]
    held(rig, 'photos', cam, track, {'L': ((0.4, 0, 0), (1, 0, 0)), 'R': ((-0.4, 0, 0), (-1, 0, 0))}, curl=28, hug=26)
    B.stash(rig, act, 'photos')
    return [cam]


def scene_projects(rig, M):
    """The circuit board in his right mitten, the iron in his left; three dabs, a wisp of smoke, then a
    pleased look up."""
    act = B.new_action(rig, 'projects')
    for f in range(1, N + 2, 4): breathe(rig, f)
    for f, x, z in ((1, 9, 0), (40, 9, 0), (52, -2, -9), (78, -2, -9), (90, 9, 0), (N + 1, 9, 0)):
        B.joint(rig, 'head', f, x=x, z=z)
    blink((56,))
    iron, pcb, smoke = soldering(M)
    pcb.scale = (1.8, 1.8, 1.8); iron.scale = (1.6, 1.6, 1.6)
    zs = shoulder_z(); yf = front_y(0.62)
    BOARD = ((-0.32, yf - 0.46, zs - 0.26), (-48, 0, -10))
    held(rig, 'projects-board', pcb, [(1, BOARD), (N + 1, BOARD)], {'R': ((-0.21, 0, -0.02), (-1, 0, 0))}, curl=28, hug=20)
    # The iron: its tip on a pad, held at the grip; dabs lift it back along its own axis.
    Mb = trs(*BOARD)
    pad = Mb @ Vector((0.05 * 1.8, -0.02 * 1.8, -0.02 * 1.8))
    up = Vector((0.8, 0.05, 0.42)).normalized()                       # from the tip back to the grip: low, from his left
    q = up.to_track_quat('Z', 'Y').to_euler()
    def iron_at(lift):
        tip = pad + up * lift
        return (tuple(tip + up * (0.37 * 1.6)), tuple(math.degrees(a) for a in q))
    track = [(f, iron_at(l)) for f, l in ((1, 0.0), (10, 0.06), (14, 0.0), (22, 0.06), (26, 0.0), (34, 0.06), (38, 0.0),
                                           (50, 0.14), (84, 0.14), (N + 1, 0.0))]
    held(rig, 'projects-iron', iron, track, {'L': ((0.0, 0.0, 0.0), (0.4, -0.6, 0.0))}, curl=30, hug=12, step=2)
    B.stash(rig, act, 'projects')
    smoke.location = pad + Vector((0, -0.02, 0.05)); bind_to(rig, smoke, 'root')
    obj_action(smoke, 'projects')
    for f, s in ((1, 0.01), (12, 0.01), (20, 1.0), (40, 1.0), (48, 0.01), (N + 1, 0.01)):
        smoke.scale = (s, s, s); smoke.keyframe_insert('scale', frame=f)
    return [iron, pcb, smoke]


def typing(rig, name, keys_center, width):
    """Both mittens on the keys; they tap in turns, pause, and glance up (head keys done by caller)."""
    taps = {}
    for f in range(1, N + 2, 3):
        pause = 40 <= f <= 62
        for side, sx, ph in (('L', 1, 0), ('R', -1, 1)):
            lift = 0.0 if pause else 0.05 * ((f // 3 + ph) % 2)
            taps.setdefault(side, []).append((f, Vector(keys_center) + Vector((sx * width, 0.02, STANDOFF * 0.9 + lift))))
    guess = {'L': [4.0, 30.0, 25.0, 25.0], 'R': [4.0, 30.0, 25.0, 25.0]}
    worst = 0.0
    for side, seq in taps.items():
        for f, target in seq:
            x, err = solve_arm(rig, side, target, 20, 10, guess[side]); guess[side] = x
            B.key_arm(rig, side, f, out=x[0], fwd=x[1], inward=x[2], curl=20, hug=10, slide=x[3])
            worst = max(worst, err.length)
    print(f'[{name}] largest gap between a mitten and the keys: {worst:.3f}')


def reach_point(rig, f, sides=('L', 'R')):
    """Where the palms land with the arms resting forward, at frame f (used to place keyboards)."""
    bpy.context.scene.frame_set(f)
    for s in sides: pose_arm(rig, s, 4, 34, 28, 20, 10, 30)
    bpy.context.view_layer.update()
    return [palm(rig, s) for s in sides]


def scene_blog(rig, M):
    """Sitting with a laptop just in front of him, typing on its keys; a pause and a glance up."""
    act = B.new_action(rig, 'blog')
    for f in (1, N + 1): sit(rig, f)
    for f, x, z in ((1, 7, 0), (38, 7, 0), (46, -3, -10), (58, -3, -10), (66, 7, 0), (N + 1, 7, 0)):
        B.joint(rig, 'head', f, x=x, z=z)
    for f in range(1, N + 2, 4): breathe(rig, f)
    blink((50,))
    pl, pr = reach_point(rig, 1)
    mid = (pl + pr) / 2
    lap = laptop(M); lap.scale = (1.6, 1.6, 1.6)
    keys_top = Vector((mid.x, mid.y + 0.04, mid.z - STANDOFF * 0.9))
    lap.location = keys_top - Vector((0, 0.02 * 1.6, 0.022 * 1.6))
    bind_to(rig, lap, 'root')
    typing(rig, 'blog', keys_top, 0.17)
    B.stash(rig, act, 'blog')
    return [lap]


def keyboard(M):
    kb = rbox('TermKeys', (0.62, 0.24, 0.06), 0.02, M['cream'])
    keys = rbox('TermKeyTops', (0.54, 0.16, 0.012), 0.004, M['paper']); keys.location.z = 0.036
    return group('Keyboard', [kb, keys])


def scene_404(rig, M):
    """Sitting at a little retro terminal, typing on its keyboard, then turning to the viewer: oh."""
    act = B.new_action(rig, '404')
    for f in (1, N + 1): sit(rig, f)
    for f, x, z in ((1, 6, 6), (48, 6, 6), (56, -4, -16), (86, -4, -16), (N + 1, 6, 6)):
        B.joint(rig, 'head', f, x=x, z=z)
    for f in range(1, N + 2, 4): breathe(rig, f)
    pl, pr = reach_point(rig, 1)
    mid = (pl + pr) / 2
    kb = keyboard(M); kb.scale = (1.3, 1.3, 1.3)
    keys_top = Vector((mid.x, mid.y + 0.02, mid.z - STANDOFF * 0.9))
    kb.location = keys_top - Vector((0, 0, 0.042 * 1.3))
    bind_to(rig, kb, 'root')
    t = terminal(M)
    for o in list(t.children):
        if o.name.startswith('TermKey'): bpy.data.objects.remove(o)
    t.scale = (1.4, 1.4, 1.4); t.location = (mid.x - 0.9, mid.y - 0.35, 0.36); t.rotation_euler = (0, 0, math.radians(32))
    bind_to(rig, t, 'root')
    typing(rig, '404', keys_top, 0.17)
    # He stops typing to turn to the viewer: lift the mittens a little while he looks.
    B.stash(rig, act, '404')
    return [t, kb]


def scene_essay(rig, M):
    """Sitting, an open book in both mittens with its pages toward him; small nods as he reads."""
    act = B.new_action(rig, 'essay')
    for f in (1, N + 1): sit(rig, f)
    for f, x in ((1, 9), (24, 10), (48, 8), (72, 10), (N + 1, 9)):
        B.joint(rig, 'head', f, x=x)
    for f in range(1, N + 2, 4): breathe(rig, f)
    blink((60,))
    bk = book_open(M, 'navy'); bk.scale = (1.7, 1.7, 1.7)
    bpy.context.scene.frame_set(1); bpy.context.view_layer.update()
    sh = [rig.matrix_world @ rig.pose.bones[f'arm_upper.{s}'].head for s in 'LR']
    c = (0, front_y(0.6) - 0.5, (sh[0].z + sh[1].z) / 2 + 0.05)
    BOOK = (c, (-35, 0, 180))                            # pages toward him, tilted up to his eyes
    BOOK2 = ((c[0], c[1], c[2] + 0.02), (-33, 0, 180))
    w = 0.42                                             # the outer bottom corners, in the book's frame
    held(rig, 'essay', bk, [(1, BOOK), (48, BOOK2), (N + 1, BOOK)],
         {'L': ((-w, 0, -0.25), (-0.6, 0, -0.8)), 'R': ((w, 0, -0.25), (0.6, 0, -0.8))}, curl=28, hug=24)
    B.stash(rig, act, 'essay')
    return [bk]


def scene_rotation_empty(rig, M):
    """Carrying a stack of books against his chest, a mitten on each side; it sways with his weight."""
    act = B.new_action(rig, 'rotation_empty')
    for f in range(1, N + 2, 4):
        s = math.sin(2 * math.pi * (f - 1) / N)
        B.key_body(rig, f, lean_y=1.2 * s); breathe(rig, f)
    for f, x, z in ((1, 2, -4), (48, 3, 4), (N + 1, 2, -4)): B.joint(rig, 'head', f, x=x, z=z)
    st = book_stack(M); st.scale = (1.7, 1.7, 1.7)
    zs = shoulder_z(); yf = front_y(0.66)
    track = [(f, ((0.02 * math.sin(2 * math.pi * (f - 1) / N), yf - 0.36, zs - 0.18), (0, 2 * math.sin(2 * math.pi * (f - 1) / N), 0)))
             for f in range(1, N + 2, 12)]
    held(rig, 'rotation_empty', st, track, {'L': ((0.25, 0, 0.08), (1, 0, 0)), 'R': ((-0.25, 0, 0.08), (-1, 0, 0))}, curl=26, hug=26)
    B.stash(rig, act, 'rotation_empty')
    return [st]


def headphones(M):
    """Fitted to his dome: the band follows the shell's own curve a little above it, the cups sit on
    the sides at eye height. Built in the body's frame (z = height above the ground)."""
    zc = B.ZT - 0.33 * B.BODY_H
    def hw_at(z): return B.half_width((B.ZT - z) / B.BODY_H * 125)
    cups = []
    for sx in (1, -1):
        x = hw_at(zc) + 0.05
        c = cyl(f'Cup{sx}', 0.17, 0.11, M['graphite'], bevel=0.03); c.rotation_euler = (0, math.radians(90), 0)
        c.location = (sx * (x + 0.05), 0, zc); cups.append(c)
        pad = ball(f'Pad{sx}', 0.15, M['graphite'], (0.4, 1, 1)); pad.location = (sx * x, 0, zc); cups.append(pad)
    # Offset the dome's own profile outward along its normal, so the band hugs it evenly over the top.
    zs_ = np.linspace(zc + 0.12, B.ZT, 40)
    prof = [(hw_at(z), z) for z in zs_] + [(0.0, B.ZT)]
    pts = []
    for i in range(len(prof)):
        x0, z0 = prof[max(0, i - 1)]; x1, z1 = prof[min(len(prof) - 1, i + 1)]
        tx, tz = x1 - x0, z1 - z0; L = math.hypot(tx, tz) or 1
        nx, nz = tz / L, -tx / L                                   # outward (to +x, up)
        if nx < 0: nx, nz = -nx, -nz
        pts.append((prof[i][0] + 0.05 * nx, 0, prof[i][1] + 0.05 * nz))
    pts[-1] = (0.0, 0, B.ZT + 0.05)
    band_pts = pts + [(-x, y, z) for x, y, z in reversed(pts[:-1])]
    band = tube('Band', band_pts, 0.05, M['graphite'])
    return group('Headphones', cups + [band])


def scene_rotation(rig, M):
    """Headphones on, eyes shut, bobbing to the beat (96 bpm: a beat every 15 frames)."""
    act = B.new_action(rig, 'rotation')
    beat = 15
    for f in range(1, N + 2, 3):
        ph = ((f - 1) % beat) / beat
        nod = 3.5 * math.exp(-((ph - 0.1) / 0.18) ** 2)
        sway = math.sin(2 * math.pi * (f - 1) / (2 * beat * 3.2))
        B.joint(rig, 'head', f, x=nod, y=2.5 * sway)
        B.key_body(rig, f, lean_y=1.5 * sway, bob=-0.01 * math.exp(-((ph - 0.12) / 0.2) ** 2))
        for side, sx in (('L', 1), ('R', -1)):
            hold(rig, f, side, out=4 + 2 * sway * sx, fwd=4 * sway * sx)
    B.stash(rig, act, 'rotation')
    B.use_move('rotation'); bpy.context.scene.frame_set(1)
    hp = headphones(M)
    bind_to(rig, hp, 'head')
    return [hp]



SCENES = {   # name: (builder, face, camera view)
    'weeks': (scene_weeks, 'sip'), 'blog': (scene_blog, 'muse'), 'projects': (scene_projects, 'muse'),
    'photos': (scene_photos, 'wink'), 'rotation': (scene_rotation, 'content'), 'contact': (scene_contact, 'muse'),
    '404': (scene_404, 'surprised'), 'empty': (scene_empty, 'happy'), 'essay': (scene_essay, 'muse'),
    'sent': (scene_sent, 'happy'), 'rotation_empty': (scene_rotation_empty, 'smile'),
}


def build_scene(name):
    fn, face = SCENES[name]
    B.POSES[f'scene_{name}'] = {'face': face}
    rig = B.build(f'scene_{name}', with_anims=False)
    rig.animation_data_create()
    M = mats()
    props = fn(rig, M)
    B.use_move(name)
    for ob in bpy.data.objects:                 # props that carry their own animation for this scene
        if ob.animation_data and ob.animation_data.action is None:
            ob.animation_data.action = bpy.data.actions.get(f'{name}|{ob.name}')
    return rig


if __name__ == '__main__':
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else sys.argv[1:]
    ap = argparse.ArgumentParser()
    ap.add_argument('--scene'); ap.add_argument('--list', action='store_true')
    ap.add_argument('--frame', type=int); ap.add_argument('--step', type=int, default=1); ap.add_argument('--first', type=int, default=1)
    ap.add_argument('--view', type=float, default=-18); ap.add_argument('--elev', type=float, default=7)
    ap.add_argument('--lens', type=float, default=60); ap.add_argument('--dist', type=float, default=7.6)
    ap.add_argument('--target', type=float, default=1.55); ap.add_argument('--size', type=int, default=760)
    ap.add_argument('--samples', type=int, default=18); ap.add_argument('--out')
    a = ap.parse_args(argv)
    if a.list:
        print('\n'.join(SCENES)); sys.exit()
    rig = build_scene(a.scene)
    B.stage(a.view, a.elev, a.size, a.samples, dark=True, lens=a.lens, dist=a.dist, target=a.target)
    sc = bpy.context.scene
    frames = [a.frame] if a.frame else range(a.first, N + 1, a.step)
    for f in frames:
        sc.frame_set(f); sc.render.filepath = a.out.replace('#', f'{f:03d}')
        bpy.ops.render.render(write_still=True)

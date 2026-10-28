"""Props for the kitchens: taps, boards, ceramics, glass, fruit, plants, books, lamps.
Each returns a list of objects. Sizes in metres, z = the surface it stands on."""
import math
import random
import bpy
from mathutils import Vector, Matrix
from . import geo, mats


def _join(objs, name):
    """Join objects into one (keeps the scene light)."""
    objs = [o for o in objs if o is not None]
    if len(objs) <= 1:
        return objs
    ctx = bpy.context
    for o in ctx.view_layer.objects:
        o.select_set(False)
    for o in objs:
        if o.name not in ctx.view_layer.objects:
            continue
        o.select_set(True)
    ctx.view_layer.objects.active = objs[0]
    try:
        bpy.ops.object.join()
    except Exception:
        return objs
    objs[0].name = name
    return [objs[0]]


def rest(objs):
    """Mark objects as things that rest on a surface, for physics.settle (taps, handles and lamps are never marked)."""
    for o in objs:
        if o is not None and hasattr(o, "keys"):
            o["rest"] = 1
    return objs


def place(objs, loc=(0, 0, 0), rot=0.0, pivot=(0, 0, 0)):
    """Rotate a group about z round `pivot` and move it."""
    c, s = math.cos(rot), math.sin(rot)
    for o in objs:
        x, y, z = o.location
        # objects built in place have their origin at the world origin; move their mesh instead
        if o.type == 'MESH' and o.location.length < 1e-9 and o.rotation_euler.z == 0:
            mw = Matrix.Translation(Vector(loc)) @ Matrix.Translation(Vector(pivot)) @ Matrix.Rotation(rot, 4, 'Z') @ Matrix.Translation(-Vector(pivot))
            o.data.transform(mw)
        else:
            px, py = x - pivot[0], y - pivot[1]
            o.location = (pivot[0] + px * c - py * s + loc[0], pivot[1] + px * s + py * c + loc[1], z + loc[2])
            o.rotation_euler.z += rot
    return objs


# ── taps ────────────────────────────────────────────────────────────────────

def faucet_pulldown(name, x, y, z, height=0.38, reach=0.2, mat=None, col=None, r=0.0125, head_len=0.085, turn=0.0):
    """A pull-down tap: round base, tall column, an arc forward and the spray head hanging down."""
    objs = []
    objs.append(geo.lathe([(0.0, 0.0), (0.026, 0.0), (0.026, 0.006), (0.022, 0.012), (0.0, 0.012)], n=48, name=name + "_base", mat=mat, collection=col, cx=x, cy=y, z=z))
    R = reach / 2
    col_top = z + height - R
    pts = [(x, y, z + 0.01), (x, y, col_top)]
    for k in range(1, 29):
        a = math.pi * k / 28
        pts.append((x, y - R + R * math.cos(a), col_top + R * math.sin(a)))
    end = pts[-1]
    objs.append(geo.tube(pts, r, 28, name=name + "_neck", mat=mat, collection=col))
    # spray head
    hx, hy, hz = end
    objs.append(geo.lathe([(0.0, 0.0), (r * 1.25, 0.002), (r * 1.3, 0.02), (r * 1.18, head_len), (r * 1.0, head_len + 0.004)], n=40, name=name + "_head", mat=mat, collection=col, cx=hx, cy=hy, z=hz - head_len - 0.002))
    objs.append(geo.cylinder(hx, hy, hz - head_len - 0.003, hz - head_len - 0.0015, r * 1.05, 32, name=name + "_face", mat=mats.metal("gunmetal"), collection=col))
    # side lever
    objs.append(geo.cylinder(x + r * 0.9, y, z + 0.11, z + 0.13, 0.0095, 24, name=name + "_lever_hub", mat=mat, collection=col, bevel=0.002))
    objs.append(geo.tube([(x + r + 0.008, y, z + 0.12), (x + r + 0.058, y + 0.004, z + 0.128)], 0.004, 12, name=name + "_lever", mat=mat, collection=col))
    if turn:
        place(objs, rot=turn, pivot=(x, y, z))
    return objs


def faucet_gooseneck(name, x, y, z, height=0.36, reach=0.21, mat=None, col=None, r=0.011, lever=True, turn=0.0):
    """A gooseneck tap: slim column, a half-circle spout, a lever on the side of the body."""
    objs = []
    objs.append(geo.lathe([(0.0, 0.0), (0.024, 0.0), (0.024, 0.004), (0.019, 0.010), (0.0, 0.010)], n=48, name=name + "_base", mat=mat, collection=col, cx=x, cy=y, z=z))
    objs.append(geo.cylinder(x, y, z + 0.008, z + 0.15, 0.019, 40, name=name + "_body", mat=mat, collection=col, bevel=0.002))
    R = reach / 2
    col_top = z + height - R
    pts = [(x, y, z + 0.14), (x, y, col_top)]
    for k in range(1, 29):
        a = math.pi * k / 28
        pts.append((x, y - R + R * math.cos(a), col_top + R * math.sin(a)))
    ex, ey, ez = pts[-1]
    pts.append((ex, ey, ez - 0.03))
    objs.append(geo.tube(pts, r, 28, name=name + "_neck", mat=mat, collection=col))
    objs.append(geo.cylinder(ex, ey, ez - 0.034, ez - 0.03, r * 0.8, 24, name=name + "_aer", mat=mats.metal("gunmetal"), collection=col))
    if lever:
        objs.append(geo.tube([(x + 0.017, y, z + 0.115), (x + 0.03, y, z + 0.12), (x + 0.085, y + 0.006, z + 0.135)], 0.0045, 12, name=name + "_lever", mat=mat, collection=col))
    if turn:
        place(objs, rot=turn, pivot=(x, y, z))
    return objs


def faucet_square(name, x, y, z, height=0.30, reach=0.22, mat=None, col=None, turn=0.0):
    """A square-section tap: column, a straight spout out at the top, a flat lever on top."""
    objs = []
    s = 0.0155
    objs.append(geo.box(x - 0.024, y - 0.024, z, x + 0.024, y + 0.024, z + 0.006, name=name + "_base", mat=mat, collection=col, bevel=0.0015))
    objs.append(geo.box(x - s, y - s, z + 0.005, x + s, y + s, z + height, name=name + "_col", mat=mat, collection=col, bevel=0.0025))
    objs.append(geo.box(x - 0.011, y - reach, z + height - 0.03, x + 0.011, y - s + 0.002, z + height - 0.006, name=name + "_spout", mat=mat, collection=col, bevel=0.0025))
    objs.append(geo.box(x - 0.008, y - reach + 0.003, z + height - 0.0315, x + 0.008, y - reach + 0.025, z + height - 0.029, name=name + "_aer", mat=mats.metal("gunmetal"), collection=col))
    objs.append(geo.box(x + s - 0.002, y - 0.006, z + height - 0.012, x + s + 0.07, y + 0.006, z + height - 0.004, name=name + "_lever", mat=mat, collection=col, bevel=0.002))
    if turn:
        place(objs, rot=turn, pivot=(x, y, z))
    return objs


def faucet_bridge(name, x, y, z, mat=None, col=None, spread=0.22, height=0.30, reach=0.22, turn=0.0):
    """A classic bridge tap: two pillars with cross handles, a bridge, a swan-neck spout."""
    objs = []
    hx = spread / 2
    for sx in (-1, 1):
        cx = x + sx * hx
        objs.append(geo.lathe([(0.0, 0.0), (0.028, 0.0), (0.028, 0.006), (0.02, 0.012), (0.016, 0.02), (0.016, 0.09), (0.019, 0.1), (0.0, 0.1)], n=40, name=name + "_pillar", mat=mat, collection=col, cx=cx, cy=y, z=z))
        objs.append(geo.cylinder(cx, y, z + 0.1, z + 0.125, 0.008, 24, name=name + "_stem", mat=mat, collection=col))
        for a in (0, math.pi / 2):
            objs.append(geo.tube([(cx - 0.035 * math.cos(a), y - 0.035 * math.sin(a), z + 0.13), (cx + 0.035 * math.cos(a), y + 0.035 * math.sin(a), z + 0.13)], 0.0045, 12, name=name + "_cross", mat=mat, collection=col))
        objs.append(geo.lathe([(0.0, 0.0), (0.009, 0.0), (0.012, 0.012), (0.0, 0.016)], n=24, name=name + "_cap", mat=mats.ceramic((0.9, 0.9, 0.88)), collection=col, cx=cx, cy=y, z=z + 0.128))
    objs.append(geo.tube([(x - hx, y, z + 0.07), (x + hx, y, z + 0.07)], 0.011, 20, name=name + "_bridge", mat=mat, collection=col))
    R = reach / 2
    pts = [(x, y, z + 0.07), (x, y, z + height - R)]
    for k in range(1, 25):
        a = math.pi * k / 24
        pts.append((x, y - R + R * math.cos(a), z + height - R + R * math.sin(a)))
    ex, ey, ez = pts[-1]
    pts.append((ex, ey, ez - 0.025))
    objs.append(geo.tube(pts, 0.0105, 24, name=name + "_spout", mat=mat, collection=col))
    if turn:
        place(objs, rot=turn, pivot=(x, y, z))
    return objs


def faucet_wall(name, x, y, z, mat=None, col=None, reach=0.24, spread=0.2):
    """A wall-mounted tap on the splashback: a plate, a straight spout, two lever handles. y = the wall."""
    objs = []
    ob = geo.cylinder(0, 0, 0, 0.012, 0.03, 40, name=name + "_rose", mat=mat, collection=col, bevel=0.002)
    ob.rotation_euler = (math.pi / 2, 0, 0)
    ob.location = (x, y, z)
    objs.append(ob)
    objs.append(geo.tube([(x, y - 0.01, z), (x, y - reach, z - 0.004), (x, y - reach - 0.006, z - 0.03)], 0.0105, 20, name=name + "_spout", mat=mat, collection=col))
    for sx in (-1, 1):
        hx = x + sx * spread / 2
        ob = geo.cylinder(0, 0, 0, 0.016, 0.024, 32, name=name + "_hrose", mat=mat, collection=col, bevel=0.002)
        ob.rotation_euler = (math.pi / 2, 0, 0)
        ob.location = (hx, y, z)
        objs.append(ob)
        objs.append(geo.tube([(hx, y - 0.016, z), (hx, y - 0.03, z), (hx + sx * 0.0, y - 0.03, z + 0.075)], 0.0055, 12, name=name + "_lever", mat=mat, collection=col))
    return objs


# ── boards, ceramics, glass ────────────────────────────────────────────────

def board(name, x, y, z, w=0.42, d=0.26, t=0.022, rot=0.0, wood="oak", col=None, handle=True, round_=False):
    m = mats.wood(wood, along='X', rough=0.55, seed=hash(name) % 17)
    if round_:
        objs = [geo.cylinder(0, 0, 0, t, w / 2, 72, name=name, mat=m, collection=col, bevel=0.003)]
    else:
        pts = geo.rrect(-w / 2, w / 2, -d / 2, d / 2, 0.012, n_corner=6, n_side=(8, 6))
        if handle:
            # a tab with a hole at one end
            pts = geo.rrect(-w / 2, w / 2, -d / 2, d / 2, 0.012, n_corner=6, n_side=(8, 6))
        objs = [geo.slab(pts, [geo.circle(w / 2 - 0.03, 0, 0.011, 24)] if handle else [], 0.0, t, name=name, mat=m, collection=col, bevel=0.0025)]
    for o in objs:
        o.location = (x, y, z)
        o.rotation_euler = (0, 0, rot)
    return rest(objs)


def vessel(name, x, y, z, profile, mat, col=None, n=64, thick=0.004):
    """A turned vessel (bowl, vase, jar, cup) from an outside profile [(r, h)…] starting at the foot.
    The inside follows the outside, `thick` in."""
    outer = list(profile)
    inner = [(max(0.0, r - thick), h) for (r, h) in reversed(outer[1:])]
    inner[-1] = (0.0, outer[0][1] + thick) if inner else (0, thick)
    # a rounded lip, from the outer rim over to the inner one, as thrown or blown things have
    (ro, ho), (ri, hi) = outer[-1], inner[0]
    lip = [(ro - (ro - ri) * 0.12, ho + thick * 0.3), (ro - (ro - ri) * 0.5, ho + thick * 0.45), (ri + (ro - ri) * 0.12, hi + thick * 0.3)]
    prof = [(0.0, outer[0][1])] + outer + lip + inner
    ob = geo.lathe(prof, n=n, name=name, mat=mat, collection=col, cx=0, cy=0, z=0)
    ob.location = (x, y, z)
    return rest([ob])


def bowl(name, x, y, z, r=0.12, h=0.075, mat=None, col=None):
    prof = [(r * 0.38, 0.0), (r * 0.42, 0.006), (r * 0.7, h * 0.35), (r * 0.92, h * 0.75), (r, h)]
    return vessel(name, x, y, z, prof, mat, col, thick=0.005)


def vase(name, x, y, z, h=0.28, r=0.07, neck=0.03, mat=None, col=None, style=0):
    if style == 0:  # bottle vase
        prof = [(r * 0.75, 0.0), (r, h * 0.2), (r * 0.95, h * 0.5), (neck * 1.2, h * 0.82), (neck, h * 0.92), (neck * 1.15, h)]
    elif style == 1:  # cylinder
        prof = [(r * 0.95, 0.0), (r, 0.01), (r, h * 0.98), (r * 0.97, h)]
    else:  # amphora
        prof = [(r * 0.5, 0.0), (r * 0.85, h * 0.25), (r, h * 0.5), (r * 0.7, h * 0.78), (neck, h * 0.9), (neck * 1.3, h)]
    return vessel(name, x, y, z, prof, mat, col, thick=0.004)


def jar(name, x, y, z, r=0.05, h=0.16, mat=None, lid=None, col=None):
    objs = vessel(name, x, y, z, [(r * 0.97, 0.0), (r, 0.006), (r, h * 0.97), (r * 0.98, h)], mat, col, thick=0.003)
    if lid is not None:
        objs.append(geo.lathe([(0.0, 0.0), (r * 1.02, 0.0), (r * 1.02, 0.014), (r * 0.6, 0.018), (0.15 * r, 0.03), (0.0, 0.032)], n=48, name=name + "_lid", mat=lid, collection=col, cx=x, cy=y, z=z + h - 0.004))
    return objs


def bottle(name, x, y, z, h=0.26, r=0.033, glass=None, liquid=None, cap=None, col=None):
    z += 0.0006
    gm = glass or mats.glass((0.9, 0.95, 0.9))
    prof = [(r * 0.95, 0.0), (r, 0.004), (r, h * 0.62), (r * 0.45, h * 0.78), (r * 0.32, h * 0.86), (r * 0.32, h * 0.97), (r * 0.36, h)]
    objs = vessel(name, x, y, z, prof, gm, col, thick=0.0025)
    if liquid is not None:
        objs.append(geo.lathe([(0.0, 0.003), (r - 0.003, 0.004), (r - 0.003, h * 0.5), (0.0, h * 0.5)], n=48, name=name + "_liq", mat=liquid, collection=col, cx=x, cy=y, z=z))
    if cap is not None:
        objs.append(geo.cylinder(x, y, z + h - 0.002, z + h + 0.02, r * 0.38, 24, name=name + "_cap", mat=cap, collection=col, bevel=0.002))
    return objs


def soap_pump(name, x, y, z, mat=None, col=None, h=0.17, r=0.035, pump=None):
    objs = vessel(name, x, y, z, [(r * 0.96, 0.0), (r, 0.004), (r, h * 0.9), (r * 0.5, h * 0.98), (r * 0.42, h)], mat, col, thick=0.003)
    pm = pump or mats.metal("brass")
    objs.append(geo.cylinder(x, y, z + h, z + h + 0.03, 0.009, 24, name=name + "_stem", mat=pm, collection=col))
    objs.append(geo.box(x - 0.008, y - 0.045, z + h + 0.03, x + 0.008, y + 0.008, z + h + 0.042, name=name + "_head", mat=pm, collection=col, bevel=0.003))
    return objs


def cup(name, x, y, z, r=0.04, h=0.085, mat=None, col=None, handle=True):
    objs = vessel(name, x, y, z, [(r * 0.8, 0.0), (r * 0.85, 0.005), (r, h)], mat, col, thick=0.003)
    if handle:
        objs.append(geo.tube([(x + r * 0.9, y, z + h * 0.8), (x + r + 0.022, y, z + h * 0.7), (x + r + 0.022, y, z + h * 0.32), (x + r * 0.85, y, z + h * 0.25)], 0.004, 12, name=name + "_handle", mat=mat, collection=col))
    return objs


def plate_stack(name, x, y, z, r=0.13, n=4, mat=None, col=None):
    objs = []
    for i in range(n):
        # one group (name_0, name_1 …), nested as plates sit: a plate's thickness plus its rim's slope apart
        objs += vessel(f"{name}_{i}", x, y, z + i * 0.0068, [(r * 0.55, 0.0), (r * 0.6, 0.004), (r * 0.82, 0.008), (r, 0.018)], mat, col, thick=0.0035)
    return objs


def wine_glass(name, x, y, z, col=None):
    z += 0.0006
    gm = mats.glass()
    prof = [(0.0, 0.0), (0.038, 0.0), (0.038, 0.002), (0.004, 0.006), (0.0035, 0.10), (0.022, 0.115), (0.04, 0.15), (0.042, 0.19), (0.04, 0.215)]
    ob = geo.lathe(prof + [(0.038, 0.215), (0.039, 0.19), (0.037, 0.152), (0.02, 0.12), (0.0, 0.112)], n=48, name=name, mat=gm, collection=col, cx=x, cy=y, z=z)
    return rest([ob])


def tumbler(name, x, y, z, r=0.036, h=0.095, col=None, mat=None):
    z += 0.0006
    return vessel(name, x, y, z, [(r * 0.94, 0.0), (r, h)], mat or mats.glass(), col, thick=0.0025)


# ── food, plants ───────────────────────────────────────────────────────────

def _ellipsoid(name, x, y, z, rx, ry, rz, mat, col, seg=32, ring=16):
    me = bpy.data.meshes.new(name)
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=ring, radius=1.0)
    for v in bm.verts:
        v.co.x *= rx
        v.co.y *= ry
        v.co.z *= rz
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    ob = geo.new_object(name, me, col, mat)
    ob.location = (x, y, z)
    return ob


# how far each fruit reaches from its middle, along and across its length, at the size fruit_bowl sets it (s 0.85,
# apples 0.9): a lemon's tip included
FRUIT_REACH = {"lemon": (0.049 * 0.85, 0.03 * 0.85), "lime": (0.03 * 0.85, 0.028 * 0.85), "orange": (0.04 * 0.85, 0.04 * 0.85),
               "apple": (0.04 * 0.9, 0.04 * 0.9), "pear": (0.038, 0.038)}


def lemon(name, x, y, z, s=1.0, col=None, kind="lemon", rot=0.0):
    if kind == "lemon":
        m = mats.fruit((0.80, 0.56, 0.04), 0.35, 0.25, 420)
        ob = _ellipsoid(name, x, y, z + 0.03 * s, 0.042 * s, 0.03 * s, 0.03 * s, m, col)
        ob.rotation_euler = (0, 0, rot)
        tip = _ellipsoid(name + "_tip", 0, 0, 0, 0.006 * s, 0.005 * s, 0.005 * s, m, col, 12, 8)
        tip.location = (x + 0.043 * s * math.cos(rot), y + 0.043 * s * math.sin(rot), z + 0.03 * s)
        return rest([ob, tip])
    if kind == "lime":
        m = mats.fruit((0.12, 0.30, 0.03), 0.4, 0.2, 420)
        return rest([_ellipsoid(name, x, y, z + 0.026 * s, 0.03 * s, 0.028 * s, 0.026 * s, m, col)])
    if kind == "orange":
        m = mats.fruit((0.82, 0.30, 0.02), 0.45, 0.35, 380)
        return rest([_ellipsoid(name, x, y, z + 0.037 * s, 0.04 * s, 0.04 * s, 0.037 * s, m, col)])
    if kind == "apple":
        m = mats.fruit((0.38, 0.55, 0.08) if s > 0 else (0.5, 0.05, 0.03), 0.3, 0.05, 200)
        ob = _ellipsoid(name, x, y, z + 0.036 * abs(s), 0.04 * abs(s), 0.04 * abs(s), 0.036 * abs(s), m, col)
        stem = geo.tube([(x, y, z + 0.066 * abs(s)), (x + 0.004, y, z + 0.082 * abs(s))], 0.0018, 8, name=name + "_stem", mat=mats.wood("walnut"), collection=col)
        return rest([ob, stem])
    if kind == "pear":
        m = mats.fruit((0.55, 0.52, 0.12), 0.45, 0.15, 300)
        ob = geo.lathe([(0.0, 0.0), (0.03, 0.006), (0.038, 0.03), (0.03, 0.06), (0.018, 0.085), (0.008, 0.1), (0.0, 0.103)], n=32, name=name, mat=m, collection=col, cx=x, cy=y, z=z)
        return rest([ob])
    raise ValueError(kind)


def _leaf(bm, p, d, side, ll, ww, fold=0.25, droop=0.15, shape=0.5):
    """One leaf into a bmesh: a blade from p along d, `side` across it, folded along the midrib and drooping toward
    the tip. shape: where along the blade it is widest (0.35 olive .. 0.55 bay)."""
    up = side.cross(d).normalized()
    if up.z < 0:
        up = -up
    def at(t, k):   # k: -1 .. 1 across the blade
        w = ww * (math.sin(math.pi * min(1.0, t / (2 * shape))) if t < shape else math.cos(math.pi / 2 * (t - shape) / (1 - shape)))
        c = p + d * (ll * t) - up * (droop * ll * t * t)
        return c + side * (k * w / 2) + up * (fold * ww * (1 - abs(k)) * 0.5)
    ts = (0.0, 0.25, 0.5, 0.75, 1.0)
    rows = []
    for t in ts:
        if t in (0.0, 1.0):
            rows.append([bm.verts.new(at(t, 0.0))])
        else:
            rows.append([bm.verts.new(at(t, k)) for k in (-1.0, 0.0, 1.0)])
    base, tip = rows[0][0], rows[-1][0]
    bm.faces.new((base, rows[1][0], rows[1][1]))
    bm.faces.new((base, rows[1][1], rows[1][2]))
    for a, b in ((rows[1], rows[2]), (rows[2], rows[3])):
        bm.faces.new((a[0], b[0], b[1], a[1]))
        bm.faces.new((a[1], b[1], b[2], a[2]))
    bm.faces.new((rows[3][0], tip, rows[3][1]))
    bm.faces.new((rows[3][1], tip, rows[3][2]))


def branch(name, x, y, z, height=0.55, spread=0.3, leaf_col=(0.16, 0.2, 0.12), n_leaves=90, seed=1, col=None, leaf_len=0.05, leaf_w=0.012, stems=3, lean=0.0,
           wall_y=None):
    """Olive/eucalyptus-like branches in a vase: thin stems, many small leaves. wall_y: a wall behind, which the
    stems and leaves lean away from."""
    rnd = random.Random(seed)
    stem_m = mats.wood("walnut", rough=0.7)
    leaf_m = mats.leaf(leaf_col, 0.5)
    objs = []
    import bmesh
    me = bpy.data.meshes.new(name + "_leaves")
    bm = bmesh.new()
    for s in range(stems):
        a = rnd.uniform(0, 2 * math.pi)
        if wall_y is not None and wall_y - y < 0.45:
            a = rnd.uniform(math.pi * 1.1, math.pi * 1.9)      # toward the room
        tilt = rnd.uniform(0.15, 0.45)
        pts = []
        cx, cy, cz = x, y, z
        dx, dy = math.cos(a) * tilt + lean, math.sin(a) * tilt
        L = height * rnd.uniform(0.8, 1.05)
        for k in range(12):
            t = k / 11
            px = x + dx * L * t ** 1.4
            py = y + dy * L * t ** 1.4
            pz = z + L * t * (1 - 0.15 * t)
            pts.append((px, py, pz))
        objs.append(geo.tube(pts, 0.0022, 6, name=name + "_stem", mat=stem_m, collection=col))
        # leaves along the upper two thirds
        for i in range(n_leaves // stems):
            t = rnd.uniform(0.3, 1.0)
            idx = min(10, int(t * 11))
            p0 = Vector(pts[idx])
            p1 = Vector(pts[idx + 1])
            p = p0 + (p1 - p0) * rnd.random()
            ang = rnd.uniform(0, 2 * math.pi)
            up = rnd.uniform(-0.6, 0.6)
            d = Vector((math.cos(ang), math.sin(ang), up)).normalized()
            if wall_y is not None and p.y + d.y * leaf_len * 1.3 > wall_y - 0.012:
                d = Vector((d.x, -abs(d.y), d.z)).normalized()
            side = d.cross(Vector((0, 0, 1)))
            if side.length < 1e-3:
                side = Vector((1, 0, 0))
            side.normalize()
            ll = leaf_len * rnd.uniform(0.7, 1.2)
            ww = leaf_w * rnd.uniform(0.8, 1.2)
            _leaf(bm, p, d, side, ll, ww, fold=rnd.uniform(0.15, 0.35), droop=rnd.uniform(0.05, 0.25), shape=0.42)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    objs.append(geo.new_object(name + "_leaves", me, col, leaf_m))
    return objs


def herb_pot(name, x, y, z, r=0.06, h=0.1, pot_mat=None, col=None, seed=3, leaf_col=(0.07, 0.16, 0.04), size=0.14):
    """A small pot of herbs: a pot, soil, a mound of small leaves."""
    objs = vessel(name + "_pot", x, y, z, [(r * 0.8, 0.0), (r * 0.85, 0.004), (r, h)], pot_mat or mats.ceramic((0.62, 0.36, 0.22), matte=True), col, thick=0.005)
    objs.append(geo.cylinder(x, y, z + h * 0.7, z + h * 0.9, r * 0.93, 32, name=name + "_soil", mat=mats.soil(), collection=col))
    rnd = random.Random(seed)
    import bmesh
    me = bpy.data.meshes.new(name + "_leaves")
    bm = bmesh.new()
    for i in range(160):
        a = rnd.uniform(0, 2 * math.pi)
        rr = r * 0.9 * math.sqrt(rnd.random())
        stem_h = size * rnd.uniform(0.25, 1.0)
        p = Vector((x + rr * math.cos(a), y + rr * math.sin(a), z + h * 0.88 + stem_h))
        d = Vector((math.cos(a) * rnd.uniform(0.2, 1.0), math.sin(a) * rnd.uniform(0.2, 1.0), rnd.uniform(-0.3, 0.6))).normalized()
        side = d.cross(Vector((0, 0, 1)))
        if side.length < 1e-3:
            side = Vector((1, 0, 0))
        side.normalize()
        ll = rnd.uniform(0.018, 0.032)
        ww = ll * 0.6
        _leaf(bm, p, d, side, ll, ww, fold=0.3, droop=0.2, shape=0.45)
    bm.to_mesh(me)
    bm.free()
    objs.append(geo.new_object(name + "_leaves", me, col, mats.leaf(leaf_col)))
    return objs


def book_stack(name, x, y, z, n=3, col=None, seed=5, rot=0.0, palette=None):
    rnd = random.Random(seed)
    pal = palette or [(0.55, 0.45, 0.32), (0.15, 0.17, 0.16), (0.7, 0.66, 0.58), (0.35, 0.12, 0.08), (0.2, 0.25, 0.3)]
    objs = []
    zz = z
    for i in range(n):
        w = rnd.uniform(0.17, 0.24)
        d = rnd.uniform(0.13, 0.17)
        t = rnd.uniform(0.018, 0.035)
        c = pal[rnd.randrange(len(pal))]
        # the stack is one group (name_0, name_0_p, name_1 …): it rests as a whole
        ob = geo.box(-w / 2, -d / 2, 0, w / 2, d / 2, t, name=f"{name}_{i}", mat=mats.paint(c, 0.6, texture=0), collection=col, bevel=0.002)
        pages = geo.box(-w / 2 + 0.003, -d / 2 - 0.0005, 0.002, w / 2 - 0.0005, d / 2 - 0.003, t - 0.002, name=f"{name}_{i}_p", mat=mats.paper(), collection=col)
        for o in (ob, pages):
            o.location = (x, y, zz)
            o.rotation_euler = (0, 0, rot + rnd.uniform(-0.12, 0.12))
        objs += rest([ob, pages])
        zz += t
    return objs


def towel(name, x, y, z, w=0.3, d=0.2, t=0.012, col=None, color=(0.75, 0.70, 0.62), rot=0.0, stripe=None):
    """A folded linen towel."""
    ob = geo.box(-w / 2, -d / 2, 0, w / 2, d / 2, t, name=name, mat=mats.linen(color), collection=col, bevel=0.005, segments=3)
    ob.location = (x, y, z)
    ob.rotation_euler = (0, 0, rot)
    return rest([ob])


def pendant(name, x, y, z_ceiling, drop=0.8, shade="dome", r=0.18, mat=None, col=None, light_power=40.0, color=(1.0, 0.78, 0.55), glow=True):
    """A pendant lamp: cord, shade, a glowing bulb and a light inside."""
    objs = []
    zs = z_ceiling - drop
    objs.append(geo.tube([(x, y, z_ceiling), (x, y, zs + 0.02)], 0.002, 8, name=name + "_cord", mat=mats.metal("black"), collection=col))
    m = mat or mats.metal("brass")
    if shade == "dome":
        prof = [(0.012, 0.0), (0.03, -0.01), (r * 0.6, -0.06), (r * 0.9, -0.13), (r, -0.17)]
    elif shade == "cone":
        prof = [(0.012, 0.0), (0.02, -0.005), (r, -0.22)]
    elif shade == "cyl":
        prof = [(r, 0.0), (r, -0.26)]
    else:  # globe
        prof = None
    if prof:
        inner = [(max(0.0, rr - 0.002), h) for rr, h in reversed(prof)]
        ob = geo.lathe(prof + inner, n=64, name=name + "_shade", mat=m, collection=col, cx=x, cy=y, z=zs)
        objs.append(ob)
        lowest = prof[-1][1]
        if glow:
            objs.append(geo.lathe([(0.0, -0.04), (0.03, -0.055), (0.035, -0.08), (0.03, -0.1), (0.0, -0.11)], n=32, name=name + "_bulb", mat=mats.emission(color, 6.0), collection=col, cx=x, cy=y, z=zs + 0.02))
        from . import common
        L = common.point_light(name + "_light", (x, y, zs - 0.08), energy=light_power, color=color, radius=0.03)
        objs.append(L)
    else:
        glob = _ellipsoid(name + "_globe", x, y, zs - r, r, r, r, mats.emission(color, 2.5) if glow else mats.glass(), col)
        objs.append(glob)
        from . import common
        objs.append(common.point_light(name + "_light", (x, y, zs - r), energy=light_power, color=color, radius=r * 0.8))
    return objs

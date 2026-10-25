"""The kitchens the sinks are installed in. A kitchen is a run of base cabinets under a worktop with
the sink cut into it — along a wall, under a window, or in an island with the room behind — and
its walls, splashback, shelves, lights and props. Everything is described by a recipe (scenes.py).

World: x along the run, y away from the camera (the wall the sink backs onto is +y), z up, metres.
The sink is centred on (sx, 0) of its worktop, its back to +y."""
import math
import random
import bpy
from mathutils import Vector
from . import geo, mats, props, common


# ── doors and handles ──────────────────────────────────────────────────────

def door(x0, x1, z0, z1, yf, style, mat, col, handle=None, hmat=None, hpos="top", t=0.019, gap=0.003):
    """One cabinet front, its face at y = yf (facing -y)."""
    objs = []
    x0 += gap / 2
    x1 -= gap / 2
    z0 += gap / 2
    z1 -= gap / 2
    if style in ("slab", "groove"):
        objs.append(geo.box(x0, yf, z0, x1, yf + t, z1, name="door", mat=mat, collection=col, bevel=0.0012))
    elif style == "shaker":
        f = 0.065
        objs.append(geo.box(x0, yf + 0.006, z0, x1, yf + t, z1, name="door_panel", mat=mat, collection=col, bevel=0.001))
        for (a, b, c, d) in ((x0, x0 + f, z0, z1), (x1 - f, x1, z0, z1), (x0 + f, x1 - f, z0, z0 + f), (x0 + f, x1 - f, z1 - f, z1)):
            objs.append(geo.box(a, yf, c, b, yf + 0.008, d, name="door_rail", mat=mat, collection=col, bevel=0.0015))
    elif style == "fluted":
        objs.append(geo.box(x0, yf + 0.006, z0, x1, yf + t, z1, name="door_core", mat=mat, collection=col, bevel=0.001))
        n = max(4, int((x1 - x0) / 0.022))
        w = (x1 - x0) / n
        for i in range(n):
            ob = geo.cylinder(0, 0, 0, z1 - z0 - 0.002, w * 0.5, 16, name="flute", mat=mat, collection=col)
            ob.location = (x0 + w * (i + 0.5), yf + w * 0.5 + 0.001, z0 + 0.001)
            ob.scale = (1.0, 0.55, 1.0)
            objs.append(ob)
    elif style == "slatted":
        objs.append(geo.box(x0, yf + 0.010, z0, x1, yf + t, z1, name="door_core", mat=mats.paint((0.02, 0.02, 0.02), 0.8, texture=0), collection=col))
        n = max(4, int((x1 - x0) / 0.04))
        w = (x1 - x0) / n
        for i in range(n):
            objs.append(geo.box(x0 + w * i + 0.004, yf, z0, x0 + w * (i + 1) - 0.004, yf + 0.011, z1, name="slat", mat=mat, collection=col, bevel=0.0015))
    elif style == "beadboard":
        objs.append(geo.box(x0, yf + 0.004, z0, x1, yf + t, z1, name="door", mat=mat, collection=col, bevel=0.001))
        f = 0.06
        for (a, b, c, d) in ((x0, x0 + f, z0, z1), (x1 - f, x1, z0, z1), (x0 + f, x1 - f, z0, z0 + f), (x0 + f, x1 - f, z1 - f, z1)):
            objs.append(geo.box(a, yf, c, b, yf + 0.006, d, name="door_rail", mat=mat, collection=col, bevel=0.0012))
        n = max(3, int((x1 - x0 - 2 * f) / 0.05))
        for i in range(1, n):
            xx = x0 + f + (x1 - x0 - 2 * f) * i / n
            objs.append(geo.box(xx - 0.0012, yf + 0.0025, z0 + f, xx + 0.0012, yf + 0.0045, z1 - f, name="bead", mat=mats.paint((0.02, 0.02, 0.02), 0.9, texture=0), collection=col))
    if handle and handle != "none":
        hm = hmat or mats.metal("brass")
        cx = (x0 + x1) / 2
        if hpos == "top":
            hz = z1 - 0.05
        elif hpos == "mid":
            hz = (z0 + z1) / 2
        elif hpos == "bottom":
            hz = z0 + 0.05
        else:
            hz = z1 - 0.05
        if handle == "bar":
            L = min(0.32, (x1 - x0) * 0.55)
            objs.append(geo.tube([(cx - L / 2, yf - 0.032, hz), (cx + L / 2, yf - 0.032, hz)], 0.0065, 16, name="bar", mat=hm, collection=col))
            for sx in (-1, 1):
                objs.append(geo.tube([(cx + sx * (L / 2 - 0.02), yf, hz), (cx + sx * (L / 2 - 0.02), yf - 0.032, hz)], 0.0055, 12, name="bar_post", mat=hm, collection=col))
        elif handle == "vbar":
            L = 0.22
            hx = x1 - 0.045 if hpos == "right" else (x0 + 0.045 if hpos == "left" else cx)
            objs.append(geo.tube([(hx, yf - 0.03, z1 - 0.06), (hx, yf - 0.03, z1 - 0.06 - L)], 0.006, 16, name="vbar", mat=hm, collection=col))
            for dz in (0.02, L - 0.02):
                objs.append(geo.tube([(hx, yf, z1 - 0.06 - dz), (hx, yf - 0.03, z1 - 0.06 - dz)], 0.005, 12, name="vbar_post", mat=hm, collection=col))
        elif handle == "knob":
            ob = geo.lathe([(0.0, 0.0), (0.008, 0.0), (0.007, 0.012), (0.016, 0.02), (0.017, 0.028), (0.0, 0.03)], n=32, name="knob", mat=hm, collection=col)
            ob.rotation_euler = (math.pi / 2, 0, 0)
            ob.location = (cx, yf, hz)
            objs.append(ob)
        elif handle == "edge":
            L = min(0.3, (x1 - x0) * 0.5)
            ze = z1 if hpos != "bottom" else z0
            objs.append(geo.box(cx - L / 2, yf - 0.002, ze - 0.002, cx + L / 2, yf + 0.03, ze + 0.006, name="edge_pull", mat=hm, collection=col, bevel=0.001))
        elif handle == "cup":
            ob = geo.box(cx - 0.05, yf - 0.018, hz - 0.012, cx + 0.05, yf, hz + 0.012, name="cup", mat=hm, collection=col, bevel=0.006)
            objs.append(ob)
        elif handle == "leather":
            objs.append(geo.box(cx - 0.012, yf - 0.006, hz - 0.06, cx + 0.012, yf, hz + 0.01, name="strap", mat=mats.paint((0.25, 0.12, 0.05), 0.6, texture=0), collection=col, bevel=0.003))
    return objs


def base_run(x0, x1, y_front, z_top, style, col, door_w=0.6, plinth=0.1, toe=0.06, depth=0.58, split=None, drawers=None):
    """Base cabinets between x0 and x1: carcass, plinth, doors (and drawer fronts where `drawers` says)."""
    objs = []
    cm = style["cab_mat"]
    pm = style.get("plinth_mat") or mats.paint((0.03, 0.03, 0.03), 0.7, texture=0)
    objs.append(geo.box(x0, y_front + toe, 0.0, x1, y_front + depth, plinth, name="plinth", mat=pm, collection=col))
    objs.append(geo.open_box(x0, y_front + 0.02, plinth, x1, y_front + depth, z_top - 0.0005, name="carcass", mat=mats.paint((0.03, 0.03, 0.03), 0.9, texture=0), collection=col))
    n = max(1, int(round((x1 - x0) / door_w)))
    w = (x1 - x0) / n
    for i in range(n):
        a, b = x0 + w * i, x0 + w * (i + 1)
        if drawers and i in drawers:
            hs = [0.0, 0.25, 0.5, 1.0] if drawers[i] == 3 else [0.0, 0.5, 1.0]
            for k in range(len(hs) - 1):
                za = plinth + (z_top - plinth) * hs[k]
                zb = plinth + (z_top - plinth) * hs[k + 1]
                objs += door(a, b, za, zb, y_front, style["door"], cm, col, handle=style.get("handle"), hmat=style.get("handle_mat"), hpos="mid" if style.get("handle") in ("bar", "knob", "cup") else "top")
        else:
            objs += door(a, b, plinth, z_top, y_front, style["door"], cm, col, handle=style.get("handle"), hmat=style.get("handle_mat"), hpos="top")
    return objs


# ── the worktop ────────────────────────────────────────────────────────────

def worktop(x0, x1, y0, y1, z_top, t, mat, cutouts, col, edge="eased"):
    outer = geo.rrect(x0, x1, y0, y1, 0.002 if edge != "round" else 0.02, n_corner=4, n_side=(20, 10))
    ob = geo.slab(outer, cutouts, z_top - t, z_top, name="worktop", mat=mat, collection=col,
                  bevel={"eased": 0.0025, "square": 0.0008, "round": 0.008, "bullnose": t * 0.45}.get(edge, 0.002),
                  bevel_segments=4 if edge != "bullnose" else 8)
    return [ob]


# ── the room ───────────────────────────────────────────────────────────────

def wall(x0, x1, y, z0, z1, mat, col, t=0.1, holes=None):
    """A wall in the x-z plane, its face at y (facing -y). holes: [(x0, x1, z0, z1)]."""
    if not holes:
        return [geo.box(x0, y, z0, x1, y + t, z1, name="wall", mat=mat, collection=col)]
    objs = []
    hx0, hx1, hz0, hz1 = holes[0]
    objs.append(geo.box(x0, y, z0, hx0, y + t, z1, name="wall_l", mat=mat, collection=col))
    objs.append(geo.box(hx1, y, z0, x1, y + t, z1, name="wall_r", mat=mat, collection=col))
    objs.append(geo.box(hx0, y, z0, hx1, y + t, hz0, name="wall_b", mat=mat, collection=col))
    objs.append(geo.box(hx0, y, hz1, hx1, y + t, z1, name="wall_t", mat=mat, collection=col))
    return objs


def window(x0, x1, z0, z1, y, frame_mat, col, mullions=1, reveal=0.1, sill_mat=None, glass=True, transoms=0):
    """A window in a wall face at y: reveals, a slim frame, glazing bars, glass, a sill."""
    objs = []
    fw = 0.035
    yy = y + reveal * 0.6
    # reveals (the wall's thickness round the opening)
    rm = sill_mat or frame_mat
    for (a, b, c, d) in ((x0 - 0.002, x0, z0, z1), (x1, x1 + 0.002, z0, z1)):
        pass
    objs.append(geo.box(x0, yy, z0, x0 + fw, yy + 0.05, z1, name="win_frame_l", mat=frame_mat, collection=col, bevel=0.002))
    objs.append(geo.box(x1 - fw, yy, z0, x1, yy + 0.05, z1, name="win_frame_r", mat=frame_mat, collection=col, bevel=0.002))
    objs.append(geo.box(x0, yy, z0, x1, yy + 0.05, z0 + fw, name="win_frame_b", mat=frame_mat, collection=col, bevel=0.002))
    objs.append(geo.box(x0, yy, z1 - fw, x1, yy + 0.05, z1, name="win_frame_t", mat=frame_mat, collection=col, bevel=0.002))
    for i in range(1, mullions + 1):
        xm = x0 + (x1 - x0) * i / (mullions + 1)
        objs.append(geo.box(xm - 0.018, yy, z0, xm + 0.018, yy + 0.05, z1, name="win_mullion", mat=frame_mat, collection=col, bevel=0.002))
    for i in range(1, transoms + 1):
        zm = z0 + (z1 - z0) * i / (transoms + 1)
        objs.append(geo.box(x0, yy, zm - 0.015, x1, yy + 0.05, zm + 0.015, name="win_transom", mat=frame_mat, collection=col, bevel=0.002))
    if glass:
        g = mats.glass((0.98, 0.99, 0.99), 0.0)
        objs.append(geo.box(x0 + fw, yy + 0.024, z0 + fw, x1 - fw, yy + 0.028, z1 - fw, name="win_glass", mat=g, collection=col))
    return objs


def shelf(x0, x1, z, y_wall, depth, mat, col, t=0.03, brackets=None):
    objs = [geo.box(x0, y_wall - depth, z - t, x1, y_wall, z, name="shelf", mat=mat, collection=col, bevel=0.0015)]
    if brackets:
        for xb in (x0 + 0.12, x1 - 0.12):
            objs.append(geo.box(xb - 0.006, y_wall - depth + 0.03, z - t - 0.12, xb + 0.006, y_wall, z - t, name="bracket", mat=brackets, collection=col))
    return objs


def led_strip(x0, x1, z, y, col, color=(1.0, 0.8, 0.6), strength=6.0, width=0.008):
    """A hidden LED strip: a thin emitter facing down."""
    ob = geo.box(x0, y - width, z - 0.002, x1, y, z, name="led", mat=mats.emission(color, strength), collection=col)
    ob.visible_camera = False
    return [ob]


# ── placing the sink ───────────────────────────────────────────────────────

def install_sink(sink, x, y, z_top, t, col=None, rot=0.0):
    """Move the sink's objects into place on a worktop whose top is z_top, t thick.
    Undermount: the sink's rim under the stone. Top-mount: its rim on the stone. Inset: its turned
    edge resting on the stone."""
    mount = sink["mount"]
    if mount == "under":
        z = z_top - t
    elif mount == "top":
        z = z_top + sink.get("flange", 0.012)
    else:  # inset (pressed)
        z = z_top + sink.get("rim_above", 0.010)
    for o in sink["objects"]:
        if o.type != 'MESH':
            continue
        o.location = (o.location.x + x, o.location.y + y, o.location.z + z)
        if rot:
            # rotate about the sink's centre
            c, s = math.cos(rot), math.sin(rot)
            dx, dy = o.location.x - x, o.location.y - y
            o.location = (x + dx * c - dy * s, y + dx * s + dy * c, o.location.z)
            o.rotation_euler.z += rot
    sink["placed"] = (x, y, z)
    cut = []
    for poly in sink["cutout"]:
        c, s = math.cos(rot), math.sin(rot)
        cut.append([(x + px * c - py * s, y + px * s + py * c) for (px, py) in poly])
    return cut, z


def interior_box(x0, x1, y0, y1, z0, z1, col):
    """A dark box inside the sink cabinet so light doesn't leak under the worktop."""
    return [geo.box(x0, y0, z0, x1, y1, z1, name="cab_inside", mat=mats.paint((0.02, 0.02, 0.02), 0.9, texture=0), collection=col)]

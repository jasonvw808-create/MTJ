"""Geometry helpers for the kitchen-sink renders.

All 2D outlines are lists of (x, y) points in metres, counter-clockwise, with
x across the sink (left -> right) and y front -> back (+y is away from the
viewer). The sink measurements come in millimetres with z front-to-back where
negative z is the back, so mm(x, z) -> (x / 1000, -z / 1000).
"""
import math
import bmesh
import bpy
import numpy as np
from mathutils import Vector


def mm(v):
    return v / 1000.0


# ── 2D outlines ────────────────────────────────────────────────────────────

def _arc(cx, cy, r, a0, a1, n):
    return [(cx + r * math.cos(a0 + (a1 - a0) * i / n), cy + r * math.sin(a0 + (a1 - a0) * i / n)) for i in range(n + 1)]


def rrect(x0, x1, y0, y1, r, n_corner=10, n_side=(8, 6)):
    """Rounded rectangle, CCW from the front-right corner's end. `r` may be one radius or
    [front-left, front-right, back-right, back-left]. Always returns the same number of points
    for the same n_corner / n_side, so rings of different sizes correspond point for point."""
    if not isinstance(r, (list, tuple)):
        r = [r] * 4
    w, h = x1 - x0, y1 - y0
    r = [max(1e-5, min(ri, w / 2 - 1e-5, h / 2 - 1e-5)) for ri in r]
    rfl, rfr, rbr, rbl = r
    nx, ny = n_side
    pts = []
    # front edge, left -> right (y = y0)
    for i in range(nx):
        t = i / nx
        pts.append((x0 + rfl + (x1 - rfr - (x0 + rfl)) * t, y0))
    pts += _arc(x1 - rfr, y0 + rfr, rfr, -math.pi / 2, 0, n_corner)[:-1]
    for i in range(ny):
        t = i / ny
        pts.append((x1, y0 + rfr + (y1 - rbr - (y0 + rfr)) * t))
    pts += _arc(x1 - rbr, y1 - rbr, rbr, 0, math.pi / 2, n_corner)[:-1]
    for i in range(nx):
        t = i / nx
        pts.append((x1 - rbr - (x1 - rbr - (x0 + rbl)) * t, y1))
    pts += _arc(x0 + rbl, y1 - rbl, rbl, math.pi / 2, math.pi, n_corner)[:-1]
    for i in range(ny):
        t = i / ny
        pts.append((x0, y1 - rbl - (y1 - rbl - (y0 + rfl)) * t))
    pts += _arc(x0 + rfl, y0 + rfl, rfl, math.pi, 1.5 * math.pi, n_corner)[:-1]
    return pts


def rpoly(points, radii, n_corner=10, n_side=6):
    """A polygon (CCW) with rounded corners; radii per corner. Fixed point count per (len, n)."""
    k = len(points)
    if not isinstance(radii, (list, tuple)):
        radii = [radii] * k
    P = [np.array(p, float) for p in points]
    out = []
    for i in range(k):
        p0, p1, p2 = P[i - 1], P[i], P[(i + 1) % k]
        d0 = (p0 - p1) / np.linalg.norm(p0 - p1)
        d2 = (p2 - p1) / np.linalg.norm(p2 - p1)
        r = radii[i]
        ang = math.acos(max(-1.0, min(1.0, float(np.dot(d0, d2)))))
        if r <= 1e-6 or ang > math.pi - 1e-3:
            arc = [tuple(p1)] * (n_corner + 1)
        else:
            t = r / math.tan(ang / 2)
            t = min(t, 0.49 * np.linalg.norm(p0 - p1), 0.49 * np.linalg.norm(p2 - p1))
            r = t * math.tan(ang / 2)
            a = p1 + d0 * t
            b = p1 + d2 * t
            bis = (d0 + d2) / np.linalg.norm(d0 + d2)
            c = p1 + bis * (r / math.sin(ang / 2))
            a0 = math.atan2(a[1] - c[1], a[0] - c[0])
            a1 = math.atan2(b[1] - c[1], b[0] - c[0])
            da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
            arc = [(c[0] + r * math.cos(a0 + da * j / n_corner), c[1] + r * math.sin(a0 + da * j / n_corner)) for j in range(n_corner + 1)]
        # straight run from previous arc end to this arc start is added by sampling between
        if out:
            s = np.array(out[-1])
            e = np.array(arc[0])
            for j in range(1, n_side):
                out.append(tuple(s + (e - s) * j / n_side))
        out += arc
    # close: run from last arc end to first arc start
    s = np.array(out[-1])
    e = np.array(out[0])
    for j in range(1, n_side):
        out.append(tuple(s + (e - s) * j / n_side))
    return out


def circle(cx, cy, r, n=48):
    return [(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n)) for i in range(n)]


def stadium(x0, x1, yc, w, n=8):
    r = w / 2
    pts = _arc(x1 - r, yc, r, -math.pi / 2, math.pi / 2, n) + _arc(x0 + r, yc, r, math.pi / 2, 1.5 * math.pi, n)
    return pts


def area(poly):
    a = 0
    for i in range(len(poly)):
        x0, y0 = poly[i - 1]
        x1, y1 = poly[i]
        a += x0 * y1 - x1 * y0
    return a / 2


def ccw(poly):
    return poly if area(poly) > 0 else poly[::-1]


def offset_rrect(spec, d):
    """spec = (x0, x1, y0, y1, r) -> grown (+d) or shrunk (-d) rounded rectangle spec."""
    x0, x1, y0, y1, r = spec
    if isinstance(r, (list, tuple)):
        r = [max(0.0005, ri + d) for ri in r]
    else:
        r = max(0.0005, r + d)
    return (x0 - d, x1 + d, y0 - d, y1 + d, r)


# ── meshes ─────────────────────────────────────────────────────────────────

def new_object(name, me, collection=None, mat=None):
    ob = bpy.data.objects.new(name, me)
    (collection or bpy.context.scene.collection).objects.link(ob)
    if mat is not None:
        if isinstance(mat, (list, tuple)):
            for m in mat:
                ob.data.materials.append(m)
        else:
            ob.data.materials.append(mat)
    return ob


def smooth(me, angle=35):
    for p in me.polygons:
        p.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(angle))
    except Exception:
        pass


def loft(rings, close_bottom=None, cap_top=False, name="loft", mat=None, collection=None, smooth_angle=35, flip=False):
    """Bridge a list of rings (each a list of (x, y, z) with equal counts). Optionally cap the
    last ring with a fan to `close_bottom` (a point) or fill it with a polygon."""
    bm = bmesh.new()
    vrings = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for a, b in zip(vrings[:-1], vrings[1:]):
        for i in range(n):
            j = (i + 1) % n
            f = (a[i], a[j], b[j], b[i])
            try:
                bm.faces.new(f[::-1] if flip else f)
            except ValueError:
                pass
    if close_bottom is not None:
        c = bm.verts.new(close_bottom)
        last = vrings[-1]
        for i in range(n):
            j = (i + 1) % n
            try:
                f = (last[i], last[j], c)
                bm.faces.new(f[::-1] if flip else f)
            except ValueError:
                pass
    if cap_top:
        try:
            bm.faces.new(vrings[0][::-1] if not flip else vrings[0])
        except ValueError:
            pass
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    smooth(me, smooth_angle)
    return new_object(name, me, collection, mat)


def fill_with_holes(outer, holes, z=0.0, name="fill", mat=None, collection=None, flip=False):
    """A flat face (at height z) bounded by `outer` with `holes` cut out, triangulated."""
    bm = bmesh.new()
    loops = [ccw(outer)] + [ccw(h)[::-1] for h in holes]
    edges = []
    for loop in loops:
        vs = [bm.verts.new((x, y, z)) for (x, y) in loop]
        for i in range(len(vs)):
            edges.append(bm.edges.new((vs[i], vs[(i + 1) % len(vs)])))
    bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=edges)
    for f in bm.faces:
        if (f.normal.z < 0) != flip:
            f.normal_flip()
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    return new_object(name, me, collection, mat)


def slab(outer, holes, z0, z1, name="slab", mat=None, collection=None, bevel=0.0, bevel_segments=3):
    """A solid slab between z0 and z1 with an outline and holes: top, bottom and every side.
    Optional bevel on its edges (via the Bevel modifier, applied)."""
    bm = bmesh.new()
    loops = [ccw(outer)] + [ccw(h)[::-1] for h in holes]
    top_edges, bot_edges = [], []
    side_loops = []
    for loop in loops:
        vt = [bm.verts.new((x, y, z1)) for (x, y) in loop]
        vb = [bm.verts.new((x, y, z0)) for (x, y) in loop]
        n = len(loop)
        for i in range(n):
            j = (i + 1) % n
            top_edges.append(bm.edges.new((vt[i], vt[j])))
            bot_edges.append(bm.edges.new((vb[i], vb[j])))
            bm.faces.new((vb[i], vb[j], vt[j], vt[i]))
        side_loops.append((vt, vb))
    r = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=top_edges)
    for f in r['geom']:
        if isinstance(f, bmesh.types.BMFace) and f.normal.z < 0:
            f.normal_flip()
    r = bmesh.ops.triangle_fill(bm, use_beauty=True, use_dissolve=False, edges=bot_edges)
    for f in r['geom']:
        if isinstance(f, bmesh.types.BMFace) and f.normal.z > 0:
            f.normal_flip()
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    ob = new_object(name, me, collection, mat)
    if bevel > 0:
        md = ob.modifiers.new("bevel", 'BEVEL')
        md.width = bevel
        md.segments = bevel_segments
        md.limit_method = 'ANGLE'
        md.angle_limit = math.radians(50)
        md.harden_normals = False
    for p in me.polygons:
        p.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(40))
    except Exception:
        pass
    return ob


def box(x0, y0, z0, x1, y1, z1, name="box", mat=None, collection=None, bevel=0.0, segments=2):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x = x0 if v.co.x < 0 else x1
        v.co.y = y0 if v.co.y < 0 else y1
        v.co.z = z0 if v.co.z < 0 else z1
    bm.to_mesh(me)
    bm.free()
    ob = new_object(name, me, collection, mat)
    if bevel > 0:
        md = ob.modifiers.new("bevel", 'BEVEL')
        md.width = bevel
        md.segments = segments
        md.limit_method = 'ANGLE'
        for p in me.polygons:
            p.use_smooth = True
        try:
            me.set_sharp_from_angle(angle=math.radians(50))
        except Exception:
            pass
        md.harden_normals = True
    return ob


def cylinder(cx, cy, z0, z1, r, n=48, name="cyl", mat=None, collection=None, bevel=0.0, cap_top=True, cap_bottom=True):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    top = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z1)) for i in range(n)]
    bot = [bm.verts.new((cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z0)) for i in range(n)]
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((bot[i], bot[j], top[j], top[i]))
    if cap_top:
        bm.faces.new(top)
    if cap_bottom:
        bm.faces.new(bot[::-1])
    bm.to_mesh(me)
    bm.free()
    ob = new_object(name, me, collection, mat)
    for p in me.polygons:
        p.use_smooth = True
    try:
        me.set_sharp_from_angle(angle=math.radians(40))
    except Exception:
        pass
    if bevel > 0:
        md = ob.modifiers.new("bevel", 'BEVEL')
        md.width = bevel
        md.segments = 3
        md.limit_method = 'ANGLE'
        md.harden_normals = True
    return ob


def lathe(profile, n=64, name="lathe", mat=None, collection=None, cx=0.0, cy=0.0, z=0.0, smooth_angle=60, close_ends=True):
    """Revolve a profile [(r, z), ...] around the vertical axis."""
    rings = []
    for (r, h) in profile:
        rings.append([(cx + r * math.cos(2 * math.pi * i / n), cy + r * math.sin(2 * math.pi * i / n), z + h) for i in range(n)])
    bm = bmesh.new()
    vr = []
    for k, ring in enumerate(rings):
        if profile[k][0] < 1e-7:
            v = bm.verts.new((cx, cy, z + profile[k][1]))
            vr.append([v] * n)
        else:
            vr.append([bm.verts.new(p) for p in ring])
    for a, b in zip(vr[:-1], vr[1:]):
        for i in range(n):
            j = (i + 1) % n
            quad = [a[i], a[j], b[j], b[i]]
            uniq = []
            for v in quad:
                if v not in uniq:
                    uniq.append(v)
            if len(uniq) >= 3:
                try:
                    bm.faces.new(uniq)
                except ValueError:
                    pass
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    smooth(me, smooth_angle)
    return new_object(name, me, collection, mat)


def tube(points, radius, n=16, name="tube", mat=None, collection=None, caps=True):
    """A round tube along a 3D polyline (list of (x, y, z))."""
    P = [Vector(p) for p in points]
    rings = []
    prev_n = None
    for i, p in enumerate(P):
        if i == 0:
            t = (P[1] - P[0]).normalized()
        elif i == len(P) - 1:
            t = (P[-1] - P[-2]).normalized()
        else:
            t = ((P[i + 1] - P[i]).normalized() + (P[i] - P[i - 1]).normalized()).normalized()
        if prev_n is None:
            up = Vector((0, 0, 1)) if abs(t.z) < 0.9 else Vector((1, 0, 0))
            nrm = t.cross(up).normalized()
        else:
            nrm = (prev_n - t * prev_n.dot(t)).normalized()
        prev_n = nrm
        b = t.cross(nrm).normalized()
        rings.append([p + (nrm * math.cos(2 * math.pi * k / n) + b * math.sin(2 * math.pi * k / n)) * radius for k in range(n)])
    bm = bmesh.new()
    vr = [[bm.verts.new(v) for v in ring] for ring in rings]
    for a, b2 in zip(vr[:-1], vr[1:]):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((a[k], a[j], b2[j], b2[k]))
    if caps:
        bm.faces.new(vr[0][::-1])
        bm.faces.new(vr[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    smooth(me, 70)
    return new_object(name, me, collection, mat)


def heightfield(x0, x1, y0, y1, res, hfun, name="hf", mat=None, collection=None, mask=None, z=0.0):
    """A grid over [x0,x1]x[y0,y1] at spacing `res`, z = z + hfun(X, Y) (numpy, metres).
    Faces whose four corners are all outside `mask(X, Y)` (bool array) are left out."""
    nx = max(2, int(round((x1 - x0) / res)) + 1)
    ny = max(2, int(round((y1 - y0) / res)) + 1)
    xs = np.linspace(x0, x1, nx)
    ys = np.linspace(y0, y1, ny)
    X, Y = np.meshgrid(xs, ys)
    Z = z + hfun(X, Y)
    keep = np.ones_like(X, bool) if mask is None else mask(X, Y)
    verts = np.stack([X.ravel(), Y.ravel(), Z.ravel()], 1)
    idx = np.arange(nx * ny).reshape(ny, nx)
    a = idx[:-1, :-1].ravel()
    b = idx[:-1, 1:].ravel()
    c = idx[1:, 1:].ravel()
    d = idx[1:, :-1].ravel()
    k = keep.ravel()
    fk = k[a] & k[b] & k[c] & k[d]
    faces = np.stack([a[fk], b[fk], c[fk], d[fk]], 1)
    used = np.unique(faces)
    remap = -np.ones(nx * ny, np.int64)
    remap[used] = np.arange(len(used))
    verts = verts[used]
    faces = remap[faces]
    me = bpy.data.meshes.new(name)
    me.vertices.add(len(verts))
    me.vertices.foreach_set("co", verts.astype(np.float32).ravel())
    me.loops.add(faces.size)
    me.loops.foreach_set("vertex_index", faces.astype(np.int32).ravel())
    me.polygons.add(len(faces))
    me.polygons.foreach_set("loop_start", (np.arange(len(faces)) * 4).astype(np.int32))
    me.update(calc_edges=True)
    me.validate()
    me.polygons.foreach_set("use_smooth", np.ones(len(faces), bool))
    return new_object(name, me, collection, mat)


# ── signed distance functions (numpy, metres) for heightfields ─────────────

def sd_rrect(X, Y, x0, x1, y0, y1, r):
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
    r = min(r, hx, hy)
    qx = np.abs(X - cx) - (hx - r)
    qy = np.abs(Y - cy) - (hy - r)
    return np.hypot(np.maximum(qx, 0), np.maximum(qy, 0)) + np.minimum(np.maximum(qx, qy), 0) - r


def sd_poly(X, Y, poly):
    """Signed distance to a polygon (negative inside)."""
    P = np.asarray(poly, float)
    d = np.full(X.shape, np.inf)
    s = np.ones(X.shape)
    n = len(P)
    for i in range(n):
        ax, ay = P[i - 1]
        bx, by = P[i]
        ex, ey = bx - ax, by - ay
        wx, wy = X - ax, Y - ay
        t = np.clip((wx * ex + wy * ey) / (ex * ex + ey * ey + 1e-12), 0, 1)
        dx, dy = wx - ex * t, wy - ey * t
        d = np.minimum(d, dx * dx + dy * dy)
        c1 = Y >= ay
        c2 = Y < by
        c3 = ex * wy > ey * wx
        flip = (c1 & c2 & c3) | (~c1 & ~c2 & ~c3)
        s = np.where(flip, -s, s)
    return s * np.sqrt(d)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


def open_box(x0, y0, z0, x1, y1, z1, name="open_box", mat=None, collection=None):
    """A box without its top face (a cabinet carcass a sink can hang into)."""
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    v = [bm.verts.new(p) for p in [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]]
    for f in [(0, 3, 2, 1), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]:
        bm.faces.new([v[i] for i in f])
    bm.to_mesh(me)
    bm.free()
    return new_object(name, me, collection, mat)

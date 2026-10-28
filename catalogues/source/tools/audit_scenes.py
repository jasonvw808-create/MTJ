"""Build scenes without rendering them and report objects that pass through one another: surfaces that cross
(the shelf through the tap) and objects sunk into others.

    python tools/audit_scenes.py [recipe ...]      (all recipes when none are named)

Prints one line per offending pair: the two objects, how many of their triangles cross, and how deep the deepest
vertex of one lies inside the other (closed meshes only)."""
import sys
import os
sys.path.insert(0, os.getcwd())
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from render import common, mats, physics, scene, scenes

# architecture meets architecture on purpose (walls, floor, carcass, doors): only pairs with something else count
ARCH = ("wall", "floor", "ceiling", "plinth", "carcass", "door", "slat", "flute", "bead", "worktop", "splash", "sill", "rev_",
        "win_", "tall", "upper_body", "cab_inside", "lawn", "garden_wall", "sky_card", "island", "back_", "stone", "panel", "led")


def is_arch(name):
    n = name.lower()
    return any(n.startswith(a) or ("_" + a) in n for a in ARCH)


def group(name):
    """The prop an object belongs to: tap_base, tap_neck -> tap; br_stem.001 -> br."""
    return name.split(".")[0].split("_")[0].lower()


def world_mesh(ob, dg, step=0.004):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ob.matrix_world
    verts = [mw @ v.co for v in me.vertices]
    polys = [tuple(p.vertices) for p in me.polygons]
    edges = {}
    for p in polys:
        for i in range(len(p)):
            e = tuple(sorted((p[i], p[(i + 1) % len(p)])))
            edges[e] = edges.get(e, 0) + 1
    closed = bool(edges) and all(c == 2 for c in edges.values())
    # sample points: the vertices and points along the edges, so a long straight tube through a shelf is caught
    pts = list(verts)
    for (i, j) in edges:
        a, b = verts[i], verts[j]
        n = int((b - a).length / step)
        for k in range(1, n):
            pts.append(a + (b - a) * (k / n))
    ev.to_mesh_clear()
    return verts, polys, closed, pts


def inside(tree, p, dirs=(Vector((1, 0.013, 0.007)), Vector((-0.011, 1, 0.017)), Vector((0.009, -0.014, 1)))):
    """Ray-parity test against a closed mesh, by majority over three directions."""
    votes = 0
    for d in dirs:
        d = d.normalized()
        o, n = p.copy(), 0
        for _ in range(64):
            hit, nor, idx, dist = tree.ray_cast(o, d)
            if hit is None:
                break
            n += 1
            o = hit + d * 1e-6
        votes += n % 2
    return votes >= 2


def audit(name, tol=0.0015):
    common.reset()
    mats._cache.clear()
    R = scenes.RECIPES[name]()
    ctx = scene.compose(R, "preview")
    sink = {o.name for o in ctx["sink"]["objects"]}
    loose = set(physics.loose_groups(ctx))
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    data = {}
    for o in bpy.context.scene.objects:
        if o.type != 'MESH' or not o.visible_camera:
            continue
        v, p, closed, pts = world_mesh(o, dg)
        if not v or not p:
            continue
        lo = Vector((min(a.x for a in v), min(a.y for a in v), min(a.z for a in v)))
        hi = Vector((max(a.x for a in v), max(a.y for a in v), max(a.z for a in v)))
        data[o.name] = dict(v=v, pts=pts, tree=BVHTree.FromPolygons(v, p, epsilon=0.0), lo=lo, hi=hi, closed=closed,
                            arch=is_arch(o.name), group=group(o.name), sink=o.name in sink)
    names = sorted(data)
    out = []
    for i, a in enumerate(names):
        A = data[a]
        for b in names[i + 1:]:
            B = data[b]
            if (A["arch"] and B["arch"]) or A["group"] == B["group"]:
                continue
            if any(A["lo"][k] > B["hi"][k] + tol or B["lo"][k] > A["hi"][k] + tol for k in range(3)):
                continue
            cross = len(A["tree"].overlap(B["tree"]))
            # depth: vertices of one inside the other (closed meshes), deeper than tol
            depth = 0.0
            for X, Y in ((A, B), (B, A)):
                if not Y["closed"]:
                    continue
                for pt in X["pts"]:
                    if any(pt[k] < Y["lo"][k] or pt[k] > Y["hi"][k] for k in range(3)):
                        continue
                    loc, nor, idx, dist = Y["tree"].find_nearest(pt)
                    if loc is None or dist <= tol or dist <= depth:
                        continue
                    if inside(Y["tree"], pt):
                        depth = dist
            sink_in_top = {A["group"], B["group"]} & {"worktop"} and (A["sink"] or B["sink"])
            if depth > 2 * tol and not (sink_in_top and cross == 0):
                out.append((depth, cross, a, b))
    out.sort(reverse=True)
    for depth, cross, a, b in out:
        print(f"{name:18s} SUNK  {a:28s} x {b:28s} crossing={cross:5d} depth={depth * 1000:6.1f} mm", flush=True)
    # floating: no point of a prop's underside touches anything, yet something lies 1.5 mm .. 40 mm under it;
    # perched: it touches something, but only on that thing's flank, its lowest point hanging 5 mm or more over
    # what is under it (a lemon on another lemon's side; fruit heaped in a bowl is perched too, so look at those)
    groups = {}
    for n, D in data.items():
        if not D["arch"]:
            groups.setdefault(D["group"], []).append(n)
    trees = [(n, D["tree"]) for n, D in data.items()]

    def gap_under(pt, g, reach=0.06):
        o = Vector((pt.x, pt.y, pt.z + 0.0005))   # from just above, so a surface it rests on is found at once
        best, what = None, None
        for n, t in trees:
            if data[n]["group"] == g:
                continue
            hit, nor, idx, dist = t.ray_cast(o, Vector((0, 0, -1)), reach)
            if hit is not None and (best is None or dist - 0.0005 < best):
                best, what = max(0.0, dist - 0.0005), n
        return best, what

    floats = perched = 0
    for g, members in sorted(groups.items()):
        pts = sorted((pt for n in members for pt in data[n]["v"]), key=lambda v: v.z)
        zmin = pts[0].z
        low = [pt for pt in pts if pt.z < zmin + 0.0008]
        under = [gap_under(pt, g, reach=3.0)[0] for pt in low[::max(1, len(low) // 24)]]
        under = min((u for u in under if u is not None), default=None)
        if g not in loose:
            # fixed things (a tap, a knob, a lamp): only a lowest point hanging over something counts
            if under is not None and 0.0015 < under < 0.04:
                floats += 1
                print(f"{name:18s} FLOAT {g:28s} gap={under * 1000:6.1f} mm over the surface under it", flush=True)
            continue
        # a resting thing must rest on something, with its lower part (as physics.settle has it): the nearest surface
        # under that, however far down
        sup = physics.support_points([bpy.data.objects[n] for n in members], {n: (data[n]["v"], None) for n in members})
        touch, on = None, None
        for pt in sup[::max(1, len(sup) // 200)]:
            gp, what = gap_under(pt, g, reach=3.0)
            if gp is not None and (touch is None or gp < touch):
                touch, on = gp, what
        if touch is None or touch > 0.0015:
            floats += 1
            gap = "nothing under it" if touch is None else f"gap={touch * 1000:6.1f} mm over {on}"
            print(f"{name:18s} FLOAT {g:28s} {gap}", flush=True)
        elif under is not None and under >= 0.005:
            perched += 1
            print(f"{name:18s} PERCH {g:28s} on {on:24s} its lowest point {under * 1000:5.1f} mm over the surface under it", flush=True)
    print(f"{name:18s} -- {len(data)} objects, {len(out)} sunk pairs, {floats} floating, {perched} perched", flush=True)


if __name__ == "__main__":
    which = sys.argv[1:] or sorted(scenes.RECIPES)
    for n in which:
        try:
            audit(n)
        except Exception as e:
            print(f"{n:18s} ERROR {e!r}", flush=True)

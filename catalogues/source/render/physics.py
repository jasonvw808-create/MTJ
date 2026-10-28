"""Make the props sit as real things do: each one resting on whatever is under it (the worktop, a shelf, a board, the
fruit below it in a bowl) and none inside a wall. Run after a scene is built, before it is lit and framed.

A prop is a group of objects whose names share a first word (a jar and its lid, jar and jar_lid; a vase and the
branches in it, bv and bv_br); only props the builders tagged as resting things are moved (props.rest)."""
import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

def group_of(name):
    return name.split(".")[0].split("_")[0].lower()


def loose_groups(ctx):
    """The props that rest on something: groups with at least one object tagged "rest" by the prop builders
    (props.rest). A tap, a handle, a lamp or a shelf is never tagged, so never moved."""
    sink_names = {o.name for o in ctx["sink"]["objects"]}
    groups, tagged = {}, set()
    for o in ctx["sc"].objects:
        if o.type != 'MESH' or not o.visible_camera or o.name in sink_names:
            continue
        g = group_of(o.name)
        groups.setdefault(g, []).append(o)
        if o.get("rest"):
            tagged.add(g)
    return {g: m for g, m in groups.items() if g in tagged}


def _world(ob, dg):
    ev = ob.evaluated_get(dg)
    me = ev.to_mesh()
    mw = ob.matrix_world
    v = [mw @ x.co for x in me.vertices]
    p = [tuple(f.vertices) for f in me.polygons]
    ev.to_mesh_clear()
    return v, p


def support_points(members, meshes):
    """The points a prop can rest on: the lower part of each of its pieces (a lemon's side against a bowl's curve, a
    plate's slope, a pot's base), never its upper part, so it cannot hang by its rim from an edge."""
    pts = []
    for o in members:
        v = meshes[o.name][0]
        if not v:
            continue
        oz0, oz1 = min(p.z for p in v), max(p.z for p in v)
        cut = oz0 + max(0.004, 0.4 * (oz1 - oz0))
        pts += [p for p in v if p.z <= cut]
    return sorted(pts, key=lambda p: p.z)[:1200]


def settle(ctx, order=None, gap=0.0004, max_drop=0.25, verbose=False):
    """Drop every loose prop onto what is under it. Props are settled lowest first, so fruit lands on the bowl and
    then on the fruit already in it; a prop whose base is inside its support is lifted out."""
    sc = ctx["sc"]
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    obs = [o for o in sc.objects if o.type == 'MESH' and o.visible_camera]
    meshes = {o.name: _world(o, dg) for o in obs}
    groups = loose_groups(ctx)
    # lowest first
    def zmin(g):
        return min(min(v.z for v in meshes[o.name][0]) for o in groups[g] if meshes[o.name][0])
    names = sorted(groups, key=zmin)
    # a prop rests only on fixed things and on props already settled: two fruit set down side by side at the same
    # height must not lift each other
    owner = {o.name: g for g, m in groups.items() for o in m}
    settled = set()
    moved = []
    for g in names:
        members = groups[g]
        mine = {o.name for o in members}
        others = [n for n in meshes if n not in mine and (n not in owner or owner[n] in settled)]
        settled.add(g)
        if not others:
            continue
        verts = [v for o in members for v in meshes[o.name][0]]
        if not verts:
            continue
        z0 = min(v.z for v in verts)
        low = support_points(members, meshes)
        lo = Vector((min(v.x for v in verts), min(v.y for v in verts), z0))
        hi = Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts)))
        # the supports: everything else whose box lies under this prop's footprint
        tv, tp = [], []
        for n in others:
            v, p = meshes[n]
            if not v:
                continue
            if max(a.x for a in v) < lo.x or min(a.x for a in v) > hi.x or max(a.y for a in v) < lo.y or min(a.y for a in v) > hi.y:
                continue
            if min(a.z for a in v) > hi.z:
                continue
            base = len(tv)
            tv += v
            tp += [tuple(i + base for i in f) for f in p]
        if not tp:
            continue
        tree = BVHTree.FromPolygons(tv, tp, epsilon=0.0)
        # for each low point, the surface it should rest on: straight down from just inside the prop; but if that
        # first meets the underside of something, the point is buried in it, and its top (straight up) is the surface
        best = None
        step = max(1, len(low) // 200)
        for v in low[::step]:
            hit, nor, idx, dist = tree.ray_cast(v + Vector((0, 0, 0.001)), Vector((0, 0, -1)), max_drop)
            if hit is None:
                continue
            if nor.z < 0:
                up, nup, _, _ = tree.ray_cast(v - Vector((0, 0, 0.0005)), Vector((0, 0, 1)), 0.25)
                if up is None:
                    continue
                dz = up.z - v.z
            else:
                dz = hit.z - v.z
            if best is None or dz > best:
                best = dz
        if best is None or abs(best + gap) < 0.0002:
            continue
        dz = best + gap
        for o in members:
            o.location.z += dz
        for o in members:
            meshes[o.name] = ([v + Vector((0, 0, dz)) for v in meshes[o.name][0]], meshes[o.name][1])
        moved.append((g, dz))
        if verbose:
            print(f"settle {g}: {dz * 1000:+.1f} mm")
    bpy.context.view_layer.update()
    return moved


def clear_of(ctx, faces, margin=0.004, verbose=False):
    """Keep loose props in front of the back surfaces they stand against: faces = [(y_face, z0, z1, x0, x1)], the
    front faces of the wall, splashback, upstand or ledge. A prop reaching behind one is moved forward."""
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    for g, members in loose_groups(ctx).items():
        verts = [v for o in members for v in _world(o, dg)[0]]
        if not verts:
            continue
        push = 0.0
        for (yf, z0, z1, x0, x1) in faces:
            # a prop standing level with a face's top or foot (a pot on the sill at the splashback's top) is not in
            # front of it
            inside = [v.y for v in verts if z0 + 0.003 < v.z < z1 - 0.003 and x0 <= v.x <= x1]
            if inside:
                push = max(push, max(inside) - (yf - margin))
        if push > 0:
            for o in members:
                o.location.y -= push
            if verbose:
                print(f"clear {g}: {push * 1000:.1f} mm forward")
    bpy.context.view_layer.update()

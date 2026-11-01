"""Build scenes without rendering them and report boxes whose faces lie in one plane, face the same way and overlap.
Cycles shadows such a face with its twin, and it renders black: a black square where a window's glazing bar ran over
its rail, a black line round an opening where the reveal ran on into the wall's face.

    python tools/coplanar.py [recipe ...]      (all recipes when none are named)

Prints, for each recipe, every such pair: the shared area, the axis and the side the faces look to (y- faces the room,
z+ looks up), the two objects, and the overlap's size. Only axis-aligned boxes are compared (geo.box, before its bevel).
Faces that look into a wall, a frame or a neighbouring box cannot be seen and need no change: the ones to fix face the
camera (most often y-, z+ or x+/-) on something in the picture."""
import sys
import os
import itertools
sys.path.insert(0, os.getcwd())
import bpy
from render import common, mats, scene, scenes


def boxes():
    out = []
    for o in bpy.data.objects:
        if o.type != 'MESH' or len(o.data.vertices) != 8 or len(o.data.polygons) != 6 or o.hide_render:
            continue
        if not getattr(o, "visible_camera", True):
            continue
        vs = [o.matrix_world @ v.co for v in o.data.vertices]
        lo = [min(v[i] for v in vs) for i in range(3)]
        hi = [max(v[i] for v in vs) for i in range(3)]
        # axis-aligned: every corner sits on its box's bounds
        if all(any(abs(v[i] - b[i]) < 1e-6 for b in (lo, hi)) for v in vs for i in range(3)):
            out.append((o.name, lo, hi))
    return out


def shared(bx):
    hits = []
    for (na, la, ha), (nb, lb, hb) in itertools.combinations(bx, 2):
        for k in range(3):
            u, w = [i for i in range(3) if i != k]
            ou = min(ha[u], hb[u]) - max(la[u], lb[u])
            ow = min(ha[w], hb[w]) - max(la[w], lb[w])
            if ou <= 1e-4 or ow <= 1e-4:
                continue
            for side, a, b in (("-", la[k], lb[k]), ("+", ha[k], hb[k])):
                if abs(a - b) < 1e-6:
                    hits.append((ou * ow * 1e4, "xyz"[k] + side, na, nb, ou * 1000, ow * 1000))
    return sorted(hits, reverse=True)


def check(name):
    common.reset()
    mats._cache.clear()
    from render import calm
    if calm.enabled():
        calm.begin(name)
    R = scenes.RECIPES[name]()
    if calm.enabled():
        R = calm.restyle(name, R)
    scene.compose(R, "preview")
    bx = boxes()
    hits = shared(bx)
    print(f"== {name}: {len(bx)} boxes, {len(hits)} shared faces")
    for area, d, a, b, u, w in hits:
        print(f"   {area:>9.2f} cm2  {d}  {a} | {b}   ({u:.1f} x {w:.1f} mm)")
    sys.stdout.flush()


if __name__ == "__main__":
    for name in sys.argv[1:] or sorted(scenes.RECIPES):
        check(name)

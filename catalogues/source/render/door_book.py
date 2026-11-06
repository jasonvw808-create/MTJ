"""The door catalogue's pictures: the hallway of the site's door picture (vignettes.door: the supplied PT 2602
photograph, cut out and set into the wall), framed again for the catalogue's cover (A4, upright) and for the band at
the top of its introduction (1.6 : 1). Same room, light and door; only the camera and the size change.
Usage: python -m render.door_book <cover|intro> <out.png> [preview|check|final]"""
import math
import sys
import bpy
from mathutils import Vector
from . import common, mats, vignettes

VIEWS = {
    # upright, the whole door with floor below it for the title, the console beside it
    "cover": dict(res=(2160, 3031), tgt=(0.5, 0.0, 1.12), az=7.0, dist=2.7, lens=40, shift=(0.0, -0.112)),
    # wide: the door, the console and the light from the window on the wall
    "intro": dict(res=(2400, 1500), tgt=(0.42, 0.0, 1.12), az=14.0, dist=3.55, lens=32, shift=(0.0, 0.0)),
}


def main():
    view, out = sys.argv[1], sys.argv[2]
    q = sys.argv[3] if len(sys.argv) > 3 else "preview"
    common.reset()
    mats._cache.clear()
    sc = vignettes.door(q)
    v = VIEWS[view]
    k = dict(preview=0.4, check=0.6, final=1.0)[q]
    sc.render.resolution_x, sc.render.resolution_y = round(v["res"][0] * k), round(v["res"][1] * k)
    sc.render.resolution_percentage = 100
    old = sc.camera
    tgt = Vector(v["tgt"])
    az = math.radians(v["az"])
    loc = tgt + Vector((math.sin(az) * v["dist"], -math.cos(az) * v["dist"], 0.0))
    focus = (Vector((-0.1, -0.028, 1.1)) - loc).length
    common.camera(sc, tuple(loc), tuple(tgt), lens=v["lens"], dof=focus, fstop=5.6, shift=v["shift"])
    if old is not None:
        bpy.data.objects.remove(old, do_unlink=True)
    common.render(sc, out)


if __name__ == "__main__":
    main()

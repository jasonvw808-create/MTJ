"""Render a sink straight from above on the photographs' plate colour, to check the model
against its product photograph.  Usage: python -m render.test_top <kind> <model> <variant> <out.png>"""
import sys
import math
import bpy
from . import common, geo, mats


def main():
    kind, model, variant, out = sys.argv[1:5]
    samples = int(sys.argv[5]) if len(sys.argv) > 5 else 64
    persp = len(sys.argv) > 6 and sys.argv[6] == "persp"
    sc = common.reset()
    common.cycles(sc, samples=samples, res=(900, 900), look="AgX - Base Contrast", exposure=0.0)
    common.world_color(sc, (0.9, 0.9, 0.9), 0.15)
    if kind == "granite":
        from . import granite as G
        info = G.build(model, variant)
    elif kind == "pressed":
        from . import pressed as P
        info = P.build(model)
    else:
        from . import handmade as H
        info = H.build(model)
    W, D = info["size"]
    # a plate under it, the photographs' colour
    plate = mats.paint((0.89, 0.885, 0.875), rough=0.9, texture=0)
    z0 = -info.get("depth", 0.2) - 0.03
    geo.box(-2, -2, z0 - 0.01, 2, 2, z0, name="plate", mat=plate)
    common.area_light("key", (0.0, -0.4, 2.5), (0, 0, 0), size=(2.5, 2.5), energy=120)
    common.area_light("fill", (-1.5, 0.5, 1.5), (0, 0, 0), size=(1.5, 1.5), energy=25)
    if persp:
        common.camera(sc, (0.0, -1.35, 1.25), (0, 0.02, -0.06), lens=50)
    else:
        common.camera(sc, (0, 0, 3.0), (0, 0, 0), ortho=max(W, D) * 1.12)
    common.render(sc, out)


if __name__ == "__main__":
    main()

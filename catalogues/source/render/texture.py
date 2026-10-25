"""A dark honed-stone surface under raking light, for the catalogue's text pages and back covers.
Usage: python -m render.texture <out.png> [w h]"""
import sys
import math
from . import common, geo, mats


def main():
    out = sys.argv[1]
    w = int(sys.argv[2]) if len(sys.argv) > 2 else 1800
    h = int(sys.argv[3]) if len(sys.argv) > 3 else 2526
    sc = common.reset()
    common.cycles(sc, samples=64, res=(w, h), threshold=0.03, look="AgX - Medium High Contrast", exposure=-1.8)
    common.world_color(sc, (0.002, 0.002, 0.002), 1.0)
    # near-black, with faint light hairlines in the fine (crisp) vein layer and soft darker clouding in the
    # broad one: light broad veins blur into glowing bands, and text has to sit on this
    stone = mats.marble(base=(0.014, 0.0135, 0.013), vein=(0.010, 0.0095, 0.009), vein2=(0.040, 0.038, 0.036), rough=0.42, scale=0.9,
                        vein_width=0.012, warp=3.0, seed=8.0, honed=True)
    geo.box(-1, -1.4, -0.02, 1, 1.4, 0.0, name="slab", mat=stone)
    # light raking across from the upper left, and a faint warm one from the right
    common.area_light("rake", (-1.6, 1.2, 0.35), (0.2, -0.2, 0.0), size=(2.5, 0.4), energy=900, color=common.kelvin(4800), spread=60)
    common.area_light("warm", (1.8, -1.0, 0.5), (0, 0, 0), size=(1.0, 1.0), energy=120, color=common.kelvin(2800), spread=80)
    common.camera(sc, (0, 0, 3.0), (0, 0, 0), ortho=1.0)
    common.render(sc, out)


if __name__ == "__main__":
    main()

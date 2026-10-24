"""All recipes, by name — one per model, plus the extra views the catalogue uses (covers, intro and
range-opener images, details), each a new camera (and for one cover, new light) on a model's kitchen."""
from .scenes_granite import RECIPES as _G
from .scenes_steel import RECIPES as _S
from . import kit

RECIPES = dict(_G)
RECIPES.update(_S)


def variant(base, camera=None, light=None, **over):
    def f():
        R = base()
        if camera:
            cam = dict(R["camera"])
            cam.update(camera)
            R["camera"] = cam
        if light:
            R["light"] = light
        R.update(over)
        return R
    return f


def _moody_cover(ctx):
    kit.moody(ctx, key_dir=(-1.4, -0.7, 1.7), key_power=170, key_k=5200, fill=6, world=(0.004, 0.004, 0.0042), rim_dir=(1.4, 1.2, 0.7),
              rim_power=40, rim_k=3600, top=16, top_k=5000)


PORTRAIT = (2160, 3031)   # 254 ppi on a full A4 page with bleed
WIDE = (2400, 1500)
STRIP = (2400, 1040)
EXTRAS = {
    "cover_granite": variant(_G["gdu8145"], res=PORTRAIT, camera=dict(dist=1.42, elev=31, azim=-24, lens=42, fstop=2.0, tz=-0.04, ty=0.16, sy=-0.06)),
    "cover_stainless": variant(_S["w7646uss"], res=PORTRAIT, light=_moody_cover, exposure=-1.7, look="AgX - Medium High Contrast",
                               camera=dict(dist=1.38, elev=31, azim=22, lens=42, fstop=2.0, tz=-0.04, ty=0.16, sy=-0.06)),
    "intro_granite": variant(_G["gsu7545"], res=WIDE, camera=dict(dist=1.05, elev=19, azim=32, lens=50, fstop=2.0, tz=0.02, ty=0.12, fx=0.0, fy=0.1)),
    "intro_stainless": variant(_S["w7546tsbn"], res=WIDE, camera=dict(dist=0.9, elev=24, azim=-26, lens=55, fstop=2.0, tz=0.05, ty=0.16, fy=0.17)),
    "opener_pressed": variant(_S["lps9643a"], res=PORTRAIT, camera=dict(dist=0.95, elev=52, azim=18, lens=50, fstop=2.8, tx=-0.18, ty=0.0, fx=-0.2, sy=-0.1)),
    "opener_hand": variant(_S["w8050tsb"], res=PORTRAIT, camera=dict(dist=0.95, elev=40, azim=-22, lens=50, fstop=2.4, tx=0.2, ty=0.12, fx=0.25, fy=0.17, sy=-0.1)),
    "closing": variant(_S["w5050tsb"], res=PORTRAIT, camera=dict(dist=1.15, elev=23, azim=27, lens=48, fstop=2.0, tz=0.0, ty=0.08, sy=-0.04)),
    "notes_stainless": variant(_S["wl18"], res=STRIP, camera=dict(dist=1.75, elev=30, azim=-6, lens=40, fstop=3.2, tz=0.02, ty=0.12)),
    "index_granite": variant(_G["gst6045"], res=STRIP, camera=dict(dist=1.5, elev=31, azim=12, lens=45, fstop=2.8, tz=0.0, ty=0.1)),
}
RECIPES.update(EXTRAS)

"""The granite collection's six kitchens."""
import math
from . import mats, props, geo, kitchen, common, kit
from .common import kelvin


def C(r, g, b):
    """sRGB 0-255 -> linear."""
    f = lambda c: (c / 255) / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


# ── GDU 8145 · Pearl Black — warm marble, smoked oak, a dark plaster room, evening ──
def gdu8145():
    stone = mats.marble(base=(0.50, 0.45, 0.38), vein=(0.22, 0.19, 0.16), vein2=(0.38, 0.34, 0.29), rough=0.36, scale=0.55, vein_width=0.014, warp=3.0, seed=2.0, honed=True)
    oak = mats.wood("smoked_oak", along='Z', rough=0.5, seed=1.3)
    plaster = mats.plaster((0.075, 0.069, 0.062), var=0.05, rough=0.9, scale=0.35, bump=0.08)
    brass = mats.metal("brass")
    cer = mats.ceramic((0.75, 0.70, 0.62), matte=True, speck=0.06)
    cer2 = mats.ceramic((0.10, 0.09, 0.085), rough=0.4)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        cab = dict(cab_mat=oak, door="fluted", handle="none")
        kit_back = kitchen.worktop(-2.6, 2.6, yw - 0.62, yw, H, 0.04, stone, [], None)
        kitchen.base_run(-2.6, 2.6, yw - 0.6, H - 0.04, cab, None, depth=0.58)
        kit.shelf(ctx, -2.0, 0.9, 1.58, mat=oak, t=0.045, led=(6, 2700))
        kit.shelf_items(ctx, -2.0, 0.9, 1.58, seed=4, kinds=("vase", "vase2", "bowl", "plates", "jar", "jar", "vase"), palette=[cer, cer2])
        props.board("bb1", -1.2, yw - 0.18, H, w=0.5, d=0.32, t=0.025, wood="walnut")
        props.bottle("bo1", -0.75, yw - 0.18, H, h=0.28, r=0.034, glass=mats.glass((0.55, 0.45, 0.25)), liquid=mats.liquid_oil(), cap=mats.metal("black"))
        props.jar("bj1", 0.8, yw - 0.2, H, r=0.07, h=0.2, mat=cer, lid=oak)
        props.herb_pot("bh1", 1.25, yw - 0.22, H, r=0.08, h=0.13, pot_mat=cer2, seed=4)
        props.board("b1", sx - 0.72, sy + 0.02, H, w=0.46, d=0.30, t=0.03, rot=0.18, wood="walnut")
        props.lemon("l1", sx - 0.70, sy + 0.04, H + 0.03, s=1.0, rot=0.3)
        props.lemon("l2", sx - 0.62, sy - 0.03, H + 0.03, s=0.95, rot=1.9)
        kit.fruit_bowl(ctx, sx + 0.68, sy - 0.02, cer)
        kit.branches(ctx, sx + 1.02, sy + 0.18, cer2, h=0.34, r=0.085)
        props.soap_pump("sp", sx + 0.27, kit.behind(ctx, 0.07), H, mat=mats.glass((0.45, 0.33, 0.18)), pump=brass)

    def light(ctx):
        kit.moody(ctx)

    return dict(model="GDU 8145", kind="granite", variant="pearl", layout="island", island_depth=1.0, run=(-1.35, 1.35),
                height=0.91, thick=0.04, counter=stone, edge="eased", back_y=1.95,
                cab=dict(cab_mat=oak, door="fluted", handle="none"),
                floor=mats.wood("smoked_oak", along='X', rough=0.6, scale=0.5), wall=plaster,
                tap=dict(kind="gooseneck", finish="brass", gap=0.06, height=0.36, reach=0.22),
                build=[build], light=light,
                camera=dict(dist=2.35, elev=27, azim=-21, lens=42, fstop=2.4, tz=0.06, ty=0.5),
                exposure=-1.9)


# ── GST 6045 · Pure White — a Nordic morning: oak worktop, sage shaker, a window ──
def gst6045():
    oak = mats.wood("light_oak", along='X', rough=0.5, seed=0.7, contrast=0.4)
    sage = mats.paint(C(150, 163, 140), rough=0.55)
    plaster = mats.plaster(C(232, 226, 214), var=0.03, rough=0.9, scale=0.4, bump=0.05)
    zel = mats.tile(col=C(236, 234, 226), grout=C(205, 200, 190), w=0.1, h=0.1, gap=0.0025, rough=0.06, var=0.07, zellige=True, offset=0.0)
    frame = mats.metal("black")
    brass = mats.metal("brass")
    cer = mats.ceramic(C(214, 200, 180), matte=True, speck=0.05)
    win = dict(x0=-0.62, x1=0.62, z0=0.91 + 0.48, z1=2.35, frame=frame, mullions=1, transoms=1, sill=mats.wood("white_oak", along='X', contrast=0.4))

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.garden(ctx, y0=yw + 0.2, seed=5, col=(0.10, 0.17, 0.06), ground=False)
        kit.outside_glow(ctx, 2.2)
        # on the sill: herbs and a jug
        props.herb_pot("sill1", -0.42, yw + 0.06, win["z0"], r=0.055, h=0.09, pot_mat=mats.ceramic(C(180, 110, 80), matte=True), seed=7)
        props.herb_pot("sill2", 0.38, yw + 0.06, win["z0"], r=0.05, h=0.085, pot_mat=cer, seed=9)
        # worktop: a ceramic bowl of pears to the left, plates and a towel to the right, utensils
        kit.fruit_bowl(ctx, kit.left(ctx, 0.28), sy + 0.02, cer, r=0.14, fruit=("pear", "pear", "lemon"))
        props.plate_stack("pl", kit.right(ctx, 0.25), sy + 0.08, H, r=0.12, n=4, mat=mats.ceramic(C(240, 238, 232)))
        props.jar("ut", kit.left(ctx, 0.62), yw - 0.12, H, r=0.06, h=0.16, mat=cer)
        props.bottle("oil", kit.right(ctx, 0.62), yw - 0.12, H, h=0.27, r=0.032, glass=mats.glass((0.55, 0.5, 0.3)), liquid=mats.liquid_oil(), cap=brass)
        kit.shelf(ctx, -1.75, -0.8, 1.62, mat=oak, t=0.035)
        kit.shelf_items(ctx, -1.75, -0.8, 1.62, seed=11, kinds=("plates", "cups", "jar"), palette=[cer, mats.ceramic(C(240, 238, 232))])

    def light(ctx):
        kit.daylight(ctx, sun_elev=26, sun_azim=205, sun_power=4.5, sun_k=5800, sky=1.0, fill=14, top=10)
        kit.portal(ctx, win)

    return dict(model="GST 6045", kind="granite", variant="pure", layout="window", run=(-1.9, 1.9), depth=0.64, wall_y=0.32,
                height=0.91, thick=0.038, counter=oak, edge="eased",
                cab=dict(cab_mat=sage, door="shaker", handle="knob", handle_mat=brass, drawers={2: 3}),
                floor=mats.wood("oak", along='X', scale=0.5), wall=plaster, window=win,
                splash=dict(mat=zel, h=0.48),
                tap=dict(kind="gooseneck", where="taphole", hole=(0.0, 0.1944), finish="brass", height=0.34, reach=0.2),
                build=[build], light=light,
                camera=dict(dist=2.05, elev=32, azim=17, lens=38, fstop=4.0, tz=0.05, ty=0.25),
                exposure=-1.2, look="AgX - Base Contrast")


# ── GST 7546 · Pearl Black — black and concrete: a loft workstation ──
def gst7546():
    conc = mats.concrete(base=C(178, 175, 168), rough=0.55, tone=0.08)
    black = mats.paint(C(26, 26, 27), rough=0.5, texture=0.0)
    wallc = mats.concrete(base=C(120, 118, 114), rough=0.8, tone=0.1, pores=False)
    steelb = mats.metal("black")
    oak = mats.wood("oak", along='X', contrast=0.5)
    cer = mats.ceramic(C(236, 233, 226), rough=0.2)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        # an oak shelf on black steel rods, with a warm strip under it
        z = 1.55
        kit.shelf(ctx, -1.3, 1.1, z, depth=0.24, mat=oak, t=0.03, led=(5, 2800))
        for x in (-1.1, 0.9):
            props.place([geo.tube([(x, yw, z - 0.03), (x, yw - 0.22, z - 0.03)], 0.006, 10, name="rod", mat=steelb)])
        kit.shelf_items(ctx, -1.3, 1.1, z, seed=21, kinds=("bowl", "plates", "jar", "jar", "vase", "books", "cups"), palette=[cer, mats.ceramic(C(40, 40, 40), rough=0.4)])
        kit.board_with(ctx, kit.left(ctx, 0.3), sy - 0.02, rot=-0.12, wood="oak", fruit="lime", n=3)
        props.plate_stack("bw", kit.right(ctx, 0.24), sy + 0.06, H, r=0.1, n=3, mat=cer)
        props.cup("esp", kit.right(ctx, 0.45), sy - 0.12, H, r=0.032, h=0.06, mat=cer)
        kit.branches(ctx, kit.right(ctx, 0.62), yw - 0.16, mats.ceramic(C(30, 30, 30), rough=0.5), h=0.28, r=0.07, leaf=(0.35, 0.30, 0.18), seed=8, n_leaves=110)

    def light(ctx):
        kit.moody(ctx, key_dir=(-1.6, -0.5, 1.5), key_power=210, key_k=5600, fill=14, world=(0.012, 0.012, 0.012), rim_power=20, top=24)

    return dict(model="GST 7546", kind="granite", variant="pearl", layout="wall", run=(-1.7, 1.7), depth=0.64, wall_y=0.32,
                height=0.92, thick=0.025, counter=conc, edge="square",
                cab=dict(cab_mat=black, door="groove", handle="edge", handle_mat=mats.metal("gunmetal")),
                floor=mats.concrete(base=C(90, 88, 84), rough=0.5), wall=wallc,
                splash=dict(mat=conc, h=0.62),
                tap=None, build=[build], light=light,
                camera=dict(dist=1.95, elev=37, azim=16, lens=44, fstop=3.2, tz=0.04, ty=0.2),
                exposure=-1.7)


# ── GSU 6045 · Titanium Grey — Japandi: pale ash, white quartz, limewash ──
def gsu6045():
    quartz = mats.quartz(base=C(232, 229, 222), speck=C(170, 165, 158), dens=0.035, rough=0.3)
    ash = mats.wood("ash", along='Z', rough=0.55, contrast=0.4)
    lime = mats.plaster(C(222, 214, 200), var=0.04, rough=0.92, scale=0.5, bump=0.06)
    blk = mats.metal("black")
    cer = mats.ceramic(C(205, 196, 182), matte=True, speck=0.08)
    cer2 = mats.ceramic(C(92, 80, 70), matte=True)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        # a low oak ledge along the splash
        geo.box(-1.5, yw - 0.1, H + 0.14, 1.5, yw, H + 0.16, name="ledge", mat=mats.wood("light_oak", along='X', contrast=0.4))
        props.vase("lv1", -0.95, yw - 0.05, H + 0.16, h=0.16, r=0.05, mat=cer, style=2)
        props.cup("lc1", -0.75, yw - 0.05, H + 0.16, r=0.035, h=0.07, mat=cer2, handle=False)
        props.bowl("lb1", 0.82, yw - 0.05, H + 0.16, r=0.07, h=0.045, mat=cer)
        # a teapot-ish jar, cups and a tray on the left; a branch on the right
        props.board("tray", kit.left(ctx, 0.3), sy + 0.02, H, w=0.36, d=0.24, t=0.018, rot=0.05, wood="light_oak", handle=False)
        props.jar("tea", kit.left(ctx, 0.36), sy + 0.03, H + 0.018, r=0.055, h=0.11, mat=cer2, lid=cer2)
        props.cup("c1", kit.left(ctx, 0.22), sy - 0.03, H + 0.018, r=0.032, h=0.06, mat=cer, handle=False)
        props.cup("c2", kit.left(ctx, 0.16), sy + 0.06, H + 0.018, r=0.032, h=0.06, mat=cer, handle=False)
        kit.branches(ctx, kit.right(ctx, 0.35), sy + 0.1, cer, h=0.22, r=0.06, leaf=(0.14, 0.17, 0.08), seed=12, height=0.42, style=1, n_leaves=90)
        props.towel("tw", kit.right(ctx, 0.62), sy - 0.06, H, w=0.26, d=0.14, t=0.009, color=C(170, 160, 142), rot=-0.05)

    def light(ctx):
        kit.daylight(ctx, sun_elev=30, sun_azim=250, sun_power=3.2, sky=0.9, key_dir=(-1.8, -0.4, 1.2), key_power=110, key_k=6000, fill=12, top=10)

    return dict(model="GSU 6045", kind="granite", variant="titan", layout="wall", run=(-1.6, 1.6), depth=0.64, wall_y=0.32,
                height=0.9, thick=0.02, counter=quartz, edge="square",
                cab=dict(cab_mat=ash, door="slatted", handle="none"),
                floor=mats.wood("ash", along='X', scale=0.5), wall=lime, side_wall=None,
                splash=dict(mat=lime, h=0.7),
                tap=dict(kind="gooseneck", finish="black", gap=0.05, height=0.32, reach=0.19),
                build=[build], light=light,
                camera=dict(dist=1.75, elev=41, azim=-11, lens=48, fstop=4.0, tz=0.0, ty=0.12),
                exposure=-1.3, look="AgX - Base Contrast")


# ── GSU 7545 · Pure White — emerald lacquer and black marble, an island at night ──
def gsu7545():
    nero = mats.marble(base=(0.014, 0.014, 0.015), vein=(0.30, 0.30, 0.29), vein2=(0.06, 0.06, 0.06), rough=0.14, scale=0.6, vein_width=0.008, warp=3.5, seed=5.0)
    green = mats.paint(C(22, 58, 46), rough=0.35, coat=0.15)
    plaster = mats.plaster(C(70, 74, 66), var=0.04, rough=0.9, scale=0.4, bump=0.06)
    brass = mats.metal("brass_polished")
    cer = mats.ceramic(C(236, 232, 224), rough=0.2)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        cab = dict(cab_mat=green, door="slab", handle="vbar", handle_mat=brass)
        kitchen.worktop(-2.6, 2.6, yw - 0.62, yw, H, 0.03, nero, [], None)
        kitchen.base_run(-2.6, 2.6, yw - 0.6, H - 0.03, cab, None, depth=0.58)
        kit.uppers(ctx, -2.6, -0.3, 1.5, 2.3, dict(cab_mat=green, door="slab", handle="none"), led=(5, 2700))
        kit.shelf(ctx, 0.0, 1.6, 1.55, depth=0.22, mat=brass, t=0.012, led=(4, 2700))
        kit.shelf_items(ctx, 0.0, 1.6, 1.55, seed=31, kinds=("vase", "bowl", "jar", "vase2"), palette=[cer, mats.ceramic(C(30, 60, 50), rough=0.3)])
        kit.fruit_bowl(ctx, kit.left(ctx, 0.3), sy + 0.04, mats.metal("brass"), r=0.13, fruit=("lemon", "lemon", "lemon", "lime"))
        kit.branches(ctx, kit.right(ctx, 0.42), sy + 0.12, cer, h=0.3, r=0.08, leaf=(0.2, 0.28, 0.24), seed=15, n_leaves=150)
        props.wine_glass("wg1", kit.right(ctx, 0.18), sy - 0.14, H)
        props.wine_glass("wg2", kit.right(ctx, 0.27), sy - 0.06, H)

    def light(ctx):
        kit.moody(ctx, key_dir=(-1.6, -0.8, 1.6), key_power=170, key_k=4600, fill=8, world=(0.004, 0.005, 0.0045), rim_power=24, rim_k=2800, top=18)

    return dict(model="GSU 7545", kind="granite", variant="pure", layout="island", island_depth=1.0, run=(-1.3, 1.3),
                height=0.91, thick=0.03, counter=nero, edge="eased", back_y=1.95,
                cab=dict(cab_mat=green, door="slab", handle="vbar", handle_mat=brass),
                floor=mats.wood("walnut", along='X', scale=0.5), wall=plaster,
                tap=dict(kind="gooseneck", finish="brass_polished", gap=0.06, height=0.37, reach=0.22),
                build=[build], light=light,
                camera=dict(dist=2.2, elev=30, azim=19, lens=42, fstop=2.8, tz=0.05, ty=0.45),
                exposure=-1.8)


# ── GSU 8045 · Titanium Grey — travertine and terracotta in late sun ──
def gsu8045():
    trav = mats.travertine(base=C(200, 180, 150), rough=0.45)
    walnut = mats.wood("walnut", along='Z', rough=0.5, contrast=0.5)
    terra = mats.tile(col=C(158, 98, 74), grout=C(196, 182, 162), w=0.13, h=0.065, gap=0.003, rough=0.12, var=0.1, zellige=True, offset=0.5)
    lime = mats.plaster(C(226, 214, 196), var=0.04, rough=0.9, scale=0.5, bump=0.06)
    nickel = mats.metal("nickel")
    cer = mats.ceramic(C(226, 216, 196), matte=True, speck=0.05)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.shelf(ctx, -1.6, -0.55, 1.6, depth=0.24, mat=mats.wood("walnut", along='X', contrast=0.4), t=0.04)
        kit.shelf_items(ctx, -1.6, -0.55, 1.6, seed=41, kinds=("jar", "bowl", "vase"), palette=[cer, mats.ceramic(C(150, 80, 50), matte=True)])
        # bread on a board, oil, oranges
        props.board("bd", kit.left(ctx, 0.32), sy, H, w=0.5, d=0.3, t=0.03, rot=-0.1, wood="oak")
        loaf = props._ellipsoid("loaf", kit.left(ctx, 0.3), sy + 0.01, H + 0.075, 0.13, 0.075, 0.05, mats.fruit(C(150, 95, 45), 0.7, 0.6, 120), None)
        kit.oil_and_salt(ctx, kit.left(ctx, 0.62), yw - 0.14)
        kit.fruit_bowl(ctx, kit.right(ctx, 0.3), sy + 0.05, cer, r=0.14, fruit=("orange", "orange", "orange", "lime"))
        props.vase("jug", kit.right(ctx, 0.62), yw - 0.15, H, h=0.26, r=0.075, neck=0.04, mat=mats.ceramic(C(160, 85, 50), matte=True), style=2)

    def light(ctx):
        kit.daylight(ctx, sun_elev=16, sun_azim=75, sun_power=5.0, sun_k=3600, sky=0.6, key_dir=(1.8, -0.3, 1.1), key_power=70, key_k=4200, fill=10, top=8, top_k=4200)

    return dict(model="GSU 8045", kind="granite", variant="titan", layout="wall", run=(-1.7, 1.7), depth=0.64, wall_y=0.32,
                height=0.91, thick=0.03, counter=trav, edge="eased",
                cab=dict(cab_mat=walnut, door="slab", handle="leather"),
                floor=mats.terrazzo(base=C(200, 182, 160)), wall=lime,
                splash=dict(mat=terra, h=0.58),
                tap=dict(kind="bridge", finish="nickel", gap=0.055, height=0.3, reach=0.2),
                build=[build], light=light,
                camera=dict(dist=1.9, elev=34, azim=18, lens=44, fstop=3.5, tz=0.03, ty=0.18),
                exposure=-1.5)


RECIPES = {"gdu8145": gdu8145, "gst6045": gst6045, "gst7546": gst7546, "gsu6045": gsu6045, "gsu7545": gsu7545, "gsu8045": gsu8045}

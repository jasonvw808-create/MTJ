"""The stainless steel collection's twenty-five kitchens."""
import math
from . import mats, props, geo, kitchen, common, kit
from .common import kelvin
from .scenes_granite import C


def _r(model, kind, layout="wall", **kw):
    d = dict(model=model, kind=kind, layout=layout, run=(-1.7, 1.7), depth=0.64, wall_y=0.32, height=0.91, thick=0.03, edge="eased")
    d.update(kw)
    return d


# ════════════════════════════ PRESSED ════════════════════════════

# LPS 5040 — a compact pantry kitchen: powder blue, terrazzo, square white tiles
def lps5040():
    terr = mats.terrazzo(base=C(232, 226, 216), chips=(C(150, 140, 130), C(250, 248, 244), C(90, 86, 82), C(200, 160, 130)), scale=38, rough=0.3, density=0.13, contrast=0.8)
    blue = mats.paint(C(158, 180, 194), rough=0.5)
    tile = mats.tile(col=C(242, 241, 236), grout=C(190, 188, 182), w=0.1, h=0.1, gap=0.0022, rough=0.05, var=0.03, offset=0.0)
    wall = mats.plaster(C(236, 232, 224), var=0.03)
    oak = mats.wood("light_oak", along='X', contrast=0.45)
    cer = mats.ceramic(C(240, 238, 232))

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        # shelves from one pantry column to the other
        for z in (1.5, 1.86):
            kit.shelf(ctx, -0.95, 0.95, z, depth=0.22, mat=oak, t=0.03)
        kit.shelf_items(ctx, -0.95, 0.95, 1.5, seed=51, kinds=("jar", "jar", "jar", "jar", "plant", "jar"))
        kit.shelf_items(ctx, -0.95, 0.95, 1.86, seed=52, kinds=("plates", "cups", "bowl"), palette=[cer, mats.ceramic(C(158, 180, 194))])
        # a tall pantry column on each side
        for (a, b) in ((-1.55, -0.95), (0.95, 1.55)):
            geo.box(a, yw - 0.6, 0.0, b, yw, 2.3, name="tall", mat=blue)
            kitchen.door(a, b, 0.1, 2.25, yw - 0.6, "slab", blue, None, handle="knob", hmat=oak, hpos="mid")
        props.bowl("tb", kit.right(ctx, 0.2), sy - 0.02, ctx["H"], r=0.1, h=0.06, mat=mats.ceramic(C(236, 232, 224), matte=True))
        props.lemon("tl", kit.right(ctx, 0.2), sy - 0.02, ctx["H"] + 0.012, kind="lemon", s=0.9)
        props.soap_pump("sp", kit.left(ctx, 0.12), kit.behind(ctx, 0.0), H, mat=mats.glass((0.8, 0.85, 0.8)), pump=mats.metal("chrome"))
        props.herb_pot("hp", kit.left(ctx, 0.22), sy - 0.05, H, r=0.055, h=0.09, pot_mat=mats.ceramic(C(200, 120, 90), matte=True), seed=17)

    def light(ctx):
        kit.natural(ctx, side=-1, power=150, sun=True, sun_elev=30, sun_azim=290, sun_power=5.5, room=0.3)

    return _r("LPS 5040", "pressed", run=(-0.95, 0.95), depth=0.6, counter=terr, edge="square",
              cab=dict(cab_mat=blue, door="slab", handle="knob", handle_mat=oak, door_w=0.47),
              floor=mats.wood("light_oak", along='X'), wall=wall, splash=dict(mat=tile, h=0.62),
              tap=dict(kind="bridge", where="wall", h=0.36, finish="steel", reach=0.24),
              build=[build], light=light, front_margin=0.06,
              camera=dict(dist=1.85, elev=34, azim=-14, lens=50, fstop=3.2, tz=0.06, ty=0.2), exposure=-1.2, look="AgX - Base Contrast")


# LPS 7540 A — classic white shaker, honey oak worktop, subway tiles, wall cabinets
def lps7540a():
    oak = mats.wood("oak", along='X', rough=0.45, contrast=0.5, coat=0.15)
    white = mats.paint(C(238, 236, 230), rough=0.45)
    sub = mats.tile(col=C(244, 243, 239), grout=C(200, 198, 192), w=0.15, h=0.075, gap=0.002, rough=0.04, var=0.025)
    wall = mats.plaster(C(232, 229, 222), var=0.02)
    blk = mats.metal("black")

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.uppers(ctx, -1.7, 1.7, 1.55, 2.3, dict(cab_mat=white, door="shaker", handle="cup", handle_mat=blk), led=(6, 3200))
        kit.board_with(ctx, kit.right(ctx, 0.3), sy - 0.02, rot=0.12, wood="walnut", fruit="apple", n=2)
        props.jar("coffee", kit.left(ctx, 0.35), yw - 0.12, H, r=0.06, h=0.18, mat=mats.ceramic(C(240, 238, 232)), lid=mats.wood("walnut"))
        props.jar("tea", kit.left(ctx, 0.5), yw - 0.12, H, r=0.05, h=0.14, mat=mats.ceramic(C(240, 238, 232)), lid=mats.wood("walnut"))
        kit.branches(ctx, kit.right(ctx, 0.66), yw - 0.14, mats.glass((0.9, 0.95, 0.92)), h=0.24, r=0.06, leaf=(0.16, 0.24, 0.1), seed=19, n_leaves=110, style=1)

    def light(ctx):
        kit.natural(ctx, side=1, power=160, sun=True, sun_elev=28, sun_azim=68, sun_power=5.0, room=0.3)

    return _r("LPS 7540 A", "pressed", counter=oak, cab=dict(cab_mat=white, door="shaker", handle="cup", handle_mat=blk),
              floor=mats.wood("oak", along='X'), wall=wall, splash=dict(mat=sub, h=0.64),
              tap=dict(kind="gooseneck", finish="black", gap=0.045, height=0.33, reach=0.2, dx=0.17),
              build=[build], light=light,
              camera=dict(dist=2.1, elev=33, azim=13, lens=50, fstop=3.2, tz=0.04, ty=0.15), exposure=-1.2, look="AgX - Base Contrast")


# LPS 8643 A — Mediterranean: whitewash, blue-and-white zellige, limestone, a sunny window
def lps8643a():
    lime = mats.marble(base=C(222, 216, 200), vein=C(188, 180, 162), vein2=C(206, 200, 184), rough=0.4, vein_width=0.02, seed=7.0, honed=True)
    wash = mats.plaster(C(240, 236, 228), var=0.05, rough=0.95, scale=0.5, bump=0.18)
    zel = mats.tile(col=C(28, 60, 112), grout=C(225, 222, 214), w=0.1, h=0.1, gap=0.003, rough=0.22, var=0.16, zellige=True, offset=0.0)
    cab = mats.paint(C(232, 226, 214), rough=0.6)
    brass = mats.metal("brass")
    win = dict(x0=-0.55, x1=0.55, z0=0.91 + 0.55, z1=2.3, frame=mats.paint(C(40, 70, 120), 0.5), mullions=1, transoms=2)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.garden(ctx, y0=yw + 0.3, seed=8, col=(0.13, 0.17, 0.07), n=7, ground=False)
        kit.outside_glow(ctx, 2.4)
        kit.outside_wall(ctx, y=yw + 3.5, mat=mats.plaster(C(245, 240, 230), var=0.05))
        kit.fruit_bowl(ctx, kit.left(ctx, 0.28), sy + 0.03, mats.ceramic(C(236, 232, 222), speck=0.04), r=0.14, fruit=("lemon", "lemon", "lemon", "lemon", "lime"))
        kit.branches(ctx, kit.right(ctx, 0.32), sy + 0.12, mats.ceramic(C(170, 95, 60), matte=True), h=0.3, r=0.08, leaf=(0.18, 0.22, 0.14), seed=21, n_leaves=170, style=2)
        props.bottle("ob", kit.right(ctx, 0.6), yw - 0.12, H, h=0.3, r=0.034, glass=mats.glass((0.4, 0.55, 0.35)), liquid=mats.liquid_oil(), cap=mats.paint(C(150, 110, 70), 0.6, texture=0))
        props.herb_pot("sill", 0.36, yw + 0.045, win["z0"], r=0.041, h=0.075, pot_mat=mats.ceramic(C(180, 100, 60), matte=True), seed=23)

    def light(ctx):
        kit.natural(ctx, side=-1, power=120, sun=True, sun_elev=34, sun_azim=165, sun_power=6.0, room=0.3, back_window=win)

    return _r("LPS 8643 A", "pressed", layout="window", counter=lime, cab=dict(cab_mat=cab, door="shaker", handle="knob", handle_mat=brass),
              floor=mats.tile(col=C(176, 98, 64), grout=C(140, 120, 100), w=0.3, h=0.3, gap=0.006, rough=0.6, var=0.12, along='XY', offset=0.0),
              wall=wash, window=win, splash=dict(mat=zel, h=0.55),
              tap=dict(kind="bridge", finish="brass", gap=0.05, height=0.3, reach=0.2, dx=0.19),
              build=[build], light=light,
              camera=dict(dist=2.25, elev=31, azim=-16, lens=45, fstop=3.2, tz=0.04, ty=0.2), exposure=-1.2, look="AgX - Base Contrast")


# LPS 9643 A — industrial loft: dark concrete, black steel, charcoal tiles, Edison light
def lps9643a():
    conc = mats.concrete(base=C(92, 90, 86), rough=0.5, tone=0.12)
    blackc = mats.paint(C(30, 31, 32), rough=0.55)
    # pale glazed tiles behind the sink: the flat steel drainboard mirrors the wall, and it should read as steel
    tiles = mats.tile(col=C(206, 204, 198), grout=C(150, 147, 141), w=0.2, h=0.065, gap=0.003, rough=0.12, var=0.06)
    brick = mats.plaster(C(132, 122, 112), var=0.08, rough=0.9)
    steel = mats.metal("black")
    oak = mats.wood("smoked_oak", along='X', contrast=0.5)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        for z in (1.55, 1.95):
            kit.shelf(ctx, -1.5, 1.4, z, depth=0.26, mat=oak, t=0.035)
        for x in (-1.45, 1.35):
            geo.box(x, yw - 0.26, 1.2, x + 0.02, yw, 2.3, name="upright", mat=steel)
        # the things on the shelves stand between the two uprights
        kit.shelf_items(ctx, -1.43, 1.35, 1.55, seed=61, kinds=("bottle", "jar", "bowl", "books", "jar", "plant", "cups"), palette=[mats.ceramic(C(230, 228, 222)), mats.ceramic(C(60, 60, 60), rough=0.4)])
        kit.shelf_items(ctx, -1.43, 1.35, 1.95, seed=62, kinds=("plates", "vase", "books", "jar", "bowl"))
        props.board("bd", kit.left(ctx, 0.25), sy + 0.02, H, w=0.42, d=0.28, t=0.03, rot=0.1, wood="smoked_oak")
        props.cup("mug", kit.right(ctx, 0.2), sy - 0.06, H, r=0.04, h=0.09, mat=mats.ceramic(C(236, 234, 228)))
        props.herb_pot("hp", kit.right(ctx, 0.45), yw - 0.18, H, r=0.07, h=0.12, pot_mat=mats.concrete(base=C(130, 128, 122)), seed=27)

    def light(ctx):
        kit.natural(ctx, side=1, power=180, sun=True, sun_elev=26, sun_azim=70, sun_power=5.5, room=0.3)

    return _r("LPS 9643 A", "pressed", counter=conc, edge="square", cab=dict(cab_mat=blackc, door="slab", handle="bar", handle_mat=mats.metal("steel")),
              floor=mats.concrete(base=C(70, 68, 64)), wall=brick, splash=dict(mat=tiles, h=0.62),
              tap=dict(kind="pulldown", finish="black", gap=0.045, height=0.42, reach=0.22, dx=0.2),
              build=[build], light=light,
              camera=dict(dist=2.15, elev=34, azim=18, lens=50, fstop=3.2, tz=0.04, ty=0.16), exposure=-1.2)


# LPS 10050 A — modern farmhouse: charcoal-blue shaker, butcher block, a window to the garden
def lps10050a():
    oak = mats.wood("oak", along='X', rough=0.45, contrast=0.55, coat=0.1)
    blue = mats.paint(C(62, 72, 84), rough=0.5)
    vert = mats.tile(col=C(240, 238, 232), grout=C(210, 206, 198), w=0.075, h=0.3, gap=0.002, rough=0.05, var=0.03, offset=0.5, along='XZ')
    wall = mats.plaster(C(234, 230, 222), var=0.03)
    brass = mats.metal("brass")
    win = dict(x0=-0.75, x1=0.75, z0=0.91 + 0.42, z1=2.25, frame=mats.paint(C(40, 40, 40), 0.5), mullions=2, transoms=0)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.garden(ctx, y0=yw + 0.3, seed=11, col=(0.11, 0.18, 0.06), n=8, ground=False)
        kit.outside_glow(ctx, 2.2)
        kit.board_with(ctx, kit.right(ctx, 0.3), sy + 0.0, rot=-0.08, wood="walnut", fruit="apple", n=3)
        props.bowl("eggs", kit.left(ctx, 0.3), sy + 0.06, H, r=0.12, h=0.07, mat=mats.ceramic(C(236, 234, 226), matte=True))
        # eggs lying on their sides, round the bowl, apart; settle lets them down onto it
        for i, (dx, dy, a) in enumerate([(-0.034, 0.004, 1.57), (0.036, 0.022, 2.11), (0.004, -0.044, 0.1)]):
            egg = props._ellipsoid(f"egg{i}", kit.left(ctx, 0.3) + dx, sy + 0.06 + dy, H + 0.045, 0.03, 0.022, 0.022, mats.fruit(C(220, 190, 160), 0.6, 0.02, 100), None)
            egg.rotation_euler = (0, 0, a)
            props.rest([egg])
        props.herb_pot("sill1", -0.5, yw + 0.045, win["z0"], r=0.041, h=0.075, seed=29)
        props.herb_pot("sill2", 0.48, yw + 0.045, win["z0"], r=0.041, h=0.075, seed=31)
        props.towel("tw", kit.left(ctx, 0.55), sy - 0.1, H, w=0.25, d=0.15, t=0.01, color=C(214, 206, 190), rot=0.12)

    def light(ctx):
        kit.natural(ctx, side=1, power=120, sun=True, sun_elev=28, sun_azim=200, sun_power=6.0, room=0.3, back_window=win)

    return _r("LPS 10050 A", "pressed", layout="window", run=(-1.9, 1.9), depth=0.66, counter=oak,
              cab=dict(cab_mat=blue, door="shaker", handle="cup", handle_mat=brass, drawers={0: 3}),
              floor=mats.wood("oak", along='X'), wall=wall, window=win, splash=dict(mat=vert, h=0.42),
              tap=dict(kind="bridge", finish="brass", gap=0.05, height=0.3, reach=0.22, dx=0.12),
              build=[build], light=light,
              camera=dict(dist=2.4, elev=31, azim=14, lens=45, fstop=3.2, tz=0.04, ty=0.2), exposure=-1.2, look="AgX - Base Contrast")


# WL 03 — tropical modern: teak slats, white terrazzo, palms in the light
def wl03():
    terr = mats.terrazzo(base=C(238, 234, 226), chips=(C(170, 160, 150), C(255, 252, 248), C(120, 110, 100), C(190, 150, 120)), scale=30, rough=0.25, density=0.12, contrast=0.75)
    teak = mats.wood("teak", along='Z', rough=0.5, contrast=0.5)
    wall = mats.plaster(C(236, 228, 214), var=0.04, bump=0.1)
    brass = mats.metal("brass")

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        # a big leafy plant at the end of the run, a rattan-like pendant
        props.herb_pot("palm", kit.right(ctx, 0.42), yw - 0.17, H, r=0.1, h=0.18, pot_mat=mats.ceramic(C(220, 214, 200), matte=True), seed=33, size=0.3, leaf_col=(0.06, 0.15, 0.04))
        props.branch("palm_br", kit.right(ctx, 0.42), yw - 0.17, H + 0.16, height=0.7, leaf_col=(0.07, 0.16, 0.05), n_leaves=70, seed=35, leaf_len=0.15, leaf_w=0.055, stems=6)
        kit.fruit_bowl(ctx, kit.left(ctx, 0.3), sy + 0.02, mats.wood("teak", along='X'), r=0.15, fruit=("lime", "lime", "orange", "lime"))
        props.tumbler("gl", kit.right(ctx, 0.16), sy - 0.12, H)
        props.bottle("wb", kit.right(ctx, 0.2), sy + 0.0, H, h=0.26, r=0.035, glass=mats.glass((0.92, 0.96, 0.94)), cap=mats.wood("teak"))
        kit.shelf(ctx, -1.4, 0.2, 1.62, depth=0.22, mat=mats.wood("teak", along='X'), t=0.035)
        kit.shelf_items(ctx, -1.4, 0.2, 1.62, seed=71, kinds=("bowl", "plant", "jar", "vase"))

    def light(ctx):
        kit.natural(ctx, side=-1, power=160, sun=True, sun_elev=40, sun_azim=300, sun_power=6.0, room=0.3)

    return _r("WL 03", "pressed", run=(-1.5, 1.5), counter=terr, edge="square", cab=dict(cab_mat=teak, door="slatted", handle="none"),
              floor=mats.terrazzo(base=C(220, 214, 204)), wall=wall, splash=dict(mat=terr, h=0.12),
              tap=dict(kind="gooseneck", finish="brass", gap=0.05, height=0.34, reach=0.2),
              build=[build], light=light,
              camera=dict(dist=2.0, elev=34, azim=-12, lens=50, fstop=3.2, tz=0.04, ty=0.16), exposure=-1.25, look="AgX - Medium High Contrast")


# WL 05 A — navy shaker, white marble, brass
def wl05a():
    cal = mats.marble(base=C(238, 236, 232), vein=C(120, 116, 110), vein2=C(190, 186, 180), rough=0.12, vein_width=0.011, seed=9.0, scale=0.42,
                      density=0.6, warp=6.0, halo=0.12)
    navy = mats.paint(C(34, 46, 70), rough=0.45)
    wall = mats.plaster(C(228, 224, 216), var=0.03)
    brass = mats.metal("brass")
    cer = mats.ceramic(C(244, 242, 236))

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.shelf(ctx, -1.6, 1.6, 1.62, depth=0.22, mat=brass, t=0.01, led=(4, 3000))
        kit.shelf_items(ctx, -1.6, 1.6, 1.62, seed=81, kinds=("plates", "vase", "bowl", "jar", "plates", "cups"), palette=[cer, mats.ceramic(C(34, 46, 70), rough=0.3)])
        kit.fruit_bowl(ctx, kit.right(ctx, 0.3), sy + 0.04, mats.metal("brass"), r=0.13, fruit=("lemon", "lemon", "lemon"))
        props.vessel("mortar", kit.left(ctx, 0.25), sy + 0.06, H, [(0.05, 0.0), (0.065, 0.02), (0.07, 0.07)], cal, None, thick=0.012)
        kit.branches(ctx, kit.left(ctx, 0.6), yw - 0.15, cer, h=0.3, r=0.07, leaf=(0.15, 0.2, 0.12), seed=37, n_leaves=130)

    def light(ctx):
        kit.natural(ctx, side=1, power=170, sun=True, sun_elev=30, sun_azim=70, sun_power=5.0, room=0.3)

    return _r("WL 05 A", "pressed", depth=0.68, counter=cal, cab=dict(cab_mat=navy, door="shaker", handle="bar", handle_mat=brass),
              floor=mats.wood("oak", along='X'), wall=wall, splash=dict(mat=cal, h=0.62),
              tap=dict(kind="bridge", finish="brass", gap=0.05, height=0.3, reach=0.22),
              build=[build], light=light,
              camera=dict(dist=2.05, elev=34, azim=15, lens=50, fstop=3.2, tz=0.03, ty=0.16), exposure=-1.2, look="AgX - Base Contrast")


# WL 07 — mid-century: walnut slab, ochre gloss tiles, white quartz, a globe pendant
def wl07():
    quartz = mats.quartz(base=C(238, 236, 230), speck=C(180, 176, 170), dens=0.03, rough=0.15)
    walnut = mats.wood("walnut", along='X', rough=0.4, contrast=0.55, coat=0.2)
    ochre = mats.tile(col=C(236, 228, 212), grout=C(206, 198, 184), w=0.15, h=0.15, gap=0.0025, rough=0.06, var=0.05, offset=0.0, zellige=True)
    wall = mats.plaster(C(232, 226, 214), var=0.03)
    chrome = mats.metal("chrome")

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        props.board("tray", kit.left(ctx, 0.3), sy + 0.02, H, w=0.4, d=0.26, t=0.02, rot=0.0, wood="teak", handle=False)
        props.vase("v1", kit.left(ctx, 0.36), sy + 0.03, H + 0.02, h=0.22, r=0.06, neck=0.025, mat=mats.ceramic(C(200, 90, 40), rough=0.3), style=0)
        props.cup("cp", kit.left(ctx, 0.2), sy - 0.03, H + 0.02, r=0.035, h=0.07, mat=mats.ceramic(C(236, 234, 228)))
        props.book_stack("bk", kit.right(ctx, 0.35), yw - 0.14, H, n=3, seed=41)
        props.vase("v2", kit.right(ctx, 0.62), yw - 0.14, H, h=0.3, r=0.07, neck=0.03, mat=mats.ceramic(C(196, 120, 40), rough=0.3), style=0)
        kit.uppers(ctx, -1.7, 1.7, 1.62, 2.3, dict(cab_mat=walnut, door="slab", handle="edge", handle_mat=mats.metal("brass")), led=(4, 3000))

    def light(ctx):
        kit.golden(ctx, side=-1, sun_elev=16, sun_azim=285, sun_power=5.0, sun_k=3800, room=0.45, fill=100)

    return _r("WL 07", "pressed", counter=quartz, cab=dict(cab_mat=walnut, door="slab", handle="edge", handle_mat=mats.metal("brass")),
              floor=mats.terrazzo(base=C(210, 200, 186)), wall=wall, splash=dict(mat=ochre, h=0.71),
              tap=dict(kind="gooseneck", finish="chrome", gap=0.05, height=0.34, reach=0.2, dx=-0.17),
              build=[build], light=light,
              camera=dict(dist=2.1, elev=33, azim=-18, lens=50, fstop=3.2, tz=0.03, ty=0.15), exposure=-1.1)


# WL 11 — a family island: warm terrazzo, soft grey-blue, wooden shelves and plants behind
def wl11():
    terr = mats.terrazzo(base=C(226, 214, 198), chips=(C(170, 120, 90), C(245, 240, 232), C(110, 100, 92), C(200, 170, 140)), scale=30, rough=0.3, density=0.14, contrast=0.85)
    grey = mats.paint(C(170, 180, 186), rough=0.5)
    wall = mats.plaster(C(230, 224, 214), var=0.03)
    oak = mats.wood("light_oak", along='X', contrast=0.45)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        cab = dict(cab_mat=grey, door="shaker", handle="knob", handle_mat=oak)
        kitchen.worktop(-2.6, 2.6, yw - 0.62, yw, H, 0.03, terr, [], None)
        kitchen.base_run(-2.6, 2.6, yw - 0.6, H - 0.03, cab, None, depth=0.58)
        for z in (1.5, 1.88):
            kit.shelf(ctx, -2.0, 1.4, z, depth=0.24, mat=oak, t=0.035)
        kit.shelf_items(ctx, -2.0, 1.4, 1.5, seed=91, kinds=("plant", "jar", "bowl", "plates", "jar", "plant", "cups"))
        kit.shelf_items(ctx, -2.0, 1.4, 1.88, seed=92, kinds=("books", "vase", "plant", "bowl", "jar"))
        kit.fruit_bowl(ctx, kit.right(ctx, 0.32), sy + 0.03, mats.ceramic(C(240, 238, 232)), r=0.15, fruit=("apple", "apple", "orange", "apple"))
        props.board("bd", kit.left(ctx, 0.3), sy + 0.0, H, w=0.42, d=0.3, t=0.03, rot=0.2, wood="oak")
        kit.branches(ctx, kit.left(ctx, 0.65), sy + 0.15, mats.glass((0.9, 0.95, 0.92)), h=0.22, r=0.06, leaf=(0.14, 0.24, 0.08), seed=43, height=0.4, style=1, n_leaves=120)

    def light(ctx):
        kit.natural(ctx, side=-1, power=170, sun=True, sun_elev=30, sun_azim=290, sun_power=5.0, room=0.32)

    return _r("WL 11", "pressed", layout="island", island_depth=1.0, run=(-1.4, 1.4), back_y=1.95, counter=terr,
              cab=dict(cab_mat=grey, door="shaker", handle="knob", handle_mat=oak),
              floor=mats.wood("light_oak", along='X'), wall=wall,
              tap=dict(kind="pulldown", finish="black", gap=0.06, height=0.42, reach=0.22, dx=-0.08),
              build=[build], light=light,
              camera=dict(dist=2.5, elev=31, azim=-12, lens=45, fstop=3.2, tz=0.05, ty=0.4), exposure=-1.2, look="AgX - Base Contrast")


# WL 12 — minimal microcement in soft north light
def wl12():
    micro = mats.concrete(base=C(178, 174, 166), rough=0.55, tone=0.07, pores=False)
    flat = mats.paint(C(196, 194, 188), rough=0.5)
    oak = mats.wood("light_oak", along='X', contrast=0.4)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.shelf(ctx, -0.9, 0.9, 1.6, depth=0.22, mat=oak, t=0.035)
        props.vase("v", -0.5, yw - 0.12, 1.6, h=0.24, r=0.06, neck=0.02, mat=mats.ceramic(C(60, 58, 54), matte=True), style=0)
        props.bowl("b", 0.1, yw - 0.12, 1.6, r=0.1, h=0.06, mat=mats.ceramic(C(230, 226, 218), matte=True))
        props.board("bd", kit.right(ctx, 0.3), sy + 0.03, H, w=0.36, d=0.36, t=0.03, wood="light_oak", round_=True)
        props.bottle("carafe", kit.right(ctx, 0.62), yw - 0.15, H, h=0.25, r=0.045, glass=mats.glass())
        props.tumbler("tb", kit.right(ctx, 0.75), yw - 0.2, H)

    def light(ctx):
        kit.natural(ctx, side=-1, power=260, sun=False, room=0.38)

    return _r("WL 12", "pressed", run=(-1.8, 1.8), counter=micro, edge="square", cab=dict(cab_mat=flat, door="groove", handle="edge", handle_mat=flat),
              floor=micro, wall=micro, splash=None,
              tap=dict(kind="square", finish="steel", gap=0.05, height=0.3, reach=0.21, dx=-0.23),
              build=[build], light=light,
              camera=dict(dist=2.35, elev=33, azim=12, lens=50, fstop=3.2, tz=0.04, tx=0.2, ty=0.1), exposure=-1.15, look="AgX - Base Contrast")


# WL 18 — a long galley under a wide window, white tiles, light oak
def wl18():
    quartz = mats.quartz(base=C(240, 238, 234), speck=C(196, 192, 186), dens=0.025, rough=0.18)
    oak = mats.wood("light_oak", along='X', rough=0.5, contrast=0.45)
    tile = mats.tile(col=C(246, 245, 241), grout=C(214, 212, 206), w=0.2, h=0.1, gap=0.002, rough=0.04, var=0.02)
    wall = mats.plaster(C(240, 238, 232), var=0.02)
    chrome = mats.metal("chrome")
    win = dict(x0=-1.05, x1=1.05, z0=0.91 + 0.32, z1=2.3, frame=mats.paint(C(245, 245, 242), 0.4), mullions=2, transoms=0)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.garden(ctx, y0=yw + 0.3, seed=14, col=(0.12, 0.19, 0.07), n=10, ground=False)
        kit.outside_glow(ctx, 2.2)
        for i, x in enumerate((-0.75, -0.25, 0.3)):
            props.herb_pot(f"sill{i}", x, yw + 0.045, win["z0"], r=0.041, h=0.075, seed=40 + i, pot_mat=mats.ceramic(C(236, 234, 228), matte=True))
        props.bottle("jug", kit.left(ctx, 0.25), sy + 0.06, H, h=0.24, r=0.05, glass=mats.glass())
        props.branch("jug_br", kit.left(ctx, 0.25), sy + 0.06, H + 0.22, height=0.35, leaf_col=(0.16, 0.26, 0.1), n_leaves=90, seed=45)
        kit.board_with(ctx, kit.right(ctx, 0.3), sy + 0.0, rot=0.1, wood="oak", fruit="lemon", n=2)

    def light(ctx):
        kit.natural(ctx, side=-1, power=110, sun=True, sun_elev=26, sun_azim=192, sun_power=6.0, room=0.3, back_window=win)

    return _r("WL 18", "pressed", layout="window", run=(-2.0, 2.0), depth=0.66, counter=quartz, cab=dict(cab_mat=oak, door="slab", handle="bar", handle_mat=chrome),
              floor=mats.wood("light_oak", along='X'), wall=wall, window=win, splash=dict(mat=tile, h=0.32),
              tap=dict(kind="pulldown", finish="chrome", gap=0.05, height=0.4, reach=0.22, dx=-0.18),
              build=[build], light=light,
              camera=dict(dist=2.6, elev=31, azim=-11, lens=42, fstop=3.2, tz=0.05, ty=0.2), exposure=-1.2, look="AgX - Base Contrast")


# ════════════════════════════ HAND MADE ════════════════════════════

# W 5050 TSB — a dark bar: walnut, honed white marble, glassware, evening
def w5050tsb():
    arab = mats.marble(base=C(232, 230, 226), vein=C(90, 90, 92), vein2=C(170, 168, 166), rough=0.3, vein_width=0.016, seed=11.0, honed=True, scale=0.55,
                       density=0.62, warp=6.0, halo=0.14)
    walnut = mats.wood("walnut", along='Z', rough=0.45, contrast=0.55, coat=0.15)
    wall = mats.plaster(C(126, 108, 92), var=0.05, rough=0.9, scale=0.4, bump=0.06)
    smoke = mats.glass((0.55, 0.5, 0.45), 0.02)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        for z in (1.42, 1.78):
            kit.shelf(ctx, -1.0, 1.0, z, depth=0.24, mat=smoke, t=0.01, led=(5, 2600))
        for i, x in enumerate((-0.7, -0.55, -0.4, 0.4, 0.55)):
            props.wine_glass(f"wgs{i}", x, ctx["wall_y"] - 0.12, 1.42)
        kit.shelf_items(ctx, -1.0, 1.0, 1.78, seed=101, kinds=("bottle", "bottle", "gap", "bottle", "jar", "bottle"))
        props.wine_glass("wg1", kit.right(ctx, 0.15), sy - 0.08, H)
        props.wine_glass("wg2", kit.right(ctx, 0.27), sy + 0.02, H)
        props.bottle("wine", kit.right(ctx, 0.42), sy + 0.1, H, h=0.31, r=0.037, glass=mats.glass((0.15, 0.22, 0.12)), cap=mats.paint(C(110, 30, 30), 0.5, texture=0))
        props.board("bd", kit.left(ctx, 0.28), sy + 0.02, H, w=0.32, d=0.22, t=0.025, rot=-0.15, wood="walnut")
        for i, (dx, dy) in enumerate([(0.0, 0.03), (0.07, -0.03)]):
            props.lemon(f"lm{i}", kit.left(ctx, 0.28) + dx, sy + 0.02 + dy, H + 0.025, kind="lime" if i else "lemon", s=0.9, rot=i)

    def light(ctx):
        kit.golden(ctx, side=-1, sun_elev=14, sun_azim=280, sun_power=5.0, sun_k=3500, room=0.4, fill=100)

    return _r("W 5050 TSB", "handmade", run=(-1.2, 1.2), depth=0.64, counter=arab, cab=dict(cab_mat=walnut, door="slab", handle="none"),
              floor=mats.wood("walnut", along='X'), wall=wall, splash=dict(mat=arab, h=0.4),
              tap=dict(kind="gooseneck", finish="black", gap=0.035, height=0.3, reach=0.18, dx=-0.14),
              build=[build], light=light, front_margin=0.06,
              camera=dict(dist=1.8, elev=36, azim=18, lens=55, fstop=2.8, tz=0.03, ty=0.12), exposure=-1.1,
              # evening light: a gentle fill, so the black bowl reads and the warmth stays
              sink_fill=18)


# W 6045 TSS — light oak minimal, white quartz, bright
def w6045tss():
    quartz = mats.quartz(base=C(244, 242, 238), speck=C(210, 206, 200), dens=0.02, rough=0.2)
    oak = mats.wood("white_oak", along='Z', rough=0.5, contrast=0.4)
    wall = mats.plaster(C(244, 242, 238), var=0.02)
    steel = mats.metal("steel")
    cer = mats.ceramic(C(246, 244, 240))

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.uppers(ctx, -1.6, -0.45, 1.55, 2.3, dict(cab_mat=oak, door="groove", handle="none"))
        kit.shelf(ctx, 0.5, 1.6, 1.6, depth=0.22, mat=mats.wood("white_oak", along='X', contrast=0.4), t=0.03)
        kit.shelf_items(ctx, 0.5, 1.6, 1.6, seed=111, kinds=("plates", "bowl", "cups"), palette=[cer])
        kit.branches(ctx, kit.right(ctx, 0.3), sy + 0.1, mats.glass((0.92, 0.95, 0.93)), h=0.26, r=0.055, leaf=(0.2, 0.26, 0.14), seed=47, height=0.45, style=1, n_leaves=60)
        props.plate_stack("pl", kit.left(ctx, 0.25), sy + 0.03, H, r=0.11, n=3, mat=cer)
        props.towel("tw", kit.left(ctx, 0.3), sy - 0.15, H, w=0.26, d=0.14, t=0.009, color=C(225, 220, 210), rot=0.05)

    def light(ctx):
        kit.natural(ctx, side=1, power=170, sun=True, sun_elev=30, sun_azim=70, sun_power=5.0, room=0.32)

    return _r("W 6045 TSS", "handmade", counter=quartz, edge="square", cab=dict(cab_mat=oak, door="groove", handle="none"),
              floor=mats.wood("white_oak", along='X'), wall=wall, splash=dict(mat=quartz, h=0.64),
              tap=dict(kind="gooseneck", finish="steel", gap=0.035, height=0.34, reach=0.2, dx=0.0),
              build=[build], light=light, front_margin=0.06, depth=0.62,
              camera=dict(dist=2.15, elev=34, azim=-16, lens=50, fstop=3.2, tz=0.05, ty=0.18), exposure=-1.25, look="AgX - Medium High Contrast")


# W 6045 TSB — ochre lacquer, pale concrete, black accents, warm sun
def w6045tsb():
    conc = mats.concrete(base=C(200, 196, 188), rough=0.55, tone=0.06)
    ochre = mats.paint(C(178, 112, 52), rough=0.45, coat=0.1)
    wall = mats.plaster(C(236, 228, 214), var=0.04)
    blk = mats.metal("black")

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.shelf(ctx, -1.5, 0.2, 1.6, depth=0.22, mat=blk, t=0.012)
        kit.shelf_items(ctx, -1.5, 0.2, 1.6, seed=121, kinds=("vase", "bowl", "jar", "vase2"), palette=[mats.ceramic(C(30, 30, 30), rough=0.4), mats.ceramic(C(236, 230, 220), matte=True)])
        kit.fruit_bowl(ctx, kit.left(ctx, 0.28), sy + 0.03, mats.ceramic(C(30, 30, 30), rough=0.4), r=0.13, fruit=("orange", "orange", "orange"))
        props.jar("kettle", kit.right(ctx, 0.38), yw - 0.16, H, r=0.08, h=0.18, mat=mats.metal("black"), lid=mats.metal("black"))
        props.board("bd", kit.right(ctx, 0.25), sy - 0.04, H, w=0.38, d=0.24, t=0.025, rot=0.1, wood="oak")

    def light(ctx):
        kit.natural(ctx, side=-1, power=150, sun=True, sun_elev=26, sun_azim=290, sun_power=6.0, sun_k=4800, room=0.3)

    return _r("W 6045 TSB", "handmade", counter=conc, edge="square", cab=dict(cab_mat=ochre, door="slab", handle="bar", handle_mat=blk),
              floor=mats.concrete(base=C(170, 164, 156)), wall=wall, splash=dict(mat=conc, h=0.5),
              tap=dict(kind="square", finish="black", gap=0.035, height=0.3, reach=0.2),
              build=[build], light=light, front_margin=0.06, depth=0.62,
              camera=dict(dist=1.95, elev=35, azim=16, lens=50, fstop=3.2, tz=0.03, ty=0.12), exposure=-1.2)


# W 7546 TSB — smoked oak and pale limestone, a soft dark room
def w7546tsb():
    lime = mats.marble(base=C(200, 194, 184), vein=C(160, 154, 146), vein2=C(182, 176, 168), rough=0.38, vein_width=0.02, seed=13.0, honed=True)
    oak = mats.wood("smoked_oak", along='Z', rough=0.5)
    wall = mats.plaster(C(200, 192, 180), var=0.04, rough=0.9, scale=0.4, bump=0.06)
    cer = mats.ceramic(C(214, 206, 194), matte=True, speck=0.05)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.shelf(ctx, -1.5, 1.5, 1.6, depth=0.26, mat=oak, t=0.05, led=(6, 2700))
        kit.shelf_items(ctx, -1.5, 1.5, 1.6, seed=131, kinds=("vase", "bowl", "plates", "jar", "vase2", "books"), palette=[cer, mats.ceramic(C(40, 38, 36), rough=0.4)])
        kit.board_with(ctx, kit.left(ctx, 0.3), sy + 0.0, rot=0.14, wood="walnut", fruit="lemon", n=2)
        kit.oil_and_salt(ctx, kit.right(ctx, 0.25), yw - 0.14)
        kit.branches(ctx, kit.right(ctx, 0.6), sy + 0.1, mats.ceramic(C(40, 38, 36), rough=0.4), h=0.32, r=0.08, leaf=(0.13, 0.16, 0.1), seed=49)

    def light(ctx):
        kit.natural(ctx, side=-1, power=170, sun=True, sun_elev=28, sun_azim=288, sun_power=5.5, room=0.3)

    return _r("W 7546 TSB", "handmade", counter=lime, cab=dict(cab_mat=oak, door="fluted", handle="none"),
              floor=mats.wood("smoked_oak", along='X'), wall=wall, splash=dict(mat=lime, h=0.55),
              tap=None, build=[build], light=light, front_margin=0.06, depth=0.66,
              camera=dict(dist=2.05, elev=34, azim=-16, lens=50, fstop=3.2, tz=0.06, ty=0.18), exposure=-1.2)


# W 7546 TSBN — dark luxury: warm grey porcelain, gloss charcoal, light lines
def w7546tsbn():
    # light veins only in the fine, crisp layer (vein2): the broad layer blurs where it widens, so it carries soft
    # darker clouding instead. The veins run lengthwise on the worktop and the splashback alike.
    porc = mats.marble(base=C(150, 146, 140), vein=C(138, 134, 128), vein2=C(196, 193, 188), rough=0.2, vein_width=0.012, seed=23.0, scale=0.5,
                       stretch=(1.0, 2.2, 2.4))
    gloss = mats.paint(C(34, 34, 36), rough=0.12, coat=0.6, texture=0)
    wall = mats.plaster(C(170, 166, 160), var=0.03, rough=0.85)
    chrome = mats.metal("chrome")

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.uppers(ctx, -1.7, 1.7, 1.6, 2.35, dict(cab_mat=gloss, door="groove", handle="none"), led=(8, 3500))
        props.wine_glass("wg", kit.right(ctx, 0.22), sy - 0.06, H)
        props.bottle("bt", kit.right(ctx, 0.4), yw - 0.15, H, h=0.3, r=0.036, glass=mats.glass((0.3, 0.3, 0.32)), cap=chrome)
        props.bowl("bw", kit.left(ctx, 0.3), sy + 0.03, H, r=0.12, h=0.06, mat=mats.ceramic(C(236, 234, 230), rough=0.15))
        for i, (dx, dy) in enumerate([(-0.03, 0.0), (0.04, 0.02)]):
            props.lemon(f"ap{i}", kit.left(ctx, 0.3) + dx, sy + 0.03 + dy, H + 0.02, kind="apple", s=-0.85)

    def light(ctx):
        kit.natural(ctx, side=1, power=170, sun=True, sun_elev=27, sun_azim=72, sun_power=5.0, room=0.32)

    return _r("W 7546 TSBN", "handmade", counter=porc, edge="square", cab=dict(cab_mat=gloss, door="groove", handle="none"),
              floor=mats.concrete(base=C(50, 50, 50)), wall=wall, splash=dict(mat=porc, h=0.69),
              tap=None, build=[build], light=light, front_margin=0.06, depth=0.66,
              camera=dict(dist=2.05, elev=33, azim=15, lens=50, fstop=3.2, tz=0.07, ty=0.16), exposure=-1.2)


# W 7646 USS — a chef's kitchen: honed black granite, white subway tile, steel shelves
def w7646uss():
    absb = mats.quartz(base=C(28, 28, 29), speck=C(70, 70, 70), dens=0.04, rough=0.35)
    white = mats.paint(C(236, 234, 228), rough=0.45)
    sub = mats.tile(col=C(246, 245, 241), grout=C(150, 148, 144), w=0.15, h=0.075, gap=0.0025, rough=0.04, var=0.02)
    steel = mats.metal("steel")

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        for z in (1.55, 1.95):
            kit.shelf(ctx, -1.6, 1.6, z, depth=0.3, mat=steel, t=0.012)
        kit.shelf_items(ctx, -1.6, 1.6, 1.55, seed=141, kinds=("plates", "bowl", "jar", "jar", "bottle", "bowl", "plates"), palette=[mats.ceramic(C(244, 242, 238))])
        kit.shelf_items(ctx, -1.6, 1.6, 1.95, seed=142, kinds=("jar", "jar", "plant", "jar", "books", "jar"))
        props.board("bd", kit.left(ctx, 0.3), sy + 0.0, H, w=0.5, d=0.34, t=0.04, rot=0.0, wood="oak", handle=False)
        props.herb_pot("hp", kit.right(ctx, 0.25), sy + 0.04, H, r=0.075, h=0.11, pot_mat=mats.ceramic(C(236, 234, 228), matte=True), seed=51)
        props.jar("ut", kit.right(ctx, 0.6), yw - 0.14, H, r=0.06, h=0.17, mat=mats.metal("steel"))

    def light(ctx):
        kit.natural(ctx, side=-1, power=200, sun=True, sun_elev=34, sun_azim=295, sun_power=4.5, room=0.32)

    return _r("W 7646 USS", "handmade", counter=absb, edge="square", cab=dict(cab_mat=white, door="slab", handle="bar", handle_mat=steel),
              floor=mats.tile(col=C(60, 60, 60), grout=C(40, 40, 40), w=0.3, h=0.3, gap=0.004, rough=0.4, along='XY', offset=0.0), wall=sub, splash=None,
              tap=dict(kind="pulldown", finish="steel", gap=0.06, height=0.44, reach=0.23),
              build=[build], light=light, depth=0.66,
              camera=dict(dist=2.05, elev=34, azim=-13, lens=50, fstop=3.2, tz=0.03, ty=0.14), exposure=-1.2, look="AgX - Base Contrast")


# W 7646 USB — fluted light oak, white quartz, bronze
def w7646usb():
    quartz = mats.marble(base=C(240, 238, 234), vein=C(190, 186, 180), vein2=C(218, 214, 208), rough=0.15, vein_width=0.008, seed=19.0, scale=0.45,
                         density=0.6, warp=6.0, halo=0.1)
    oak = mats.wood("light_oak", along='Z', rough=0.5, contrast=0.45)
    wall = mats.plaster(C(226, 220, 210), var=0.03)
    bronze = mats.metal("bronze")
    cer = mats.ceramic(C(214, 204, 188), matte=True, speck=0.05)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.shelf(ctx, -1.6, 1.0, 1.6, depth=0.24, mat=mats.wood("light_oak", along='X', contrast=0.45), t=0.04)
        kit.shelf_items(ctx, -1.6, 1.0, 1.6, seed=151, kinds=("vase", "plates", "bowl", "jar", "vase2"), palette=[cer, mats.ceramic(C(150, 120, 90), matte=True)])
        kit.board_with(ctx, kit.right(ctx, 0.3), sy + 0.0, rot=-0.12, wood="oak", fruit="pear", n=2)
        kit.branches(ctx, kit.left(ctx, 0.35), sy + 0.12, cer, h=0.28, r=0.07, leaf=(0.15, 0.2, 0.1), seed=53)

    def light(ctx):
        kit.natural(ctx, side=-1, power=160, sun=True, sun_elev=30, sun_azim=290, sun_power=5.5, room=0.3)

    return _r("W 7646 USB", "handmade", counter=quartz, edge="eased", cab=dict(cab_mat=oak, door="fluted", handle="none"),
              floor=mats.wood("light_oak", along='X'), wall=wall, splash=dict(mat=quartz, h=0.64),
              tap=dict(kind="gooseneck", finish="bronze", gap=0.06, height=0.35, reach=0.21),
              build=[build], light=light, depth=0.66,
              camera=dict(dist=2.0, elev=34, azim=16, lens=50, fstop=3.2, tz=0.03, ty=0.14), exposure=-1.2, look="AgX - Base Contrast")


# W 7845 UDS — greige plaster, honed grey marble, linen, soft light
def w7845uds():
    # light veins only in the fine, crisp layer (vein2), as in the W 7546 TSBN kitchen
    # Pietra Grey: a dark grey limestone with sparse white calcite veins running through it, the finer veins only a
    # shade off the ground (light ones on a fine network read as cracked glaze)
    pietra = mats.marble(base=C(120, 116, 110), vein=C(196, 192, 186), vein2=C(134, 130, 124), rough=0.36, vein_width=0.009, seed=23.0, honed=True, scale=0.6,
                         stretch=(1.0, 2.2, 2.4), density=0.55, halo=0.0, crisp=True)
    greige = mats.paint(C(190, 180, 166), rough=0.6)
    wall = mats.plaster(C(200, 190, 176), var=0.05, rough=0.92, scale=0.45, bump=0.1)
    nickel = mats.metal("nickel")
    cer = mats.ceramic(C(236, 230, 220), matte=True)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        geo.box(-1.7, yw - 0.02, H + 0.0, 1.7, yw, H + 0.10, name="upstand", mat=pietra)
        kit.back_face(ctx, yw - 0.02, H, H + 0.10, -1.7, 1.7)
        kit.shelf(ctx, -1.2, 0.3, 1.62, depth=0.2, mat=mats.wood("white_oak", along='X', contrast=0.4), t=0.03)
        kit.shelf_items(ctx, -1.2, 0.3, 1.62, seed=161, kinds=("bowl", "vase", "jar"), palette=[cer])
        props.towel("tw", kit.right(ctx, 0.25), sy - 0.02, H, w=0.3, d=0.18, t=0.012, color=C(206, 196, 180), rot=-0.06)
        props.plate_stack("pl", kit.right(ctx, 0.25), sy + 0.0, H + 0.012, r=0.1, n=2, mat=cer)
        kit.branches(ctx, kit.left(ctx, 0.3), sy + 0.1, cer, h=0.3, r=0.075, leaf=(0.17, 0.2, 0.13), seed=55, style=2)

    def light(ctx):
        kit.natural(ctx, side=1, power=220, sun=False, room=0.38)

    return _r("W 7845 UDS", "handmade", counter=pietra, cab=dict(cab_mat=greige, door="shaker", handle="knob", handle_mat=nickel),
              floor=mats.wood("white_oak", along='X'), wall=wall, splash=None,
              tap=dict(kind="bridge", finish="nickel", gap=0.07, height=0.3, reach=0.22),
              build=[build], light=light, depth=0.66,
              camera=dict(dist=2.05, elev=34, azim=-14, lens=50, fstop=3.2, tz=0.03, ty=0.14), exposure=-1.15, look="AgX - Base Contrast")


# W 7845 UDB — oxblood lacquer, Calacatta marble, polished brass, an island
def w7845udb():
    cal = mats.marble(base=C(240, 238, 234), vein=C(150, 130, 110), vein2=C(205, 196, 186), rough=0.12, vein_width=0.014, seed=29.0, scale=0.42,
                      density=0.6, warp=6.0, halo=0.14)
    ox = mats.paint(C(98, 34, 30), rough=0.35, coat=0.2)
    wall = mats.plaster(C(178, 154, 136), var=0.04, rough=0.9, scale=0.4, bump=0.06)
    brass = mats.metal("brass_polished")
    cer = mats.ceramic(C(240, 238, 232))

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        cab = dict(cab_mat=ox, door="shaker", handle="bar", handle_mat=brass)
        kitchen.worktop(-2.6, 2.6, yw - 0.62, yw, H, 0.03, cal, [], None)
        kitchen.base_run(-2.6, 2.6, yw - 0.6, H - 0.03, cab, None, depth=0.58)
        geo.box(-2.6, yw - 0.012, H, 2.6, yw, H + 0.65, name="slab_b", mat=cal)
        # a walnut shelf, not brass: the black divider's brushed top mirrors whatever is above it
        kit.shelf(ctx, -1.8, 1.2, 1.7, depth=0.22, mat=mats.wood("walnut", along='X'), t=0.03, led=(5, 3500))
        kit.shelf_items(ctx, -1.8, 1.2, 1.7, seed=171, kinds=("vase", "plates", "bowl", "jar", "vase2", "cups"), palette=[cer, mats.ceramic(C(98, 34, 30), rough=0.3)])
        kit.fruit_bowl(ctx, kit.right(ctx, 0.32), sy + 0.03, cer, r=0.13, fruit=("pear", "pear", "apple"))
        kit.branches(ctx, kit.left(ctx, 0.4), sy + 0.12, mats.glass((0.92, 0.95, 0.93)), h=0.3, r=0.07, leaf=(0.15, 0.2, 0.12), seed=57, style=1)

    def light(ctx):
        kit.golden(ctx, side=-1, sun_elev=14, sun_azim=278, sun_power=5.0, sun_k=3600, room=0.42, fill=100)

    return _r("W 7845 UDB", "handmade", layout="island", island_depth=1.0, run=(-1.35, 1.35), back_y=1.95, counter=cal,
              cab=dict(cab_mat=ox, door="shaker", handle="bar", handle_mat=brass),
              floor=mats.wood("walnut", along='X'), wall=wall,
              tap=dict(kind="gooseneck", finish="brass_polished", gap=0.07, height=0.37, reach=0.22),
              build=[build], light=light,
              camera=dict(dist=2.4, elev=29, azim=-18, lens=50, fstop=2.8, tz=0.05, ty=0.42), exposure=-1.1,
              # evening light: a gentle fill, so the black bowl reads and the warmth stays
              sink_fill=18)


# W 8050 TSS — white under a skylight: lacquer, quartz, pale oak
def w8050tss():
    quartz = mats.quartz(base=C(244, 243, 240), speck=C(220, 218, 214), dens=0.02, rough=0.12)
    white = mats.paint(C(242, 241, 238), rough=0.25, coat=0.3, texture=0)
    wall = mats.plaster(C(244, 243, 240), var=0.015)
    steel = mats.metal("steel")

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.uppers(ctx, -1.8, -0.55, 1.5, 2.4, dict(cab_mat=white, door="groove", handle="none"))
        kit.uppers(ctx, 0.55, 1.8, 1.5, 2.4, dict(cab_mat=white, door="groove", handle="none"))
        props.herb_pot("hp", kit.left(ctx, 0.28), sy + 0.08, H, r=0.07, h=0.12, pot_mat=mats.ceramic(C(236, 234, 228), matte=True), seed=67, leaf_col=(0.06, 0.15, 0.04))
        props.bowl("lb", kit.left(ctx, 0.3), sy - 0.14, H, r=0.1, h=0.06, mat=mats.ceramic(C(200, 190, 175), matte=True, speck=0.05))
        for i, (dx, dy) in enumerate([(-0.034, -0.01), (0.036, 0.014)]):
            props.lemon(f"lm{i}", kit.left(ctx, 0.3) + dx, sy - 0.14 + dy, H + 0.012, kind="lemon", s=0.85, rot=i)
        kit.branches(ctx, kit.right(ctx, 0.35), sy + 0.12, mats.ceramic(C(246, 245, 242)), h=0.3, r=0.07, leaf=(0.15, 0.24, 0.1), seed=59, style=1)
        props.board("bd", kit.right(ctx, 0.25), sy - 0.08, H, w=0.36, d=0.24, t=0.02, wood="white_oak", rot=0.05)

    def light(ctx):
        kit.natural(ctx, side=1, power=200, sun=True, sun_elev=42, sun_azim=60, sun_power=4.5, room=0.35)

    return _r("W 8050 TSS", "handmade", counter=quartz, edge="square", cab=dict(cab_mat=white, door="groove", handle="none"),
              floor=mats.wood("white_oak", along='X'), wall=mats.plaster(C(232, 228, 220), var=0.03), splash=dict(mat=quartz, h=0.59),
              tap=dict(kind="pulldown", finish="steel", gap=0.035, height=0.42, reach=0.22, dx=-0.1),
              build=[build], light=light, front_margin=0.06, depth=0.64,
              camera=dict(dist=2.15, elev=35, azim=13, lens=50, fstop=3.2, tz=0.05, ty=0.15), exposure=-1.3, look="AgX - Medium High Contrast")


# W 8050 TSB — walnut and honed limestone, warm evening
def w8050tsb():
    # honed limestone: its veins flowing up the splashback and breaking off, not closing into cells
    lime = mats.marble(base=C(214, 206, 192), vein=C(176, 166, 150), vein2=C(196, 188, 174), rough=0.4, vein_width=0.018, seed=31.0, honed=True,
                       stretch=(1.0, 2.2, 2.4), density=0.7, breakup=0.8)
    walnut = mats.wood("walnut", along='X', rough=0.45, contrast=0.55)
    wall = mats.plaster(C(150, 136, 120), var=0.04, rough=0.9, scale=0.4, bump=0.08)
    blk = mats.metal("black")
    cer = mats.ceramic(C(226, 218, 204), matte=True, speck=0.05)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.shelf(ctx, -1.6, 1.6, 1.62, depth=0.24, mat=mats.wood("walnut", along='X', contrast=0.5), t=0.045, led=(5, 2700))
        kit.shelf_items(ctx, -1.6, 1.6, 1.62, seed=181, kinds=("jar", "vase", "bowl", "plates", "books", "vase2", "jar"), palette=[cer, mats.ceramic(C(50, 46, 42), rough=0.4)])
        kit.board_with(ctx, kit.left(ctx, 0.3), sy - 0.02, rot=0.1, wood="walnut", fruit="orange", n=2)
        kit.oil_and_salt(ctx, kit.right(ctx, 0.28), yw - 0.14)
        props.herb_pot("hp", kit.right(ctx, 0.6), sy + 0.05, H, r=0.07, h=0.12, pot_mat=cer, seed=61)

    def light(ctx):
        kit.natural(ctx, side=-1, power=150, sun=True, sun_elev=24, sun_azim=285, sun_power=5.5, sun_k=4400, room=0.32)

    return _r("W 8050 TSB", "handmade", counter=lime, cab=dict(cab_mat=walnut, door="slab", handle="edge", handle_mat=blk),
              floor=mats.wood("walnut", along='X'), wall=wall, splash=dict(mat=lime, h=0.6),
              tap=dict(kind="gooseneck", finish="black", gap=0.035, height=0.34, reach=0.2, dx=-0.1),
              build=[build], light=light, front_margin=0.06, depth=0.64,
              camera=dict(dist=2.05, elev=34, azim=-15, lens=50, fstop=3.2, tz=0.04, ty=0.14), exposure=-1.2)


# W 8245 TDB — coastal: pale grey-blue shaker, white marble, rattan, morning
def w8245tdb():
    cal = mats.marble(base=C(238, 236, 232), vein=C(150, 150, 152), vein2=C(210, 208, 206), rough=0.14, vein_width=0.01, seed=37.0, scale=0.42,
                      density=0.6, warp=6.0, halo=0.12)
    blue = mats.paint(C(176, 190, 196), rough=0.5)
    wall = mats.plaster(C(240, 238, 232), var=0.02)
    nickel = mats.metal("nickel")

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.uppers(ctx, -1.8, -0.6, 1.55, 2.3, dict(cab_mat=blue, door="shaker", handle="knob", handle_mat=nickel))
        kit.shelf(ctx, 0.6, 1.8, 1.62, depth=0.22, mat=mats.wood("white_oak", along='X'), t=0.035)
        kit.shelf_items(ctx, 0.6, 1.8, 1.62, seed=191, kinds=("plates", "jar", "bowl"), palette=[mats.ceramic(C(244, 242, 238)), mats.ceramic(C(120, 150, 170))])
        props.board("bd", kit.right(ctx, 0.3), sy + 0.02, H, w=0.42, d=0.28, t=0.03, rot=0.1, wood="white_oak")
        props.bottle("lemonade", kit.right(ctx, 0.3), sy + 0.03, H + 0.03, h=0.24, r=0.05, glass=mats.glass(), liquid=mats.fruit(C(240, 220, 120), 0.1, 0.0, 10))
        props.tumbler("tb", kit.right(ctx, 0.15), sy - 0.06, H + 0.03)
        kit.branches(ctx, kit.left(ctx, 0.35), sy + 0.12, mats.ceramic(C(244, 242, 238)), h=0.3, r=0.07, leaf=(0.18, 0.24, 0.16), seed=63)

    def light(ctx):
        kit.natural(ctx, side=1, power=170, sun=True, sun_elev=28, sun_azim=70, sun_power=5.5, room=0.32)

    return _r("W 8245 TDB", "handmade", counter=cal, cab=dict(cab_mat=blue, door="shaker", handle="knob", handle_mat=nickel),
              floor=mats.wood("white_oak", along='X'), wall=wall, splash=dict(mat=cal, h=0.64),
              tap=dict(kind="bridge", finish="nickel", gap=0.04, height=0.3, reach=0.22, dx=-0.17),
              build=[build], light=light, front_margin=0.06, depth=0.62,
              camera=dict(dist=2.05, elev=34, azim=-14, lens=50, fstop=3.2, tz=0.03, ty=0.12), exposure=-1.2, look="AgX - Base Contrast")


# W 8550 TDG — a sleek island, the glass covers closed: grey porcelain, white, a dark room
def w8550tdg():
    porc = mats.marble(base=C(206, 204, 200), vein=C(140, 138, 136), vein2=C(186, 184, 180), rough=0.2, vein_width=0.01, seed=41.0, scale=0.5)
    white = mats.paint(C(232, 230, 226), rough=0.4)
    dark = mats.paint(C(42, 42, 44), rough=0.5)
    wall = mats.plaster(C(190, 188, 184), var=0.03)
    gun = mats.metal("gunmetal")

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        cab = dict(cab_mat=dark, door="groove", handle="none")
        kitchen.worktop(-2.6, 2.6, yw - 0.62, yw, H, 0.03, porc, [], None)
        kitchen.base_run(-2.6, 2.6, yw - 0.6, H - 0.03, cab, None, depth=0.58)
        geo.box(-2.6, yw - 0.35, 1.5, 2.6, yw, 2.4, name="uppers_b", mat=dark)
        kitchen.led_strip(-2.5, 2.5, 1.499, yw - 0.3, None, color=kelvin(4000), strength=6)
        kit.shelf_items(ctx, -2.2, 2.2, H, seed=201, kinds=("gap", "jar", "bottle", "gap", "gap", "vase", "gap", "bowl", "gap"), y=yw - 0.2)
        props.bowl("bw", kit.right(ctx, 0.35), sy + 0.03, H, r=0.14, h=0.06, mat=mats.ceramic(C(30, 30, 30), rough=0.3))
        kit.branches(ctx, kit.left(ctx, 0.4), sy + 0.15, mats.ceramic(C(232, 230, 226)), h=0.32, r=0.08, leaf=(0.15, 0.2, 0.12), seed=65)

    def light(ctx):
        kit.natural(ctx, side=-1, power=180, sun=True, sun_elev=26, sun_azim=290, sun_power=5.0, room=0.33)

    return _r("W 8550 TDG", "handmade", layout="island", island_depth=1.0, run=(-1.35, 1.35), back_y=1.95, counter=porc, edge="square",
              cab=dict(cab_mat=white, door="groove", handle="none"),
              floor=mats.concrete(base=C(120, 118, 114)), wall=wall,
              tap=dict(kind="square", finish="gunmetal", gap=0.06, height=0.3, reach=0.22, dx=0.2),
              build=[build], light=light,
              camera=dict(dist=2.35, elev=30, azim=17, lens=50, fstop=3.2, tz=0.05, ty=0.4), exposure=-1.2)


# W 10050 TSG — the glass wing: warm light quartz, charcoal fronts, smoked oak
def w10050tsg():
    quartz = mats.quartz(base=C(214, 208, 198), speck=C(170, 164, 156), dens=0.04, rough=0.2)
    char = mats.paint(C(56, 56, 56), rough=0.5)
    oak = mats.wood("smoked_oak", along='X', contrast=0.5)
    wall = mats.plaster(C(206, 200, 190), var=0.03)

    def build(ctx):
        H, sx, sy, yw = ctx["H"], ctx["sx"], ctx["sy"], ctx["wall_y"]
        kit.shelf(ctx, -1.8, 1.8, 1.62, depth=0.26, mat=oak, t=0.05, led=(5, 3000))
        kit.shelf_items(ctx, -1.8, 1.8, 1.62, seed=211, kinds=("plates", "jar", "vase", "bowl", "books", "jar", "plant", "vase2"),
                        palette=[mats.ceramic(C(236, 232, 224), matte=True), mats.ceramic(C(40, 40, 40), rough=0.4)])
        kit.board_with(ctx, kit.left(ctx, 0.3), sy + 0.0, rot=0.12, wood="smoked_oak", fruit="lime", n=3)
        props.cup("cp", kit.right(ctx, 0.25), sy - 0.06, H, r=0.04, h=0.09, mat=mats.ceramic(C(236, 232, 224), matte=True))

    def light(ctx):
        kit.natural(ctx, side=-1, power=160, sun=True, sun_elev=30, sun_azim=290, sun_power=5.5, room=0.3)

    return _r("W 10050 TSG", "handmade", run=(-1.9, 1.9), counter=quartz, edge="square", cab=dict(cab_mat=char, door="groove", handle="edge", handle_mat=oak),
              floor=mats.wood("smoked_oak", along='X'), wall=wall, splash=dict(mat=quartz, h=0.62),
              tap=dict(kind="gooseneck", where="taphole", hole=(0.109, 0.193), finish="steel", height=0.34, reach=0.21),
              build=[build], light=light, front_margin=0.06, depth=0.64,
              camera=dict(dist=2.25, elev=34, azim=-13, lens=48, fstop=3.2, tz=0.03, ty=0.14), exposure=-1.2, look="AgX - Base Contrast")


RECIPES = {
    "lps5040": lps5040, "lps7540a": lps7540a, "lps8643a": lps8643a, "lps9643a": lps9643a, "lps10050a": lps10050a,
    "wl03": wl03, "wl05a": wl05a, "wl07": wl07, "wl11": wl11, "wl12": wl12, "wl18": wl18,
    "w5050tsb": w5050tsb, "w6045tss": w6045tss, "w6045tsb": w6045tsb, "w7546tsb": w7546tsb, "w7546tsbn": w7546tsbn,
    "w7646uss": w7646uss, "w7646usb": w7646usb, "w7845uds": w7845uds, "w7845udb": w7845udb, "w8050tss": w8050tss,
    "w8050tsb": w8050tsb, "w8245tdb": w8245tdb, "w8550tdg": w8550tdg, "w10050tsg": w10050tsg,
}

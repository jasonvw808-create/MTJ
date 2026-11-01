"""The kitchens as the catalogue now shows them: each sink, its tap and the camera exactly as before; round them a warm
ivory limestone (or a soft light quartz) worktop, matt painted cabinets, a restrained stone or plaster splashback, a
stone floor, plaster walls, nothing made of wood, almost nothing on the worktop, and soft daylight.

It works on the recipes as they are (scenes_granite.py, scenes_steel.py). begin() runs before a recipe is built and
stands in for what the brief leaves out: fluted, slatted and beadboard fronts become plain painted ones, wooden boards
and the small things of a lived-in kitchen are not placed (one styling piece stays on the worktop, two or three on a
shelf, herbs on a window sill), shelves lose their lights, and every light set-up becomes soft daylight from the same
side. restyle() then gives the recipe its new worktop, cabinets, splashback, floor and walls, and after the kitchen is
built swaps every surface that still shows the old palette or wood for the new one. The splashback and every other
piece keep their size, so the tap stands where it stood.

Every kitchen has its own cabinet colour (KITCHENS); the extra views (covers, openers…) take their model's kitchen.
The model pages name each kitchen's worktop and cabinets (layout/build.py: GRANITE_SHOW, STEEL_SETTING, translated in
layout/i18n.py): change them with KITCHENS. Set CALM=0 to render the kitchens as they were."""
import os
from . import mats, props, kit, kitchen, common
from .common import kelvin


def C(r, g, b):
    """sRGB 0-255 -> linear."""
    f = lambda c: (c / 255) / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


def enabled():
    return os.environ.get("CALM", "1") != "0"


# matt cabinet paints
PAINT = {
    "greige": C(186, 176, 160), "taupe": C(142, 128, 114), "mushroom": C(168, 156, 142), "chalk": C(226, 221, 210),
    "stone": C(160, 158, 150), "sage": C(146, 155, 135), "olive": C(92, 97, 80), "slate": C(110, 122, 130),
    "mist": C(162, 174, 180), "ink": C(48, 56, 68), "charcoal": C(56, 56, 54), "clay": C(164, 124, 102),
    "mocha": C(104, 88, 76), "oxblood": C(100, 56, 52), "sand": C(196, 180, 156),
}

# the kitchen round each model: cabinet colour, door (in place of a fluted, slatted or beadboard one), worktop
# (limestone or a light quartz), splashback (the worktop's stone or the wall's plaster) and floor
KITCHENS = {
    # granite
    "gdu8145":   dict(paint="taupe",    door="slab",   top="limestone", splash="stone",   floor="stone"),
    "gst6045":   dict(paint="sage",     door="shaker", top="limestone", splash="plaster", floor="stone"),
    "gst7546":   dict(paint="charcoal", door="groove", top="limestone", splash="stone",   floor="micro"),
    "gsu6045":   dict(paint="greige",   door="slab",   top="quartz",    splash="plaster", floor="stone"),
    "gsu7545":   dict(paint="olive",    door="slab",   top="limestone", splash="stone",   floor="stone"),
    "gsu8045":   dict(paint="clay",     door="slab",   top="limestone", splash="stone",   floor="stone"),
    # stainless steel, pressed
    "lps5040":   dict(paint="mist",     door="slab",   top="quartz",    splash="plaster", floor="stone"),
    "lps7540a":  dict(paint="stone",    door="shaker", top="limestone", splash="stone",   floor="stone"),
    "lps8643a":  dict(paint="chalk",    door="shaker", top="limestone", splash="stone",   floor="stone"),
    "lps9643a":  dict(paint="charcoal", door="slab",   top="limestone", splash="plaster", floor="micro"),
    "lps10050a": dict(paint="ink",      door="shaker", top="limestone", splash="stone",   floor="stone"),
    "wl03":      dict(paint="sand",     door="slab",   top="quartz",    splash="plaster", floor="stone"),
    "wl05a":     dict(paint="sage",     door="shaker", top="limestone", splash="stone",   floor="stone"),
    "wl07":      dict(paint="clay",     door="slab",   top="quartz",    splash="stone",   floor="stone"),
    "wl11":      dict(paint="slate",    door="slab",   top="limestone", splash="plaster", floor="stone"),
    "wl12":      dict(paint="greige",   door="slab",   top="limestone", splash="plaster", floor="micro"),
    "wl18":      dict(paint="mushroom", door="slab",   top="limestone", splash="stone",   floor="stone"),
    # stainless steel, hand made
    "w5050tsb":  dict(paint="olive",    door="slab",   top="limestone", splash="stone",   floor="stone"),
    "w6045tss":  dict(paint="chalk",    door="groove", top="quartz",    splash="plaster", floor="stone"),
    "w6045tsb":  dict(paint="mushroom", door="slab",   top="limestone", splash="plaster", floor="micro"),
    "w7546tsb":  dict(paint="taupe",    door="slab",   top="limestone", splash="stone",   floor="stone"),
    "w7546tsbn": dict(paint="charcoal", door="groove", top="quartz",    splash="stone",   floor="stone"),
    "w7646uss":  dict(paint="stone",    door="slab",   top="limestone", splash="stone",   floor="micro"),
    "w7646usb":  dict(paint="greige",   door="slab",   top="quartz",    splash="plaster", floor="stone"),
    "w7845uds":  dict(paint="mushroom", door="shaker", top="limestone", splash="plaster", floor="stone"),
    "w7845udb":  dict(paint="oxblood",  door="slab",   top="limestone", splash="stone",   floor="stone"),
    "w8050tss":  dict(paint="chalk",    door="groove", top="quartz",    splash="plaster", floor="stone"),
    "w8050tsb":  dict(paint="mocha",    door="slab",   top="limestone", splash="stone",   floor="stone"),
    "w8245tdb":  dict(paint="mist",     door="shaker", top="limestone", splash="stone",   floor="stone"),
    "w8550tdg":  dict(paint="stone",    door="slab",   top="quartz",    splash="stone",   floor="stone"),
    "w10050tsg": dict(paint="ink",      door="slab",   top="limestone", splash="stone",   floor="stone"),
}
# the extra views, each on its model's kitchen (scenes.EXTRAS)
BASE = {"cover_granite": "gdu8145", "cover_stainless": "w7646uss", "intro_granite": "gsu7545", "intro_stainless": "w7546tsbn",
        "opener_pressed": "lps9643a", "opener_hand": "w8050tsb", "closing": "w5050tsb", "notes_stainless": "wl18",
        "index_granite": "gst6045", "closing_granite": "gsu8045"}

LIMESTONE = C(216, 205, 186)      # warm ivory, honed
QUARTZ = C(228, 223, 213)         # a soft light quartz, warm
WALL = C(232, 226, 215)           # lime plaster, warm white
FLOOR = C(190, 180, 164)          # limestone floor, a shade deeper than the worktop
MICRO = C(186, 178, 166)          # microcement

CUR = {}


def kitchen_of(name):
    return KITCHENS[BASE.get(name, name)]


def materials(name):
    k = kitchen_of(name)
    seed = (sum(map(ord, BASE.get(name, name))) % 17) * 0.37
    top = (mats.limestone(base=LIMESTONE, rough=0.5, seed=seed) if k["top"] == "limestone"
           else mats.quartz(base=QUARTZ, speck=C(200, 194, 184), dens=0.03, rough=0.36))
    wall = mats.plaster(WALL, var=0.035, rough=0.92, scale=0.45, bump=0.05)
    m = dict(top=top, wall=wall,
             paint=mats.paint(PAINT[k["paint"]], rough=0.62, texture=0.012),
             splash=top if k["splash"] == "stone" else wall,
             floor=(mats.limestone(base=FLOOR, rough=0.55, seed=seed + 1.0, bands=0.15, joints=(0.9, 0.6, 0.003)) if k["floor"] == "stone"
                    else mats.concrete(base=MICRO, rough=0.6, tone=0.05, pores=False)),
             ledge=mats.limestone(base=LIMESTONE, rough=0.52, seed=seed + 2.0, bands=0.1),
             handle=mats.metal("steel"))
    return m


# ── while a recipe builds ─────────────────────────────────────────────────

def _noop(*a, **k):
    return []


ORIG = {}


def _orig(mod, attr):
    """The library's own function, as it was before any recipe was built (begin() may run once per recipe in one
    process: the scene audit builds them all)."""
    key = (mod.__name__, attr)
    if key not in ORIG:
        ORIG[key] = getattr(mod, attr)
    return ORIG[key]


def begin(name):
    """Stand in for what the brief leaves out, while the recipe called `name` is built."""
    k = kitchen_of(name)
    CUR.clear()
    CUR.update(name=name, door=k["door"], worktop=0, shelf=0, sill=0, in_group=False)
    # fronts: plain painted ones
    door0 = _orig(kitchen, "door")

    def door(x0, x1, z0, z1, yf, style, mat, col, handle=None, hmat=None, hpos="top", t=0.019, gap=0.003):
        if style in ("fluted", "slatted", "beadboard"):
            style = CUR["door"]
        if handle == "leather":
            handle = "edge"
        return door0(x0, x1, z0, z1, yf, style, mat, col, handle=handle, hmat=hmat, hpos=hpos, t=t, gap=gap)
    kitchen.door = door
    # the small things of a lived-in kitchen: not placed
    for f in ("board", "bottle", "soap_pump", "wine_glass", "tumbler", "towel", "plate_stack", "book_stack", "jar", "cup"):
        setattr(props, f, _guard(_orig(props, f), allow=False))
    for f in ("board_with", "oil_and_salt"):
        _orig(kit, f)
        setattr(kit, f, _noop)
    props.lemon = _guard(_orig(props, "lemon"), allow=False)
    # one styling piece on the worktop; two or three on a shelf; herbs on a sill
    props.vase = _guard(_orig(props, "vase"))
    props.bowl = _guard(_orig(props, "bowl"))
    props.herb_pot = _guard(_orig(props, "herb_pot"))
    props.vessel = _guard(_orig(props, "vessel"))
    props.branch = _stem(_orig(props, "branch"))
    kit.garden = _free(_orig(kit, "garden"))
    kit.fruit_bowl = _group(_orig(kit, "fruit_bowl"))
    kit.branches = _group(_orig(kit, "branches"))
    _orig(kit, "shelf_items")
    kit.shelf_items = _shelf_items
    # shelves and wall cabinets without their light strips
    shelf0, uppers0 = _orig(kit, "shelf"), _orig(kit, "uppers")
    kit.shelf = lambda ctx, *a, **kw: shelf0(ctx, *a, **dict(kw, led=None))
    kit.uppers = lambda ctx, *a, **kw: uppers0(ctx, *a, **dict(kw, led=None))
    _orig(kitchen, "led_strip")
    kitchen.led_strip = _noop
    # every light: soft daylight from the same side
    kit.natural = _calm_light(_orig(kit, "natural"))
    for f in ("golden", "daylight", "moody"):
        _orig(kit, f)
    kit.golden = lambda ctx, side=1, **kw: CUR["light"](ctx, side=side)
    kit.daylight = lambda ctx, sun_azim=200, **kw: CUR["light"](ctx, side=-1 if (sun_azim or 0) > 180 else 1)
    kit.moody = lambda ctx, key_dir=(-1.5, -0.75, 1.65), **kw: CUR["light"](ctx, side=-1 if key_dir[0] < 0 else 1)


def _where(z):
    """worktop, sill or shelf, from the height something is placed at."""
    H = CUR.get("H", 0.91)
    if abs(z - H) < 0.03:
        return "worktop"
    win = CUR.get("window")
    if win and abs(z - win["z0"]) < 0.03:
        return "sill"
    return "shelf"


def _guard(fn, allow=True):
    """A prop that is placed only inside a styling group, or while its place still has room. Fruit is placed only in
    a bowl: in a styling group, or in the one bowl kept on the worktop."""
    def wrap(name, x, y, z, *a, **kw):
        if CUR.get("in_group"):
            return fn(name, x, y, z, *a, **kw)
        if not allow:
            bowl = CUR.get("bowl")
            if fn.__name__ == "lemon" and bowl and (x - bowl[0]) ** 2 + (y - bowl[1]) ** 2 < bowl[2] ** 2:
                return fn(name, x, y, z, *a, **kw)
            return []
        if 0.005 < z - CUR.get("H", 0.91) < 0.05:  # it stood on a board or a tray, which is left out
            return []
        w = _where(z)
        if w == "worktop":
            if CUR["worktop"] >= 1:
                return []
            CUR["worktop"] += 1
            if fn.__name__ == "bowl":
                CUR["bowl"] = (x, y, kw.get("r", 0.12))
        elif w == "sill":
            if CUR["sill"] >= 2:
                return []
            CUR["sill"] += 1
        else:
            if CUR["shelf"] >= 3:
                return []
            CUR["shelf"] += 1
        CUR.setdefault("kept", []).append((x, y))
        # what it is made of (a bowl is a vessel, a herb pot a vessel and leaves) comes with it
        was = CUR.get("in_group")
        CUR["in_group"] = True
        try:
            return fn(name, x, y, z, *a, **kw)
        finally:
            CUR["in_group"] = was
    return wrap


def _stem(fn):
    """A branch stands in a vessel: in a styling group, or in a pot or vase that was kept at the same spot. One whose
    jug or bottle was left out is not placed."""
    def wrap(name, x, y, z, *a, **kw):
        if CUR.get("in_group") or any((x - kx) ** 2 + (y - ky) ** 2 < 0.03 ** 2 for kx, ky in CUR.get("kept", [])):
            return fn(name, x, y, z, *a, **kw)
        return []
    return wrap


def _free(fn):
    """Something outside the room (trees beyond a window): placed as it was, outside the styling budgets."""
    def wrap(ctx, *a, **kw):
        was = CUR.get("in_group")
        CUR["in_group"] = True
        try:
            return fn(ctx, *a, **kw)
        finally:
            CUR["in_group"] = was
    return wrap


def _group(fn):
    """A styling group on the worktop (a bowl of fruit, a vase of branches): the first one only."""
    def wrap(ctx, *a, **kw):
        z = kw.get("z", ctx["H"])
        if _where(z) == "worktop":
            if CUR["worktop"] >= 1:
                return None
            CUR["worktop"] += 1
        CUR["in_group"] = True
        try:
            return fn(ctx, *a, **kw)
        finally:
            CUR["in_group"] = False
    return wrap


def _shelf_items(ctx, x0, x1, z, seed=1, kinds=None, palette=None, y=None):
    """Two or three pieces of plain stoneware on a shelf, well apart. A row along the back of the worktop is not
    placed: the worktop keeps its one piece."""
    if CUR["shelf"] >= 3 or _where(z) == "worktop":
        return
    yw = ctx["wall_y"]
    y = y if y is not None else yw - 0.12
    pal = [mats.ceramic(C(226, 220, 208), matte=True, speck=0.04), mats.ceramic(C(150, 140, 128), matte=True, speck=0.05),
           mats.ceramic(C(196, 186, 170), matte=True)]
    span = x1 - x0
    CUR["in_group"] = True
    try:
        n = 3 if span > 1.4 else 2
        for i in range(n):
            if CUR["shelf"] >= 3:
                break
            x = x0 + span * (i + 0.5) / n + (0.06 if i % 2 else -0.04)
            m = pal[(seed + i) % len(pal)]
            if i % 2 == 0:
                props.vase(f"cs{seed}_{i}", x, y, z, h=0.2 + 0.04 * ((seed + i) % 3), r=0.055, neck=0.024, mat=m, style=(seed + i) % 3)
            else:
                props.bowl(f"cs{seed}_{i}", x, y, z, r=0.09, h=0.055, mat=m)
            CUR["shelf"] += 1
    finally:
        CUR["in_group"] = False


def _light(ctx, side=-1, back_window=None):
    """Soft daylight: the room's light from every open side, a tall window off to one side giving direction, no sun."""
    nat = CUR["natural"]
    env = lambda k, d: float(os.environ.get(k, d))
    nat(ctx, side=side, power=env("CALM_POWER", CUR.get("power", 320)), k=5900, size=(2.2, 2.2), dist=2.4, front=-0.8, height=1.1,
        room=env("CALM_ROOM", CUR.get("room", 0.15)), sat=0.5, sun=False, back_window=back_window)
    # a soft bounce from the camera's side, as an interior photographer would use, so the fronts are never in murk
    common.area_light("bounce", (ctx["sx"], ctx["sy"] - 3.0, ctx["H"] + 0.9), (ctx["sx"], ctx["sy"], ctx["H"] - 0.3),
                      size=(3.0, 1.6), energy=env("CALM_BOUNCE", CUR.get("bounce", 0)), color=kelvin(5800), spread=150)


def _calm_light(nat0):
    CUR["natural"] = nat0
    CUR["light"] = _light

    def natural(ctx, side=-1, *a, back_window=None, **kw):
        return _light(ctx, side=side, back_window=back_window)
    return natural


# ── the recipe's surfaces ─────────────────────────────────────────────────

def restyle(name, R):
    """The recipe R with its new worktop, cabinets, splashback, floor, walls, light and finish."""
    k = kitchen_of(name)
    m = materials(name)
    old = dict(counter=R.get("counter"), cab=(R.get("cab") or {}).get("cab_mat"), floor=R.get("floor"), wall=R.get("wall"),
               splash=(R.get("splash") or {}).get("mat"), side=(R.get("side_wall") or {}).get("mat"))
    CUR.update(H=R.get("height", 0.91), window=R.get("window"), m=m, old=old, kitchen=k)
    R["counter"] = m["top"]
    cab = dict(R.get("cab") or {})
    cab["cab_mat"] = m["paint"]
    if cab.get("door") in ("fluted", "slatted", "beadboard", None):
        cab["door"] = k["door"]
    if cab.get("handle") == "leather":
        cab["handle"] = "edge"
    if cab.get("handle_mat") is not None and cab["handle_mat"].name.startswith("wood"):
        cab["handle_mat"] = m["handle"]
    R["cab"] = cab
    if R.get("floor") is not None:
        R["floor"] = m["floor"]
    if R.get("wall") is not None:
        R["wall"] = m["wall"]
    if R.get("splash"):
        R["splash"] = dict(R["splash"], mat=m["splash"])
    if R.get("side_wall"):
        R["side_wall"] = dict(R["side_wall"], mat=m["wall"])
    win = R.get("window")
    if win:
        win = dict(win)
        if win["frame"].name.startswith("wood") or _coloured(win["frame"]):
            win["frame"] = mats.metal("black")
        win["sill"] = m["ledge"]
        win["reveal_mat"] = m["wall"]
        R["window"] = win
        CUR["window"] = win
    R["exposure"] = float(os.environ.get("CALM_EXP", k.get("exposure", -1.75)))
    R["look"] = os.environ.get("CALM_LOOK", "AgX - Medium High Contrast")
    R["post"] = dict(bloom=0.03, threshold=2.0, dispersion=0.0, vignette=0.08)
    R.setdefault("after_build", []).append(_remap)
    return R


# what each kind of piece is made of now, by its name
PAINTED = ("door", "door_panel", "door_rail", "door_core", "flute", "slat", "bead", "upper_body", "tall", "plinth", "panel", "end_panel")
LEDGES = ("shelf", "sill", "ledge", "rev_l", "rev_r", "rev_t", "upright", "rod", "bracket")


def _remap(ctx):
    """Every surface that still shows the old palette, or wood, takes the new one."""
    import bpy
    m, old = CUR["m"], CUR["old"]
    # first come, first kept: a recipe whose splashback is its wall's plaster or its worktop's stone keeps those
    swap = {}
    for key, new in (("counter", m["top"]), ("cab", m["paint"]), ("wall", m["wall"]), ("floor", m["floor"]),
                     ("side", m["wall"]), ("splash", m["splash"])):
        if old.get(key) is not None:
            swap.setdefault(old[key].name, new)
    sink = {o.name for o in ctx["sink"]["objects"]}
    for ob in bpy.data.objects:
        if ob.type != 'MESH' or ob.name in sink:
            continue
        base = ob.name.split(".")[0]
        for slot in ob.material_slots:
            mat = slot.material
            if mat is None:
                continue
            if mat.name in swap:
                slot.material = swap[mat.name]
            elif mat.name.startswith("wood"):
                if base in LEDGES:
                    slot.material = m["ledge"]
                elif base in ("knob", "bar", "bar_post", "vbar", "vbar_post", "edge_pull", "cup", "strap"):
                    slot.material = m["handle"]
                elif base.endswith("_br") or base.startswith("tree") or "stem" in base:
                    pass        # a branch's stems
                else:
                    slot.material = m["paint"]
            elif base in PAINTED and mat.name.startswith(("paint", "plaster", "concrete", "marble", "travertine", "terrazzo", "tile")):
                dark = mat.name.startswith("paint") and _is_dark_core(mat)
                if not dark:
                    slot.material = m["paint"]
            elif base in ("worktop",) and not mat.name.startswith(("limestone", "quartz")):
                slot.material = m["top"]


def _is_dark_core(mat):
    """The near-black paint inside a carcass or behind slats."""
    try:
        bsdf = [n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
        c = bsdf.inputs['Base Color'].default_value
        return max(c[0], c[1], c[2]) < 0.05
    except Exception:
        return False


def _coloured(mat):
    """A frame painted a colour rather than black, grey or white: it went with a tiled scheme that is gone."""
    try:
        bsdf = [n for n in mat.node_tree.nodes if n.type == 'BSDF_PRINCIPLED'][0]
        c = bsdf.inputs['Base Color'].default_value
        hi, lo = max(c[0], c[1], c[2]), min(c[0], c[1], c[2])
        return hi > 0 and (hi - lo) / hi > 0.3
    except Exception:
        return False

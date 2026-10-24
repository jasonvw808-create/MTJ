"""Building blocks the recipes share: positions round the sink, light set-ups, windows with the day
outside, shelves and wall cabinets, and small groups of props."""
import math
import random
import bpy
from mathutils import Vector
from . import mats, props, geo, kitchen, common
from .common import kelvin


# ── where things go, round the sink ────────────────────────────────────────

def left(ctx, d=0.1):
    return ctx["sx"] - ctx["W"] / 2 - d


def right(ctx, d=0.1):
    return ctx["sx"] + ctx["W"] / 2 + d


def behind(ctx, d=0.06):
    return ctx["sy"] + ctx["D"] / 2 + d


# ── light ──────────────────────────────────────────────────────────────────

def moody(ctx, key_dir=(-1.5, -0.75, 1.65), key_power=190, key_size=(1.3, 1.1), key_k=5000, fill=10, world=(0.006, 0.0055, 0.005),
          rim_dir=(1.5, 1.3, 0.8), rim_power=26, rim_k=3000, top=22, top_k=4500):
    sx, sy, H = ctx["sx"], ctx["sy"], ctx["H"]
    common.world_color(ctx["sc"], world, 1.0)
    tgt = (sx, sy, H)
    common.area_light("key", (sx + key_dir[0], sy + key_dir[1], H + key_dir[2]), tgt, size=key_size, energy=key_power, color=kelvin(key_k), spread=110)
    if fill:
        common.area_light("fill", (sx + 0.4, sy - 2.6, H + 1.0), tgt, size=(2.0, 1.2), energy=fill, color=kelvin(5200))
    if rim_power:
        common.area_light("rim", (sx + rim_dir[0], sy + rim_dir[1], H + rim_dir[2]), tgt, size=(0.8, 0.5), energy=rim_power, color=kelvin(rim_k), spread=90)
    if top:
        common.area_light("top", (sx + 0.1, sy - 0.25, H + 1.35), (sx, sy, H - 0.1), size=(0.7, 0.5), energy=top, color=kelvin(top_k))


def daylight(ctx, sun_elev=32, sun_azim=200, sun_power=4.0, sun_k=5400, sky=1.0, window_light=None, key_dir=None, key_power=150, key_k=6200,
             key_size=(1.6, 1.4), fill=18, top=12, top_k=5600):
    """A sunny or bright interior. sun_azim: 180 = from behind the back wall (through a window there);
    90 = from the right; 270 = from the left."""
    sx, sy, H = ctx["sx"], ctx["sy"], ctx["H"]
    common.world_sky(ctx["sc"], sun_elev=sun_elev, sun_rot=sun_azim, strength=sky)
    if sun_power:
        common.sun("sun", elev=sun_elev, azim=sun_azim, energy=sun_power, color=kelvin(sun_k), angle=1.2)
    tgt = (sx, sy, H)
    if key_dir:
        common.area_light("key", (sx + key_dir[0], sy + key_dir[1], H + key_dir[2]), tgt, size=key_size, energy=key_power, color=kelvin(key_k), spread=120)
    if fill:
        common.area_light("fill", (sx, sy - 2.6, H + 1.1), tgt, size=(2.4, 1.4), energy=fill, color=kelvin(6000))
    if top:
        common.area_light("top", (sx + 0.1, sy - 0.25, H + 1.35), (sx, sy, H - 0.1), size=(0.8, 0.6), energy=top, color=kelvin(top_k))


def portal(ctx, win):
    """An area light filling the window opening, marked as a portal so the sky's light is found."""
    yw = ctx["wall_y"]
    w, h = win["x1"] - win["x0"], win["z1"] - win["z0"]
    ld = bpy.data.lights.new("portal", 'AREA')
    ld.shape = 'RECTANGLE'
    ld.size, ld.size_y = w, h
    try:
        ld.cycles.is_portal = True
    except Exception:
        pass
    ob = bpy.data.objects.new("portal", ld)
    ctx["sc"].collection.objects.link(ob)
    ob.location = ((win["x0"] + win["x1"]) / 2, yw + 0.16, (win["z0"] + win["z1"]) / 2)
    ob.rotation_euler = (math.radians(90), 0, 0)  # facing -y, into the room


def garden(ctx, y0=2.0, x0=-3, x1=3, seed=2, col=(0.12, 0.2, 0.08), n=9, h=(1.4, 2.8), ground=True):
    """Foliage outside a window: a few loose trees of leaves, far enough to fall out of focus."""
    rnd = random.Random(seed)
    for i in range(n):
        x = rnd.uniform(x0, x1)
        y = y0 + rnd.uniform(0.3, 2.5)
        props.branch(f"tree{i}", x, y, rnd.uniform(0.2, 0.8), height=rnd.uniform(*h), leaf_col=tuple(c * rnd.uniform(0.75, 1.25) for c in col),
                     n_leaves=900, seed=seed * 10 + i, stems=5, leaf_len=0.11, leaf_w=0.05)
    if ground:
        geo.box(-8, y0, -0.05, 8, y0 + 8, 0.0, name="lawn", mat=mats.paint((0.10, 0.14, 0.06), 0.9, texture=0))


def outside_wall(ctx, y=4.0, mat=None):
    """A sunlit garden wall far behind a window."""
    geo.box(-8, y, 0, 8, y + 0.2, 3.0, name="garden_wall", mat=mat or mats.plaster((0.6, 0.55, 0.47), var=0.08))


# ── wall cabinets, shelves ─────────────────────────────────────────────────

def uppers(ctx, x0, x1, z0, z1, style, depth=0.34, door_w=0.5, led=None):
    yw = ctx["wall_y"]
    cm = style["cab_mat"]
    geo.box(x0, yw - depth + 0.02, z0, x1, yw, z1, name="upper_body", mat=cm)
    n = max(1, int(round((x1 - x0) / door_w)))
    w = (x1 - x0) / n
    for i in range(n):
        a, b = x0 + w * i, x0 + w * (i + 1)
        kitchen.door(a, b, z0, z1, yw - depth, style["door"], cm, None, handle=style.get("upper_handle", style.get("handle")),
                     hmat=style.get("handle_mat"), hpos="bottom")
    if led:
        kitchen.led_strip(x0 + 0.02, x1 - 0.02, z0 - 0.001, yw - depth + 0.05, None, color=kelvin(led[1]), strength=led[0])


def shelf(ctx, x0, x1, z, depth=0.26, mat=None, t=0.04, led=None, brackets=None):
    yw = ctx["wall_y"]
    kitchen.shelf(x0, x1, z, yw, depth, mat, None, t=t, brackets=brackets)
    if led:
        kitchen.led_strip(x0 + 0.02, x1 - 0.02, z - t - 0.001, yw - 0.03, None, color=kelvin(led[1]), strength=led[0])
    return z


def shelf_items(ctx, x0, x1, z, seed=1, kinds=("vase", "bowl", "plates", "jar", "jar", "books", "vase2"), palette=None, y=None):
    """Spread a few things along a shelf."""
    rnd = random.Random(seed)
    yw = ctx["wall_y"]
    y = y if y is not None else yw - 0.13
    pal = palette or [mats.ceramic((0.78, 0.74, 0.66), matte=True, speck=0.05), mats.ceramic((0.12, 0.11, 0.10), rough=0.35),
                      mats.ceramic((0.62, 0.50, 0.38), matte=True)]
    x = x0 + 0.12
    i = 0
    while x < x1 - 0.12 and i < 40:
        k = kinds[i % len(kinds)]
        m = pal[rnd.randrange(len(pal))]
        if k == "vase":
            props.vase(f"sv{i}", x, y, z, h=rnd.uniform(0.18, 0.3), r=rnd.uniform(0.05, 0.075), neck=0.025, mat=m, style=0)
            x += 0.2
        elif k == "vase2":
            props.vase(f"sv{i}", x, y, z, h=rnd.uniform(0.14, 0.22), r=0.055, mat=m, style=2)
            x += 0.18
        elif k == "bowl":
            props.bowl(f"sb{i}", x + 0.04, y, z, r=0.1, h=0.065, mat=m)
            x += 0.26
        elif k == "plates":
            props.plate_stack(f"spl{i}", x + 0.04, y, z, r=0.11, n=rnd.randint(3, 6), mat=m)
            x += 0.27
        elif k == "jar":
            props.jar(f"sj{i}", x, y, z, r=0.045, h=rnd.uniform(0.12, 0.2), mat=mats.glass((0.92, 0.9, 0.85)), lid=mats.wood("oak"))
            x += 0.13
        elif k == "books":
            props.book_stack(f"sbk{i}", x + 0.05, y, z, n=rnd.randint(2, 4), seed=seed + i, rot=0.0)
            x += 0.28
        elif k == "cups":
            for j in range(2):
                props.cup(f"sc{i}{j}", x + j * 0.1, y, z, mat=m)
            x += 0.24
        elif k == "plant":
            props.herb_pot(f"sh{i}", x, y, z, r=0.06, h=0.1, pot_mat=m, seed=seed + i)
            x += 0.2
        elif k == "bottle":
            props.bottle(f"sbo{i}", x, y, z, h=rnd.uniform(0.22, 0.3), r=0.03, glass=mats.glass((0.55, 0.6, 0.45)), cap=mats.metal("black"))
            x += 0.12
        elif k == "gap":
            x += 0.18
        i += 1


# ── prop groups on the worktop ─────────────────────────────────────────────

def board_with(ctx, x, y, rot=0.15, wood="walnut", w=0.44, d=0.3, fruit="lemon", n=2, round_=False):
    H = ctx["H"]
    props.board("board", x, y, H, w=w, d=d, t=0.028, rot=rot, wood=wood, round_=round_)
    for i in range(n):
        dx, dy = [(0.02, 0.03), (0.09, -0.04), (-0.06, -0.02)][i % 3]
        props.lemon(f"bf{i}", x + dx, y + dy, H + 0.028, kind=fruit, s=0.95, rot=i * 1.3)


def fruit_bowl(ctx, x, y, mat, r=0.13, fruit=("lemon", "lime", "lemon", "lime"), h=0.08):
    H = ctx["H"]
    props.bowl("fbowl", x, y, H, r=r, h=h, mat=mat)
    offs = [(-0.035, 0.0), (0.04, 0.02), (0.0, -0.045), (0.05, -0.04), (-0.05, 0.045)]
    for i, k in enumerate(fruit):
        dx, dy = offs[i % len(offs)]
        props.lemon(f"ff{i}", x + dx, y + dy, H + 0.022, kind=k, s=0.85 if k != "apple" else 0.9, rot=i)


def branches(ctx, x, y, vase_mat, h=0.32, r=0.08, leaf=(0.12, 0.15, 0.09), seed=3, height=0.5, style=0, n_leaves=140, z=None):
    z = ctx["H"] if z is None else z
    props.vase("bv", x, y, z, h=h, r=r, neck=0.032, mat=vase_mat, style=style)
    props.branch("br", x, y, z + h - 0.04, height=height, leaf_col=leaf, n_leaves=n_leaves, seed=seed)


def oil_and_salt(ctx, x, y, glass_col=(0.5, 0.42, 0.25)):
    H = ctx["H"]
    props.bottle("oil", x, y, H, h=0.27, r=0.032, glass=mats.glass(glass_col), liquid=mats.liquid_oil(), cap=mats.metal("black"))
    props.bowl("salt", x + 0.09, y - 0.03, H, r=0.045, h=0.035, mat=mats.ceramic((0.85, 0.83, 0.78), matte=True))


def outside_glow(ctx, strength=2.2, color=(1.0, 0.98, 0.95), y=None):
    """A bright backdrop far outside the window: the view out reads as daylight, the way an interior
    photograph exposes for the room. Seen by the camera only; it does not light the room."""
    yw = ctx["wall_y"] if y is None else y
    ob = geo.box(-10, yw + 7.0, -2.0, 10, yw + 7.2, 8.0, name="sky_card", mat=mats.emission(color, strength))
    ob.visible_diffuse = False
    ob.visible_glossy = True
    ob.visible_shadow = False
    ob.visible_transmission = True
    return ob


def reflector(ctx, power=60, k=5600, size=(1.6, 0.6), dy=0.25, dz=1.05):
    """A softbox the camera never sees, set behind and above the sink so flat steel picks up a sheen
    instead of mirroring a dark room."""
    sx, sy, H = ctx["sx"], ctx["sy"], ctx["H"]
    ob = common.area_light("reflector", (sx, ctx["wall_y"] - dy, H + dz), (sx, sy - 0.3, H), size=size, energy=power, color=kelvin(k), spread=60)
    ob.visible_camera = False
    ob.visible_diffuse = False
    return ob

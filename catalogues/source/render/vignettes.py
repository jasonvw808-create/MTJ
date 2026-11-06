"""The site's category pictures, in the kitchens' own light and materials: a door in a hallway and a
basin with its tap. The door is the supplied product photograph (PT 2602), cut out and set into the wall.
Usage: python -m render.vignettes <door|basin> <out.png> [preview|check|final]"""
import json
import math
import os
import sys
import bpy
from mathutils import Vector
from . import common, geo, mats, props, kit
from .common import kelvin

HERE = os.path.dirname(os.path.abspath(__file__))
# the supplied PT 2602 photograph (Dark Grey, black list), cut out: its colour (door.png), its panes (door_mask.png) and
# its size and edge colours (door.json)
TEX = os.path.join(HERE, "tex")


def C(r, g, b):
    f = lambda c: (c / 255) / 12.92 if c / 255 <= 0.04045 else ((c / 255 + 0.055) / 1.055) ** 2.4
    return (f(r), f(g), f(b))


def quality(sc, q, res, samples):
    k = dict(preview=0.4, check=0.6, final=1.0)[q]
    s = dict(preview=40, check=80, final=samples)[q]
    common.cycles(sc, samples=s, res=(round(res[0] * k), round(res[1] * k)), threshold=0.05 if q == "preview" else 0.022,
                  look="AgX - Medium High Contrast")


def photo_material(name, path, mask_path, rough=(0.48, 0.16), glow=0.0):
    """The product photograph as a surface: its colour and cut-out from the picture; the panes (the mask) smoother,
    and if glow is set, a little of the room behind showing through their frosting."""
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(path)
    tex.interpolation = 'Cubic'
    msk = nt.nodes.new("ShaderNodeTexImage")
    msk.image = bpy.data.images.load(mask_path)
    msk.image.colorspace_settings.name = 'Non-Color'
    ro = nt.nodes.new("ShaderNodeMapRange")
    ro.inputs["To Min"].default_value = rough[0]
    ro.inputs["To Max"].default_value = rough[1]
    nt.links.new(msk.outputs["Color"], ro.inputs["Value"])
    nt.links.new(ro.outputs["Result"], bsdf.inputs["Roughness"])
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    for k, v in (("Specular IOR Level", 0.45),):
        if k in bsdf.inputs:
            bsdf.inputs[k].default_value = v
    if glow:
        em = nt.nodes.new("ShaderNodeMath")
        em.operation = 'MULTIPLY'
        em.inputs[1].default_value = glow
        nt.links.new(msk.outputs["Color"], em.inputs[0])
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Emission Color"])
        nt.links.new(em.outputs["Value"], bsdf.inputs["Emission Strength"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return m


def plane_xz(name, x0, x1, z0, z1, y, mat):
    """A rectangle standing in the XZ plane at y, facing -y (the camera's side), UVs 0..1."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)], [], [(0, 1, 2, 3)])
    uv = me.uv_layers.new(name="UVMap")
    for i, (u, v) in enumerate(((0, 0), (1, 0), (1, 1), (0, 1))):
        uv.data[i].uv = (u, v)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    ob.data.materials.append(mat)
    return ob


# ── the door: PT 2602 in grey, black list — a hallway in limestone and warm plaster, morning light ──
def door(q):
    sc = bpy.context.scene
    quality(sc, q, (1200, 1500), 160)
    info = json.load(open(os.path.join(TEX, "door.json")))
    lime = mats.marble(base=C(214, 206, 192), vein=C(180, 170, 156), vein2=C(198, 190, 176), rough=0.4, vein_width=0.018, seed=41.0, honed=True,
                       stretch=(1.0, 2.2, 2.4), density=0.55, breakup=0.8)
    floor = mats.tile(col=C(206, 198, 184), grout=C(184, 176, 162), w=0.9, h=0.6, gap=0.0025, rough=0.42, var=0.035, along='XY', offset=0.5, bevel=0.0015)
    wall = mats.plaster(C(196, 187, 174), var=0.04, rough=0.9, scale=0.4, bump=0.06)
    skirt = mats.paint(C(184, 175, 162), rough=0.6, texture=0)
    dark = mats.paint(C(38, 37, 36), rough=0.55, texture=0)
    cer = mats.ceramic(C(226, 218, 204), matte=True, speck=0.05)
    cer2 = mats.ceramic(C(48, 45, 42), rough=0.42)

    objs = []
    objs.append(geo.box(-6, -6, -0.02, 6, 3, 0.0, name="floor", mat=floor))
    objs.append(geo.box(-6, 0.0, 0.0, 6, 0.15, 3.0, name="wall", mat=wall))
    objs.append(geo.box(-1.87, -4.0, 2.8, 6, 0.15, 2.85, name="ceiling", mat=mats.paint((0.7, 0.68, 0.64), 0.9, texture=0)))

    # the door and its frame, as photographed: 2.12 m to the head of the frame
    H = 2.12
    W = H * info["w"] / info["h"]
    dx0, dx1 = -0.1 - W / 2, -0.1 + W / 2
    yd = -0.028
    objs.append(geo.box(-6, -0.012, 0.0, dx0 + 0.005, 0.0, 0.085, name="skirt_l", mat=skirt))
    objs.append(geo.box(dx1 - 0.005, -0.012, 0.0, 6, 0.0, 0.085, name="skirt_r", mat=skirt))
    dm = photo_material("door", os.path.join(TEX, "door.png"), os.path.join(TEX, "door_mask.png"), glow=0.22)
    plane_xz("door", dx0, dx1, 0.0, H, yd, dm)
    edge = mats.paint(tuple(C(*[c * 0.92 for c in info["edge"]])), rough=0.45, texture=0)
    objs.append(geo.box(dx0 + 0.001, yd + 0.0005, 0.0, dx0 + 0.02, 0.0, H - 0.001, name="frame_l", mat=edge))
    objs.append(geo.box(dx1 - 0.02, yd + 0.0005, 0.0, dx1 - 0.001, 0.0, H - 0.001, name="frame_r", mat=edge))
    objs.append(geo.box(dx0 + 0.001, yd + 0.0005, H - 0.02, dx1 - 0.001, 0.0, H - 0.001, name="frame_t", mat=edge))

    # the window the light comes in by: a wall off to the left, out of the frame, with a tall opening in two by two panes
    wx, hy0, hy1, hz0, hz1 = -1.75, -1.6, -0.3, 0.42, 2.6
    for (a, b, c, d, e, f) in ((wx - 0.12, -4.0, 0.0, wx, hy0, 2.8), (wx - 0.12, hy1, 0.0, wx, 0.15, 2.8),
                               (wx - 0.12, hy0, 0.0, wx, hy1, hz0), (wx - 0.12, hy0, hz1, wx, hy1, 2.8),
                               (wx - 0.08, (hy0 + hy1) / 2 - 0.025, hz0, wx - 0.04, (hy0 + hy1) / 2 + 0.025, hz1),
                               (wx - 0.08, hy0, 1.62, wx - 0.04, hy1, 1.67)):
        objs.append(geo.box(a, b, c, d, e, f, name="win", mat=wall))

    # a console in the same limestone, on a dark frame, and what stands on it
    cx0, cx1, cd, ch = 0.66, 1.44, 0.32, 0.8
    objs.append(geo.box(cx0, -cd, ch - 0.045, cx1, -0.004, ch, name="console_top", mat=lime, bevel=0.003))
    for lx in (cx0 + 0.03, cx1 - 0.05):
        for ly in (-cd + 0.03, -0.035):
            objs.append(geo.box(lx, ly, 0.0, lx + 0.02, ly + 0.02, ch - 0.045, name="leg", mat=dark))
    objs.append(geo.box(cx0 + 0.03, -cd + 0.03, 0.12, cx1 - 0.03, -0.015, 0.14, name="rail", mat=dark))
    ctx = dict(sc=sc, sx=0.0, sy=-0.9, H=1.0, wall_y=0.0, overhead=[])
    kit.branches(ctx, 1.24, -0.16, cer2, h=0.34, r=0.08, leaf=(0.12, 0.15, 0.09), seed=77, height=0.6, z=ch, name="bv")
    props.book_stack("books", 0.86, -0.17, ch, n=3, seed=12, rot=0.08, palette=[(0.62, 0.58, 0.52), (0.16, 0.16, 0.15), (0.55, 0.47, 0.38)])
    props.bowl("bowl", 0.86, -0.17, ch + 0.075, r=0.085, h=0.045, mat=cer)
    props.vase("vlow", 1.0, -0.13, 0.14, h=0.34, r=0.1, neck=0.045, mat=cer, style=0)

    # light: the window off to the left; the sun low through it, as the kitchens have it
    kit.natural(ctx, side=-1, power=260, sun=True, sun_elev=26, sun_azim=292, sun_power=4.2, sun_k=5000, room=0.34)
    # camera: eye height, a little to the right of the door, the console beside it
    tgt = Vector((0.3, 0.0, 1.12))
    az, el, dist = math.radians(12), math.radians(1.0), 2.95
    loc = tgt + Vector((math.sin(az) * math.cos(el) * dist, -math.cos(az) * math.cos(el) * dist, math.sin(el) * dist))
    common.camera(sc, tuple(loc), tuple(tgt), lens=40, dof=(Vector((dx1 - 0.3, yd, 1.1)) - loc).length, fstop=5.6)
    common.post(sc, bloom=0.04, vignette=0.12)
    sc.view_settings.exposure = -1.0
    return sc


# ── the basin: a stone vanity, a white vessel basin and a brushed brass wall mixer on limestone ──
def basin(q):
    sc = bpy.context.scene
    quality(sc, q, (1200, 1500), 160)
    lime = mats.marble(base=C(214, 206, 192), vein=C(176, 166, 150), vein2=C(196, 188, 174), rough=0.4, vein_width=0.018, seed=31.0, honed=True,
                       stretch=(1.0, 2.2, 2.4), density=0.7, breakup=0.8)
    lime_wall = mats.marble(base=C(208, 200, 186), vein=C(192, 183, 168), vein2=C(199, 191, 177), rough=0.45, vein_width=0.011, seed=57.0, honed=True,
                            stretch=(1.0, 2.6, 2.6), density=0.35, breakup=0.9)
    floor = mats.tile(col=C(196, 188, 174), grout=C(176, 168, 154), w=0.6, h=0.6, gap=0.0025, rough=0.45, var=0.035, along='XY', offset=0.0, bevel=0.0015)
    dark = mats.paint(C(40, 38, 36), rough=0.5, texture=0)
    white = mats.ceramic(C(238, 236, 231), rough=0.18)
    brass = mats.metal("brass")
    cer2 = mats.ceramic(C(48, 45, 42), rough=0.42)

    objs = []
    objs.append(geo.box(-6, -6, -0.02, 6, 3, 0.0, name="floor", mat=floor))
    objs.append(geo.box(-6, 0.0, 0.0, 6, 0.15, 3.0, name="wall", mat=lime_wall))
    objs.append(geo.box(-1.72, -4.0, 2.7, 6, 0.15, 2.75, name="ceiling", mat=mats.paint((0.7, 0.68, 0.64), 0.9, texture=0)))
    # a floating vanity: the stone top over a dark drawer, set back from its edge
    top = 0.86
    objs.append(geo.box(-0.75, -0.52, top - 0.06, 0.75, -0.002, top, name="vanity_top", mat=lime, bevel=0.003))
    objs.append(geo.box(-0.72, -0.49, top - 0.36, 0.72, -0.004, top - 0.06, name="vanity", mat=dark, bevel=0.002))
    objs.append(geo.box(-0.70, -0.4905, top - 0.205, 0.70, -0.489, top - 0.2, name="drawer_gap", mat=mats.paint(C(18, 17, 16), 0.7, texture=0)))
    # the basin: a round vessel, its waste in brass
    bx, by = 0.0, -0.27
    prof = [(0.07, 0.0), (0.11, 0.006), (0.165, 0.035), (0.19, 0.075), (0.2, 0.125)]
    props.vessel("basin", bx, by, top, prof, white, thick=0.008)
    objs.append(geo.cylinder(bx, by, top + 0.0085, top + 0.011, 0.024, 40, name="waste", mat=brass, bevel=0.001))
    # the mixer on the wall above it
    props.faucet_wall("tap", bx, -0.001, top + 0.125 + 0.19, mat=brass, reach=0.22, spread=0.19)
    # a folded towel, a soap pump, a branch in a dark vase
    props.bowl("dish", -0.44, -0.24, top, r=0.075, h=0.03, mat=mats.ceramic(C(52, 49, 46), rough=0.4))
    objs.append(geo.box(-0.475, -0.262, top + 0.006, -0.405, -0.218, top + 0.03, name="soap", mat=mats.ceramic(C(232, 226, 214), rough=0.6), bevel=0.008))
    wx, hy0, hy1, hz0, hz1 = -1.6, -1.5, -0.2, 0.5, 2.5
    for (a, b, c, d, e, f) in ((wx - 0.12, -4.0, 0.0, wx, hy0, 2.7), (wx - 0.12, hy1, 0.0, wx, 0.15, 2.7),
                               (wx - 0.12, hy0, 0.0, wx, hy1, hz0), (wx - 0.12, hy0, hz1, wx, hy1, 2.7),
                               (wx - 0.08, (hy0 + hy1) / 2 - 0.025, hz0, wx - 0.04, (hy0 + hy1) / 2 + 0.025, hz1),
                               (wx - 0.08, hy0, 1.55, wx - 0.04, hy1, 1.6)):
        objs.append(geo.box(a, b, c, d, e, f, name="win", mat=lime_wall))
    props.soap_pump("pump", 0.38, -0.12, top, mat=mats.ceramic(C(52, 49, 46), rough=0.4), pump=brass)
    ctx = dict(sc=sc, sx=0.0, sy=-0.3, H=top, wall_y=0.0, overhead=[])
    kit.branches(ctx, 0.6, -0.16, cer2, h=0.26, r=0.06, leaf=(0.12, 0.15, 0.09), seed=91, height=0.48, z=top, name="bv")

    kit.natural(ctx, side=-1, power=240, sun=True, sun_elev=28, sun_azim=292, sun_power=4.2, sun_k=5000, room=0.34)
    tgt = Vector((0.02, -0.25, 1.06))
    az, el, dist = math.radians(16), math.radians(9), 1.95
    loc = tgt + Vector((math.sin(az) * math.cos(el) * dist, -math.cos(az) * math.cos(el) * dist, math.sin(el) * dist))
    common.camera(sc, tuple(loc), tuple(tgt), lens=42, dof=(Vector((bx, by, top + 0.12)) - loc).length, fstop=3.2)
    common.post(sc, bloom=0.04, vignette=0.12)
    sc.view_settings.exposure = -1.15
    return sc


def main():
    name, out = sys.argv[1], sys.argv[2]
    q = sys.argv[3] if len(sys.argv) > 3 else "preview"
    common.reset()
    mats._cache.clear()
    sc = dict(door=door, basin=basin)[name](q)
    common.render(sc, out)


if __name__ == "__main__":
    main()

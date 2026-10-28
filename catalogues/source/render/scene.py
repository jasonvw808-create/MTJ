"""Compose a kitchen round a sink from a recipe, light it, frame it and render it.
Usage: python -m render.scene <recipe-name> <out.png> [preview|final]"""
import math
import sys
import bpy
from mathutils import Vector
from . import common, geo, mats, props, kitchen, physics


def build_sink(kind, model, variant):
    if kind == "granite":
        from . import granite
        return granite.build(model, variant)
    if kind == "pressed":
        from . import pressed
        return pressed.build(model)
    from . import handmade
    return handmade.build(model)


def compose(R, quality="preview"):
    sc = bpy.context.scene
    fr = R.get("res", (2000, 1600))
    k = 720 / max(fr)
    q = dict(preview=dict(res=(round(fr[0] * k), round(fr[1] * k)), samples=48, threshold=0.05),
             check=dict(res=(1200, 960), samples=96, threshold=0.03),
             final=dict(res=R.get("res", (2000, 1600)), samples=R.get("samples", 112), threshold=0.025))[quality]
    common.cycles(sc, samples=q["samples"], res=q["res"], threshold=q["threshold"], look=R.get("look", "AgX - Medium High Contrast"),
                  exposure=R.get("exposure", 0.0))
    ctx = dict(sc=sc, R=R, back_faces=[], overhead=[])
    sink = build_sink(R["kind"], R["model"], R.get("variant"))
    ctx["sink"] = sink
    W, D = sink["size"]
    H = R.get("height", 0.91)
    T = R.get("thick", 0.03)
    layout = R.get("layout", "wall")
    if layout == "island":
        y0, y1 = -R.get("island_depth", 1.0) / 2, R.get("island_depth", 1.0) / 2
    else:
        y1 = R.get("wall_y", 0.32)
        y0 = y1 - R.get("depth", 0.64)
    front_margin = R.get("front_margin", 0.07)
    sy = y0 + front_margin + D / 2 if layout != "island" else y0 + front_margin + D / 2
    sx = R.get("sink_x", 0.0)
    cut, zs = kitchen.install_sink(sink, sx, sy, H, T)
    ctx.update(H=H, T=T, y0=y0, y1=y1, sx=sx, sy=sy, zs=zs, W=W, D=D)
    run = R.get("run", (-1.6, 1.6))
    objs = []
    objs += kitchen.worktop(run[0], run[1], y0, y1, H, T, R["counter"], cut, None, edge=R.get("edge", "eased"))
    cab = R["cab"]
    objs += kitchen.base_run(run[0] + 0.0, run[1] - 0.0, y0 + R.get("overhang", 0.02), H - T, cab, None,
                             door_w=cab.get("door_w", 0.6), plinth=cab.get("plinth", 0.1), depth=(y1 - y0) - 0.04,
                             drawers=cab.get("drawers"))
    if layout == "island":
        objs += kitchen.base_run(run[0], run[1], y1 - 0.02, H - T, cab, None, door_w=0.6, depth=0.02)
    # floor
    fl = R.get("floor")
    if fl is not None:
        objs.append(geo.box(-6, -6, -0.02, 6, 6, 0.0, name="floor", mat=fl))
    # walls
    room = R.get("room", {})
    wall_y = R.get("back_wall_y", y1 if layout != "island" else R.get("back_y", 1.9))
    wall_mat = R.get("wall")
    if wall_mat is not None:
        win = R.get("window")
        holes = [(win["x0"], win["x1"], win["z0"], win["z1"])] if win else None
        objs += kitchen.wall(-6, 6, wall_y, 0, 3.2, wall_mat, None, t=0.15 if win else 0.1, holes=holes)
        if win:
            objs += kitchen.window(win["x0"], win["x1"], win["z0"], win["z1"], wall_y, win["frame"], None,
                                   mullions=win.get("mullions", 1), transoms=win.get("transoms", 0), reveal=0.15)
            # the reveal's sides, head and the sill
            rm = win.get("reveal_mat", wall_mat)
            objs.append(geo.box(win["x0"] - 0.0, wall_y, win["z0"] - 0.03, win["x1"], wall_y + 0.15, win["z0"], name="sill", mat=win.get("sill", rm)))
            objs.append(geo.box(win["x0"] - 0.01, wall_y, win["z0"], win["x0"], wall_y + 0.15, win["z1"], name="rev_l", mat=rm))
            objs.append(geo.box(win["x1"], wall_y, win["z0"], win["x1"] + 0.01, wall_y + 0.15, win["z1"], name="rev_r", mat=rm))
            objs.append(geo.box(win["x0"], wall_y, win["z1"], win["x1"], wall_y + 0.15, win["z1"] + 0.01, name="rev_t", mat=rm))
    side = R.get("side_wall")
    if side:
        x = side["x"]
        objs.append(geo.box(x - 0.1 if x > 0 else x, -6, 0, x if x > 0 else x + 0.1, wall_y + 0.2, 3.2, name="side_wall", mat=side["mat"]))
    if R.get("ceiling", True):
        # the room's own ceiling, not one that runs on for metres: daylight from the side comes in under its edge,
        # as through a tall window in the side wall
        cx0, cx1 = min(run[0], -2.4) - 0.3, max(run[1], 2.4) + 0.3
        objs.append(geo.box(cx0, -3.2, R.get("ceiling_z", 2.75), cx1, wall_y + 0.2, R.get("ceiling_z", 2.75) + 0.05, name="ceiling",
                            mat=R.get("ceiling_mat") or mats.paint((0.7, 0.68, 0.64), 0.9, texture=0)))
    # splashback
    sp = R.get("splash")
    if sp and layout != "island":
        h = sp.get("h", 0.6)
        objs.append(geo.box(run[0] if sp.get("full_width") is None else sp["full_width"][0], wall_y - sp.get("t", 0.012), H,
                            run[1] if sp.get("full_width") is None else sp["full_width"][1], wall_y, H + h, name="splash", mat=sp["mat"]))
        ctx["splash"] = dict(t=sp.get("t", 0.012), top=H + h)
        ctx["back_faces"].append((wall_y - sp.get("t", 0.012), H, H + h, run[0], run[1]))
    ctx["wall_y"] = wall_y
    if layout != "island":
        win = R.get("window") if wall_mat is not None else None
        if win:
            # the wall round its window: what stands in the opening (on the sill) is not in front of the wall
            ctx["back_faces"] += [(wall_y, 0.0, win["z0"] - 0.002, -9.0, 9.0), (wall_y, win["z1"], 3.2, -9.0, 9.0),
                                  (wall_y, win["z0"], win["z1"], -9.0, win["x0"]), (wall_y, win["z0"], win["z1"], win["x1"], 9.0)]
        else:
            ctx["back_faces"].append((wall_y, 0.0, 3.2, -9.0, 9.0))
    # the scene's own additions: back run, shelves, uppers, props, lights
    for fn in R.get("build", []):
        fn(ctx)
    # tap
    tap = R.get("tap")
    if tap:
        place_tap(ctx, tap)
    # nothing floats, nothing is sunk into what it stands on or against
    physics.clear_of(ctx, ctx["back_faces"])
    physics.settle(ctx)
    # lights & world
    L = R["light"]
    L(ctx)
    # camera
    cam = R["camera"]
    tgt = Vector((sx + cam.get("tx", 0.0), sy + cam.get("ty", 0.0), H + cam.get("tz", -0.05)))
    el, az, dist = math.radians(cam["elev"]), math.radians(cam.get("azim", 0.0)), cam["dist"]
    loc = tgt + Vector((math.sin(az) * math.cos(el) * dist, -math.cos(az) * math.cos(el) * dist, math.sin(el) * dist))
    focus = Vector((sx + cam.get("fx", 0.0), sy + cam.get("fy", 0.0), H - 0.05 + cam.get("fz", 0.0)))
    common.camera(sc, tuple(loc), tuple(tgt), lens=cam.get("lens", 50), dof=(focus - loc).length if cam.get("fstop") else None,
                  fstop=cam.get("fstop", 4.0), shift=(cam.get("sx", 0.0), cam.get("sy", 0.0)))
    if cam.get("roll"):
        sc.camera.rotation_euler.rotate_axis('Z', math.radians(cam["roll"]))
    if R.get("post", True):
        common.post(sc, **(R["post"] if isinstance(R.get("post"), dict) else {}))
    return ctx


# how far behind its centre each kind of tap reaches (base, cross handles)
TAP_REAR = dict(gooseneck=0.027, pulldown=0.028, square=0.026, bridge=0.037)


def place_tap(ctx, tap):
    sink = ctx["sink"]
    sx, sy, H = ctx["sx"], ctx["sy"], ctx["H"]
    W, D = sink["size"]
    m = tap.get("mat") or mats.metal(tap.get("finish", "steel"))
    kind = tap.get("kind", "gooseneck")
    where = tap.get("where", "behind")
    if where == "taphole":
        hx, hy = tap["hole"]
        x, y, z = sx + hx, sy + hy, ctx["zs"]
    elif where == "wall":
        x, y, z = sx + tap.get("dx", 0.0), ctx["wall_y"], H + tap.get("h", 0.42)
        if ctx.get("splash") and z < ctx["splash"]["top"]:
            y -= ctx["splash"]["t"]   # on the face of the tiling, not inside it
        return props.faucet_wall("tap", x, y, z, mat=m, reach=tap.get("reach", 0.26))
    else:
        x = sx + tap.get("dx", 0.0)
        y = sy + D / 2 + tap.get("gap", 0.05)
        z = H
        # in front of whatever stands behind it (the wall, the splashback, a ledge or an upstand), with room to spare
        rear = TAP_REAR.get(kind, 0.03)
        top = H + tap.get("height", 0.36) + 0.02
        for (yf, z0, z1, x0, x1) in ctx.get("back_faces", []):
            if z0 < top and z1 > H and x0 < x + 0.12 and x1 > x - 0.12 and y + rear + 0.004 > yf:
                y = yf - rear - 0.004
        if y - rear < sy + D / 2 - 0.004:
            print(f"WARNING tap: no room for the {kind} tap between the sink and the back ({(y - sy - D / 2) * 1000:.0f} mm)")
    fn = dict(gooseneck=props.faucet_gooseneck, pulldown=props.faucet_pulldown, square=props.faucet_square, bridge=props.faucet_bridge)[kind]
    kw = dict(mat=m)
    if "height" in tap:
        kw["height"] = tap["height"]
    if "reach" in tap:
        kw["reach"] = tap["reach"]
    if "turn" in tap:
        kw["turn"] = tap["turn"]
    return fn("tap", x, y, z, **kw)


def sink_bbox(ctx):
    """Where the sink lands in the frame: its objects' bounding boxes projected, normalised (x right, y down)."""
    from bpy_extras.object_utils import world_to_camera_view
    sc = ctx["sc"]
    xs, ys = [], []
    for o in ctx["sink"]["objects"]:
        if o.type != 'MESH':
            continue
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            p = world_to_camera_view(sc, sc.camera, w)
            if p.z > 0:
                xs.append(p.x)
                ys.append(1 - p.y)
    return dict(x0=min(xs), x1=max(xs), y0=min(ys), y1=max(ys))


def main():
    name, out = sys.argv[1], sys.argv[2]
    quality = sys.argv[3] if len(sys.argv) > 3 else "preview"
    from . import scenes
    common.reset()
    mats._cache.clear()
    R = scenes.RECIPES[name]()
    ctx = compose(R, quality)
    if len(sys.argv) > 4 and sys.argv[4] == "blend":
        bpy.ops.wm.save_as_mainfile(filepath=out.replace(".png", ".blend"))
    import json
    bpy.context.view_layer.update()
    meta = dict(recipe=name, model=R["model"], variant=R.get("variant"), bbox=sink_bbox(ctx),
                res=[ctx["sc"].render.resolution_x, ctx["sc"].render.resolution_y])
    open(out.rsplit(".", 1)[0] + ".json", "w").write(json.dumps(meta, indent=1))
    common.render(ctx["sc"], out)


if __name__ == "__main__":
    main()

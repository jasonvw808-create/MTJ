"""Scene setup shared by every render: an empty scene, Cycles settings, colour management,
camera helpers."""
import math
import bpy
from mathutils import Vector


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    for c in (bpy.data.meshes, bpy.data.materials, bpy.data.lights, bpy.data.cameras, bpy.data.images, bpy.data.curves):
        for item in list(c):
            c.remove(item)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    return sc


def cycles(sc, samples=256, res=(1600, 1200), denoise=True, threshold=0.015, clamp_indirect=6.0, bounces=None, look='AgX - Medium High Contrast', exposure=0.0):
    sc.render.engine = 'CYCLES'
    c = sc.cycles
    c.device = 'CPU'
    c.samples = samples
    c.use_adaptive_sampling = True
    c.adaptive_threshold = threshold
    c.use_denoising = denoise
    try:
        c.denoiser = 'OPENIMAGEDENOISE'
        c.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
        c.denoising_prefilter = 'ACCURATE'
        c.denoising_quality = 'HIGH'
    except Exception:
        pass
    b = bounces or dict(max=8, diffuse=3, glossy=4, transmission=6, transparent=8, volume=0)
    c.max_bounces = b['max']
    c.diffuse_bounces = b['diffuse']
    c.glossy_bounces = b['glossy']
    c.transmission_bounces = b['transmission']
    c.transparent_max_bounces = b['transparent']
    c.volume_bounces = b['volume']
    c.sample_clamp_indirect = clamp_indirect
    c.sample_clamp_direct = 0.0
    c.caustics_reflective = False
    c.caustics_refractive = False
    c.blur_glossy = 1.0
    try:
        c.use_light_tree = True
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.threads_mode = 'AUTO'
    sc.render.use_persistent_data = False
    vs = sc.view_settings
    try:
        vs.view_transform = 'AgX'
        vs.look = look
    except Exception:
        try:
            vs.view_transform = 'Filmic'
            vs.look = 'Medium High Contrast'
        except Exception:
            pass
    vs.exposure = exposure
    vs.gamma = 1.0
    sc.display_settings.display_device = 'sRGB'
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '16'
    sc.render.image_settings.color_mode = 'RGB'
    return sc


def world_color(sc, col=(0.05, 0.05, 0.05), strength=1.0):
    w = bpy.data.worlds.new("world")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes.get("Background") or nt.nodes.new("ShaderNodeBackground")
    bg.inputs[0].default_value = (*col, 1)
    bg.inputs[1].default_value = strength
    out = nt.nodes.get("World Output") or nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(bg.outputs[0], out.inputs[0])
    return w


def world_sky(sc, sun_elev=25, sun_rot=135, strength=1.0, air=1.0, dust=1.0, ozone=1.0):
    """Physical sky (no image needed)."""
    w = bpy.data.worlds.new("sky")
    sc.world = w
    w.use_nodes = True
    nt = w.node_tree
    nt.nodes.clear()
    sky = nt.nodes.new("ShaderNodeTexSky")
    for t in ('MULTIPLE_SCATTERING', 'NISHITA', 'SINGLE_SCATTERING'):
        try:
            sky.sky_type = t
            break
        except Exception:
            continue
    try:
        sky.sun_elevation = math.radians(sun_elev)
        sky.sun_rotation = math.radians(sun_rot)
        sky.air_density = air
        sky.dust_density = dust
        sky.ozone_density = ozone
        sky.sun_disc = False
    except Exception as e:
        print('sky params', e)
    bg = nt.nodes.new("ShaderNodeBackground")
    bg.inputs[1].default_value = strength
    out = nt.nodes.new("ShaderNodeOutputWorld")
    nt.links.new(sky.outputs[0], bg.inputs[0])
    nt.links.new(bg.outputs[0], out.inputs[0])
    return w


def look_at(ob, target):
    d = Vector(target) - ob.location
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def camera(sc, loc, target, lens=50, sensor=36, dof=None, fstop=4.0, shift=(0, 0), ortho=None, clip=(0.01, 100)):
    cd = bpy.data.cameras.new("cam")
    cd.lens = lens
    cd.sensor_width = sensor
    cd.sensor_fit = 'HORIZONTAL'
    cd.clip_start, cd.clip_end = clip
    cd.shift_x, cd.shift_y = shift
    if ortho:
        cd.type = 'ORTHO'
        cd.ortho_scale = ortho
    cam = bpy.data.objects.new("cam", cd)
    sc.collection.objects.link(cam)
    cam.location = loc
    look_at(cam, target)
    if dof is not None:
        cd.dof.use_dof = True
        cd.dof.focus_distance = dof if isinstance(dof, (int, float)) else (Vector(dof) - Vector(loc)).length
        cd.dof.aperture_fstop = fstop
        cd.dof.aperture_blades = 7
        cd.dof.aperture_rotation = math.radians(10)
    sc.camera = cam
    return cam


def area_light(name, loc, target, size=(1.0, 1.0), energy=100.0, color=(1, 1, 1), spread=180, shape='RECTANGLE', visible=False):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = shape
    ld.size = size[0]
    ld.size_y = size[1]
    ld.energy = energy
    ld.color = color
    try:
        ld.spread = math.radians(spread)
    except Exception:
        pass
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    ob.visible_camera = visible
    return ob


def point_light(name, loc, energy=50.0, color=(1, 0.85, 0.7), radius=0.02):
    ld = bpy.data.lights.new(name, 'POINT')
    ld.energy = energy
    ld.color = color
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    return ob


def spot_light(name, loc, target, energy=200.0, color=(1, 0.9, 0.8), angle=45, blend=0.4, radius=0.03):
    ld = bpy.data.lights.new(name, 'SPOT')
    ld.energy = energy
    ld.color = color
    ld.spot_size = math.radians(angle)
    ld.spot_blend = blend
    ld.shadow_soft_size = radius
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    look_at(ob, target)
    return ob


def sun(name, elev=35, azim=135, energy=4.0, color=(1.0, 0.95, 0.88), angle=1.0):
    ld = bpy.data.lights.new(name, 'SUN')
    ld.energy = energy
    ld.color = color
    ld.angle = math.radians(angle)
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    # light travels along -Z of the object: point it from (azim, elev) towards the origin
    el, az = math.radians(elev), math.radians(azim)
    d = Vector((math.cos(el) * math.sin(az), -math.cos(el) * math.cos(az), math.sin(el)))
    ob.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    return ob


def kelvin(k):
    """Approximate RGB (linear) of a black body at k kelvin, normalised."""
    t = k / 100.0
    if t <= 66:
        r = 255
        g = 99.4708025861 * math.log(t) - 161.1195681661
        b = 0 if t <= 19 else 138.5177312231 * math.log(t - 10) - 305.0447927307
    else:
        r = 329.698727446 * (t - 60) ** -0.1332047592
        g = 288.1221695283 * (t - 60) ** -0.0755148492
        b = 255
    c = [max(0, min(255, v)) / 255.0 for v in (r, g, b)]
    c = [x ** 2.2 for x in c]
    m = max(c)
    return tuple(x / m for x in c)


def render(sc, path):
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)

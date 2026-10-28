"""Procedural materials for the kitchen renders (Cycles). Everything is built from
nodes: no image textures are downloaded. Colours are linear RGB."""
import math
import bpy

_cache = {}


class NB:
    """A small node-tree builder."""

    def __init__(self, name):
        self.mat = bpy.data.materials.new(name)
        self.mat.use_nodes = True
        self.nt = self.mat.node_tree
        self.nt.nodes.clear()
        self.out = self.nt.nodes.new("ShaderNodeOutputMaterial")
        self.out.target = 'CYCLES' if hasattr(self.out, 'target') else self.out.target

    def n(self, kind, **kw):
        node = self.nt.nodes.new(kind)
        for k, v in kw.items():
            if k.startswith('i_'):
                self.set(node, k[2:].replace('_', ' '), v)
            else:
                try:
                    setattr(node, k, v)
                except Exception:
                    pass
        return node

    @staticmethod
    def sock(node, name, outputs=False):
        coll = node.outputs if outputs else node.inputs
        if isinstance(name, int):
            # index among the sockets in use (a Mix node keeps one per data type, most of them off)
            return [s for s in coll if s.enabled][name]
        if name in coll:
            # several sockets may share a name (Mix node); prefer the enabled one
            cands = [s for s in coll if s.name == name and s.enabled]
            return cands[0] if cands else coll[name]
        alias = {"Subsurface": "Subsurface Weight", "Transmission": "Transmission Weight", "Coat": "Coat Weight",
                 "Sheen": "Sheen Weight", "Specular": "Specular IOR Level", "Emission": "Emission Color",
                 "Clearcoat": "Coat Weight", "Clearcoat Roughness": "Coat Roughness", "Fac": "Factor", "Factor": "Fac"}
        if name in alias and alias[name] in coll:
            return coll[alias[name]]
        raise KeyError(f"{node.bl_idname} has no socket {name!r}: {[s.name for s in coll]}")

    def set(self, node, name, value):
        s = self.sock(node, name)
        if isinstance(value, tuple) and len(value) == 3 and s.type == 'RGBA':
            value = (*value, 1.0)
        s.default_value = value

    def link(self, a, b, a_name=0, b_name=0):
        """link(nodeA, nodeB, 'Output', 'Input') or link(socket, socket)."""
        if hasattr(a, 'is_output'):
            sa = a
        else:
            sa = self.sock(a, a_name, outputs=True)
        if hasattr(b, 'is_output'):
            sb = b
        else:
            sb = self.sock(b, b_name)
        self.nt.links.new(sa, sb)
        return b

    # common nodes
    def coord(self, space='Object', scale=1.0, mapping_scale=None, rot=(0, 0, 0), loc=(0, 0, 0)):
        tc = self.n("ShaderNodeTexCoord")
        mp = self.n("ShaderNodeMapping")
        self.link(tc, mp, space, 'Vector')
        s = mapping_scale if mapping_scale is not None else (scale, scale, scale)
        mp.inputs['Scale'].default_value = s
        mp.inputs['Rotation'].default_value = rot
        mp.inputs['Location'].default_value = loc
        return mp

    def noise(self, vec, scale=5.0, detail=4.0, rough=0.5, distortion=0.0, dims='3D'):
        nz = self.n("ShaderNodeTexNoise")
        try:
            nz.noise_dimensions = dims
        except Exception:
            pass
        self.set(nz, 'Scale', scale)
        self.set(nz, 'Detail', detail)
        self.set(nz, 'Roughness', rough)
        if 'Distortion' in nz.inputs:
            self.set(nz, 'Distortion', distortion)
        if vec is not None:
            self.link(vec, nz, 0, 'Vector')
        return nz

    def voronoi(self, vec, scale=10.0, feature='F1', rand=1.0):
        vo = self.n("ShaderNodeTexVoronoi")
        vo.feature = feature
        self.set(vo, 'Scale', scale)
        if 'Randomness' in vo.inputs:
            self.set(vo, 'Randomness', rand)
        if vec is not None:
            self.link(vec, vo, 0, 'Vector')
        return vo

    def ramp(self, src, stops, src_out=0, interp='LINEAR'):
        r = self.n("ShaderNodeValToRGB")
        cr = r.color_ramp
        cr.interpolation = interp
        while len(cr.elements) > len(stops):
            cr.elements.remove(cr.elements[-1])
        while len(cr.elements) < len(stops):
            cr.elements.new(0.5)
        for el, (pos, col) in zip(cr.elements, stops):
            el.position = pos
            if isinstance(col, (int, float)):
                col = (col, col, col)
            el.color = (*col, 1.0) if len(col) == 3 else col
        self.link(src, r, src_out, 'Fac')
        return r

    def mix(self, a, b, fac, blend='MIX', a_out=0, b_out=0, fac_out=0):
        m = self.n("ShaderNodeMix")
        m.data_type = 'RGBA'
        m.blend_type = blend
        sock_f = [s for s in m.inputs if s.name == 'Factor' and s.enabled][0]
        ins = [s for s in m.inputs if s.enabled and s.type == 'RGBA']
        for src, dst, o in ((a, ins[0], a_out), (b, ins[1], b_out)):
            if isinstance(src, tuple):
                dst.default_value = (*src, 1.0) if len(src) == 3 else src
            else:
                self.link(self.sock(src, o, True), dst)
        if isinstance(fac, (int, float)):
            sock_f.default_value = fac
        else:
            self.link(self.sock(fac, fac_out, True), sock_f)
        return m

    def math(self, op, a, b=None, a_out=0, b_out=0, clamp=False):
        m = self.n("ShaderNodeMath")
        m.operation = op
        m.use_clamp = clamp
        for i, (src, o) in enumerate(((a, a_out), (b, b_out))):
            if src is None:
                continue
            if isinstance(src, (int, float)):
                m.inputs[i].default_value = src
            else:
                self.link(self.sock(src, o, True), m.inputs[i])
        return m

    def bump(self, height, strength=0.2, distance=0.001, h_out=0, normal=None):
        b = self.n("ShaderNodeBump")
        self.set(b, 'Strength', strength)
        self.set(b, 'Distance', distance)
        self.link(self.sock(height, h_out, True), self.sock(b, 'Height'))
        if normal is not None:
            self.link(normal, b, 0, 'Normal')
        return b

    def principled(self, **kw):
        p = self.n("ShaderNodeBsdfPrincipled")
        for k, v in kw.items():
            self.set(p, k.replace('_', ' '), v)
        return p

    def finish(self, shader, displacement=None):
        self.link(shader, self.out, 0, 'Surface')
        if displacement is not None:
            self.link(displacement, self.out, 0, 'Displacement')
        return self.mat


def _p(nb, node, name):
    return nb.sock(node, name)


def cached(fn):
    def wrap(*a, **k):
        key = (fn.__name__, repr(a), repr(sorted(k.items())))
        if key not in _cache or _cache[key].name not in bpy.data.materials:
            _cache[key] = fn(*a, **k)
        return _cache[key]
    wrap.__name__ = fn.__name__
    return wrap


# ── sinks ──────────────────────────────────────────────────────────────────

GRANITE_COLOURS = {
    # base albedo, fleck albedo, fleck density, roughness
    "pearl": ((0.020, 0.020, 0.021), (0.16, 0.16, 0.165), 0.06, 0.52),
    "pure": ((0.80, 0.79, 0.77), (0.60, 0.60, 0.59), 0.035, 0.52),
    "titan": ((0.33, 0.335, 0.345), (0.68, 0.68, 0.69), 0.07, 0.50),
}


@cached
def granite_composite(colour):
    """Granite composite: quartz sand bound in resin. A fine sandy grain over the whole face, small specks of the
    lighter (or darker) quartz, a few larger flecks, a matt surface with a soft sheen."""
    base, fleck, dens, rough = GRANITE_COLOURS[colour]
    nb = NB("granite_" + colour)
    co = nb.coord('Object', 1.0)
    # the sand: dense tiny cells, each a little lighter or darker
    sand = nb.voronoi(co, scale=2600.0, feature='F1')
    sand_c = nb.ramp(sand, [(0.0, tuple(c * 0.86 for c in base)), (0.5, base), (1.0, tuple(min(1, c * 1.12 + 0.004) for c in base))], src_out='Color')
    # specks and the odd larger fleck
    vo = nb.voronoi(co, scale=950.0, feature='F1')
    specks = nb.ramp(vo, [(0.0, 1.0), (dens, 1.0), (dens + 0.05, 0.0), (1.0, 0.0)], src_out='Distance')
    vo2 = nb.voronoi(co, scale=320.0, feature='F1')
    flecks = nb.ramp(vo2, [(0.0, 0.8), (dens * 0.45, 0.8), (dens * 0.45 + 0.03, 0.0), (1.0, 0.0)], src_out='Distance')
    nz = nb.noise(co, scale=60.0, detail=3.0, rough=0.6)
    mott = nb.ramp(nz, [(0.3, 0.0), (0.7, 1.0)])
    c0 = nb.mix(sand_c, tuple(c * 1.06 for c in base), mott, blend='MIX')
    c1 = nb.mix(c0, fleck, specks)
    c2 = nb.mix(c1, tuple(min(1, f * 1.15) for f in fleck), flecks)
    # matt with a soft sheen; the grains catch the light
    gn = nb.noise(co, scale=900.0, detail=2.0, rough=0.5)
    gr = nb.n("ShaderNodeMapRange")
    nb.link(gn, gr, 'Fac', 0)
    gr.inputs[3].default_value = rough * 0.85
    gr.inputs[4].default_value = rough * 1.2
    p = nb.principled(Specular_IOR_Level=0.42)
    nb.link(c2, p, 0, 'Base Color')
    nb.link(gr, p, 0, 'Roughness')
    b = nb.bump(sand, strength=0.22, distance=0.00015, h_out='Distance')
    nb.link(b, p, 0, 'Normal')
    nb.set(p, 'Coat Weight', 0.05)
    nb.set(p, 'Coat Roughness', 0.35)
    return nb.finish(p)

STEEL = {
    #               base colour              rough  aniso  brush
    "satin":        ((0.56, 0.56, 0.56), 0.30, 0.75, 1.0),
    "mat_polished": ((0.60, 0.60, 0.60), 0.27, 0.40, 0.6),
    "electroplate": ((0.66, 0.66, 0.66), 0.10, 0.25, 0.3),
    "nano_black":   ((0.105, 0.105, 0.11), 0.24, 0.6, 1.0),
    "brushed_trim": ((0.55, 0.55, 0.55), 0.28, 0.7, 1.0),
}


@cached
def steel(finish):
    base, rough, aniso, brush = STEEL[finish]
    nb = NB("steel_" + finish)
    co = nb.coord('Object', 1.0)
    # brushing: noise stretched along x (and along each wall, see tangent)
    tc = nb.n("ShaderNodeTexCoord")
    stretch = nb.n("ShaderNodeMapping")
    nb.link(tc, stretch, 'Object', 'Vector')
    stretch.inputs['Scale'].default_value = (6.0, 1500.0, 1500.0)
    nz = nb.noise(stretch, scale=1.0, detail=4.0, rough=0.7)
    rr = nb.ramp(nz, [(0.3, rough * (1 - 0.35 * brush)), (0.7, rough * (1 + 0.35 * brush))])
    # tangent: along x on flat parts; horizontal along the wall on walls
    geo = nb.n("ShaderNodeNewGeometry")
    sep = nb.n("ShaderNodeSeparateXYZ")
    nb.link(geo, sep, 'Normal', 0)
    absz = nb.math('ABSOLUTE', sep, None, a_out='Z')
    flat = nb.math('GREATER_THAN', absz, 0.7)
    cross = nb.n("ShaderNodeVectorMath", operation='CROSS_PRODUCT')
    nb.link(geo, cross, 'Normal', 0)
    cross.inputs[1].default_value = (0, 0, 1)
    xvec = nb.n("ShaderNodeCombineXYZ")
    xvec.inputs[0].default_value = 1.0
    mixv = nb.n("ShaderNodeMix")
    mixv.data_type = 'VECTOR'
    fs = [s for s in mixv.inputs if s.name == 'Factor' and s.enabled][0]
    vs = [s for s in mixv.inputs if s.enabled and s.type == 'VECTOR']
    nb.link(nb.sock(flat, 0, True), fs)
    nb.link(nb.sock(cross, 0, True), vs[0])
    nb.link(nb.sock(xvec, 0, True), vs[1])
    norm = nb.n("ShaderNodeVectorMath", operation='NORMALIZE')
    nb.link(mixv, norm, 0, 0)
    # subtle colour variation
    nz2 = nb.noise(co, scale=40.0, detail=2.0)
    col = nb.mix(base, tuple(c * 0.93 for c in base), nz2)
    p = nb.principled(Metallic=1.0)
    nb.link(col, p, 0, 'Base Color')
    nb.link(rr, p, 0, 'Roughness')
    nb.set(p, 'Anisotropic', aniso)
    nb.link(norm, p, 0, 'Tangent')
    bmp = nb.bump(nz, strength=0.03 * brush, distance=0.0001)
    nb.link(bmp, p, 0, 'Normal')
    if finish == "nano_black":
        nb.set(p, 'Coat Weight', 0.15)
        nb.set(p, 'Coat Roughness', 0.3)
    return nb.finish(p)


@cached
def metal(kind):
    cols = {
        "chrome": ((0.75, 0.76, 0.77), 0.04, 0.0),
        "brass": ((0.80, 0.58, 0.30), 0.30, 0.6),
        "brass_polished": ((0.86, 0.66, 0.36), 0.12, 0.2),
        "bronze": ((0.42, 0.28, 0.17), 0.38, 0.5),
        "gunmetal": ((0.14, 0.14, 0.15), 0.32, 0.5),
        "black": ((0.025, 0.025, 0.026), 0.45, 0.0),
        "nickel": ((0.62, 0.58, 0.52), 0.25, 0.6),
        "copper": ((0.86, 0.48, 0.32), 0.28, 0.3),
        "steel": ((0.58, 0.58, 0.58), 0.25, 0.6),
        "white": ((0.80, 0.80, 0.78), 0.35, 0.0),
    }
    base, rough, aniso = cols[kind]
    nb = NB("metal_" + kind)
    if kind in ("black", "white"):
        p = nb.principled(Base_Color=base, Roughness=rough, Metallic=0.0, Coat_Weight=0.2, Coat_Roughness=0.3)
        return nb.finish(p)
    p = nb.principled(Base_Color=base, Roughness=rough, Metallic=1.0)
    nb.set(p, 'Anisotropic', aniso)
    return nb.finish(p)


@cached
def black_glass():
    nb = NB("black_glass")
    p = nb.principled(Base_Color=(0.004, 0.004, 0.005), Roughness=0.03, Specular_IOR_Level=0.5, IOR=1.52)
    return nb.finish(p)


@cached
def glass(tint=(0.95, 0.97, 0.96), rough=0.0):
    """Clear glass that still lets light through for shadows (no caustics are traced, so plain
    refractive glass would leave everything inside or behind it black)."""
    nb = NB("glass")
    p = nb.principled(Base_Color=tint, Roughness=rough, Transmission_Weight=1.0, IOR=1.5)
    tr = nb.n("ShaderNodeBsdfTransparent")
    nb.set(tr, 'Color', tint)
    lp = nb.n("ShaderNodeLightPath")
    ms = nb.n("ShaderNodeMixShader")
    nb.link(lp, ms, 'Is Shadow Ray', 0)
    nb.link(p, ms, 0, 1)
    nb.link(tr, ms, 0, 2)
    return nb.finish(ms)


@cached
def rubber_dark():
    nb = NB("rubber")
    p = nb.principled(Base_Color=(0.015, 0.015, 0.015), Roughness=0.7)
    return nb.finish(p)


@cached
def plastic(col=(0.8, 0.8, 0.8), rough=0.35):
    nb = NB("plastic")
    p = nb.principled(Base_Color=col, Roughness=rough)
    return nb.finish(p)


@cached
def emission(col=(1.0, 0.8, 0.6), strength=10.0):
    nb = NB("emit")
    e = nb.n("ShaderNodeEmission")
    nb.set(e, 'Color', col)
    nb.set(e, 'Strength', strength)
    return nb.finish(e)


# ── stone ──────────────────────────────────────────────────────────────────

@cached
def marble(base=(0.82, 0.80, 0.77), vein=(0.30, 0.29, 0.28), vein2=(0.55, 0.52, 0.48), rough=0.12,
           scale=1.0, vein_width=0.03, warp=4.0, seed=0.0, honed=False, stretch=(1.0, 2.2, 1.0), cloud=0.06,
           density=1.0, halo=0.22, angle=0.35):
    """Veined marble. The veins are the edges of a few large, warped cells (cracks that run across the slab and branch),
    a finer network between them and hairline cracks, each fading in and out, with a soft halo round the main veins
    and a cloudy ground. vein: the main veins' colour; vein2: the fine network's. vein_width ~ 0.01 (hairline) ..
    0.05 (bold). stretch lengthens the cells along y (the run of the slab on a worktop), so veins flow one way."""
    nb = NB("marble")
    tc = nb.n("ShaderNodeTexCoord")
    mp = nb.n("ShaderNodeMapping")
    nb.link(tc, mp, 'Object', 'Vector')
    mp.inputs['Scale'].default_value = tuple(v * scale for v in stretch)
    mp.inputs['Location'].default_value = (seed * 1.37, seed * 0.71, seed * 1.13)
    mp.inputs['Rotation'].default_value = (0.0, 0.0, angle)   # veins on the diagonal, as slabs are cut

    def warped(vec, sc, amount, det=3.0):
        nz = nb.noise(vec, scale=sc, detail=det, rough=0.55)
        sub = nb.n("ShaderNodeVectorMath", operation='SUBTRACT')
        nb.link(nz, sub, 'Color', 0)
        sub.inputs[1].default_value = (0.5, 0.5, 0.5)
        sc_ = nb.n("ShaderNodeVectorMath", operation='SCALE')
        nb.link(sub, sc_, 0, 0)
        sc_.inputs['Scale'].default_value = amount
        add = nb.n("ShaderNodeVectorMath", operation='ADD')
        nb.link(vec, add, 0, 0)
        nb.link(sc_, add, 0, 1)
        return add

    p1 = warped(mp, 0.45, warp * 0.24, 2.0)
    p2 = warped(p1, 1.7, warp * 0.085, 4.0)

    def veins(vec, cells, width, fade_scale, fade, seed_off):
        off = nb.n("ShaderNodeVectorMath", operation='ADD')
        nb.link(vec, off, 0, 0)
        off.inputs[1].default_value = (seed_off, seed_off * 0.6, seed_off * 0.3)
        vo = nb.n("ShaderNodeTexVoronoi")
        vo.feature = 'DISTANCE_TO_EDGE'
        nb.set(vo, 'Scale', cells)
        nb.link(off, vo, 0, 'Vector')
        # width varies along the vein
        wn = nb.noise(off, scale=cells * 0.9, detail=2.0, rough=0.5)
        wmul = nb.n("ShaderNodeMapRange")
        nb.link(wn, wmul, 'Fac', 0)
        wmul.inputs[3].default_value = width * 0.12
        wmul.inputs[4].default_value = width * 1.9
        # 1 on the edge, 0 a width away
        div = nb.math('DIVIDE', vo, wmul, a_out='Distance')
        inv = nb.math('SUBTRACT', 1.0, div, clamp=True)
        sharp = nb.math('POWER', inv, 2.2)
        # some stretches fade out altogether
        fn = nb.noise(off, scale=fade_scale, detail=2.0, rough=0.5)
        fm = nb.n("ShaderNodeMapRange")
        nb.link(fn, fm, 'Fac', 0)
        fm.inputs[1].default_value = 0.5 - fade * 0.25
        fm.inputs[2].default_value = 0.5 + fade * 0.12
        fm.inputs[3].default_value = 0.0
        fm.inputs[4].default_value = 1.0
        return nb.math('MULTIPLY', sharp, fm), wmul, vo

    main, wmain, vo_main = veins(p2, 2.2 * density, vein_width * 1.4, 1.1, 1.7, 0.0)
    fine, _, _ = veins(p2, 6.5 * density, vein_width * 0.5, 2.0, 2.0, 11.3)
    hair, _, _ = veins(p1, 17.0 * density, vein_width * 0.2, 3.5, 2.2, 23.7)
    # a soft halo either side of the main veins
    hdiv = nb.math('DIVIDE', vo_main, nb.math('MULTIPLY', wmain, 7.0), a_out='Distance')
    hinv = nb.math('SUBTRACT', 1.0, hdiv, clamp=True)
    hal = nb.math('MULTIPLY', nb.math('POWER', hinv, 3.0), halo)
    # cloudy ground
    cl = nb.noise(p1, scale=2.2, detail=5.0, rough=0.62)
    clr = nb.ramp(cl, [(0.3, 0.0), (0.72, 1.0)])
    c0 = nb.mix(base, tuple(min(1, c * (1 - cloud)) for c in base), clr)
    c1 = nb.mix(c0, tuple(b + (v - b) * 0.3 for b, v in zip(base, vein)), hal)
    c2 = nb.mix(c1, vein2, nb.math('MULTIPLY', hair, 0.45))
    c3 = nb.mix(c2, vein2, nb.math('MULTIPLY', fine, 0.7))
    c4 = nb.mix(c3, vein, main)
    rr = rough if not honed else max(rough, 0.32)
    # polish is never perfectly even: a faint drift in the gloss
    gn = nb.noise(mp, scale=3.0, detail=3.0, rough=0.6)
    gr = nb.n("ShaderNodeMapRange")
    nb.link(gn, gr, 'Fac', 0)
    gr.inputs[3].default_value = rr * 0.8
    gr.inputs[4].default_value = rr * 1.3
    p = nb.principled(Specular_IOR_Level=0.5)
    nb.link(c4, p, 0, 'Base Color')
    nb.link(gr, p, 0, 'Roughness')
    # veins sit a hair lower on a honed face; fine crystalline grain
    nz = nb.noise(mp, scale=420.0, detail=2.0)
    b1 = nb.bump(nz, strength=0.035 if honed else 0.012, distance=0.0002)
    inv_b = nb.math('SUBTRACT', 1.0, main)
    b2 = nb.bump(inv_b, strength=0.15 if honed else 0.04, distance=0.0002)
    nb.link(b1, b2, 'Normal', 'Normal')
    nb.link(b2, p, 0, 'Normal')
    return nb.finish(p)


@cached
def terrazzo(base=(0.78, 0.76, 0.72), chips=((0.45, 0.42, 0.38), (0.88, 0.86, 0.82), (0.25, 0.24, 0.23), (0.62, 0.48, 0.38)),
             scale=60.0, rough=0.28, density=0.16, contrast=1.0):
    """Terrazzo: sparse irregular chips in a fine-grained cement ground."""
    nb = NB("terrazzo")
    co = nb.coord('Object', 1.0)
    warp = nb.noise(co, scale=scale * 0.8, detail=2.0)
    vm = nb.n("ShaderNodeVectorMath", operation='SCALE')
    nb.link(warp, vm, 'Color', 0)
    vm.inputs['Scale'].default_value = 0.6 / scale
    add = nb.n("ShaderNodeVectorMath", operation='ADD')
    nb.link(co, add, 0, 0)
    nb.link(vm, add, 0, 1)
    vo = nb.voronoi(add, scale=scale, feature='F1')
    mask = nb.ramp(vo, [(0.0, 1.0), (density, 1.0), (density + 0.02, 0.0), (1.0, 0.0)], src_out='Distance')
    mix_chips = [tuple(b + (c - b) * contrast for b, c in zip(base, ch)) for ch in chips]
    cellc = nb.ramp(vo, [(0.0, mix_chips[0]), (0.3, mix_chips[1]), (0.55, mix_chips[2]), (0.8, mix_chips[3]), (1.0, mix_chips[1])], src_out='Color', interp='CONSTANT')
    vo2 = nb.voronoi(add, scale=scale * 3.0, feature='F1')
    mask2 = nb.ramp(vo2, [(0.0, 1.0), (density * 0.7, 1.0), (density * 0.7 + 0.02, 0.0), (1.0, 0.0)], src_out='Distance')
    cellc2 = nb.ramp(vo2, [(0.0, mix_chips[2]), (0.5, mix_chips[0]), (1.0, mix_chips[1])], src_out='Color', interp='CONSTANT')
    nz = nb.noise(co, scale=30.0, detail=3.0)
    b0 = nb.mix(base, tuple(c * 0.96 for c in base), nz)
    c1 = nb.mix(b0, cellc2, mask2)
    c2 = nb.mix(c1, cellc, mask)
    p = nb.principled(Roughness=rough)
    nb.link(c2, p, 0, 'Base Color')
    return nb.finish(p)


@cached
def concrete(base=(0.42, 0.41, 0.39), rough=0.62, scale=1.0, pores=True, tone=0.12):
    """Cast concrete or microcement: a soft cloudy tone, faint trowel sweeps, fine aggregate and (cast) small air
    holes. tone: how strongly the clouding shows."""
    nb = NB("concrete")
    co = nb.coord('Object', scale)
    n1 = nb.noise(co, scale=1.1, detail=4.0, rough=0.55)
    r1 = nb.ramp(n1, [(0.3, 0.0), (0.7, 1.0)], interp='EASE')
    dark = tuple(c * (1 - tone * 0.55) for c in base)
    light = tuple(min(1, c * (1 + tone * 0.45)) for c in base)
    c = nb.mix(dark, light, r1)
    # trowel sweeps: long soft strokes
    tc = nb.n("ShaderNodeTexCoord")
    st = nb.n("ShaderNodeMapping")
    nb.link(tc, st, 'Object', 'Vector')
    st.inputs['Scale'].default_value = (2.5 * scale, 14.0 * scale, 14.0 * scale)
    st.inputs['Rotation'].default_value = (0.0, 0.0, 0.5)
    sw = nb.noise(st, scale=1.0, detail=3.0, rough=0.5)
    swr = nb.ramp(sw, [(0.35, 0.0), (0.65, 1.0)])
    c1 = nb.mix(c, tuple(cc * 0.95 for cc in base), nb.math('MULTIPLY', swr, 0.5), blend='MIX')
    # fine aggregate
    ag = nb.voronoi(co, scale=520.0, feature='F1')
    agm = nb.ramp(ag, [(0.0, 1.0), (0.05, 1.0), (0.09, 0.0), (1.0, 0.0)], src_out='Distance')
    agc = nb.ramp(ag, [(0.0, tuple(cc * 0.8 for cc in base)), (1.0, tuple(min(1, cc * 1.15) for cc in base))], src_out='Color')
    c2 = nb.mix(c1, agc, nb.math('MULTIPLY', agm, 0.6))
    gr = nb.n("ShaderNodeMapRange")
    nb.link(n1, gr, 'Fac', 0)
    gr.inputs[3].default_value = rough * 0.9
    gr.inputs[4].default_value = min(1.0, rough * 1.12)
    sh = nb.principled()
    nb.link(gr, sh, 0, 'Roughness')
    fine = nb.noise(co, scale=700.0, detail=2.0)
    b0 = nb.bump(fine, strength=0.05, distance=0.0003)
    if pores:
        vo = nb.voronoi(co, scale=300.0, feature='F1')
        pm = nb.ramp(vo, [(0.0, 0.0), (0.035, 0.0), (0.06, 1.0), (1.0, 1.0)], src_out='Distance')
        c3 = nb.mix(tuple(cc * 0.45 for cc in base), c2, pm)
        nb.link(c3, sh, 0, 'Base Color')
        b = nb.bump(pm, strength=0.3, distance=0.0006)
        nb.link(b0, b, 'Normal', 'Normal')
        nb.link(b, sh, 0, 'Normal')
    else:
        nb.link(c2, sh, 0, 'Base Color')
        nb.link(b0, sh, 0, 'Normal')
    return nb.finish(sh)

@cached
def travertine(base=(0.66, 0.58, 0.47), rough=0.45):
    """Filled, honed travertine: fine bands laid along the slab, soft clouding, small elongated pits."""
    nb = NB("travertine")
    tc = nb.n("ShaderNodeTexCoord")
    st = nb.n("ShaderNodeMapping")
    nb.link(tc, st, 'Object', 'Vector')
    st.inputs['Scale'].default_value = (0.6, 7.0, 7.0)
    w = nb.noise(st, scale=1.0, detail=2.0, rough=0.5)
    vm = nb.n("ShaderNodeVectorMath", operation='SCALE')
    nb.link(w, vm, 'Color', 0)
    vm.inputs['Scale'].default_value = 0.6
    add = nb.n("ShaderNodeVectorMath", operation='ADD')
    nb.link(st, add, 0, 0)
    nb.link(vm, add, 0, 1)
    wave = nb.n("ShaderNodeTexWave", wave_type='BANDS', bands_direction='Y', wave_profile='SIN')
    nb.set(wave, 'Scale', 1.3)
    nb.set(wave, 'Distortion', 4.0)
    nb.set(wave, 'Detail', 4.0)
    nb.link(add, wave, 0, 'Vector')
    bands = nb.ramp(wave, [(0.0, 0.0), (0.5, 0.5), (1.0, 1.0)], src_out='Fac')
    c = nb.mix(tuple(x * 0.93 for x in base), tuple(min(1, x * 1.04) for x in base), bands)
    cl = nb.noise(st, scale=0.7, detail=4.0, rough=0.6)
    c1 = nb.mix(c, tuple(x * 0.96 for x in base), nb.ramp(cl, [(0.3, 0.0), (0.7, 1.0)]))
    st2 = nb.n("ShaderNodeMapping")
    nb.link(tc, st2, 'Object', 'Vector')
    st2.inputs['Scale'].default_value = (1.0, 5.0, 5.0)
    vo = nb.voronoi(st2, scale=40.0, feature='F1')
    pits = nb.ramp(vo, [(0.0, 1.0), (0.05, 1.0), (0.085, 0.0), (1.0, 0.0)], src_out='Distance')
    c2 = nb.mix(c1, tuple(x * 0.62 for x in base), nb.math('MULTIPLY', pits, 0.8))
    p = nb.principled(Roughness=rough)
    nb.link(c2, p, 0, 'Base Color')
    b = nb.bump(pits, strength=0.2, distance=0.0006)
    nb.link(b, p, 0, 'Normal')
    return nb.finish(p)

@cached
def quartz(base=(0.86, 0.85, 0.83), speck=(0.55, 0.54, 0.52), dens=0.05, rough=0.18, scale=500.0):
    nb = NB("quartz")
    co = nb.coord('Object', 1.0)
    vo = nb.voronoi(co, scale=scale)
    sp = nb.ramp(vo, [(0.0, 1.0), (dens, 1.0), (dens + 0.03, 0.0), (1.0, 0.0)], src_out='Distance')
    nz = nb.noise(co, scale=8.0, detail=4.0)
    c0 = nb.mix(base, tuple(min(1, c * 1.03) for c in base), nz)
    c1 = nb.mix(c0, speck, sp)
    p = nb.principled(Roughness=rough)
    nb.link(c1, p, 0, 'Base Color')
    return nb.finish(p)


@cached
def soapstone(base=(0.07, 0.075, 0.075), vein=(0.22, 0.23, 0.22), rough=0.4):
    return marble(base=base, vein=vein, vein2=tuple(c * 1.4 for c in base), rough=rough, vein_width=0.02, warp=3.0, seed=3.3, honed=True)


# ── wood ───────────────────────────────────────────────────────────────────

WOODS = {
    "oak": ((0.48, 0.33, 0.19), (0.30, 0.19, 0.10)),
    "light_oak": ((0.62, 0.47, 0.31), (0.42, 0.29, 0.17)),
    "white_oak": ((0.66, 0.55, 0.42), (0.47, 0.37, 0.26)),
    "smoked_oak": ((0.20, 0.13, 0.08), (0.10, 0.065, 0.04)),
    "walnut": ((0.22, 0.12, 0.065), (0.11, 0.06, 0.03)),
    "teak": ((0.42, 0.24, 0.11), (0.25, 0.13, 0.06)),
    "ash": ((0.68, 0.58, 0.45), (0.50, 0.40, 0.29)),
    "black_ash": ((0.035, 0.032, 0.03), (0.015, 0.014, 0.013)),
}


@cached
def wood(kind="oak", along='X', rough=0.45, scale=1.0, seed=0.0, coat=0.0, sheen=0.0, contrast=0.6):
    """Plain/quarter-sawn grain along an axis. along: 'X', 'Y' or 'Z' (grain direction)."""
    light, dark = WOODS[kind]
    dark = tuple(l + (d - l) * contrast for l, d in zip(light, dark))
    nb = NB("wood_" + kind)
    tc = nb.n("ShaderNodeTexCoord")
    mp = nb.n("ShaderNodeMapping")
    nb.link(tc, mp, 'Object', 'Vector')
    # stretch along the grain direction
    sx = {'X': (0.06, 1.0, 1.0), 'Y': (1.0, 0.06, 1.0), 'Z': (1.0, 1.0, 0.06)}[along]
    mp.inputs['Scale'].default_value = tuple(v * scale for v in sx)
    mp.inputs['Location'].default_value = (seed, seed * 1.7, seed * 0.3)
    n1 = nb.noise(mp, scale=2.2, detail=3.0, rough=0.5)
    vm = nb.n("ShaderNodeVectorMath", operation='SCALE')
    nb.link(n1, vm, 'Color', 0)
    vm.inputs['Scale'].default_value = 0.6
    add = nb.n("ShaderNodeVectorMath", operation='ADD')
    nb.link(mp, add, 0, 0)
    nb.link(vm, add, 0, 1)
    wave = nb.n("ShaderNodeTexWave", wave_type='RINGS', rings_direction={'X': 'X', 'Y': 'Y', 'Z': 'Z'}[along], wave_profile='SAW')
    nb.set(wave, 'Scale', 14.0)
    nb.set(wave, 'Distortion', 2.2)
    nb.set(wave, 'Detail', 3.0)
    nb.link(add, wave, 0, 'Vector')
    rings = nb.ramp(wave, [(0.0, 0.0), (0.55, 0.25), (0.92, 1.0), (1.0, 0.2)], src_out='Fac')
    # fine pores / fleck
    n2 = nb.noise(mp, scale=90.0, detail=2.0, rough=0.5)
    pores = nb.ramp(n2, [(0.45, 0.0), (0.62, 1.0)])
    c0 = nb.mix(light, dark, rings)
    c1 = nb.mix(c0, tuple(x * 0.75 for x in dark), pores, blend='MIX')
    # board-to-board tone variation
    n3 = nb.noise(mp, scale=0.6, detail=1.0)
    c2 = nb.mix(c1, tuple(x * 1.15 for x in light), n3, blend='OVERLAY')
    p = nb.principled(Roughness=rough)
    nb.link(c1 if kind == "black_ash" else c2, p, 0, 'Base Color')
    b = nb.bump(pores, strength=0.08, distance=0.0004)
    nb.link(b, p, 0, 'Normal')
    if coat:
        nb.set(p, 'Coat Weight', coat)
        nb.set(p, 'Coat Roughness', 0.2)
    if sheen:
        nb.set(p, 'Sheen Weight', sheen)
    return nb.finish(p)


# ── paint, plaster, tile, fabric ───────────────────────────────────────────

@cached
def paint(col, rough=0.5, sheen=0.0, coat=0.0, texture=0.02):
    nb = NB("paint")
    co = nb.coord('Object', 1.0)
    nz = nb.noise(co, scale=60.0, detail=3.0)
    p = nb.principled(Base_Color=col, Roughness=rough)
    if texture:
        b = nb.bump(nz, strength=texture, distance=0.0005)
        nb.link(b, p, 0, 'Normal')
    if coat:
        nb.set(p, 'Coat Weight', coat)
        nb.set(p, 'Coat Roughness', 0.15)
    if sheen:
        nb.set(p, 'Sheen Weight', sheen)
    return nb.finish(p)


@cached
def plaster(col=(0.70, 0.66, 0.60), var=0.08, rough=0.85, scale=1.0, bump=0.12):
    """Limewash or polished plaster: a soft cloudiness, overlapping trowel or brush sweeps, a fine sandy tooth."""
    nb = NB("plaster")
    co = nb.coord('Object', scale)
    n1 = nb.noise(co, scale=1.4, detail=5.0, rough=0.6)
    r1 = nb.ramp(n1, [(0.28, 0.0), (0.72, 1.0)], interp='EASE')
    c = nb.mix(tuple(x * (1 - var) for x in col), tuple(min(1, x * (1 + var * 0.8)) for x in col), r1)
    tc = nb.n("ShaderNodeTexCoord")
    st = nb.n("ShaderNodeMapping")
    nb.link(tc, st, 'Object', 'Vector')
    st.inputs['Scale'].default_value = (3.0 * scale, 3.0 * scale, 3.0 * scale)
    sw = nb.noise(st, scale=2.5, detail=6.0, rough=0.65, distortion=1.2)
    swr = nb.ramp(sw, [(0.4, 0.0), (0.6, 1.0)])
    c1 = nb.mix(c, tuple(x * (1 - var * 0.6) for x in col), nb.math('MULTIPLY', swr, 0.35))
    p = nb.principled(Roughness=rough)
    nb.link(c1, p, 0, 'Base Color')
    n2 = nb.noise(co, scale=14.0, detail=4.0, rough=0.55)
    b = nb.bump(n2, strength=bump, distance=0.002)
    fine = nb.noise(co, scale=500.0, detail=2.0)
    b2 = nb.bump(fine, strength=0.06, distance=0.0003)
    nb.link(b2, b, 'Normal', 'Normal')
    nb.link(b, p, 0, 'Normal')
    return nb.finish(p)

@cached
def tile(col=(0.80, 0.80, 0.78), grout=(0.55, 0.53, 0.50), w=0.15, h=0.075, gap=0.002, rough=0.08, var=0.08,
         zellige=False, offset=0.5, along='XZ', bevel=0.004, col2=None):
    """Glazed tiles in a running bond. along: the plane they lie in ('XZ' wall facing -y, 'YZ', 'XY')."""
    nb = NB("tile")
    tc = nb.n("ShaderNodeTexCoord")
    sep = nb.n("ShaderNodeSeparateXYZ")
    nb.link(tc, sep, 'Object', 0)
    comb = nb.n("ShaderNodeCombineXYZ")
    a, b = along[0], along[1]
    nb.link(sep, comb, a, 'X')
    nb.link(sep, comb, b, 'Y')
    br = nb.n("ShaderNodeTexBrick")
    br.offset = offset
    br.squash = 1.0
    nb.set(br, 'Scale', 1.0)
    nb.set(br, 'Mortar Size', gap)
    nb.set(br, 'Mortar Smooth', 0.3)
    nb.set(br, 'Brick Width', w)
    nb.set(br, 'Row Height', h)
    nb.set(br, 'Bias', 0.0)
    nb.set(br, 'Color1', (1, 1, 1))
    nb.set(br, 'Color2', (0, 0, 0))
    nb.set(br, 'Mortar', (0, 0, 0))
    nb.link(comb, br, 0, 'Vector')
    # per-tile random value from the brick's own colour variation
    br2 = nb.n("ShaderNodeTexBrick")
    br2.offset = offset
    nb.set(br2, 'Scale', 1.0)
    nb.set(br2, 'Mortar Size', 0.0)
    nb.set(br2, 'Brick Width', w)
    nb.set(br2, 'Row Height', h)
    nb.set(br2, 'Bias', 0.0)
    nb.set(br2, 'Color1', (0, 0, 0))
    nb.set(br2, 'Color2', (1, 1, 1))
    nb.link(comb, br2, 0, 'Vector')
    tone = nb.ramp(br2, [(0.0, tuple(x * (1 - var) for x in col)), (1.0, tuple(min(1, x * (1 + var)) for x in col) if col2 is None else col2)], src_out='Color')
    if zellige:
        # hand-glazed: the glaze pools and thins across each tile
        gz = nb.noise(comb, scale=28.0, detail=3.0, rough=0.55)
        gzr = nb.ramp(gz, [(0.3, 0.0), (0.7, 1.0)])
        tone = nb.mix(tone, tuple(x * (1 - var * 1.4) for x in col), nb.math('MULTIPLY', gzr, 0.6))
    c = nb.mix(tone, grout, br, fac_out='Fac')
    p = nb.principled(Roughness=rough)
    nb.link(c, p, 0, 'Base Color')
    # bevelled tile edges via the mortar mask, plus zellige undulation
    hb = nb.math('SUBTRACT', 1.0, br, b_out='Fac')
    if zellige:
        nz = nb.noise(comb, scale=22.0, detail=3.0, rough=0.5)
        hz = nb.math('MULTIPLY', nz, 0.35)
        hsum = nb.math('ADD', hb, hz)
        bm = nb.bump(hsum, strength=0.35, distance=0.002)
    else:
        bm = nb.bump(hb, strength=0.5, distance=0.0015)
    nb.link(bm, p, 0, 'Normal')
    # grout is rough
    rmix = nb.n("ShaderNodeMapRange")
    nb.link(br, rmix, 'Fac', 0)
    rmix.inputs[3].default_value = rough
    rmix.inputs[4].default_value = 0.9
    nb.link(rmix, p, 0, 'Roughness')
    return nb.finish(p)


@cached
def linen(col=(0.72, 0.68, 0.60), rough=0.9):
    nb = NB("linen")
    co = nb.coord('Object', 1.0)
    st = nb.n("ShaderNodeMapping")
    tc = nb.n("ShaderNodeTexCoord")
    nb.link(tc, st, 'Object', 'Vector')
    st.inputs['Scale'].default_value = (900.0, 30.0, 30.0)
    n1 = nb.noise(st, scale=1.0, detail=2.0)
    st2 = nb.n("ShaderNodeMapping")
    nb.link(tc, st2, 'Object', 'Vector')
    st2.inputs['Scale'].default_value = (30.0, 900.0, 30.0)
    n2 = nb.noise(st2, scale=1.0, detail=2.0)
    h = nb.math('ADD', n1, n2)
    c = nb.mix(col, tuple(x * 0.85 for x in col), n1)
    p = nb.principled(Roughness=rough)
    nb.set(p, 'Sheen Weight', 0.4)
    nb.link(c, p, 0, 'Base Color')
    b = nb.bump(h, strength=0.15, distance=0.0005)
    nb.link(b, p, 0, 'Normal')
    return nb.finish(p)


@cached
def ceramic(col=(0.85, 0.84, 0.80), rough=0.25, speck=0.0, matte=False):
    nb = NB("ceramic")
    co = nb.coord('Object', 1.0)
    p = nb.principled(Base_Color=col, Roughness=0.55 if matte else rough)
    if speck:
        vo = nb.voronoi(co, scale=300.0)
        sp = nb.ramp(vo, [(0.0, 1.0), (speck, 1.0), (speck + 0.02, 0.0), (1.0, 0.0)], src_out='Distance')
        c = nb.mix(col, tuple(x * 0.35 for x in col), sp)
        nb.link(c, p, 0, 'Base Color')
    if not matte:
        nb.set(p, 'Coat Weight', 0.3)
        nb.set(p, 'Coat Roughness', 0.05)
    return nb.finish(p)


@cached
def leaf(col=(0.06, 0.12, 0.04), rough=0.45):
    nb = NB("leaf")
    co = nb.coord('Object', 1.0)
    nz = nb.noise(co, scale=40.0, detail=2.0)
    c = nb.mix(col, tuple(x * 1.4 for x in col), nz)
    p = nb.principled(Roughness=rough)
    nb.link(c, p, 0, 'Base Color')
    nb.set(p, 'Subsurface Weight', 0.0)
    tr = nb.n("ShaderNodeBsdfTranslucent")
    nb.set(tr, 'Color', tuple(x * 1.5 for x in col))
    ms = nb.n("ShaderNodeMixShader")
    ms.inputs[0].default_value = 0.25
    nb.link(p, ms, 0, 1)
    nb.link(tr, ms, 0, 2)
    return nb.finish(ms)


@cached
def fruit(col=(0.75, 0.55, 0.05), rough=0.35, bump=0.3, scale=300.0):
    nb = NB("fruit")
    co = nb.coord('Object', 1.0)
    vo = nb.voronoi(co, scale=scale)
    p = nb.principled(Base_Color=col, Roughness=rough)
    nb.set(p, 'Subsurface Weight', 0.2)
    try:
        nb.set(p, 'Subsurface Radius', (0.01, 0.006, 0.003))
        nb.set(p, 'Subsurface Scale', 0.01)
    except KeyError:
        pass
    b = nb.bump(vo, strength=bump, distance=0.0005, h_out='Distance')
    nb.link(b, p, 0, 'Normal')
    return nb.finish(p)


@cached
def liquid_oil():
    nb = NB("oil")
    p = nb.principled(Base_Color=(0.55, 0.42, 0.06), Roughness=0.0, Transmission_Weight=1.0, IOR=1.47)
    return nb.finish(p)


@cached
def paper(col=(0.85, 0.82, 0.76)):
    nb = NB("paper")
    p = nb.principled(Base_Color=col, Roughness=0.9)
    return nb.finish(p)


@cached
def soil(col=(0.06, 0.045, 0.035)):
    nb = NB("soil")
    co = nb.coord('Object', 1.0)
    nz = nb.noise(co, scale=200.0, detail=4.0)
    b = nb.bump(nz, strength=0.6, distance=0.002)
    p = nb.principled(Base_Color=col, Roughness=0.95)
    nb.link(b, p, 0, 'Normal')
    return nb.finish(p)


@cached
def spun_steel(base=(0.62, 0.62, 0.62), rough=0.16):
    """Steel spun on a lathe: brushed in circles round the object's own origin."""
    nb = NB("spun_steel")
    tg = nb.n("ShaderNodeTangent")
    tg.direction_type = 'RADIAL'
    tg.axis = 'Z'
    co = nb.coord('Object', 1.0)
    wave = nb.n("ShaderNodeTexWave", wave_type='RINGS', wave_profile='SIN')
    nb.set(wave, 'Scale', 260.0)
    nb.set(wave, 'Distortion', 0.0)
    nb.link(co, wave, 0, 'Vector')
    p = nb.principled(Base_Color=base, Metallic=1.0, Roughness=rough)
    nb.set(p, 'Anisotropic', 0.85)
    nb.link(tg, p, 0, 'Tangent')
    b = nb.bump(wave, strength=0.04, distance=0.0001, h_out='Fac')
    nb.link(b, p, 0, 'Normal')
    return nb.finish(p)


@cached
def perforated(base=(0.30, 0.30, 0.30), hole=(0.01, 0.01, 0.01), scale=260.0):
    """Steel with a regular field of small holes (strainer baskets)."""
    nb = NB("perforated")
    co = nb.coord('Object', 1.0)
    vo = nb.voronoi(co, scale=scale, feature='F1', rand=0.0)
    m = nb.ramp(vo, [(0.0, 1.0), (0.28, 1.0), (0.32, 0.0), (1.0, 0.0)], src_out='Distance')
    c = nb.mix(base, hole, m)
    p = nb.principled(Metallic=0.8, Roughness=0.35)
    nb.link(c, p, 0, 'Base Color')
    return nb.finish(p)


@cached
def lcd():
    nb = NB("lcd")
    p = nb.principled(Base_Color=(0.01, 0.012, 0.014), Roughness=0.08)
    nb.set(p, 'Emission Color', (0.35, 0.55, 0.9))
    nb.set(p, 'Emission Strength', 0.6)
    return nb.finish(p)

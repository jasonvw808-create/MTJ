"""The 25 stainless steel sinks' measurements, as the shop's site took them from the supplied
product photographs and the Price List 2024 (index.html: STEEL_3D, STEEL_EST). Millimetres;
x across, z front to back with the back negative, from the middle of the sink.

VERIFIED (price list): overall size, height, sheet thickness, finish, edge.
MEASURED (photographs): bowls, radii, rims, drainboards, drains, deck fittings.
TYPICAL (not visible from above): skirt, channel depth, deck drop, lip and floor radii, fall,
ledges, fitting heights."""
import math

P = dict(skirt=10, edgeR=2.5, channelDepth=5, deckDrop=3, lip=6, floorR=30, fall=3, run=38)
H = dict(edgeR=0.8, lip=1.5, floorR=8, fall=6, ledge=dict(drop=32, w=15), base=dict(dispenser=8, knob=10, knife=4))


def pbowl(rect, r, rBottom, depth, drain, run=None, shape=None):
    d = dict(type="hole", lip=4)
    d.update(drain)
    b = dict(shape=dict(rect=rect, r=r), depth=depth, lip=P["lip"], run=run or P["run"], rBottom=rBottom,
             floorR=P["floorR"], fall=P["fall"], floorStyle="dish", drain=d)
    if shape:
        b["shape"] = shape
    return b


def hbowl(rect, r, depth, drain, ledges=True, overflow=None, outlet=None):
    return dict(shape=dict(rect=rect, r=r), depth=depth, lip=H["lip"], floorR=H["floorR"], fall=H["fall"], floorStyle="planes",
                ledges=dict(back=H["ledge"], front=H["ledge"]) if ledges else None, drain=drain, overflow=overflow, outlet=outlet)


def pressed(model, finish, size, height, sheet, rim, bowls, features=()):
    rr = dict(r=12)
    rr.update(rim)
    return dict(model=model, family="pressed", finish=finish, size=size, height=height, sheet=sheet, cornerR=10, rim=rr,
                bowls=bowls, features=list(features))


def handmade(model, finish, size, height, sheet, bowls, fittings=(), cornerR=12, **extra):
    d = dict(model=model, family="handmade", finish=finish, size=size, height=height, sheet=sheet, plate=3, cornerR=cornerR,
             bowls=bowls, fittings=list(fittings))
    d.update(extra)
    return d


def pd(h, t):
    return round((h - P["deckDrop"] - P["fall"] - t) * 10) / 10


def hd(h, t):
    return round((h - H["fall"] - t) * 10) / 10


def pad(x0, x1, z0, z1, r=5, h=1.5, e=3):
    return dict(shape=dict(rect=[x0, x1, z0, z1], r=r), h=h, e=e)


def groove(x0, x1, zc, w, g):
    return dict(shape=dict(stadium=[x0, x1, zc, w]), h=-g, e=w / 2 - 0.4)


def knife(x0, x1, z0, z1):
    return dict(kind="knife", x0=x0, x1=x1, z0=z0, z1=z1, h=H["base"]["knife"])


def dispenser(x, z, d):
    return dict(kind="dispenser", x=x, z=z, d=d, h=H["base"]["dispenser"])


def knob(x, z, d):
    return dict(kind="knob", x=x, z=z, d=d, h=H["base"]["knob"])


def fan():
    """LPS 9643 A's drainboard: thirteen blades fanning out from the bowl."""
    out, tipX = [], -18
    for s in (-1, 1):
        for k in range(0, 7):
            if s > 0 and k == 0:
                continue
            zt = s * 23.3 * k
            bulge = 0
            if k <= 2:
                p2, w2 = [-428, s * 55 * k], 15
            else:
                p2, w2, bulge = [[-430, -330, -240, -131][k - 3], s * 155], 2.5, 5.5
            p1 = [tipX + (p2[0] - tipX) * 0.55, zt]
            out.append(dict(shape=dict(blade=dict(p0=[tipX, zt], p1=p1, p2=p2, w0=4.2, w2=w2, k=1.4, bulge=bulge)), h=1.4, e=2.2))
    return out


STEEL = {
    # ── PRESSED ──
    "LPS 5040": pressed("LPS 5040", "mat_polished", [500, 400], 160, 0.4, dict(band=13, channel=9),
                        [pbowl([-198, 198, -163, 173], 75, 42, pd(160, 0.4), dict(x=0, z=0, d=76))]),
    "LPS 7540 A": pressed("LPS 7540 A", "mat_polished", [750, 400], 145, 0.33, dict(band=15, channel=9),
                          [pbowl([-35, 340, -164, 160], 60, 36, pd(145, 0.33), dict(x=147, z=-2, d=77))],
                          [pad(-331, -49, z0, z1, [5, 12, 5, 5], 1.5, 3) for (z0, z1) in [(-157, -112), (-96, -71), (-56, -31), (-16, 9), (25, 50), (65, 90), (103, 147)]]),
    "LPS 8643 A": pressed("LPS 8643 A", "mat_polished", [860, 430], 145, 0.4, dict(band=18, channel=9),
                          [pbowl([-8, 396, -172, 175], 65, 38, pd(145, 0.4), dict(x=186, z=-1, d=86))],
                          [groove(-386, -24, -154.7 + 16.47 * k, 6.5, 2.2) for k in range(20)]),
    "LPS 9643 A": pressed("LPS 9643 A", "mat_polished", [960, 430], 145, 0.33, dict(band=22, channel=10),
                          [pbowl([-4, 421, -174, 170], 65, 38, pd(145, 0.33), dict(x=198, z=-1, d=85))], fan()),
    "LPS 10050 A": pressed("LPS 10050 A", "mat_polished", [1000, 500], 160, 0.5, dict(band=21, channel=9),
                           [pbowl([-18, 417, -197, 197], 65, 40, pd(160, 0.5), dict(x=93, z=10, d=79, type="cap"))],
                           [dict(shape=dict(poly=[[-445, -190], [-172, -190], [-116, -158], [-36, -158], [-36, 150], [-116, 150], [-176, 190], [-445, 190]], r=10), h=-3, e=4,
                                 children=[dict(shape=dict(rect=[-358, -48, -134, 126], r=8), h=1.5, e=3,
                                                children=[dict(shape=dict(stadium=[-342, -60, z - 3, 6]), h=1.2, e=2.2) for z in (-90, -45, 0, 45, 90)])]),
                            dict(shape=dict(poly=[[-165, -216], [32, -216], [-38, -166], [-104, -166]], r=6), h=-2.5, e=3),
                            dict(shape=dict(poly=[[-165, 216], [32, 216], [-38, 166], [-104, 166]], r=6), h=-2.5, e=3)]),
    "WL 03": pressed("WL 03", "mat_polished", [600, 450], 210, 0.6, dict(band=18, channel=10),
                     [pbowl([-234, 236, -183, 183], 80, 45, pd(210, 0.6), dict(x=0, z=0, d=84))]),
    "WL 05 A": pressed("WL 05 A", "electroplate", [800, 500], 210, 0.7, dict(band=16, channel=10),
                       [pbowl([0, 0, 0, 0], 0, 0, pd(210, 0.7), dict(x=-173, z=0, d=93), run=30,
                              shape=dict(cpoly=[[-350, -215], [-112, -215], [-15, -140], [-15, 147], [-104, 214], [-350, 214]], r=[45, 28, 18, 18, 28, 45], rBottom=[32, 20, 12, 12, 20, 32])),
                        pbowl([0, 0, 0, 0], 0, 0, pd(210, 0.7), dict(x=168, z=0, d=93), run=30,
                              shape=dict(cpoly=[[11, -137], [104, -214], [347, -214], [347, 214], [112, 214], [11, 147]], r=[18, 28, 45, 45, 28, 18], rBottom=[12, 20, 32, 32, 20, 12]))],
                       [dict(shape=dict(poly=[[-86, -221], [80, -221], [15, -182], [-20, -182]], r=5), h=-1.5, e=2.5),
                        dict(shape=dict(poly=[[-88, 221], [88, 221], [15, 177], [-20, 177]], r=5), h=-1.5, e=2.5)]),
    "WL 07": pressed("WL 07", "electroplate", [850, 500], 210, 0.7, dict(band=18, channel=9),
                     [pbowl([-358, 0, -205, 203], 55, 35, pd(210, 0.7), dict(x=-170, z=-8, d=81), run=30)],
                     [dict(shape=dict(poly=[[-4, -219], [394, -219], [394, 219], [-2, 219], [14, 214], [30, 201], [40, 186], [43, 173], [43, -172], [40, -186], [28, -201], [12, -214]],
                                      r=[4, 8, 8, 4, 0, 0, 0, 6, 6, 0, 0, 0]), h=-2, e=4,
                           children=[dict(shape=dict(stadium=[52, 324, z, 11]), h=3, e=5.1) for z in (-164, -50, 54, 169)] +
                                    [dict(shape=dict(rect=[333, 388, -213, 213], r=6), h=-2, e=4)])]),
    "WL 11": pressed("WL 11", "electroplate", [930, 450], 210, 0.6, dict(band=13, channel=7),
                     [pbowl([-432, -93, -183, 178], 35, 25, pd(210, 0.6), dict(x=-254, z=-3, d=96), run=25),
                      pbowl([136, 408, -125, 164], 30, 22, pd(210, 0.6), dict(x=257, z=18, d=92), run=25)],
                     [dict(shape=dict(rect=[-65, 112, -130, 176], r=6), h=4, e=4,
                           bowls=[pbowl([-56, 102, -121, 66], 48, 30, 100, dict(x=23, z=-28, d=46, type="popup"), run=18)],
                           children=[dict(shape=dict(rect=[x0, x1, z0, z1], r=3), h=-3, e=7) for (x0, x1) in [(-58, -28), (-17, 13), (24, 54), (65, 95)] for (z0, z1) in [(90, 119), (132, 161)]]),
                      dict(shape=dict(rect=[-62, 441, -202, -150], r=[10, 18, 4, 4]), h=3, e=4)]),
    "WL 12": pressed("WL 12", "electroplate", [1000, 460], 210, 0.6, dict(band=28, channel=10),
                     [pbowl([-440, -42, -173, 172], 45, 30, pd(210, 0.6), dict(x=-232, z=-1, d=93), run=30)],
                     [dict(shape=dict(poly=[[18, -170], [121, -170], [121, -99], [-26, -99], [-26, -125]], r=3), h=2, e=4),
                      pad(-26, 121, -83, -10, 3, 2, 4), pad(-26, 121, 5, 78, 3, 2, 4),
                      dict(shape=dict(poly=[[-26, 95], [121, 95], [121, 168], [18, 168], [-26, 124]], r=3), h=2, e=4)] +
                     [pad(x0, x1, z0, z1, 3, 2, 4) for (x0, x1) in [(136, 274), (290, 427)] for (z0, z1) in [(-170, -99), (-83, -10), (5, 78), (95, 168)]]),
    "WL 18": pressed("WL 18", "electroplate", [1200, 500], 180, 0.6, dict(band=20, channel=10),
                     [pbowl([-546, -194, -194, 194], 80, 45, pd(180, 0.6), dict(x=-359, z=1, d=92), run=30),
                      pbowl([-166, 185, -194, 194], 80, 45, pd(180, 0.6), dict(x=6, z=1, d=92), run=30)],
                     [dict(shape=dict(poly=[[-236, -213], [-66, -213], [-108, -199], [-192, -199]], r=4), h=-1.5, e=2.5),
                      dict(shape=dict(poly=[[-236, 213], [-66, 213], [-108, 199], [-192, 199]], r=4), h=-1.5, e=2.5)] +
                     [pad(x0, x1, z0, z1, 6, 2, 4) for (x0, x1) in [(227, 375), (394, 538)] for (z0, z1) in [(-208, -120), (-100, -14), (7, 95), (115, 201)]]),

    # ── HAND MADE ──
    "W 5050 TSB": handmade("W 5050 TSB", "nano_black", [500, 500], 230, 0.9,
                           [hbowl([-223, 224, -175, 223], 10, hd(230, 0.9), dict(x=-5, z=-48, d=83, type="basket"), overflow=[80, 95, 110, 125])],
                           [knife(-209, -38, -235, -187), dispenser(8, -214, 47), knob(195, -222, 47)]),
    "W 6045 TSS": handmade("W 6045 TSS", "satin", [600, 450], 230, 0.7,
                           [hbowl([-273, 273, -149, 198], 10, hd(230, 0.7), dict(x=0, z=24, d=98, type="basket"), overflow=[108, 120, 132, 144])],
                           [knife(-259, -85, -210, -162), dispenser(10, -189, 48), knob(245, -193, 48)]),
    "W 6045 TSB": handmade("W 6045 TSB", "nano_black", [600, 450], 230, 0.7,
                           [hbowl([-273, 273, -149, 198], 10, hd(230, 0.7), dict(x=0, z=24, d=98, type="basket"), overflow=[108, 120, 132, 144])],
                           [knife(-259, -85, -210, -162), dispenser(5, -188, 46), knob(238, -193, 48)]),
    "W 7546 TSB": handmade("W 7546 TSB", "nano_black", [750, 460], 230, 0.7,
                           [hbowl([-350, 350, -155, 205], 10, hd(230, 0.7), dict(x=70, z=20, d=85, type="basket"), outlet=[42, 231])],
                           [dict(kind="rinser", x=-300, z=-190, d=84, h=9),
                            dict(kind="block", x0=24, x1=259, z0=-224, z1=-157, h=10, part="black"),
                            dict(kind="round", x=224, z=-190, d=52, h=12, y=10, part="yellow"),
                            dict(kind="round", x=321, z=-194, d=42, h=6, part="white"),
                            dict(kind="faucet", x=95, z=-190, y=10, h=380, reach=200)]),
    "W 7546 TSBN": handmade("W 7546 TSBN", "nano_black", [750, 460], 230, 0.7,
                            [hbowl([-360, 360, -150, 213], 10, hd(230, 0.7), dict(x=70, z=25, d=85, type="basket"), outlet=[105, 294])],
                            [dict(kind="block", x0=-372, x1=372, z0=-228, z1=-152, h=12, part="black"),
                             dict(kind="block", x0=-360, x1=-270, z0=-224, z1=-160, h=2, y=12, part="steel"),
                             dict(kind="round", x=-247, z=-197, d=25, h=5, y=12, part="white"),
                             dict(kind="round", x=-162, z=-191, d=45, h=10, y=12, part="white"),
                             dict(kind="inlay", x0=125, x1=197, z0=-197, z1=-170, y=12),
                             dict(kind="round", x=259, z=-191, d=45, h=10, y=12, part="white"),
                             dict(kind="faucet", x=70, z=-178, y=12, h=380, reach=205)]),
    "W 7646 USS": handmade("W 7646 USS", "satin", [760, 460], 230, 0.7,
                           [hbowl([-354, 353, -204, 205], 15, hd(230, 0.7), dict(x=1, z=0, d=82, type="popup"), overflow=[-21, -7, 7, 21])], [], cornerR=20),
    "W 7646 USB": handmade("W 7646 USB", "nano_black", [760, 460], 230, 0.7,
                           [hbowl([-354, 353, -203, 204], 15, hd(230, 0.7), dict(x=0, z=0, d=99, type="basket"), overflow=[-21, -7, 7, 21])], [], cornerR=20),
    "W 7845 UDS": handmade("W 7845 UDS", "satin", [780, 450], 230, 0.7,
                           [hbowl([-365, 62, -202, 202], 15, hd(230, 0.7), dict(x=-120, z=-5, d=77, type="popup")),
                            hbowl([86, 370, -202, 202], 15, hd(230, 0.7), dict(x=202, z=-5, d=77, type="popup"))], [], cornerR=20),
    "W 7845 UDB": handmade("W 7845 UDB", "nano_black", [780, 450], 230, 0.7,
                           [hbowl([-365, 62, -202, 202], 15, hd(230, 0.7), dict(x=-130, z=-12, d=78, type="popup")),
                            hbowl([86, 371, -202, 202], 15, hd(230, 0.7), dict(x=198, z=-12, d=78, type="popup"))], [], cornerR=20),
    "W 8050 TSS": handmade("W 8050 TSS", "satin", [800, 500], 230, 0.9,
                           [hbowl([-376, 376, -178, 224], 12, hd(230, 0.9), dict(x=0, z=-53, d=86, type="basket"), overflow=[164, 178, 192, 206])],
                           [knife(-344, -172, -236, -187), dispenser(0, -215, 46), knob(339, -219, 46)]),
    "W 8050 TSB": handmade("W 8050 TSB", "nano_black", [800, 500], 230, 0.9,
                           [hbowl([-376, 376, -178, 224], 12, hd(230, 0.9), dict(x=0, z=-53, d=86, type="basket"), overflow=[164, 178, 192, 206])],
                           [knife(-344, -172, -236, -187), dispenser(0, -215, 46), knob(339, -219, 46)]),
    "W 8245 TDB": handmade("W 8245 TDB", "nano_black", [820, 450], 230, 0.9,
                           [hbowl([-384, 53, -198, 198], 12, hd(230, 0.9), dict(x=-154, z=-98, d=95, type="basket")),
                            hbowl([88, 383, -151, 198], 12, hd(230, 0.9), dict(x=222, z=-48, d=100, type="popup"))],
                           [dispenser(118, -185, 49), knife(149, 328, -214, -163), knob(367, -188, 49)]),
    "W 8550 TDG": handmade("W 8550 TDG", "satin", [850, 500], 230, 0.9, [],
                           [dict(kind="pane", x0=-409, x1=0, z0=-170, z1=211, y=-7, h=5.5),
                            dict(kind="pane", x0=6, x1=414, z0=-170, z1=211, y=-7, h=5.5),
                            dispenser(-2, -215, 48), knob(350, -219, 50)],
                           cornerR=8,
                           recesses=[dict(rect=[-410, 1, -171, 212], r=6, depth=7, bowl=dict(rect=[-404, -5, -165, 206], r=8, drain=dict(x=-205, z=20, d=85))),
                                     dict(rect=[5, 415, -171, 212], r=6, depth=7, bowl=dict(rect=[11, 409, -165, 206], r=8, drain=dict(x=210, z=20, d=85)))]),
    "W 10050 TSG": handmade("W 10050 TSG", "satin", [1000, 500], 230, 0.9, [],
                            [dict(kind="tapring", x=109, z=-193, d=49, h=1.5)],
                            cornerR=10, top="glass", glass_plate=6,
                            opening=dict(rect=[-431, 51, -200, 198], r=18, depth=6,
                                         bowl=hbowl([-419, 39, -188, 186], 12, hd(230, 0.9) - 6, dict(x=-172, z=-75, d=84, type="basket"))),
                            grooves=[dict(z=z, x0=60, x1=445, w0=1.8, w2=0.5) for z in (-144, -48, 47, 142)]),
}

ORDER = ["LPS 5040", "LPS 7540 A", "LPS 8643 A", "LPS 9643 A", "LPS 10050 A", "WL 03", "WL 05 A", "WL 07", "WL 11", "WL 12", "WL 18",
         "W 5050 TSB", "W 6045 TSS", "W 6045 TSB", "W 7546 TSB", "W 7546 TSBN", "W 7646 USS", "W 7646 USB", "W 7845 UDS", "W 7845 UDB",
         "W 8050 TSS", "W 8050 TSB", "W 8245 TDB", "W 8550 TDG", "W 10050 TSG"]

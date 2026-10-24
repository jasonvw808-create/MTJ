"""The granite sinks' measurements (millimetres), shared by the 3D builder and the drawings."""

EST = dict(depth=200, flange=12, wall=9, floorR=10, lip=3)

GRANITE = {
    "GDU 8145": dict(size=(810, 450), bowls=2, cornerR=3, rim=(22, 22, 22, 22), divider=22.5, bowlR=11, runX=20, runZ=26,
                     drains=[dict(x=None, z=-96, d=95, ring=100)], mount="under"),
    "GSU 6045": dict(size=(600, 450), bowls=1, cornerR=8.5, rim=(21.1, 21.6, 22.0, 23.6), bowlR=9.6, runX=20, runZ=28,
                     drains=[dict(x=0, z=-28, d=94.5, ring=100)], mount="under"),
    "GSU 7545": dict(size=(750, 450), bowls=1, cornerR=5, rim=(23.3, 23.4, 20.1, 23.1), bowlR=12.5, runX=20, runZ=28.4,
                     drains=[dict(x=0, z=-61.6, d=96, ring=100.4)], mount="under"),
    "GSU 8045": dict(size=(800, 450), bowls=1, cornerR=5, rim=(24.8, 25.0, 20.1, 23.1), bowlR=12.9, runX=20, runZ=28,
                     drains=[dict(x=0, z=-61.8, d=93.8, ring=101.7)], mount="under"),
    "GST 6045": dict(size=(600, 450), bowls=1, cornerR=(13, 8), rim=(29.8, 30.3, 59.8, 27.3), bowlR=10.3, runX=20, runZ=19.2,
                     drains=[dict(x=0, z=-31, d=83, ring=87.5)], holes=[dict(x=0, z=-194.4, d=31)], edgeR=4, mount="top"),
    "GST 7546": dict(size=(750, 460), bowls=1, cornerR=(7, 4), rim=(25, 25, 74.4, 24.2), bowlR=9.5, runX=20, runZ=15.5,
                     drains=[dict(x=192, z=37, d=95, ring=101)], floorStep=dict(x=192, z=37, r=72, h=2),
                     ledge=dict(w=11, drop=15), outlet=dict(x0=116, x1=300), edgeR=3, mount="top"),
}


"""Generate laser (xTool P2) and 3D-print (Bambu X1C) files for the
non-foam parts of the Airspeed A.S.31 (Jivaro Models plan, 71 cm span).

Run:  python3 make_parts.py      (needs: ezdxf, manifold3d, trimesh, numpy)

Firewall geometry was measured from airspeed_plan.pdf (drawn 1:1):
  outer diameter 35.0 mm, centre hole 11.5 mm,
  3 x 3.6 mm screw holes and 3 x 6.9 mm cooling holes, alternating every
  60 deg on an 11.5 mm radius (23 mm bolt circle). Screw holes at the top
  left, top right and bottom (viewed from the front).
"""
import math
from pathlib import Path

import ezdxf
import manifold3d as m3d
import numpy as np
import trimesh

OUT = Path(__file__).parent
(OUT / "laser").mkdir(exist_ok=True)
(OUT / "print").mkdir(exist_ok=True)

# ---- firewall parameters (mm) -------------------------------------------
FW_D = 35.0          # outer diameter
FW_T = 3.0           # thickness (plan: 3 mm plywood)
CENTER_D = 11.5      # shaft / bearing boss clearance
BOLT_R = 11.5        # bolt-circle radius (23 mm PCD)
SCREW_D = 3.6        # M3 clearance
COOL_D = 6.9         # cooling holes
# angles measured clockwise from 12 o'clock, front view
SCREW_ANG = [300, 60, 180]
COOL_ANG = [0, 120, 240]

# universal printed mount: 4 radial slots covering ~16-28 mm bolt patterns
SLOT_W = 3.3
SLOT_R0, SLOT_R1 = 8.0, 14.0
SLOT_ANG = [45, 135, 225, 315]


def polar(r, ang_cw_from_top):
    a = math.radians(ang_cw_from_top)
    return r * math.sin(a), r * math.cos(a)  # x right, y up


def plan_holes():
    holes = [(0.0, 0.0, CENTER_D)]
    holes += [(*polar(BOLT_R, a), SCREW_D) for a in SCREW_ANG]
    holes += [(*polar(BOLT_R, a), COOL_D) for a in COOL_ANG]
    return holes


# ---- laser: SVG + DXF ----------------------------------------------------
def laser_files(copies=4, gap=5.0):
    pitch = FW_D + gap
    cols = 2
    rows = math.ceil(copies / cols)
    W = cols * pitch + gap
    H = rows * pitch + gap
    svg = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}mm" height="{H}mm" '
           f'viewBox="0 0 {W} {H}">',
           '<g fill="none" stroke="#ff0000" stroke-width="0.1">']
    dxf = ezdxf.new("R2010", setup=False)
    dxf.units = ezdxf.units.MM
    msp = dxf.modelspace()
    for i in range(copies):
        cx = gap + pitch * (i % cols) + FW_D / 2
        cy = gap + pitch * (i // cols) + FW_D / 2
        for hx, hy, d in plan_holes():  # inner holes first
            svg.append(f'<circle cx="{cx + hx:.3f}" cy="{cy - hy:.3f}" r="{d / 2:.3f}"/>')
            msp.add_circle((cx + hx, H - (cy - hy)), d / 2)
        svg.append(f'<circle cx="{cx:.3f}" cy="{cy:.3f}" r="{FW_D / 2:.3f}"/>')
        msp.add_circle((cx, H - cy), FW_D / 2)
    svg += ["</g>", "</svg>"]
    (OUT / "laser" / "firewall_3mm_plywood_x4.svg").write_text("\n".join(svg))
    dxf.saveas(OUT / "laser" / "firewall_3mm_plywood_x4.dxf")


# ---- 3D: manifold helpers ------------------------------------------------
SEG = 128


def cyl(d, h, x=0.0, y=0.0, z=0.0):
    return m3d.Manifold.cylinder(h, d / 2, d / 2, SEG).translate((x, y, z))


def slot(r0, r1, w, ang, h):
    # stadium-shaped slot along a radius
    x0, y0 = polar(r0, ang)
    x1, y1 = polar(r1, ang)
    a = cyl(w, h + 2, x0, y0, -1)
    b = cyl(w, h + 2, x1, y1, -1)
    return m3d.Manifold.batch_hull([a, b])


def plate():
    return cyl(FW_D, FW_T)


def mount_plan_pattern():
    m = plate()
    for hx, hy, d in plan_holes():
        m = m - cyl(d, FW_T + 2, hx, hy, -1)
    return m


def mount_universal():
    m = plate() - cyl(CENTER_D, FW_T + 2, 0, 0, -1)
    for a in SLOT_ANG:
        m = m - slot(SLOT_R0, SLOT_R1, SLOT_W, a, FW_T)
    return m


def kfm_sanding_block():
    # 90 x 40 x 24 block; concave half-round grooves along the length on
    # opposite faces for rounding leading edges. Radii include ~0.5 mm for
    # sandpaper stuck in the groove with double-sided tape.
    L, W, H = 90.0, 40.0, 24.0
    m = m3d.Manifold.cube((L, W, H))
    for r, z in [(3.5, H), (6.5, 0.0)]:  # 6 mm sheet on top, 12 mm KFM step below
        g = m3d.Manifold.cylinder(L + 2, r, r, SEG).rotate((0, 90, 0)).translate((-1, W / 2, z))
        m = m - g
    return m.translate((-L / 2, -W / 2, 0))


def to_trimesh(man):
    mesh = man.to_mesh()
    return trimesh.Trimesh(vertices=np.asarray(mesh.vert_properties)[:, :3],
                           faces=np.asarray(mesh.tri_verts), process=True)


def print_files():
    parts = {
        "motor_mount_plan_pattern": mount_plan_pattern(),
        "motor_mount_universal_slots": mount_universal(),
        "kfm_sanding_block": kfm_sanding_block(),
    }
    scene = trimesh.Scene()
    x = 0.0
    for name, man in parts.items():
        tm = to_trimesh(man)
        assert tm.is_watertight, name
        tm.export(OUT / "print" / f"{name}.stl")
        b = tm.bounds
        placed = tm.copy()
        placed.apply_translation((x - b[0][0], -(b[0][1] + b[1][1]) / 2, -b[0][2]))
        scene.add_geometry(placed, node_name=name, geom_name=name)
        x += (b[1][0] - b[0][0]) + 10
    scene.export(OUT / "print" / "airspeed_as31_all_parts.3mf")


if __name__ == "__main__":
    laser_files()
    print_files()
    for p in sorted(OUT.rglob("*")):
        if p.is_file() and p.suffix != ".py":
            print(p.relative_to(OUT), p.stat().st_size)

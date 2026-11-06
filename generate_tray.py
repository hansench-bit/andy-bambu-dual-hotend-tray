"""
Parametric CAD Generator for Andy Bambu Toolbox Upper Replacement Tray (v4.0 — Option B-2)
Calibrated directly to MakerWorld #2106466 (H2C Tool Box Hotend Box), #1418034 (H2D/H2S),
Vortek H2C 3MF reference geometry, and physical nozzle test-fit photogrammetry:
  - Outer Shell: 184.20 x 114.20 x 19.00 mm with front-center push-button lock through-gap,
    4 corner ears, and recessed left/right side finger-lift walls (171.4 mm inner deck width)
  - Zero Engraved / Debossed Text on the tray surface
  - Left Section (5x Interleaved Left-Hand H2D/H2C Standard Finned Hotends, 56.4 mm total length):
      * 3.2 x 7.2 mm top filament inlet boss notch
      * 19.6 mm wide x 18.0 mm full-depth heatsink fin cavity + 4.8 mm upper overhang relief
        (22.8 mm total 19.6 mm-wide heatsink opening to clear all 8 fins & 'H2 | 0.2' overhang)
      * 22.4 mm span finger-pinch side scoops
      * 12.0 mm wide flanged heater-block channel with 6.6 mm deep central trough + 5.2 mm tip cone
  - Right Section (5x Interleaved Right-Hand H2C Induction Hotends, 57.6 mm total length):
      * 6.2 x 8.6 mm top mushroom-pin cap cavity
      * Stepped heatsink cavity: 15.8 x 8.0 mm upper block step + 19.2 x 11.0 mm lower 4-fin step
        (19.0 mm total heatsink length) with 22.2 mm span finger-pinch scoops
      * 9.8 mm wide cylindrical shaft channel with 6.8 mm deep central cradle trough
      * 14.8 mm diameter bulbous induction head cavity + 4.6 mm pointed tip cone
  - 3 Lower Accessory Pockets (Option B-2):
      * Bottom-Left  (X = -74.2, Y = -31.0): 1x H2C Induction Silicone Sock Pocket
      * Center       (X =   0.0, Y = -25.0): 1x Wiper / Silicone Purge Pad Slot
      * Bottom-Right (X = +74.2, Y = -31.0): 1x H2C Induction Silicone Sock Pocket
"""

import os
import numpy as np
import shapely.geometry as sg
import shapely.ops as so
import manifold3d as m3d
import trimesh

m3d.set_circular_segments(96)

# ==============================================================================
# 1. OUTER SILHOUETTE & TOLERANCE PARAMETERS (mm) — MAKERWORLD #2106466 CALIBRATED
# ==============================================================================
BOX_INNER_X = 185.00
BOX_INNER_Y = 115.00
OUTER_WALL_OFFSET = 0.40  # -0.40 mm clearance per side

TRAY_X = BOX_INNER_X - 2.0 * OUTER_WALL_OFFSET  # 184.20 mm
TRAY_Y = BOX_INNER_Y - 2.0 * OUTER_WALL_OFFSET  # 114.20 mm
TRAY_Z = 19.00                                  # 19.00 mm total tray height
DECK_RECESS = 1.50                              # 1.50 mm recessed inner deck inside outer rim
DECK_Z = TRAY_Z - DECK_RECESS                   # 17.50 mm main deck surface
RIM_WALL = 2.20                                 # 2.20 mm perimeter rim wall matching #2106466
CORNER_RADIUS = 8.00                            # Corner ear outer radius

# Front-Center Push-Button Latch Through-Gap (-Y front edge, X = 0)
LATCH_GAP_W = 19.50       # Width (X) of the push-button gap
LATCH_GAP_D = 15.20       # Depth (Y) from front -Y edge into tray
LATCH_CORNER_R = 2.50

# Left & Right Side Finger-Lift Recesses (-X and +X edges between the 4 corner ears)
# 4.20 mm recess + 2.20 mm rim wall leaves X = [-85.70, +85.70] (171.40 mm) inner deck width
SIDE_RECESS_SPAN_Y = 70.00
SIDE_RECESS_DEPTH_X = 4.20

# Floor & Pocket Depths
FLOOR_THICKNESS = 2.00                 # 2.00 mm solid bottom floor
MAIN_FLOOR_Z = FLOOR_THICKNESS + 1.50  # 3.50 mm (14.00 mm main pocket depth + 1.50 mm deep central cradle)


# ==============================================================================
# 2. 2D SHAPELY & MANIFOLD3D HELPERS
# ==============================================================================
def rounded_rect(xc, yc, w, h, r=0.0):
    if r <= 0.0:
        return sg.box(xc - w / 2.0, yc - h / 2.0, xc + w / 2.0, yc + h / 2.0)
    r = min(r, w / 2.0 - 0.01, h / 2.0 - 0.01)
    core = sg.box(
        xc - w / 2.0 + r,
        yc - h / 2.0 + r,
        xc + w / 2.0 - r,
        yc + h / 2.0 - r,
    )
    return core.buffer(r, quad_segs=24)


def slot_overall(xc, yc, overall_len, width, vertical=False):
    r = width / 2.0
    half_span = max(0.0, (overall_len - width) / 2.0)
    if vertical:
        line = sg.LineString([(xc, yc - half_span), (xc, yc + half_span)])
    else:
        line = sg.LineString([(xc - half_span, yc), (xc + half_span, yc)])
    return line.buffer(r, quad_segs=24)


def poly_to_cs(poly):
    if poly.is_empty:
        return m3d.CrossSection()
    polys = [poly] if isinstance(poly, sg.Polygon) else [g for g in poly.geoms if isinstance(g, sg.Polygon)]
    contours = []
    for p in polys:
        ext = np.array(p.exterior.coords[:-1], dtype=np.float64)
        if not sg.LinearRing(ext).is_ccw:
            ext = ext[::-1]
        contours.append(ext)
        for interior in p.interiors:
            hole = np.array(interior.coords[:-1], dtype=np.float64)
            if sg.LinearRing(hole).is_ccw:
                hole = hole[::-1]
            contours.append(hole)
    return m3d.CrossSection(contours, m3d.FillRule.EvenOdd)


def extrude_poly(poly, z_bottom, z_top, lead_in=0.40):
    """
    Extrudes a 2D shapely polygon from z_bottom to z_top, plus a 45-degree
    stepped lead-in bevel at the top rim for effortless drop-in placement.
    """
    cs = poly_to_cs(poly)
    main_vol = cs.extrude((z_top - z_bottom) + 0.05).translate([0.0, 0.0, z_bottom])
    if lead_in > 0.0:
        steps = 4
        for i in range(1, steps + 1):
            frac = i / float(steps)
            z0 = z_top - lead_in * (1.0 - (i - 1) / float(steps))
            dz = (lead_in / float(steps)) + 0.04
            bevel_poly = poly.buffer(lead_in * frac, quad_segs=16)
            bevel_vol = poly_to_cs(bevel_poly).extrude(dz).translate([0.0, 0.0, z0])
            main_vol = main_vol + bevel_vol
    return main_vol


def make_outer_silhouette_poly():
    outer = rounded_rect(0.0, 0.0, TRAY_X, TRAY_Y, CORNER_RADIUS)
    for x_sign in [-1.0, 1.0]:
        cut_side = rounded_rect(
            x_sign * (TRAY_X / 2.0 + 4.0),
            0.0,
            2.0 * (SIDE_RECESS_DEPTH_X + 4.0),
            SIDE_RECESS_SPAN_Y,
            5.0,
        )
        outer = outer.difference(cut_side)
    cut_latch = rounded_rect(
        0.0,
        -TRAY_Y / 2.0,
        LATCH_GAP_W,
        2.0 * LATCH_GAP_D,
        LATCH_CORNER_R,
    )
    outer = outer.difference(cut_latch)
    return outer


# ==============================================================================
# 3. CALIBRATED POCKET GENERATORS (MAKERWORLD #2106466 + PHOTOGRAMMETRY)
# ==============================================================================
def get_h2d_finned_hotend_polys(xc, y_origin, point_down=True):
    """
    Returns (main_poly, overhang_poly, deep_cradle_poly, pinch_poly) for the
    Left-Hand H2D/H2C Standard Finned Hotend (56.40 mm total length):
      - d =  0.0 ..  3.2 mm : Top filament inlet boss notch (7.2 mm wide x 3.2 mm long)
      - d =  3.2 .. 21.2 mm : Main full-depth heatsink fin pocket (19.6 mm wide x 18.0 mm long)
      - d = 21.2 .. 26.0 mm : Upper 'H2 | 0.2' overhang relief step (19.6 mm wide x 4.8 mm long,
                              extending 22.8 mm total from inlet face so all 8 fins drop in cleanly)
      - Finger-pinch side scoops (22.4 mm span x 10.0 mm long)
      - d = 21.2 .. 51.2 mm : Flanged heater-block channel (12.0 mm wide) + 6.6 mm wide deep cradle
      - d = 51.2 .. 56.4 mm : Pointed nozzle tip cone (5.2 mm long, total slot length = 56.4 mm)
    """
    s = -1.0 if point_down else 1.0

    def y_at(d):
        return y_origin + s * d

    hs_w = 19.60
    shaft_w = 12.00

    p_inlet = rounded_rect(xc, y_at(1.60), 7.60, 3.20, 1.0)
    p_hs = rounded_rect(xc, y_at(11.85), hs_w, 18.70, 1.2)
    p_shaft = rounded_rect(xc, y_at(35.60), shaft_w, 31.20, 0.0)
    p_tip = sg.Polygon([
        (xc - shaft_w / 2.0, y_at(51.10)),
        (xc + shaft_w / 2.0, y_at(51.10)),
        (xc + 0.80, y_at(56.40)),
        (xc - 0.80, y_at(56.40)),
    ])
    main_poly = so.unary_union([p_inlet, p_hs, p_shaft, p_tip])
    overhang_poly = rounded_rect(xc, y_at(14.25), hs_w, 23.50, 1.2)
    deep_cradle_poly = slot_overall(xc, y_at(36.25), 36.50, 6.60, vertical=True)
    pinch_poly = slot_overall(xc, y_at(12.50), 22.40, 10.00, vertical=False)
    return main_poly, overhang_poly, deep_cradle_poly, pinch_poly


def get_h2c_induction_hotend_polys(xc, y_origin, point_down=True):
    """
    Returns (main_poly, deep_cradle_poly, pinch_poly) for the
    Right-Hand H2C Induction Hotend (57.60 mm total length):
      - d =  0.0 ..  5.6 mm : Top mushroom-pin cap cavity (8.8 mm wide x 5.6 mm long)
      - d =  5.6 .. 14.2 mm : Upper heatsink block step with 2 holes (16.0 mm wide x 8.6 mm long)
      - d = 13.8 .. 25.4 mm : Lower 4-fin heatsink step with '0.4' label (19.2 mm wide x 11.6 mm long;
                              total heatsink cavity length = 19.8 mm)
      - Finger-pinch side scoops (22.2 mm span x 9.5 mm long)
      - d = 25.4 .. 44.2 mm : Cylindrical shaft channel (9.8 mm wide x 18.8 mm long)
      - d = 44.2 .. 53.0 mm : Bulbous round induction nozzle head cavity (Dia 14.8 mm, centered at d = 48.6 mm)
      - d = 53.0 .. 57.6 mm : Pointed nozzle tip cone (4.6 mm long, total slot length = 57.6 mm)
    """
    s = -1.0 if point_down else 1.0

    def y_at(d):
        return y_origin + s * d

    upper_hs_w = 16.00
    lower_hs_w = 19.20
    shaft_w = 9.80
    head_dia = 14.80

    p_pin = rounded_rect(xc, y_at(3.00), 8.80, 6.00, 1.2)
    p_hs_up = rounded_rect(xc, y_at(9.90), upper_hs_w, 8.60, 1.2)
    p_hs_lo = rounded_rect(xc, y_at(19.60), lower_hs_w, 11.60, 1.2)
    p_shaft = rounded_rect(xc, y_at(36.50), shaft_w, 25.00, 0.0)
    p_head = sg.Point(xc, y_at(48.60)).buffer(head_dia / 2.0, quad_segs=32)
    p_tip = sg.Polygon([
        (xc - 5.20, y_at(51.50)),
        (xc + 5.20, y_at(51.50)),
        (xc + 0.80, y_at(57.60)),
        (xc - 0.80, y_at(57.60)),
    ])
    main_poly = so.unary_union([p_pin, p_hs_up, p_hs_lo, p_shaft, p_head, p_tip])

    cradle_slot = slot_overall(xc, y_at(35.50), 39.00, 6.80, vertical=True)
    cradle_head = sg.Point(xc, y_at(48.60)).buffer(head_dia / 2.0 - 0.80, quad_segs=32)
    deep_cradle_poly = so.unary_union([cradle_slot, cradle_head])

    pinch_poly = slot_overall(xc, y_at(19.70), 22.20, 9.50, vertical=False)
    return main_poly, deep_cradle_poly, pinch_poly


def get_induction_sock_polys(xc, yc):
    w_sock = 14.60
    l_sock = 24.00
    p_tab = rounded_rect(xc, yc + 11.50, 6.20, 4.50, 1.0)
    p_body = slot_overall(xc, yc - 0.50, l_sock, w_sock, vertical=True)
    main_poly = so.unary_union([p_tab, p_body])
    pinch_poly = slot_overall(xc, yc - 0.50, w_sock + 3.40, 8.50, vertical=False)
    return main_poly, pinch_poly


def get_wiper_slot_polys(xc, yc, w=14.20, h=25.00):
    main_poly = rounded_rect(xc, yc, w, h, 2.0)
    pinch_poly = slot_overall(xc, yc, w + 3.60, 8.50, vertical=False)
    return main_poly, pinch_poly


# ==============================================================================
# 4. BUILD SOLID MANIFOLD TRAY
# ==============================================================================
LEFT_SLOTS = [
    (-63.8, 45.2, True),
    (-37.8, 45.2, True),
    (-11.8, 45.2, True),
    (-50.8, -45.2, False),
    (-24.8, -45.2, False),
]

RIGHT_SLOTS = [
    (11.8, 44.6, True),
    (37.8, 44.6, True),
    (63.8, 44.6, True),
    (24.8, -44.6, False),
    (50.8, -44.6, False),
]

SOCK_SLOTS = [
    (-74.2, -31.0),
    (74.2, -31.0),
]

WIPER_SLOT = (0.0, -25.0, 14.2, 25.0)


def build_dual_hotend_tray_mesh():
    outer_poly = make_outer_silhouette_poly()
    inner_deck_poly = outer_poly.buffer(-RIM_WALL, quad_segs=24)

    # Start with outer body extruded to TRAY_Z, minus inner deck recess above DECK_Z
    tray_vol = poly_to_cs(outer_poly).extrude(TRAY_Z)
    deck_recess_vol = poly_to_cs(inner_deck_poly).extrude(DECK_RECESS + 0.10).translate([0.0, 0.0, DECK_Z])
    tray_vol = tray_vol - deck_recess_vol

    # Collect unioned 2D polygons by floor depth to minimize 3D boolean operations
    polys_main_floor = []
    polys_overhang = []
    polys_deep_cradle = []
    polys_pinch_95 = []
    polys_pinch_85 = []

    for xc, y0, p_down in LEFT_SLOTS:
        p_main, p_ovh, p_cradle, p_pinch = get_h2d_finned_hotend_polys(xc, y0, point_down=p_down)
        polys_main_floor.append(p_main)
        polys_overhang.append(p_ovh)
        polys_deep_cradle.append(p_cradle)
        polys_pinch_95.append(p_pinch)

    for xc, y0, p_down in RIGHT_SLOTS:
        p_main, p_cradle, p_pinch = get_h2c_induction_hotend_polys(xc, y0, point_down=p_down)
        polys_main_floor.append(p_main)
        polys_deep_cradle.append(p_cradle)
        polys_pinch_95.append(p_pinch)

    for xc, yc in SOCK_SLOTS:
        p_main, p_pinch = get_induction_sock_polys(xc, yc)
        polys_main_floor.append(p_main)
        polys_pinch_85.append(p_pinch)

    wx, wy, ww, wh = WIPER_SLOT
    p_wmain, p_wpinch = get_wiper_slot_polys(wx, wy, ww, wh)
    polys_main_floor.append(p_wmain)
    polys_pinch_85.append(p_wpinch)

    # Check that no two main pockets accidentally overlap
    for i in range(len(polys_main_floor)):
        for j in range(i + 1, len(polys_main_floor)):
            inter = polys_main_floor[i].intersection(polys_main_floor[j])
            if not inter.is_empty and inter.area > 0.01:
                print(f"WARNING: Pocket {i} and Pocket {j} intersect (area={inter.area:.2f} mm^2)")

    # Build monotonic Z-slab unions so shared walls have zero duplicate/near-coincident vertices
    u_cradle = so.unary_union(polys_deep_cradle)
    u_main = so.unary_union(polys_main_floor)
    u_ovh = so.unary_union([u_main] + polys_overhang)
    u_p95 = so.unary_union([u_ovh] + polys_pinch_95)
    u_p85 = so.unary_union([u_p95] + polys_pinch_85)

    z_ovh = DECK_Z - 10.50  # 7.00 mm
    z_p95 = DECK_Z - 9.50   # 8.00 mm
    z_p85 = DECK_Z - 8.50   # 9.00 mm

    tray_vol = tray_vol - poly_to_cs(u_cradle).extrude((MAIN_FLOOR_Z - FLOOR_THICKNESS) + 0.05).translate([0.0, 0.0, FLOOR_THICKNESS])
    tray_vol = tray_vol - poly_to_cs(u_main).extrude((z_ovh - MAIN_FLOOR_Z) + 0.05).translate([0.0, 0.0, MAIN_FLOOR_Z])
    tray_vol = tray_vol - poly_to_cs(u_ovh).extrude((z_p95 - z_ovh) + 0.05).translate([0.0, 0.0, z_ovh])
    tray_vol = tray_vol - poly_to_cs(u_p95).extrude((z_p85 - z_p95) + 0.05).translate([0.0, 0.0, z_p95])
    tray_vol = tray_vol - extrude_poly(u_p85, z_p85, DECK_Z, lead_in=0.40)

    mesh_data = tray_vol.to_mesh()
    tm = trimesh.Trimesh(vertices=mesh_data.vert_properties[:, :3], faces=mesh_data.tri_verts, process=True)
    return tm


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    stl_path = os.path.join(out_dir, "andy_dual_hotend_tray.stl")
    threemf_path = os.path.join(out_dir, "andy_dual_hotend_tray.3mf")

    print("Building v4.0 (MakerWorld #2106466 calibrated) parametric 3D solid...")
    mesh = build_dual_hotend_tray_mesh()

    print(f"Exporting high-resolution STL to: {stl_path}")
    mesh.export(stl_path)

    print(f"Exporting 3MF to: {threemf_path}")
    mesh.export(threemf_path)

    extents = mesh.extents
    print("=== MESH & GEOMETRY VERIFICATION ===")
    print(f"Is Watertight / Manifold : {mesh.is_watertight}")
    print(f"Is Winding Consistent    : {mesh.is_winding_consistent}")
    print(f"Euler Number             : {mesh.euler_number}")
    print(f"Vertices / Faces         : {len(mesh.vertices):,} / {len(mesh.faces):,}")
    print(f"Bounding Box Extents (mm): X={extents[0]:.2f}, Y={extents[1]:.2f}, Z={extents[2]:.2f}")
    print(f"Solid Volume (cm^3)      : {mesh.volume / 1000.0:.2f} cm^3")

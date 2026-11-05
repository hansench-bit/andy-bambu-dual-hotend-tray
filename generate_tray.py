"""
Parametric CAD Generator for Andy Bambu Toolbox Upper Replacement Tray (v2.1)
Exact MakerWorld #1418034 (H2D/H2S) & #2106466 (H2C) Outer Silhouette with:
  - Front-Center Push-Button Latch Cutout (through-gap for Bambu logo push lock)
  - Left & Right Recessed Side Finger-Lift Cutouts with 4 Corner Ears
  - Vertical Interleaved Layout:
      * Left Deck: 4x Standard/X2C/H2D Finned Hotends (0.2, 0.4, 0.6, 0.8) +
                   2x Form-Fitted Standard Silicone Sock Cavities + 3x Pin Holes
      * Center:    Push-Button Latch Gap + Wiper / Purge Spare Pocket above latch
      * Right Deck: 4x H2C Right-Side Induction Hotends (IND 0.2, 0.4, 0.6, 0.8) with
                    bulbous +0.5mm induction coil head relief + 3x Induction Sock
                    Cavities + 3x Pin Holes
"""

import os
import trimesh
from build123d import (
    BuildPart,
    BuildSketch,
    Plane,
    Locations,
    Mode,
    Align,
    Rectangle,
    RectangleRounded,
    Circle,
    SlotOverall,
    Polygon,
    Text,
    FontStyle,
    extrude,
    loft,
    offset,
    export_stl,
    export_step,
)

# ==============================================================================
# 1. OUTER SILHOUETTE & TOLERANCE PARAMETERS (mm)
# ==============================================================================
BOX_INNER_X = 185.00
BOX_INNER_Y = 115.00
OUTER_WALL_OFFSET = 0.40  # -0.40 mm clearance per side

TRAY_X = BOX_INNER_X - 2.0 * OUTER_WALL_OFFSET  # 184.20 mm
TRAY_Y = BOX_INNER_Y - 2.0 * OUTER_WALL_OFFSET  # 114.20 mm
TRAY_Z = 18.50                                  # 18.5 mm height matching Andy upper tray
DECK_RECESS = 1.50                              # 1.5 mm recessed inner deck inside outer rim
DECK_Z = TRAY_Z - DECK_RECESS                   # 17.00 mm main deck surface
CORNER_RADIUS = 8.00                            # Corner ear outer radius

# Front-Center Push-Button Latch Through-Gap (-Y front edge, X = 0)
LATCH_GAP_W = 19.50       # Width (X) of the push-button gap
LATCH_GAP_D = 15.60       # Depth (Y) from front -Y edge into tray
LATCH_CORNER_R = 2.50

# Left & Right Side Finger-Lift Recesses (-X and +X edges between the 4 corner ears)
SIDE_RECESS_SPAN_Y = 72.00  # Leaves 21.1 mm tall corner ears at top (+Y) and bottom (-Y)
SIDE_RECESS_DEPTH_X = 6.80  # Recessed 6.8 mm inward from outer X edge

# Floor & Clearances
FLOOR_THICKNESS = 2.40
TOL_HOTEND = 0.35           # +0.35 mm non-locking clearance
TOL_SOCK = 0.20             # +0.20 mm snug silicone sock fit
TOL_COIL_RELIEF = 0.50      # +0.50 mm extra clearance around H2C induction head
LOCK_INTERFERENCE = 0.15    # 0.15 mm neck retention snap bead
TEXT_RELIEF_DEPTH = 0.40    # 0.40 mm debossed relief depth


def make_outer_silhouette():
    """
    Constructs the exact 2D outer footprint of the Andy H2D/H2C upper tray:
    - 184.2 x 114.2 mm rounded rectangle with 4 corner ears
    - Left & Right recessed finger-lift cutouts (6.8 mm deep x 72 mm tall)
    - Front-center push-button latch through-gap (19.5 mm wide x 15.6 mm deep at -Y, X=0)
    """
    with BuildSketch(Plane.XY) as sk:
        RectangleRounded(TRAY_X, TRAY_Y, CORNER_RADIUS)

        # Subtract Left (-X) and Right (+X) side finger-lift recesses
        for x_sign in [-1, 1]:
            with Locations((x_sign * (TRAY_X / 2.0 + 4.0), 0.0)):
                RectangleRounded(
                    2.0 * (SIDE_RECESS_DEPTH_X + 4.0),
                    SIDE_RECESS_SPAN_Y,
                    5.5,
                    mode=Mode.SUBTRACT,
                )

        # Subtract Front-Center Push-Button Latch Through-Gap at -Y edge (X = 0)
        with Locations((0.0, -TRAY_Y / 2.0)):
            RectangleRounded(
                LATCH_GAP_W,
                2.0 * LATCH_GAP_D,
                LATCH_CORNER_R,
                mode=Mode.SUBTRACT,
            )
    return sk.sketch


def cut_pocket(sketch_fn, floor_z, top_z=DECK_Z, lead_in=0.55):
    """
    Cuts a vertical cavity from floor_z to top_z, plus a clean flared lead-in rim
    at the top mouth for easy drop-in placement.
    """
    with BuildSketch(Plane.XY.offset(floor_z)) as sk_main:
        sketch_fn()
    extrude(sk_main.sketch, amount=(top_z - floor_z) + 0.05, mode=Mode.SUBTRACT)

    if lead_in > 0:
        with BuildSketch(Plane.XY.offset(top_z - lead_in)) as sk_ch:
            sketch_fn()
            offset(amount=lead_in)
        extrude(sk_ch.sketch, amount=lead_in + 0.05, mode=Mode.SUBTRACT)


def add_vertical_slot_retention_bead(x_wall, y_center, side_sign, z_center=10.5):
    """
    Adds a 0.15 mm interference retention bead along a vertical slot's neck wall (X-wall).
    Uses 45-degree top/bottom draft ramps so it prints cleanly without support.
    """
    bead_len_y = 3.6
    bead_half_z = 1.0
    with BuildSketch(Plane.XY.offset(z_center - bead_half_z)) as sk1:
        with Locations((x_wall + side_sign * 0.12, y_center)):
            RectangleRounded(0.24, bead_len_y, 0.06)
    with BuildSketch(Plane.XY.offset(z_center)) as sk2:
        with Locations((x_wall - side_sign * (LOCK_INTERFERENCE / 2.0), y_center)):
            RectangleRounded(0.24 + LOCK_INTERFERENCE, bead_len_y, 0.06)
    with BuildSketch(Plane.XY.offset(z_center + bead_half_z)) as sk3:
        with Locations((x_wall + side_sign * 0.12, y_center)):
            RectangleRounded(0.24, bead_len_y, 0.06)
    loft([sk1.sketch, sk2.sketch, sk3.sketch], ruled=True, mode=Mode.ADD)


def cut_x2c_finned_hotend_vertical(xc, yc, point_down=True):
    """
    Cuts a vertical Standard / X2C / H2D Finned Hotend slot centered at (xc, yc),
    matching the exact silhouette in MakerWorld #1418034 & #2106466:
      - Total length ~48.6 mm along Y (47.3-47.9 mm nominal + 2*0.35 mm clearance)
      - Filament inlet stem pocket at top (5.2 x 5.5 mm)
      - Contoured square finned heatsink block pocket (16.4 + TOL x 16.4 mm)
      - Left/Right semi-circular finger-pinch scoops alongside the heatsink (20.6 mm span)
      - Neck step (9.2 + TOL wide) with 0.15 mm retention snap beads
      - Heater block / sock shaft channel (10.8 + TOL wide x 20.5 mm long)
      - Conical pointed nozzle tip runout + deeper central floor clearance groove
    """
    s = -1.0 if point_down else 1.0

    y_stem = yc + s * (-21.8)
    y_hs = yc + s * (-11.6)
    y_neck = yc + s * (-1.0)
    y_shaft = yc + s * (9.8)

    hs_w = 16.2 + TOL_HOTEND      # 16.55 mm
    hs_l = 16.2 + TOL_HOTEND      # 16.55 mm
    neck_w = 9.0 + TOL_HOTEND     # 9.35 mm
    shaft_w = 10.6 + TOL_HOTEND   # 10.95 mm

    def main_profile():
        with Locations((xc, y_stem)):
            RectangleRounded(5.2 + TOL_HOTEND, 5.8, 0.9)
        with Locations((xc, y_hs)):
            RectangleRounded(hs_w, hs_l, 1.2)
        with Locations((xc, y_neck)):
            Rectangle(neck_w, 6.5)
        with Locations((xc, y_shaft)):
            RectangleRounded(shaft_w, 20.0, 1.2)
        tip_pts = [
            (xc - shaft_w * 0.44, yc + s * 18.2),
            (xc + shaft_w * 0.44, yc + s * 18.2),
            (xc, yc + s * 24.3),
        ]
        Polygon(*tip_pts)

    cut_pocket(main_profile, floor_z=FLOOR_THICKNESS + 1.4, lead_in=0.55)

    # Deeper central floor groove under nozzle tip & heater shaft so nozzle never touches floor
    def deep_groove():
        with Locations((xc, yc + s * 4.5)):
            SlotOverall(35.0, 5.4, rotation=90)

    cut_pocket(deep_groove, floor_z=FLOOR_THICKNESS, top_z=FLOOR_THICKNESS + 1.6, lead_in=0.0)

    # Finger-pinch scoops on left and right of heatsink (20.6 mm total span leaves >= 3.5 mm wall)
    def pinch_scoops():
        with Locations((xc, y_hs)):
            SlotOverall(hs_w + 4.2, 10.6)

    cut_pocket(pinch_scoops, floor_z=FLOOR_THICKNESS + 5.5, lead_in=0.50)

    # Mild retention snap beads on the neck walls (0.15 mm interference)
    add_vertical_slot_retention_bead(xc + neck_w / 2.0, y_neck, side_sign=+1, z_center=10.5)
    add_vertical_slot_retention_bead(xc - neck_w / 2.0, y_neck, side_sign=-1, z_center=10.5)


def cut_h2c_induction_hotend_vertical(xc, yc, point_down=True):
    """
    Cuts a vertical H2C Right-Side Induction Hotend slot centered at (xc, yc),
    matching the exact silhouette in MakerWorld #2106466 (see ref_2106466_2.jpg):
      - Total length clearance: 49.9 mm (49.2 mm nominal + 2*0.35 mm)
      - Top inlet stem pocket (5.2 x 5.8 mm)
      - Upper H2C smart connector / heatsink block (15.0 + TOL x 16.0 mm)
      - Left/Right finger-pinch scoops at upper block (19.4 mm total span)
      - Cylindrical shaft channel (8.6 + TOL wide) with 0.15 mm retention beads
      - Bulbous / flared circular induction coil head pocket (Dia 14.2 mm)
        with +0.50 mm radial and floor relief to protect delicate coil coating
      - Pointed conical nozzle tip clearance at the end
    """
    s = -1.0 if point_down else 1.0

    y_stem = yc + s * (-22.2)
    y_blk = yc + s * (-12.0)
    y_neck = yc + s * (1.5)
    y_coil = yc + s * (15.2)

    blk_w = 14.8 + TOL_HOTEND     # 15.15 mm
    blk_l = 16.0 + TOL_HOTEND     # 16.35 mm
    neck_w = 8.4 + TOL_HOTEND     # 8.75 mm
    coil_dia = 13.2 + 2.0 * TOL_COIL_RELIEF  # 14.20 mm (+0.50 mm radial clearance per side)

    def ind_profile():
        with Locations((xc, y_stem)):
            RectangleRounded(5.2 + TOL_HOTEND, 5.8, 0.9)
        with Locations((xc, y_blk)):
            RectangleRounded(blk_w, blk_l, 1.3)
        with Locations((xc, y_neck)):
            Rectangle(neck_w, 24.0)
        with Locations((xc, y_coil)):
            Circle(coil_dia / 2.0)
        tip_pts = [
            (xc - coil_dia * 0.40, yc + s * 17.5),
            (xc + coil_dia * 0.40, yc + s * 17.5),
            (xc, yc + s * 24.9),
        ]
        Polygon(*tip_pts)

    cut_pocket(ind_profile, floor_z=FLOOR_THICKNESS + 1.4, lead_in=0.55)

    # Extra +0.50 mm floor relief under the induction coil head & nozzle tip
    def coil_floor_relief():
        with Locations((xc, yc + s * 5.0)):
            SlotOverall(35.0, 5.4, rotation=90)
        with Locations((xc, y_coil)):
            Circle(coil_dia / 2.0 - 0.5)

    cut_pocket(
        coil_floor_relief,
        floor_z=FLOOR_THICKNESS,
        top_z=FLOOR_THICKNESS + 1.6,
        lead_in=0.0,
    )

    # Finger-pinch scoops on left and right of the upper H2C block (19.35 mm span)
    def ind_pinch():
        with Locations((xc, y_blk)):
            SlotOverall(blk_w + 4.2, 10.4)

    cut_pocket(ind_pinch, floor_z=FLOOR_THICKNESS + 5.5, lead_in=0.50)

    # Mild retention snap beads on neck walls (0.15 mm interference)
    add_vertical_slot_retention_bead(xc + neck_w / 2.0, yc + s * (-1.0), side_sign=+1, z_center=10.5)
    add_vertical_slot_retention_bead(xc - neck_w / 2.0, yc + s * (-1.0), side_sign=-1, z_center=10.5)


def cut_standard_sock_vertical(xc, yc):
    """
    Cuts a form-fitted vertical pocket for the square-profile Bambu standard silicone sock
    ("CAUTION HOT" profile from MakerWorld #1418034 ref_1418034_5.jpg) with +0.20 mm snug fit.
    """
    w_main = 16.4 + TOL_SOCK   # 16.60 mm
    h_main = 16.4 + TOL_SOCK   # 16.60 mm

    def sock_profile():
        with Locations((xc, yc + 11.4)):
            RectangleRounded(4.6 + TOL_SOCK, 4.5, 0.8)
        with Locations((xc, yc + 2.0)):
            RectangleRounded(w_main, h_main, 1.5)
        boot_pts = [
            (xc - 6.6, yc - 5.2),
            (xc + 6.6, yc - 5.2),
            (xc + 4.8, yc - 13.2),
            (xc - 4.8, yc - 13.2),
        ]
        Polygon(*boot_pts)

    cut_pocket(sock_profile, floor_z=DECK_Z - 13.5, lead_in=0.45)

    def sock_pinch():
        with Locations((xc, yc + 2.0)):
            SlotOverall(w_main + 3.4, 9.0)

    cut_pocket(sock_pinch, floor_z=DECK_Z - 8.0, lead_in=0.45)


def cut_induction_sock_vertical(xc, yc):
    """
    Cuts a form-fitted vertical pocket for the rounded/molded H2C induction thermal cover
    (+0.20 mm snug fit, sits completely flush below the tray rim).
    """
    w_cyl = 11.8 + TOL_SOCK    # 12.00 mm
    l_cyl = 24.0 + TOL_SOCK    # 24.20 mm

    def ind_sock_profile():
        with Locations((xc, yc + 11.5)):
            RectangleRounded(4.6 + TOL_SOCK, 4.5, 0.8)
        with Locations((xc, yc - 0.5)):
            SlotOverall(l_cyl, w_cyl, rotation=90)

    cut_pocket(ind_sock_profile, floor_z=DECK_Z - 13.5, lead_in=0.45)

    def ind_sock_pinch():
        with Locations((xc, yc - 0.5)):
            SlotOverall(w_cyl + 3.0, 8.5)

    cut_pocket(ind_sock_pinch, floor_z=DECK_Z - 8.0, lead_in=0.45)


def build_dual_hotend_tray():
    with BuildPart() as tray:
        # ----------------------------------------------------------------------
        # A. OUTER TRAY BODY WITH PUSH-BUTTON LATCH GAP & SIDE FINGER CUTOUTS
        # ----------------------------------------------------------------------
        sk_outer = make_outer_silhouette()
        extrude(sk_outer, amount=TRAY_Z)

        # Recessed inner deck (1.5 mm below the 2.8 mm thick outer perimeter rim wall,
        # matching MakerWorld #1418034 and #2106466)
        with BuildSketch(Plane.XY.offset(DECK_Z)) as sk_deck_recess:
            offset(sk_outer, amount=-2.80)
        extrude(sk_deck_recess.sketch, amount=DECK_RECESS + 0.1, mode=Mode.SUBTRACT)

        # Left (-X) and Right (+X) interior finger-lift slot channels inside the corner ears
        for x_sign in [-1, 1]:
            def side_slot(xs=x_sign):
                with Locations((xs * 79.5, 0.0)):
                    SlotOverall(76.0, 5.0, rotation=90)
            cut_pocket(side_slot, floor_z=FLOOR_THICKNESS + 1.0, top_z=DECK_Z, lead_in=0.45)

        # ----------------------------------------------------------------------
        # B. LEFT SECTION (X < 0): 4x X2C/H2D FINNED HOTENDS + 2x FINNED SOCKS
        # ----------------------------------------------------------------------
        x2c_slots = [
            (-63.0, 23.0, True, "0.2", (-63.0, 51.0)),
            (-37.5, 23.0, True, "0.4", (-37.5, 51.0)),
            (-12.0, 23.0, True, "0.6", (-12.0, 51.0)),
            (-21.5, -22.5, False, "0.8", (-21.5, -51.0)),
        ]
        for xc, yc, p_down, label, txt_pos in x2c_slots:
            cut_x2c_finned_hotend_vertical(xc, yc, point_down=p_down)
            with BuildSketch(Plane.XY.offset(DECK_Z - TEXT_RELIEF_DEPTH)) as sk_t:
                with Locations(txt_pos):
                    Text(label, font_size=4.0, font_style=FontStyle.BOLD, align=(Align.CENTER, Align.CENTER))
            extrude(sk_t.sketch, amount=TEXT_RELIEF_DEPTH + 0.05, mode=Mode.SUBTRACT)

        # 2x Left Standard Finned Silicone Sock Pockets ("CAUTION HOT" vertical profile)
        cut_standard_sock_vertical(-64.0, -32.0)
        cut_standard_sock_vertical(-42.8, -32.0)

        # ----------------------------------------------------------------------
        # C. CENTER SECTION (X = 0): PUSH-BUTTON GAP + WIPER/PURGE POCKET + PIN HOLES
        # ----------------------------------------------------------------------
        # Rectangular Wiper / Purge Spare Pocket directly above the Push-Button Gap
        def center_wiper_pocket():
            with Locations((0.0, -25.5)):
                RectangleRounded(16.8, 17.5, 2.2)

        cut_pocket(center_wiper_pocket, floor_z=FLOOR_THICKNESS + 1.0, top_z=DECK_Z, lead_in=0.45)

        # 6x Small Round Nozzle Pin / Tool Holes (3 on left, 3 on right above wiper pocket)
        for x_pin in [-5.2, 5.2]:
            for y_pin in [-13.2, -8.2, -3.2]:
                def pin_hole(xp=x_pin, yp=y_pin):
                    with Locations((xp, yp)):
                        Circle(1.9)
                cut_pocket(pin_hole, floor_z=FLOOR_THICKNESS + 1.0, top_z=DECK_Z, lead_in=0.35)

        # ----------------------------------------------------------------------
        # D. RIGHT SECTION (X > 0): 4x H2C INDUCTION HOTENDS + 3x IND SOCKS
        # ----------------------------------------------------------------------
        h2c_slots = [
            (12.0, 23.0, True, "IND 0.2", (12.0, 51.0)),
            (37.5, 23.0, True, "IND 0.4", (37.5, 51.0)),
            (63.0, 23.0, True, "IND 0.6", (63.0, 51.0)),
            (21.5, -22.5, False, "IND 0.8", (21.5, -51.0)),
        ]
        for xc, yc, p_down, label, txt_pos in h2c_slots:
            cut_h2c_induction_hotend_vertical(xc, yc, point_down=p_down)
            with BuildSketch(Plane.XY.offset(DECK_Z - TEXT_RELIEF_DEPTH)) as sk_tr:
                with Locations(txt_pos):
                    Text(label, font_size=3.6, font_style=FontStyle.BOLD, align=(Align.CENTER, Align.CENTER))
            extrude(sk_tr.sketch, amount=TEXT_RELIEF_DEPTH + 0.05, mode=Mode.SUBTRACT)

        # 3x Vertical Molded Induction Silicone Sock Pockets in Bottom-Right
        for ind_sx in [38.5, 53.2, 68.0]:
            cut_induction_sock_vertical(ind_sx, -32.0)

        # Debossed Section Labels ("X2C SOCKS", "H2C IND SOCKS", "WIPER") at 0.40 mm depth
        with BuildSketch(Plane.XY.offset(DECK_Z - TEXT_RELIEF_DEPTH)) as sk_lbls:
            with Locations((-53.4, -13.5)):
                Text("X2C SOCKS", font_size=3.4, font_style=FontStyle.BOLD)
            with Locations((53.2, -13.5)):
                Text("H2C IND SOCKS", font_size=3.4, font_style=FontStyle.BOLD)
            with Locations((0.0, -36.5)):
                Text("WIPER", font_size=3.0, font_style=FontStyle.BOLD)
        extrude(sk_lbls.sketch, amount=TEXT_RELIEF_DEPTH + 0.05, mode=Mode.SUBTRACT)

    return tray.part


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    stl_path = os.path.join(out_dir, "andy_dual_hotend_tray.stl")
    step_path = os.path.join(out_dir, "andy_dual_hotend_tray.step")

    print("Building v2.1 parametric 3D solid (MakerWorld #1418034/#2106466 push-button gap format)...")
    part = build_dual_hotend_tray()

    print(f"Exporting STEP to: {step_path}")
    export_step(part, step_path)

    print(f"Exporting high-resolution STL to: {stl_path}")
    export_stl(part, stl_path, tolerance=0.01, angular_tolerance=0.1)

    mesh = trimesh.load(stl_path)
    extents = mesh.extents
    print("=== MESH & GEOMETRY VERIFICATION ===")
    print(f"Is Watertight / Manifold : {mesh.is_watertight}")
    print(f"Is Winding Consistent    : {mesh.is_winding_consistent}")
    print(f"Euler Number             : {mesh.euler_number}")
    print(f"Vertices / Faces         : {len(mesh.vertices):,} / {len(mesh.faces):,}")
    print(f"Bounding Box Extents (mm): X={extents[0]:.2f}, Y={extents[1]:.2f}, Z={extents[2]:.2f}")
    print(f"Solid Volume (cm^3)      : {mesh.volume / 1000.0:.2f} cm^3")

"""
Parametric CAD Generator for Andy Bambu Toolbox Upper Replacement Tray (v3.0 — Option B-2)
Exact MakerWorld #1418034 (H2D/H2S) & #2106466 (H2C) Outer Silhouette with:
  - Front-Center Push-Button Latch Cutout (through-gap for Bambu logo push lock)
  - Left & Right Recessed Side Finger-Lift Cutouts with 4 Corner Ears (no interior side grooves)
  - Zero Engraved / Debossed Text on the tray surface
  - Full 10-Hotend Option B-2 Vertical Interleaved Layout:
      * Left Deck:  5x Left-Hand Standard Finned Hotends WITH Silicone Sock Mounted ON
                    (3 top pointing down + 2 interleaved bottom pointing up)
      * Right Deck: 5x Right-Hand H2C Induction Hotends with bulbous +0.50 mm coil relief
                    (3 top pointing down + 2 interleaved bottom pointing up)
      * Lower Dead Spaces Filled (Option B-2):
          - Bottom-Left  (X = -68.5, Y = -29.5): 1x Induction Silicone Sock Pocket
          - Center       (X =   0.0, Y = -22.5): 1x Wiper / Purge Pad Slot (above Push-Button Gap)
          - Bottom-Right (X = +68.5, Y = -29.5): 1x Induction Silicone Sock Pocket
"""

import os
import trimesh
from build123d import (
    BuildPart,
    BuildSketch,
    Plane,
    Locations,
    Mode,
    Rectangle,
    RectangleRounded,
    Circle,
    SlotOverall,
    Polygon,
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


def make_outer_silhouette():
    """
    Constructs the exact 2D outer footprint of the Andy H2D/H2C upper tray:
    - 184.2 x 114.2 mm rounded rectangle with 4 corner ears
    - Left & Right recessed finger-lift cutouts (6.8 mm deep x 72 mm tall)
    - Front-center push-button latch through-gap (19.5 mm wide x 15.6 mm deep at -Y, X=0)
    """
    with BuildSketch(Plane.XY) as sk:
        RectangleRounded(TRAY_X, TRAY_Y, CORNER_RADIUS)

        for x_sign in [-1, 1]:
            with Locations((x_sign * (TRAY_X / 2.0 + 4.0), 0.0)):
                RectangleRounded(
                    2.0 * (SIDE_RECESS_DEPTH_X + 4.0),
                    SIDE_RECESS_SPAN_Y,
                    5.5,
                    mode=Mode.SUBTRACT,
                )

        with Locations((0.0, -TRAY_Y / 2.0)):
            RectangleRounded(
                LATCH_GAP_W,
                2.0 * LATCH_GAP_D,
                LATCH_CORNER_R,
                mode=Mode.SUBTRACT,
            )
    return sk.sketch


def cut_pocket(sketch_fn, floor_z, top_z=DECK_Z, lead_in=0.50):
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
    bead_len_y = 3.4
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


def cut_x2c_sock_on_hotend_vertical(xc, yc, point_down=True):
    """
    Cuts a vertical Left-Hand (X2C / H2D Standard Finned) Hotend slot WITH the Silicone Sock
    mounted ON the heater block:
      - Top inlet stem pocket (5.55 x 5.8 mm)
      - Square finned heatsink block pocket (16.55 x 15.75 mm) + finger-pinch scoops (20.35 mm span)
      - Short neck step (9.35 mm wide) with 0.15 mm retention snap beads
      - Mounted "CAUTION HOT" Silicone Sock body cavity (16.75 mm wide x 14.55 mm long)
      - Tapered silicone sock boot + conical pointed nozzle tip runout
      - Deeper central floor clearance groove so the nozzle tip never touches bottom plastic
    """
    s = -1.0 if point_down else 1.0

    hs_w = 16.2 + TOL_HOTEND      # 16.55 mm
    hs_l = 15.4 + TOL_HOTEND      # 15.75 mm
    neck_w = 9.0 + TOL_HOTEND     # 9.35 mm
    sock_w = 16.4 + TOL_HOTEND    # 16.75 mm (silicone sock mounted on heater block)
    sock_l = 14.2 + TOL_HOTEND    # 14.55 mm

    y_stem = yc + s * (-21.8)
    y_hs = yc + s * (-12.0)
    y_neck = yc + s * (-2.0)
    y_sock = yc + s * (6.8)

    def main_profile():
        # Inlet stem
        with Locations((xc, y_stem)):
            RectangleRounded(5.2 + TOL_HOTEND, 5.8, 0.9)
        # Heatsink block
        with Locations((xc, y_hs)):
            RectangleRounded(hs_w, hs_l, 1.2)
        # Neck step
        with Locations((xc, y_neck)):
            Rectangle(neck_w, 5.5)
        # Mounted Silicone Sock Body on heater block
        with Locations((xc, y_sock)):
            RectangleRounded(sock_w, sock_l, 1.5)
        # Tapered sock boot + conical nozzle tip
        tip_pts = [
            (xc - 6.6, yc + s * 13.0),
            (xc + 6.6, yc + s * 13.0),
            (xc + 4.8, yc + s * 19.5),
            (xc, yc + s * 24.3),
            (xc - 4.8, yc + s * 19.5),
        ]
        Polygon(*tip_pts)

    cut_pocket(main_profile, floor_z=FLOOR_THICKNESS + 1.4, lead_in=0.50)

    # Deeper central floor groove under nozzle tip & mounted sock so nozzle tip hovers freely
    def deep_groove():
        with Locations((xc, yc + s * 5.0)):
            SlotOverall(35.0, 5.4, rotation=90)

    cut_pocket(deep_groove, floor_z=FLOOR_THICKNESS, top_z=FLOOR_THICKNESS + 1.6, lead_in=0.0)

    # Finger-pinch scoops on left and right of heatsink
    def pinch_scoops():
        with Locations((xc, y_hs)):
            SlotOverall(hs_w + 3.8, 10.2)

    cut_pocket(pinch_scoops, floor_z=FLOOR_THICKNESS + 5.5, lead_in=0.45)

    # Mild retention snap beads on the neck walls (0.15 mm interference)
    add_vertical_slot_retention_bead(xc + neck_w / 2.0, y_neck, side_sign=+1, z_center=10.5)
    add_vertical_slot_retention_bead(xc - neck_w / 2.0, y_neck, side_sign=-1, z_center=10.5)


def cut_h2c_induction_hotend_vertical(xc, yc, point_down=True):
    """
    Cuts a vertical Right-Hand H2C Induction Hotend slot centered at (xc, yc),
    matching MakerWorld #2106466:
      - Total length clearance: 49.9 mm (49.2 mm nominal + 2*0.35 mm)
      - Top inlet stem pocket (5.55 x 5.8 mm)
      - Upper H2C smart connector / heatsink block (15.15 x 16.35 mm)
      - Left/Right finger-pinch scoops at upper block
      - Cylindrical shaft channel (8.75 mm wide) with 0.15 mm retention beads
      - Bulbous / flared circular induction coil head pocket (Dia 14.20 mm)
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

    cut_pocket(ind_profile, floor_z=FLOOR_THICKNESS + 1.4, lead_in=0.50)

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

    # Finger-pinch scoops on left and right of the upper H2C block
    def ind_pinch():
        with Locations((xc, y_blk)):
            SlotOverall(blk_w + 3.8, 10.2)

    cut_pocket(ind_pinch, floor_z=FLOOR_THICKNESS + 5.5, lead_in=0.45)

    # Mild retention snap beads on neck walls (0.15 mm interference)
    add_vertical_slot_retention_bead(xc + neck_w / 2.0, yc + s * (-1.0), side_sign=+1, z_center=10.5)
    add_vertical_slot_retention_bead(xc - neck_w / 2.0, yc + s * (-1.0), side_sign=-1, z_center=10.5)


def cut_induction_sock_vertical(xc, yc):
    """
    Cuts a form-fitted vertical pocket for the rounded/molded H2C induction thermal cover
    (+0.20 mm snug fit, sits completely flush below the tray rim).
    """
    w_cyl = 11.8 + TOL_SOCK    # 12.00 mm
    l_cyl = 23.5 + TOL_SOCK    # 23.70 mm

    def ind_sock_profile():
        with Locations((xc, yc + 11.2)):
            RectangleRounded(4.6 + TOL_SOCK, 4.2, 0.8)
        with Locations((xc, yc - 0.5)):
            SlotOverall(l_cyl, w_cyl, rotation=90)

    cut_pocket(ind_sock_profile, floor_z=DECK_Z - 13.5, lead_in=0.45)

    def ind_sock_pinch():
        with Locations((xc, yc - 0.5)):
            SlotOverall(w_cyl + 3.2, 8.5)

    cut_pocket(ind_sock_pinch, floor_z=DECK_Z - 8.0, lead_in=0.45)


def cut_wiper_slot_vertical(xc, yc, w=13.6, h=25.5):
    """
    Cuts a dedicated vertical Wiper / Silicone Pad pocket with finger-pinch scoop.
    """
    def wiper_profile():
        with Locations((xc, yc)):
            RectangleRounded(w, h, 2.0)

    cut_pocket(wiper_profile, floor_z=FLOOR_THICKNESS + 1.0, top_z=DECK_Z, lead_in=0.45)

    def wiper_pinch():
        with Locations((xc, yc)):
            SlotOverall(w + 3.4, 8.5)

    cut_pocket(wiper_pinch, floor_z=DECK_Z - 8.0, top_z=DECK_Z, lead_in=0.45)


def build_dual_hotend_tray():
    with BuildPart() as tray:
        # ----------------------------------------------------------------------
        # A. OUTER TRAY BODY WITH PUSH-BUTTON LATCH GAP & SIDE FINGER CUTOUTS
        # ----------------------------------------------------------------------
        sk_outer = make_outer_silhouette()
        extrude(sk_outer, amount=TRAY_Z)

        # Recessed inner deck (1.5 mm below the 2.8 mm thick outer perimeter rim wall,
        # matching MakerWorld #1418034 and #2106466 — no interior side slots, no text)
        with BuildSketch(Plane.XY.offset(DECK_Z)) as sk_deck_recess:
            offset(sk_outer, amount=-2.80)
        extrude(sk_deck_recess.sketch, amount=DECK_RECESS + 0.1, mode=Mode.SUBTRACT)

        # ----------------------------------------------------------------------
        # B. LEFT SECTION (X < 0): 5x LEFT HOTENDS (WITH SILICONE SOCK MOUNTED ON)
        # ----------------------------------------------------------------------
        left_slots = [
            (-59.5, 23.2, True),
            (-35.5, 23.2, True),
            (-11.5, 23.2, True),
            (-47.5, -23.2, False),
            (-23.5, -23.2, False),
        ]
        for xc, yc, p_down in left_slots:
            cut_x2c_sock_on_hotend_vertical(xc, yc, point_down=p_down)

        # ----------------------------------------------------------------------
        # C. RIGHT SECTION (X > 0): 5x RIGHT H2C INDUCTION HOTENDS
        # ----------------------------------------------------------------------
        right_slots = [
            (11.5, 23.2, True),
            (35.5, 23.2, True),
            (59.5, 23.2, True),
            (23.5, -23.2, False),
            (47.5, -23.2, False),
        ]
        for xc, yc, p_down in right_slots:
            cut_h2c_induction_hotend_vertical(xc, yc, point_down=p_down)

        # ----------------------------------------------------------------------
        # D. THREE LOWER DEAD-SPACE POCKETS (OPTION B-2)
        # ----------------------------------------------------------------------
        # 1. Far Bottom-Left (X = -68.5, Y = -29.5): Induction Silicone Sock Pocket
        cut_induction_sock_vertical(-68.5, -29.5)

        # 2. Center above Push-Button Gap (X = 0.0, Y = -22.5): Wiper Slot
        cut_wiper_slot_vertical(0.0, -22.5, w=13.6, h=25.5)

        # 3. Far Bottom-Right (X = +68.5, Y = -29.5): Induction Silicone Sock Pocket
        cut_induction_sock_vertical(68.5, -29.5)

    return tray.part


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    stl_path = os.path.join(out_dir, "andy_dual_hotend_tray.stl")
    step_path = os.path.join(out_dir, "andy_dual_hotend_tray.step")

    print("Building v3.0 (Option B-2) parametric 3D solid...")
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

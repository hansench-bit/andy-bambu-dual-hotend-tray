"""
Parametric CAD Generator for Andy Bambu Toolbox Upper Replacement Tray
Dual-Setup: X2C Standard Finned Hotends (Left) + H2C Induction Hotends (Right)

Deliverables generated:
  1. andy_dual_hotend_tray.stl  (High-resolution manifold mesh for FDM slicing)
  2. andy_dual_hotend_tray.step (Parametric B-Rep STEP model for Bambu Studio / OrcaSlicer)
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
    SlotOverall,
    Text,
    FontStyle,
    extrude,
    loft,
    offset,
    export_stl,
    export_step,
)

# ==============================================================================
# 1. ENGINEERING PARAMETERS & TOLERANCES (mm)
# ==============================================================================

# Outer Envelope & Box Clearance
BOX_INNER_X = 185.00
BOX_INNER_Y = 115.00
OUTER_WALL_OFFSET = 0.40  # -0.40 mm offset from inner box wall per spec

TRAY_X = BOX_INNER_X - 2.0 * OUTER_WALL_OFFSET  # 184.20 mm
TRAY_Y = BOX_INNER_Y - 2.0 * OUTER_WALL_OFFSET  # 114.20 mm
TRAY_Z = 20.00                                  # 20.0 mm total depth (within 18-22 mm spec)
CORNER_RADIUS = 8.00                            # Rounded corner radius matching base shell

# Underside Perimeter Support Lip / Step-Down Rib
# Upper rim overhangs by 1.8 mm around perimeter to rest on the lower tray's ledge;
# 45-degree transition slope ensures 100% support-free FDM printing on build plate.
UPPER_RIM_HEIGHT = 6.00
LOWER_STEP_IN = 1.80
FLOOR_THICKNESS = 2.40
TOP_CLEARANCE = 1.80        # > 1.5 mm minimum top clearance below tray rim

# Fit Tolerances
TOL_HOTEND = 0.35           # +0.35 mm clearance on non-locking hotend dimensions
TOL_SOCK = 0.20             # +0.20 mm snug drop-in fit for flexible silicone socks
TOL_COIL_RELIEF = 0.50      # +0.50 mm extra clearance around H2C induction coil head
LOCK_INTERFERENCE = 0.15    # 0.15 mm retention snap / friction bead interference
TEXT_RELIEF_DEPTH = 0.40    # 0.40 mm debossed relief depth for single/dual layer legibility
CHAMFER_LEAD_IN = 0.85      # 45-degree lead-in depth at pocket mouths


def cut_pocket_with_45deg_lead_in(sketch_fn, floor_z, top_z=TRAY_Z, lead_in=CHAMFER_LEAD_IN):
    """
    Cuts a vertical pocket from floor_z to top_z, plus a 45-degree flared lead-in
    chamfer at the top mouth (from top_z - lead_in to top_z) for bridge/support-free
    printing and smooth tool drop-in.
    """
    with BuildSketch(Plane.XY.offset(floor_z)) as sk_main:
        sketch_fn()
    extrude(sk_main.sketch, amount=(top_z - floor_z) + 0.05, mode=Mode.SUBTRACT)

    with BuildSketch(Plane.XY.offset(top_z - lead_in)) as sk_ch_bot:
        sketch_fn()
    with BuildSketch(Plane.XY.offset(top_z + 0.02)) as sk_ch_top:
        sketch_fn()
        offset(amount=lead_in + 0.02)
    loft([sk_ch_bot.sketch, sk_ch_top.sketch], ruled=True, mode=Mode.SUBTRACT)


def add_retention_bead(x_center, y_wall, side_sign, z_center=11.8):
    """
    Adds a gentle 0.15 mm interference snap/retention bead on a vertical neck wall
    with 45-degree bottom/top draft angles so it prints cleanly without supports.
    side_sign = +1 means wall is on +Y side (bead protrudes in -Y direction).
    side_sign = -1 means wall is on -Y side (bead protrudes in +Y direction).
    """
    bead_len = 4.2
    bead_half_h = 1.2
    with BuildSketch(Plane.XY.offset(z_center - bead_half_h)) as sk_b1:
        with Locations((x_center, y_wall + side_sign * 0.10)):
            RectangleRounded(bead_len, 0.20, 0.06)
    with BuildSketch(Plane.XY.offset(z_center)) as sk_b2:
        with Locations((x_center, y_wall - side_sign * (LOCK_INTERFERENCE / 2.0))):
            RectangleRounded(bead_len, 0.20 + LOCK_INTERFERENCE, 0.06)
    with BuildSketch(Plane.XY.offset(z_center + bead_half_h)) as sk_b3:
        with Locations((x_center, y_wall + side_sign * 0.10)):
            RectangleRounded(bead_len, 0.20, 0.06)
    loft([sk_b1.sketch, sk_b2.sketch, sk_b3.sketch], ruled=True, mode=Mode.ADD)


def build_dual_hotend_tray():
    with BuildPart() as tray:
        # ----------------------------------------------------------------------
        # A. BASE OUTER SHELL WITH SUPPORT-FREE STEPPED PERIMETER LIP
        # ----------------------------------------------------------------------
        lower_h = TRAY_Z - UPPER_RIM_HEIGHT - LOWER_STEP_IN  # 12.2 mm
        with BuildSketch(Plane.XY) as sk_base:
            RectangleRounded(
                TRAY_X - 2 * LOWER_STEP_IN,
                TRAY_Y - 2 * LOWER_STEP_IN,
                CORNER_RADIUS - LOWER_STEP_IN,
            )
        extrude(sk_base.sketch, amount=lower_h)

        # 45-degree outward step-out transition (support-free in FDM)
        with BuildSketch(Plane.XY.offset(lower_h)) as sk_step_b:
            RectangleRounded(
                TRAY_X - 2 * LOWER_STEP_IN,
                TRAY_Y - 2 * LOWER_STEP_IN,
                CORNER_RADIUS - LOWER_STEP_IN,
            )
        with BuildSketch(Plane.XY.offset(lower_h + LOWER_STEP_IN)) as sk_step_t:
            RectangleRounded(TRAY_X, TRAY_Y, CORNER_RADIUS)
        loft([sk_step_b.sketch, sk_step_t.sketch], ruled=True)

        # Upper rim section: Z = 14.0 to 20.0 mm
        with BuildSketch(Plane.XY.offset(TRAY_Z - UPPER_RIM_HEIGHT)) as sk_rim:
            RectangleRounded(TRAY_X, TRAY_Y, CORNER_RADIUS)
        extrude(sk_rim.sketch, amount=UPPER_RIM_HEIGHT)

        # Underside weight-relief recess (leaves a perimeter support foot ring + center rib
        # so weight rests strictly on the box perimeter ledge, never on tools underneath)
        for x_side in [-43.0, 43.0]:
            with BuildSketch(Plane.XY.offset(-0.02)) as sk_ur_b:
                with Locations((x_side, 0)):
                    RectangleRounded(73.0, TRAY_Y - 2 * (LOWER_STEP_IN + 5.0), 4.0)
            with BuildSketch(Plane.XY.offset(0.80)) as sk_ur_t:
                with Locations((x_side, 0)):
                    RectangleRounded(73.0 - 1.6, TRAY_Y - 2 * (LOWER_STEP_IN + 5.0) - 1.6, 3.2)
            loft([sk_ur_b.sketch, sk_ur_t.sketch], ruled=True, mode=Mode.SUBTRACT)

        # ----------------------------------------------------------------------
        # B. SIDE LIFT TABS / FINGER GRASP CUTOUTS (LEFT & RIGHT EXTERIOR RIMS)
        # ----------------------------------------------------------------------
        # Dual semi-circular finger-access cutouts along left (-X) and right (+X) rims
        # with 45-degree lower bevel so they print bridge-free and support-free
        for x_sign in [-1, 1]:
            x_edge = x_sign * (TRAY_X / 2.0)
            with BuildSketch(Plane.XY.offset(TRAY_Z - 10.5)) as sk_lift_b:
                with Locations((x_edge, 0)):
                    SlotOverall(28.0, 9.0, rotation=90)
            with BuildSketch(Plane.XY.offset(TRAY_Z - 7.5)) as sk_lift_m:
                with Locations((x_edge, 0)):
                    SlotOverall(31.0, 12.0, rotation=90)
            loft([sk_lift_b.sketch, sk_lift_m.sketch], ruled=True, mode=Mode.SUBTRACT)
            extrude(sk_lift_m.sketch, amount=8.0, mode=Mode.SUBTRACT)

        # ----------------------------------------------------------------------
        # C. CENTER SPLIT-DECK DIVIDER GROOVE
        # ----------------------------------------------------------------------
        with BuildSketch(Plane.XY.offset(TRAY_Z - 0.6)) as sk_div_b:
            Rectangle(0.8, TRAY_Y - 10.0)
        with BuildSketch(Plane.XY.offset(TRAY_Z + 0.02)) as sk_div_t:
            Rectangle(2.0, TRAY_Y - 8.8)
        loft([sk_div_b.sketch, sk_div_t.sketch], ruled=True, mode=Mode.SUBTRACT)

        # ----------------------------------------------------------------------
        # D. LEFT SECTION: 4x STANDARD / X2C FINNED HOTEND SLOTS
        # ----------------------------------------------------------------------
        # All hotend components sit >= 2.2 mm below Z = 20.0 mm top rim (exceeding 1.5 mm spec).
        # Total slot length = 48.0 mm (47.3 mm nominal + 0.70 mm total axial clearance).
        x2c_slot_ys = [42.0, 27.5, 13.0, -1.5]
        x2c_labels = ["0.2", "0.4", "0.6", "0.8"]

        for idx, y_c in enumerate(x2c_slot_ys):
            neck_w = 7.4 + TOL_HOTEND

            # 1. Contoured Heatsink Fin Cavity (with individual fin grooves)
            def hs_sketch(yc=y_c):
                with Locations((-56.5, yc)):
                    RectangleRounded(17.2 + TOL_HOTEND, 11.2 + TOL_HOTEND, 1.0)
                for fin_i in range(3):
                    fin_x = -61.5 + fin_i * 4.2
                    with Locations((fin_x, yc)):
                        RectangleRounded(2.3, 12.2 + TOL_HOTEND, 0.4)

            cut_pocket_with_45deg_lead_in(hs_sketch, floor_z=FLOOR_THICKNESS + 1.2)

            # 2. Throat / Neck Channel
            def neck_sketch(yc=y_c):
                with Locations((-43.5, yc)):
                    Rectangle(10.0, neck_w)

            cut_pocket_with_45deg_lead_in(neck_sketch, floor_z=FLOOR_THICKNESS + 2.4)

            # 3. Heater Block Cavity
            def hb_sketch(yc=y_c):
                with Locations((-32.0, yc)):
                    RectangleRounded(14.0 + TOL_HOTEND, 11.0 + TOL_HOTEND, 1.0)

            cut_pocket_with_45deg_lead_in(hb_sketch, floor_z=FLOOR_THICKNESS + 1.4)

            # 4. Recessed Nozzle Runout Channel (deepest floor Z = FLOOR_THICKNESS so nozzle
            #    tip hovers with > 1.4 mm clearance above bottom plastic)
            def noz_sketch(yc=y_c):
                with Locations((-20.8, yc)):
                    SlotOverall(9.6, 6.6 + TOL_HOTEND)

            cut_pocket_with_45deg_lead_in(noz_sketch, floor_z=FLOOR_THICKNESS)

            # 5. Neck Locking Tabs / Mild Retention Snap Beads (0.15 mm interference)
            add_retention_bead(-43.5, y_c + neck_w / 2.0, side_sign=+1, z_center=11.5)
            add_retention_bead(-43.5, y_c - neck_w / 2.0, side_sign=-1, z_center=11.5)

            # 6. Debossed Size Indicator ("0.2", "0.4", "0.6", "0.8") at 0.4 mm depth
            with BuildSketch(Plane.XY.offset(TRAY_Z - TEXT_RELIEF_DEPTH)) as sk_txt_l:
                with Locations((-73.8, y_c)):
                    Text(
                        x2c_labels[idx],
                        font_size=5.0,
                        font_style=FontStyle.BOLD,
                        align=(Align.CENTER, Align.CENTER),
                    )
            extrude(sk_txt_l.sketch, amount=TEXT_RELIEF_DEPTH + 0.05, mode=Mode.SUBTRACT)

        # Finger-Pinch Access Scoop across X2C slots
        def x2c_finger_scoop():
            with Locations((-32.0, 20.25)):
                SlotOverall(58.0, 12.0, rotation=90)

        cut_pocket_with_45deg_lead_in(x2c_finger_scoop, floor_z=FLOOR_THICKNESS + 5.5)

        # ----------------------------------------------------------------------
        # E. LEFT LOWER SECTION: 2x FINNED SILICONE SOCK POCKETS + SPARES POCKET
        # ----------------------------------------------------------------------
        sock_x_positions = [-69.0, -48.5]
        sock_y_center = -32.0
        sock_w = 15.6 + TOL_SOCK
        sock_l = 21.8 + TOL_SOCK
        sock_floor_z = TRAY_Z - 14.5  # Socks sit > 2.5 mm below top rim

        for sx in sock_x_positions:
            def sock_sketch(x_pos=sx):
                with Locations((x_pos, sock_y_center)):
                    RectangleRounded(sock_w, sock_l, 1.8)
                    SlotOverall(sock_l + 5.0, 6.8, rotation=90)

            cut_pocket_with_45deg_lead_in(sock_sketch, floor_z=sock_floor_z)

        # Small Spares / Wire Pocket (Left lower-right)
        def spares_sketch():
            with Locations((-21.0, -32.0)):
                RectangleRounded(29.0, 30.0, 3.2)

        cut_pocket_with_45deg_lead_in(spares_sketch, floor_z=FLOOR_THICKNESS + 1.0)

        # ----------------------------------------------------------------------
        # F. RIGHT SECTION: 4x H2C RIGHT-SIDE INDUCTION HOTEND SLOTS
        # ----------------------------------------------------------------------
        # Total slot length clearance = 49.2 mm + 2*0.35 mm = 49.9 mm (~50.1 mm actual).
        # Includes +0.50 mm ceramic/coil relief around the cylindrical induction head
        # and chamfered 45-degree lead-ins on all pockets.
        h2c_slot_ys = [42.0, 27.5, 13.0, -1.5]
        h2c_labels = ["0.2", "0.4", "0.6", "0.8"]

        for idx, y_c in enumerate(h2c_slot_ys):
            collar_w = 11.6 + TOL_HOTEND
            ind_neck_w = 8.0 + TOL_HOTEND
            coil_w = 11.8 + 2 * TOL_COIL_RELIEF  # +0.5 mm radial clearance per side

            # 1. Cylindrical Upper Heatsink / Mounting Collar Cavity
            def ind_collar_sketch(yc=y_c):
                with Locations((57.2, yc)):
                    RectangleRounded(18.0 + TOL_HOTEND, collar_w, 2.2)

            cut_pocket_with_45deg_lead_in(ind_collar_sketch, floor_z=FLOOR_THICKNESS + 1.4)

            # 2. Mid Neck Cradle
            def ind_neck_sketch(yc=y_c):
                with Locations((43.8, yc)):
                    Rectangle(9.6, ind_neck_w)

            cut_pocket_with_45deg_lead_in(ind_neck_sketch, floor_z=FLOOR_THICKNESS + 2.4)

            # 3. Ceramic / Induction Coil Head Relief Cavity (+0.50 mm clearance all around,
            #    floor recessed an extra 0.50 mm below collar cradle to prevent coil abrasion)
            def ind_coil_sketch(yc=y_c):
                with Locations((31.2, yc)):
                    RectangleRounded(16.0 + 2 * TOL_COIL_RELIEF, coil_w, 2.8)

            cut_pocket_with_45deg_lead_in(ind_coil_sketch, floor_z=FLOOR_THICKNESS + 0.5)

            # 4. Nozzle Clearance Pocket with 45-deg Chamfered Lead-In
            def ind_noz_sketch(yc=y_c):
                with Locations((19.8, yc)):
                    SlotOverall(9.4, 6.6 + TOL_HOTEND)

            cut_pocket_with_45deg_lead_in(ind_noz_sketch, floor_z=FLOOR_THICKNESS)

            # 5. Mild Retention Snap Beads on Neck (0.15 mm interference)
            add_retention_bead(43.8, y_c + ind_neck_w / 2.0, side_sign=+1, z_center=11.5)
            add_retention_bead(43.8, y_c - ind_neck_w / 2.0, side_sign=-1, z_center=11.5)

            # 6. Debossed "IND" + Size Indicators at 0.4 mm relief depth
            with BuildSketch(Plane.XY.offset(TRAY_Z - TEXT_RELIEF_DEPTH)) as sk_txt_r:
                with Locations((74.2, y_c)):
                    Text(
                        h2c_labels[idx],
                        font_size=5.0,
                        font_style=FontStyle.BOLD,
                        align=(Align.CENTER, Align.CENTER),
                    )
                with Locations((9.2, y_c)):
                    Text(
                        "IND",
                        font_size=3.6,
                        font_style=FontStyle.BOLD,
                        align=(Align.CENTER, Align.CENTER),
                    )
            extrude(sk_txt_r.sketch, amount=TEXT_RELIEF_DEPTH + 0.05, mode=Mode.SUBTRACT)

        # Finger-Pinch Access Scoop across H2C Induction slots
        def h2c_finger_scoop():
            with Locations((56.0, 20.25)):
                SlotOverall(58.0, 12.0, rotation=90)

        cut_pocket_with_45deg_lead_in(h2c_finger_scoop, floor_z=FLOOR_THICKNESS + 5.5)

        # ----------------------------------------------------------------------
        # G. RIGHT LOWER SECTION: 3x INDUCTION SOCK POCKETS + WIPER/PURGE CUTOUT
        # ----------------------------------------------------------------------
        ind_sock_xs = [14.5, 32.0, 49.5]
        ind_sock_y = -32.0
        ind_sock_w = 13.6 + TOL_SOCK
        ind_sock_l = 21.8 + TOL_SOCK
        ind_sock_floor_z = TRAY_Z - 15.0  # Flush > 2.0 mm below tray top rim

        for isx in ind_sock_xs:
            def ind_sock_sketch(x_pos=isx):
                with Locations((x_pos, ind_sock_y)):
                    SlotOverall(ind_sock_l, ind_sock_w, rotation=90)
                    RectangleRounded(ind_sock_w + 2.2, 6.8, 1.2)

            cut_pocket_with_45deg_lead_in(ind_sock_sketch, floor_z=ind_sock_floor_z)

        # Wiper / Purge Spare Cutout (Right lower-right)
        def wiper_sketch():
            with Locations((71.2, -32.0)):
                RectangleRounded(21.5, 30.0, 3.0)

        cut_pocket_with_45deg_lead_in(wiper_sketch, floor_z=FLOOR_THICKNESS + 1.0)

        # ----------------------------------------------------------------------
        # H. DEBOSSED SECTION HEADERS & POCKET LABELS (0.40 mm relief depth)
        # ----------------------------------------------------------------------
        with BuildSketch(Plane.XY.offset(TRAY_Z - TEXT_RELIEF_DEPTH)) as sk_hdr:
            with Locations((-42.0, 52.8)):
                Text("X2C STANDARD", font_size=4.2, font_style=FontStyle.BOLD)
            with Locations((42.0, 52.8)):
                Text("H2C INDUCTION", font_size=4.2, font_style=FontStyle.BOLD)
            with Locations((-58.8, -11.5)):
                Text("SOCKS", font_size=3.5, font_style=FontStyle.BOLD)
            with Locations((-21.0, -11.5)):
                Text("SPARES", font_size=3.5, font_style=FontStyle.BOLD)
            with Locations((32.0, -11.5)):
                Text("IND SOCKS", font_size=3.5, font_style=FontStyle.BOLD)
            with Locations((71.2, -11.5)):
                Text("WIPER", font_size=3.5, font_style=FontStyle.BOLD)
        extrude(sk_hdr.sketch, amount=TEXT_RELIEF_DEPTH + 0.05, mode=Mode.SUBTRACT)

    return tray.part


if __name__ == "__main__":
    out_dir = os.path.dirname(os.path.abspath(__file__))
    stl_path = os.path.join(out_dir, "andy_dual_hotend_tray.stl")
    step_path = os.path.join(out_dir, "andy_dual_hotend_tray.step")

    print("Building parametric 3D solid via build123d (OpenCASCADE)...")
    part = build_dual_hotend_tray()

    print(f"Exporting STEP to: {step_path}")
    export_step(part, step_path)

    print(f"Exporting high-resolution STL to: {stl_path}")
    export_stl(part, stl_path, tolerance=0.01, angular_tolerance=0.1)

    # Validate mesh with trimesh
    mesh = trimesh.load(stl_path)
    extents = mesh.extents
    print("=== MESH & GEOMETRY VERIFICATION ===")
    print(f"Is Watertight / Manifold : {mesh.is_watertight}")
    print(f"Is Winding Consistent    : {mesh.is_winding_consistent}")
    print(f"Euler Number             : {mesh.euler_number}")
    print(f"Vertices / Faces         : {len(mesh.vertices):,} / {len(mesh.faces):,}")
    print(f"Bounding Box Extents (mm): X={extents[0]:.2f}, Y={extents[1]:.2f}, Z={extents[2]:.2f}")
    print(f"Solid Volume (cm^3)      : {mesh.volume / 1000.0:.2f} cm^3")

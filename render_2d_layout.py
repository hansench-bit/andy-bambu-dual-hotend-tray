"""
Generates a 2D Top-View Engineering Layout Blueprint for OPTION B (10 Hotends Total:
5 Left w/ Silicone Sock Mounted ON + 5 Right H2C Induction), with:
  - ZERO text/size labels written on the tray surface
  - All 10 hotend spots preserved (3 top + 2 interleaved bottom on EACH side)
  - The 3 dead spaces (Far Bottom-Left, Center above Push-Button Gap, and Far Bottom-Right)
    filled with Induction Silicone Socks and Wiper pockets.
"""

import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPolygon
from build123d import (
    BuildSketch,
    Plane,
    Locations,
    Mode,
    Rectangle,
    RectangleRounded,
    Circle,
    SlotOverall,
    Polygon,
    offset,
)

TRAY_X = 184.20
TRAY_Y = 114.20
CORNER_RADIUS = 8.00
LATCH_GAP_W = 19.50
LATCH_GAP_D = 15.60
LATCH_CORNER_R = 2.50
SIDE_RECESS_SPAN_Y = 72.00
SIDE_RECESS_DEPTH_X = 6.80

TOL_HOTEND = 0.35
TOL_SOCK = 0.20
TOL_COIL_RELIEF = 0.50


def sketch_to_mpl_polygons(sk):
    loops = []
    for face in sk.faces():
        outer_wire = face.outer_wire()
        sampled = []
        for edge in outer_wire.edges():
            for t in np.linspace(0.0, 1.0, 24, endpoint=False):
                p = edge.position_at(t)
                sampled.append((p.X, p.Y))
        loops.append(np.array(sampled))
    return loops


def make_outer_sketch():
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


def make_x2c_sock_on_slot_sketch(xc, yc, point_down=True):
    """
    Left-Hand (X2C / H2D Standard Finned) Hotend WITH the Silicone Sock mounted ON it.
    """
    s = -1.0 if point_down else 1.0
    hs_w = 16.2 + TOL_HOTEND
    hs_l = 15.4 + TOL_HOTEND
    neck_w = 9.0 + TOL_HOTEND
    sock_w = 16.4 + TOL_HOTEND
    sock_l = 14.2 + TOL_HOTEND

    y_stem = yc + s * (-21.8)
    y_hs = yc + s * (-12.0)
    y_neck = yc + s * (-2.0)
    y_sock = yc + s * (6.8)

    with BuildSketch(Plane.XY) as sk_body:
        with Locations((xc, y_stem)):
            RectangleRounded(5.2 + TOL_HOTEND, 5.8, 0.9)
        with Locations((xc, y_hs)):
            RectangleRounded(hs_w, hs_l, 1.2)
        with Locations((xc, y_neck)):
            Rectangle(neck_w, 5.5)
        with Locations((xc, y_sock)):
            RectangleRounded(sock_w, sock_l, 1.5)
        tip_pts = [
            (xc - 6.6, yc + s * 13.0),
            (xc + 6.6, yc + s * 13.0),
            (xc + 4.8, yc + s * 19.5),
            (xc, yc + s * 24.3),
            (xc - 4.8, yc + s * 19.5),
        ]
        Polygon(*tip_pts)

    with BuildSketch(Plane.XY) as sk_pinch:
        with Locations((xc, y_hs)):
            SlotOverall(hs_w + 3.8, 10.2)

    return sk_body.sketch, sk_pinch.sketch


def make_h2c_induction_slot_sketch(xc, yc, point_down=True):
    """
    Right-Hand H2C Induction Hotend slot.
    """
    s = -1.0 if point_down else 1.0
    blk_w = 14.8 + TOL_HOTEND
    blk_l = 16.0 + TOL_HOTEND
    neck_w = 8.4 + TOL_HOTEND
    coil_dia = 13.2 + 2.0 * TOL_COIL_RELIEF

    y_stem = yc + s * (-22.2)
    y_blk = yc + s * (-12.0)
    y_neck = yc + s * (1.5)
    y_coil = yc + s * (15.2)

    with BuildSketch(Plane.XY) as sk_body:
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

    with BuildSketch(Plane.XY) as sk_pinch:
        with Locations((xc, y_blk)):
            SlotOverall(blk_w + 3.8, 10.2)

    return sk_body.sketch, sk_pinch.sketch


def make_induction_sock_sketch(xc, yc, rot=0):
    w_cyl = 11.8 + TOL_SOCK
    l_cyl = 23.5 + TOL_SOCK
    with BuildSketch(Plane.XY) as sk_body:
        with Locations((xc, yc + 11.2)):
            RectangleRounded(4.6 + TOL_SOCK, 4.2, 0.8)
        with Locations((xc, yc - 0.5)):
            SlotOverall(l_cyl, w_cyl, rotation=90)
    with BuildSketch(Plane.XY) as sk_pinch:
        with Locations((xc, yc - 0.5)):
            SlotOverall(w_cyl + 3.2, 8.5)
    return sk_body.sketch, sk_pinch.sketch


def make_wiper_pocket_sketch(xc, yc, w=14.2, h=25.0):
    with BuildSketch(Plane.XY) as sk_body:
        with Locations((xc, yc)):
            RectangleRounded(w, h, 2.0)
    with BuildSketch(Plane.XY) as sk_pinch:
        with Locations((xc, yc)):
            SlotOverall(w + 3.4, 8.5)
    return sk_body.sketch, sk_pinch.sketch


def draw_option_b_panel(ax, title, subtitle, mode="B1"):
    ax.set_facecolor("#0f172a")
    sk_outer = make_outer_sketch()
    with BuildSketch(Plane.XY) as sk_inner:
        offset(sk_outer, amount=-2.80)

    # Outer rim wall
    for pts in sketch_to_mpl_polygons(sk_outer):
        ax.add_patch(MplPolygon(pts, closed=True, facecolor="#cbd5e1", edgecolor="#f8fafc", linewidth=1.4, zorder=1))

    # Recessed inner deck (ZERO engraved text)
    for pts in sketch_to_mpl_polygons(sk_inner):
        ax.add_patch(MplPolygon(pts, closed=True, facecolor="#334155", edgecolor="#64748b", linewidth=0.9, zorder=2))

    # 5x Left-Hand (Sock-On) Hotends (3 Top pointing DOWN + 2 Interleaved Bottom pointing UP)
    left_slots = [
        (-59.5, 23.2, True, "L1"),
        (-35.5, 23.2, True, "L2"),
        (-11.5, 23.2, True, "L3"),
        (-47.5, -23.2, False, "L4"),
        (-23.5, -23.2, False, "L5"),
    ]
    for xc, yc, p_down, tag in left_slots:
        sk_b, sk_p = make_x2c_sock_on_slot_sketch(xc, yc, point_down=p_down)
        for pts in sketch_to_mpl_polygons(sk_p):
            ax.add_patch(MplPolygon(pts, closed=True, facecolor="#1e40af", edgecolor="#60a5fa", linewidth=0.8, linestyle="--", zorder=3))
        for pts in sketch_to_mpl_polygons(sk_b):
            ax.add_patch(MplPolygon(pts, closed=True, facecolor="#0284c7", edgecolor="#bae6fd", linewidth=1.1, zorder=4))
        s = -1.0 if p_down else 1.0
        ax.text(xc, yc + s * (-12.0), f"LEFT\n({tag})", color="#e0f2fe", fontsize=5.2, fontweight="bold", ha="center", va="center", zorder=6)
        ax.text(xc, yc + s * 6.8, "SOCK\nON", color="#bae6fd", fontsize=5.0, fontweight="bold", ha="center", va="center", zorder=6)

    # 5x Right-Hand (H2C Induction) Hotends (3 Top pointing DOWN + 2 Interleaved Bottom pointing UP)
    right_slots = [
        (11.5, 23.2, True, "R1"),
        (35.5, 23.2, True, "R2"),
        (59.5, 23.2, True, "R3"),
        (23.5, -23.2, False, "R4"),
        (47.5, -23.2, False, "R5"),
    ]
    for xc, yc, p_down, tag in right_slots:
        sk_b, sk_p = make_h2c_induction_slot_sketch(xc, yc, point_down=p_down)
        for pts in sketch_to_mpl_polygons(sk_p):
            ax.add_patch(MplPolygon(pts, closed=True, facecolor="#065f46", edgecolor="#34d399", linewidth=0.8, linestyle="--", zorder=3))
        for pts in sketch_to_mpl_polygons(sk_b):
            ax.add_patch(MplPolygon(pts, closed=True, facecolor="#0d9488", edgecolor="#99f6e4", linewidth=1.1, zorder=4))
        s = -1.0 if p_down else 1.0
        ax.text(xc, yc + s * (-12.0), f"H2C IND\n({tag})", color="#ccfbf1", fontsize=5.0, fontweight="bold", ha="center", va="center", zorder=6)
        ax.text(xc, yc + s * 15.2, "COIL", color="#99f6e4", fontsize=4.8, fontweight="bold", ha="center", va="center", zorder=6)

    # 1. MIDDLE DEAD SPACE (Directly above the Push-Button Gap at X = 0.0, Y = -22.5):
    # Wiper / Silicone Pad Pocket (13.6 mm wide x 25.5 mm tall)
    sk_wb, sk_wp = make_wiper_pocket_sketch(0.0, -22.5, w=13.6, h=25.5)
    for pts in sketch_to_mpl_polygons(sk_wp):
        ax.add_patch(MplPolygon(pts, closed=True, facecolor="#78350f", edgecolor="#fbbf24", linewidth=0.8, linestyle="--", zorder=3))
    for pts in sketch_to_mpl_polygons(sk_wb):
        ax.add_patch(MplPolygon(pts, closed=True, facecolor="#d97706", edgecolor="#fde68a", linewidth=1.1, zorder=4))
    ax.text(0.0, -22.5, "WIPER\nSLOT", color="#fef3c7", fontsize=5.3, fontweight="bold", ha="center", va="center", zorder=6)

    # 2. FAR BOTTOM-RIGHT DEAD SPACE (X = +68.5, Y = -28.0):
    # Holds 1x Induction Silicone Sock (+1x upper mini wiper/sock pocket if mode=="B2")
    sk_rb, sk_rp = make_induction_sock_sketch(68.5, -29.5)
    for pts in sketch_to_mpl_polygons(sk_rp):
        ax.add_patch(MplPolygon(pts, closed=True, facecolor="#3b0764", edgecolor="#c084fc", linewidth=0.8, linestyle="--", zorder=3))
    for pts in sketch_to_mpl_polygons(sk_rb):
        ax.add_patch(MplPolygon(pts, closed=True, facecolor="#7e22ce", edgecolor="#e9d5ff", linewidth=1.1, zorder=4))
    ax.text(68.5, -29.5, "IND\nSOCK", color="#f3e8ff", fontsize=5.2, fontweight="bold", ha="center", va="center", zorder=6)

    # 3. FAR BOTTOM-LEFT DEAD SPACE (X = -68.5, Y = -29.5):
    if mode == "B1":
        # B1: Far Bottom-Left = Wiper Slot (-68.5), Center = Wiper Slot (0.0), Far Bottom-Right = Ind Sock (+68.5)
        sk_lb, sk_lp = make_wiper_pocket_sketch(-68.5, -28.5, w=13.8, h=26.5)
        for pts in sketch_to_mpl_polygons(sk_lp):
            ax.add_patch(MplPolygon(pts, closed=True, facecolor="#78350f", edgecolor="#fbbf24", linewidth=0.8, linestyle="--", zorder=3))
        for pts in sketch_to_mpl_polygons(sk_lb):
            ax.add_patch(MplPolygon(pts, closed=True, facecolor="#d97706", edgecolor="#fde68a", linewidth=1.1, zorder=4))
        ax.text(-68.5, -28.5, "WIPER\nSLOT", color="#fef3c7", fontsize=5.2, fontweight="bold", ha="center", va="center", zorder=6)
    else:
        # B2: Far Bottom-Left = Ind Sock (-68.5), Center = Wiper Slot (0.0), Far Bottom-Right = Ind Sock (+68.5)
        sk_lb, sk_lp = make_induction_sock_sketch(-68.5, -29.5)
        for pts in sketch_to_mpl_polygons(sk_lp):
            ax.add_patch(MplPolygon(pts, closed=True, facecolor="#3b0764", edgecolor="#c084fc", linewidth=0.8, linestyle="--", zorder=3))
        for pts in sketch_to_mpl_polygons(sk_lb):
            ax.add_patch(MplPolygon(pts, closed=True, facecolor="#7e22ce", edgecolor="#e9d5ff", linewidth=1.1, zorder=4))
        ax.text(-68.5, -29.5, "IND\nSOCK", color="#f3e8ff", fontsize=5.2, fontweight="bold", ha="center", va="center", zorder=6)

    ax.text(0, -49.0, "PUSH-BUTTON\nGAP", color="#f87171", fontsize=6.5, fontweight="bold", ha="center", va="center", zorder=6)

    ax.set_xlim(-100, 100)
    ax.set_ylim(-64, 62)
    ax.set_aspect("equal")
    ax.set_title(f"{title}\n{subtitle}", color="#f8fafc", fontsize=10.0, fontweight="bold", pad=8)
    ax.tick_params(colors="#94a3b8", labelsize=7)
    ax.grid(True, color="#1e293b", linestyle="-", linewidth=0.5, zorder=0)


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    png_path = os.path.join(out_dir, "2d_top_layout_options.png")
    artifact_png = r"C:\Users\hanse\.gemini\antigravity\brain\8625c4fe-4873-430f-bbc8-dd5837b36511\2d_top_layout_options.png"

    fig, axes = plt.subplots(1, 2, figsize=(16, 7.2), dpi=180, facecolor="#0f172a")

    draw_option_b_panel(
        axes[0],
        "OPTION B-1: Full 10 Hotends (5 Left Sock-On + 5 Right H2C Ind) + 2 Wipers + 1 Ind Sock",
        "No engraved text • Bottom-Left: Wiper • Center: Wiper • Bottom-Right: Induction Sock",
        mode="B1",
    )

    draw_option_b_panel(
        axes[1],
        "OPTION B-2: Full 10 Hotends (5 Left Sock-On + 5 Right H2C Ind) + 2 Ind Socks + 1 Center Wiper",
        "No engraved text • Bottom-Left: Induction Sock • Center: Wiper • Bottom-Right: Induction Sock",
        mode="B2",
    )

    plt.suptitle(
        "Option B (Full 10 Hotends Preserved) — No Text • Dead Spaces Filled w/ Induction Socks & Wipers",
        color="#f8fafc",
        fontsize=12.8,
        fontweight="bold",
        y=0.97,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(png_path, dpi=180, facecolor="#0f172a")
    plt.savefig(artifact_png, dpi=180, facecolor="#0f172a")
    print(f"Saved Option B 2D layout preview to: {png_path}")


if __name__ == "__main__":
    main()

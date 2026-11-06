"""
Generates the v4.0 2D Top-View Engineering Layout & MakerWorld #2106466 Fit Verification Diagram.
Plots:
  1. Full v4.0 Top-View Engineering Blueprint (184.2 x 114.2 mm) with true physical outlines
     of the Bambu H2D 0.2 Finned Hotend and H2C 0.4 Induction Hotend superimposed inside the pockets.
  2. Zoomed 1:1 Dimensioned Detail of Left-Hand H2D Finned Slot (v3.0 vs v4.0 #2106466).
  3. Zoomed 1:1 Dimensioned Detail of Right-Hand H2C Induction Slot (v3.0 vs v4.0 #2106466).
"""

import os
import shutil
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import shapely.geometry as sg
import shapely.ops as so
import generate_tray as gt


def plot_shapely_poly(ax, poly, facecolor, edgecolor, lw=1.2, alpha=1.0, ls="-", zorder=2):
    if poly.is_empty:
        return
    polys = [poly] if isinstance(poly, sg.Polygon) else [g for g in poly.geoms if isinstance(g, sg.Polygon)]
    for p in polys:
        xy = np.array(p.exterior.coords)
        patch = patches.Polygon(
            xy,
            closed=True,
            facecolor=facecolor,
            edgecolor=edgecolor,
            linewidth=lw,
            linestyle=ls,
            alpha=alpha,
            zorder=zorder,
        )
        ax.add_patch(patch)


def get_physical_h2d_nozzle_poly(xc, y_origin, point_down=True):
    """True physical silhouette of the Bambu H2D/H2C Left-Hand Finned Hotend (53.8 mm long, 18.2 mm wide)."""
    s = -1.0 if point_down else 1.0

    def y_at(d):
        return y_origin + s * d

    # Offset +0.8 mm from pocket top so it sits centered in the pocket
    p_boss = gt.rounded_rect(xc, y_at(0.8 + 1.1), 4.5, 2.2, 0.4)
    p_fins = gt.rounded_rect(xc, y_at(0.8 + 2.2 + 10.8), 18.2, 21.6, 0.3)
    p_block = gt.rounded_rect(xc, y_at(0.8 + 23.8 + 13.0), 11.0, 26.0, 0.2)
    p_tip = sg.Polygon([
        (xc - 5.5, y_at(0.8 + 49.8)),
        (xc + 5.5, y_at(0.8 + 49.8)),
        (xc, y_at(0.8 + 53.8)),
    ])
    return so.unary_union([p_boss, p_fins, p_block, p_tip])


def get_physical_h2c_nozzle_poly(xc, y_origin, point_down=True):
    """True physical silhouette of the Bambu H2C Right-Hand Induction Hotend (55.9 mm long, 18.0 mm wide fins)."""
    s = -1.0 if point_down else 1.0

    def y_at(d):
        return y_origin + s * d

    p_cap = gt.rounded_rect(xc, y_at(0.8 + 1.2), 6.5, 2.4, 0.4)
    p_neck = gt.rounded_rect(xc, y_at(0.8 + 3.9), 3.8, 3.2, 0.2)
    p_hs_up = gt.rounded_rect(xc, y_at(0.8 + 5.5 + 4.0), 14.4, 8.0, 0.3)
    p_hs_lo = gt.rounded_rect(xc, y_at(0.8 + 13.5 + 5.0), 18.0, 10.0, 0.3)
    p_shaft = gt.rounded_rect(xc, y_at(0.8 + 23.5 + 9.5), 8.5, 19.0, 0.2)
    p_head = sg.Point(xc, y_at(0.8 + 47.2)).buffer(13.8 / 2.0, quad_segs=32)
    p_tip = sg.Polygon([
        (xc - 4.2, y_at(0.8 + 51.2)),
        (xc + 4.2, y_at(0.8 + 51.2)),
        (xc, y_at(0.8 + 55.9)),
    ])
    return so.unary_union([p_cap, p_neck, p_hs_up, p_hs_lo, p_shaft, p_head, p_tip])


def render_layout():
    fig = plt.figure(figsize=(20, 11), facecolor="#0f172a")
    gs = fig.add_gridspec(1, 3, width_ratios=[2.2, 1.0, 1.0], wspace=0.18)

    # --------------------------------------------------------------------------
    # PANEL 1: FULL 2D TOP-VIEW BLUEPRINT (v4.0 — MakerWorld #2106466 Dimensions)
    # --------------------------------------------------------------------------
    ax = fig.add_subplot(gs[0])
    ax.set_facecolor("#0f172a")

    outer_poly = gt.make_outer_silhouette_poly()
    inner_deck = outer_poly.buffer(-gt.RIM_WALL, quad_segs=24)
    plot_shapely_poly(ax, outer_poly, "#334155", "#94a3b8", lw=2.0, zorder=1)
    plot_shapely_poly(ax, inner_deck, "#1e293b", "#64748b", lw=1.2, zorder=2)

    # Left H2D slots
    for xc, y0, p_down in gt.LEFT_SLOTS:
        p_main, p_ovh, p_cradle, p_pinch = gt.get_h2d_finned_hotend_polys(xc, y0, point_down=p_down)
        plot_shapely_poly(ax, p_pinch, "#1e3a5f", "#38bdf8", lw=0.8, ls="--", zorder=3)
        plot_shapely_poly(ax, so.unary_union([p_main, p_ovh]), "#0284c7", "#e0f2fe", lw=1.3, zorder=4)
        plot_shapely_poly(ax, p_cradle, "#0369a1", "#7dd3fc", lw=0.7, zorder=5)
        noz = get_physical_h2d_nozzle_poly(xc, y0, point_down=p_down)
        plot_shapely_poly(ax, noz, "none", "#facc15", lw=1.1, ls=":", zorder=6)

    # Right H2C slots
    for xc, y0, p_down in gt.RIGHT_SLOTS:
        p_main, p_cradle, p_pinch = gt.get_h2c_induction_hotend_polys(xc, y0, point_down=p_down)
        plot_shapely_poly(ax, p_pinch, "#14532d", "#4ade80", lw=0.8, ls="--", zorder=3)
        plot_shapely_poly(ax, p_main, "#059669", "#d1fae5", lw=1.3, zorder=4)
        plot_shapely_poly(ax, p_cradle, "#065f46", "#6ee7b7", lw=0.7, zorder=5)
        noz = get_physical_h2c_nozzle_poly(xc, y0, point_down=p_down)
        plot_shapely_poly(ax, noz, "none", "#facc15", lw=1.1, ls=":", zorder=6)

    # 2x Induction Socks + 1x Center Wiper
    for xc, yc in gt.SOCK_SLOTS:
        p_main, p_pinch = gt.get_induction_sock_polys(xc, yc)
        plot_shapely_poly(ax, p_pinch, "#3b0764", "#c084fc", lw=0.8, ls="--", zorder=3)
        plot_shapely_poly(ax, p_main, "#7e22ce", "#f3e8ff", lw=1.2, zorder=4)

    wx, wy, ww, wh = gt.WIPER_SLOT
    p_wmain, p_wpinch = gt.get_wiper_slot_polys(wx, wy, ww, wh)
    plot_shapely_poly(ax, p_wpinch, "#7c2d12", "#fb923c", lw=0.8, ls="--", zorder=3)
    plot_shapely_poly(ax, p_wmain, "#ea580c", "#ffedd5", lw=1.2, zorder=4)

    ax.set_xlim(-100, 100)
    ax.set_ylim(-66, 66)
    ax.set_aspect("equal")
    ax.grid(True, color="#334155", alpha=0.5, lw=0.6)
    ax.tick_params(colors="#cbd5e1", labelsize=8)
    ax.set_title(
        "v4.0 Top-View Engineering Blueprint (MakerWorld #2106466 Dimensions)\n"
        "Yellow Dotted = Actual Physical Nozzle Silhouette Inside Pocket",
        color="#f8fafc",
        fontsize=11,
        fontweight="bold",
        pad=10,
    )

    # --------------------------------------------------------------------------
    # PANEL 2: LEFT-HAND H2D FINNED SLOT DETAIL (v4.0 vs Physical Nozzle & v3.0)
    # --------------------------------------------------------------------------
    ax2 = fig.add_subplot(gs[1])
    ax2.set_facecolor("#0f172a")
    p_main, p_ovh, p_cradle, p_pinch = gt.get_h2d_finned_hotend_polys(0.0, 28.2, point_down=True)
    plot_shapely_poly(ax2, p_pinch, "#1e3a5f", "#38bdf8", lw=1.0, ls="--", zorder=2)
    plot_shapely_poly(ax2, so.unary_union([p_main, p_ovh]), "#0284c7", "#ffffff", lw=1.8, zorder=3)
    noz_h2d = get_physical_h2d_nozzle_poly(0.0, 28.2, point_down=True)
    plot_shapely_poly(ax2, noz_h2d, "#facc15", "#fef08a", lw=1.5, alpha=0.35, zorder=4)

    ax2.text(0, 29.8, "Inlet Notch: 7.2 x 3.2 mm\n(Boss = 4.5 x 2.2 mm)", color="#f8fafc", ha="center", fontsize=8)
    ax2.text(0, 14.5, "Heatsink Cavity:\n19.6 mm W x 22.8 mm L\n(Fins = 18.2 x 21.6 mm)", color="#ffffff", ha="center", fontsize=8.5, fontweight="bold")
    ax2.text(0, -8.0, "Heater Block Channel:\n12.0 mm W (Block = 11.0 mm)\nTotal Slot L = 56.4 mm\n(Nozzle L = 53.8 mm)", color="#f8fafc", ha="center", fontsize=8)
    ax2.set_xlim(-16, 16)
    ax2.set_ylim(-34, 35)
    ax2.set_aspect("equal")
    ax2.grid(True, color="#334155", alpha=0.5, lw=0.6)
    ax2.tick_params(colors="#cbd5e1", labelsize=8)
    ax2.set_title("Left-Hand H2D Slot (56.4 mm)\n+1.4 mm Fin Width & +2.6 mm Length Clearance", color="#38bdf8", fontsize=10, fontweight="bold")

    # --------------------------------------------------------------------------
    # PANEL 3: RIGHT-HAND H2C INDUCTION SLOT DETAIL (v4.0 vs Physical Nozzle)
    # --------------------------------------------------------------------------
    ax3 = fig.add_subplot(gs[2])
    ax3.set_facecolor("#0f172a")
    p_main, p_cradle, p_pinch = gt.get_h2c_induction_hotend_polys(0.0, 28.8, point_down=True)
    plot_shapely_poly(ax3, p_pinch, "#14532d", "#4ade80", lw=1.0, ls="--", zorder=2)
    plot_shapely_poly(ax3, p_main, "#059669", "#ffffff", lw=1.8, zorder=3)
    noz_h2c = get_physical_h2c_nozzle_poly(0.0, 28.8, point_down=True)
    plot_shapely_poly(ax3, noz_h2c, "#facc15", "#fef08a", lw=1.5, alpha=0.35, zorder=4)

    ax3.text(0, 30.2, "Mushroom Pin: 8.6 x 6.2 mm\n(Cap = 6.5 x 5.5 mm)", color="#f8fafc", ha="center", fontsize=8)
    ax3.text(0, 18.2, "Upper Step: 15.8 x 8.0 mm\n(Block = 14.4 mm W)", color="#ffffff", ha="center", fontsize=8)
    ax3.text(0, 9.0, "4-Fin Step: 19.2 x 11.0 mm\n('0.4' Fins = 18.0 mm W)", color="#ffffff", ha="center", fontsize=8.5, fontweight="bold")
    ax3.text(0, -7.5, "Shaft: 9.8 mm W\n(Tube = 8.5 mm Dia)", color="#f8fafc", ha="center", fontsize=8)
    ax3.text(0, -20.0, "Round Head: Dia 14.8 mm\n(Head = 13.8 mm Dia)\nTotal L = 57.6 mm", color="#ffffff", ha="center", fontsize=8, fontweight="bold")
    ax3.set_xlim(-16, 16)
    ax3.set_ylim(-34, 35)
    ax3.set_aspect("equal")
    ax3.grid(True, color="#334155", alpha=0.5, lw=0.6)
    ax3.tick_params(colors="#cbd5e1", labelsize=8)
    ax3.set_title("Right-Hand H2C Slot (57.6 mm)\nStepped 15.8 / 19.2 mm Heatsink + 14.8 mm Head", color="#4ade80", fontsize=10, fontweight="bold")

    out_dir = os.path.dirname(os.path.abspath(__file__))
    out_path = os.path.join(out_dir, "2d_top_layout_options.png")
    plt.savefig(out_path, dpi=180, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)

    brain_path = r"C:\Users\hanse\.gemini\antigravity\brain\8625c4fe-4873-430f-bbc8-dd5837b36511\2d_top_layout_options.png"
    shutil.copyfile(out_path, brain_path)
    print(f"Saved 2D layout & fit diagram to: {out_path}")


if __name__ == "__main__":
    render_layout()

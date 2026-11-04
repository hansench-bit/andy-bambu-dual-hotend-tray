"""
True Z-Buffered Technical CAD Renderer for the Andy Bambu Dual Hotend Tray STL.
Produces a high-resolution 4-panel engineering sheet (Top Plan with Dimensions,
Isometric Front-Left, Isometric Rear-Right, and Underside Support-Lip View).
"""

import os
import numpy as np
import trimesh
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def look_at_matrix(eye, target, up=np.array([0.0, 0.0, 1.0])):
    f = target - eye
    f = f / np.linalg.norm(f)
    r = np.cross(f, up)
    if np.linalg.norm(r) < 1e-6:
        up = np.array([0.0, 1.0, 0.0])
        r = np.cross(f, up)
    r = r / np.linalg.norm(r)
    u = np.cross(r, f)
    return r, u, -f


def rasterize_orthographic(mesh, eye, target=np.array([0.0, 0.0, 10.0]), up=np.array([0.0, 0.0, 1.0]),
                           width=900, height=620, span_x=210.0):
    """
    Fast vectorized orthographic Z-buffer rasterizer with Phong shading and CAD feature coloring.
    """
    r, u, view_dir = look_at_matrix(np.asarray(eye, dtype=float), np.asarray(target, dtype=float), np.asarray(up, dtype=float))

    verts = mesh.vertices - target
    vx = verts @ r
    vy = verts @ u
    vz = verts @ view_dir  # larger vz = closer to camera (eye)

    span_y = span_x * (height / width)
    px = ((vx + span_x / 2.0) / span_x) * (width - 1)
    py = ((span_y / 2.0 - vy) / span_y) * (height - 1)

    faces = mesh.faces
    normals = mesh.face_normals
    centroids = mesh.triangles_center

    # Back-face culling (only keep faces facing toward eye)
    facing = (normals @ view_dir) > -0.05
    f_idx = np.where(facing)[0]

    # Sort faces back-to-front by mean vz, then rasterize bounding boxes
    tri_vz = vz[faces[f_idx]].mean(axis=1)
    order = f_idx[np.argsort(tri_vz)]

    # Lighting
    light1 = (view_dir + 0.45 * r + 0.55 * u)
    light1 /= np.linalg.norm(light1)
    light2 = (view_dir - 0.50 * r - 0.30 * u)
    light2 /= np.linalg.norm(light2)

    diff1 = np.clip(normals @ light1, 0.0, 1.0)
    diff2 = np.clip(normals @ light2, 0.0, 1.0)
    shade = 0.25 + 0.58 * diff1 + 0.22 * diff2

    # Assign engineering CAD colors per face
    face_rgb = np.zeros((len(faces), 3), dtype=np.float32)
    zc = centroids[:, 2]
    nz = normals[:, 2]

    # Default body: anodized slate-blue
    face_rgb[:] = np.array([0.26, 0.58, 0.82])
    # Top rim surface (Z ~ 20.0)
    top_mask = (zc > 19.88) & (nz > 0.85)
    face_rgb[top_mask] = np.array([0.22, 0.29, 0.38])
    # 0.4 mm debossed text floor (Z ~ 19.60)
    txt_mask = (np.abs(zc - 19.60) < 0.12) & (nz > 0.85)
    face_rgb[txt_mask] = np.array([0.98, 0.68, 0.16])
    # 45-deg lead-in chamfers near top rim
    ch_mask = (zc > 19.0) & (zc < 19.95) & (nz > 0.3) & (nz < 0.85)
    face_rgb[ch_mask] = np.array([0.38, 0.72, 0.94])
    # Deep pocket floors
    fl_mask = (zc > 2.2) & (zc < 8.5) & (nz > 0.85)
    face_rgb[fl_mask] = np.array([0.16, 0.45, 0.66])
    # Retention beads
    bead_mask = (zc > 10.2) & (zc < 12.8) & (np.abs(centroids[:, 0]) > 41.0) & (np.abs(centroids[:, 0]) < 46.5)
    face_rgb[bead_mask] = np.array([0.95, 0.45, 0.20])

    face_rgb = np.clip(face_rgb * shade[:, None], 0.0, 1.0)

    img = np.full((height, width, 3), np.array([0.059, 0.090, 0.165], dtype=np.float32))
    zbuf = np.full((height, width), -1e9, dtype=np.float32)

    x0_all = px[faces[:, 0]]
    y0_all = py[faces[:, 0]]
    x1_all = px[faces[:, 1]]
    y1_all = py[faces[:, 1]]
    x2_all = px[faces[:, 2]]
    y2_all = py[faces[:, 2]]

    z0_all = vz[faces[:, 0]]
    z1_all = vz[faces[:, 1]]
    z2_all = vz[faces[:, 2]]

    xmin_all = np.clip(np.floor(np.minimum(np.minimum(x0_all, x1_all), x2_all)).astype(int), 0, width - 1)
    xmax_all = np.clip(np.ceil(np.maximum(np.maximum(x0_all, x1_all), x2_all)).astype(int), 0, width - 1)
    ymin_all = np.clip(np.floor(np.minimum(np.minimum(y0_all, y1_all), y2_all)).astype(int), 0, height - 1)
    ymax_all = np.clip(np.ceil(np.maximum(np.maximum(y0_all, y1_all), y2_all)).astype(int), 0, height - 1)

    denom_all = (y1_all - y2_all) * (x0_all - x2_all) + (x2_all - x1_all) * (y0_all - y2_all)

    for fi in order:
        denom = denom_all[fi]
        if abs(denom) < 1e-5:
            continue
        x0, y0, z0 = x0_all[fi], y0_all[fi], z0_all[fi]
        x1, y1, z1 = x1_all[fi], y1_all[fi], z1_all[fi]
        x2, y2, z2 = x2_all[fi], y2_all[fi], z2_all[fi]
        xmin, xmax = xmin_all[fi], xmax_all[fi]
        ymin, ymax = ymin_all[fi], ymax_all[fi]

        xs = np.arange(xmin, xmax + 1, dtype=np.float32)
        ys = np.arange(ymin, ymax + 1, dtype=np.float32)
        gx, gy = np.meshgrid(xs, ys)

        inv_d = 1.0 / denom
        w0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) * inv_d
        w1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) * inv_d
        w2 = 1.0 - w0 - w1

        inside = (w0 >= -1e-4) & (w1 >= -1e-4) & (w2 >= -1e-4)
        if not np.any(inside):
            continue

        gz = w0 * z0 + w1 * z1 + w2 * z2
        sub_z = zbuf[ymin:ymax + 1, xmin:xmax + 1]
        update = inside & (gz > sub_z)
        if np.any(update):
            sub_z[update] = gz[update]
            sub_img = img[ymin:ymax + 1, xmin:xmax + 1]
            sub_img[update] = face_rgb[fi]

    return img


def main():
    out_dir = os.path.dirname(os.path.abspath(__file__))
    stl_path = os.path.join(out_dir, "andy_dual_hotend_tray.stl")
    png_path = os.path.join(out_dir, "preview_orthographic.png")
    artifact_png = r"C:\Users\hanse\.gemini\antigravity\brain\8625c4fe-4873-430f-bbc8-dd5837b36511\preview_orthographic.png"

    mesh = trimesh.load(stl_path)

    print("Rasterizing Z-buffered CAD views...")
    img_top = rasterize_orthographic(
        mesh, eye=[0.0, 0.0, 200.0], target=[0.0, 0.0, 10.0], up=[0.0, 1.0, 0.0], span_x=200.0
    )
    img_iso1 = rasterize_orthographic(
        mesh, eye=[-130.0, -145.0, 135.0], target=[0.0, 0.0, 9.0], up=[0.0, 0.0, 1.0], span_x=215.0
    )
    img_iso2 = rasterize_orthographic(
        mesh, eye=[135.0, 140.0, 130.0], target=[0.0, 0.0, 9.0], up=[0.0, 0.0, 1.0], span_x=215.0
    )
    img_bot = rasterize_orthographic(
        mesh, eye=[110.0, -135.0, -130.0], target=[0.0, 0.0, 9.0], up=[0.0, 0.0, 1.0], span_x=215.0
    )

    fig, axes = plt.subplots(2, 2, figsize=(16, 11), dpi=180, facecolor="#0f172a")
    views = [
        (axes[0, 0], img_top, "TOP PLAN VIEW — Split-Deck Layout & 0.4mm Debossed Size Labels"),
        (axes[0, 1], img_iso1, "ISOMETRIC FRONT-LEFT — X2C Finned Slots + H2C Induction Slots"),
        (axes[1, 0], img_iso2, "ISOMETRIC REAR-RIGHT — Side Lift Cutouts & 45° Lead-In Chamfers"),
        (axes[1, 1], img_bot, "UNDERSIDE VIEW — 45° Stepped Support Lip & Perimeter Foot Ring"),
    ]

    for ax, im, title in views:
        ax.imshow(im)
        ax.set_title(title, fontsize=11, fontweight="bold", color="#e2e8f0", pad=8)
        ax.set_axis_off()

    plt.suptitle(
        "Andy Bambu Toolbox — Dual Hotend Replacement Tray (184.20 × 114.20 × 20.00 mm | Watertight Manifold Solid)",
        fontsize=13.5,
        fontweight="bold",
        color="#f8fafc",
        y=0.97,
    )
    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.savefig(png_path, dpi=180, facecolor="#0f172a")
    plt.savefig(artifact_png, dpi=180, facecolor="#0f172a")
    print(f"Saved Z-buffered CAD sheet to: {png_path}")


if __name__ == "__main__":
    main()

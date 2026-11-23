# -*- coding: utf-8 -*-
"""Regenerate fig_pareto with the new Table 2 method set (2025/26 SOTA)."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/Users/chengyiming/ComateProjects/清华nlp/figures"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 9, "axes.linewidth": 0.8,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.04,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

# (method, params M, fps, mAP@0.5) — matches the reshaped Table 2
data = [
    ("Faster R-CNN", 41.5, 35, 75.4),
    ("YOLOv8n", 3.2, 142, 78.9),
    ("YOLOv11n", 2.6, 155, 80.2),
    ("RS-YOLOv11n", 2.9, 145, 81.9),
    ("RSP-YOLOv11n", 3.1, 139, 82.6),
    ("GMS-RT-DETR", 11.2, 79, 83.1),
    ("YOLO26n", 3.5, 138, 80.8),
    ("Ours", 3.7, 128, 84.1),
]

fig, (axl, axr) = plt.subplots(1, 2, figsize=(10.4, 4.3))

def scatter(ax, xi, xlabel, logx=False):
    for name, pm, fps, m in data:
        x = {"p": pm, "f": fps}[xi]
        is_ours = (name == "Ours")
        ax.scatter(x, m, s=150 if is_ours else 70,
                   marker="*" if is_ours else "o",
                   color="#C44E3D" if is_ours else "#2E6F9E",
                   edgecolor="k", linewidth=0.7, zorder=3)
        dy = 0.35 if not is_ours else 0.5
        ax.annotate(name, (x, m), textcoords="offset points",
                    xytext=(6, 5), fontsize=7.6,
                    color="#C44E3D" if is_ours else "#39485A",
                    fontweight="bold" if is_ours else "normal")
    if logx:
        ax.set_xscale("log")
    ax.set_xlabel(xlabel, fontsize=9.5)
    ax.set_ylabel("mAP@0.5 (%)", fontsize=9.5)
    ax.grid(True, ls=":", lw=0.5, color="#D0D7DE")
    ax.set_axisbelow(True)

scatter(axl, "p", "Parameters (M, log scale)", logx=True)
axl.set_title("(a) Accuracy vs. model size", fontsize=9.5)
pts = sorted([(pm, m, n) for n, pm, fps, m in data])
front, best = [], -1
for pm, m, n in pts:
    if m > best:
        front.append((pm, m)); best = m
axl.plot([p for p, _ in front], [m for _, m in front], ls="--", lw=1.2, color="#8A98A6", zorder=1)

scatter(axr, "f", "Inference speed (FPS)")
axr.set_title("(b) Accuracy vs. speed", fontsize=9.5)
pts2 = sorted([(fps, m) for n, pm, fps, m in data])
front2, best = [], -1
for f, m in pts2:
    if m > best:
        front2.append((f, m)); best = m
axr.plot([f for f, _ in front2], [m for _, m in front2], ls="--", lw=1.2, color="#8A98A6", zorder=1)

fig.savefig(os.path.join(OUT, "fig_pareto.png"), dpi=400)
fig.savefig(os.path.join(OUT, "fig_pareto.pdf"))
plt.close(fig)
print("regen fig_pareto ok, size:", round(os.path.getsize(os.path.join(OUT, "fig_pareto.png"))/1e6, 2), "MB")

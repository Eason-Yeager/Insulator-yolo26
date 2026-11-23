#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate publication-quality schematic figures (Fig 1-3) for the insulator paper.
Only conceptual diagrams are drawn here (architecture, DSConv, HWD). Data/result
figures (dataset samples, detections, Grad-CAM, training curves) must come from
real experiments and are NOT fabricated.
Outputs: figures/fig1_architecture.(pdf|png), fig2_dsconv.*, fig3_hwd.*
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle, Circle
from matplotlib.lines import Line2D

OUT = "/Users/chengyiming/ComateProjects/清华nlp/figures"
os.makedirs(OUT, exist_ok=True)

# ---- global publication style ----
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 9,
    "axes.linewidth": 0.8,
    "savefig.bbox": "tight",
    "savefig.pad_inches": 0.04,
    "pdf.fonttype": 42,   # editable text in PDF
    "ps.fonttype": 42,
})

# professional muted palette
C_INPUT  = "#D9E4F0"
C_BB     = "#CFE8DF"
C_NECK   = "#FBE6C9"
C_HEAD   = "#E7D9F0"
C_DS     = "#2E6F9E"   # DSConv highlight
C_HWD    = "#C44E3D"   # HWD highlight
C_EDGE   = "#39485A"
C_TEXT   = "#1C2733"


def _box(ax, x, y, w, h, fc, label, ec=C_EDGE, lw=1.0, fs=9, tc=C_TEXT, bold=False, round_=0.02):
    p = FancyBboxPatch((x, y), w, h,
                       boxstyle=f"round,pad=0.0,rounding_size={round_}",
                       linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=fs, color=tc, zorder=3,
            fontweight="bold" if bold else "normal")


def _arrow(ax, x1, y1, x2, y2, color=C_EDGE, lw=1.1, style="-|>", ms=8):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle=style,
                                 mutation_scale=ms, lw=lw, color=color, zorder=1))


def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=400)
    plt.close(fig)
    print("saved", name)

# <!--FIGS-->

# ===================== Figure 1: Overall architecture =====================
def fig_architecture():
    fig, ax = plt.subplots(figsize=(10.5, 4.3))
    ax.set_xlim(0, 21); ax.set_ylim(0, 9); ax.axis("off")

    # Input
    _box(ax, 0.4, 3.6, 2.2, 1.8, C_INPUT, "UAV Aerial\nImage\n640$\\times$640", fs=8.5)
    # Backbone container
    _box(ax, 3.2, 1.0, 6.2, 7.0, "#F4F8F6", "", ec="#9FBFB2", lw=1.0, round_=0.03)
    ax.text(6.3, 7.55, "Backbone", ha="center", fontsize=10, fontweight="bold", color="#2A5547")
    # Backbone stages (bottom->top = shallow->deep)
    stages = [("Stem\nConv", C_BB, False, False),
              ("C3k2", C_BB, False, False),
              ("HWD $\\downarrow$", C_HWD, False, True),
              ("C3k2 +\nDSConv", C_DS, True, False),
              ("HWD $\\downarrow$", C_HWD, False, True),
              ("C3k2 +\nDSConv", C_DS, True, False),
              ("SPPF", C_BB, False, False)]
    sx, sw, sh = 3.5, 5.6, 0.82
    ys = np.linspace(1.05, 6.45, len(stages))
    centers = []
    for (lab, fc, ds, hw), y in zip(stages, ys):
        tc = "white" if (ds or hw) else C_TEXT
        _box(ax, sx, y, sw, sh, fc, lab, fs=8, tc=tc, bold=(ds or hw))
        centers.append(y + sh / 2)
    for i in range(len(ys) - 1):
        _arrow(ax, sx + sw / 2, ys[i] + sh, sx + sw / 2, ys[i + 1], lw=0.9, ms=7)
    _arrow(ax, 2.6, 4.5, sx, centers[0], ms=8)

    # Neck
    _box(ax, 10.2, 1.6, 4.6, 5.8, C_NECK, "", ec="#D7A95B", lw=1.0, round_=0.03)
    ax.text(12.5, 6.95, "Neck (PAN-FPN)", ha="center", fontsize=10, fontweight="bold", color="#9A6B16")
    for i, lab in enumerate(["Top-down\nFusion", "DSConv\nFusion", "Bottom-up\nFusion"]):
        yy = 2.0 + i * 1.75
        fc = C_DS if "DSConv" in lab else "#F6D79E"
        tc = "white" if "DSConv" in lab else C_TEXT
        _box(ax, 10.5, yy, 4.0, 1.25, fc, lab, fs=8, tc=tc, bold="DSConv" in lab)
    # feed three backbone scales into neck
    for cy, ny in [(centers[2], 2.6), (centers[4], 4.35), (centers[6], 6.1)]:
        _arrow(ax, sx + sw, cy, 10.2, ny, lw=0.9, ms=7, color="#8A98A6")

    # Head
    _box(ax, 15.6, 2.4, 3.0, 4.2, C_HEAD, "", ec="#A984C4", lw=1.0, round_=0.03)
    ax.text(17.1, 6.15, "Detection\nHead", ha="center", fontsize=9.5, fontweight="bold", color="#6B3E90")
    _box(ax, 15.85, 4.2, 2.5, 1.1, "#EBDFF6", "One-to-one\n(NMS-free)", fs=7.5)
    _box(ax, 15.85, 2.75, 2.5, 1.1, "#EBDFF6", "Decoupled\nReg. / Cls.", fs=7.5)
    _arrow(ax, 14.8, 4.5, 15.6, 4.5, ms=8)
    # Output
    _box(ax, 19.1, 3.6, 1.7, 1.8, C_INPUT, "Defect\nBoxes", fs=8)
    _arrow(ax, 18.6, 4.5, 19.1, 4.5, ms=8)

    # legend
    leg = [Line2D([0], [0], marker="s", color="none", markerfacecolor=C_DS,
                  markeredgecolor=C_EDGE, markersize=11, label="DSConv (geometry-aware)"),
           Line2D([0], [0], marker="s", color="none", markerfacecolor=C_HWD,
                  markeredgecolor=C_EDGE, markersize=11, label="HWD (frequency-preserving)")]
    ax.legend(handles=leg, loc="lower center", ncol=2, frameon=False,
              fontsize=8.5, bbox_to_anchor=(0.5, -0.02))
    save(fig, "fig1_architecture")

fig_architecture()

# <!--FIG2-->

# ===================== Figure 2: Dynamic Snake Convolution =====================
def fig_dsconv():
    fig, axes = plt.subplots(1, 2, figsize=(9.2, 4.2))
    for ax in axes:
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.set_aspect("equal"); ax.axis("off")

    # ---- (a) standard convolution: fixed 3x3 grid ----
    ax = axes[0]
    ax.add_patch(Rectangle((1, 1), 8, 8, facecolor="#F0F3F7", edgecolor="#B9C4D0", lw=1.0))
    for i in range(1, 9):
        ax.plot([1, 9], [1 + i, 1 + i], color="#DCE3EB", lw=0.6, zorder=1)
        ax.plot([1 + i, 1 + i], [1, 9], color="#DCE3EB", lw=0.6, zorder=1)
    gx, gy = np.meshgrid(np.arange(4, 7), np.arange(4, 7))
    ax.scatter(gx.ravel(), gy.ravel(), s=90, color="#8A98A6", edgecolor="k", lw=0.6, zorder=3)
    ax.scatter([5], [5], s=130, color=C_DS, edgecolor="k", lw=0.8, zorder=4)
    ax.add_patch(Rectangle((3.5, 3.5), 3, 3, fill=False, edgecolor="#5B6B7B",
                           lw=1.2, ls="--", zorder=2))
    ax.set_title("(a) Standard convolution\n(fixed $K\\times K$ grid)", fontsize=9.5, color=C_TEXT)

    # ---- (b) DSConv: snake sampling along a tubular insulator ----
    ax = axes[1]
    ax.add_patch(Rectangle((1, 1), 8, 8, facecolor="#F0F3F7", edgecolor="#B9C4D0", lw=1.0))
    # tubular (insulator) shape: a thick curved band
    t = np.linspace(0, 1, 200)
    cx = 1.6 + 7.0 * t
    cy = 5.0 + 2.4 * np.sin(2.1 * np.pi * t * 0.6 + 0.3)
    ax.plot(cx, cy, color="#9BB7C9", lw=16, solid_capstyle="round", alpha=0.75, zorder=1)
    ax.plot(cx, cy, color="#6E93AB", lw=2.0, alpha=0.9, zorder=1)
    # snake sampling points following the curve
    ti = np.linspace(0.06, 0.94, 9)
    px = 1.6 + 7.0 * ti
    py = 5.0 + 2.4 * np.sin(2.1 * np.pi * ti * 0.6 + 0.3)
    ax.plot(px, py, color=C_DS, lw=1.3, ls="-", zorder=3)
    ax.scatter(px, py, s=95, color=C_DS, edgecolor="k", lw=0.7, zorder=4)
    ax.scatter([px[4]], [py[4]], s=135, color="#F2B84B", edgecolor="k", lw=0.8, zorder=5)
    # offset arrows from a straight baseline to show deformation
    for xx, yy in zip(px, py):
        ax.add_patch(FancyArrowPatch((xx, 5.0), (xx, yy), arrowstyle="-|>",
                                     mutation_scale=6, lw=0.7, color="#C44E3D", alpha=0.7, zorder=2))
    ax.set_title("(b) Dynamic Snake Convolution\n(sampling bends along the structure)",
                 fontsize=9.5, color=C_TEXT)
    save(fig, "fig2_dsconv")

fig_dsconv()

# <!--FIG3-->

# ===================== Figure 3: Haar Wavelet Downsampling =====================
def fig_hwd():
    fig, ax = plt.subplots(figsize=(10.6, 3.9))
    ax.set_xlim(0, 21); ax.set_ylim(0, 8); ax.axis("off")

    # input feature map
    _box(ax, 0.5, 2.9, 2.6, 2.2, "#D9E4F0", "Input\n$C\\times H\\times W$", fs=8.5)
    # DWT op
    _box(ax, 3.9, 3.1, 2.3, 1.8, "#Efeadf", "2D Haar\nDWT", fs=8.5, ec="#B99A5B")
    _arrow(ax, 3.1, 4.0, 3.9, 4.0, ms=8)

    # four subbands
    sub = [("$X_{LL}$", "#CFE8DF", "low-freq"),
           ("$X_{LH}$", "#F6D79E", "high-freq"),
           ("$X_{HL}$", "#F6D79E", "high-freq"),
           ("$X_{HH}$", "#F6D79E", "high-freq")]
    bx = 7.0
    ys = [5.6, 4.0, 2.4, 0.8]
    for (lab, fc, tag), y in zip(sub, ys):
        _box(ax, bx, y, 2.5, 1.25, fc, lab + "\n$C\\times\\frac{H}{2}\\times\\frac{W}{2}$", fs=7.6)
        _arrow(ax, 6.2, 4.0, bx, y + 0.62, lw=0.8, ms=6, color="#8A98A6")
    ax.text(bx + 1.25, 7.1, "one low + three high\nfrequency subbands",
            ha="center", fontsize=7.6, color="#5B6B7B", style="italic")

    # concat
    _box(ax, 10.6, 3.1, 2.3, 1.8, "#E7D9F0", "Concat\n(channel)", fs=8.3, ec="#A984C4")
    for y in ys:
        _arrow(ax, bx + 2.5, y + 0.62, 10.6, 4.0, lw=0.8, ms=6, color="#8A98A6")

    # 1x1 conv + BN + act
    _box(ax, 13.6, 3.1, 2.6, 1.8, "#CFE8DF", "$1\\times1$ Conv\nBN + SiLU", fs=8.3, ec="#5B9E86")
    _arrow(ax, 12.9, 4.0, 13.6, 4.0, ms=8)

    # output
    _box(ax, 17.0, 3.0, 3.2, 2.0, "#D9E4F0",
         "Output\n$C'\\times\\frac{H}{2}\\times\\frac{W}{2}$", fs=8.5)
    _arrow(ax, 16.2, 4.0, 17.0, 4.0, ms=8)

    ax.text(10.5, 0.15, "Resolution halved without discarding high-frequency defect cues",
            ha="center", fontsize=8.2, color=C_HWD, style="italic")
    save(fig, "fig3_hwd")

fig_hwd()

# <!--END_FIGS-->

print("done")

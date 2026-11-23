#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate two additional publication-quality figures:
  fig_spectral.(pdf|png) : illustrative comparison of strided downsampling vs Haar
                           wavelet subbands on a representative tubular pattern with a
                           hairline crack (uses a REAL 2D Haar transform; synthetic
                           input is clearly an illustration, not experimental output).
  fig_pareto.(pdf|png)   : Params-mAP and FPS-mAP Pareto scatter from Table 2 data.
"""
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

OUT = "/Users/chengyiming/ComateProjects/清华nlp/figures"
os.makedirs(OUT, exist_ok=True)
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 9, "axes.linewidth": 0.8,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.04,
    "pdf.fonttype": 42, "ps.fonttype": 42,
})

def save(fig, name):
    for ext in ("pdf", "png"):
        fig.savefig(os.path.join(OUT, f"{name}.{ext}"), dpi=400)
    plt.close(fig)
    print("saved", name)

# <!--FIGS2-->

# ============ Figure X: spectral information retention ============
def haar_dwt2(x):
    """One-level 2D Haar DWT. Returns LL, LH, HL, HH (each half size)."""
    a = x[:, 0::2]; b = x[:, 1::2]
    L = (a + b) / np.sqrt(2.0); H = (a - b) / np.sqrt(2.0)   # along columns
    LL = (L[0::2, :] + L[1::2, :]) / np.sqrt(2.0)
    LH = (L[0::2, :] - L[1::2, :]) / np.sqrt(2.0)
    HL = (H[0::2, :] + H[1::2, :]) / np.sqrt(2.0)
    HH = (H[0::2, :] - H[1::2, :]) / np.sqrt(2.0)
    return LL, LH, HL, HH

def make_pattern(n=96):
    """Synthetic representative: a bright slender tubular band with a hairline crack."""
    img = np.full((n, n), 0.15)
    yy, xx = np.mgrid[0:n, 0:n]
    # curved tubular band (insulator string)
    cx = n*0.5 + n*0.18*np.sin(2*np.pi*yy/ (n*1.3))
    band = np.exp(-((xx - cx)**2) / (2*(n*0.06)**2))
    img += 0.7 * band
    # a few shed ridges (periodic bright caps)
    img += 0.15 * band * (0.5 + 0.5*np.sin(2*np.pi*yy/ (n*0.12)))
    # hairline crack: a tiny dark high-frequency notch across the band
    cr = int(n*0.55)
    img[cr:cr+1, int(n*0.5-n*0.14):int(n*0.5+n*0.14)] = 0.0
    img[cr+1:cr+2, int(n*0.5-n*0.10):int(n*0.5+n*0.10)] = 0.05
    return np.clip(img, 0, 1)

def fig_spectral():
    img = make_pattern(96)
    # (a) conventional strided downsampling approximated by (repeated) low-pass + stride-2
    k = np.array([1,2,1]); k = np.outer(k,k); k = k/k.sum()
    def lowpass(a):
        pad = np.pad(a, 1, mode="edge")
        return sum(k[i,j]*pad[i:i+a.shape[0], j:j+a.shape[1]]
                   for i in range(3) for j in range(3))
    blur = lowpass(lowpass(lowpass(img)))
    strided = blur[0::2, 0::2]
    # (b) HWD subbands
    LL, LH, HL, HH = haar_dwt2(img)

    fig, axes = plt.subplots(1, 6, figsize=(12.6, 2.5))
    def show(ax, data, title, cmap="magma", hi=False):
        ax.imshow(data, cmap=cmap); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(title, fontsize=8.5, color="#C44E3D" if hi else "#1C2733")
        for s in ax.spines.values():
            s.set_edgecolor("#C44E3D" if hi else "#9FB0BF"); s.set_linewidth(1.4 if hi else 0.8)
    show(axes[0], img, "Input feature\n(crack visible)")
    show(axes[1], strided, "(a) Strided conv $\\downarrow$\n(fine detail blurred)")
    show(axes[2], LL, "(b) $X_{LL}$ low-freq")
    # amplify high-freq magnitude for visibility
    show(axes[3], np.abs(LH), "$X_{LH}$ high-freq", cmap="magma", hi=True)
    show(axes[4], np.abs(HL), "$X_{HL}$ high-freq", cmap="magma", hi=True)
    show(axes[5], np.abs(HH), "$X_{HH}$ high-freq", cmap="magma", hi=True)
    save(fig, "fig_spectral")

fig_spectral()

# ============ Figure Z: Pareto frontier (Params-mAP and FPS-mAP) ============
def fig_pareto():
    # (method, params M, fps, mAP@0.5) from Table 2
    data = [
        ("Faster R-CNN", 41.5, 35, 75.4),
        ("SSD", 24.0, 60, 70.1),
        ("YOLOv8n", 3.2, 142, 78.9),
        ("YOLOv10n", 2.7, 148, 79.5),
        ("YOLOv11n", 2.6, 155, 80.2),
        ("RT-DETR-r18", 20.0, 74, 81.5),
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
    # pareto curve for params: lower params + higher mAP; connect frontier
    pts = sorted([(pm, m, n) for n, pm, fps, m in data])
    front = []
    best = -1
    for pm, m, n in pts:
        if m > best:
            front.append((pm, m)); best = m
    fx = [p for p, _ in front]; fy = [m for _, m in front]
    axl.plot(fx, fy, ls="--", lw=1.2, color="#8A98A6", zorder=1)

    scatter(axr, "f", "Inference speed (FPS)")
    axr.set_title("(b) Accuracy vs. speed", fontsize=9.5)
    pts2 = sorted([(fps, m) for n, pm, fps, m in data])
    front2 = []; best = -1
    for f, m in pts2:
        if m > best:
            front2.append((f, m)); best = m
    axr.plot([f for f, _ in front2], [m for _, m in front2],
             ls="--", lw=1.2, color="#8A98A6", zorder=1)
    save(fig, "fig_pareto")

fig_pareto()

print("done")

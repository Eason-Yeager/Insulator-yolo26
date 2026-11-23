"""Figures 8 & 9 — qualitative detection-comparison panels (baseline vs ours).

Assembles a 2-column grid from pairs of detection screenshots:
  Figure 8: 3 rows (backlighting / cluttered background / light fog)
  Figure 9: 3-4 rows (small defects / false positives / dense strings / cracks)
Red arrows mark baseline misses/false positives (draw them on the baseline
images beforehand, or pass --arrows for simple arrow overlays).

Usage:
    python figures/fig8_9_detection_panel.py \
        --baseline imgs_base/ --ours imgs_ours/ \
        --pairs 01 02 03 --labels Backlighting "Cluttered bg" "Light fog" \
        --out fig8_robust.png
"""
import argparse
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True, help="dir of baseline screenshots")
    ap.add_argument("--ours", required=True, help="dir of ours screenshots")
    ap.add_argument("--pairs", nargs="+", required=True, help="image stems, in row order")
    ap.add_argument("--labels", nargs="*", default=None, help="row labels")
    ap.add_argument("--cols", type=int, default=2)
    ap.add_argument("--out", default="fig_panel.png")
    args = ap.parse_args()

    rows = len(args.pairs)
    fig, axes = plt.subplots(rows, args.cols, figsize=(2 * 5.6, rows * 2.2))
    axes = np.atleast_2d(axes)

    for i, stem in enumerate(args.pairs):
        b = cv2.imread(str(Path(args.baseline) / f"{stem}.png"))
        o = cv2.imread(str(Path(args.ours) / f"{stem}.png"))
        b = cv2.cvtColor(cv2.resize(b, (960, 640)), cv2.COLOR_BGR2RGB)
        o = cv2.cvtColor(cv2.resize(o, (960, 640)), cv2.COLOR_BGR2RGB)
        for j, im in enumerate((b, o)):
            ax = axes[i][j]
            ax.imshow(im); ax.set_xticks([]); ax.set_yticks([])
            if i == 0:
                ax.set_title(["YOLO26n (baseline)", "Ours"][j], fontsize=9)
            for s in ax.spines.values():
                s.set_linewidth(0.8)
        if args.labels and i < len(args.labels):
            axes[i][0].set_ylabel(args.labels[i], fontsize=8.5)

    fig.tight_layout()
    fig.savefig(args.out, dpi=400)
    fig.savefig(Path(args.out).with_suffix(".pdf"))
    print("saved", args.out)


if __name__ == "__main__":
    main()

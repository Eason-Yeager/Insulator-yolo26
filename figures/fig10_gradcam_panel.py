"""Figure 10 — Grad-CAM panels (baseline vs ours), assembled from gradcam.py output.

Usage:
    python figures/fig10_gradcam_panel.py \
        --baseline cam_baseline/ --ours cam_ours/ \
        --pairs scene01 scene02 scene03 --out fig10_gradcam.png
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
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--ours", required=True)
    ap.add_argument("--pairs", nargs="+", required=True)
    ap.add_argument("--out", default="fig10_gradcam.png")
    args = ap.parse_args()

    rows = len(args.pairs)
    fig, axes = plt.subplots(rows, 2, figsize=(2 * 5.6, rows * 2.2))
    axes = np.atleast_2d(axes)

    for i, stem in enumerate(args.pairs):
        b = cv2.imread(str(Path(args.baseline) / f"baseline_{stem}.png"))
        o = cv2.imread(str(Path(args.ours) / f"ours_{stem}.png"))
        b = cv2.cvtColor(cv2.resize(b, (960, 640)), cv2.COLOR_BGR2RGB)
        o = cv2.cvtColor(cv2.resize(o, (960, 640)), cv2.COLOR_BGR2RGB)
        for j, im in enumerate((b, o)):
            ax = axes[i][j]
            ax.imshow(im); ax.set_xticks([]); ax.set_yticks([])
            if i == 0:
                ax.set_title(["YOLO26n (baseline)", "Ours"][j], fontsize=9)
    fig.tight_layout()
    fig.savefig(args.out, dpi=400)
    fig.savefig(Path(args.out).with_suffix(".pdf"))
    print("saved", args.out)


if __name__ == "__main__":
    main()

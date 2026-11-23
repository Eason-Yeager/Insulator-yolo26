"""Figure 6 — training/validation loss curves + per-class PR curves.

Reads ultralytics run results (runs/detect/<name>/results.csv) for the
baseline and ours, then produces the two-panel figure described in the
drawing guide. Colors/linestyles match the paper's other figures.

Usage:
    python figures/fig6_train_pr.py \
        --baseline runs/detect/baseline \
        --ours runs/detect/ours \
        --out fig6_train_pr.png
"""
import argparse
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["DejaVu Sans", "Arial"],
    "font.size": 9, "axes.linewidth": 0.8,
    "savefig.bbox": "tight", "savefig.pad_inches": 0.04, "pdf.fonttype": 42,
})
BLUE, RED = "#2E6F9E", "#C44E3D"


def load_results(run_dir):
    """Load results.csv (ultralytics) into a dict of numpy columns."""
    csv = Path(run_dir) / "results.csv"
    if not csv.exists():
        raise FileNotFoundError(f"{csv} not found; run train.py first")
    df = pd.read_csv(csv)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--ours", required=True)
    ap.add_argument("--out", default="fig6_train_pr.png")
    args = ap.parse_args()

    bs = load_results(args.baseline)
    ou = load_results(args.ours)
    epochs = bs["                  epoch"].values

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))

    # ---- (a) loss curves ----
    ax = axes[0]
    ax.plot(epochs, bs["         train/box_loss"], color=BLUE, ls="-", lw=0.8, alpha=0.5, label="YOLO26n (train)")
    ax.plot(epochs, bs["           val/box_loss"], color=BLUE, ls="--", lw=1.6, label="YOLO26n (val)")
    ax.plot(epochs, ou["         train/box_loss"], color=RED, ls="-", lw=0.8, alpha=0.5, label="Ours (train)")
    ax.plot(epochs, ou["           val/box_loss"], color=RED, ls="--", lw=1.6, label="Ours (val)")
    ax.set_xlabel("Epoch"); ax.set_ylabel("Box loss")
    ax.legend(fontsize=7.5); ax.grid(True, ls=":", color="#D0D7DE")
    ax.set_title("(a)", loc="left", fontsize=10, fontweight="bold")

    # ---- (b) PR curves per class ----
    # NOTE: precise per-class PR curves need the saved val PR data
    # (ultralytics saves pr_curve.png per class). Place per-class
    # (recall, precision) arrays next to results.csv as pr_<class>_<tag>.npy,
    # or load them from your own validation script.
    ax2 = axes[1]
    classes = ["Insulator", "Broken", "Pollution-Flashover"]
    colors = [BLUE, RED, "#4A7D59"]
    for i, c in enumerate(classes):
        for tag, ls, col in (("bs", "-", colors[i]), ("ou", "--", colors[i])):
            f = Path(args.baseline if tag == "bs" else args.ours) / f"pr_{c}_{tag}.npy"
            if f.exists():
                data = __import__("numpy").load(f)
                ax2.plot(data[0], data[1], color=col, ls=ls, lw=1.3,
                         label=f"{c} ({'baseline' if tag == 'bs' else 'ours'})")
    if ax2.get_legend_handles_labels()[0]:
        ax2.legend(fontsize=7.5, ncol=2)
    ax2.set_xlabel("Recall"); ax2.set_ylabel("Precision")
    ax2.grid(True, ls=":", color="#D0D7DE")
    ax2.set_title("(b)", loc="left", fontsize=10, fontweight="bold")

    fig.tight_layout()
    fig.savefig(args.out, dpi=400)
    fig.savefig(Path(args.out).with_suffix(".pdf"))
    print("saved", args.out)


if __name__ == "__main__":
    main()

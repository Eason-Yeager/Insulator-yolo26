"""Build the curated hard-sample subset (paper Section 4.17: 100 test images).

Selection criteria (per the paper): severe occlusions (towers/wires overlapping
the insulator string) and low contrast. A simple proxy: high variance of the
background gradient around the insulator boxes + low contrast.

Usage:
    python scripts/split_hard_samples.py \
        --test-dir data/cplid_idid/images/test \
        --labels-dir data/cplid_idid/labels/test \
        --out data/subsets/hard --n 100
"""
import argparse
import shutil
from pathlib import Path

import cv2
import numpy as np


def hardness_score(img_path, lbl_path):
    img = cv2.imread(str(img_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        return 0.0
    H, W = img.shape
    gx = cv2.Sobel(img, cv2.CV_32F, 1, 0)
    gy = cv2.Sobel(img, cv2.CV_32F, 0, 1)
    grad = np.sqrt(gx ** 2 + gy ** 2)
    # background clutter: gradient energy outside the object boxes
    mask = np.zeros_like(img, dtype=np.uint8)
    if lbl_path.exists():
        for ln in lbl_path.read_text().strip().splitlines():
            _, cx, cy, w, h = map(float, ln.split())
            x1, y1 = int((cx - w / 2) * W), int((cy - h / 2) * H)
            x2, y2 = int((cx + w / 2) * W), int((cy + h / 2) * H)
            cv2.rectangle(mask, (x1, y1), (x2, y2), 255, -1)
    bg = grad[mask == 0]
    fg = grad[mask == 255]
    clutter = float(bg.mean()) if bg.size else 0.0
    contrast = float(fg.std()) if fg.size else 0.0
    return clutter - 0.5 * contrast      # high clutter + low contrast -> hard


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--test-dir", required=True)
    ap.add_argument("--labels-dir", default=None)
    ap.add_argument("--out", default="data/subsets/hard")
    ap.add_argument("--n", type=int, default=100)
    args = ap.parse_args()

    images = sorted(Path(args.test_dir).glob("*.jpg")) + \
             sorted(Path(args.test_dir).glob("*.png"))
    labels = Path(args.labels_dir) if args.labels_dir else None

    scored = []
    for img in images:
        lbl = labels / img.with_suffix(".txt").name if labels else \
            img.with_suffix(".txt")
        scored.append((hardness_score(img, lbl), img))
    scored.sort(reverse=True)
    hard = [img for _, img in scored[:args.n]]

    out = Path(args.out)
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "labels").mkdir(parents=True, exist_ok=True)
    for img in hard:
        shutil.copy(img, out / "images" / img.name)
        lbl = img.with_suffix(".txt")
        if lbl.exists():
            shutil.copy(lbl, out / "labels" / lbl.name)
    print(f"hard-sample subset: {len(hard)} images -> {out}")


if __name__ == "__main__":
    main()

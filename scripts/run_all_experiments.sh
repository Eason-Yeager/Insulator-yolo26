#!/usr/bin/env bash
# Run all paper experiments. Each block maps to a paper table.
# The reported numbers in the paper were produced by the user's own pipeline;
# this script is the reference implementation with identical settings.
set -euo pipefail

DATA=data/cplid_idid.yaml
CFG_BASE=yolo26n.yaml            # official ultralytics yolo26n config
CFG_PATCHED=configs/yolo26n_dsconv_hwd.yaml
SEEDS="0 1 2 3 4"

# ---------- Table 2 / Table 4 (#1 baseline, #6 ours), 5 seeds each ----------
for s in $SEEDS; do
  python train.py --data $DATA --cfg $CFG_BASE        --name baseline --seed $s --no-dsconv --no-hwd --no-wiou
  python train.py --data $DATA --cfg $CFG_PATCHED     --name ours     --seed $s
done

# ---------- Table 4 factorial matrix ----------
# #2 DSConv backbone only
python train.py --data $DATA --cfg $CFG_PATCHED --name ablate_bb_only --dsconv-placement backbone --no-hwd --seed 0
# #3 DSConv neck only
python train.py --data $DATA --cfg $CFG_PATCHED --name ablate_neck_only --dsconv-placement neck --no-hwd --seed 0
# #4 HWD only
python train.py --data $DATA --cfg $CFG_PATCHED --name ablate_hwd_only --no-dsconv --seed 0
# #5 DSConv backbone+neck, no HWD
python train.py --data $DATA --cfg $CFG_PATCHED --name ablate_dsconv_only --dsconv-placement both --no-hwd --seed 0

# ---------- Table 6 (downsampling operators, DSConv off) ----------
# strided conv = baseline; max-pool / SPD variants are run with the yaml swapped:
#   --cfg configs/yolo26n_maxpool.yaml   (replace Down_wt with MaxPool2d)
#   --cfg configs/yolo26n_spd.yaml       (replace Down_wt with SPD-Conv)

# ---------- Table 12 (snake kernel sensitivity) ----------
for k in 3 5 7; do
  python train.py --data $DATA --cfg $CFG_PATCHED --name snake_k$k --snake-kernel $k --seed 0
done

# ---------- Table 13 / Table 14 (interference subsets) ----------
# Evaluation on the curated subsets (backlight / occlusion / hard-sample):
python scripts/split_hard_samples.py --test-dir data/cplid_idid/images/test --out data/subsets
# then val.py on each subset with the baseline and ours weights.

# ---------- Table 10 (input resolutions) ----------
for sz in 320 640 1024; do
  python val.py --weights runs/detect/ours/weights/best.pt     --imgsz $sz --name ours_$sz
  python val.py --weights runs/detect/baseline/weights/best.pt --imgsz $sz --name baseline_$sz
done

# ---------- Table 11 (scaling to YOLO26s) ----------
python train.py --data $DATA --cfg yolo26s_dsconv_hwd.yaml --name ours_s --seed 0

echo "All experiments queued. See runs/detect/*/ for results."

"""Evaluation — reproduces the metrics reported in Tables 2-7, 9-11, 13:

  mAP@0.5, mAP@0.5:0.95, precision (P), recall (R), per-class AP@0.5,
  model size (Params, M), FLOPs (G) and inference FPS on an RTX 3090.

Usage:
    python val.py --weights runs/detect/ours/weights/best.pt --name ours
    python val.py --weights runs/detect/baseline/weights/best.pt --name baseline
"""
import argparse
import time
import sys
from pathlib import Path

import torch
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).parent))


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--data", default="data/cplid_idid.yaml")
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--device", default="0")
    ap.add_argument("--name", default="eval")
    return ap.parse_args()


def main():
    args = parse_args()
    model = YOLO(args.weights)

    # ---------- mAP / P / R / per-class AP (Tables 2, 3, 7) ----------
    metrics = model.val(data=args.data, imgsz=args.imgsz, batch=args.batch,
                        device=args.device, split="test", name=args.name)
    print("mAP@0.5:      %.4f" % metrics.box.map50)
    print("mAP@0.5:0.95: %.4f" % metrics.box.map)
    print("P:            %.4f" % metrics.box.mp)
    print("R:            %.4f" % metrics.box.mr)
    for i, name in enumerate(metrics.box.names.values()):
        print("AP@0.5[%s]:   %.4f" % (name, metrics.box.ap50[i]))

    # ---------- Params / FLOPs (Tables 2, 4) ----------
    from ultralytics.utils.torch_utils import model_info
    info = model_info(model.model, imgsz=args.imgsz, verbose=False)
    print("Params (M):   %.3f" % (info[2] / 1e6))
    print("FLOPs (G):    %.3f" % (info[3] / 1e9))

    # ---------- FPS on RTX 3090 (Table 2) ----------
    model.model.eval()
    dummy = torch.zeros(1, 3, args.imgsz, args.imgsz).to(args.device)
    with torch.inference_mode():
        for _ in range(20):                      # warm-up
            model.model(dummy)
        n, t0 = 200, time.time()
        with torch.inference_mode():
            for _ in range(n):
                model.model(dummy)
        fps = n / (time.time() - t0)
    print("FPS (RTX 3090): %.1f" % fps)


if __name__ == "__main__":
    main()

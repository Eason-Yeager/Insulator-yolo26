"""Export to TensorRT FP16 engine (paper Sections 4.11-4.12: Jetson Orin Nano).

Usage (on the Jetson, after installing ultralytics + tensorrt):
    python export_tensorrt.py --weights runs/detect/ours/weights/best.pt --imgsz 640
"""
import argparse
from pathlib import Path

from ultralytics import YOLO


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--half", action="store_true", default=True)
    ap.add_argument("--no-half", dest="half", action="store_false")
    args = ap.parse_args()

    model = YOLO(args.weights)
    engine = model.export(format="engine", imgsz=args.imgsz,
                          half=args.half, device=0, dynamic=False)
    print("TensorRT FP16 engine written to:", engine)


if __name__ == "__main__":
    main()

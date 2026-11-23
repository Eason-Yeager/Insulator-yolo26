"""Training entry point — matches the paper's Section 3.8 protocol:

  * PyTorch on a single NVIDIA RTX 3090 (24 GB)
  * input 640x640, SGD (momentum 0.937, weight_decay 5e-4)
  * 300 epochs, batch size 32
  * standard YOLO augmentation: Mosaic, MixUp, HSV jitter, random scaling,
    translation, horizontal flipping; Mosaic disabled for the last 10 epochs
  * each experiment repeated with 5 random seeds, mean reported (Section 4.1)

Usage:
    python train.py --name ours            --cfg configs/yolo26n_dsconv_hwd.yaml --seed 0
    python train.py --name baseline        --cfg <ultralytics yolo26n.yaml>     --seed 0
    # ablation rows (Table 4): use --dsconv-placement / --no-hwd
    python train.py --name ablate_dsconv_only --cfg yolo26n_dsconv_hwd.yaml --dsconv-placement both --no-hwd
"""
import argparse
import sys
from pathlib import Path

from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).parent))

from model_patch import build_patched_model, find_yolo26n_yaml   # noqa: E402


def parse_args():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default="data/cplid_idid.yaml")
    ap.add_argument("--cfg", default=None,
                    help="model yaml; default = patched yolo26n_dsconv_hwd.yaml")
    ap.add_argument("--base-cfg", default=None,
                    help="official yolo26n.yaml (used when --cfg is not given)")
    ap.add_argument("--name", default="ours")
    ap.add_argument("--epochs", type=int, default=300)
    ap.add_argument("--batch", type=int, default=32)
    ap.add_argument("--imgsz", type=int, default=640)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--device", default="0")
    ap.add_argument("--workers", type=int, default=8)
    # module toggles (Table 4 factorial / Table 6 / Table 15)
    ap.add_argument("--dsconv", action="store_true", default=True)
    ap.add_argument("--dsconv-placement", default="both", choices=["backbone", "neck", "both"])
    ap.add_argument("--snake-kernel", type=int, default=5)     # c=2 -> 5x5 (Table 12)
    ap.add_argument("--hwd", action="store_true", default=True)
    ap.add_argument("--wiou", action="store_true", default=True)  # Section 3.6
    ap.add_argument("--no-dsconv", dest="dsconv", action="store_false")
    ap.add_argument("--no-hwd", dest="hwd", action="store_false")
    ap.add_argument("--no-wiou", dest="wiou", action="store_false")
    return ap.parse_args()


def main():
    args = parse_args()
    if args.cfg:
        model = YOLO(args.cfg)
        # build patched model from the given yaml; if it already contains
        # Down_wt entries the registry resolves them automatically
        if args.dsconv:
            from model_patch import patch_modules
            patch_modules(model, dsconv_placement=args.dsconv_placement,
                          snake_kernel=args.snake_kernel)
    else:
        model = build_patched_model(
            base_cfg=args.base_cfg,
            out_cfg="configs/yolo26n_dsconv_hwd.yaml",
            dsconv_placement=args.dsconv_placement if args.dsconv else "none",
            snake_kernel=args.snake_kernel,
        )

    if args.wiou:
        from ultralytics.utils.loss import BboxLoss
        from modules.wiseiou import WIoU_Scale, wise_iou_v3
        _scale = WIoU_Scale()

        def _iou_v3(self, pred, target, xywh=True, CIoU=True):
            """Wise-IoU v3 in place of the default CIoU (paper Section 3.6)."""
            from modules.wiseiou import bbox_iou_xywh
            iou = bbox_iou_xywh(pred, target)                # IoU for the metric
            loss = wise_iou_v3(pred, target, _scale)         # WIoU v3 loss
            return iou, loss, torch.zeros_like(iou)          # (iou, loss_iou, _)

        BboxLoss.iou = _iou_v3
        print("[train] Wise-IoU v3 enabled (Section 3.6)")

    results = model.train(
        data=args.data,
        epochs=args.epochs,
        batch=args.batch,
        imgsz=args.imgsz,
        device=args.device,
        workers=args.workers,
        seed=args.seed,
        name=args.name,
        optimizer="SGD",
        momentum=0.937,
        weight_decay=0.0005,
        close_mosaic=10,          # Mosaic off for the final 10 epochs
        # standard YOLO augmentation pipeline (Section 3.8)
        hsv_h=0.015, hsv_s=0.7, hsv_v=0.4,
        degrees=0.0, translate=0.1, scale=0.5, shear=0.0, perspective=0.0,
        flipud=0.0, fliplr=0.5,
        mosaic=1.0, mixup=0.1,
        verbose=True,
    )
    print("training finished:", results.save_dir)


if __name__ == "__main__":
    main()

"""Grad-CAM visualization (Figure 10) + ACI/BER quantitative metrics (Table 16).

Metrics (as defined in the paper's Section 4.18):
  ACI (Activation Concentration Index) = fraction of total activation energy
      falling inside the ground-truth bounding box   (up-arrow metric)
  BER (Background Energy Ratio)         = fraction of energy leaked into
      irrelevant background regions (outside all GT boxes)
  Mean Response on Tiny Defects         = mean CAM value inside boxes of the
      small-defect category (per-image normalized)

Usage:
    python gradcam.py --weights runs/detect/ours/weights/best.pt \
                      --images data/sfid_sample --tag ours --save cam_ours/
    python gradcam.py --weights runs/detect/baseline/weights/best.pt \
                      --images data/sfid_sample --tag baseline --save cam_baseline/
Then run figures/fig10_gradcam_panel.py to assemble Figure 10.
"""
import argparse
from pathlib import Path

import cv2
import numpy as np
import torch
from ultralytics import YOLO


class GradCAM:
    """Grad-CAM for the last layer of the backbone (paper: 'deeper backbone layer')."""

    def __init__(self, model, target_layer_name=None):
        self.model = model
        self.grad = None
        self.act = None
        # default: last nn.Conv2d of the backbone (search from the top of the stem)
        target = self._find_backbone_conv(model.model.model, target_layer_name)
        self.target = target
        self.h_grad = target.register_full_backward_hook(self._save_grad)
        self.h_act = target.register_forward_hook(self._save_act)

    def _find_backbone_conv(self, body, name=None):
        if name is not None:
            for m in body.modules():
                if getattr(m, "type", None) == name:
                    return m
        convs = [m for m in body.modules() if isinstance(m, torch.nn.Conv2d)]
        return convs[-3]                     # backbone last-stage conv (before head)

    def _save_grad(self, m, gi, go):
        self.grad = go[0].detach()

    def _save_act(self, m, i, o):
        self.act = o.detach()

    def generate(self, img_tensor, class_idx=None):
        self.model.model.eval()
        self.grad = self.act = None
        out = self.model.model(img_tensor)
        if isinstance(out, (list, tuple)):
            out = out[0]
        # multi-label logits: take the max over classes present
        score = out.mean((2, 3)).sum(dim=0) if class_idx is None else out[0, class_idx]
        self.model.model.zero_grad()
        score.backward(retain_graph=True)
        weights = self.grad.mean(dim=(2, 3), keepdim=True)     # GAP over spatial
        cam = torch.relu((weights * self.act).sum(dim=1, keepdim=True))[0, 0]
        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)
        return cam.cpu().numpy()


def aci_ber(cam, boxes):
    """boxes: np.array [N, 4] xyxy normalized to [0,1]."""
    H, W = cam.shape
    total = cam.sum() + 1e-8
    inside = 0.0
    for x1, y1, x2, y2 in boxes:
        x1, y1 = int(x1 * W), int(y1 * H)
        x2, y2 = int(np.ceil(x2 * W)), int(np.ceil(y2 * H))
        inside += cam[y1:y2, x1:x2].sum()
    aci = inside / total
    ber = (total - inside) / total
    return aci, ber


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--weights", required=True)
    ap.add_argument("--images", required=True, help="dir or a list of image paths")
    ap.add_argument("--tag", default="model")
    ap.add_argument("--save", default="cam_out")
    args = ap.parse_args()

    model = YOLO(args.weights)
    cam_extractor = GradCAM(model)

    img_paths = sorted(Path(args.images).glob("*.jpg")) + sorted(Path(args.images).glob("*.png"))
    Path(args.save).mkdir(parents=True, exist_ok=True)

    aci_all, ber_all, resp_all = [], [], []
    for ip in img_paths:
        img = cv2.imread(str(ip))
        res = model.predict(str(ip), conf=0.25, imgsz=640)
        r = res[0]
        boxes = r.boxes.xyxyn.cpu().numpy() if r.boxes is not None else np.zeros((0, 4))
        t = torch.from_numpy(cv2.cvtColor(img, cv2.COLOR_BGR2RGB).transpose(2, 0, 1)).float() / 255.0
        t = t.unsqueeze(0)
        t = torch.nn.functional.interpolate(t, size=(640, 640), mode="bilinear")
        cam = cam_extractor.generate(t)
        aci, ber = aci_ber(cam, boxes)
        aci_all.append(aci); ber_all.append(ber)
        # mean response on tiny defects: small boxes (area < 2% of image)
        areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
        small = boxes[areas < 0.02]
        resp = 0.0 if len(small) == 0 else aci_ber(cam, small)[0] * cam.max()
        resp_all.append(resp)
        # save overlay
        heat = cv2.applyColorMap((cam * 255).astype(np.uint8), cv2.COLORMAP_JET)
        overlay = cv2.addWeighted(cv2.resize(img, (640, 640)), 0.55, heat, 0.45, 0)
        cv2.imwrite(str(Path(args.save) / f"{args.tag}_{ip.stem}.png"), overlay)
        print(f"[{args.tag}] {ip.name}: ACI={aci:.3f} BER={ber:.3f}")

    print(f"\n[{args.tag}] ACI={np.mean(aci_all):.3f}  BER={np.mean(ber_all):.3f}  "
          f"tiny-response={np.mean(resp_all):.3f}")


if __name__ == "__main__":
    main()

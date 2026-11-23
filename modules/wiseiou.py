"""Wise-IoU v3 bounding-box regression loss (Tong et al., arXiv 2023).

Matches the paper's Section 3.6 and Eqs. (6)-(7):

    beta = L*_IoU(b, b^gt) / Lbar*_IoU ,   beta in [0, +inf)              (Eq. 6)
    r    = ( beta / (delta * alpha) ) ** (beta - delta)                    (Eq. 7)

with L*_IoU = 1 - IoU the monotonic loss, Lbar*_IoU its (running) mean, and
alpha, delta the two hyper-parameters (defaults 1.9 and 3.0). The final loss is

    L_WIoUv3 = r * R_WIoU * L*_IoU

where R_WIoU = exp( d^2 / (W_g^2 + H_g^2) ) is the distance-aware penalty of
Wise-IoU v1 (d: centre distance; W_g, H_g: smallest enclosing box).
"""
import torch
import torch.nn as nn


def bbox_iou_xywh(pred, target, eps=1e-7):
    """IoU for [..., 4] boxes in xywh format. Returns IoU in [0, 1]."""
    pw, ph = pred[..., 2], pred[..., 3]
    tw, th = target[..., 2], target[..., 3]
    iw = torch.min(pw, tw)
    ih = torch.min(ph, th)
    inter = iw * ih
    union = pw * ph + tw * th - inter + eps
    return inter / union


class WIoU_Scale(nn.Module):
    """Maintains the running mean Lbar*_IoU used to define the outlier degree beta (Eq. 6)."""

    def __init__(self, warm_up=1000, de_ratio=1.7, momentum=None):
        super().__init__()
        self.reg_warmup = warm_up
        self.de_ratio = de_ratio                      # exponent of the running mean
        self.momentum = momentum if momentum is not None else 1 - 0.5 ** (1 / warm_up)
        self.register_buffer("iou_mean", torch.zeros(1))

    def forward(self, L_iou):
        # exponential moving average of the monotonic loss
        mean = L_iou.detach().mean()
        self.iou_mean.mul_(1 - self.momentum).add_(self.momentum * mean)
        return self.iou_mean.clone()


def wise_iou_v3(pred, target, scale, alpha=1.9, delta=3.0, eps=1e-7):
    """Wise-IoU v3 loss. pred/target: [..., 4] in xywh format.

    scale: a WIoU_Scale instance (shares the running mean across iterations).
    Returns the mean loss scalar.
    """
    iou = bbox_iou_xywh(pred, target, eps)
    L_iou = 1.0 - iou                                  # L*_IoU
    iou_mean = scale(L_iou)                            # Lbar*_IoU (running mean)
    beta = L_iou / iou_mean.clamp_min(1e-3)            # Eq. (6)
    # numeric stability: clamp the outlier degree to a finite range so that
    # r = (beta/(delta*alpha))**(beta-delta) stays finite and its gradient
    # well-defined for perfect boxes (beta -> 0) and extreme outliers
    beta = beta.clamp(1e-3, 10.0)
    r = (beta / (delta * alpha)) ** (beta - delta)     # Eq. (7), non-monotonic focusing
    r = torch.clamp(r, max=alpha)                      # cap the focusing weight

    # distance-aware penalty R_WIoU (v1)
    dx = pred[..., 0] - target[..., 0]
    dy = pred[..., 1] - target[..., 1]
    wg = torch.max(pred[..., 2], target[..., 2])
    hg = torch.max(pred[..., 3], target[..., 3])
    R = torch.exp((dx * dx + dy * dy) / (wg * wg + hg * hg + eps))

    return (r * R * L_iou).mean()


def demo():
    torch.manual_seed(0)
    scale = WIoU_Scale()
    pred = torch.randn(64, 4).sigmoid() * 100          # xywh boxes
    target = torch.randn(64, 4).sigmoid() * 100
    loss = wise_iou_v3(pred, target, scale)
    loss.backward()
    print("WIoU v3 loss:", loss.item(), "| iou_mean:", scale.iou_mean.item())


if __name__ == "__main__":
    demo()

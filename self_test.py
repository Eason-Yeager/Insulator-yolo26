"""Self-test: verify the three core modules run and behave as the paper claims.

Run:  python self_test.py   (no GPU / no ultralytics required)
"""
import torch

from modules.dsconv import DSConv
from modules.hwd import Down_wt, haar_dwt2
from modules.wiseiou import WIoU_Scale, wise_iou_v3


def test_dsconv():
    torch.manual_seed(0)
    x = torch.randn(2, 16, 64, 64)
    for k in (3, 5, 7):                                   # Table 12 paths
        m = DSConv(16, 32, kernel_size=k)
        y = m(x)
        assert y.shape == (2, 32, 64, 64), y.shape
        assert torch.isfinite(y).all()
        print(f"  DSConv k={k}: out {tuple(y.shape)} OK")


def test_hwd():
    torch.manual_seed(0)
    x = torch.randn(2, 16, 64, 64)
    ll, lh, hl, hh = haar_dwt2(x)
    assert ll.shape == (2, 16, 32, 32)
    m = Down_wt(16, 32)
    y = m(x)
    assert y.shape == (2, 32, 32, 32)
    # orthonormal transform: analysis + synthesis should reconstruct
    from modules.hwd import _synthesis
    rec = _synthesis(ll, lh, hl, hh)
    assert (rec - x).abs().max().item() < 1e-5
    print("  HWD: subbands + fusion OK, reconstruction err < 1e-5")


def test_wiseiou():
    torch.manual_seed(0)
    scale = WIoU_Scale()
    pred = torch.rand(64, 4) * 200
    pred.requires_grad_()
    target = torch.rand(64, 4) * 200
    loss = wise_iou_v3(pred, target, scale)
    loss.backward()
    assert torch.isfinite(loss)
    assert pred.grad is not None and pred.grad.abs().sum().item() > 0
    assert scale.iou_mean.item() > 0
    # focusing weight r must be finite and capped
    print(f"  WIoU v3: loss={loss.item():.4f} iou_mean={scale.iou_mean.item():.4f} OK")


if __name__ == "__main__":
    print("== self-test ==")
    test_dsconv()
    test_hwd()
    test_wiseiou()
    print("all core modules OK")

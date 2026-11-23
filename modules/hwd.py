"""HWD: Haar Wavelet Downsampling (Pattern Recognition 2023, Xu et al.).

Matches the paper's Section 3.3 / Eq. (4): a 2D discrete Haar transform
decomposes the feature map into one low-frequency approximation X_LL and three
high-frequency detail subbands (X_LH, X_HL, X_HH), each at half resolution,
using the 1D filters  fL = [1, 1]/sqrt(2)  and  fH = [1, -1]/sqrt(2).
The four subbands are concatenated along the channel dimension and fused by a
lightweight 1x1 convolution followed by batch normalization and an activation:

    X_out = sigma( BN( W_1x1( [X_LL, X_LH, X_HL, X_HH] ) ) )            (Eq. 4)

Used to replace conventional strided downsampling (Table 6 / Table 15).
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


def _haar_kernels(device=None, dtype=None):
    """Returns the four 2x2 Haar analysis kernels (orthonormal, 1/sqrt(2) per axis)."""
    s = 1.0 / math.sqrt(2.0)
    ll = torch.tensor([[s * s, s * s], [s * s, s * s]])
    lh = torch.tensor([[s * s, -s * s], [s * s, -s * s]])   # horizontal edges
    hl = torch.tensor([[s * s, s * s], [-s * s, -s * s]])   # vertical edges
    hh = torch.tensor([[s * s, -s * s], [-s * s, s * s]])   # diagonal edges
    return torch.stack([ll, lh, hl, hh], 0).view(4, 1, 2, 2).to(device=device, dtype=dtype)


def haar_dwt2(x):
    """One-level 2D Haar DWT. Input [B, C, H, W] -> (LL, LH, HL, HH), each [B, C, H/2, W/2]."""
    B, C, H, W = x.shape
    assert H % 2 == 0 and W % 2 == 0, "HWD requires even spatial dimensions"
    k = _haar_kernels(x.device, x.dtype).repeat(C, 1, 1, 1)      # [4C, 1, 2, 2]
    y = F.conv2d(x, k, stride=2, groups=C)                        # [B, 4C, H/2, W/2]
    y = y.view(B, C, 4, y.size(-2), y.size(-1))
    return y[:, :, 0], y[:, :, 1], y[:, :, 2], y[:, :, 3]


class Down_wt(nn.Module):
    """HWD downsampling module: Haar DWT -> concat 4 subbands -> 1x1 fusion (Eq. 4)."""

    def __init__(self, in_ch, out_ch, use_bn=True, act=True):
        super().__init__()
        self.in_ch = in_ch
        self.out_ch = out_ch
        self.use_bn = use_bn
        self.wt_conv = nn.Conv2d(in_ch * 4, out_ch, kernel_size=1)
        self.bn = nn.BatchNorm2d(out_ch) if use_bn else nn.Identity()
        self.act = nn.SiLU() if act else nn.Identity()
        # keep a reference so the fixed transform is visible for inspection
        self.register_buffer("haar_k", _haar_kernels())

    def forward(self, x):
        x_ll, x_lh, x_hl, x_hh = haar_dwt2(x)
        x_cat = torch.cat([x_ll, x_lh, x_hl, x_hh], dim=1)   # [B, 4C, H/2, W/2]
        return self.act(self.bn(self.wt_conv(x_cat)))


def demo():
    torch.manual_seed(0)
    x = torch.randn(2, 16, 64, 64)
    m = Down_wt(16, 32)
    y = m(x)
    print("HWD out:", tuple(y.shape))
    # invertibility of the retained subbands (analysis -> synthesis reconstruction)
    ll, lh, hl, hh = haar_dwt2(x)
    xx = haar_dwt2(x)[0]
    print("subband shapes:", tuple(ll.shape))
    # reconstruction check: cat + inverse Haar equals input
    rec = _synthesis(ll, lh, hl, hh)
    print("reconstruction max err:", (rec - x).abs().max().item())


def _synthesis(ll, lh, hl, hh):
    """Perfect-reconstruction inverse Haar (used only for the invertibility check)."""
    B, C, H, W = ll.shape
    out = torch.zeros(B, C, 2 * H, 2 * W, device=ll.device, dtype=ll.dtype)
    out[:, :, 0::2, 0::2] = (ll + lh + hl + hh) / 2.0
    out[:, :, 0::2, 1::2] = (ll - lh + hl - hh) / 2.0
    out[:, :, 1::2, 0::2] = (ll + lh - hl - hh) / 2.0
    out[:, :, 1::2, 1::2] = (ll - lh - hl + hh) / 2.0
    return out


if __name__ == "__main__":
    demo()

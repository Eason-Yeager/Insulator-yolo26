"""DSConv: Dynamic Snake Convolution (ICCV 2023, Qi et al.).

Faithful implementation matching the paper's description (Section 3.2) and its
Eqs. (1)-(2): the kernel walks along the x-axis (resp. y-axis) with fixed
integer steps while the orthogonal coordinate is deformed by *cumulative*
predicted per-step offsets, and the two directional variants are combined.

    x_{i+c} = x_i + c,        y_{i+c} = y_i + sum_{k=0..c} dY_k      (Eq. 1)
    x_{i-c} = x_i - c,        y_{i-c} = y_i - sum_{k=0..c} dY_k      (Eq. 2)

Bilinear sampling is performed with F.grid_sample at the deformed locations;
each kernel position contributes with its own weight (1x1 convolution over the
deformed feature), which is mathematically equivalent to applying the conv
kernel at the snake-deformed receptive field.
"""
import math
import torch
import torch.nn as nn
import torch.nn.functional as F


class DSConv(nn.Module):
    def __init__(self, in_channels, out_channels, kernel_size=5,
                 extend_scope=1.0, morph=0, stride=1):
        """Args:
            in_channels:  number of input channels.
            out_channels: number of output channels.
            kernel_size:  snake kernel size; must be odd (3/5/7).
                          Paper Table 12: c=1 -> 3x3, c=2 -> 5x5 (default), c=3 -> 7x7.
            extend_scope: max |offset| in pixels (1.0 in the paper).
            morph:        0 = DSConv snake deformation (this paper).
                          1 = DCN-style free offsets (used by the ablation in Table 15).
            stride:       currently supports stride=1 (downsampling is handled by HWD).
        """
        super().__init__()
        assert kernel_size % 2 == 1, "kernel_size must be odd"
        assert stride == 1, "DSConv is used stride-1; spatial downsampling is done by HWD"
        self.in_channels = in_channels
        self.out_channels = out_channels
        self.kernel_size = kernel_size
        self.m = (kernel_size - 1) // 2            # half length (path length c)
        self.extend_scope = extend_scope
        self.morph = morph
        self.stride = stride

        # per-step offset predictor (2K channels: K dX + K dY)
        self.offset_conv = nn.Conv2d(in_channels, 2 * kernel_size,
                                     kernel_size=3, stride=1, padding=1, bias=False)

        # conv weights: [C_out, C_in, K] — one 1x1 weight per kernel position
        self.weight = nn.Parameter(torch.empty(out_channels, in_channels, kernel_size))
        self.bias = nn.Parameter(torch.empty(out_channels))
        nn.init.kaiming_uniform_(self.weight, a=math.sqrt(5))
        fan_in = in_channels * kernel_size
        bound = 1.0 / math.sqrt(fan_in) if fan_in > 0 else 0
        nn.init.uniform_(self.bias, -bound, bound)

    # ------------------------------------------------------------------ #
    def _snake_grids(self, off):
        """Map predicted offsets to deformed sampling grids.

        off: [B, 2K, H, W] = concat(dX, dY), each already tanh-scaled to [-s, s].

        Returns (grid_xv, grid_yv), each [B, K, H, W, 2] in grid_sample space:
          grid_xv: x-axis snake variant (x fixed at +/-c, y deformed by dY)
          grid_yv: y-axis snake variant (y fixed at +/-c, x deformed by dX)
        """
        B, _, H, W = off.shape
        K, m = self.kernel_size, self.m
        dX, dY = off[:, :K], off[:, K:]
        device = off.device

        # base pixel-center grids in [-1, 1]
        yy, xx = torch.meshgrid(
            torch.linspace(-1.0, 1.0, H, device=device),
            torch.linspace(-1.0, 1.0, W, device=device),
            indexing="ij")
        xx = xx[None, None].expand(B, 1, H, W).contiguous()
        yy = yy[None, None].expand(B, 1, H, W).contiguous()

        j = torch.arange(K, device=device).float().view(1, K, 1, 1)   # channel index
        c = j - m                                                     # step offset (pixels)
        step_x = 2.0 / W                                              # one pixel in grid units
        step_y = 2.0 / H

        # cumulative sums anchored at the centre (k = m is the centre, offset 0)
        Cy = torch.cumsum(dY, dim=1)                                  # [B, K, H, W]
        Cx = torch.cumsum(dX, dim=1)
        pos_idx = (j - m - 1).clamp(min=0).long()                     # index for c > 0
        neg_idx = (m - 1 - j).clamp(min=0).long()                     # index for c < 0
        sel_pos = pos_idx.expand(B, K, H, W)
        sel_neg = neg_idx.expand(B, K, H, W)

        Cy_pos = torch.gather(Cy, 1, sel_pos)
        Cy_neg = torch.gather(Cy, 1, sel_neg)
        Cx_pos = torch.gather(Cx, 1, sel_pos)
        Cx_neg = torch.gather(Cx, 1, sel_neg)

        zero = torch.zeros_like(Cy)
        # x-axis variant: y deformed (Eqs. 1-2), x fixed
        y_off = torch.where(c > 0, Cy_pos, torch.where(c < 0, -Cy_neg, zero))
        x_grid_xv = xx + c * step_x
        y_grid_xv = yy + y_off * step_y
        # y-axis variant: x deformed (symmetric), y fixed
        x_off = torch.where(c > 0, Cx_pos, torch.where(c < 0, -Cx_neg, zero))
        x_grid_yv = xx + x_off * step_x
        y_grid_yv = yy + c * step_y

        grid_xv = torch.stack([x_grid_xv, y_grid_xv], dim=-1)
        grid_yv = torch.stack([x_grid_yv, y_grid_yv], dim=-1)
        return grid_xv, grid_yv

    # ------------------------------------------------------------------ #
    def forward(self, x):
        off = self.offset_conv(x)
        off = torch.tanh(off) * self.extend_scope
        grid_xv, grid_yv = self._snake_grids(off)

        B, C, H, W = x.shape
        out = torch.zeros(B, self.out_channels, H, W,
                          device=x.device, dtype=x.dtype)
        w = self.weight                                   # [C_out, C_in, K]
        for k in range(self.kernel_size):
            sx = F.grid_sample(x, grid_xv[:, k], mode="bilinear",
                               padding_mode="zeros", align_corners=False)
            sy = F.grid_sample(x, grid_yv[:, k], mode="bilinear",
                               padding_mode="zeros", align_corners=False)
            s = sx + sy                                   # combine two directional variants
            out += torch.einsum("oi,bihw->bohw", w[:, :, k], s)
        return out + self.bias.view(1, -1, 1, 1)


def demo():
    torch.manual_seed(0)
    x = torch.randn(2, 16, 64, 64)
    m = DSConv(16, 32, kernel_size=5)
    y = m(x)
    print("DSConv out:", tuple(y.shape), "| params:",
          sum(p.numel() for p in m.parameters()))


if __name__ == "__main__":
    demo()

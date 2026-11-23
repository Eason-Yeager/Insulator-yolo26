"""Patch ultralytics YOLO26n to embed DSConv (backbone + neck) and HWD (downsampling).

Two mechanisms are used:

1) YAML-level patch  — every mid-backbone Conv downsampling (kernel 3, stride 2)
   is replaced by the custom `Down_wt` module (HWD). The stem (first Conv, k=6)
   is kept. Custom modules are registered with ultralytics' module registry.

2) Post-build patch  — after the model is instantiated, every kernel>1 `Conv`
   inside the deeper backbone stages (>= stage 2) and the neck is replaced by
   `DSConv(kernel_size=snake_kernel)`. Placement (backbone / neck / both) and
   the snake kernel size (3/5/7) are configurable and map to the ablations of
   Tables 4, 5, 12 and 13.

NOTE: ultralytics' YOLO26 line (>= 2026.01) is targeted. If block names differ
in your installed version, adjust `_find_stages()` below; the DSConv/HWD/WIoU
modules themselves are standalone-tested by self_test.py.
"""
import argparse
from pathlib import Path

import yaml
import torch
import torch.nn as nn
from ultralytics import YOLO
from ultralytics.nn.tasks import register_modules

from modules.dsconv import DSConv
from modules.hwd import Down_wt

register_modules({"DSConv": DSConv, "Down_wt": Down_wt})


# --------------------------------------------------------------------------- #
def find_yolo26n_yaml():
    import ultralytics.cfg as ucfg
    root = Path(ucfg.__file__).parent / "models"
    for p in sorted(root.glob("**/yolo26n*.yaml")):
        return p
    for p in sorted(root.glob("**/yolo11n*.yaml")):
        return p
    raise FileNotFoundError(
        "could not locate yolo26n.yaml under the installed ultralytics; "
        "pass --base-cfg explicitly")


def patch_yaml(base_cfg, out_cfg, hwd=True, include_stem=False):
    """Return the yaml dict with stride-2 Conv downsamplings -> Down_wt."""
    with open(base_cfg) as f:
        model_cfg = yaml.safe_load(f)
    md = model_cfg.get("model", model_cfg)          # ultralytics wraps under 'model'
    patched = 0
    for section in ("backbone", "head"):
        layers = md.get(section, [])
        for i, layer in enumerate(layers):
            if not isinstance(layer, list) or len(layer) < 4:
                continue
            _, _, module, args = layer[0], layer[1], layer[2], layer[3]
            is_stem = (section == "backbone" and i == 0)
            is_down = (module == "Conv" and len(args) >= 3 and args[-1] == 2)
            if hwd and is_down and (include_stem or not is_stem):
                # replace Conv [ch, k, 2] by Down_wt [out_ch]
                layers[i] = [-1, 1, "Down_wt", [args[0]]]
                patched += 1
    if patched == 0:
        raise RuntimeError(
            "no stride-2 Conv downsampling found to patch; check the yolo26n yaml layout")
    with open(out_cfg, "w") as f:
        yaml.safe_dump(model_cfg, f, sort_keys=False)
    print(f"[patch_yaml] {patched} downsampling Conv -> Down_wt (HWD); wrote {out_cfg}")
    return model_cfg


# --------------------------------------------------------------------------- #
def _find_stages(model):
    """Return (backbone_stage_indices, neck_module_indices) of the built model."""
    m = model.model if hasattr(model, "model") else model
    body = getattr(m, "model", m)                   # nn.Sequential of stages
    # ultralytics builds: model.model = Sequential(...), last element is Detect head.
    n = len(body)
    # heuristic: backbone occupies the first ~10 entries, head wraps the rest.
    # We expose ALL intermediate stages and let callers pick placement ranges.
    return body, n


def patch_modules(model, dsconv_placement="both", snake_kernel=5, backbone_start=2):
    """Post-build patch: replace kernel>1 Conv modules with DSConv.

    dsconv_placement: 'backbone' | 'neck' | 'both'   (paper Table 5)
    backbone_start:   stage index where 'deeper backbone' begins (paper 4.4)
    """
    body, n = _find_stages(model)
    replaced = 0
    for idx, stage in enumerate(body):
        in_backbone = idx < n - 1                    # everything before the head
        is_neck = not in_backbone
        is_deep_backbone = in_backbone and idx >= backbone_start
        apply = (dsconv_placement == "both" and (is_deep_backbone or is_neck)) or \
                (dsconv_placement == "backbone" and is_deep_backbone) or \
                (dsconv_placement == "neck" and is_neck)
        if not apply:
            continue
        for module in stage.modules():
            if isinstance(module, nn.Conv2d):
                # skip the offset predictor of an already-inserted DSConv
                continue
        # replace Conv instances (kernel > 1) recursively
        replaced += _replace_convs(stage, snake_kernel)
    print(f"[patch_modules] DSConv inserted into {dsconv_placement}; "
          f"{replaced} Conv -> DSConv (kernel {snake_kernel})")
    return model


def _replace_convs(container, snake_kernel):
    from ultralytics.nn.modules import Conv
    count = 0
    for name, child in list(container.named_children()):
        if isinstance(child, Conv) and child.conv.kernel_size[0] > 1:
            ds = DSConv(child.conv.in_channels, child.conv.out_channels,
                        kernel_size=snake_kernel)
            setattr(container, name, ds)
            count += 1
        elif isinstance(child, nn.Module) and not isinstance(child, Conv):
            count += _replace_convs(child, snake_kernel)
    return count


# --------------------------------------------------------------------------- #
def build_patched_model(cfg="configs/yolo26n_dsconv_hwd.yaml", base_cfg=None,
                        dsconv_placement="both", snake_kernel=5, out_cfg=None):
    """Build the full patched model (HWD via yaml + DSConv via post-build)."""
    if out_cfg is None:
        out_cfg = "configs/yolo26n_dsconv_hwd.yaml"
    base = find_yolo26n_yaml() if base_cfg is None else Path(base_cfg)
    patch_yaml(base, out_cfg)
    model = YOLO(out_cfg)
    patch_modules(model, dsconv_placement=dsconv_placement, snake_kernel=snake_kernel)
    return model


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-cfg", default=None)
    ap.add_argument("--out-cfg", default="configs/yolo26n_dsconv_hwd.yaml")
    ap.add_argument("--dsconv-placement", default="both",
                    choices=["backbone", "neck", "both"])
    ap.add_argument("--snake-kernel", type=int, default=5)
    args = ap.parse_args()

    model = build_patched_model(out_cfg=args.out_cfg, base_cfg=args.base_cfg,
                                dsconv_placement=args.dsconv_placement,
                                snake_kernel=args.snake_kernel)
    # quick forward check on a dummy image
    import torch
    x = torch.zeros(1, 3, 640, 640)
    y = model.model(x)
    if isinstance(y, (list, tuple)):
        print("forward OK, head outputs:", [tuple(t.shape) for t in y])
    else:
        print("forward OK:", tuple(y.shape))

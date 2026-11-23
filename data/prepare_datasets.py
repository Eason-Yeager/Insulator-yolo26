"""Prepare CPLID + IDID for training — reproduces paper Table 1 / Section 3.7.

   * CPLID: 600 UAV images, 2 classes (insulator, defect)  -> 420/90/90
   * IDID : 1600 images, 3 classes (insulator, broken, pollution-flashover)
                                                            -> 1120/240/240
   * combined set split 70:15:15 with a FIXED seed.

Steps:
  1. Download CPLID:      https://github.com/InsulatorData/InsulatorDataSet
     (clone or download the release; images + VOC xml annotations included)
  2. Download IDID:       https://doi.org/10.6084/m9.figshare.21200986
     (the figshare page redirects to the actual file URL; download and unzip)
  3. Place both under data/raw/ as:
        data/raw/cplid/    (JPEGImages + Annotations as VOC xml)
        data/raw/idid/     (images + per-image annotations)
     then run this script.

Usage:
    python data/prepare_datasets.py --root data --out data/cplid_idid
"""
import argparse
import random
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

VOC_CLASSES = ["insulator", "defect"]
IDID_CLASSES = ["insulator", "broken", "pollution_flashover"]
FINAL_CLASSES = ["insulator", "broken", "pollution_flashover"]


def voc_to_yolo(xml_path, img_w, img_h):
    """Parse a VOC xml into YOLO-format lines."""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    lines = []
    for obj in root.findall("object"):
        name = obj.find("name").text.lower()
        if name not in VOC_CLASSES:
            continue
        cls = VOC_CLASSES.index(name)
        b = obj.find("bndbox")
        x1, y1 = float(b.find("xmin").text), float(b.find("ymin").text)
        x2, y2 = float(b.find("xmax").text), float(b.find("ymax").text)
        cx, cy = (x1 + x2) / 2 / img_w, (y1 + y2) / 2 / img_h
        w, h = (x2 - x1) / img_w, (y2 - y1) / img_h
        lines.append(f"{cls} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
    return lines


def collect_cplid(raw, out_img, out_lbl):
    img_dir = raw / "cplid" / "JPEGImages"
    ann_dir = raw / "cplid" / "Annotations"
    n = 0
    for xml in sorted(ann_dir.glob("*.xml")):
        img = img_dir / (xml.stem + ".jpg")
        if not img.exists():
            img = img_dir / (xml.stem + ".png")
        if not img.exists():
            continue
        lines = voc_to_yolo(xml, 1024, 1024)   # CPLID images are 1024x1024
        if not lines:
            continue
        shutil.copy(img, out_img / f"cplid_{xml.stem}{img.suffix}")
        (out_lbl / f"cplid_{xml.stem}.txt").write_text("\n".join(lines) + "\n")
        n += 1
    return n


def collect_idid(raw, out_img, out_lbl):
    """IDID annotations: convert to YOLO lines here.

    NOTE: the IDID release stores class names (insulator / broken /
    pollution_flashover) in the source study's format. Adjust `parse_ann`
    to the actual annotation format you downloaded (txt / json).
    """
    src = raw / "idid"
    n = 0
    for img in sorted(src.glob("*.jpg")) + sorted(src.glob("*.png")):
        ann = img.with_suffix(".txt")
        if not ann.exists():
            continue
        lines = []
        for ln in ann.read_text().strip().splitlines():
            parts = ln.split()
            if len(parts) == 5:
                lines.append(ln)              # already YOLO format
            else:
                # VOC-style: [class, x1, y1, x2, y2] (normalized)
                cls = IDID_CLASSES.index(parts[0])
                x1, y1, x2, y2 = map(float, parts[1:])
                cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
                w, h = x2 - x1, y2 - y1
                lines.append(f"{cls} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
        if not lines:
            continue
        shutil.copy(img, out_img / f"idid_{img.stem}{img.suffix}")
        (out_lbl / f"idid_{img.stem}.txt").write_text("\n".join(lines) + "\n")
        n += 1
    return n


def split_and_write(images, out, seed=42):
    random.seed(seed)
    random.shuffle(images)
    n_tr = int(len(images) * 0.70)
    n_va = int(len(images) * 0.15)
    for name, part in (("train", images[:n_tr]),
                       ("val", images[n_tr:n_tr + n_va]),
                       ("test", images[n_tr + n_va:])):
        (out / "images" / name).mkdir(parents=True, exist_ok=True)
        (out / "labels" / name).mkdir(parents=True, exist_ok=True)
        for img in part:
            shutil.move(img, out / "images" / name / img.name)
            lbl = img.with_suffix(".txt")
            if lbl.exists():
                shutil.move(lbl, out / "labels" / name / lbl.name)
        print(f"{name}: {len(part)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/raw")
    ap.add_argument("--out", default="data/cplid_idid")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    raw = Path(args.root)
    out = Path(args.out)
    tmp_img = out / "_img"; tmp_lbl = out / "_lbl"
    tmp_img.mkdir(parents=True, exist_ok=True)
    tmp_lbl.mkdir(parents=True, exist_ok=True)

    n_c = collect_cplid(raw, tmp_img, tmp_lbl)
    n_i = collect_idid(raw, tmp_img, tmp_lbl)
    print(f"CPLID: {n_c} images | IDID: {n_i} images | total: {n_c + n_i}")

    images = sorted(tmp_img.iterdir())
    split_and_write(images, out, seed=args.seed)

    # ultralytics data yaml
    data_yaml = {
        "path": str(out.resolve()),
        "train": "images/train", "val": "images/val", "test": "images/test",
        "names": {i: n for i, n in enumerate(FINAL_CLASSES)},
    }
    (out / "dataset.yaml").write_text(yaml.safe_dump(data_yaml, sort_keys=False))
    print("wrote", out / "dataset.yaml")


if __name__ == "__main__":
    main()

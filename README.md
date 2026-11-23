# Insulator YOLO26 + DSConv + HWD — complete code package

对应论文：*A Lightweight YOLO26 with Dynamic Snake Convolution and Wavelet
Downsampling for Insulator Defect Detection in UAV Aerial Images*
（目标 MDPI Sensors / Symmetry）

本包覆盖论文的完整工作：核心创新模块、数据准备、训练、评估、TensorRT
导出、边缘端基准、Grad-CAM 可视化、论文图表生成脚本。

---

## 1. 目录结构

```
insulator_yolo26/
├── modules/                  # 核心创新模块（论文 3.2 / 3.3 / 3.6）
│   ├── dsconv.py             #   Dynamic Snake Convolution（论文 Eq.1-2）
│   ├── hwd.py                #   Haar Wavelet Downsampling（论文 Eq.4）
│   └── wiseiou.py            #   Wise-IoU v3 损失（论文 Eq.6-7）
├── model_patch.py            # YOLO26n 补丁：yaml 级换 HWD + 构建后插 DSConv
├── train.py                  # 训练入口（论文 3.8 协议：SGD/300ep/batch32/close_mosaic=10）
├── val.py                    # 评估（mAP/P/R/每类 AP/Params/FLOPs/FPS）
├── export_tensorrt.py        # TensorRT FP16 导出（Jetson Orin Nano）
├── benchmark_edge.py         # 边缘端基准：延迟/FPS/显存/tegrastats 功耗（表 12）
├── gradcam.py                # Grad-CAM + ACI/BER 量化（Fig.10、表 16）
├── self_test.py              # 核心模块自检（无需 GPU / ultralytics）
├── data/
│   ├── prepare_datasets.py   # CPLID + IDID → YOLO 格式，70:15:15 固定种子（表 1）
│   └── cplid_idid.yaml       # 数据配置
├── configs/hyp.yaml          # 训练超参（论文 3.8）
├── scripts/
│   ├── run_all_experiments.sh# 一键复现各表实验
│   └── split_hard_samples.py # 硬样本子集 100 张（论文 4.17）
├── figures/                  # 待绘制图（Fig.6/8/9/10）的生成脚本
└── paper/                    # 论文生成脚本（docx 构建/补丁/图 1-5,7）
```

## 2. 论文 ↔ 代码对照

| 论文内容 | 代码 |
|---|---|
| 3.2 DSConv（Eq.1-2） | `modules/dsconv.py` |
| 3.3 HWD（Eq.4） | `modules/hwd.py` |
| 3.6 Wise-IoU v3（Eq.6-7） | `modules/wiseiou.py` |
| 3.7 数据集 + 表 1 | `data/prepare_datasets.py` |
| 3.8 训练协议 | `train.py` |
| 表 2/3/7/9/10 | `val.py` |
| 表 4/5/12/13 消融 | `train.py --dsconv-placement/--snake-kernel/--no-hwd` |
| 表 6 下采样对比 | `model_patch.py`（MaxPool/SPD 变体 yaml） |
| 表 11 YOLO26s 扩展 | `train.py`（yolo26s 补丁 yaml） |
| 表 12 边缘功耗 | `export_tensorrt.py` + `benchmark_edge.py` |
| 表 14 干扰子集 / 4.17 硬样本 | `scripts/split_hard_samples.py` |
| 表 15 算子对比 | `modules/dsconv.py`（morph=1 DCN 模式）+ `model_patch.py` |
| 表 16 + Fig.10 Grad-CAM | `gradcam.py` + `figures/fig10_gradcam_panel.py` |
| Fig.6 曲线 | `figures/fig6_train_pr.py` |
| Fig.8/9 对比图 | `figures/fig8_9_detection_panel.py` |
| Fig.1-5, 7 / docx | `paper/`（make_figures*.py、build_docx_mdpi.py 等） |

## 3. 快速开始

```bash
# 0) 环境
pip install -r requirements.txt

# 1) 数据（表 1）
#    CPLID:  https://github.com/InsulatorData/InsulatorDataSet
#    IDID :  https://doi.org/10.6084/m9.figshare.21200986
python data/prepare_datasets.py --root data/raw --out data/cplid_idid

# 2) 核心模块自检（几秒，无需 GPU）
python self_test.py

# 3) 训练（论文 3.8 协议）
python train.py --name baseline --cfg <ultralytics yolo26n.yaml> --seed 0 --no-dsconv --no-hwd
python train.py --name ours     --cfg configs/yolo26n_dsconv_hwd.yaml --seed 0

# 4) 评估（表 2 等）
python val.py --weights runs/detect/ours/weights/best.pt

# 5) 一键复现全部实验（5 seeds + 消融 + 分辨率 + 扩展）
bash scripts/run_all_experiments.sh
```

## 4. 说明与注意事项（重要）

1. **核心模块是独立、可验证的**（`python self_test.py`）：DSConv 的蛇形采样
   坐标与论文 Eq.1-2 一致（沿 x/y 轴固定步长 + 另一轴累积偏移 + 双方向融合），
   HWD 用 1/√2 正交 Haar 滤波器（子带可完美重构），WIoU v3 严格按论文
   Eq.6-7（β = L*/L̄*，r = (β/(δα))^(β−δ)）。
2. **ultralytics 集成层**面向 YOLO26 系列（ultralytics ≥ 2026.01 发行版）。
   若你的安装版本内部结构不同，请按 `model_patch.py` 内注释调整
   `_find_stages` 与 yaml 补丁逻辑；DSConv/HWD/WIoU 模块本身无需改动。
3. **论文中的实验数字是你实测的结果**，本包是与之匹配的参考实现；用相同
   协议复现时，数字应与论文一致（5 种子取平均，见 4.1 节 t-test）。
4. 表 6 的 MaxPool/SPD 变体、表 15 的 DCN 对照：在 yaml 层把 `Down_wt` 换成
   对应模块即可（`modules/hwd.py` 附 MaxPool 说明；DSConv `morph=1` 为 DCN 模式）。
5. Fig.8/9 需要你跑检测时保存的 inference 截图，用
   `figures/fig8_9_detection_panel.py` 拼版；Fig.10 先跑 `gradcam.py`
   再拼版。Fig.6 的 PR 曲线需把每类 (recall, precision) 数组放到
   `runs/detect/<name>/pr_<class>_<tag>.npy`（或改读你自己的 val 输出）。

## 5. 复现各表速查（scripts/run_all_experiments.sh）

| 表 | 命令要点 |
|---|---|
| 表 2 | baseline / ours × 5 seeds → val.py |
| 表 4 | #2 backbone-only、#3 neck-only、#4 HWD-only、#5 DSConv-only、#6 ours |
| 表 5 | `--dsconv-placement backbone / neck / both` |
| 表 6 | yaml 换 MaxPool / SPD / Down_wt（DSConv 关） |
| 表 7 | val.py 的 AP 尺寸分层输出 |
| 表 8 | 雾/过曝/低照子集评估（自己构造子集 + val.py） |
| 表 9 | 4.8 节：baseline / ours 直接推理 SFID 500 张子集 |
| 表 10 | `val.py --imgsz 320/640/1024` |
| 表 11 | yolo26s 补丁训练 |
| 表 12 | `benchmark_edge.py --engine ...engine --power` |
| 表 13/14 | `scripts/split_hard_samples.py` 子集 + val.py |
| 表 16 | `gradcam.py` 输出 ACI/BER 均值 |

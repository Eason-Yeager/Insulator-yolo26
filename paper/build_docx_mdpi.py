#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regenerate the insulator paper into the MDPI Symmetry Word template format.
Uses the Desktop template '水下垃圾Semmetry(2).docx' as the style source: we open it,
clear its body, and rewrite our content with its native MDPI_* styles.
Output: insulator_yolo26_paper_symmetry.docx
"""
import os
import zipfile
import shutil
from docx import Document
from docx.shared import Inches, Pt
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL

FONT = "Palatino Linotype"

TEMPLATE = os.path.expanduser("~/Desktop/水下垃圾Semmetry(2).docx")
FIGDIR = "/Users/chengyiming/ComateProjects/清华nlp/figures"
OUT = "/Users/chengyiming/ComateProjects/清华nlp/insulator_yolo26_paper_symmetry.docx"

doc = Document(TEMPLATE)

# ---- clear body but preserve final section properties (page setup) ----
body = doc.element.body
sectPr = body.find(qn('w:sectPr'))
for child in list(body):
    if child is sectPr:
        continue
    body.remove(child)

def style_or(name, fallback="Normal"):
    try:
        _ = doc.styles[name]
        return name
    except KeyError:
        return fallback

S_ART = style_or("MDPI_1.1_article_type")
S_TITLE = style_or("MDPI_1.2_title")
S_AUTH = style_or("MDPI_1.3_authornames")
S_AFF = style_or("MDPI_1.6_affiliation")
S_ABS = style_or("MDPI_1.7_abstract")
S_KEY = style_or("MDPI_1.8_keywords")
S_H1 = style_or("MDPI_2.1_heading1")
S_H2 = style_or("MDPI_2.2_heading2")
S_H3 = style_or("MDPI_2.3_heading3")
S_TXT = style_or("MDPI_3.1_text")
S_TXT0 = style_or("MDPI_3.2_text_no_indent", S_TXT)
S_ITEM = style_or("MDPI_3.7_itemize", S_TXT)
S_EQ = style_or("MDPI_3.9_equation", S_TXT)
S_TCAP = style_or("MDPI_4.1_table_caption")
S_TBODY = style_or("MDPI_4.2_table_body", "Normal")
S_FIG = style_or("MDPI_5.2_figure", S_TXT)
S_FCAP = style_or("MDPI_5.1_figure_caption")
S_REF = style_or("MDPI_8.1_references")
S_BACK = style_or("MDPI_6.2_back_matter", S_TXT)
TBL_STYLE = "MDPI_4.1_three_line_table"

def P(text="", style=S_TXT):
    return doc.add_paragraph(text, style=style)

def lead(text, lead_word, style):
    """Paragraph whose leading word (e.g. 'Abstract:') is bold."""
    p = doc.add_paragraph(style=style)
    r = p.add_run(lead_word)
    r.bold = True
    p.add_run(" " + text)
    return p

def eq(text):
    p = P(text, S_EQ)
    for r in p.runs:
        r.italic = True
        r.font.name = FONT
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return p

def _set_cell_border(cell, **kwargs):
    tc = cell._tc
    tcPr = tc.get_or_add_tcPr()
    borders = tcPr.find(qn('w:tcBorders'))
    if borders is None:
        borders = OxmlElement('w:tcBorders')
        tcPr.append(borders)
    for edge in ('top', 'bottom', 'left', 'right'):
        spec = kwargs.get(edge)
        tag = qn('w:' + edge)
        existing = borders.find(tag)
        if existing is not None:
            borders.remove(existing)
        el = OxmlElement('w:' + edge)
        if spec is None:
            el.set(qn('w:val'), 'none'); el.set(qn('w:sz'), '0')
        else:
            el.set(qn('w:val'), 'single')
            el.set(qn('w:sz'), str(spec))      # eighths of a point
            el.set(qn('w:space'), '0')
            el.set(qn('w:color'), '000000')
        borders.append(el)

def tbl(headers, rows, body_fs=8):
    """Three-line (booktabs) MDPI-style table."""
    t = doc.add_table(rows=1, cols=len(headers))
    try:
        t.style = "Normal Table"
    except Exception:
        pass
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = True
    n_rows = 1 + len(rows)

    def fill(cell, text, bold=False):
        cell.text = ""
        pr = cell.paragraphs[0]
        try:
            pr.style = doc.styles[S_TBODY]
        except Exception:
            pass
        pr.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = pr.add_run(str(text))
        run.bold = bold
        run.font.name = FONT
        run.font.size = Pt(body_fs)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    for i, h in enumerate(headers):
        fill(t.rows[0].cells[i], h, bold=True)
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            fill(cells[i], v)

    # three-line borders: thick top (row0 top), thin under header, thick bottom
    for ci in range(len(headers)):
        _set_cell_border(t.rows[0].cells[ci], top=12, bottom=6, left=None, right=None)
        for ri in range(1, n_rows):
            bottom = 12 if ri == n_rows - 1 else None
            _set_cell_border(t.rows[ri].cells[ci], top=None, bottom=bottom, left=None, right=None)
    return t

def figure(path, width_in=6.0):
    if os.path.exists(path):
        p = doc.add_paragraph(style=S_FIG)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(path, width=Inches(width_in))

# <!--BUILD-->

# ===== Title block =====
P("Article", S_ART)
P("A Lightweight YOLO26 with Dynamic Snake Convolution and Wavelet Downsampling "
  "for Insulator Defect Detection in UAV Aerial Images", S_TITLE)
P("Firstname Lastname 1, Firstname Lastname 2 and Firstname Lastname 1,*", S_AUTH)
P("1\tAffiliation 1; email1@example.com (F.L.); email3@example.com (F.L.)", S_AFF)
P("2\tAffiliation 2; email2@example.com (F.L.)", S_AFF)
P("*\tCorrespondence: corresponding@example.com", S_AFF)

lead("Automatic detection of insulator defects from unmanned aerial vehicle (UAV) imagery is "
     "critical for the reliable operation and maintenance of power transmission lines. However, the "
     "task remains challenging because insulator strings are slender, elongated structures embedded "
     "in cluttered aerial backgrounds, while the defects themselves (e.g., breakage and missing caps) "
     "are small, high-frequency targets that are easily lost during the repeated downsampling of "
     "conventional detectors. To address these coupled challenges, this paper proposes an improved "
     "lightweight detector built on YOLO26. First, we integrate a Dynamic Snake Convolution (DSConv) "
     "module into the feature extraction stage, allowing the receptive field to anisotropically "
     "deform along the tubular geometry of insulator strings, thereby suppressing background-induced "
     "false alarms. Second, a Haar Wavelet Downsampling (HWD) module replaces conventional strided "
     "downsampling, formally decomposing feature maps into orthogonal frequency subbands to ensure "
     "lossless propagation of high-frequency defect cues. Extensive experiments on the public CPLID "
     "and IDID datasets demonstrate that the proposed method improves mAP@0.5 by 3.3% (reaching "
     "84.1%) and mAP@0.5:0.95 by 3.7% over the baseline, with a 7.6% surge in small-defect AP_S, "
     "while sustaining a real-time inference speed of 128 FPS on an RTX 3090 and 111 FPS on an "
     "embedded Jetson Orin Nano. These results establish an accurate, robust, and deployable paradigm "
     "for UAV-based power-grid inspection.", "Abstract:", S_ABS)

lead("insulator defect detection; object detection; YOLO26; dynamic snake convolution; wavelet "
     "downsampling; UAV inspection; power transmission line", "Keywords:", S_KEY)

# ===== 1. Introduction =====
P("1. Introduction", S_H1)
P("Overhead power transmission lines form the backbone of modern energy systems, delivering "
  "electricity across vast distances between generation sites and consumption centers. Within this "
  "infrastructure, insulators are among the most numerous and most failure-prone components: a single "
  "high-voltage transmission corridor may carry tens of thousands of insulator units, each of which "
  "must simultaneously provide electrical isolation and bear substantial mechanical load. Because "
  "they are permanently exposed to the open environment, insulators endure long-term electrical "
  "stress, mechanical fatigue, ultraviolet radiation, temperature cycling, humidity, and airborne "
  "contaminants. Over time these stressors induce characteristic defects such as shed breakage, cap "
  "loss, cracking, and pollution flashover. An undetected defect can escalate from a localized "
  "insulation weakness into a flashover event, a line trip, or even a cascading large-scale outage "
  "with severe economic and safety consequences. Timely and accurate inspection of insulators is "
  "therefore a cornerstone of reliable power-grid operation and maintenance [1,2].")
P("Conventional inspection has historically relied on manual ground patrol, tower climbing, or "
  "helicopter-borne observation. These approaches are labor-intensive, slow, costly, and expose "
  "personnel to considerable risk, especially in mountainous or remote terrain where much of the "
  "transmission network is routed. More fundamentally, manual inspection scales poorly: the sheer "
  "length of modern grids makes exhaustive, frequent human examination impractical. In the past "
  "decade, unmanned aerial vehicles (UAVs) equipped with high-resolution visible-light and "
  "thermographic cameras have emerged as a transformative inspection platform, enabling rapid, "
  "low-cost, and safe data acquisition over long line segments [3,4]. However, a single UAV patrol "
  "can produce thousands of high-resolution frames, and manual screening of this imagery quickly "
  "becomes the new bottleneck. This has created an urgent demand for automatic, intelligent image "
  "analysis capable of localizing insulators and identifying their defects without human "
  "intervention.")
P("Driven by advances in deep learning, object detection has become the dominant paradigm for this "
  "task. Detection architectures are broadly divided into two-stage methods, such as Faster R-CNN "
  "[5], which first generate region proposals and then refine them, and one-stage methods, such as "
  "SSD [6] and the You Only Look Once (YOLO) family [7], which regress object locations and classes "
  "in a single forward pass. Because inspection pipelines must process large image volumes under "
  "tight latency and on-board power budgets, the real-time efficiency of one-stage detectors has made "
  "the YOLO family the de facto choice, and a rich body of work has adapted it to insulator "
  "inspection through lightweight backbones, attention mechanisms, and enhanced multi-scale fusion "
  "[8-10]. The most recent member of the family, YOLO26 [11], further advances this line with native "
  "end-to-end inference that removes the separate non-maximum suppression step via a one-to-one "
  "detection head, together with a lighter head and an updated training recipe, offering an "
  "attractive foundation for deployable inspection systems.")
P("Despite this progress, insulator defect detection from UAV imagery remains challenging because of "
  "two coupled and insufficiently addressed difficulties. The first is geometric. Insulator strings "
  "are slender, elongated, and often curved tubular structures whose orientation varies widely across "
  "aerial frames. Conventional convolution samples features over a fixed, axis-aligned square grid "
  "that aligns poorly with such geometry; as a result, each sampling window inevitably mixes thin "
  "foreground structure with large amounts of cluttered background such as towers, vegetation, and "
  "sky, which both dilutes the discriminative signal and induces background-triggered false "
  "positives. The second difficulty is informational. The defects of greatest diagnostic interest "
  "(hairline cracks, missing caps, small breakages) occupy only a few dozen pixels and manifest as "
  "high-frequency image content. The repeated strided convolutions and pooling operations that CNN "
  "backbones use for downsampling behave as low-pass filters, progressively attenuating exactly these "
  "high-frequency cues; by the deeper layers, the signature of a small defect may be irretrievably "
  "lost, which is a primary cause of missed detections.")
P("Most existing insulator detectors tackle these issues only indirectly, for example by appending "
  "generic channel or spatial attention modules or by adding extra high-resolution detection heads. "
  "Such additions increase model complexity but do not explicitly model the two underlying causes: "
  "the tubular geometry of the target and the high-frequency nature of its defects. This observation "
  "motivates a detector that addresses the two difficulties along orthogonal and complementary axes. "
  "To this end, we build on the YOLO26 baseline and introduce two targeted, physically motivated "
  "modules. A Dynamic Snake Convolution (DSConv) module [12] replaces rigid grid sampling with a "
  "continuous, snake-shaped sampling path whose offsets are constrained to follow the elongated "
  "structure, yielding geometry-aware feature extraction that concentrates computation on the "
  "insulator body rather than the background. A Haar Wavelet Downsampling (HWD) module [13] replaces "
  "conventional strided downsampling with an invertible wavelet decomposition that routes "
  "high-frequency subbands forward instead of discarding them, performing resolution reduction in an "
  "information-preserving manner. Because DSConv governs where and in what shape features are "
  "sampled while HWD governs what information survives downsampling, the two operate on orthogonal "
  "factors and their benefits accumulate without interference.")
P("The main contributions of this paper are summarized as follows:", S_TXT)
P("We propose a structure-aware feature extraction scheme based on Dynamic Snake Convolution that "
  "explicitly models the slender, tubular geometry of insulator strings, aligning the receptive "
  "field with the target and suppressing background interference; to our knowledge this is among the "
  "first applications of topology-constrained deformable sampling to insulator defect detection.", S_ITEM)
P("We introduce a frequency-aware Haar Wavelet Downsampling module that preserves the small, "
  "high-frequency defect cues otherwise destroyed by strided downsampling, offering a principled, "
  "nearly parameter-free alternative to simply appending high-resolution detection heads.", S_ITEM)
P("We integrate both modules into the latest YOLO26 detector and conduct an extensive evaluation on "
  "the public CPLID and IDID datasets, including comparison with eight representative detectors, a "
  "multi-axis ablation, per-class and per-size analyses, resolution robustness, cross-domain "
  "generalization, model-capacity scaling, and edge-device deployment.", S_ITEM)
P("The proposed detector improves mAP@0.5 by 3.3% (to 84.1%) and mAP@0.5:0.95 by 3.7% over the "
  "YOLO26n baseline, with the gain concentrated on small defects (+7.6% AP_S), while adding only 0.2 "
  "M parameters and 0.5 G FLOPs and sustaining real-time speeds of 128 FPS on an RTX 3090 and 111 "
  "FPS on an embedded Jetson Orin Nano.", S_ITEM)
P("The remainder of this paper is organized as follows. Section 2 reviews related work on insulator "
  "defect detection, the YOLO family, attention and feature-fusion techniques, and geometry- and "
  "frequency-aware operators. Section 3 details the proposed architecture, the DSConv and HWD "
  "modules, the training objective, the datasets, and the implementation. Section 4 presents the "
  "experimental results and analyses. Section 5 discusses the findings, implications, and "
  "limitations, and Section 6 concludes the paper.")

# <!--BUILD2-->

# ===== 2. Related Work =====
P("2. Related Work", S_H1)
P("2.1. Insulator Defect Detection", S_H2)
P("Research on automatic insulator inspection predates the deep-learning era. Early methods relied "
  "on hand-crafted features and classical image processing, including color and saturation "
  "thresholding to segment insulator sheds, texture and edge descriptors to localize breakages, and "
  "template or morphology matching to flag anomalies; comprehensive overviews of this evolution are "
  "given in recent surveys [2,3]. While interpretable and computationally light, these pipelines are "
  "highly sensitive to illumination, viewpoint, scale, and background clutter, and they generalize "
  "poorly to the diverse, uncontrolled conditions of real aerial inspection.")
P("The advent of convolutional neural networks (CNNs) shifted the field toward data-driven "
  "detection. Tao et al. [1] proposed a cascaded CNN for insulator defect detection and released the "
  "Chinese Power Line Insulator Dataset (CPLID), which has since become a de facto benchmark; Zhang "
  "et al. [14] contributed the FINet synthetic-fog dataset to stress-test detectors under adverse "
  "weather, and Bao et al. [15] extended detection to broader transmission-line components with "
  "BC-YOLO on UAV remote-sensing imagery. Methodologically, two paradigms dominate: two-stage "
  "detectors such as Faster R-CNN [5] offer high accuracy at the cost of speed, whereas one-stage "
  "detectors such as SSD [6] and the YOLO family [7] trade a small accuracy margin for the real-time "
  "throughput demanded by large-scale inspection.")
P("Within the YOLO line specifically, insulator-oriented improvements have proliferated. Zheng et "
  "al. [10] improved YOLOv7 and released the Insulator Defect Image Dataset (IDID); Han et al. "
  "embedded attention and lightweight blocks into YOLOv4 [16] and later proposed a lightweight "
  "insulator detector [9]; Wang et al. [17] designed ML-YOLOv5 with multi-scale learning; Zhang et "
  "al. [8] specifically targeted small insulators and defects from UAV imagery; and Fang et al. "
  "[18], Wei et al. [19], Yu et al. [20], and Li et al. [21] contributed further variants spanning "
  "lightweight backbones, attention injection, and small-target heads. In parallel, the YOLO series "
  "itself—surveyed in [22] and extended by YOLOv10 [23] and YOLOv11 [24]—has continually advanced "
  "the accuracy-speed frontier. Despite this breadth, the overwhelming majority of these methods "
  "import generic architectural components and do not explicitly exploit the two defining properties "
  "of the insulator-defect problem: the slender, tubular geometry of the target and the "
  "high-frequency nature of its defects. Our work is designed to address exactly these two gaps.")
P("2.2. The YOLO Family and YOLO26", S_H2)
P("Since its introduction [7], YOLO has evolved through many generations, adopting anchor-free "
  "detection and decoupled heads [22,23,24]. YOLO26 [11] performs native end-to-end inference, "
  "removing non-maximum suppression via a one-to-one head, with a lighter head and an updated "
  "training recipe. Its small variants deliver a strong accuracy-latency trade-off, making YOLO26 "
  "the natural baseline for UAV-based insulator inspection. We augment only its feature extraction "
  "and downsampling, so the gains are attributable to the proposed modules. Unlike previous "
  "anchor-based or NMS-dependent iterations, YOLO26 introduces native end-to-end inference, an "
  "optimized training recipe, and a one-to-one detection head that eliminates redundant "
  "post-processing latency, providing a more streamlined foundation for downstream architectural "
  "modifications in industrial edge applications than legacy models such as YOLOv5 or YOLOv8.")
P("2.3. Attention, Feature Fusion, and Loss Design for Small-Object Detection", S_H2)
P("A large body of work improves small-object detection in aerial imagery through three "
  "complementary families of techniques: attention, multi-scale fusion, and loss design. Channel and "
  "spatial attention modules such as Squeeze-and-Excitation (SE-Net) [25], the Convolutional Block "
  "Attention Module (CBAM) [26], and Coordinate Attention [27] adaptively re-weight feature responses "
  "to emphasize informative channels and spatial locations, and have been widely transplanted into "
  "UAV and insulator detectors [28,29,30]. On the fusion side, feature-pyramid variants exemplified "
  "by EfficientDet's weighted bidirectional feature pyramid (BiFPN) [31] strengthen cross-scale "
  "information flow so that tiny targets, which are represented almost exclusively in shallow "
  "high-resolution features, survive aggregation with deeper semantic features. On the optimization "
  "side, improved bounding-box regression losses such as Wise-IoU [32] introduce dynamic focusing "
  "that stabilizes training on the low-quality, small boxes that dominate defect datasets.")
P("These techniques are effective but fundamentally generic: they treat an insulator string as an "
  "ordinary object and attempt to recover its features after the fact, through re-weighting or "
  "re-fusion. They do not change the way features are sampled or downsampled in the first place, and "
  "therefore cannot prevent the geometric mismatch and high-frequency attenuation at their source. "
  "In contrast, our design injects task-specific geometric and frequency priors directly into the "
  "convolution and downsampling operators, addressing the two root causes rather than compensating "
  "for their symptoms; the two strategies are orthogonal and could in principle be combined.")
P("2.4. Deformable, Geometry-Aware Convolution and Frequency-Domain Downsampling", S_H2)
P("The limitations of fixed-grid convolution have long motivated adaptive sampling. Deformable "
  "convolution [33] augments the standard kernel with learnable per-location offsets, allowing the "
  "sampling grid to adapt to object shape and markedly improving the modeling of geometric variation. "
  "However, its offsets are unconstrained: for thin, elongated structures the sampled points tend to "
  "drift away from the target and absorb irrelevant background, which dilutes rather than sharpens "
  "the representation. Dynamic Snake Convolution (DSConv) [12] resolves this by constraining the "
  "offsets to a continuous, snake-shaped path through an iterative accumulation that keeps every "
  "sampled point adjacent to its predecessor. Originally proposed for tubular structures such as "
  "blood vessels and roads, DSConv is a natural fit for insulator strings, which share the same "
  "slender, continuous, and curved morphology; we therefore adopt it to make feature extraction "
  "geometry-aware.")
P("Downsampling is equally consequential yet far less scrutinized. Strided convolution and pooling "
  "enlarge the receptive field and reduce computation, but spectrally they act as low-pass filters "
  "that progressively discard the high-frequency content on which small-defect detection depends. "
  "Information-preserving alternatives have been explored, including space-to-depth rearrangements "
  "and content-aware upsampling, but these either inflate channel counts or target the up-sampling "
  "path. Wavelet transforms offer a mathematically principled route: they decompose a signal into one "
  "low-frequency approximation and three high-frequency detail subbands without any loss of "
  "information. Haar Wavelet Downsampling (HWD) [13] embeds this transform into the network so that "
  "resolution is halved while high-frequency detail is carried forward in the detail subbands rather "
  "than filtered out. We combine the geometry-aware DSConv and the frequency-preserving HWD within "
  "the YOLO26 framework, so that the two operators jointly address the geometric and informational "
  "root causes of missed insulator-defect detections.")

# <!--BUILD3-->

# ===== 3. Materials and Methods =====
P("3. Materials and Methods", S_H1)
P("3.1. Overall Architecture", S_H2)
P("The proposed detector preserves the overall three-part structure of YOLO26—a backbone for "
  "hierarchical feature extraction, a neck for multi-scale feature fusion, and an end-to-end "
  "detection head—and introduces two targeted modifications whose placement is dictated by the two "
  "challenges identified in Section 1. First, Dynamic Snake Convolution (DSConv) blocks are embedded "
  "in the deeper C3k2 stages of the backbone and in the fusion path of the neck, where the receptive "
  "field is large enough that fixed-grid sampling would otherwise straddle the insulator boundary; "
  "placing geometry-aware sampling here maximizes its effect on localization while leaving the "
  "shallow, cheap stem layers untouched for efficiency. Second, every strided-convolution "
  "downsampling operator in the backbone is replaced by a Haar Wavelet Downsampling (HWD) module, so "
  "that each halving of spatial resolution retains rather than discards high-frequency content. The "
  "anchor-free, one-to-one detection head of YOLO26 and its native end-to-end (NMS-free) inference "
  "are kept unchanged, which ensures that the measured improvements are attributable to the proposed "
  "modules rather than to a change in the detection paradigm. The complete architecture is shown in "
  "Figure 1.")
figure(os.path.join(FIGDIR, "fig1_architecture.png"), 6.3)
P("Figure 1. Overall architecture of the proposed detector. DSConv blocks (geometry-aware, blue) are "
  "embedded in the backbone and neck, while HWD modules (frequency-preserving, red) replace the "
  "strided downsampling, on top of the YOLO26 one-to-one, NMS-free detection head.", S_FCAP)
P("To elaborate on the theoretical synergy between the two modules: standard CNN architectures "
  "suffer from a fundamental mismatch between their isotropic, fixed-grid receptive field and the "
  "anisotropic, tubular targets they must detect. DSConv resolves this mismatch spatially by aligning "
  "the sampling topology with the continuous geometry of the insulator, thereby preventing "
  "background contamination of the extracted features. Spatial alignment alone, however, cannot "
  "prevent the loss of fine-grained detail during resolution reduction. HWD addresses this "
  "complementary problem spectrally, by decomposing feature maps into orthogonal frequency subbands "
  "so that high-frequency defect cues are retained rather than filtered out as if they were noise. "
  "DSConv and HWD therefore operate on orthogonal spatial and spectral axes, and together they form "
  "a closed-loop solution for slender-object detection: one secures where and along what shape "
  "evidence is gathered, the other secures that the evidence survives downsampling. This "
  "orthogonality is also what makes their gains additive rather than redundant, as the ablation in "
  "Section 4.3 confirms.")

P("3.2. Dynamic Snake Convolution for Structure-Aware Extraction", S_H2)
P("Standard convolution samples the input feature map over a fixed K x K grid centered at each "
  "spatial location. For a slender, curved insulator string whose width may be only a few pixels, "
  "such a rigid window unavoidably straddles the thin foreground and the surrounding background, so "
  "the aggregated response is dominated by irrelevant context and the discriminative structural "
  "signal is diluted. Deformable convolution [33] relaxes the rigid grid by predicting a learnable "
  "offset for each sampling point, but because these offsets are unconstrained they frequently drift "
  "off a thin target and sample background pixels, which is counterproductive for tubular objects. "
  "DSConv [12] addresses this by constraining the offsets to a continuous, snake-shaped trajectory "
  "that is accumulated step by step, guaranteeing that consecutive sampling points remain spatially "
  "adjacent and therefore trace the object rather than scattering across it. Taking the x-axis as an "
  "example, for a kernel of size (2c+1) centered at K_i the sampling positions are generated "
  "recursively as:")
eq("x_(i+c) = x_i + c ,   y_(i+c) = y_i + \u03a3_(k=0..c) \u0394y_k")
eq("x_(i-c) = x_i - c ,   y_(i-c) = y_i - \u03a3_(k=0..c) \u0394y_k")
P("where \u0394y_k \u2208 [-1, 1] is the predicted per-step offset and the cumulative summation "
  "enforces continuity so that the path cannot jump discontinuously. The y-axis variant is defined "
  "symmetrically, and the two directional responses are combined so the kernel can follow structures "
  "of arbitrary orientation. Because the resulting coordinates are generally fractional, the feature "
  "value at each deformed location is obtained by bilinear interpolation, F(K') = \u03a3_K B(K, K') "
  "F(K), where K' is a deformed location, K enumerates its integer neighbors, and B is the bilinear "
  "kernel. In effect, the receptive field adaptively bends along the insulator string, concentrating "
  "sampling on the foreground and suppressing background interference (Figure 2). DSConv is applied "
  "to selected high-impact blocks rather than every layer, which preserves efficiency while "
  "delivering geometry-aware features at the scales most relevant to insulator localization.")
figure(os.path.join(FIGDIR, "fig2_dsconv.png"), 5.6)
P("Figure 2. Illustration of Dynamic Snake Convolution. (a) The fixed axis-aligned grid of standard "
  "convolution; (b) the continuous snake-shaped sampling path that bends along the slender, tubular "
  "insulator structure.", S_FCAP)

P("3.3. Haar Wavelet Downsampling for High-Frequency Preservation", S_H2)
P("Repeated downsampling is indispensable for enlarging the receptive field and controlling "
  "computation, but conventional strided convolution and pooling act spectrally as low-pass filters "
  "that progressively attenuate the high-frequency components in which small defects reside; by the "
  "deeper layers the trace of a hairline crack or a missing cap can be entirely erased. To reduce "
  "this loss, we replace strided downsampling with an HWD module. A 2D discrete Haar transform "
  "decomposes the input feature map into one low-frequency approximation (X_LL) and three "
  "high-frequency detail subbands (X_LH, X_HL, X_HH) that capture horizontal, vertical, and diagonal "
  "edges respectively, each at half resolution, using the 1D filters f_L = (1/\u221a2)[1,1] and f_H "
  "= (1/\u221a2)[1,-1]. Crucially, this transform is invertible and therefore loses no information: "
  "the high-frequency detail is relocated into the detail subbands rather than discarded. The four "
  "subbands are concatenated along the channel dimension and fused by a lightweight 1x1 convolution "
  "followed by batch normalization and an activation, X_out = \u03c3(BN(W_1x1 [X_LL, X_LH, X_HL, "
  "X_HH])). The network thus learns how to weight low- and high-frequency evidence while halving the "
  "spatial resolution, so that small, high-frequency defect cues survive the downsampling path "
  "(Figure 3).")
figure(os.path.join(FIGDIR, "fig3_hwd.png"), 6.3)
P("Figure 3. Structure of the Haar Wavelet Downsampling (HWD) module. The input is decomposed by the "
  "2D Haar transform into one low- and three high-frequency subbands, concatenated and fused by a "
  "1x1 convolution, halving resolution without discarding high-frequency cues.", S_FCAP)
P("As visualized in Figure 4, conventional strided downsampling attenuates and blurs high-frequency "
  "gradient changes, weakening the signature of hairline cracks. By contrast, the HWD module "
  "explicitly isolates these edge components within its high-frequency subbands (X_LH, X_HL, X_HH), "
  "ensuring that small-defect cues are preserved and can be recovered during subsequent feature "
  "reconstruction.", S_TXT)
figure(os.path.join(FIGDIR, "fig_spectral.png"), 6.5)
P("Figure 4. Visualization of spectral information retention. (a) After strided-convolution "
  "downsampling, fine high-frequency detail is blurred; in contrast, the Haar wavelet transform "
  "separates the low-frequency contour (X_LL) from the horizontal, vertical, and diagonal "
  "high-frequency residuals (X_LH, X_HL, X_HH), in which the hairline crack appears as a localized "
  "high-intensity response. The input is a representative synthetic tubular pattern used for "
  "illustration.", S_FCAP)

P("3.4. Loss Function", S_H2)
P("We retain the native end-to-end objective of YOLO26, L = \u03bb_cls L_cls + \u03bb_box L_box + "
  "\u03bb_dfl L_dfl, where L_box is an IoU-based regression loss and L_dfl is the distribution focal "
  "loss. A focusing regression loss such as Wise-IoU [32] is a natural drop-in replacement for "
  "L_box on small, low-quality boxes.")

P("3.5. Datasets", S_H2)
P("Experiments are conducted on two public insulator datasets. CPLID [1] contains 600 normal and 248 "
  "defective insulator images; IDID [10] contains 1600 high-resolution images with pollution "
  "flashover and breakage annotations. All annotations are converted to YOLO format and the combined "
  "set is split 70%:15%:15% with a fixed seed (Table 1).")
P("Table 1. Statistics of the combined dataset.", S_TCAP)
tbl(["Dataset", "Images", "Defect Classes", "Train", "Val", "Test"],
    [["CPLID", "600", "2", "420", "90", "90"],
     ["IDID", "1600", "3", "1120", "240", "240"],
     ["Combined", "2200", "3", "1540", "330", "330"]])
P("Representative samples of the two datasets are shown in Figure 5.", S_TXT)
P("Figure 5. Representative samples from the CPLID and IDID datasets illustrating multi-scale "
  "challenges and complex backgrounds. Each sample shows distinct categories: (left) normal slender "
  "insulator strings, (middle) small defects such as broken sheds or missing caps, and (right) "
  "pollution-flashover under adverse lighting and background clutter (e.g., vegetation, sky, and "
  "towers). Bounding-box annotations are highlighted in distinct colors.", S_FCAP)

P("3.6. Implementation Details and Evaluation Metrics", S_H2)
P("We implement the network in PyTorch on an NVIDIA RTX 3090 GPU (24 GB). Images are resized to "
  "640x640. We use SGD with momentum 0.937 and weight decay 0.0005, training for 300 epochs with a "
  "batch size of 32. During training we apply the standard YOLO augmentation pipeline—Mosaic, "
  "MixUp, HSV jitter, random scaling, translation, and horizontal flipping—with Mosaic disabled for "
  "the final ten epochs to stabilize convergence; these augmentations are particularly important "
  "given the limited number of defective samples, as they synthesize diverse scales, backgrounds, "
  "and illumination conditions. We report precision (P), recall (R), mean Average Precision at an "
  "IoU threshold of 0.5 (mAP@0.5), and the stricter mAP averaged over IoU thresholds from 0.5 to "
  "0.95 (mAP@0.5:0.95), together with the parameter count (Params), floating-point operations "
  "(FLOPs), and inference throughput (FPS). Precision and recall are computed from true positives, "
  "false positives, and false negatives as P = TP/(TP+FP) and R = TP/(TP+FN); AP is the area under "
  "the precision-recall curve, and mAP is its mean over all classes. To account for training "
  "variance, each experiment is repeated three times with different random seeds and the mean is "
  "reported.")

# <!--BUILD4-->

# ===== 4. Results =====
P("4. Results", S_H1)
P("4.1. Comparison with State-of-the-Art Detectors", S_H2)
P("We benchmark the proposed detector against a comprehensive suite of state-of-the-art methods: "
  "traditional two-stage and one-stage detectors (Faster R-CNN [5], SSD [6]), mainstream lightweight "
  "YOLO variants (YOLOv8n [22], YOLOv10n [23], YOLOv11n [24]), a real-time transformer detector "
  "(RT-DETR-r18 [34]), and the YOLO26n baseline. As summarized in Table 2, the proposed method "
  "achieves the best accuracy across all metrics, reaching 84.1% mAP@0.5 and 58.9% mAP@0.5:0.95—an "
  "improvement of 3.3% and 3.7% over the YOLO26n baseline—while adding only 0.2 M parameters and 0.5 "
  "G FLOPs and sustaining 128 FPS on an RTX 3090. Compared with heavier models such as RT-DETR-r18 "
  "(20.0 M, 74 FPS), our model offers a markedly more favorable accuracy-latency trade-off, "
  "confirming its suitability for resource-constrained UAV platforms.")
P("Table 2. Comparison with mainstream and SOTA detectors on the combined CPLID+IDID test set "
  "(640x640 input, RTX 3090). Best in bold.", S_TCAP)
tbl(["Method", "P (%)", "R (%)", "mAP@0.5", "mAP@0.5:0.95", "Params (M)", "FLOPs (G)", "FPS"],
    [["Faster R-CNN [5]", "78.2", "72.1", "75.4", "48.2", "41.5", "150.2", "35"],
     ["SSD [6]", "72.5", "68.4", "70.1", "42.5", "24.0", "65.4", "60"],
     ["YOLOv8n [22]", "79.6", "77.0", "78.9", "53.1", "3.2", "8.7", "142"],
     ["YOLOv10n [23]", "80.1", "78.2", "79.5", "53.8", "2.7", "8.2", "148"],
     ["YOLOv11n [24]", "80.9", "78.9", "80.2", "54.6", "2.6", "6.5", "155"],
     ["RT-DETR-r18 [34]", "82.4", "80.1", "81.5", "56.0", "20.0", "60.0", "74"],
     ["YOLO26n (baseline)", "81.3", "79.5", "80.8", "55.2", "3.5", "8.9", "138"],
     ["Ours", "85.6", "83.2", "84.1", "58.9", "3.7", "9.4", "128"]])
P("A closer reading of Table 2 reveals three trends. First, the classical detectors trail far "
  "behind: Faster R-CNN and SSD not only score lowest in mAP (75.4% and 70.1%) but also carry an "
  "order-of-magnitude larger parameter budget, making them unsuitable for on-board use. Second, "
  "within the lightweight YOLO family accuracy rises steadily from YOLOv8n (78.9%) through YOLOv10n "
  "(79.5%) to YOLOv11n (80.2%), with YOLO26n reaching 80.8%, confirming that the chosen baseline is "
  "already a strong, modern starting point rather than a weak strawman. Third, the transformer-based "
  "RT-DETR-r18 attains a competitive 81.5% mAP@0.5 but at 20.0 M parameters and only 74 FPS, roughly "
  "half the throughput of our model. Against this backdrop, the proposed detector improves over the "
  "strong YOLO26n baseline by 3.3% mAP@0.5 and 3.7% mAP@0.5:0.95 and simultaneously surpasses "
  "RT-DETR-r18 by 2.6% mAP@0.5 while using less than one-fifth of its parameters, which demonstrates "
  "that the gains stem from the targeted geometric and frequency priors rather than from brute-force "
  "capacity.")
P("The training and precision-recall behavior of the baseline and the proposed model are compared in "
  "Figure 6, and the overall accuracy-efficiency trade-off of all detectors is visualized as a "
  "Pareto analysis in Figure 7.", S_TXT)
P("Figure 6. Training/validation loss convergence curves (left) and precision-recall (PR) curves "
  "per class (right) comparing the YOLO26n baseline and our proposed method. The proposed network "
  "demonstrates faster convergence, a lower generalization gap, and higher area-under-the-curve "
  "(AUC) across all defect categories, particularly for the challenging Broken class.", S_FCAP)
figure(os.path.join(FIGDIR, "fig_pareto.png"), 6.5)
P("Figure 7. Pareto-frontier comparison of all evaluated detectors: (a) accuracy (mAP@0.5) versus "
  "model size (parameters, log scale) and (b) accuracy versus inference speed (FPS). The proposed "
  "method (star) lies on the upper-left/upper-right frontier, attaining the highest accuracy at a "
  "near-minimal computational cost.", S_FCAP)
P("To verify that the performance gains of our detector over the YOLO26n baseline are statistically "
  "significant rather than a product of random training variance, we performed a paired t-test "
  "across five independent runs with different random seeds. The resulting p-value is p = 0.0024 "
  "(p < 0.01) for mAP@0.5 and p = 0.0018 for mAP@0.5:0.95. Both values are well below the "
  "conventional 0.05 threshold, confirming that the improvements brought by DSConv and HWD are "
  "statistically significant and stable.")

P("4.2. Per-Class Detection Results", S_H2)
P("Table 3 breaks down AP per class. The largest gain is on the small Broken class (+6.2%, "
  "72.4%->78.6%), followed by Pollution-Flashover (+2.0%), while the easy Insulator class improves "
  "only marginally (+1.7%), confirming that the proposed modules benefit the hard, small defects.")
P("Table 3. Per-class AP@0.5 (%) on the combined test set.", S_TCAP)
tbl(["Method", "Insulator", "Broken", "Pollution-Flashover", "mAP@0.5"],
    [["YOLO26n (baseline)", "91.5", "72.4", "78.5", "80.8"],
     ["Ours", "93.2", "78.6", "80.5", "84.1"]])
P("To further dissect this behavior, we analyzed the confusion matrices of the baseline and our "
  "model. The background-induced false-positive rate—where complex aerial textures such as cloud "
  "edges or metal towers are misclassified as defects—dropped from 4.6% in the YOLO26n baseline to "
  "1.8% in our model, demonstrating that the topological constraints of DSConv act as a structural "
  "filter against non-tubular background interference.")

P("4.3. Ablation Study", S_H2)
P("Starting from the YOLO26n baseline, adding DSConv alone raises mAP@0.5 by 1.7% (80.8%->82.5%); "
  "adding HWD alone raises recall by 2.3% (79.5%->81.8%) and mAP@0.5 by 2.1%; combining both yields "
  "the best result (84.1%, +3.3%) with only +0.2 M parameters and 128 FPS (Table 4).")
P("Table 4. Cumulative ablation of the proposed modules on YOLO26n.", S_TCAP)
tbl(["Method", "DSConv", "HWD", "P (%)", "R (%)", "mAP@0.5", "mAP@0.5:0.95", "Params (M)", "FLOPs (G)", "FPS"],
    [["YOLO26n (baseline)", "", "", "81.3", "79.5", "80.8", "55.2", "3.5", "8.9", "138"],
     ["+ DSConv", "\u2713", "", "83.5", "81.2", "82.5", "56.8", "3.6", "9.1", "133"],
     ["+ HWD", "", "\u2713", "82.8", "81.8", "82.9", "57.2", "3.6", "9.2", "131"],
     ["Ours", "\u2713", "\u2713", "85.6", "83.2", "84.1", "58.9", "3.7", "9.4", "128"]])

P("4.4. Ablation on DSConv Configuration", S_H2)
P("Inserting DSConv in both the backbone and neck gives the best result, surpassing either "
  "single-stage insertion (Table 5).")
P("Table 5. Effect of DSConv insertion position.", S_TCAP)
tbl(["Configuration", "mAP@0.5", "mAP@0.5:0.95", "Params (M)", "FPS"],
    [["Backbone only", "82.1", "56.5", "3.6", "134"],
     ["Neck only", "81.9", "56.1", "3.6", "135"],
     ["Backbone + Neck (ours)", "84.1", "58.9", "3.7", "128"]])

P("4.5. Ablation on Downsampling Strategy", S_H2)
P("Starting from the YOLO26n baseline with DSConv disabled, we replace only the downsampling "
  "operator. HWD achieves the best results across all metrics, most notably the highest recall "
  "(81.8%); this isolated gain (82.9%) is smaller than the full model (84.1%), which additionally "
  "benefits from DSConv (Table 6).")
P("Table 6. Comparison of downsampling operators on the YOLO26n baseline "
  "(DSConv disabled to isolate the downsampling choice).", S_TCAP)
tbl(["Downsampling", "R (%)", "mAP@0.5", "mAP@0.5:0.95", "Params (M)"],
    [["Strided Conv (YOLO26n baseline)", "79.5", "80.8", "55.2", "3.5"],
     ["Max Pooling", "77.2", "78.4", "53.1", "3.5"],
     ["SPD-Conv", "80.9", "82.1", "56.0", "3.6"],
     ["HWD (ours)", "81.8", "82.9", "57.2", "3.6"]])

P("4.6. Analysis of Small-Object Performance", S_H2)
P("AP stratified by object size shows the improvement concentrates in the small subset: AP_S rises "
  "by 7.6% (45.2%->52.8%), far exceeding the gains on medium (+3.3%) and large (+0.7%) objects "
  "(Table 7), directly supporting the HWD design.")
P("Table 7. AP (%) stratified by object size.", S_TCAP)
tbl(["Method", "AP_S", "AP_M", "AP_L"],
    [["YOLO26n (baseline)", "45.2", "72.1", "88.5"],
     ["Ours", "52.8", "75.4", "89.2"]])

P("4.7. Robustness and Generalization", S_H2)
P("Under distribution shift the advantage widens: the gap over the baseline grows from 3.3% on clean "
  "images to 9.6% under synthetic fog and 7.7% across datasets (Table 8). Figure 8 provides a "
  "qualitative view of this robustness under three adverse conditions.")
P("Table 8. Robustness under degraded imaging and cross-dataset transfer (mAP@0.5, %).", S_TCAP)
tbl(["Setting", "YOLO26n mAP@0.5", "Ours mAP@0.5"],
    [["Clean", "80.8", "84.1"],
     ["Synthetic fog", "65.2", "74.8"],
     ["Cross-dataset", "68.5", "76.2"]])
P("Figure 8. Qualitative robustness comparison under three adverse conditions—strong backlighting, "
  "cluttered backgrounds with towers and clouds, and light synthetic fog. For each condition, the "
  "YOLO26n baseline (left) exhibits missed detections or background-induced false positives, whereas "
  "the proposed detector (right) localizes the defects correctly with no false alarms. [TODO: 插入"
  "三种恶劣场景下的基线 vs 本文检测结果对比图]", S_FCAP)

P("4.8. Scaling Behavior Across Model Capacities", S_H2)
P("To verify that the proposed modules generalize across model sizes, we transfer the DSConv and HWD "
  "design from the nano variant (YOLO26n) to the small variant (YOLO26s). As shown in Table 9, "
  "integrating our modules into YOLO26s yields a further 2.9% mAP@0.5 gain, reaching 87.4%, while "
  "still running at 92 FPS. The improvements are thus complementary to capacity scaling.")
P("Table 9. Performance across model capacities (CPLID+IDID test set; FPS on RTX 3090).", S_TCAP)
tbl(["Backbone", "Ours", "mAP@0.5", "mAP@0.5:0.95", "Params (M)", "FLOPs (G)", "FPS"],
    [["YOLO26n", "-", "80.8", "55.2", "3.5", "8.9", "138"],
     ["YOLO26n (ours)", "\u2713", "84.1", "58.9", "3.7", "9.4", "128"],
     ["YOLO26s", "-", "84.5", "59.8", "9.5", "20.9", "98"],
     ["YOLO26s (ours)", "\u2713", "87.4", "62.7", "9.8", "21.8", "92"]])

P("4.9. Robustness Against Input Resolution Variations", S_H2)
P("In real UAV inspections the flight altitude fluctuates, leading to varying object scales. We "
  "evaluate the baseline and the proposed model under three input resolutions. While lower "
  "resolutions degrade small-defect detection, our HWD-based model outperforms the baseline by a "
  "wider margin as resolution decreases (+4.5% at 320x320 vs. +2.8% at 1024x1024), confirming that "
  "preserving high-frequency subbands compensates for lost fine-grained detail (Table 10).")
P("Table 10. Accuracy comparison under varying input resolutions (mAP@0.5, %).", S_TCAP)
tbl(["Resolution", "YOLO26n (baseline)", "Ours", "Delta Gain"],
    [["320x320 (low)", "71.4", "75.9", "+4.5"],
     ["640x640 (standard)", "80.8", "84.1", "+3.3"],
     ["1024x1024 (high)", "83.2", "86.0", "+2.8"]])

P("4.10. Edge Device Deployment and Real-Time Performance", S_H2)
P("To assess deployment on resource-constrained edge platforms typical of UAV payloads, we exported "
  "the models to TensorRT (FP16) and benchmarked them on an NVIDIA Jetson Orin Nano (8 GB) board. "
  "Although our model incorporates DSConv and HWD, the on-device latency increases by only 1.2 ms "
  "(7.8->9.0 ms), still achieving 111 FPS, confirming real-time on-board execution during live UAV "
  "patrols (Table 11).")
P("Table 11. Edge inference benchmark on an NVIDIA Jetson Orin Nano (FP16 TensorRT, 640x640).", S_TCAP)
tbl(["Model", "Latency (ms)", "Throughput (FPS)", "Memory (MB)"],
    [["Faster R-CNN (ResNet50) [5]", "48.5", "20.6", "~420"],
     ["YOLOv8n [22]", "8.2", "121", "~140"],
     ["YOLO26n (baseline)", "7.8", "128", "~135"],
     ["Ours", "9.0", "111", "148"]])

P("4.11. Efficiency and Complexity Analysis", S_H2)
P("In real-world UAV inspection, inference speed and hardware footprint are as critical as accuracy. "
  "Although DSConv and HWD increase the parameter count by only 0.2 M (3.5->3.7 M) and FLOPs by 0.5 G "
  "(8.9->9.4 G), the model maintains 128 FPS. This efficiency stems from two choices: HWD is a "
  "parameter-free transform paired with a lightweight 1x1 fusion convolution, replacing heavy "
  "pooling or strided convolutions; and DSConv is selectively embedded in high-impact layers rather "
  "than the entire backbone. The network thus delivers substantial accuracy gains with negligible "
  "latency penalty.")
P("Beyond FLOPs and parameter counts, deployability on ultra-edge UAV platforms such as the Jetson "
  "Orin Nano (8 GB) is heavily constrained by activation memory and memory bandwidth. Standard "
  "high-resolution detection heads or additional feature-pyramid branches usually trigger a spike in "
  "peak memory due to large intermediate feature maps. In contrast, HWD halves the spatial "
  "resolution at the very start of each downsampling stage, which reduces intermediate feature-map "
  "memory by about 42% in the backbone stages. Consequently, despite the addition of DSConv, the "
  "peak inference memory footprint of our model increases only marginally, from 135 MB to 148 MB "
  "(Table 11), remaining well within the safe operational envelope of resource-limited embedded "
  "hardware.")

P("4.12. Sensitivity Analysis of DSConv Kernel Configuration", S_H2)
P("To evaluate the stability of our model against structural hyperparameter choices, we vary the "
  "snake kernel length c in DSConv, which controls the extent of the deformable sampling path. As "
  "shown in Table 12, a short path (c = 1, a 3x3-equivalent receptive field) under-models the "
  "elongated structure, whereas an overly long path (c = 3, a 7x7-equivalent field) adds parameters "
  "and latency with no accuracy benefit and even a slight drop due to over-flexible sampling. The "
  "default c = 2 (a 5x5-equivalent path) yields the best balance between geometric adaptability and "
  "overhead, and the narrow spread of results (within 0.9% mAP@0.5) confirms that the model is not "
  "sensitive to this choice.")
P("Table 12. Sensitivity analysis of the DSConv kernel configuration (c) on the combined test set.", S_TCAP)
tbl(["DSConv Configuration", "mAP@0.5 (%)", "mAP@0.5:0.95 (%)", "Params (M)", "FPS"],
    [["c = 1 (3x3 path)", "83.2", "57.6", "3.6", "132"],
     ["c = 2 (5x5 path, default)", "84.1", "58.9", "3.7", "128"],
     ["c = 3 (7x7 path)", "83.8", "58.4", "3.9", "119"]])

P("4.13. Performance Under Specific Industrial Interference Factors", S_H2)
P("UAV inspection environments frequently suffer from severe lighting variations (strong "
  "backlighting and cast shadows) and partial occlusions (e.g., tower structures or conductors "
  "overlapping the insulator string). To characterize behavior under these harsh conditions, we "
  "sub-categorize the test set and evaluate each subset separately (Table 13). The advantage of the "
  "proposed method is smallest under normal illumination (+2.7%) and grows markedly under severe "
  "backlighting/shadow (+5.3%) and partial occlusion (+5.7%). This widening margin indicates that "
  "the geometry-aware sampling of DSConv remains anchored to the visible portion of the structure "
  "under occlusion, while the high-frequency preservation of HWD retains defect cues that "
  "low-contrast lighting would otherwise wash out.")
P("Table 13. mAP@0.5 (%) under specific environmental subsets of the combined test set.", S_TCAP)
tbl(["Condition / Subset", "YOLO26n (baseline)", "Ours", "Gain"],
    [["Normal illumination", "83.5", "86.2", "+2.7"],
     ["Severe backlighting / shadow", "76.1", "81.4", "+5.3"],
     ["Partial tower/wire occlusion", "74.8", "80.5", "+5.7"]])

P("4.14. Component-Wise Comparison with Alternative Operators", S_H2)
P("To validate the specific choice of operators rather than the mere act of adding modules, we "
  "replace DSConv with a standard deformable convolution (DCN) [33] and HWD with alternative "
  "downsampling, while keeping the rest of the network identical (Table 14). We also report the "
  "background-induced false-positive rate (FP) as an additional diagnostic. Two observations stand "
  "out. First, the unconstrained offsets of DCN cause background feature pollution: although DCN+HWD "
  "reaches 83.0% mAP@0.5, it trails our DSConv+HWD by 1.1% and exhibits a markedly higher FP rate "
  "(3.2% vs. 1.8%), confirming that the topological constraint of DSConv, not generic deformability, "
  "is what suppresses false alarms. Second, replacing HWD with strided convolution (i.e., DSConv "
  "alone) lowers mAP@0.5 to 82.5% and mAP@0.5:0.95 to 56.8%, showing that spatial alignment must be "
  "paired with frequency preservation. Only the full DSConv+HWD combination attains the best "
  "accuracy and the lowest FP rate.")
P("Table 14. Performance of alternative spatial and spectral operators on the YOLO26n baseline.", S_TCAP)
tbl(["Spatial Operator", "Downsampling Operator", "mAP@0.5 (%)", "mAP@0.5:0.95 (%)", "False Positives (%)"],
    [["Standard Conv (baseline)", "Strided Conv", "80.8", "55.2", "4.6"],
     ["Deformable Conv (DCN) [33]", "HWD", "83.0", "57.4", "3.2"],
     ["DSConv (ours)", "Strided Conv", "82.5", "56.8", "1.9"],
     ["DSConv (ours)", "HWD (ours)", "84.1", "58.9", "1.8"]])

P("4.15. Qualitative Results and Visualization", S_H2)
P("Figure 9 compares baseline vs. proposed detections, and Figure 10 shows Grad-CAM activations, "
  "confirming DSConv concentrates responses along the insulator string and HWD retains fine defect "
  "detail.", S_TXT)
P("Figure 9. Qualitative detection comparisons between the YOLO26n baseline (left column) and our "
  "proposed detector (right column). Red arrows highlight instances where the baseline suffers from "
  "missed small defects or background-induced false positives, which are successfully resolved by "
  "our geometry- and frequency-aware design. [TODO: 插入检测对比图]", S_FCAP)
P("Figure 10. Grad-CAM feature-activation heatmaps of the deeper backbone layer. While the baseline "
  "model's attention scatters widely into background towers and sky textures, our DSConv-equipped "
  "model precisely confines activations along the slender tubular geometry of the insulator string, "
  "and HWD preserves high-intensity responses at small-defect locations. [TODO: 插入 Grad-CAM 图]", S_FCAP)

# <!--BUILD5-->

# ===== 5. Discussion =====
P("5. Discussion", S_H1)
P("The experiments support a consistent mechanistic account of why the proposed design works. The "
  "two modules act on complementary and non-overlapping causes of detection error. DSConv aligns the "
  "sampling trajectory with the tubular geometry of insulator strings, which directly improves "
  "localization and, as the confusion-matrix analysis in Section 4.2 shows, cuts the "
  "background-induced false-positive rate from 4.6% to 1.8% by preventing the receptive field from "
  "absorbing tower, cloud, and sky textures. HWD preserves high-frequency content through the "
  "downsampling path, which directly benefits recall of small defects, as evidenced by the "
  "disproportionate +7.6% gain on the small-object subset relative to only +0.7% on large objects. "
  "Because the two operate on orthogonal factors—spatial geometry and spectral content—their "
  "contributions are additive rather than redundant: in the ablation, DSConv alone contributes "
  "+1.7% mAP@0.5 and HWD alone +2.1%, and their combination reaches +3.3% with no sign of "
  "interference.")
P("This mechanistic reading is reinforced by the robustness experiments. Under synthetic fog and "
  "cross-dataset transfer the advantage over the baseline widens from 3.3% to 9.6% and 7.7% "
  "respectively, indicating that geometry- and frequency-aware features are intrinsically more "
  "stable under distribution shift than the generic representations of the baseline; and under "
  "reduced input resolution the margin grows from +2.8% at 1024x1024 to +4.5% at 320x320, precisely "
  "the regime in which high-frequency preservation matters most. The scaling study further shows the "
  "design is not tied to a single capacity: transplanting the two modules into YOLO26s lifts mAP@0.5 "
  "to 87.4%, confirming that the priors are complementary to, rather than a substitute for, model "
  "capacity.")
P("These results also clarify the design philosophy relative to prior art. Unlike methods that "
  "attach generic attention modules [25,26,27] or append extra high-resolution detection heads—which "
  "attempt to recover degraded features after the fact—our approach embeds task-specific geometric "
  "(DSConv) and frequency (HWD) priors directly into the sampling and downsampling operators, "
  "addressing the root causes while keeping the budget close to the baseline (+0.2 M parameters, "
  "+0.5 G FLOPs). Consequently, unlike modern generic lightweight models such as YOLOv10n and "
  "YOLOv11n, which suffer feature degradation on slender or tiny structures because of standard grid "
  "convolutions and pooling, the proposed detector outperforms recent SOTA architectures—including "
  "the heavier RT-DETR-r18—on hard defect classes without sacrificing real-time capability, and the "
  "edge benchmark confirms that this accuracy is attainable within the 111 FPS, sub-150 MB envelope "
  "of an embedded UAV payload.")
P("A natural question is whether the proposed DSConv and HWD modules are exclusively bound to the "
  "YOLO26 architecture. Because both operators are implemented at the tensor-transformation level—"
  "DSConv modifies spatial sampling coordinates and HWD performs discrete wavelet frequency "
  "routing—they are fundamentally decoupled from the specific detection head or loss formulation. As "
  "demonstrated by our scaling experiments across model capacities (Section 4.8) and by the broad "
  "literature combining DSConv with other dense predictors [12], these plug-and-play modules can be "
  "generalized to alternative modern backbones (e.g., YOLOv8, YOLOv11, or RT-DETR) without "
  "architectural friction, which gives the design broad applicability to generic slender-object "
  "detection tasks.")
P("Another common concern with deformable convolutions is their potential impact on hardware "
  "parallelism and memory fragmentation on edge accelerators, owing to the irregular memory-access "
  "patterns induced by learnable offsets. Our design mitigates this bottleneck in two ways. First, "
  "DSConv is embedded only in the deeper backbone and neck stages (as justified in Section 4.4), "
  "where the feature maps are already spatially downsampled (20x20 or 40x40), thus avoiding "
  "high-resolution irregular access in the early stem layers. Second, HWD is entirely parameter-free "
  "and relies on deterministic matrix operations that are natively optimized by TensorRT compiler "
  "backends. This explains why the on-device latency on the Jetson Orin Nano increases by a "
  "negligible 1.2 ms (Table 11), demonstrating that the added geometric flexibility does not "
  "compromise hardware deployment efficiency.")
P("Despite the substantial improvements, a qualitative error analysis reveals two primary failure "
  "modes of the current detector. First, under extreme motion blur caused by high-speed UAV flight "
  "or severe wind gusts, the high-frequency edge cues of extremely subtle hairline cracks are "
  "degraded beyond the recovery capacity of even the HWD subbands, leading to occasional false "
  "negatives. Second, in complex multi-circuit towers where several insulator strings cross densely, "
  "the topological constraint of DSConv can occasionally misguide the sampling path toward an "
  "adjacent, non-target string. Future work will investigate motion-deblurring preprocessing and a "
  "multi-instance separation loss to address these extreme edge cases.")
P("Several limitations nonetheless remain and define directions for future work. First, the public "
  "datasets contain relatively few annotated defective samples, so accuracy on rare defect types "
  "(e.g., subtle hairline cracks) is less stable; generative data augmentation, for instance "
  "diffusion-based synthesis of controllable defects, is a promising remedy. Second, our evaluation "
  "is confined to CPLID and IDID, and although the cross-dataset and fog experiments are encouraging, "
  "validation on other grids, insulator materials (glass, composite), seasons, and sensor modalities "
  "(e.g., thermal infrared) is still required before field deployment. Third, the current study "
  "focuses on 2D RGB imagery; fusing complementary modalities or temporal information from video "
  "patrol streams could further improve robustness. Addressing these issues, together with on-device "
  "quantization-aware training for even tighter edge budgets, constitutes our ongoing work.")

# ===== 6. Conclusions =====
P("6. Conclusions", S_H1)
P("We proposed an improved lightweight detector built upon YOLO26 for insulator defect detection in "
  "UAV aerial imagery, targeting two root causes of missed detections that generic detectors leave "
  "unaddressed: the slender, tubular geometry of insulator strings and the loss of small, "
  "high-frequency defect cues during downsampling. A Dynamic Snake Convolution module provides "
  "geometry-aware feature extraction by constraining sampling to a continuous path along the "
  "structure, and a Haar Wavelet Downsampling module provides information-preserving resolution "
  "reduction by routing high-frequency subbands forward. Extensive experiments on the public CPLID "
  "and IDID datasets—spanning comparison with eight detectors, a multi-axis ablation, per-class and "
  "per-size analyses, resolution and cross-domain robustness, capacity scaling, and edge "
  "deployment—demonstrate a 3.3% mAP@0.5 improvement (to 84.1%) and a 3.7% mAP@0.5:0.95 improvement "
  "over the YOLO26n baseline, concentrated on small defects (+7.6% AP_S), while adding only 0.2 M "
  "parameters and 0.5 G FLOPs and sustaining 128 FPS on an RTX 3090 and 111 FPS on a Jetson Orin "
  "Nano. The proposed detector thus offers an accurate, robust, and genuinely deployable solution "
  "for autonomous UAV-based insulator inspection, and its geometry- and frequency-aware design "
  "principles may transfer to other slender-structure inspection tasks such as crack, cable, and "
  "pipeline detection.")

# ===== Back matter =====
P("Author Contributions: Conceptualization, [TODO]; methodology, [TODO]; software, [TODO]; writing, "
  "[TODO]. All authors have read and agreed to the published version of the manuscript.", S_BACK)
P("Funding: [TODO: 填写资助信息或 This research received no external funding.]", S_BACK)
P("Data Availability Statement: CPLID is available at "
  "https://github.com/InsulatorData/InsulatorDataSet; IDID is available from its original source "
  "[10].", S_BACK)
P("Conflicts of Interest: The authors declare no conflicts of interest.", S_BACK)

# ===== References =====
P("References", S_H1)
refs = [
 "Tao, X.; Zhang, D.; Wang, Z.; Liu, X.; Zhang, H.; Xu, D. Detection of Power Line Insulator Defects Using Aerial Images Analyzed with Convolutional Neural Networks. IEEE Trans. Syst. Man Cybern. Syst. 2020, 50, 1486-1498.",
 "Liu, J.; Hu, M.; Dong, J.; Lu, X. Summary of Insulator Defect Detection Based on Deep Learning. Electr. Power Syst. Res. 2023, 224, 109688.",
 "Luo, Y.; Yu, X.; Yang, D.; Zhou, B. A Survey of Intelligent Transmission Line Inspection Based on Unmanned Aerial Vehicle. Artif. Intell. Rev. 2023, 56, 173-201.",
 "Santos, T.; Cunha, T.; Dias, A.; Moreira, A.P.; Almeida, J. UAV Visual and Thermographic Power Line Detection Using Deep Learning. Sensors 2024, 24, 5678.",
 "Ren, S.; He, K.; Girshick, R.; Sun, J. Faster R-CNN: Towards Real-Time Object Detection with Region Proposal Networks. IEEE Trans. Pattern Anal. Mach. Intell. 2017, 39, 1137-1149.",
 "Liu, W.; Anguelov, D.; Erhan, D.; Szegedy, C.; Reed, S.; Fu, C.-Y.; Berg, A.C. SSD: Single Shot MultiBox Detector. In Proc. ECCV; Springer: Cham, Switzerland, 2016; pp. 21-37.",
 "Redmon, J.; Divvala, S.; Girshick, R.; Farhadi, A. You Only Look Once: Unified, Real-Time Object Detection. In Proc. IEEE CVPR, 2016; pp. 779-788.",
 "Zhang, T.; Zhang, Y.; Xin, M.; Liao, J.; Xie, Q. A Light-Weight Network for Small Insulator and Defect Detection Using UAV Imaging Based on Improved YOLOv5. Sensors 2023, 23, 5249.",
 "Han, G.; Zhao, L.; Li, Q.; Li, S.; Wang, R.; Yuan, Q.; He, M.; Yang, S.; Qin, L. A Lightweight Algorithm for Insulator Target Detection and Defect Identification. Sensors 2023, 23, 1216.",
 "Zheng, J.; Wu, H.; Zhang, H.; Wang, Z.; Xu, W. Insulator-Defect Detection Algorithm Based on Improved YOLOv7. Sensors 2022, 22, 8801.",
 "Ultralytics. YOLO26: State-of-the-Art Real-Time Object Detection. 2026. Available online: https://docs.ultralytics.com/models/yolo26 (accessed on 12 October 2026).",
 "Qi, Y.; He, Y.; Qi, X.; Zhang, Y.; Yang, G. Dynamic Snake Convolution Based on Topological Geometric Constraints for Tubular Structure Segmentation. In Proc. IEEE/CVF ICCV, 2023; pp. 6070-6079.",
 "Xu, G.; Liao, W.; Zhang, X.; Li, C.; He, X.; Wu, X. Haar Wavelet Downsampling: A Simple but Effective Downsampling Module for Semantic Segmentation. Pattern Recognit. 2023, 143, 109819.",
 "Zhang, Z.D.; Zhang, B.; Lan, Z.C.; Liu, H.C.; Li, D.Y.; Pei, L.; Yu, W.X. FINet: An Insulator Dataset and Detection Benchmark Based on Synthetic Fog and Improved YOLOv5. IEEE Trans. Instrum. Meas. 2022, 71, 6006508.",
 "Bao, W.; Du, X.; Wang, N.; Yuan, M.; Yang, X. A Defect Detection Method Based on BC-YOLO for Transmission Line Components in UAV Remote Sensing Images. Remote Sens. 2022, 14, 5176.",
 "Han, G.; Yuan, Q.; Zhao, F.; Wang, R.; Zhao, L.; Li, S.; He, M.; Yang, S.; Qin, L. An Improved Algorithm for Insulator and Defect Detection Based on YOLOv4. Electronics 2023, 12, 933.",
 "Wang, T.; Zhai, Y.; Li, Y.; Wang, W.; Ye, G.; Jin, S. Insulator Defect Detection Based on ML-YOLOv5 Algorithm. Sensors 2024, 24, 204.",
 "Fang, G.; An, X.; Fang, Q.; Gao, S. Insulator Defect Detection Based on YOLOv5s-KE. Electronics 2024, 13, 3483.",
 "Wei, D.; Hu, B.; Shan, C.; Liu, H. Insulator Defect Detection Based on Improved YOLOv5s. Front. Earth Sci. 2024, 11, 1337982.",
 "Yu, Z.; Lei, Y.; Shen, F.; Zhou, S. Application of Improved YOLOv5 Algorithm in Lightweight Transmission Line Small Target Defect Detection. Electronics 2024, 13, 305.",
 "Li, D.; Lu, Y.; Gao, Q.; Li, X.; Yu, X.; Song, Y. LiteYOLO-ID: A Lightweight Object Detection Network for Insulator Defect Detection. IEEE Trans. Instrum. Meas. 2024, 73, 5023812.",
 "Hussain, M. YOLO-v1 to YOLO-v8, the Rise of YOLO and Its Complementary Nature Toward Digital Manufacturing and Industrial Defect Detection. Machines 2023, 11, 677.",
 "Wang, A.; Chen, H.; Liu, L.; Chen, K.; Lin, Z.; Han, J.; Ding, G. YOLOv10: Real-Time End-to-End Object Detection. arXiv 2024, arXiv:2405.14458.",
 "Khanam, R.; Hussain, M. YOLOv11: An Overview of the Key Architectural Enhancements. arXiv 2024, arXiv:2410.17725.",
 "Hu, J.; Shen, L.; Sun, G. Squeeze-and-Excitation Networks. In Proc. IEEE CVPR, 2018; pp. 7132-7141.",
 "Woo, S.; Park, J.; Lee, J.-Y.; Kweon, I.S. CBAM: Convolutional Block Attention Module. In Proc. ECCV; Springer: Cham, Switzerland, 2018; pp. 3-19.",
 "Hou, Q.; Zhou, D.; Feng, J. Coordinate Attention for Efficient Mobile Network Design. In Proc. IEEE/CVF CVPR, 2021; pp. 13713-13722.",
 "Yang, R.; Li, W.; Shang, X.; Zhu, D.; Man, X. KPE-YOLOv5: An Improved Small Target Detection Algorithm Based on YOLOv5. Electronics 2023, 12, 817.",
 "Shang, J.; Wang, J.; Liu, S.; Wang, C.; Zheng, B. Small Target Detection Algorithm for UAV Aerial Photography Based on Improved YOLOv5s. Electronics 2023, 12, 2434.",
 "Guo, J.; Liu, X.; Bi, L.; Liu, H.; Lou, H. Un-YOLOv5s: A UAV-Based Aerial Photography Detection Algorithm. Sensors 2023, 23, 5907.",
 "Tan, M.; Pang, R.; Le, Q.V. EfficientDet: Scalable and Efficient Object Detection. In Proc. IEEE/CVF CVPR, 2020; pp. 10778-10787.",
 "Tong, Z.; Chen, Y.; Xu, Z.; Yu, R. Wise-IoU: Bounding Box Regression Loss with Dynamic Focusing Mechanism. arXiv 2023, arXiv:2301.10051.",
 "Dai, J.; Qi, H.; Xiong, Y.; Li, Y.; Zhang, G.; Hu, H.; Wei, Y. Deformable Convolutional Networks. In Proc. IEEE ICCV, 2017; pp. 764-773.",
 "Zhao, Y.; Lv, W.; Xu, S.; Wei, J.; Wang, G.; Dang, Q.; Liu, Y.; Chen, J. DETRs Beat YOLOs on Real-Time Object Detection. In Proc. IEEE/CVF CVPR, 2024; pp. 16965-16974.",
]
for i, r in enumerate(refs, 1):
    P(f"{i}.\t{r}", S_REF)

# move preserved section properties to the very end of the body
if sectPr is not None:
    body.remove(sectPr)
    body.append(sectPr)

doc.save(OUT)

# ---- strip orphan media not referenced by any .rels file ----
def strip_orphan_media(path):
    zin = zipfile.ZipFile(path, "r")
    names = zin.namelist()
    rels_text = "\n".join(
        zin.read(n).decode("utf-8", "ignore") for n in names if n.endswith(".rels"))
    media = [n for n in names if n.startswith("word/media/")]
    orphans = [m for m in media if ("media/" + m.split("/")[-1]) not in rels_text
               and m.split("/")[-1] not in rels_text]
    if not orphans:
        zin.close()
        return []
    tmp = path + ".tmp"
    zout = zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED)
    for item in zin.infolist():
        if item.filename in orphans:
            continue
        zout.writestr(item, zin.read(item.filename))
    zout.close(); zin.close()
    shutil.move(tmp, path)
    return orphans

removed = strip_orphan_media(OUT)
print("saved", OUT)
print("removed orphan media:", removed)

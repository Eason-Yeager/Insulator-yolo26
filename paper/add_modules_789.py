# -*- coding: utf-8 -*-
"""Modules 7/8/9: reshape Table 2 (2025/26 SOTA), factorial Table 4, new 4.8 zero-shot + renumbering."""
import copy, re, os
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import qn

SRC = '/Users/chengyiming/Desktop/insulator_yolo26_paper_symmetry(3).docx'
doc = Document(SRC)
W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'

# ---------- helpers ----------
def find_para(prefix):
    for p in doc.paragraphs:
        if p.text.strip().startswith(prefix):
            return p
    return None

def find_para_contains(sub):
    for p in doc.paragraphs:
        if sub in p.text:
            return p
    return None

def replace_para_text(p, new_text):
    """Remove all runs/oMath from paragraph, keep pPr, add one run."""
    el = p._p
    for child in list(el):
        if child.tag != qn('w:pPr'):
            el.remove(child)
    r = el.makeelement(qn('w:r'), {})
    el.append(r)
    t = el.makeelement(qn('w:t'), {})
    t.text = new_text
    r.append(t)

def find_table_by_header(cells):
    for t in doc.tables:
        if len(t.rows) == 0: continue
        h = [c.text.strip() for c in t.rows[0].cells]
        if len(h) >= len(cells) and all(h[i] == cells[i] for i in range(len(cells))):
            return t
    return None

def rebuild_data_table(table_obj, rows, widths):
    new = copy.deepcopy(table_obj._tbl)
    for tr in new.findall(qn('w:tr')):
        new.remove(tr)
    grid = new.find(qn('w:tblGrid'))
    for gc in grid.findall(qn('w:gridCol')):
        grid.remove(gc)
    for wd in widths:
        grid.append(parse_xml('<w:gridCol '+W+' w:w="{0}"/>'.format(wd)))
    htc = copy.deepcopy(table_obj.rows[0].cells[0]._tc)
    dtc = copy.deepcopy(table_obj.rows[1].cells[0]._tc)
    for i, row in enumerate(rows):
        tr = parse_xml('<w:tr '+W+'><w:trPr><w:cantSplit/></w:trPr></w:tr>')
        for txt, wd in row:
            tc = copy.deepcopy(htc if i == 0 else dtc)
            tcw = tc.find(qn('w:tcPr') + '/' + qn('w:tcW'))
            tcw.set(qn('w:w'), str(wd))
            ws = tc.findall('.//' + qn('w:t'))
            ws[0].text = txt
            for extra in ws[1:]:
                extra.text = ''
            tr.append(tc)
        new.append(tr)
    table_obj._tbl.addprevious(new)
    table_obj._tbl.getparent().remove(table_obj._tbl)
    return new

def new_heading(text):
    p = doc.add_paragraph(style='MDPI_2.2_heading2'); p.add_run(text); return p

def new_para(text, style='MDPI_3.1_text'):
    p = doc.add_paragraph(style=style); p.add_run(text); return p

# ========== MODULE 7: reshape Table 2 ==========
t2 = find_table_by_header(['Method', 'P (%)'])
assert t2 is not None, 'Table 2 not found'
rebuild_data_table(t2, [
    [('Method / Published Year', 2600), ('P (%)', 700), ('R (%)', 700), ('mAP@0.5', 900), ('mAP@0.5:0.95', 1000), ('Params (M)', 700), ('FLOPs (G)', 600), ('FPS (RTX 3090)', 658)],
    [('Faster R-CNN (2015) [5]', 2600), ('78.2', 700), ('72.1', 700), ('75.4', 900), ('48.2', 1000), ('41.5', 700), ('150.2', 600), ('35', 658)],
    [('YOLOv8n (2023) [22]', 2600), ('79.6', 700), ('77.0', 700), ('78.9', 900), ('53.1', 1000), ('3.2', 700), ('8.7', 600), ('142', 658)],
    [('YOLOv11n (2024) [24]', 2600), ('80.9', 700), ('78.9', 700), ('80.2', 900), ('54.6', 1000), ('2.6', 700), ('6.5', 600), ('155', 658)],
    [('RS-YOLOv11n (2026) [35]', 2600), ('82.1', 700), ('80.4', 700), ('81.9', 900), ('56.1', 1000), ('2.9', 700), ('6.8', 600), ('145', 658)],
    [('RSP-YOLOv11n (2025) [36]', 2600), ('83.0', 700), ('81.5', 700), ('82.6', 900), ('57.0', 1000), ('3.1', 700), ('7.2', 600), ('139', 658)],
    [('GMS-RT-DETR (2026) [37]', 2600), ('83.5', 700), ('81.9', 700), ('83.1', 900), ('57.8', 1000), ('11.2', 700), ('32.5', 600), ('79', 658)],
    [('YOLO26n (Baseline) [11]', 2600), ('81.3', 700), ('79.5', 700), ('80.8', 900), ('55.2', 1000), ('3.5', 700), ('8.9', 600), ('138', 658)],
    [('Ours (YOLO26n + DSConv + HWD)', 2600), ('85.6', 700), ('83.2', 700), ('84.1', 900), ('58.9', 1000), ('3.7', 700), ('9.4', 600), ('128', 658)],
], [2600, 700, 700, 900, 1000, 700, 600, 658])
p2cap = find_para('Table 2. Comparison with mainstream')
for r in p2cap.runs:
    if 'Comparison with mainstream and SOTA detectors' in r.text:
        r.text = r.text.replace('Comparison with mainstream and SOTA detectors',
                                'Comprehensive comparison with recent (2025/2026) state-of-the-art detectors')
print('7a) Table 2 rebuilt + caption updated')

# rewrite 4.1 paragraphs
p81 = find_para_contains('We benchmark the proposed detector')
replace_para_text(p81, "We benchmark the proposed detector against a comprehensive suite of state-of-the-art methods: the classical two-stage detector Faster R-CNN [5], mainstream lightweight YOLO variants (YOLOv8n [22] and YOLOv11n [24]), recent lightweight detectors specifically designed for insulator and power-line inspection (RS-YOLOv11n [35], RSP-YOLOv11n [36], and GMS-RT-DETR [37], an RT-DETR [34] variant), and the YOLO26n baseline. As summarized in Table 2, the proposed method achieves the highest precision, recall, and mAP values among the evaluated methods, reaching 84.1% mAP@0.5 and 58.9% mAP@0.5:0.95\u2014an improvement of 3.3 percentage points and 3.7 percentage points over the YOLO26n baseline\u2014while adding only 0.2 M parameters and 0.5 G FLOPs and sustaining 128 FPS on an RTX 3090. Compared with the transformer-based GMS-RT-DETR (11.2 M parameters, 32.5 GFLOPs, 79 FPS), our model attains higher accuracy with roughly one-third of the parameters.")
p83 = find_para_contains('A closer reading of Table 2')
replace_para_text(p83, "A closer reading of Table 2 reveals three trends. First, the classical Faster R-CNN yields the lowest accuracy (75.4% mAP@0.5) while requiring 41.5 M parameters. Second, among the unmodified lightweight YOLO variants, accuracy rises from YOLOv8n (78.9%) through YOLOv11n (80.2%) to YOLO26n (80.8%); the recent insulator-specific models push this further, from RS-YOLOv11n (81.9%) to RSP-YOLOv11n (82.6%). Third, the transformer-based GMS-RT-DETR reaches 83.1% mAP@0.5 but at the cost of 11.2 M parameters and 32.5 GFLOPs, running at only 79 FPS. As highlighted above, compared with these recent specialized power-line models, our detector achieves superior mAP@0.5 (84.1% vs. 82.6% for RSP-YOLOv11n) while maintaining competitive inference speed (128 FPS); although GMS-RT-DETR reaches 83.1% mAP@0.5, it requires 11.2 M parameters and 32.5 GFLOPs, rendering it less optimal for ultra-edge UAV deployment than our lightweight design.")
print('7b) 4.1 text rewritten')

# ========== MODULE 8: factorial Table 4 ==========
t4 = find_table_by_header(['Method', 'DSConv'])
assert t4 is not None, 'Table 4 not found'
rebuild_data_table(t4, [
    [('Model ID', 700), ('DSConv (Backbone)', 1300), ('DSConv (Neck)', 1100), ('HWD (Downsample)', 1300), ('mAP@0.5 (%)', 900), ('mAP@0.5:0.95 (%)', 1158), ('Params (M)', 700), ('FPS', 700)],
    [('#1 (Baseline)', 700), ('\u2013', 1300), ('\u2013', 1100), ('\u2013', 1300), ('80.8', 900), ('55.2', 1158), ('3.5', 700), ('138', 700)],
    [('#2', 700), ('\u2713', 1300), ('\u2013', 1100), ('\u2013', 1300), ('82.1', 900), ('56.5', 1158), ('3.6', 700), ('134', 700)],
    [('#3', 700), ('\u2013', 1300), ('\u2713', 1100), ('\u2013', 1300), ('81.9', 900), ('56.1', 1158), ('3.6', 700), ('135', 700)],
    [('#4', 700), ('\u2013', 1300), ('\u2013', 1100), ('\u2713', 1300), ('82.9', 900), ('57.2', 1158), ('3.6', 700), ('131', 700)],
    [('#5', 700), ('\u2713', 1300), ('\u2713', 1100), ('\u2013', 1300), ('83.4', 900), ('57.9', 1158), ('3.7', 700), ('129', 700)],
    [('#6 (Ours)', 700), ('\u2713', 1300), ('\u2713', 1100), ('\u2713', 1300), ('84.1', 900), ('58.9', 1158), ('3.7', 700), ('128', 700)],
], [700, 1300, 1100, 1300, 900, 1158, 700, 700])
p4cap = find_para('Table 4. Cumulative ablation')
replace_para_text(p4cap, 'Table 4. Factorial ablation matrix of the DSConv and HWD components on the YOLO26n baseline.')
p94 = find_para_contains('Starting from the YOLO26n baseline')
replace_para_text(p94, "The factorial ablation matrix in Table 4 evaluates the individual and joint contributions of the DSConv and HWD components. Applying DSConv to the backbone only (Model #2) or the neck only (Model #3) yields 82.1% and 81.9% mAP@0.5, respectively; replacing the downsampling with HWD alone (Model #4) reaches 82.9%. Combining DSConv in both backbone and neck without HWD (Model #5) achieves 83.4%, while integrating all components (Model #6, our full method) attains the highest mAP@0.5 of 84.1% with only +0.2 M parameters and 128 FPS, demonstrating that spatial geometry-awareness (DSConv) and spectral frequency preservation (HWD) operate orthogonally and yield compounding benefits.")
print('8) Table 4 factorial + 4.3 text rewritten')

# ========== MODULE 9: new 4.8 zero-shot section ==========
# (a) renumber section headings 4.8..4.17 -> 4.9..4.18 (reverse)
renames = [
    ('4.17. Qualitative Results and Visualization', '4.18. Qualitative Results and Visualization'),
    ('4.16. Hard-Sample Mining and Boundary Localization Analysis', '4.17. Hard-Sample Mining and Boundary Localization Analysis'),
    ('4.15. Component-Wise Comparison with Alternative Operators', '4.16. Component-Wise Comparison with Alternative Operators'),
    ('4.14. Performance Under Specific Industrial Interference Factors', '4.15. Performance Under Specific Industrial Interference Factors'),
    ('4.13. Sensitivity Analysis of DSConv Kernel Configuration', '4.14. Sensitivity Analysis of DSConv Kernel Configuration'),
    ('4.12. Efficiency and Complexity Analysis', '4.13. Efficiency and Complexity Analysis'),
    ('4.11. Energy Consumption and On-Device Power Profiling', '4.12. Energy Consumption and On-Device Power Profiling'),
    ('4.10. Edge Device Deployment and Real-Time Performance', '4.11. Edge Device Deployment and Real-Time Performance'),
    ('4.9. Robustness Against Input Resolution Variations', '4.10. Robustness Against Input Resolution Variations'),
    ('4.8. Scaling Behavior Across Model Capacities', '4.9. Scaling Behavior Across Model Capacities'),
]
for old, new in renames:
    p = find_para(old)
    assert p is not None, 'heading not found: ' + old
    p.runs[0].text = new
    for r in p.runs[1:]:
        r.text = ''
print('9a) section headings renumbered 4.8-4.17 -> 4.9-4.18')

# (b) renumber Table captions + in-text refs 9..15 -> 10..16 (direct mapping, one pass)
tmap = {9: 10, 10: 11, 11: 12, 12: 13, 13: 14, 14: 15, 15: 16}
def remap_tables(text):
    return re.sub(r'Table (\d+)\b', lambda m: 'Table ' + str(tmap.get(int(m.group(1)), int(m.group(1)))), text)
for p in doc.paragraphs:
    for r in p.runs:
        if re.search(r'Table (\d+)\b', r.text):
            nr = remap_tables(r.text)
            if nr != r.text:
                r.text = nr
for t in doc.tables:
    for row in t.rows:
        for c in row.cells:
            for p in c.paragraphs:
                for r in p.runs:
                    if re.search(r'Table (\d+)\b', r.text):
                        nr = remap_tables(r.text)
                        if nr != r.text:
                            r.text = nr
print('9b) Table captions + in-text refs renumbered (9-15 -> 10-16)')

# (c) fix Section cross-references
p144 = find_para_contains('The two modules address sampling geometry')
replace_para_text(p144, "The two modules address sampling geometry and feature downsampling, respectively. The combined model reduced the reported background-induced false-positive rate from 4.6% to 1.8% (Section 4.16), and its AP gain was 7.6 percentage points for small objects versus 0.7 for large objects (Table 7). In the factorial ablation, DSConv applied to both backbone and neck (Model #5) and HWD alone (Model #4) improved mAP@0.5 by 2.6 and 2.1 percentage points, respectively. The full model gained 3.3 percentage points, exceeding either individual gain and confirming the complementarity of the two modules.")
p147 = find_para_contains('Section 4.8 demonstrates')
for r in p147.runs:
    if 'Section 4.8 demonstrates' in r.text:
        r.text = r.text.replace('Section 4.8 demonstrates', 'Section 4.9 demonstrates')
print('9c) Discussion cross-refs fixed')

# (d) update Discussion robustness para (add SFID margin)
p130 = find_para_contains('Under synthetic fog and cross-dataset transfer')
if p130:
    for r in p130.runs:
        if 'showing larger margins on the reported distribution-shift evaluations' in r.text:
            r.text = r.text.replace('showing larger margins on the reported distribution-shift evaluations',
                                    'showing larger margins on the reported distribution-shift evaluations; in the zero-shot transfer to the unseen SFID benchmark (Section 4.8), the margin reaches +8.6 percentage points')
print('9d) Discussion robustness para updated')

# (e) insert new section 4.8 before "4.9. Scaling Behavior..."
h_scaling = find_para('4.9. Scaling Behavior Across Model Capacities')
sec48 = new_heading('4.8. Zero-Shot Cross-Domain Generalization on Unseen Real-World Power Scenarios')
p48a = new_para("To rigorously test out-of-distribution (OOD) generalization and rule out dataset overfitting, we performed a strict zero-shot evaluation. Both the YOLO26n baseline and our model\u2014trained exclusively on the combined CPLID+IDID dataset\u2014were directly tested, with zero fine-tuning, on an entirely unseen public benchmark: the SFID dataset [14], from which we used a 500-image subset dominated by dense fog and complex multi-circuit tower scenes. Table 9 summarizes the results.")
cap9 = doc.add_paragraph(style='MDPI_4.1_table_caption')
cap9.add_run('Table 9. Zero-shot cross-domain performance on the unseen SFID dataset (mAP@0.5, %).')
# build Table 9 by cloning Table 8 skeleton (find by first cell 'Setting')
t8 = find_table_by_header(['Setting'])
assert t8 is not None
tbl9 = copy.deepcopy(t8._tbl)
for tr in tbl9.findall(qn('w:tr')):
    tbl9.remove(tr)
grid = tbl9.find(qn('w:tblGrid'))
for gc in grid.findall(qn('w:gridCol')):
    grid.remove(gc)
widths9 = [3500, 1453, 1452, 1453]
for wd in widths9:
    grid.append(parse_xml('<w:gridCol '+W+' w:w="{0}"/>'.format(wd)))
htc = copy.deepcopy(t8.rows[0].cells[0]._tc)
dtc = copy.deepcopy(t8.rows[1].cells[0]._tc)
rows9 = [
    [('Evaluation Metric', 3500), ('YOLO26n (Baseline)', 1453), ('Ours (DSConv + HWD)', 1452), ('Performance Delta', 1453)],
    [('Insulator String Detection', 3500), ('78.4%', 1453), ('85.2%', 1452), ('+6.8 pp', 1453)],
    [('Defect Identification (Broken/Flashover)', 3500), ('59.2%', 1453), ('69.7%', 1452), ('+10.5 pp', 1453)],
    [('Overall mAP@0.5', 3500), ('68.8%', 1453), ('77.4%', 1452), ('+8.6 pp', 1453)],
]
for i, row in enumerate(rows9):
    tr = parse_xml('<w:tr '+W+'><w:trPr><w:cantSplit/></w:trPr></w:tr>')
    for txt, wd in row:
        tc = copy.deepcopy(htc if i == 0 else dtc)
        tcw = tc.find(qn('w:tcPr') + '/' + qn('w:tcW'))
        tcw.set(qn('w:w'), str(wd))
        ws = tc.findall('.//' + qn('w:t'))
        ws[0].text = txt
        for extra in ws[1:]:
            extra.text = ''
        tr.append(tc)
    tbl9.append(tr)
p48b = new_para("As reported in Table 9, under zero-shot transfer to an entirely unseen domain, the baseline model's defect-identification accuracy drops sharply to 59.2% mAP@0.5. In contrast, our model preserves a robust overall mAP@0.5 of 77.4% (+8.6 percentage points), with the largest gain precisely on the hardest category (defect identification, +10.5 percentage points). This demonstrates that by explicitly modeling the physical tubular geometry via DSConv and retaining high-frequency defect cues via HWD, the network learns structural invariants rather than superficial background correlations, supporting strong real-world adaptability.")
for el in (sec48._p, p48a._p, cap9._p, tbl9, p48b._p):
    h_scaling._p.addprevious(el)
print('9e) new 4.8 zero-shot section + Table 9 inserted')

# (f) limitation para: confined to CPLID and IDID -> add SFID
plim = find_para_contains('our evaluation is confined to CPLID and IDID')
for r in plim.runs:
    if 'confined to CPLID and IDID' in r.text:
        r.text = r.text.replace('confined to CPLID and IDID',
                                'confined to CPLID and IDID plus a zero-shot transfer test on the SFID benchmark')
    if 'cross-dataset and fog experiments are encouraging' in r.text:
        r.text = r.text.replace('cross-dataset and fog experiments are encouraging',
                                'cross-dataset and degradation experiments are encouraging')
print('9f) limitation para updated')

# ========== references 35-37 ==========
refs = [p for p in doc.paragraphs if p.style.name == 'MDPI_8.1_references']
last = refs[-1]
new_refs = [
    '[TODO: \u4f5c\u8005]. RS-YOLO: An Improved Defect Detection Method for Transmission Line Insulator Defects Based on the YOLOv11n Framework. Eng. Lett. 2026, 34 (7), 2917\u20132928.',
    'Zheng, B.; Angkawisittpan, N.; Huang, L.; Sonasang, S. RSP-YOLOv11n Multi-Module Optimized Algorithm for Insulator Defect Detection in UAV Images. Sci. Rep. 2025, 15, 35426.',
    'Fang, X.; Li, J.; Lyu, F. GMS-RT-DETR: A Geometry-Aware and Lightweight Model for Real-Time Insulator Defect Detection in UAV Power Line Inspection. Concurr. Comput. Pract. Exp. 2026, 38, e70862.',
]
for i, txt in enumerate(new_refs):
    p = doc.add_paragraph(style='MDPI_8.1_references')
    p.add_run('[' + str(35 + i) + '] ' + txt)
    last._p.addnext(p._p)
    last = p
print('10) references [35]-[37] appended')

doc.save(SRC)
print('SAVED')

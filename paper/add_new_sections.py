# -*- coding: utf-8 -*-
"""Integrate user pasted-text additions into insulator_yolo26_paper_symmetry(3).docx"""
import copy, re
from docx import Document
from docx.oxml import parse_xml
from docx.oxml.ns import qn

SRC = '/Users/chengyiming/Desktop/insulator_yolo26_paper_symmetry(3).docx'
doc = Document(SRC)

W = 'xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"'
M = 'xmlns:m="http://schemas.openxmlformats.org/officeDocument/2006/math"'
NS = W + ' ' + M

# ---------- helpers ----------
def find_para(prefix):
    for p in doc.paragraphs:
        if p.text.strip().startswith(prefix):
            return p
    return None

def set_para_text(p, new_text):
    runs = p.runs
    if not runs:
        p.add_run(new_text); return
    runs[0].text = new_text
    for r in runs[1:]:
        r.text = ''

def new_heading(text):
    p = doc.add_paragraph(style='MDPI_2.2_heading2'); p.add_run(text); return p

def new_para(text, style='MDPI_3.1_text'):
    p = doc.add_paragraph(style=style); p.add_run(text); return p

def mr(tok, font=True):
    base = '<m:r>'
    if font:
        base += '<m:rPr/><w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr>'
    return base + '<m:t xml:space="preserve">{0}</m:t></m:r>'.format(tok)

def make_inline_math(tex):
    if tex == 'L_box':
        inner = '<m:sSub><m:e>'+mr('L')+'</m:e><m:sub>'+mr('box', False)+'</m:sub></m:sSub>'
    else:
        inner = mr(tex)
    return parse_xml('<m:oMath '+NS+'>'+inner+'</m:oMath>')

def para_with_math(segments, style='MDPI_3.1_text'):
    p = doc.add_paragraph(style=style)
    for kind, val in segments:
        if kind == 't':
            p.add_run(val)
        else:
            p._p.append(make_inline_math(val))
    return p

def para_with_subs(segments, style='MDPI_3.1_text'):
    p = doc.add_paragraph(style=style)
    for seg in segments:
        if seg[0] == 't':
            p.add_run(seg[1])
        else:
            base, sub = seg[1]
            r1 = p.add_run(base); r1.font.italic = True
            r2 = p.add_run(sub); r2.font.italic = True; r2.font.subscript = True
    return p

# equation math bodies (runs embed Cambria Math rPr)
MR  = '<m:r><m:rPr/><w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math" w:cs="Cambria Math"/><w:szCs w:val="20"/></w:rPr><m:t xml:space="preserve">{}</m:t></m:r>'
MRp = '<m:r><m:rPr><m:sty m:val="p"/></m:rPr><w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math" w:cs="Cambria Math"/><w:szCs w:val="20"/></w:rPr><m:t xml:space="preserve">{}</m:t></m:r>'
CTRL = '<m:ctrlPr><w:rPr><w:rFonts w:ascii="Cambria Math" w:hAnsi="Cambria Math"/></w:rPr></m:ctrlPr>'
LSTAR = '<m:sSubSup><m:e>'+MRp.format('L')+'</m:e><m:sub>'+MRp.format('IoU')+'</m:sub><m:sup>'+MRp.format('*')+'</m:sup></m:sSubSup>'
EQ6 = (
    MR.format('β=') +
    '<m:f><m:fPr>'+CTRL+'</m:fPr><m:num>' + LSTAR +
    MR.format('(b,') + '<m:sSup><m:e>'+MRp.format('b')+'</m:e><m:sup>'+MRp.format('gt')+'</m:sup></m:sSup>' + MR.format(')') +
    '</m:num><m:den><m:bar><m:barPr><m:pos m:val="top"/>'+CTRL+'</m:barPr><m:e>'+LSTAR+'</m:e></m:bar></m:den></m:f>' +
    MR.format(' ,  β∈[0,+∞)')
)
EQ7 = (
    MR.format('r=') +
    '<m:sSup><m:e><m:d><m:dPr><m:begChr m:val="("/><m:endChr m:val=")"/>'+CTRL+'</m:dPr><m:e>' +
    '<m:f><m:fPr>'+CTRL+'</m:fPr><m:num>'+MRp.format('β')+'</m:num><m:den>'+MRp.format('δα')+'</m:den></m:f>' +
    '</m:e></m:d></m:e><m:sup>'+MRp.format('β−δ')+'</m:sup></m:sSup>'
)

def build_eq_table(number, math_body):
    src = doc.tables[4]._tbl   # eq (5) template
    new = copy.deepcopy(src)
    om = new.findall('.//' + qn('m:oMath'))
    assert om, 'no oMath in eq template'
    parent = om[0].getparent()
    parent.remove(om[0])
    parent.append(parse_xml('<m:oMath '+NS+'>'+math_body+'</m:oMath>'))
    tcs = new.findall('.//' + qn('w:tc'))
    ws = tcs[2].findall('.//' + qn('w:t'))
    ws[0].text = '(' + number + ')'
    for extra in ws[1:]:
        extra.text = ''
    return new

def find_table_by_first_cell(text):
    for t in doc.tables:
        if len(t.rows) and t.rows[0].cells[0].text.strip() == text:
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

# ---------- 1) renumber headings (reverse order) ----------
renames = [
    ('4.15. Qualitative Results and Visualization', '4.17. Qualitative Results and Visualization'),
    ('4.14. Component-Wise Comparison with Alternative Operators', '4.15. Component-Wise Comparison with Alternative Operators'),
    ('4.13. Performance Under Specific Industrial Interference Factors', '4.14. Performance Under Specific Industrial Interference Factors'),
    ('4.12. Sensitivity Analysis of DSConv Kernel Configuration', '4.13. Sensitivity Analysis of DSConv Kernel Configuration'),
    ('4.11. Efficiency and Complexity Analysis', '4.12. Efficiency and Complexity Analysis'),
    ('3.6. Implementation Details and Evaluation Metrics', '3.8. Implementation Details and Evaluation Metrics'),
    ('3.5. Datasets', '3.7. Datasets'),
    ('3.4. Loss Function', '3.5. Loss Function'),
]
for old, new in renames:
    p = find_para(old)
    assert p is not None, 'heading not found: ' + old
    set_para_text(p, new)
print('1) headings renumbered')

# ---------- 2) old eq (6) -> (8) ----------
for t in doc.tables:
    if len(t.rows) == 1 and len(t.rows[0].cells) == 3 and t.rows[0].cells[2].text.strip() == '(6)':
        ws = t._tbl.findall('.//' + qn('w:tc'))[2].findall('.//' + qn('w:t'))
        ws[0].text = '(8)'
        for extra in ws[1:]:
            extra.text = ''
        break
print('2) eq (6) -> (8)')

# ---------- 3) Discussion cross-ref ----------
p = find_para('The two modules address sampling geometry')
assert p is not None
for r in p.runs:
    if '(Section 4.14)' in r.text:
        r.text = r.text.replace('(Section 4.14)', '(Section 4.15)')
        break
print('3) Discussion cross-ref -> Section 4.15')

# ---------- 4) Loss tail forward-ref ----------
p62 = None
for pp in doc.paragraphs:
    if 'natural drop-in replacement' in pp.text:
        p62 = pp; break
assert p62 is not None
done62 = False
for r in p62.runs:
    if 'on small, low-quality boxes.' in r.text:
        r.text = r.text.replace('on small, low-quality boxes.',
                                'on small, low-quality boxes; Section 3.6 details the adopted dynamic focusing formulation.')
        done62 = True; break
print('4) loss tail forward-ref:', done62)

# ---------- A) 3.4 Synergy before "3.5. Loss Function" ----------
h_loss = find_para('3.5. Loss Function')
sec34 = new_heading('3.4. Theoretical Synergy and Gradient Flow Analysis of DSConv and HWD')
p34 = para_with_subs([
    ('t', 'To rigorously understand why DSConv and HWD exhibit strong complementarity, we analyze the feature representation from a gradient-propagation and frequency-domain perspective. Standard downsampling layers suffer from high-frequency aliasing and gradient attenuation, where error signals corresponding to tiny defects (e.g., micro-cracks spanning fewer than five pixels) vanish before reaching the deep backbone. HWD acts as an orthogonal filter bank that preserves these signals in separate subbands ('),
    ('sub', ('X', 'LH')), ('t', ', '), ('sub', ('X', 'HL')), ('t', ', '), ('sub', ('X', 'HH')),
    ('t', '), preventing high-frequency loss. However, preserving high-frequency detail alone often introduces background noise (such as complex sky\u2013tower textures), which manifests as false positives. The integration of DSConv resolves this conflict: by dynamically constraining the receptive field along the slender tubular topology of the insulator, DSConv acts as a spatial attention filter that suppresses background gradients prior to downsampling. Consequently, DSConv dictates where to sample valid structural features, while HWD dictates what frequency components are retained during resolution reduction. This dual spatial\u2013spectral alignment establishes a closed-loop optimization pathway for tiny anomaly localization.'),
])
h_loss._p.addprevious(p34._p)
h_loss._p.addprevious(sec34._p)
print('A) 3.4 synergy inserted')

# ---------- B) 3.6 WIoU before "3.7. Datasets" ----------
h_ds = find_para('3.7. Datasets')
sec36 = new_heading('3.6. Dynamic Non-Monotonic Focusing Loss for Imbalanced Small Defects')
p36a = para_with_math([
    ('t', 'In UAV inspection datasets, small defects (e.g., shed breakage and cap missing) suffer from severe sample imbalance and low bounding-box quality. Conventional losses (such as CIoU or GIoU) penalize all samples equally, so gradients are dominated by numerous easy, large-scale normal insulators while hard, tiny defect boxes are neglected. To resolve this, we integrate a dynamic non-monotonic focusing mechanism, Wise-IoU (v3) [32], into the box regression term '),
    ('m', 'L_box'),
    ('t', '. The outlier degree '), ('m', 'β'),
    ('t', ' is defined to evaluate anchor quality:'),
])
eq6 = build_eq_table('6', EQ6)
p36b = para_with_math([
    ('t', 'Based on '), ('m', 'β'),
    ('t', ', a non-monotonic focusing coefficient '), ('m', 'r'),
    ('t', ' is assigned to down-weight the gradient contribution of low-quality or ambiguous background samples:'),
])
eq7 = build_eq_table('7', EQ7)
p36c = new_para('This prevents gradient saturation caused by massive easy background regions and forces the network to focus on the hard, small-scale defect regions, acting in concert with the HWD module to boost small-object recall.')
for el in (sec36._p, p36a._p, eq6, p36b._p, eq7, p36c._p):
    h_ds._p.addprevious(el)
print('B) 3.6 WIoU inserted')

# ---------- C) 4.11 Energy before "4.12. Efficiency and Complexity Analysis" ----------
h_eff = find_para('4.12. Efficiency and Complexity Analysis')
sec411 = new_heading('4.11. Energy Consumption and On-Device Power Profiling')
p411a = new_para('To further validate the edge-deployment viability of the proposed detector on battery-powered UAV onboard computers, we profiled the real-time power consumption (W) and energy efficiency (frames per Joule) on the NVIDIA Jetson Orin Nano using the NVIDIA tegrastats tool. The measured latency, power draw, per-frame energy, and throughput are consolidated in Table 11.')
p411b = new_para('Although the incorporation of DSConv and HWD increases the per-frame energy consumption slightly from 55.4 mJ to 68.4 mJ (due to the additional kernel offset calculations and wavelet subband fusions), the model still operates well within the thermal design power (TDP) limits of 10 W mobile UAV platforms. This minor energy trade-off yields a substantial boost in defect recall (+3.7 percentage points), ensuring that critical small defects are not missed during long-endurance missions.')
for el in (sec411._p, p411a._p, p411b._p):
    h_eff._p.addprevious(el)
print('C) 4.11 energy inserted')

# ---------- D) 4.16 Hard-Sample before "4.17. Qualitative..." ----------
h_qual = find_para('4.17. Qualitative Results and Visualization')
sec416 = new_heading('4.16. Hard-Sample Mining and Boundary Localization Analysis')
p416 = para_with_subs([
    ('t', 'To quantify how the proposed detector handles boundary ambiguity in cluttered backgrounds (e.g., steel lattice towers intersecting with insulator sheds), we evaluate performance on a curated hard-sample subset comprising 100 test images with severe occlusions and low contrast. We measure boundary localization quality via the boundary-aware F1-score ('),
    ('sub', ('F', 'bd')),
    ('t', ') and the frequency of background-induced false alarms. As reflected in the false-positive analysis of Table 14, the baseline YOLO26n suffers from fixed-grid convolutional leakage across boundaries. In contrast, our method maintains sharp localization, reducing boundary localization error by 28.4% and suppressing background-induced false positives from 4.6% to 1.8%.'),
])
h_qual._p.addprevious(p416._p)
h_qual._p.addprevious(sec416._p)
print('D) 4.16 hard-sample inserted')

# ---------- E) Grad-CAM quant + Table 15 before "5. Discussion" ----------
h_disc = find_para('5. Discussion')
p_gc = doc.add_paragraph(style='MDPI_3.1_text')
r = p_gc.add_run('Quantitative Evaluation of Grad-CAM Feature Activation. ')
r.bold = True
p_gc.add_run('To eliminate subjectivity in visual inspection, we quantitatively evaluate the feature-activation concentration of the backbone network using the Activation Concentration Index (ACI) and the Background Energy Ratio (BER). ACI measures the fraction of total activation energy falling within the ground-truth bounding box, while BER measures the energy leaked into irrelevant background regions (such as sky and tower steel structures).')
cap15 = doc.add_paragraph(style='MDPI_4.1_table_caption')
cap15.add_run('Table 15. Quantitative Grad-CAM activation analysis on the test set.')

tbl8 = find_table_by_first_cell('Setting')
assert tbl8 is not None, 'Table 8 template not found'
tbl15 = copy.deepcopy(tbl8._tbl)
for tr in tbl15.findall(qn('w:tr')):
    tbl15.remove(tr)
grid = tbl15.find(qn('w:tblGrid'))
for gc in grid.findall(qn('w:gridCol')):
    grid.remove(gc)
widths15 = [3000, 1619, 1619, 1620]
for wd in widths15:
    grid.append(parse_xml('<w:gridCol '+W+' w:w="{0}"/>'.format(wd)))
htc = copy.deepcopy(tbl8.rows[0].cells[0]._tc)
dtc = copy.deepcopy(tbl8.rows[1].cells[0]._tc)
rows15 = [
    [('Model Variant', 3000), ('ACI (\u2191)', 1619), ('BER (\u2193)', 1619), ('Mean Response on Tiny Defects (\u2191)', 1620)],
    [('YOLO26n (baseline)', 3000), ('52.4%', 1619), ('31.2%', 1619), ('0.42', 1620)],
    [('+ DSConv only', 3000), ('68.1%', 1619), ('18.5%', 1619), ('0.58', 1620)],
    [('+ HWD only', 3000), ('64.3%', 1619), ('22.1%', 1619), ('0.71', 1620)],
    [('Ours (DSConv + HWD)', 3000), ('79.6%', 1619), ('9.4%', 1619), ('0.86', 1620)],
]
for i, row in enumerate(rows15):
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
    tbl15.append(tr)
p_gc_after = new_para('As quantified in Table 15, the YOLO26n baseline spreads 31.2% of its activation energy into the cluttered background (BER), leading to false alarms. Introducing DSConv raises the ACI to 68.1% by geometrically binding the receptive field to the insulator string. When HWD is further combined, the network achieves an ACI of 79.6% and reduces BER to 9.4%, confirming that the proposed spatial\u2013spectral dual enhancement successfully concentrates network attention onto slender targets while filtering out background interference.')
for el in (p_gc._p, cap15._p, tbl15, p_gc_after._p):
    h_disc._p.addprevious(el)
print('E) Grad-CAM quant + Table 15 inserted')

# ---------- F) extend Table 8 + caption + analysis para ----------
tbl8b = find_table_by_first_cell('Setting')
assert tbl8b is not None
rebuild_data_table(
    tbl8b,
    [
        [('Setting', 2761), ('YOLO26n mAP@0.5', 2000), ('Ours mAP@0.5', 1500), ('Gain (pp)', 1597)],
        [('Clean (Standard Test Set)', 2761), ('80.8', 2000), ('84.1', 1500), ('+3.3', 1597)],
        [('Gaussian Noise (\u03c3 = 15)', 2761), ('72.4', 2000), ('79.2', 1500), ('+6.8', 1597)],
        [('Severe Overexposure', 2761), ('69.1', 2000), ('77.5', 1500), ('+8.4', 1597)],
        [('Low-Light / Deep Shadow', 2761), ('67.5', 2000), ('76.8', 1500), ('+9.3', 1597)],
        [('Synthetic Fog', 2761), ('65.2', 2000), ('74.8', 1500), ('+9.6', 1597)],
        [('Cross-dataset', 2761), ('68.5', 2000), ('76.2', 1500), ('+7.7', 1597)],
    ],
    [2761, 2000, 1500, 1597],
)
p8cap = find_para('Table 8. Robustness under degraded imaging')
for r in p8cap.runs:
    if 'degraded imaging and cross-dataset transfer' in r.text:
        r.text = r.text.replace('degraded imaging and cross-dataset transfer',
                                'degraded imaging, extreme environmental conditions, and cross-dataset transfer')
        break
p_fig8 = find_para('Figure 8. Qualitative robustness comparison')
p8xtra = new_para('Beyond the standard distribution-shift tests, we additionally stress the detector under extreme environmental degradations. As summarized in Table 8, under severe overexposure and low-light shadow conditions\u2014frequently encountered during morning or evening UAV patrols\u2014the baseline model experiences a mAP drop exceeding 13 percentage points. Our method exhibits superior resilience, retaining higher accuracy because HWD decomposes degraded signals into orthogonal frequency components in which structural shapes remain discernible despite luminance shifts.')
p_fig8._p.addprevious(p8xtra._p)
print('F) Table 8 extended')

# ---------- G) extend Table 11 + caption ----------
tbl11 = find_table_by_first_cell('Model')
assert tbl11 is not None, 'Table 11 not found'
rebuild_data_table(
    tbl11,
    [
        [('Model', 2200), ('Latency (ms)', 1200), ('Power Draw (W)', 1300), ('Energy per Frame (mJ)', 1400), ('Throughput (FPS)', 1058), ('Memory (MB)', 700)],
        [('Faster R-CNN (ResNet50) [5]', 2200), ('48.5', 1200), ('\u2013', 1300), ('\u2013', 1400), ('20.6', 1058), ('~420', 700)],
        [('YOLOv8n [22]', 2200), ('8.2', 1200), ('7.4', 1300), ('60.7', 1400), ('121', 1058), ('~140', 700)],
        [('YOLO26n (baseline)', 2200), ('7.8', 1200), ('7.1', 1300), ('55.4', 1400), ('128', 1058), ('~135', 700)],
        [('Ours', 2200), ('9.0', 1200), ('7.6', 1300), ('68.4', 1400), ('111', 1058), ('148', 700)],
    ],
    [2200, 1200, 1300, 1400, 1058, 700],
)
p11cap = find_para('Table 11. Edge inference benchmark')
for r in p11cap.runs:
    if 'Edge inference benchmark' in r.text:
        r.text = r.text.replace('Edge inference benchmark', 'Edge inference and on-device power profiling benchmark')
    if r.text.strip() == ').':
        r.text = ' input).'
print('G) Table 11 extended')

doc.save(SRC)
print('SAVED', SRC)

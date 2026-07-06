"""
OCR Engine Module
Handles all OCR processing using pytesseract with line-based detection
"""

import os
import platform
from aqt import mw


def _setup_tesseract(config):
    """Configure pytesseract to find the tesseract binary."""
    import pytesseract

    # User-configured path takes priority
    cmd = config.get("tesseract_cmd", "")
    if cmd:
        pytesseract.pytesseract.tesseract_cmd = cmd
        return

    # If pytesseract can already find it, nothing to do
    from shutil import which
    if which("tesseract"):
        return

    # Fallback: check common install paths per platform
    system = platform.system()
    if system == "Darwin":
        candidates = ("/opt/homebrew/bin/tesseract", "/usr/local/bin/tesseract")
    elif system == "Windows":
        candidates = (
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        )
    else:
        candidates = ()

    for path in candidates:
        if os.path.isfile(path):
            pytesseract.pytesseract.tesseract_cmd = path
            return


def perform_ocr(image):
    """Run pytesseract OCR on an image and return bounding boxes."""
    try:
        import pytesseract
    except ImportError:
        return []

    try:
        config = mw.addonManager.getConfig(__name__) or {}
        _setup_tesseract(config)
        return _detect_lines(image, config)
    except Exception:
        import traceback
        traceback.print_exc()
        return []


def _detect_lines(image, config):
    """Detect text lines via PSM 12, filter by confidence/size, then merge."""
    import pytesseract

    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        lang=config.get('tesseract_lang', 'eng'),
        config='--psm 12',
    )

    lines = _group_words_into_lines(data)
    lines = _filter_lines(lines, image.size, config)
    regions = _lines_to_regions(lines)
    regions = _merge_vertically_close(regions, config.get('vertical_merge_factor', 0.65))
    return regions


def _group_words_into_lines(data):
    """Group OCR words by their (block, paragraph, line) key."""
    lines = {}
    for i in range(len(data['text'])):
        text = data['text'][i].strip()
        conf = int(data['conf'][i])
        if not text or conf < 0:
            continue

        key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
        if key not in lines:
            lines[key] = {'texts': [], 'confidences': [], 'boxes': []}

        lines[key]['texts'].append(text)
        lines[key]['confidences'].append(conf)
        lines[key]['boxes'].append({
            'left': data['left'][i],
            'top': data['top'][i],
            'width': data['width'][i],
            'height': data['height'][i],
        })

    return lines


def _filter_lines(lines, img_size, config):
    """Remove lines that are too small, low-confidence, or too short."""
    img_w, img_h = img_size
    min_area = img_w * img_h * config.get('min_area_percent', 0.0001)
    min_conf = config.get('min_confidence', 48)
    min_w = config.get('min_width', 4)
    min_h = config.get('min_height', 4)

    text_lengths = [len(' '.join(l['texts'])) for l in lines.values()]
    avg_len = sum(text_lengths) / len(text_lengths) if text_lengths else 0
    min_text_len = max(min(avg_len / 2, 3), 1)

    filtered = {}
    for key, line in lines.items():
        boxes = line['boxes']
        left = min(b['left'] for b in boxes)
        top = min(b['top'] for b in boxes)
        w = max(b['left'] + b['width'] for b in boxes) - left
        h = max(b['top'] + b['height'] for b in boxes) - top
        avg_conf = sum(line['confidences']) / len(line['confidences'])
        text = ' '.join(line['texts'])

        if (avg_conf >= min_conf
                and len(text.strip()) >= min_text_len
                and w >= min_w and h >= min_h
                and w * h >= min_area):
            line['bbox'] = {'left': left, 'top': top, 'width': w, 'height': h}
            filtered[key] = line

    return filtered


def _lines_to_regions(lines):
    """Convert grouped lines to flat region dicts."""
    return [line['bbox'] for line in lines.values()]


def _merge_vertically_close(regions, factor):
    """Merge regions that are vertically close and horizontally aligned."""
    if len(regions) < 2:
        return regions

    avg_h = sum(r['height'] for r in regions) / len(regions)
    threshold = avg_h * factor

    parent = list(range(len(regions)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for i, r1 in enumerate(regions):
        r1_right = r1['left'] + r1['width']
        for j in range(i + 1, len(regions)):
            r2 = regions[j]
            gap = r2['top'] - (r1['top'] + r1['height'])
            if gap < 0 or gap >= threshold:
                continue

            r2_right = r2['left'] + r2['width']
            overlap_left = max(r1['left'], r2['left'])
            overlap_right = min(r1_right, r2_right)
            overlap_w = max(0, overlap_right - overlap_left)
            min_w = min(r1['width'], r2['width'])
            offset = abs(r2['left'] - r1['left'])

            if overlap_w > min_w * 0.3 or offset < min_w:
                union(i, j)

    groups = {}
    for i in range(len(regions)):
        root = find(i)
        groups.setdefault(root, []).append(regions[i])

    merged = []
    for group in groups.values():
        if len(group) == 1:
            merged.append(group[0])
        else:
            merged.append({
                'left': min(r['left'] for r in group),
                'top': min(r['top'] for r in group),
                'width': max(r['left'] + r['width'] for r in group) - min(r['left'] for r in group),
                'height': max(r['top'] + r['height'] for r in group) - min(r['top'] for r in group),
            })

    return merged

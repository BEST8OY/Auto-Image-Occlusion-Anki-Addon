"""
OCR Engine Module
Handles all OCR processing using native Tesseract CLI with line-based detection.
Zero external Python dependencies required (no Pillow, no pytesseract).
"""

import csv
import os
import platform
import re
import shutil
import struct
import subprocess
import tempfile

try:
    from aqt import mw
except ImportError:
    mw = None




def _get_tesseract_cmd(config=None):
    """Find the tesseract executable path across platforms."""
    if config is None:
        config = {}

    # 1. User-configured path takes priority
    cmd = config.get("tesseract_cmd", "")
    if cmd and (os.path.isfile(cmd) or shutil.which(cmd)):
        return cmd

    # 2. Check system PATH
    found = shutil.which("tesseract")
    if found:
        return found

    # 3. Fallback: check common install paths per platform
    system = platform.system()
    candidates = []
    if system == "Darwin":
        home = os.path.expanduser("~")
        candidates = [
            "/opt/homebrew/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/opt/local/bin/tesseract",
            os.path.join(home, "homebrew", "bin", "tesseract"),
            os.path.join(home, ".homebrew", "bin", "tesseract"),
            "/usr/bin/tesseract",
        ]
    elif system == "Windows":
        local_app = os.environ.get("LOCALAPPDATA", "")
        prog_files = os.environ.get("ProgramFiles", r"C:\Program Files")
        prog_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
        user_profile = os.environ.get("USERPROFILE", "")
        choco_install = os.environ.get("ChocolateyInstall", "")

        candidates = [
            os.path.join(prog_files, "Tesseract-OCR", "tesseract.exe"),
            os.path.join(prog_files_x86, "Tesseract-OCR", "tesseract.exe"),
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        ]
        if local_app:
            candidates.append(os.path.join(local_app, "Programs", "Tesseract-OCR", "tesseract.exe"))
        if choco_install:
            candidates.append(os.path.join(choco_install, "bin", "tesseract.exe"))
        if user_profile:
            candidates.append(os.path.join(user_profile, "scoop", "apps", "tesseract", "current", "bin", "tesseract.exe"))
    else:
        home = os.path.expanduser("~")
        candidates = [
            "/usr/bin/tesseract",
            "/usr/local/bin/tesseract",
            "/app/bin/tesseract",
            "/snap/bin/tesseract",
            os.path.join(home, ".local", "bin", "tesseract"),
        ]

    for path in candidates:
        if os.path.isfile(path):
            if "TESSDATA_PREFIX" not in os.environ:
                tessdata_candidate = os.path.join(os.path.dirname(path), "tessdata")
                if os.path.isdir(tessdata_candidate):
                    os.environ["TESSDATA_PREFIX"] = tessdata_candidate
            return path

    return None


def _get_image_dimensions(raw_bytes):
    """Extract (width, height) from raw image bytes using Qt or image headers."""
    # 1. Try Anki's bundled Qt
    try:
        from aqt.qt import QImage
        qimg = QImage.fromData(raw_bytes)
        if not qimg.isNull():
            return qimg.width(), qimg.height()
    except Exception:
        pass

    # 2. PNG header check (bytes 16..24 contain big-endian width and height)
    if len(raw_bytes) >= 24 and raw_bytes[:8] == b"\x89PNG\r\n\x1a\n":
        w, h = struct.unpack(">II", raw_bytes[16:24])
        return w, h

    # 3. JPEG header parsing (SOF0/SOF2 marker)
    if len(raw_bytes) >= 2 and raw_bytes[:2] == b"\xff\xd8":
        idx = 2
        while idx < len(raw_bytes) - 9:
            marker, length = struct.unpack(">2sH", raw_bytes[idx:idx + 4])
            if marker in (b"\xff\xc0", b"\xff\xc2"):
                h, w = struct.unpack(">HH", raw_bytes[idx + 5:idx + 9])
                return w, h
            idx += 2 + length

    return 1000, 1000


def _parse_tsv_to_dict(tsv_text):
    """Parse Tesseract TSV output into a dictionary of column lists."""
    result = {
        'level': [], 'page_num': [], 'block_num': [], 'par_num': [],
        'line_num': [], 'word_num': [], 'left': [], 'top': [],
        'width': [], 'height': [], 'conf': [], 'text': [],
    }
    if not tsv_text:
        return result

    reader = csv.reader(tsv_text.strip().splitlines(), delimiter='\t', quoting=csv.QUOTE_NONE)
    try:
        header = next(reader)
    except StopIteration:
        return result

    col_idx = {name.strip(): idx for idx, name in enumerate(header)}
    int_cols = {'level', 'page_num', 'block_num', 'par_num', 'line_num', 'word_num', 'left', 'top', 'width', 'height'}

    for row in reader:
        if not row:
            continue
        for col, idx in col_idx.items():
            if idx < len(row):
                val = row[idx]
                if col in int_cols:
                    try:
                        result[col].append(int(val))
                    except ValueError:
                        result[col].append(0)
                elif col == 'conf':
                    try:
                        result[col].append(int(float(val)))
                    except ValueError:
                        result[col].append(-1)
                elif col == 'text':
                    result[col].append(val)
                else:
                    result.setdefault(col, []).append(val)
            else:
                if col in int_cols or col == 'conf':
                    result[col].append(0)
                else:
                    result.setdefault(col, []).append('')

    return result


def _run_tesseract(tesseract_cmd, image_path, lang="eng", psm=12, timeout=30):
    """Run Tesseract CLI on an image and return raw TSV output."""
    cmd = [
        tesseract_cmd,
        image_path,
        "stdout",
        "-l", str(lang),
        "--psm", str(psm),
        "tsv",
    ]
    # On Windows, suppress the console window
    startupinfo = None
    if platform.system() == "Windows":
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = 0

    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        startupinfo=startupinfo,
    )
    if proc.returncode != 0:
        err = proc.stderr.strip() if proc.stderr else f"Return code {proc.returncode}"
        raise RuntimeError(f"Tesseract failed: {err}")
    return proc.stdout


def perform_ocr(image_input, img_size=None, custom_merge_factor=None):
    """Run native Tesseract OCR on an image and return bounding boxes.

    Args:
        image_input: bytes (raw image bytes) or str/Path (image file path)
        img_size: optional tuple of (width, height). Inferred if not provided.
        custom_merge_factor: optional float overriding vertical_merge_factor.
    """
    config = {}
    if mw and hasattr(mw, "addonManager") and mw.addonManager:
        try:
            config = mw.addonManager.getConfig(__name__) or {}
        except Exception:
            config = {}

    tesseract_cmd = _get_tesseract_cmd(config)
    if not tesseract_cmd:
        system = platform.system()
        if system == "Darwin":
            hint = "Install via Homebrew: 'brew install tesseract' or MacPorts: 'sudo port install tesseract'."
        elif system == "Windows":
            hint = "Download Tesseract OCR installer from GitHub releases and install it, or configure 'tesseract_cmd'."
        else:
            hint = "Install via package manager: e.g. 'sudo apt install tesseract-ocr'."
        raise RuntimeError(
            f"Tesseract OCR binary was not found.\n{hint}\n"
            "If Tesseract is installed in a custom location, configure 'tesseract_cmd' in Tools > Add-ons > Config."
        )

    temp_path = None
    try:
        if isinstance(image_input, (bytes, bytearray)):
            if not img_size or img_size[0] <= 0 or img_size[1] <= 0:
                img_size = _get_image_dimensions(image_input)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(image_input)
                temp_path = tmp.name
            image_path = temp_path
        elif isinstance(image_input, str):
            image_path = image_input
            if not img_size or img_size[0] <= 0 or img_size[1] <= 0:
                with open(image_path, "rb") as f:
                    img_size = _get_image_dimensions(f.read())
        else:
            raise ValueError(f"Unsupported image input type: {type(image_input)}")

        lang = config.get("tesseract_lang", "eng")
        psm = config.get("psm", 12)

        tsv_text = _run_tesseract(tesseract_cmd, image_path, lang=lang, psm=psm)
        data = _parse_tsv_to_dict(tsv_text)

        lines = _parse_and_clean_lines(data, img_size, config)

        if custom_merge_factor is not None:
            effective_merge_factor = max(0.0, min(1.5, float(custom_merge_factor)))
            if mw and hasattr(mw, "addonManager") and mw.addonManager:
                try:
                    if round(config.get("vertical_merge_factor", 0.8), 2) != round(effective_merge_factor, 2):
                        config["vertical_merge_factor"] = round(effective_merge_factor, 2)
                        mw.addonManager.writeConfig(__name__, config)
                except Exception:
                    pass
        else:
            effective_merge_factor = max(0.0, min(1.5, float(config.get("vertical_merge_factor", 0.8))))

        regions = _merge_lines_syntax_aware(lines, effective_merge_factor, img_size, config)
        return regions

    except Exception as e:
        import traceback
        traceback.print_exc()
        raise RuntimeError(f"OCR detection error: {e}") from e

    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


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


def _clean_token_text(text):
    """Clean leader line dots, dashes, and bullet marks from OCR tokens."""
    t = text.strip()
    # Strip leading leader line artifacts: dots, dashes, underscores, commas, tildes
    t = re.sub(r'^[_\-.,~:;\'"|/\\`^+=*]+', '', t)
    # Strip trailing leader line artifacts
    t = re.sub(r'[_\-.,~:;\'"|/\\`^+=*]+$', '', t)
    # Fix case where leader line dot touched the first capital letter (e.g. 'vPostcentral' -> 'Postcentral')
    t = re.sub(r'^[a-z]([A-Z][a-z]{2,})', r'\1', t)
    return t


def _parse_and_clean_lines(data, img_size, config):
    """Group words into lines using line-level confidence anchoring,

    stripping leader-line bounding box inflation and diagram artifacts.
    """
    img_w, img_h = img_size
    raw_lines = {}

    for i in range(len(data['text'])):
        raw_t = data['text'][i].strip()
        conf = data['conf'][i]

        if not raw_t or conf < 0:
            continue

        letters = [c for c in raw_t if c.isalpha()]
        if not letters:
            continue

        cleaned_t = _clean_token_text(raw_t)
        if not cleaned_t:
            continue

        key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
        raw_lines.setdefault(key, []).append({
            'raw_text': raw_t,
            'text': cleaned_t,
            'conf': conf,
            'left': data['left'][i],
            'top': data['top'][i],
            'width': data['width'][i],
            'height': data['height'][i],
        })

    lines = []

    for key, words in raw_lines.items():
        if not words:
            continue

        max_conf = max(w['conf'] for w in words)
        total_letters = sum(sum(1 for c in w['text'] if c.isalpha()) for w in words)

        # Discard lines that are clearly diagram noise (e.g. creases, shading)
        if max_conf < 54 and total_letters < 5:
            continue

        words.sort(key=lambda w: w['left'])

        # Keep words that belong to the line:
        # High confidence anchor (>= 70) allows catching lower-contrast adjacent words (e.g. touched by dots)
        valid_words = []
        for w in words:
            w_letters = sum(1 for c in w['text'] if c.isalpha())
            if max_conf >= 70:
                if w['conf'] >= 15:
                    valid_words.append(w)
            else:
                if w['conf'] >= 50 and w_letters >= 3:
                    valid_words.append(w)

        if not valid_words:
            continue

        # Filter height outliers (e.g. leader line artifact tick 'y' with > 2.3x median height)
        if len(valid_words) > 1:
            heights = sorted(w['height'] for w in valid_words)
            med_h = heights[len(heights) // 2]
            size_filtered = []
            for w in valid_words:
                if w['height'] > med_h * 2.3 and len(w['text']) <= 2:
                    continue
                size_filtered.append(w)
            valid_words = size_filtered

        if not valid_words:
            continue

        # Filter horizontal outliers (stray marks far from the actual line text)
        if len(valid_words) > 1:
            clean_words = [valid_words[0]]
            avg_word_w = sum(w['width'] for w in valid_words) / len(valid_words)
            for k in range(1, len(valid_words)):
                gap = valid_words[k]['left'] - (valid_words[k - 1]['left'] + valid_words[k - 1]['width'])
                if gap > 4.0 * avg_word_w and len(valid_words[k]['text']) <= 2 and valid_words[k]['conf'] < 70:
                    continue
                clean_words.append(valid_words[k])
            valid_words = clean_words

        if not valid_words:
            continue

        # Reject standalone single-character lines unless it has very high confidence
        if len(valid_words) == 1 and len(valid_words[0]['text']) == 1:
            if valid_words[0]['conf'] < 85:
                continue

        l = min(w['left'] for w in valid_words)
        t = min(w['top'] for w in valid_words)
        r = max(w['left'] + w['width'] for w in valid_words)
        b = max(w['top'] + w['height'] for w in valid_words)

        line_text = ' '.join(w['text'] for w in valid_words)
        avg_conf = sum(w['conf'] for w in valid_words) / len(valid_words)

        lines.append({
            'text': line_text,
            'conf': avg_conf,
            'left': l,
            'top': t,
            'width': r - l,
            'height': b - t,
            'right': r,
            'bottom': b,
            'words': valid_words,
        })

    return lines


def _should_merge_lines(l1, l2, factor):
    """Determine whether l2 is a continuation of l1 (multi-line label).

    l1 is physically above l2.
    """
    if factor <= 0.0:
        return False

    t1 = l1['text'].strip()
    t2 = l2['text'].strip()

    if not t1 or not t2:
        return False

    avg_h = (l1['height'] + l2['height']) / 2.0
    gap = l2['top'] - l1['bottom']

    # Max vertical gap directly proportional to average line height
    max_gap = avg_h * factor
    if gap < -0.35 * avg_h or gap > max_gap:
        return False

    min_w = min(l1['width'], l2['width'])
    left_diff = abs(l1['left'] - l2['left'])
    right_diff = abs(l1['right'] - l2['right'])
    center1 = (l1['left'] + l1['right']) / 2.0
    center2 = (l2['left'] + l2['right']) / 2.0
    center_diff = abs(center1 - center2)

    overlap_l = max(l1['left'], l2['left'])
    overlap_r = min(l1['right'], l2['right'])
    overlap = max(0, overlap_r - overlap_l)

    # Must share alignment edge or have substantial horizontal overlap
    aligned = (
        left_diff <= max(24, 0.22 * min_w) or
        right_diff <= max(24, 0.22 * min_w) or
        center_diff <= max(24, 0.22 * min_w) or
        overlap >= 0.40 * min_w
    )
    if not aligned:
        return False

    # Universal Typographic Continuation Rules:
    first_char_l2 = None
    for ch in t2:
        if ch.isalpha():
            first_char_l2 = ch
            break

    # 1. Lowercase continuation: In standard typography, wrapped continuation lines begin with lowercase
    if first_char_l2 and first_char_l2.islower():
        return True

    # 2. Unclosed parenthesis / bracket (e.g. "communis (terminal" -> "tendons)")
    if t1.count('(') > t1.count(')') or t1.count('[') > t1.count(']'):
        return True

    # 3. Line 2 starts with closing punctuation or bracket
    if t2.startswith(')') or t2.startswith(']'):
        return True

    # 4. Hyphenation continuation (e.g. "Supra-" -> "marginal g.")
    raw_last = l1['words'][-1]['raw_text']
    if (raw_last.endswith('-') or raw_last.endswith('—') or t1.endswith('-')) and (first_char_l2 and first_char_l2.islower()):
        return True

    # Otherwise: Both lines are independent capitalized items or unrelated! DO NOT MERGE!
    return False


def _merge_lines_syntax_aware(lines, factor, img_size, config):
    """Merge multi-line labels using syntax-aware continuation analysis

    and disjoint-set grouping.
    """
    if not lines:
        return []

    img_w, img_h = img_size
    padding_px = config.get('box_padding', 4)

    n = len(lines)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    # Sort lines top-to-bottom
    sorted_indices = sorted(range(n), key=lambda i: lines[i]['top'])
    for idx_a in range(len(sorted_indices)):
        i = sorted_indices[idx_a]
        l1 = lines[i]
        for idx_b in range(idx_a + 1, len(sorted_indices)):
            j = sorted_indices[idx_b]
            l2 = lines[j]
            if l2['top'] - l1['bottom'] > 2.0 * max(l1['height'], l2['height']):
                break
            if _should_merge_lines(l1, l2, factor):
                union(i, j)

    groups = {}
    for i in range(n):
        root = find(i)
        groups.setdefault(root, []).append(lines[i])

    results = []
    for g in groups.values():
        top_y = min(l['top'] for l in g)
        bottom_y = max(l['bottom'] for l in g)
        left_x = min(l['left'] for l in g)
        right_x = max(l['right'] for l in g)
        box_w = right_x - left_x
        box_h = bottom_y - top_y

        # Symmetric padding
        pad_l = max(0, left_x - padding_px)
        pad_t = max(0, top_y - padding_px)
        pad_r = min(img_w, right_x + padding_px)
        pad_b = min(img_h, bottom_y + padding_px)

        results.append({
            'left': pad_l,
            'top': pad_t,
            'width': pad_r - pad_l,
            'height': pad_b - pad_t,
        })

    return results

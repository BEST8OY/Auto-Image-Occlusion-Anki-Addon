"""
OCR Engine Module
Handles all OCR processing using pytesseract with line-based detection
"""

from aqt import mw


def perform_ocr(image):
    """
    Perform OCR on an image using pytesseract.
    Uses PSM 11 (sparse text) with line-based grouping for reliable detection.
    
    Args:
        image: PIL Image object
        
    Returns:
        List of region dictionaries with keys: left, top, width, height
    """
    try:
        import pytesseract
        
        config = mw.addonManager.getConfig(__name__) or {}
        return perform_ocr_line_mode(image, config)
    
    except ImportError:
        return []
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return []


def perform_ocr_line_mode(image, config):
    """
    Line-based detection using sparse text mode (inspired by logseq-anki-sync).
    Uses PSM 11 (sparse text) with line-based grouping for reliable detection.
    Good for: All use cases - scattered text, dense documents, diagrams with labels
    """
    import pytesseract
    
    # Run Tesseract OCR in sparse text mode (detects text blocks)
    # PSM 11 = Sparse text. Find as much text as possible in no particular order
    data = pytesseract.image_to_data(
        image,
        output_type=pytesseract.Output.DICT,
        lang=config.get('tesseract_lang', 'eng'),
        config='--psm 11'  # Sparse text mode for line detection
    )
    
    # Get filter thresholds
    img_width, img_height = image.size
    min_area = img_width * img_height * config.get('min_area_percent', 0.0001)
    min_conf = config.get('min_confidence', 48)
    min_width = config.get('min_width', 4)
    min_height = config.get('min_height', 4)
    
    # Group by line (using line_num from OCR) - more reliable than par_num with PSM 11
    # PSM 11 (SPARSE_TEXT) doesn't always create meaningful paragraph boundaries
    # Line-based grouping gives us individual text lines, which we can then filter
    # This is closer to how tesseract.js actually behaves with sparse text
    lines = {}
    for i in range(len(data['text'])):
        # Create unique line identifier: block_num + par_num + line_num
        # This ensures we group by actual text lines
        line_key = (data['block_num'][i], data['par_num'][i], data['line_num'][i])
        text = data['text'][i].strip()
        conf = int(data['conf'][i])
        
        if not text or conf < 0:
            continue
        
        if line_key not in lines:
            lines[line_key] = {
                'texts': [],
                'confidences': [],
                'boxes': []
            }
        
        lines[line_key]['texts'].append(text)
        lines[line_key]['confidences'].append(conf)
        lines[line_key]['boxes'].append({
            'left': data['left'][i],
            'top': data['top'][i],
            'width': data['width'][i],
            'height': data['height'][i]
        })
    
    # Calculate average text length for filtering (like logseq-anki-sync)
    text_lengths = []
    for line in lines.values():
        combined_text = ' '.join(line['texts'])
        text_lengths.append(len(combined_text))
    
    avg_text_length = sum(text_lengths) / len(text_lengths) if text_lengths else 0
    # Use the same formula as logseq-anki-sync: min(avg / 2, 3)
    min_text_length = max(min(avg_text_length / 2, 3), 1)
    
    # Process lines into regions
    regions = []
    
    for line_key, line in lines.items():
        # Calculate line bounding box (encompassing all words in line)
        boxes = line['boxes']
        min_left = min(b['left'] for b in boxes)
        min_top = min(b['top'] for b in boxes)
        max_right = max(b['left'] + b['width'] for b in boxes)
        max_bottom = max(b['top'] + b['height'] for b in boxes)
        
        width = max_right - min_left
        height = max_bottom - min_top
        
        # Calculate average confidence for line
        avg_conf = sum(line['confidences']) / len(line['confidences'])
        combined_text = ' '.join(line['texts'])
        
        # Filter by confidence
        if avg_conf < min_conf:
            continue
        
        # Filter by text length (like logseq-anki-sync)
        # Ignore blocks with text shorter than the calculated minimum
        if len(combined_text.strip()) < min_text_length:
            continue
        
        # Filter by size
        if width < min_width or height < min_height:
            continue
        
        # Filter by area
        if width * height < min_area:
            continue
        
        regions.append({
            'left': min_left,
            'top': min_top,
            'width': width,
            'height': height
        })
    
    # Merge vertically adjacent lines (e.g., multi-line labels)
    # This handles cases like "Abductor pollicis\n       brevis muscle"
    regions = merge_vertically_close_regions(regions, config)
    
    return regions


def merge_vertically_close_regions(regions, config):
    """
    Merge regions that are vertically close to each other.
    Handles multi-line text labels that span multiple lines.
    
    Example: "Abductor pollicis"
             "       brevis muscle"
    Should become one region instead of two.
    """
    if not regions:
        return regions
    
    # Get merge threshold from config (default: 1.5x average height)
    vertical_merge_factor = config.get('vertical_merge_factor', 1.5)
    
    # Calculate average region height for relative threshold
    avg_height = sum(r['height'] for r in regions) / len(regions)
    vertical_threshold = avg_height * vertical_merge_factor
    
    # Build a graph of which regions should merge
    # Use union-find to handle transitive merging across multiple columns
    n = len(regions)
    parent = list(range(n))
    
    def find(x):
        if parent[x] != x:
            parent[x] = find(parent[x])
        return parent[x]
    
    def union(x, y):
        px, py = find(x), find(y)
        if px != py:
            parent[px] = py
    
    # Check all pairs for merge eligibility
    for i in range(n):
        for j in range(i + 1, n):
            r1, r2 = regions[i], regions[j]
            
            # Calculate vertical distance
            vertical_gap = r2['top'] - (r1['top'] + r1['height'])
            
            # Only consider if vertically close
            if vertical_gap < 0 or vertical_gap >= vertical_threshold:
                continue
            
            # Get horizontal spans
            r1_left = r1['left']
            r1_right = r1['left'] + r1['width']
            r2_left = r2['left']
            r2_right = r2['left'] + r2['width']
            
            # Calculate horizontal offset (left edge alignment)
            horizontal_offset = abs(r2_left - r1_left)
            
            # Calculate horizontal overlap
            overlap_left = max(r1_left, r2_left)
            overlap_right = min(r1_right, r2_right)
            overlap_width = max(0, overlap_right - overlap_left)
            
            max_width = max(r1['width'], r2['width'])
            min_width = min(r1['width'], r2['width'])
            
            # Merge if:
            # 1. They have significant horizontal overlap (>30%), OR
            # 2. They're closely aligned (left edges within 1x min_width)
            # This prevents merging regions in different columns
            has_overlap = overlap_width > min_width * 0.3
            is_aligned = horizontal_offset < min_width
            
            if has_overlap or is_aligned:
                union(i, j)
    
    # Group regions by their root parent
    groups = {}
    for i in range(n):
        root = find(i)
        if root not in groups:
            groups[root] = []
        groups[root].append(regions[i])
    
    # Merge each group into a single region
    merged = []
    for group in groups.values():
        if len(group) > 1:
            min_left = min(r['left'] for r in group)
            min_top = min(r['top'] for r in group)
            max_right = max(r['left'] + r['width'] for r in group)
            max_bottom = max(r['top'] + r['height'] for r in group)
            
            merged.append({
                'left': min_left,
                'top': min_top,
                'width': max_right - min_left,
                'height': max_bottom - min_top
            })
        else:
            merged.append(group[0])
    
    return merged

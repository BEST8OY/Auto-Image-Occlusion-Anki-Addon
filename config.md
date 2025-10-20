# Configuration

Access via: **Tools → Add-ons → [Auto Image Occlusion] → Config**

## OCR Settings

### tesseract_lang
- **Default:** `"eng"`
- Language for OCR. Use `+` for multiple: `"eng+fra"`
- Requires language pack installed (see README)

### min_confidence
- **Default:** `48`
- **Range:** 0-100
- Confidence threshold for OCR. Higher = fewer but more reliable detections.

---

## Size Filters

### min_area_percent
- **Default:** `0.0001` (0.01% of image)
- Minimum box area as percentage of image size
- Increase to filter out small text/noise

### min_width / min_height
- **Default:** `4` pixels each
- Minimum box dimensions in pixels

### vertical_merge_factor
- **Default:** `1.5`
- **Range:** 0 to 3+
- Merges text lines that are close vertically (within 1.5x average height)
- Handles multi-line labels like:
  ```
  Abductor pollicis
         brevis muscle
  ```
- Set to `0` to disable merging (each line separate)
- Increase to `2.5` for more aggressive merging

---

## UI Settings

### button_shortcut
- **Default:** `"Ctrl+Shift+A"`
- Keyboard shortcut to trigger auto-detection

---

## Quick Examples

**Default (works for most cases):**
```json
{
  "tesseract_lang": "eng",
  "min_confidence": 48,
  "vertical_merge_factor": 1.5
}
```

**For blurry/low-quality images (more detections):**
```json
{
  "min_confidence": 35,
  "min_area_percent": 0.00005
}
```

**For high-quality images (fewer false positives):**
```json
{
  "min_confidence": 60,
  "min_area_percent": 0.001
}
```

**For non-English text (Spanish):**
```json
{
  "tesseract_lang": "spa",
  "min_confidence": 48
}
```

**For mixed languages:**
```json
{
  "tesseract_lang": "eng+spa+fra",
  "min_confidence": 40
}
```

**For anatomy diagrams with multi-line labels:**
```json
{
  "vertical_merge_factor": 2.0
}
```

**Disable line merging (each line separate):**
```json
{
  "vertical_merge_factor": 0
}
```

---

## Technical Details

**Detection Method:**
- Uses PSM 12 (SPARSE_TEXT with OSD) - optimized for scattered text
- Line-based grouping for reliable granularity
- Vertical merging for multi-line labels (configurable)
- Each text block (single or multi-line) becomes a separate occlusion
- Collision detection prevents duplicates

**More Information:**
- Full documentation: See README.md
- Installation guide: See README.md (Installation section)
# Configuration

**Tools > Add-ons > Auto Image Occlusion > Config**

## Options

### tesseract_lang
- **Default:** `"eng"`
- Tesseract language code. Use `+` for multiple: `"eng+spa+fra"`
- Requires matching language pack installed (see README)

### tesseract_cmd
- **Default:** `""` (auto-detect)
- Full path to the tesseract binary. Only needed if Anki can't find it automatically.
- macOS Homebrew example: `"/opt/homebrew/bin/tesseract"`
- Windows example: `"C:\\Program Files\\Tesseract-OCR\\tesseract.exe"`

### min_confidence
- **Default:** `48`
- **Range:** 0-100
- OCR confidence threshold. Higher = fewer but more reliable detections.

### min_width / min_height
- **Default:** `4` pixels
- Minimum box dimensions. Filter out tiny noise.

### min_area_percent
- **Default:** `0.0001` (0.01% of image area)
- Minimum box area as fraction of total image size.

### vertical_merge_factor
- **Default:** `0.8`
- **Range:** `0.0` to `1.5` (Recommended: `0.6` to `1.0`)
- Maximum vertical gap allowed between lines of the same label, expressed as a multiple of line height (`gap <= factor * line_height`).
- Multi-line labels are intelligently unified using universal typography continuation rules (lowercase continuation, unclosed parentheses, and hyphens).
- Set to `0` to disable multi-line merging entirely (each line becomes an individual occlusion).

### box_padding
- **Default:** `4` pixels
- Symmetric padding in pixels around detected text boxes to prevent glyph clipping.

### button_shortcut
- **Default:** `"Ctrl+Shift+X"`
- Keyboard shortcut to trigger auto-detection
- Format: modifier keys separated by `+` then the key (e.g. `"Ctrl+Shift+A"`, `"Cmd+Alt+D"`)
- Supported modifiers: `Ctrl`, `Shift`, `Alt`, `Meta`/`Cmd`

## Examples

**Default (most cases):**
```json
{ "tesseract_lang": "eng", "min_confidence": 48, "vertical_merge_factor": 0.8, "button_shortcut": "Ctrl+Shift+X" }
```

**Low-quality images (more detections):**
```json
{ "min_confidence": 35, "min_area_percent": 0.00005 }
```

**High-quality images (fewer false positives):**
```json
{ "min_confidence": 60, "min_area_percent": 0.001 }
```

**Non-English (Spanish):**
```json
{ "tesseract_lang": "spa" }
```

**Loose line spacing (diagrams with wider gaps):**
```json
{ "vertical_merge_factor": 1.2 }
```

**No merging (each line separate):**
```json
{ "vertical_merge_factor": 0 }
```

**Custom shortcut (macOS Cmd):**
```json
{ "button_shortcut": "Cmd+Alt+D" }
```

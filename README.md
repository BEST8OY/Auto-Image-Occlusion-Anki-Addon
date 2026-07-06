# Auto Image Occlusion - Anki Addon

Automatically detect text regions in images and create Image Occlusion shapes with one click. Works with Anki's native Image Occlusion editor (25.09+).

![Anki Version](https://img.shields.io/badge/anki-25.09+-green)
![License](https://img.shields.io/badge/license-AGPL--3.0-orange)

**Inspired by** [logseq-anki-sync](https://github.com/debanjandhar12/logseq-anki-sync)

## Features

- One-click text detection via magic wand button in the IO toolbar
- Keyboard shortcut: `Ctrl+Shift+X`
- Skips existing occlusions (collision detection)
- Merges multi-line labels (configurable)
- Works with 100+ Tesseract languages
- Auto-installs pytesseract and Pillow on first run

## Installation

### Prerequisites: Tesseract OCR

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:** Download from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki), add `C:\Program Files\Tesseract-OCR` to PATH.

**Additional languages:** Install via package manager (e.g. `sudo apt-get install tesseract-ocr-spa`) or download `.traineddata` files from [tessdata](https://github.com/tesseract-ocr/tessdata) into Tesseract's tessdata directory.

### Install Addon

**AnkiWeb:** Tools > Add-ons > Get Add-ons > code `1414192727`

**Manual:** Copy this folder to your Anki addons directory:
- Windows: `%APPDATA%\Anki2\addons21\`
- macOS: `~/Library/Application Support/Anki2/addons21/`
- Linux: `~/.local/share/Anki2/addons21/`

Restart Anki. Dependencies (pytesseract, Pillow) install automatically on first launch.

## Usage

1. Open **Add** cards, select Image Occlusion note type
2. Load your image
3. Click the magic wand button or press `Ctrl+Shift+X`
4. Wait 2-10 seconds for OCR processing
5. Adjust the generated occlusion boxes as needed
6. Click **Add** to create your cards

## Configuration

**Tools > Add-ons > Auto Image Occlusion > Config**

```json
{
    "tesseract_lang": "eng",
    "min_confidence": 48,
    "min_width": 4,
    "min_height": 4,
    "min_area_percent": 0.0001,
    "vertical_merge_factor": 0.65,
    "button_shortcut": "Ctrl+Shift+X"
}
```

| Option | Default | Description |
|--------|---------|-------------|
| `tesseract_lang` | `"eng"` | Language code. Use `"eng+fra"` for multiple |
| `tesseract_cmd` | `""` | Path to tesseract binary. Auto-detects if empty |
| `min_confidence` | `48` | OCR confidence threshold (0-100). Lower = more detections |
| `min_width` | `4` | Minimum box width in pixels |
| `min_height` | `4` | Minimum box height in pixels |
| `min_area_percent` | `0.0001` | Minimum box area as fraction of image |
| `vertical_merge_factor` | `0.65` | Merge lines within this factor of avg height. `0` to disable |
| `button_shortcut` | `"Ctrl+Shift+X"` | Keyboard shortcut (modifiers + key) |

See [config.md](config.md) for detailed examples.

## How It Works

1. User clicks button, JS captures the image as base64
2. Image sent to Python via `pycmd()`
3. Tesseract runs PSM 12 (sparse text detection)
4. Words are grouped by line, filtered by confidence/size/text-length
5. Vertically close lines are merged (e.g. multi-line labels)
6. Collision check against existing canvas shapes
7. Results sent back to JS, which creates `Rectangle` shapes on the canvas

## Troubleshooting

**"TesseractNotFoundError":** Tesseract isn't installed or not on PATH. Run `tesseract --version` to verify. On macOS with Homebrew, set `tesseract_cmd` in config (e.g. `"/opt/homebrew/bin/tesseract"`).

**"No text detected":** Lower `min_confidence` (try 35) and `min_area_percent` (try 0.00005). Ensure image has clear, readable text.

**"OCR timeout":** Image too large. Reduce to ~1920px width.

**Poor accuracy:** Adjust `min_confidence` up (fewer false positives) or down (catch more text).

## Architecture

```
__init__.py             # Entry point, dependency setup
addon.py                # Hook registration
editor_integration.py   # JS injection via editor_mask_editor_did_load_image hook
js_builder.py           # Generates injected JavaScript (button, OCR flow, canvas interaction)
message_handler.py      # pycmd() message routing (JS <-> Python)
ocr_engine.py           # Tesseract wrapper (PSM 12, line grouping, merging)
dependency_manager.py   # Auto-installs pytesseract + Pillow into libs/
```

## Credits

- [logseq-anki-sync](https://github.com/debanjandhar12/logseq-anki-sync) - Original auto-detection concept
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Text detection engine
- [pytesseract](https://github.com/madmaze/pytesseract) - Python wrapper
- [Pillow](https://python-pillow.org/) - Image processing
- Magic wand icon: [Material Design Icons](https://materialdesignicons.com/) (mdiAutoFix)

## License

GNU AGPL v3+ (same as Anki)

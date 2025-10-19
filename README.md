# Auto Image Occlusion - Anki Addon

> Automatically detect and occlude text regions in images using Tesseract OCR

![Anki Version](https://img.shields.io/badge/anki-25.09+-green)
![Python](https://img.shields.io/badge/python-3.9+-blue)
![License](https://img.shields.io/badge/license-AGPL--3.0-orange)

Automatically detect text regions in images and create Image Occlusion shapes with a single click. Works seamlessly with Anki's native Image Occlusion feature (Anki 25.09+).

**Inspired by**: [logseq-anki-sync](https://github.com/debanjandhar12/logseq-anki-sync)

---

## ✨ Features

- 🪄 **One-Click Detection**: Auto-detect text regions with a single button click
- 🎨 **Native Integration**: Seamlessly integrates with Anki's Image Occlusion toolbar
- ⌨️ **Keyboard Shortcut**: Quick access via `Ctrl+Shift+A`
- 🧠 **Smart Detection**: Line-based detection with PSM 11 (sparse text)
- 🎯 **Collision Detection**: Automatically skips existing occlusions
- 📏 **Text Length Filtering**: Intelligently filters based on average line length
- 🔧 **Configurable**: Adjust confidence, size thresholds, and filters
- 🚀 **Persistent UI**: Button automatically reappears when selecting new images
- 🐍 **Python Backend**: Uses pytesseract for reliable, fast OCR processing

---

## 📦 Installation

### Prerequisites

#### 1. Anki 25.09 or Later
Ensure you have Anki 25.09+ which includes native Image Occlusion support.

#### 2. Tesseract OCR
Install Tesseract OCR on your system:

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**macOS:**
```bash
brew install tesseract
```

**Windows:**
1. Download installer from [GitHub releases](https://github.com/UB-Mannheim/tesseract/wiki)
2. Run installer and note the installation path
3. Add to PATH: `C:\Program Files\Tesseract-OCR`

#### 2.1. Additional Language Data (Optional)

Tesseract supports 100+ languages. To use non-English languages, you need to download additional language data files.

**Download Language Data:**
- Visit [tessdata repository](https://github.com/tesseract-ocr/tessdata)
- Download `.traineddata` files for your language(s)
- Common examples: `spa.traineddata` (Spanish), `fra.traineddata` (French), `deu.traineddata` (German), `chi_sim.traineddata` (Chinese Simplified)

**Install Language Data:**

**Windows:**
```
Copy .traineddata files to: C:\Program Files\Tesseract-OCR\tessdata\
```

**Linux (Package Install):**
```bash
# Option 1: Install via package manager
sudo apt-get install tesseract-ocr-spa  # Spanish
sudo apt-get install tesseract-ocr-fra  # French

# Option 2: Manual install
sudo cp *.traineddata /usr/share/tesseract-ocr/tessdata/
# or: /usr/share/tessdata/
```

**macOS (Homebrew):**
```bash
# Option 1: Install via brew
brew install tesseract-lang  # All languages

# Option 2: Manual install
cp *.traineddata /usr/local/share/tessdata/
# or: /opt/homebrew/share/tessdata/ (Apple Silicon)
```

**Verify Installation:**
```bash
tesseract --list-langs
```

**Example Config for Spanish:**
```json
{
    "tesseract_lang": "spa"
}
```

**Example Config for Multiple Languages:**
```json
{
    "tesseract_lang": "eng+spa+fra"
}
```

#### 3. Python Packages (**MOST IMPORTANT PART**)
You have to install pytesseract and pillow in Anki installation environment

### Install Addon

**Method 1: AnkiWeb (Recommended)**
1. Go to **Tools → Add-ons**
2. Click **Get Add-ons...**
3. Enter code: `[CODE WILL BE ADDED AFTER ANKIWEB SUBMISSION]`
4. Restart Anki

**Method 2: Manual Installation**
1. Download or clone this repository
2. Copy the entire folder to your Anki addons directory:
   - **Windows**: `%APPDATA%\Anki2\addons21\auto_image_occlusion`
   - **macOS**: `~/Library/Application Support/Anki2/addons21/auto_image_occlusion`
   - **Linux**: `~/.local/share/Anki2/addons21/auto_image_occlusion`
3. Restart Anki

---

## 🚀 Quick Start

1. **Open Add Cards**: In Anki, click **Add** or press `A`
2. **Select Image Occlusion**: Choose the Image Occlusion note type
3. **Load Your Image**: Click the image icon and select your image
4. **Auto-Detect**: Click the magic wand button (🪄) or press `Ctrl+Shift+A`
5. **Wait**: OCR processing takes 2-10 seconds depending on image size
6. **Review**: Automatically created occlusion boxes appear on text regions
7. **Adjust**: Move, resize, or delete boxes as needed
8. **Add**: Click "Add" to create your cards

### Visual Guide

```
┌─────────────────────────────────────┐
│  Image Occlusion Toolbar            │
│  [Rect] [Ellipse] [...] [🪄]        │  ← Magic wand button
└─────────────────────────────────────┘
            ↓ Click or Ctrl+Shift+A
┌─────────────────────────────────────┐
│  Your image with auto-detected      │
│  ┌──────┐  ┌─────┐  ┌─────────┐    │
│  │Text 1│  │Text2│  │  Text 3 │    │
│  └──────┘  └─────┘  └─────────┘    │
│                                     │
└─────────────────────────────────────┘
```

---

## ⚙️ Configuration

### Access Config
**Tools → Add-ons → Auto Image Occlusion Detection → Config**

### Default Configuration
```json
{
    "tesseract_lang": "eng",
    "min_confidence": 48,
    "min_width": 4,
    "min_height": 4,
    "min_area_percent": 0.0001,
    "button_shortcut": "Ctrl+Shift+A",
    "vertical_merge_factor": 0.65
}
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `tesseract_lang` | `"eng"` | OCR language code(s). Use `"eng+fra"` for multiple languages |
| `min_confidence` | `48` | Minimum OCR confidence (0-100). Lower = more detections |
| `min_width` | `4` | Minimum box width in pixels |
| `min_height` | `4` | Minimum box height in pixels |
| `min_area_percent` | `0.0001` | Minimum box area as % of image (0.01 = 1%) |
| `button_shortcut` | `"Ctrl+Shift+A"` | Keyboard shortcut for auto-detection |
| `vertical_merge_factor` | `0.65` | Merge lines within 1.5x average height (handles multi-line labels) |

### Configuration Examples

**For Higher Quality (fewer false positives):**
```json
{
    "min_confidence": 60,
    "min_area_percent": 0.001
}
```

**For More Detections (catch more text):**
```json
{
    "min_confidence": 35,
    "min_area_percent": 0.00005
}
```

**For Non-English Text (e.g., Spanish):**
```json
{
    "tesseract_lang": "spa",
    "min_confidence": 48
}
```

**For Mixed Languages (e.g., English + Chinese):**
```json
{
    "tesseract_lang": "eng+chi_sim",
    "min_confidence": 40
}
```

**Disable multi-line merging (treat each line separately):**
```json
{
    "vertical_merge_factor": 0
}
```

**More aggressive multi-line merging:**
```json
{
    "vertical_merge_factor": 2.5
}
```

---

## 🧠 How It Works

Uses Tesseract's PSM 11 (sparse text) with line-based grouping for reliable detection.

**Best for:**
- ✅ Scattered text elements (diagrams, labels)
- ✅ Dense text documents
- ✅ Books and articles
- ✅ Mixed layouts with varied text positioning
- ✅ Anatomy diagrams
- ✅ Flowcharts and infographics

**Detection Process:**
1. Detects text using sparse text detection (PSM 11)
2. Groups words by text line for granular detection
3. Merges vertically adjacent lines
4. Calculates average text length for intelligent filtering
5. Filters by confidence threshold (min 48)
6. Filters by text length (ignores lines shorter than avg/2 or 3 chars)
7. Detects collisions with existing occlusions (backend & frontend)
8. Creates individual occlusions per text block

**Technical Details:**
- Uses PSM 11 (sparse text) - optimized for finding scattered text
- Line-based grouping provides reliable granularity
- Vertical merging handles multi-line labels (e.g., anatomy diagrams)
- Each text block (single or multi-line) becomes a separate occlusion
- Collision detection prevents duplicate occlusions

---

## 🏗️ Architecture

### Module Structure

```
anki addon/
├── __init__.py                 # Package initialization
├── addon.py                    # Main entry point, registers hooks
├── editor_integration.py       # JavaScript injection logic
├── js_builder.py               # JavaScript code generator
├── message_handler.py          # Python ↔ JavaScript communication
├── ocr_engine.py               # Tesseract OCR wrapper (PSM 11, line-based)
├── config.json                 # Default configuration
├── config.md                   # Configuration documentation
├── manifest.json               # Addon metadata
└── README.md                   # This file
```

### Data Flow

```
1. User opens IO note
   ↓
2. editor_did_load_note hook fires
   ↓
3. Python injects JavaScript (100ms delay)
   ↓
4. JavaScript initializes:
   - Create window.AutoIOAddon namespace
   - Intercept resetIOImageLoaded()
   - Wait for IO editor (MutationObserver)
   - Add button to toolbar
   ↓
5. User clicks button or presses Ctrl+Shift+A
   ↓
6. JavaScript:
   - Capture image element
   - Convert to base64 DataURL
   - Send via pycmd('autoDetectOCR:...')
   ↓
7. Python:
   - Decode image
   - Run Tesseract OCR (PSM 11 - sparse text)
   - Group text by lines
   - Calculate average text length
   - Filter by confidence, size, and text length
   - Detect collisions with existing shapes
   - Return non-colliding JSON results
   ↓
8. JavaScript:
   - Transform coordinates (image → canvas)
   - Double-check overlapping regions (safety measure)
   - Create Rectangle shapes
   - Add to maskEditor
   - Redraw canvas
```

---

## 🔧 Troubleshooting

### "Auto-detection failed: OCR timeout"

**Symptoms:** Error message after clicking button

**Solutions:**
1. ✅ Image is too large (reduce to ~1920px width)
2. ✅ System is slow (increase timeout in JavaScript config)
3. ✅ Tesseract not installed properly
4. ✅ Check Anki debug console for Python errors

### Tesseract Not Found

**Symptoms:** `pytesseract.TesseractNotFoundError`

**Solutions:**
1. **Verify Installation:**
   ```bash
   tesseract --version
   ```
2. **Add to PATH** (Windows):
   - System Properties → Environment Variables
   - Add `C:\Program Files\Tesseract-OCR` to PATH
   - Restart Anki
3. **Reinstall Tesseract** and verify during installation

### No Text Detected

**Symptoms:** "No text regions detected" message

**Solutions:**
1. ✅ Lower `min_confidence` (try 30-40)
2. ✅ Lower `min_area_percent` (try 0.00005)
3. ✅ Ensure image has clear, readable text
4. ✅ Check if correct language is set (`tesseract_lang`)
5. ✅ Improve image quality/contrast

### Poor Detection Accuracy

**Symptoms:** Too many false positives or missing text

**Solutions:**

**Too many false positives:**
- Increase `min_confidence` (try 55-65)
- Increase `min_area_percent` (try 0.001)

**Missing text:**
- Decrease `min_confidence` (try 35-40)
- Decrease `min_area_percent` (try 0.00001)
- Improve image quality/contrast

---

## 📊 Performance

### Typical Processing Times

| Image Size | OCR Time | Regions Detected |
|------------|----------|------------------|
| 800×600 | 2-3s | 10-20 |
| 1200×800 | 3-5s | 20-40 |
| 1920×1080 | 5-8s | 30-60 |
| 4K (3840×2160) | 15-20s | 100+ |

### Optimization Tips

1. **Resize Images:** Keep images under 1920px width for best performance
2. **Increase Confidence:** Filters out noise, faster processing
3. **Crop Images:** Remove unnecessary whitespace before importing
4. **Improve Contrast:** Better contrast = faster, more accurate OCR

---

## 🤝 Contributing

Contributions are welcome! To contribute:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Test thoroughly in Anki
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## 🙏 Credits

### Inspiration
- [logseq-anki-sync](https://github.com/debanjandhar12/logseq-anki-sync) - Original auto-detection concept

### Dependencies
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) - Text detection engine
- [pytesseract](https://github.com/madmaze/pytesseract) - Python wrapper for Tesseract
- [Pillow](https://python-pillow.org/) - Image processing library

### Icons
- Magic wand icon from [Material Design Icons](https://materialdesignicons.com/) (mdiAutoFix)

## 📄 License

GNU AGPL v3+ - Same as Anki's license

This addon is free and open-source. See Anki's license for full details.

---

**Made with ❤️ for the Anki community**

# Repository Guidelines: Auto-Occlusion Anki Addon

## 1. Zero-Dependency Architecture Invariants
- **No External Binary Python Dependencies**: Do not reintroduce `Pillow`, `pytesseract`, `cv2`, or dynamic wheel downloaders (`dependency_manager.py`).
- **Use Anki Bundled Qt / Standard Library**:
  - Read image dimensions and decode image formats using Anki's bundled `PyQt6.QtGui.QImage` (or `PyQt5`) or standard library `struct` binary header parsing.
  - Invoke OCR via standard `subprocess` calls directly to the system `tesseract` executable with TSV output.
- **Zero-Overhead Startup**: `__init__.py` must remain lightweight (instant import, no network requests or background worker threads during initialization).

## 2. Tesseract TSV Parsing Rules
- **Mandatory `quoting=csv.QUOTE_NONE`**:
  When parsing Tesseract TSV stdout via Python's `csv.reader`, **always** pass `quoting=csv.QUOTE_NONE`:
  ```python
  csv.reader(tsv_text.strip().splitlines(), delimiter='\t', quoting=csv.QUOTE_NONE)
  ```
  *Rationale*: Tesseract OCR text from noisy diagrams often emits unescaped double quotes (e.g. `"y`). Default quote handling treats this as a multiline quoted field, silently swallowing all subsequent OCR rows.

## 3. Packaging & Installation
- **`.ankiaddon` Format**: Standard ZIP containing addon source files directly at the archive root (e.g., `manifest.json`, `__init__.py`). Exclude `.git`, `__pycache__`, `libs/`, and existing `.ankiaddon` files.
- **Local Anki Addon Directory**: When testing or updating installed addons, ensure files are synced directly to `~/.local/share/Anki2/addons21/<addon_id>/`.

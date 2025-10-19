"""
Auto Image Occlusion Addon for Anki
====================================

Adds automatic text detection to Anki's native Image Occlusion feature.
Uses pytesseract OCR to detect text regions and automatically creates occlusion shapes.

Features:
- 🤖 Button in Image Occlusion editor toolbar
- Automatic text detection using Tesseract OCR
- Configurable confidence thresholds and filters
- Handles image scaling and coordinate normalization
- Filters overlapping regions
- Keyboard shortcut: Ctrl+Shift+A

Architecture:
- Python backend: Runs OCR using pytesseract
- JavaScript frontend: Injects button and handles UI
- Communication: pycmd() for Python ↔ JavaScript messaging
- Coordinate system: Normalized (0-1 range) relative to bounding box

Author: Inspired by logseq-anki-sync
License: GNU AGPL v3+
"""

from aqt import gui_hooks

from .editor_integration import on_editor_load_note
from .message_handler import handle_messages


def init():
    """Initialize the addon by registering hooks"""
    gui_hooks.editor_did_load_note.append(on_editor_load_note)
    gui_hooks.webview_did_receive_js_message.append(handle_messages)

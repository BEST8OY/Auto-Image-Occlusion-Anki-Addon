# Auto Image Occlusion Anki Addon
# Adds automatic occlusion detection to Anki's native image occlusion editor

import sys
import os

# Ensure dependencies are available (download on first startup if needed)
from .dependency_manager import ensure_dependencies

if not ensure_dependencies():
    # Defer error dialog until Anki's main window is ready
    # At import time, aqt.mw is not yet initialized
    def _show_dep_error():
        try:
            from aqt import mw
            import aqt.utils
            if mw:
                aqt.utils.showCritical(
                    "Auto Image Occlusion Error",
                    "Failed to install required dependencies.<br>"
                    "Please check your internet connection and restart Anki."
                )
            else:
                print("[Auto Image Occlusion] Failed to install dependencies")
        except Exception:
            print("[Auto Image Occlusion] Failed to install dependencies")

    # Use QTimer to defer until the event loop is running
    try:
        from aqt.qt import QTimer
        QTimer.singleShot(0, _show_dep_error)
    except Exception:
        print("[Auto Image Occlusion] Failed to install dependencies")

from . import addon

# Initialize the addon
addon.init()

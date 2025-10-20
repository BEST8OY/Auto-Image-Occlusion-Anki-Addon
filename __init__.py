# Auto Image Occlusion Anki Addon
# Adds automatic occlusion detection to Anki's native image occlusion editor

import sys
import os

# Ensure dependencies are available (download on first startup if needed)
from .dependency_manager import ensure_dependencies

if not ensure_dependencies():
    # Show error dialog if dependencies failed to install
    try:
        from aqt import mw
        import aqt.utils
        
        def show_error():
            aqt.utils.showCritical(
                "Auto Image Occlusion Error",
                "Failed to install required dependencies.<br>"
                "Please check your internet connection and restart Anki."
            )
        
        mw.taskTimer.singleShot(2000, show_error)
    except Exception as e:
        print(f"[Auto Image Occlusion] Failed to initialize addon: {e}")

from . import addon

# Initialize the addon
addon.init()

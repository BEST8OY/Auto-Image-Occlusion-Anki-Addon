# Auto Image Occlusion Anki Addon
# Adds automatic occlusion detection to Anki's native image occlusion editor

import sys
import os

# Add bundled libs to Python path
libs_path = os.path.join(os.path.dirname(__file__), "libs")
if libs_path not in sys.path:
    sys.path.insert(0, libs_path)

from . import addon

# Initialize the addon
addon.init()

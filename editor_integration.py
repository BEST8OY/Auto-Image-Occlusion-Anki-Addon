"""
Editor Integration Module

Handles injection of JavaScript into Anki's Image Occlusion editor.

Architecture:
- Hook: gui_hooks.editor_did_load_note
- Timing: 100ms delay via QTimer for editor readiness
- Caching: JavaScript built once and reused
- Error handling: Exceptions logged to console

The JavaScript is injected every time an IO note is loaded, but the JS code
itself is idempotent and handles re-injection gracefully.
"""

from aqt import mw
from aqt.editor import Editor
from aqt.qt import QTimer

from .js_builder import build_injection_javascript

# Global cache for compiled JavaScript code
# Cleared when addon reloads; config changes require addon reload
_cached_js_code = None


def on_editor_load_note(editor: Editor) -> None:
    """
    Hook handler: Called when a note is loaded in the editor.
    
    Injects JavaScript to add auto-detect button if it's an Image Occlusion note.
    
    Args:
        editor: Anki Editor instance
        
    Flow:
        1. Check if note is Image Occlusion type
        2. Build/fetch JavaScript code (cached after first build)
        3. Delay 100ms for editor readiness
        4. Inject JavaScript via editor.web.eval()
    """
    global _cached_js_code
    
    # Only inject for Image Occlusion notes
    if not editor.note:
        return
    
    if not editor.current_notetype_is_image_occlusion():
        return
    
    # Build JavaScript once and cache it (config rarely changes)
    if _cached_js_code is None:
        config = mw.addonManager.getConfig(__name__) or {}
        _cached_js_code = build_injection_javascript(config)
    
    # Delay injection slightly to ensure editor is fully loaded
    def inject_delayed():
        try:
            editor.web.eval(_cached_js_code)
        except Exception as e:
            # Log errors for debugging (visible in Anki's debug console)
            # Not a fatal error - user can still use Anki normally
            print(f"[Auto-IO Addon] Failed to inject JavaScript: {e}")
            import traceback
            traceback.print_exc()
    
    # Use QTimer for delayed execution
    # 100ms is usually sufficient; slower systems may need more time
    QTimer.singleShot(100, inject_delayed)


def clear_cache() -> None:
    """
    Clear the JavaScript cache.
    
    Call this if config changes and you want to rebuild the JavaScript.
    Useful for development/testing.
    """
    global _cached_js_code
    _cached_js_code = None

"""
Editor Integration Module

Handles injection of JavaScript into Anki's Image Occlusion editor.

Architecture:
- Hook: gui_hooks.editor_mask_editor_did_load_image (precise timing)
- Timing: 50ms delay after image loads (Svelte components need hydration)
- Caching: JavaScript built once and reused
- Error handling: Exceptions logged to console

The JavaScript is injected every time an IO image loads, but the JS code
itself is idempotent and handles re-injection gracefully.
"""

from aqt import mw
from aqt.editor import Editor
from aqt.qt import QTimer

from .js_builder import build_injection_javascript

# Global cache for compiled JavaScript code
# Cleared when addon reloads; config changes require addon reload
_cached_js_code = None


def on_mask_editor_image_loaded(editor: Editor, path_or_nid) -> None:
    """
    Hook handler: Called when the IO mask editor finishes loading an image.

    This is more precise than editor_did_load_note because it fires exactly
    when the IO editor is ready (canvas and maskEditor are available).

    Args:
        editor: Anki Editor instance
        path_or_nid: Image path (str) for new notes, or NoteId for existing notes

    Flow:
        1. Build/fetch JavaScript code (cached after first build)
        2. Short delay for Svelte component hydration
        3. Inject JavaScript via editor.web.eval()
    """
    global _cached_js_code

    # Build JavaScript once and cache it (config rarely changes)
    if _cached_js_code is None:
        config = mw.addonManager.getConfig(__name__) or {}
        _cached_js_code = build_injection_javascript(config)

    # Short delay for Svelte components to hydrate after image loads
    # The hook fires when image.onload completes, but toolbar/canvas need
    # a moment to mount. 50ms is sufficient vs the old 200ms guesswork.
    def inject_delayed():
        try:
            editor.web.eval(_cached_js_code)
        except Exception as e:
            # Log errors for debugging (visible in Anki's debug console)
            # Not a fatal error - user can still use Anki normally
            print(f"[Auto-IO Addon] Failed to inject JavaScript: {e}")
            import traceback
            traceback.print_exc()

    QTimer.singleShot(50, inject_delayed)


def clear_cache() -> None:
    """
    Clear the JavaScript cache.

    Call this if config changes and you want to rebuild the JavaScript.
    Useful for development/testing.
    """
    global _cached_js_code
    _cached_js_code = None

"""
Message Handler Module
Handles communication between JavaScript and Python via pycmd()
"""

import base64
import io
import json
from aqt.utils import tooltip

from .ocr_engine import perform_ocr

PREFIX_OCR = "autoDetectOCR:"
PREFIX_DONE = "autoDetect:"


def _rects_collide(a, b):
    """Check if two rectangles intersect."""
    return not (
        a['top'] + a['height'] < b['top'] or
        a['top'] > b['top'] + b['height'] or
        a['left'] + a['width'] < b['left'] or
        a['left'] > b['left'] + b['width']
    )


def _send_to_js(context, payload):
    """Send a JSON payload back to JavaScript via the callback."""
    data = json.dumps(payload)
    if hasattr(context, 'web'):
        context.web.eval(f'window.autoIOCallback && window.autoIOCallback({data})')


def filter_colliding_regions(regions, existing_shapes, img_width, img_height):
    """Filter out regions that collide with existing shapes."""
    existing = [
        {
            'left': s['left'] * img_width,
            'top': s['top'] * img_height,
            'width': s['width'] * img_width,
            'height': s['height'] * img_height,
        }
        for s in existing_shapes
    ]

    return [
        r for r in regions
        if not any(_rects_collide(r, e) for e in existing)
    ]


def handle_messages(handled, message, context):
    """Hook: Handle messages from JavaScript via pycmd()."""
    if not isinstance(message, str):
        return handled

    if message.startswith(PREFIX_OCR):
        _process_ocr(message, context)
        return (True, None)

    if message.startswith(PREFIX_DONE):
        _show_completion(message)
        return (True, None)

    return handled


def _process_ocr(message, context):
    """Decode image, run OCR, filter collisions, send results back."""
    try:
        data = json.loads(message[len(PREFIX_OCR):])
        image_data = data.get('imageData', '')
        existing = data.get('existingShapes', [])
        img_w = data.get('imageWidth', 0)
        img_h = data.get('imageHeight', 0)

        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]

        from PIL import Image
        image = Image.open(io.BytesIO(base64.b64decode(image_data)))

        regions = perform_ocr(image)

        if existing and img_w > 0 and img_h > 0:
            regions = filter_colliding_regions(regions, existing, img_w, img_h)

        _send_to_js(context, {'regions': regions})

    except Exception:
        import traceback
        traceback.print_exc()
        _send_to_js(context, {'error': traceback.format_exc()})


def _show_completion(message):
    """Show tooltip when detection completes."""
    try:
        data = json.loads(message[len(PREFIX_DONE):])
        if data.get("status") == "complete":
            count = data.get("count", 0)
            tooltip(f"Added {count} auto-detected occlusions" if count else "No new regions detected")
    except Exception:
        pass

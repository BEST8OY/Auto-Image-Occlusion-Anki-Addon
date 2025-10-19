"""
Message Handler Module
Handles communication between JavaScript and Python via pycmd()
"""

import base64
import io
import json
from PIL import Image
from aqt.utils import tooltip

from .ocr_engine import perform_ocr


def filter_colliding_regions(regions, existing_shapes, img_width, img_height):
    """
    Filter out regions that collide with existing shapes (like logseq-anki-sync).
    
    Args:
        regions: List of detected OCR regions in image coordinates
        existing_shapes: List of existing shapes from canvas (normalized 0-1 coords)
        img_width: Image width in pixels
        img_height: Image height in pixels
        
    Returns:
        List of non-colliding regions
    """
    def do_rects_collide(a, b):
        """Check if two rectangles intersect (like logseq-anki-sync)"""
        return not (
            a['top'] + a['height'] < b['top'] or
            a['top'] > b['top'] + b['height'] or
            a['left'] + a['width'] < b['left'] or
            a['left'] > b['left'] + b['width']
        )
    
    # Convert existing shapes from normalized (0-1) to image coordinates
    existing_in_image_coords = []
    for shape in existing_shapes:
        existing_in_image_coords.append({
            'left': shape['left'] * img_width,
            'top': shape['top'] * img_height,
            'width': shape['width'] * img_width,
            'height': shape['height'] * img_height
        })
    
    # Filter out colliding regions
    filtered = []
    for region in regions:
        intersects = False
        for existing in existing_in_image_coords:
            if do_rects_collide(region, existing):
                intersects = True
                break
        
        if not intersects:
            filtered.append(region)
    
    return filtered


def handle_messages(handled, message, context):
    """
    Hook: Handle messages from JavaScript via pycmd().
    Processes OCR requests and completion notifications.
    
    Args:
        handled: Previous handler's return value
        message: Message string from JavaScript
        context: Editor context object
        
    Returns:
        Tuple (handled, result)
    """
    if not isinstance(message, str):
        return handled
    
    # Handle OCR request
    if message.startswith('autoDetectOCR:'):
        process_ocr_request(message, context)
        return (True, None)
    
    # Handle completion notification
    if message.startswith('autoDetect:'):
        show_completion_message(message)
        return (True, None)
    
    return handled


def process_ocr_request(message, context):
    """
    Process OCR request from JavaScript.
    Decodes image, runs OCR, filters out collisions, and sends results back.
    """
    try:
        # Parse request (now includes existing shapes for collision detection)
        request_data = json.loads(message[14:])  # Remove 'autoDetectOCR:' prefix
        image_data = request_data.get('imageData', '')
        existing_shapes = request_data.get('existingShapes', [])
        image_width = request_data.get('imageWidth', 0)
        image_height = request_data.get('imageHeight', 0)
        
        # Extract and decode image data
        if ',' in image_data:
            image_data = image_data.split(',', 1)[1]
        
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        # Perform OCR
        regions = perform_ocr(image)
        
        # Filter out regions that collide with existing shapes
        if existing_shapes and image_width > 0 and image_height > 0:
            regions = filter_colliding_regions(regions, existing_shapes, image_width, image_height)
        
        # Send results back to JavaScript
        result = json.dumps({'regions': regions})
        if hasattr(context, 'web'):
            context.web.eval(f'window.autoIOCallback && window.autoIOCallback({result})')
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        
        # Send error to JavaScript
        error_result = json.dumps({'error': str(e)})
        if hasattr(context, 'web'):
            context.web.eval(f'window.autoIOCallback && window.autoIOCallback({error_result})')


def show_completion_message(message):
    """Show tooltip when detection completes"""
    try:
        data = json.loads(message[11:])  # Remove 'autoDetect:' prefix
        
        if data.get("status") == "complete":
            count = data.get("count", 0)
            if count > 0:
                tooltip(f"✓ Added {count} auto-detected occlusions")
            else:
                tooltip("No new regions detected")
    except Exception as e:
        pass

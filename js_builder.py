"""
JavaScript Builder Module
Generates the JavaScript code to inject into Anki's Image Occlusion editor

Architecture:
- Single global namespace (window.AutoIOAddon)
- Function interception for persistence (resetIOImageLoaded)
- MutationObserver for initial button addition
- Idempotent design (safe to run multiple times)
"""


def build_injection_javascript(config):
    """
    Builds the complete JavaScript code to inject into the Image Occlusion editor.
    This adds the auto-detect button and all related functionality.
    
    Args:
        config: Dictionary of addon configuration settings
        
    Returns:
        String containing JavaScript code
    """
    return f'''
(function() {{
    'use strict';
    
    
    // =========================================================================
    // NAMESPACE - Single global object for all addon state
    // =========================================================================
    
    if (!window.AutoIOAddon) {{
        window.AutoIOAddon = {{
            observer: null,              // MutationObserver for initial button addition
            resetIntercepted: false,     // Track if we've wrapped resetIOImageLoaded
            config: {{
                topPaddingPercent: 0.10, // Add 10% padding on top of detected boxes
                ocrTimeout: 30000,       // 30 second timeout for OCR operations
                debounceDelay: 100,      // Debounce delay for MutationObserver (ms)
                resetDelay: 200          // Delay after IO reset before re-adding button (ms)
            }}
        }};
    }}
    
    const addon = window.AutoIOAddon;
    
    
    // =========================================================================
    // INTERCEPTION - Hook into Anki's resetIOImageLoaded function
    // =========================================================================
    
    function interceptReset() {{
        // Only intercept once to avoid nested wrappers
        if (addon.resetIntercepted) {{
            return;
        }}
        
        // Check if the function exists (it's created when IO editor loads)
        if (typeof globalThis.resetIOImageLoaded !== 'function') {{
            return;
        }}
        
        // Store original function and wrap it
        const originalReset = globalThis.resetIOImageLoaded;
        globalThis.resetIOImageLoaded = function(...args) {{
            // Call original function first
            originalReset.apply(this, args);
            
            // Re-add button after toolbar is rebuilt
            console.log('[Auto-IO] IO editor reset detected, re-adding button');
            setTimeout(() => {{
                waitForIO();
            }}, addon.config.resetDelay);
        }};
        
        addon.resetIntercepted = true;
        console.log('[Auwto-IO] Successfully intercepted resetIOImageLoaded');
    }}
    
    
    // =========================================================================
    // INITIALIZATION - Wait for IO editor and add button
    // =========================================================================
    
    function waitForIO() {{
        // Try to intercept reset function if not already done
        interceptReset();
        
        function checkAndAddButton() {{
            // If button already exists, clean up observer and exit
            if (document.getElementById('auto-detect-btn')) {{
                if (addon.observer) {{
                    addon.observer.disconnect();
                    addon.observer = null;
                }}
                return;
            }}
            
            // Check if all required IO components are available
            const toolbar = document.querySelector('.top-tool-bar-container');
            const canvas = globalThis.canvas;
            const maskEditor = globalThis.maskEditor;
            
            if (toolbar && canvas && maskEditor) {{
                addButton();
                
                // Clean up observer after successful button addition
                if (addon.observer) {{
                    addon.observer.disconnect();
                    addon.observer = null;
                }}
            }}
        }}
        
        // Try immediate addition first
        checkAndAddButton();
        
        // If button wasn't added, watch for DOM changes
        if (!document.getElementById('auto-detect-btn') && !addon.observer) {{
            let debounceTimeout;
            
            addon.observer = new MutationObserver(() => {{
                // Debounce: only check after DOM stops changing
                clearTimeout(debounceTimeout);
                debounceTimeout = setTimeout(checkAndAddButton, addon.config.debounceDelay);
            }});
            
            // Observe editor container (more efficient than watching entire document)
            const targetElement = document.querySelector('.note-editor') || document.body;
            addon.observer.observe(targetElement, {{
                childList: true,
                subtree: true
            }});
        }}
    }}
    
    
    // =========================================================================
    // UI - Add auto-detect button to toolbar
    // =========================================================================
    
    function addButton() {{
        const toolbar = document.querySelector('.top-tool-bar-container');
        if (!toolbar) {{
            console.warn('[Auto-IO] Toolbar not found');
            return;
        }}
        
        // Check if button already exists (idempotent)
        if (document.getElementById('auto-detect-btn')) {{
            return;
        }}
        
        // Create container matching Anki's style
        const container = document.createElement('div');
        container.className = 'tool-button-container';
        
        // Create button matching Anki's IconButton style
        const btn = document.createElement('button');
        btn.className = 'top-tool-icon-button border-radius';
        btn.id = 'auto-detect-btn';
        btn.title = 'Auto-detect text regions (Ctrl+Shift+A)';
        btn.type = 'button';
        
        // Ensure button matches the height of other toolbar buttons
        btn.style.height = '100%';
        btn.style.aspectRatio = '1';
        btn.style.display = 'flex';
        btn.style.alignItems = 'center';
        btn.style.justifyContent = 'center';
        
        // Match the icon size used by other toolbar buttons
        const iconSize = 100; // Default iconSize for toolbar buttons
        
        // Use magic wand / auto-fix icon for distinctiveness (mdiAutoFix)
        btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width: ${{iconSize}}%; height: ${{iconSize}}%;">
                <path fill="currentColor" d="M7.5,5.6L5,7L6.4,4.5L5,2L7.5,3.4L10,2L8.6,4.5L10,7L7.5,5.6M19.5,15.4L22,14L20.6,16.5L22,19L19.5,17.6L17,19L18.4,16.5L17,14L19.5,15.4M22,2L20.6,4.5L22,7L19.5,5.6L17,7L18.4,4.5L17,2L19.5,3.4L22,2M13.34,12.78L15.78,10.34L13.66,8.22L11.22,10.66L13.34,12.78M14.37,7.29L16.71,9.63C17.1,10 17.1,10.65 16.71,11.04L5.04,22.71C4.65,23.1 4,23.1 3.63,22.71L1.29,20.37C0.9,20 0.9,19.35 1.29,18.96L12.96,7.29C13.35,6.9 14,6.9 14.37,7.29Z" />
            </svg>
        `;
        
        // Event listeners
        btn.addEventListener('click', autoDetect);
        
        // Add to toolbar at the end
        container.appendChild(btn);
        toolbar.appendChild(container);
        
        console.log('[Auto-IO] Button added successfully');
    }}
    
    // Helper: Set button visual state
    function setButtonState(btn, disabled, state) {{
        if (!btn) return;
        
        btn.disabled = disabled;
        
        if (state === 'loading') {{
            btn.style.opacity = '0.6';
            btn.style.cursor = 'wait';
        }} else {{
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }}
    }}
    
    // Global keyboard shortcut (Ctrl+Shift+A)
    document.addEventListener('keydown', (e) => {{
        if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'a') {{
            e.preventDefault();
            const btn = document.getElementById('auto-detect-btn');
            if (btn && !btn.disabled) {{
                autoDetect();
            }}
        }}
    }});
    
    
    // =========================================================================
    // OCR - Auto-detection orchestration
    // =========================================================================
    
    async function autoDetect() {{
        // Check if editor is ready
        if (!globalThis.canvas || !globalThis.maskEditor) {{
            alert('Image Occlusion editor not ready');
            return;
        }}
        
        const btn = document.getElementById('auto-detect-btn');
        setButtonState(btn, true, 'loading');
        
        try {{
            const canvas = globalThis.canvas;
            const maskEditor = globalThis.maskEditor;
            
            // Get image element and dimensions
            const imageElement = document.getElementById('image');
            if (!imageElement || !imageElement.complete || !imageElement.naturalWidth) {{
                throw new Error('Image not loaded');
            }}
            
            const imageWidth = imageElement.naturalWidth;
            const imageHeight = imageElement.naturalHeight;
            
            // Run OCR to detect text regions (collision detection done in Python)
            const regions = await detectText(imageElement);
            
            if (regions.length === 0) {{
                alert('No text regions detected or all regions already have occlusions');
                return;
            }}
            
            // Get canvas bounding box
            const boundingBox = canvas.getObjects().find(obj => obj['id'] === 'boundingBox');
            if (!boundingBox) {{
                throw new Error('Bounding box not found');
            }}
            
            const boundingRect = boundingBox.getBoundingRect();
            
            // Transform coordinates from image space to canvas space
            const scaledRegions = scaleRegions(regions, imageWidth, imageHeight, boundingRect);
            
            // Note: Collision detection is now done in Python for better accuracy
            // Double-check as a safety measure (should be redundant)
            const existing = maskEditor.getShapes();
            const filtered = filterOverlaps(scaledRegions, existing);
            
            if (filtered.length === 0) {{
                alert('All detected regions already have occlusions');
                return;
            }}
            
            // Add shapes to canvas
            addShapes(maskEditor, filtered, boundingBox, boundingRect);
            
            // Notify completion
            pycmd(`autoDetect:{{"status":"complete","count":${{filtered.length}}}}`);
            
        }} catch (error) {{
            console.error('[Auto-IO] Auto-detection failed:', error);
            alert('Auto-detection failed: ' + error.message);
        }} finally {{
            setButtonState(btn, false, 'normal');
        }}
    }}
    
    
    // =========================================================================
    // OCR - Detect text using Python backend
    // =========================================================================
    
    async function detectText(imageElement) {{
        // Convert image to data URL
        const canvas = document.createElement('canvas');
        canvas.width = imageElement.naturalWidth;
        canvas.height = imageElement.naturalHeight;
        const ctx = canvas.getContext('2d');
        ctx.drawImage(imageElement, 0, 0);
        const imageData = canvas.toDataURL('image/png');
        
        // Get existing shapes for collision detection (like logseq-anki-sync)
        const maskEditor = globalThis.maskEditor;
        const existingShapes = [];
        
        if (maskEditor) {{
            const shapes = maskEditor.getShapes();
            for (const shapeOrShapes of shapes) {{
                const shapeList = Array.isArray(shapeOrShapes) ? shapeOrShapes : [shapeOrShapes];
                for (const shape of shapeList) {{
                    existingShapes.push({{
                        left: shape.left,
                        top: shape.top,
                        width: shape.width,
                        height: shape.height
                    }});
                }}
            }}
        }}
        
        // Send to Python and wait for response
        return new Promise((resolve, reject) => {{
            // Set up callback for Python to call
            window.autoIOCallback = (result) => {{
                delete window.autoIOCallback;
                if (result.error) {{
                    reject(new Error(result.error));
                }} else {{
                    resolve(result.regions || []);
                }}
            }};
            
            // Set timeout for OCR operation
            const timeout = setTimeout(() => {{
                delete window.autoIOCallback;
                reject(new Error('OCR timeout'));
            }}, addon.config.ocrTimeout);
            
            // Clear timeout when callback is called
            const originalCallback = window.autoIOCallback;
            window.autoIOCallback = (result) => {{
                clearTimeout(timeout);
                originalCallback(result);
            }};
            
            // Send request to Python with collision detection data
            const request = {{
                imageData: imageData,
                existingShapes: existingShapes,
                imageWidth: imageElement.naturalWidth,
                imageHeight: imageElement.naturalHeight
            }};
            pycmd(`autoDetectOCR:${{JSON.stringify(request)}}`);
        }});
    }}
    
    
    // =========================================================================
    // COORDINATE TRANSFORMATION - Scale regions from image to canvas space
    // =========================================================================
    
    function scaleRegions(regions, imageWidth, imageHeight, boundingRect) {{
        const scaledRegions = [];
        
        for (const region of regions) {{
            // Add configurable top padding
            const topPadding = region.height * addon.config.topPaddingPercent;
            
            scaledRegions.push({{
                left: (region.left / imageWidth) * boundingRect.width,
                top: ((region.top - topPadding) / imageHeight) * boundingRect.height,
                width: (region.width / imageWidth) * boundingRect.width,
                height: ((region.height + topPadding) / imageHeight) * boundingRect.height
            }});
        }}
        
        return scaledRegions;
    }}
    
    
    // =========================================================================
    // FILTERING - Remove overlapping regions
    // =========================================================================
    
    function filterOverlaps(regions, existingShapes) {{
        const filtered = [];
        
        for (const region of regions) {{
            let overlaps = false;
            
            for (const shapeOrShapes of existingShapes) {{
                const shapes = Array.isArray(shapeOrShapes) ? shapeOrShapes : [shapeOrShapes];
                
                for (const shape of shapes) {{
                    if (rectsIntersect(region, shape)) {{
                        overlaps = true;
                        break;
                    }}
                }}
                if (overlaps) break;
            }}
            
            if (!overlaps) {{
                filtered.push(region);
            }}
        }}
        
        return filtered;
    }}
    
    function rectsIntersect(r1, r2) {{
        return !(
            r1.top + r1.height < r2.top ||
            r1.top > r2.top + r2.height ||
            r1.left + r1.width < r2.left ||
            r1.left > r2.left + r2.width
        );
    }}
    
    
    // =========================================================================
    // SHAPE CREATION - Add rectangles to canvas
    // =========================================================================
    
    function addShapes(maskEditor, regions, boundingBox, boundingRect) {{
        const Rectangle = maskEditor.Rectangle;
        
        for (const region of regions) {{
            // Normalize coordinates to 0-1 range (required by Anki's API)
            const normalizedShape = new Rectangle({{
                left: region.left / boundingRect.width,
                top: region.top / boundingRect.height,
                width: region.width / boundingRect.width,
                height: region.height / boundingRect.height
            }});
            
            maskEditor.addShape(boundingBox, normalizedShape);
        }}
        
        maskEditor.redraw();
    }}
    
    
    // =========================================================================
    // START
    // =========================================================================
    
    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', waitForIO);
    }} else {{
        waitForIO();
    }}
    
}})();
'''

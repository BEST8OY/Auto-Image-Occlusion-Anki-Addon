"""
JavaScript Builder Module
Generates the JavaScript code to inject into Anki's Image Occlusion editor

Architecture:
- Single global namespace (window.AutoIOAddon)
- Function interception for persistence (resetIOImage)
- MutationObserver for initial button addition
- Idempotent design (safe to run multiple times)
"""

import json


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
            resetIntercepted: false,     // Track if we've wrapped resetIOImage
            ocrPending: false,           // Prevent concurrent OCR requests
            config: {{
                topPaddingPercent: 0.10, // Add 10% padding on top of detected boxes
                ocrTimeout: 30000,       // 30 second timeout for OCR operations
                debounceDelay: 100,      // Debounce delay for MutationObserver (ms)
                resetDelay: 200,         // Delay after IO reset before re-adding button (ms)
                shortcut: {json.dumps(config.get('button_shortcut', 'Ctrl+Shift+A'))},
                verticalMergeFactor: {float(config.get('vertical_merge_factor', 0.65))}
            }}
        }};
    }}

    const addon = window.AutoIOAddon;

    try {{
        const storedFactor = localStorage.getItem('auto_io_vertical_merge_factor');
        if (storedFactor !== null && !isNaN(parseFloat(storedFactor))) {{
            addon.config.verticalMergeFactor = parseFloat(storedFactor);
        }}
    }} catch (e) {{}}


    // =========================================================================
    // INTERCEPTION - Hook into Anki's resetIOImage function
    // =========================================================================

    function interceptReset() {{
        // Only intercept once to avoid nested wrappers
        if (addon.resetIntercepted) {{
            return;
        }}

        // Check if the function exists (it's created when IO editor loads)
        // Anki exposes this as globalThis.resetIOImage in mask-editor.ts
        if (typeof globalThis.resetIOImage !== 'function') {{
            return;
        }}

        // Store original function and wrap it
        const originalReset = globalThis.resetIOImage;
        globalThis.resetIOImage = function(...args) {{
            // Call original function first
            originalReset.apply(this, args);

            // Re-add button after toolbar is rebuilt
            console.log('[Auto-IO] IO editor reset detected, re-adding button');
            setTimeout(() => {{
                waitForIO();
            }}, addon.config.resetDelay);
        }};

        addon.resetIntercepted = true;
        console.log('[Auto-IO] Successfully intercepted resetIOImage');
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

            // Observe the image-occlusion container (Anki's actual DOM structure)
            // Falls back to document.body if the container doesn't exist yet
            const targetElement = document.querySelector('.image-occlusion')
                || document.querySelector('.editor-main')
                || document.body;
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
        container.className = 'tool-button-container auto-io-group-container';
        container.id = 'auto-detect-container';
        container.style.display = 'flex';
        container.style.alignItems = 'center';

        // 1. Magic Wand Action Button
        const btn = document.createElement('button');
        btn.className = 'icon-button top-tool-icon-button left-border-radius';
        btn.id = 'auto-detect-btn';
        btn.title = `Auto-detect text regions (${{addon.config.shortcut}})`;
        btn.type = 'button';
        btn.style.setProperty('width', '32px', 'important');
        btn.style.setProperty('height', '36px', 'important');
        btn.style.setProperty('padding', '6px', 'important');
        btn.style.setProperty('display', 'inline-flex', 'important');
        btn.style.setProperty('align-items', 'center', 'important');
        btn.style.setProperty('justify-content', 'center', 'important');
        btn.style.setProperty('box-sizing', 'border-box', 'important');
        btn.style.setProperty('cursor', 'pointer', 'important');
        btn.style.setProperty('border-right', 'none', 'important');

        // Match the icon size used by other toolbar buttons
        const iconSize = 100;

        // Use magic wand / auto-fix icon for distinctiveness (mdiAutoFix)
        btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width: ${{iconSize}}%; height: ${{iconSize}}%; pointer-events: none;">
                <path fill="currentColor" d="M7.5,5.6L5,7L6.4,4.5L5,2L7.5,3.4L10,2L8.6,4.5L10,7L7.5,5.6M19.5,15.4L22,14L20.6,16.5L22,19L19.5,17.6L17,19L18.4,16.5L17,14L19.5,15.4M22,2L20.6,4.5L22,7L19.5,5.6L17,7L18.4,4.5L17,2L19.5,3.4L22,2M13.34,12.78L15.78,10.34L13.66,8.22L11.22,10.66L13.34,12.78M14.37,7.29L16.71,9.63C17.1,10 17.1,10.65 16.71,11.04L5.04,22.71C4.65,23.1 4,23.1 3.63,22.71L1.29,20.37C0.9,20 0.9,19.35 1.29,18.96L12.96,7.29C13.35,6.9 14,6.9 14.37,7.29Z" />
            </svg>
        `;

        btn.addEventListener('click', autoDetect);
        container.appendChild(btn);

        // Inject CSS for Auto-IO toolbar and popover
        if (!document.getElementById('auto-io-toolbar-styles')) {{
            const style = document.createElement('style');
            style.id = 'auto-io-toolbar-styles';
            style.textContent = `
                .auto-io-group-container {{
                    display: flex !important;
                    align-items: center !important;
                    flex-shrink: 0 !important;
                }}
                #auto-detect-btn {{
                    width: 32px !important;
                    height: 36px !important;
                    padding: 6px !important;
                    display: inline-flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    box-sizing: border-box !important;
                    cursor: pointer !important;
                    border-right: none !important;
                    flex-shrink: 0 !important;
                }}
                #auto-detect-merge-btn {{
                    width: auto !important;
                    max-width: none !important;
                    height: 36px !important;
                    line-height: 36px !important;
                    padding: 0 8px !important;
                    display: inline-flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                    gap: 4px !important;
                    font-size: 11px !important;
                    font-weight: 600 !important;
                    white-space: nowrap !important;
                    overflow: visible !important;
                    box-sizing: border-box !important;
                    cursor: pointer !important;
                    flex-shrink: 0 !important;
                    border-left: 1px solid var(--border-subtle) !important;
                }}
                .auto-io-preset-item {{
                    display: flex !important;
                    justify-content: space-between !important;
                    align-items: center !important;
                    width: calc(100% - 8px) !important;
                    margin: 1px 4px !important;
                    padding: 6px 10px !important;
                    border-radius: 4px !important;
                    background: transparent !important;
                    border: none !important;
                    color: inherit !important;
                    cursor: pointer !important;
                    font-size: 12px !important;
                    text-align: left !important;
                    transition: background-color 0.1s ease;
                    box-sizing: border-box !important;
                }}
                .auto-io-preset-item:hover {{
                    background-color: var(--highlight-bg, rgba(128, 128, 128, 0.18)) !important;
                }}
                .auto-io-preset-item.active {{
                    background-color: rgba(10, 132, 255, 0.2) !important;
                    color: var(--border-focus, #0a84ff) !important;
                    font-weight: 600 !important;
                }}
                .auto-io-preset-item.active:hover {{
                    background-color: rgba(10, 132, 255, 0.3) !important;
                }}
            `;
            document.head.appendChild(style);
        }}

        // 2. Merge Factor Split Button with Dropdown Trigger
        const mergeBtn = document.createElement('button');
        mergeBtn.className = 'icon-button top-tool-icon-button right-border-radius';
        mergeBtn.id = 'auto-detect-merge-btn';
        mergeBtn.title = 'Line merge tolerance: click for presets or scroll to adjust';
        mergeBtn.type = 'button';
        mergeBtn.style.setProperty('width', 'auto', 'important');
        mergeBtn.style.setProperty('max-width', 'none', 'important');
        mergeBtn.style.setProperty('height', '36px', 'important');
        mergeBtn.style.setProperty('line-height', '36px', 'important');
        mergeBtn.style.setProperty('padding', '0 8px', 'important');
        mergeBtn.style.setProperty('display', 'inline-flex', 'important');
        mergeBtn.style.setProperty('align-items', 'center', 'important');
        mergeBtn.style.setProperty('justify-content', 'center', 'important');
        mergeBtn.style.setProperty('gap', '4px', 'important');
        mergeBtn.style.setProperty('font-size', '11px', 'important');
        mergeBtn.style.setProperty('font-weight', '600', 'important');
        mergeBtn.style.setProperty('cursor', 'pointer', 'important');
        mergeBtn.style.setProperty('box-sizing', 'border-box', 'important');
        mergeBtn.style.setProperty('white-space', 'nowrap', 'important');
        mergeBtn.style.setProperty('overflow', 'visible', 'important');
        mergeBtn.style.setProperty('flex-shrink', '0', 'important');
        mergeBtn.style.setProperty('border-left', '1px solid var(--border-subtle)', 'important');

        const initialFactor = (addon.config.verticalMergeFactor !== undefined)
            ? addon.config.verticalMergeFactor
            : 0.65;

        mergeBtn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width: 12px; height: 12px; fill: currentColor; opacity: 0.7; flex-shrink: 0; pointer-events: none;">
                <path d="M9 3L5 7h3v7h2V7h3L9 3zm6 18l4-4h-3v-7h-2v7h-3l4 4z"/>
            </svg>
            <span id="auto-detect-merge-label" style="font-variant-numeric: tabular-nums; flex-shrink: 0; line-height: 1;">${{Number(initialFactor).toFixed(2)}}</span>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="width: 10px; height: 10px; fill: currentColor; opacity: 0.7; flex-shrink: 0; pointer-events: none;">
                <path d="M7 10l5 5 5-5z"/>
            </svg>
        `;

        container.appendChild(mergeBtn);

        // 3. Dropdown Popover Management
        let popover = null;

        function updateMergeFactor(val) {{
            const clamped = Math.max(0, Math.min(2, Math.round(val * 100) / 100));
            addon.config.verticalMergeFactor = clamped;
            const label = document.getElementById('auto-detect-merge-label');
            if (label) label.textContent = clamped.toFixed(2);
            try {{
                localStorage.setItem('auto_io_vertical_merge_factor', clamped.toString());
            }} catch (e) {{}}

            if (popover) {{
                popover.querySelectorAll('.auto-io-preset-item').forEach(pBtn => {{
                    const pVal = parseFloat(pBtn.dataset.val);
                    const isMatch = Math.abs(pVal - clamped) < 0.02;
                    pBtn.classList.toggle('active', isMatch);
                }});
                const slider = popover.querySelector('.auto-io-slider');
                const numInput = popover.querySelector('.auto-io-num-input');
                const fineVal = popover.querySelector('.auto-io-fine-val');
                if (slider && parseFloat(slider.value) !== clamped) slider.value = clamped;
                if (numInput && parseFloat(numInput.value) !== clamped) numInput.value = clamped.toFixed(2);
                if (fineVal) fineVal.textContent = clamped.toFixed(2);
            }}
        }}

        function createPopover() {{
            if (popover) return popover;

            popover = document.createElement('div');
            popover.id = 'auto-detect-popover';
            popover.style.position = 'fixed';
            popover.style.width = '240px';
            popover.style.background = 'var(--canvas-elevated, #2c2c2e)';
            popover.style.border = '1px solid var(--border-subtle, #48484a)';
            popover.style.borderRadius = '6px';
            popover.style.boxShadow = '0 10px 30px rgba(0,0,0,0.5)';
            popover.style.zIndex = '99999';
            popover.style.padding = '6px 0';
            popover.style.fontSize = '12px';
            popover.style.color = 'var(--fg, #f2f2f7)';
            popover.style.fontFamily = 'system-ui, -apple-system, sans-serif';
            popover.style.boxSizing = 'border-box';
            popover.style.userSelect = 'none';
            popover.style.display = 'none';

            popover.innerHTML = `
                <div style="padding: 6px 14px 4px; font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; color: var(--fg-subtle, #8e8e93); display: flex; justify-content: space-between; align-items: center;">
                    <span>Line Merge Tolerance</span>
                    <span style="font-size: 9px; opacity: 0.7;">↕ factor</span>
                </div>
                <div class="auto-io-presets" style="display: flex; flex-direction: column;">
                    <button type="button" class="auto-io-preset-item" data-val="0.0">
                        <span>Separate Lines</span><span style="opacity: 0.5;">0.00</span>
                    </button>
                    <button type="button" class="auto-io-preset-item" data-val="0.4">
                        <span>Tight Spacing</span><span style="opacity: 0.5;">0.40</span>
                    </button>
                    <button type="button" class="auto-io-preset-item" data-val="0.65">
                        <span>Standard (Default)</span><span style="opacity: 0.5;">0.65</span>
                    </button>
                    <button type="button" class="auto-io-preset-item" data-val="1.0">
                        <span>Wide Spacing</span><span style="opacity: 0.5;">1.00</span>
                    </button>
                    <button type="button" class="auto-io-preset-item" data-val="1.5">
                        <span>Aggressive Merge</span><span style="opacity: 0.5;">1.50</span>
                    </button>
                </div>
                <div style="padding: 8px 14px 4px; border-top: 1px solid var(--border, #38383a); margin-top: 4px;">
                    <div style="font-size: 11px; color: var(--fg-subtle, #8e8e93); margin-bottom: 6px; display: flex; justify-content: space-between;">
                        <span>Fine-Tune</span>
                        <span class="auto-io-fine-val" style="font-weight: 600; color: var(--fg, inherit);">${{Number(addon.config.verticalMergeFactor).toFixed(2)}}</span>
                    </div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <input type="range" class="auto-io-slider" min="0" max="2" step="0.05" value="${{Number(addon.config.verticalMergeFactor).toFixed(2)}}" style="flex: 1; height: 4px; accent-color: var(--border-focus, #0a84ff); cursor: pointer;">
                        <input type="number" class="auto-io-num-input" step="0.05" min="0" max="2" value="${{Number(addon.config.verticalMergeFactor).toFixed(2)}}" style="width: 48px; height: 24px; background: var(--canvas-inset, var(--canvas, rgba(128, 128, 128, 0.15))); border: 1px solid var(--border-subtle, #48484a); border-radius: 4px; color: var(--fg, inherit); text-align: center; font-size: 12px; font-weight: 600; outline: none;">
                    </div>
                </div>
            `;

            popover.querySelectorAll('.auto-io-preset-item').forEach(item => {{
                item.addEventListener('click', (e) => {{
                    e.stopPropagation();
                    const val = parseFloat(item.dataset.val);
                    updateMergeFactor(val);
                    closePopover();
                }});
            }});

            const slider = popover.querySelector('.auto-io-slider');
            const numInput = popover.querySelector('.auto-io-num-input');

            slider.addEventListener('input', () => {{
                const val = parseFloat(slider.value);
                updateMergeFactor(val);
            }});

            ['keydown', 'keyup', 'keypress'].forEach(evt => {{
                numInput.addEventListener(evt, e => e.stopPropagation());
            }});

            numInput.addEventListener('input', () => {{
                const val = parseFloat(numInput.value);
                if (!isNaN(val)) updateMergeFactor(val);
            }});

            document.body.appendChild(popover);
            return popover;
        }}

        function openPopover() {{
            const p = createPopover();
            const rect = mergeBtn.getBoundingClientRect();
            p.style.top = (rect.bottom + 4) + 'px';
            p.style.left = Math.max(8, Math.min(window.innerWidth - 250, rect.left)) + 'px';
            p.style.display = 'block';
            updateMergeFactor(addon.config.verticalMergeFactor);
        }}

        function closePopover() {{
            if (popover) popover.style.display = 'none';
        }}

        function togglePopover(e) {{
            e.stopPropagation();
            if (popover && popover.style.display === 'block') {{
                closePopover();
            }} else {{
                openPopover();
            }}
        }}

        mergeBtn.addEventListener('click', togglePopover);

        // Wheel scrolling on mergeBtn adjusts by 0.05
        mergeBtn.addEventListener('wheel', (e) => {{
            e.preventDefault();
            e.stopPropagation();
            const current = parseFloat(addon.config.verticalMergeFactor) || 0;
            const delta = e.deltaY < 0 ? 0.05 : -0.05;
            updateMergeFactor(current + delta);
        }}, {{ passive: false }});

        // Close on outside click or escape
        document.addEventListener('click', (e) => {{
            if (popover && popover.style.display === 'block' && !popover.contains(e.target) && e.target !== mergeBtn) {{
                closePopover();
            }}
        }});

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape' && popover && popover.style.display === 'block') {{
                closePopover();
            }}
        }});

        // Add to toolbar at the end
        toolbar.appendChild(container);

        console.log('[Auto-IO] Segmented button and merge factor popover added successfully');
    }}

    // Helper: Set button visual state
    function setButtonState(btn, disabled, state) {{
        if (!btn) return;

        btn.disabled = disabled;
        const mergeBtn = document.getElementById('auto-detect-merge-btn');
        if (mergeBtn) {{
            mergeBtn.disabled = disabled;
        }}

        if (state === 'loading') {{
            btn.style.opacity = '0.6';
            btn.style.cursor = 'wait';
        }} else {{
            btn.style.opacity = '1';
            btn.style.cursor = 'pointer';
        }}
    }}

    // Global keyboard shortcut (configurable)
    function parseShortcut(str) {{
        const parts = str.toLowerCase().split('+');
        const key = parts.pop();
        return {{
            ctrl: parts.includes('ctrl'),
            shift: parts.includes('shift'),
            alt: parts.includes('alt'),
            meta: parts.includes('meta') || parts.includes('cmd'),
            key: key
        }};
    }}

    const shortcut = parseShortcut(addon.config.shortcut);

    document.addEventListener('keydown', (e) => {{
        if (e.ctrlKey === shortcut.ctrl
            && e.shiftKey === shortcut.shift
            && e.altKey === shortcut.alt
            && e.metaKey === shortcut.meta
            && e.key.toLowerCase() === shortcut.key) {{
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

        // Prevent concurrent OCR requests
        if (addon.ocrPending) {{
            return;
        }}

        const btn = document.getElementById('auto-detect-btn');
        setButtonState(btn, true, 'loading');
        addon.ocrPending = true;

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
            addon.ocrPending = false;
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
            // Use a unique ID to prevent stale callbacks from interfering
            const requestId = Date.now() + '_' + Math.random();

            // Set timeout for OCR operation
            const timeout = setTimeout(() => {{
                delete window.autoIOCallback;
                reject(new Error('OCR timeout'));
            }}, addon.config.ocrTimeout);

            // Set up callback for Python to call
            window.autoIOCallback = (result) => {{
                clearTimeout(timeout);
                delete window.autoIOCallback;
                if (result.error) {{
                    reject(new Error(result.error));
                }} else {{
                    resolve(result.regions || []);
                }}
            }};

            // Get current merge factor from addon config
            const mergeFactor = (addon.config.verticalMergeFactor !== undefined)
                ? addon.config.verticalMergeFactor
                : 0.65;

            // Send request to Python with collision detection data and merge factor
            const request = {{
                imageData: imageData,
                existingShapes: existingShapes,
                imageWidth: imageElement.naturalWidth,
                imageHeight: imageElement.naturalHeight,
                mergeFactor: mergeFactor
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

import re
import time
import random

from input_helpers import (
    natural_mouse_move, update_cursor, virtual_click,
    virtual_type
)


class VirtualBrowserController:
    def __init__(self, page):
        """Initialize the virtual browser controller."""
        self.page = page
        self.current_x = 100
        self.current_y = 100

        # Set up navigation event listeners
        self.page.on("popup", lambda popup: self._handle_new_tab(popup))

        # Initialize cursor position
        self._update_cursor(self.current_x, self.current_y)



    def analyze_page(self):
        """Extract all visible text and page elements in a structured format while maintaining hierarchy."""
        try:
            # Initialize page elements array to store detailed information
            self.page_elements = []

            # Use JavaScript to directly analyze the DOM
            page_content = self.page.evaluate("""
            () => {
                // Helper function to check if element is visible
                function isVisible(el) {
                    if (!el.getBoundingClientRect) return false;
                    const rect = el.getBoundingClientRect();

                    // Check if element has dimensions
                    if (rect.width <= 0 || rect.height <= 0) return false;

                    // Check CSS properties that would make it invisible
                    const style = window.getComputedStyle(el);
                    if (style.display === 'none' ||
                        style.visibility === 'hidden' ||
                        parseFloat(style.opacity) <= 0.1) {
                        return false;
                    }

                    return true;
                }

                // Helper to clean text
                function cleanText(text) {
                    if (!text) return '';
                    return text.replace(/\\s+/g, ' ').trim();
                }

                // In the analyze_page method, replace the current getElementType function with this enhanced version:
                function getElementType(el) {
                    const tagName = el.tagName.toLowerCase();
                    const type = el.getAttribute('type')?.toLowerCase();
                    const role = el.getAttribute('role')?.toLowerCase();

                    // Interactive elements with specific types
                    if (tagName === 'a') return 'link';
                    if (tagName === 'button') return 'button';

                    if (tagName === 'input') {
                        if (['submit', 'button', 'reset'].includes(type)) return 'button';
                        if (['text', 'email', 'password', 'search', 'tel', 'url'].includes(type)) return 'input';
                        if (type === 'checkbox') return 'checkbox';
                        if (type === 'radio') return 'radio';
                        return 'input'; // Default for other input types
                    }

                    if (tagName === 'select') return 'dropdown';
                    if (tagName === 'textarea') return 'textarea';

                    // Check for ARIA roles
                    if (role === 'button') return 'button';
                    if (role === 'link') return 'link';
                    if (role === 'checkbox') return 'checkbox';
                    if (role === 'radio') return 'radio';
                    if (role === 'textbox' || role === 'searchbox') return 'input';
                    if (role === 'combobox' || role === 'listbox') return 'dropdown';
                    if (role === 'tab') return 'tab';

                    // Check for interactive divs/spans
                    const style = window.getComputedStyle(el);
                    const hasClickHandler = el.onclick || el.getAttribute('onclick');
                    const isPointable = style.cursor === 'pointer';

                    if ((tagName === 'div' || tagName === 'span') && (hasClickHandler || isPointable)) {
                        // Try to determine a more specific type for divs/spans that are clickable
                        if (el.getAttribute('aria-haspopup') === 'true') return 'dropdown';
                        if (el.classList.contains('btn') || el.classList.contains('button')) return 'button';
                        if (el.getAttribute('href') || el.getAttribute('url')) return 'link';

                        // If we can't determine a more specific type, default to button
                        return 'button';
                    }

                    // Enhanced detection for additional interactive elements
                    if (el.getAttribute('onclick') || el.getAttribute('tabindex') === '0') return 'interactive';
                    if (style.cursor === 'pointer') return 'interactive';

                    // Form label elements often need to be clickable
                    if (tagName === 'label') return 'label';

                    // Interactive list items
                    if (tagName === 'li' && (isPointable || hasClickHandler)) return 'listitem';

                    // Images that might be clickable
                    if (tagName === 'img' && (isPointable || hasClickHandler || el.parentElement?.tagName.toLowerCase() === 'a'))
                        return 'image';

                    // Headers that might be expandable
                    if (['h1','h2','h3','h4','h5','h6'].includes(tagName) && (isPointable || hasClickHandler))
                        return 'header';

                    // For elements that aren't clearly interactive but have children that are
                    if (el.querySelector('a, button, input, select, textarea')) return 'container';

                    // Last resort: any element with sufficient content should be identifiable
                    if (el.innerText && el.innerText.trim().length > 0 &&
                        ['div', 'span', 'p', 'section', 'article'].includes(tagName))
                        return 'content';

                    return null; // Only truly non-interactive elements get null
                }

                // Get all attributes of an element
                function getElementAttributes(el) {
                    const result = {};
                    for (const attr of el.attributes) {
                        result[attr.name] = attr.value;
                    }
                    return result;
                }

                // Generate CSS selector for element
                function generateSelector(el) {
                    if (!el) return '';
                    if (el.id) return '#' + CSS.escape(el.id);

                    let selector = el.tagName.toLowerCase();

                    if (el.classList && el.classList.length) {
                        const classes = Array.from(el.classList).slice(0, 2);
                        selector += '.' + classes.join('.');
                    }

                    return selector;
                }

                // Get parent info for context
                function getParentInfo(el) {
                    if (!el || !el.parentElement) return null;

                    const parent = el.parentElement;
                    return {
                        tagName: parent.tagName.toLowerCase(),
                        id: parent.id || '',
                        className: parent.className || '',
                        text: cleanText(parent.innerText || parent.textContent || '').substring(0, 50)
                    };
                }

                // Extract all visible content maintaining the document structure
                function extractStructuredContent() {
                    const extractedContent = [];
                    const detailedElements = [];
                    const processedNodes = new Set();
                    let elementId = 0;

                    // Process elements in document order
                    function processNode(node, depth = 0) {
                        if (!node || processedNodes.has(node)) return;
                        processedNodes.add(node);

                        // Only process elements (not text nodes or other node types)
                        if (node.nodeType !== Node.ELEMENT_NODE) return;

                        // Skip invisible elements
                        if (!isVisible(node)) return;

                        // Get element's own text (excluding child element text)
                        let ownText = '';

                        for (const child of node.childNodes) {
                            if (child.nodeType === Node.TEXT_NODE) {
                                ownText += child.textContent;
                            }
                        }
                        ownText = cleanText(ownText);

                        // Get element type
                        const elementType = getElementType(node);

                        // Replace the conditional element processing block with this:
                        // For interactive elements, add with type prefix
                        if (elementType) {
                            // For input fields, use placeholder or name if there's no text
                            let displayText = ownText;
                            if ((elementType === 'input' || elementType === 'textarea') && !displayText) {
                                displayText = node.getAttribute('placeholder') ||
                                            node.getAttribute('name') ||
                                            node.getAttribute('aria-label') ||
                                            node.getAttribute('title') || '';
                            }

                            // For images without text, use alt text
                            if (elementType === 'image' && !displayText) {
                                displayText = node.getAttribute('alt') || node.getAttribute('title') || 'image';
                            }

                            // Only include elements that have text content or are interactive inputs
                            if (displayText || elementType === 'input' || elementType === 'button' ||
                                elementType === 'checkbox' || elementType === 'radio') {
                                if (!displayText) displayText = elementType; // Default text is the element type

                                // Add element ID to the output
                                extractedContent.push(`[${elementId}][${elementType}]${displayText}`);

                                // Get detailed information about the element
                                const rect = node.getBoundingClientRect();
                                const elementInfo = {
                                    id: elementId,
                                    tagName: node.tagName,
                                    type: elementType,
                                    text: displayText,
                                    x: rect.left + window.pageXOffset,
                                    y: rect.top + window.pageYOffset,
                                    width: rect.width,
                                    height: rect.height,
                                    center_x: rect.left + rect.width/2 + window.pageXOffset,
                                    center_y: rect.top + rect.height/2 + window.pageYOffset,
                                    inViewport: (
                                        rect.top >= 0 &&
                                        rect.left >= 0 &&
                                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                                        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                                    ),
                                    attributes: getElementAttributes(node),
                                    cssSelector: generateSelector(node),
                                    parentInfo: getParentInfo(node),
                                    innerHTML: node.innerHTML.substring(0, 200),
                                    childElementCount: node.childElementCount,
                                    isDisabled: node.disabled || node.hasAttribute('disabled'),
                                    zIndex: parseInt(window.getComputedStyle(node).zIndex) || 0
                                };

                                detailedElements.push(elementInfo);
                                elementId++;
                            }
                        }
                        // For non-interactive elements with text, just add the text
                        else if (ownText && ownText.length > 1) {
                            extractedContent.push(ownText);
                        }

                        // Process children in document order
                        for (const child of node.children) {
                            processNode(child, depth + 1);
                        }
                    }

                    // Start processing from body
                    processNode(document.body);

                    return {
                        content: extractedContent,
                        elements: detailedElements
                    };
                }

                // Extract content in document structure order
                return extractStructuredContent();
            }
            """)

            # Store the detailed elements information
            self.page_elements = page_content['elements']

            # Post-process the content - clean up formatting and structure
            result = []
            current_line = ""

            # Add each item, grouping related content on the same line
            for item in page_content['content']:
                # Start a new line for interactive elements or if current line is empty
                if item.startswith('[') or not current_line:
                    if (current_line):  # Add the previous line if it exists
                        result.append(current_line)
                    current_line = item

                # Keep short content items together if they're related (price, ratings, etc.)
                elif len(item) < 30 and len(current_line) + len(item) + 1 < 80:
                    current_line += " " + item

                # Otherwise start a new line
                else:
                    result.append(current_line)
                    current_line = item

            # Don't forget the last line
            if current_line:
                result.append(current_line)

            # Format the result and limit length
            formatted_result = "\n".join(result).strip()

            # if len(formatted_result) > 4000:
            #     return formatted_result[:4000] + "\n...content truncated..."

            return formatted_result

        except Exception as e:
            return f"Error analyzing page: {str(e)}"

    def visual_click(self, target_description):
        """
        Click on an element based on element ID, type, and text using DOM selection.
        """
        try:
            print(f"Attempting visual click for: {target_description}")

            # Parse structured input with ID field
            target_id, target_type, target_text, is_structured = self._parse_click_target(target_description)

            # If ID is provided, try to use it directly from page_elements array
            if target_id is not None and hasattr(self, 'page_elements') and self.page_elements:
                try:
                    element_index = int(target_id)
                    if 0 <= element_index < len(self.page_elements):
                        # Direct access to element by ID
                        result = self.page_elements[element_index]
                        print(f"Using direct element access by ID: {target_id}")
                    else:
                        result = None
                except (ValueError, TypeError):
                    result = None
            else:
                # Fallback to traditional finding if no valid ID
                result = None

            # If direct access failed or wasn't available, use traditional search
            if not result:
                print(f"Element ID {target_id} not found, trying traditional search")
                # Find matching element using unified selection logic
                result = self._find_element(target_type, target_text, is_structured, target_description=target_description)

            # If no element found, try scrolling and searching again
            if not result:
                print("No matching element found. Attempting to scroll and search...")
                self.scroll("down")
                time.sleep(1)
                result = self._find_element(target_type, target_text, is_structured, relaxed=True)

            # If still no matching element, return error
            if not result:
                if is_structured:
                    criteria = [f"{k}={v}" for k, v in {'id': target_id, 'type': target_type, 'text': target_text}.items() if v]
                    return f"No elements matching {', '.join(criteria)} found, even after scrolling."
                else:
                    return f"No elements matching '{target_description}' found, even after scrolling."

            # Get element coordinates for clicking
            x, y = result['center_x'], result['center_y']
            print(f"Selected element: ID={result.get('id', 'unknown')}, Type={result['type']}, Text=\"{result['text']}\"")

            # Ensure element is visible in viewport
            if not result.get('inViewport', False):
                x, y = self._scroll_to_element(result)

            # Perform the click
            return self._perform_click(x, y, result)

        except Exception as e:
            print(f"Error in visual_click: {str(e)}")
            return f"Error clicking on element: {str(e)}"



    def _parse_click_target(self, target_description):
        """Parse target description into ID, type and text components."""
        target_id = None
        target_type = None
        target_text = None
        is_structured = False

        # Try to parse structured input (JSON format)
        if isinstance(target_description, str) and target_description.startswith('{') and target_description.endswith('}'):
            try:
                # First try to parse as JSON
                import json
                try:
                    parsed_input = json.loads(target_description)
                    if isinstance(parsed_input, dict):
                        target_id = parsed_input.get('id')
                        target_type = parsed_input.get('type', '').lower() if parsed_input.get('type') else None
                        target_text = parsed_input.get('text', '').lower() if parsed_input.get('text') else None
                        if target_id or target_type or target_text:
                            is_structured = True
                            print(f"Using JSON structured input: id='{target_id}', type='{target_type}', text='{target_text}'")
                except json.JSONDecodeError:
                    # If not valid JSON, fall back to simple parsing
                    content = target_description.strip('{}').strip()
                    parts = [part.strip() for part in content.split(',')]

                    for part in parts:
                        if ':' in part:
                            key, value = [item.strip() for item in part.split(':', 1)]
                            if key.lower() == 'id':
                                target_id = value
                            elif key.lower() == 'type':
                                target_type = value.lower()
                            elif key.lower() == 'text':
                                target_text = value.lower()

                    if target_id or target_type or target_text:
                        is_structured = True
                        print(f"Using structured input: id='{target_id}', type='{target_type}', text='{target_text}'")
            except Exception as e:
                print(f"Error parsing input: {e}, using as free text instead")

        # Handle direct ID pattern extraction (like [3][button]Submit)
        if not is_structured and isinstance(target_description, str):
            id_type_pattern = re.match(r'\[(\d+)\]\[(.*?)\](.*)', target_description)
            if id_type_pattern:
                target_id = id_type_pattern.group(1)
                target_type = id_type_pattern.group(2).lower()
                target_text = id_type_pattern.group(3)
                is_structured = True
                print(f"Extracted from pattern: id='{target_id}', type='{target_type}', text='{target_text}'")

        return target_id, target_type, target_text, is_structured

    def _find_element(self, target_type, target_text, is_structured, relaxed=False, target_description=None):
            """Find an element based on type and text with improved selection logic."""
            js_code = """
                (params) => {
                    const { targetType, targetText, isStructured, relaxed } = params;

                    // Helper function to check if element is visible
                    function isVisible(el) {
                        if (!el.getBoundingClientRect) return false;
                        const rect = el.getBoundingClientRect();
                        if (rect.width <= 0 || rect.height <= 0) return false;
                        const style = window.getComputedStyle(el);
                        return !(style.display === 'none' || style.visibility === 'hidden' ||
                            parseFloat(style.opacity) <= 0.1);
                    }

                    // Helper to normalize and clean text
                    function normalizeText(text) {
                        if (!text) return '';
                        // First normalize spaces
                        text = text.replace(/\\s+/g, ' ').trim().toLowerCase();
                        // Then normalize common separators to help with matching
                        text = text.replace(/\\s*\\/\\s*/g, '/'); // Normalize "Cash on Delivery / Pay on Delivery" -> "Cash on Delivery/Pay on Delivery"
                        return text;
                    }

                    // Helper to get element type with better categorization
                    function getElementType(el) {
                        const tagName = el.tagName.toLowerCase();
                        const type = el.getAttribute('type')?.toLowerCase();
                        const role = el.getAttribute('role')?.toLowerCase();

                        // Basic element types
                        if (tagName === 'a') return 'link';
                        if (tagName === 'button') return 'button';

                        // Input elements
                        if (tagName === 'input') {
                            if (['submit', 'button', 'reset'].includes(type)) return 'button';
                            if (['text', 'email', 'password', 'search', 'tel', 'url'].includes(type)) return 'input';
                            if (type === 'checkbox') return 'checkbox';
                            if (type === 'radio') return 'radio';
                            return 'input';
                        }

                        // Other form elements
                        if (tagName === 'select') return 'dropdown';
                        if (tagName === 'textarea') return 'textarea';

                        // ARIA roles
                        if (role === 'button') return 'button';
                        if (role === 'link') return 'link';
                        if (role === 'checkbox') return 'checkbox';
                        if (role === 'radio') return 'radio';
                        if (role === 'textbox' || role === 'searchbox') return 'input';
                        if (role === 'combobox' || role === 'listbox') return 'dropdown';
                        if (role === 'tab') return 'tab';

                        // Look for common payment method patterns
                        if ((tagName === 'div' || tagName === 'label' || tagName === 'span') &&
                            (el.innerText || '').toLowerCase().includes('cash on delivery')) {
                            return 'button';
                        }

                        // Interactive elements detection (improved)
                        if ((tagName === 'div' || tagName === 'span')) {
                            if (el.onclick || el.getAttribute('onclick')) return 'button';
                            if (window.getComputedStyle(el).cursor === 'pointer') return 'button';
                            if (el.getAttribute('tabindex') === '0') return 'button';
                            // Special case for payment selection - likely a clickable div/label
                            if (el.classList.contains('payment-option') ||
                                el.classList.contains('payment-method') ||
                                el.parentElement?.classList.contains('payment-methods')) {
                                return 'button';
                            }
                        }

                        return null;
                    }

                    // Enhanced function to get element text from all possible sources
                    function getElementText(el) {
                        // Check for actual content first (innerText is most reliable)
                        let text = normalizeText(el.innerText || '');

                        // If no innerText, try textContent (includes hidden text)
                        if (!text) text = normalizeText(el.textContent || '');

                        // For labels that are associated with inputs (common for payment methods)
                        if (el.tagName.toLowerCase() === 'label') {
                            const forId = el.getAttribute('for');
                            if (forId) {
                                const input = document.getElementById(forId);
                                if (input && input.value) {
                                    text = normalizeText(text + ' ' + input.value);
                                }
                            }
                        }

                        // For elements without visible text, check attributes
                        if (!text) {
                            // Check all possible text attributes in priority order
                            text = normalizeText(
                                el.getAttribute('aria-label') ||
                                el.getAttribute('placeholder') ||
                                el.getAttribute('value') ||
                                el.getAttribute('title') ||
                                el.getAttribute('name') ||
                                el.getAttribute('alt') ||
                                el.id || ''
                            );
                        }

                        // Special case for payment elements with images
                        if (!text && (el.classList.contains('payment-option') || el.parentElement?.classList.contains('payment-methods'))) {
                            // Look for images with alt text inside the element
                            const images = el.querySelectorAll('img[alt]');
                            for (const img of images) {
                                const altText = img.getAttribute('alt');
                                if (altText) text = normalizeText(altText);
                            }
                        }

                        return text;
                    }

                    // Generate a unique CSS selector for an element
                    function generateSelector(el) {
                        if (!el) return '';
                        if (el.id) return '#' + CSS.escape(el.id);

                        let selector = el.tagName.toLowerCase();

                        // Add classes (up to 2 for specificity without being too specific)
                        if (el.classList && el.classList.length) {
                            const classes = Array.from(el.classList).slice(0, 2);
                            selector += '.' + classes.join('.');
                        }

                        // Add common attributes that help identification
                        ['type', 'name', 'placeholder', 'role'].forEach(attr => {
                            if (el.hasAttribute(attr)) {
                                selector += `[${attr}="${CSS.escape(el.getAttribute(attr))}"]`;
                            }
                        });

                        return selector;
                    }

                    // Generate XPath for element (useful for rare edge cases)
                    function getXPath(el) {
                        if (!el) return '';

                        const parts = [];
                        let current = el;

                        while (current && current.nodeType === Node.ELEMENT_NODE) {
                            let idx = 0;
                            let sibling = current.previousSibling;

                            while (sibling) {
                                if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === current.tagName) {
                                    idx++;
                                }
                                sibling = sibling.previousSibling;
                            }

                            const tagName = current.tagName.toLowerCase();
                            let idxStr = '';

                            if (idx > 0 || current.nextSibling && current.nextSibling.nodeType === Node.ELEMENT_NODE &&
                                current.nextSibling.tagName === current.tagName) {
                                idxStr = `[${idx + 1}]`;
                            }

                            parts.unshift(tagName + idxStr);
                            current = current.parentNode;

                            // Limit XPath length to avoid extremely long paths
                            if (parts.length >= 8) {
                                parts.unshift('...');
                                break;
                            }
                        }

                        return '/' + parts.join('/');
                    }

                    // Extract important attributes from element
                    function getElementAttributes(el) {
                        if (!el) return {};

                        const result = {};
                        const importantAttrs = [
                            'id', 'class', 'name', 'type', 'role', 'aria-label', 'href',
                            'value', 'placeholder', 'for', 'title', 'alt', 'data-testid'
                        ];

                        importantAttrs.forEach(attr => {
                            if (el.hasAttribute(attr)) {
                                result[attr] = el.getAttribute(attr);
                            }
                        });

                        // Add any data-* attributes
                        for (let i = 0; i < el.attributes.length; i++) {
                            const attr = el.attributes[i];
                            if (attr.name.startsWith('data-') && !result[attr.name]) {
                                result[attr.name] = attr.value;
                            }
                        }

                        return result;
                    }

                    // Get parent information for context
                    function getParentInfo(el) {
                        if (!el || !el.parentElement) return null;

                        const parent = el.parentElement;
                        return {
                            tagName: parent.tagName.toLowerCase(),
                            id: parent.id || '',
                            className: parent.className || '',
                            text: normalizeText(parent.innerText || '').substring(0, 50)
                        };
                    }

                    // Look for child elements with matching text
                    function findTextInChildren(el, targetDesc) {
                        const normalizedTarget = normalizeText(targetDesc);
                        let foundText = '';

                        // Check all child nodes recursively
                        function checkNode(node) {
                            if (node.nodeType === Node.TEXT_NODE) {
                                const nodeText = normalizeText(node.textContent);
                                if (nodeText.includes(normalizedTarget)) {
                                    foundText = nodeText;
                                    return true;
                                }
                            } else if (node.nodeType === Node.ELEMENT_NODE) {
                                // Check this element's text
                                const elText = normalizeText(node.innerText || node.textContent || '');
                                if (elText.includes(normalizedTarget)) {
                                    foundText = elText;
                                    return true;
                                }

                                // Check child elements
                                for (const child of node.childNodes) {
                                    if (checkNode(child)) return true;
                                }
                            }
                            return false;
                        }

                        checkNode(el);
                        return foundText;
                    }

                    // Element scoring with improved algorithm
                    function scoreElement(el, elementType, elementText) {
                        if (!isVisible(el)) return 0;
                        if (!elementType) return 0;

                        const targetDesc = normalizeText(isStructured ? targetText || '' : targetText || '');
                        if (!targetDesc && !targetType) return 0;

                        // Skip elements with no text unless they're the right type and we're in relaxed mode
                        if (!elementText && !relaxed) return 0;

                        let score = 0;

                        // Type matching (30% of scoring weight)
                        if (targetType) {
                            if (elementType === targetType) {
                                score += 150; // Exact type match
                            }
                            else if (relaxed && (elementType.includes(targetType) || targetType.includes(elementType))) {
                                score += 40; // Partial type match when relaxed
                            }
                            else if (!relaxed) {
                                return 0; // No match on type when not relaxed
                            }
                        }

                        // Text matching (70% of scoring weight)
                        if (targetDesc) {
                            // Reject empty text elements if target has text
                            if (!elementText && targetDesc) {
                                if (relaxed) {
                                    // Check text in children
                                    const childText = findTextInChildren(el, targetDesc);
                                    if (!childText) return 0;
                                    elementText = childText;
                                } else {
                                    return 0;
                                }
                            }

                            // Exact match - highest priority
                            if (elementText === targetDesc) {
                                score += 450; // Increased priority for exact match
                            }
                            // Full match with case/whitespace differences
                            else if (elementText.replace(/[^a-z0-9]/gi, '') === targetDesc.replace(/[^a-z0-9]/gi, '')) {
                                score += 400;
                            }
                            // Element contains target text completely
                            else if (elementText.includes(targetDesc)) {
                                // Prioritize by precision of match
                                const precision = targetDesc.length / elementText.length;
                                score += Math.round(300 * precision);
                            }
                            // Special case for composite texts like "Cash on Delivery/Pay on Delivery"
                            else if (targetDesc.includes('/')) {
                                const targetParts = targetDesc.split('/');
                                for (const part of targetParts) {
                                    if (part.length > 3 && elementText.includes(part)) {
                                        const precision = part.length / elementText.length;
                                        score += Math.round(200 * precision);
                                    }
                                }
                            }
                            // Target contains element text (if element text is substantial)
                            else if (targetDesc.includes(elementText) && elementText.length > 3) {
                                const coverage = elementText.length / targetDesc.length;
                                score += Math.round(100 * coverage);
                            }
                            // Word matching (for partial matches)
                            else if (relaxed || targetDesc.length > 15) {
                                const targetWords = targetDesc.split(' ');
                                const elementWords = elementText.split(' ');

                                let matchCount = 0;
                                for (const word of targetWords) {
                                    if (word.length > 2 &&
                                        elementWords.some(w => w.includes(word) || word.includes(w))) {
                                        matchCount++;
                                    }
                                }

                                score += matchCount * (relaxed ? 15 : 25);
                            }
                        }

                        // Boost for elements in viewport (accessibility bonus)
                        const rect = el.getBoundingClientRect();
                        const inViewport = (
                            rect.top >= 0 &&
                            rect.left >= 0 &&
                            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
                        );

                        if (inViewport) {
                            score += 25; // Visible elements are preferred
                        }

                        // Penalty for elements at the top-left corner (likely navigation elements, not content)
                        if (rect.top < 50 && rect.left < 50) {
                            score -= 50;
                        }

                        // Extra penalty for empty text
                        if (!elementText) {
                            score -= 100;
                        }

                        return score;
                    }

                    // Find all elements and evaluate them
                    const candidates = [];
                    const allElements = document.querySelectorAll('*');

                    allElements.forEach(el => {
                        const elementType = getElementType(el);
                        if (!elementType) return; // Skip non-interactive elements

                        // Skip disabled elements unless explicitly requested
                        if (el.disabled && !targetText?.includes('disabled')) return;

                        const elementText = getElementText(el);

                        // Calculate match score
                        const score = scoreElement(el, elementType, elementText);

                        // Only include elements with some match
                        if (score > 0) {
                            const rect = el.getBoundingClientRect();

                            candidates.push({
                                score: score,
                                tagName: el.tagName,
                                type: elementType,
                                text: elementText.substring(0, 100), // Limit text length
                                x: rect.left + window.pageXOffset,
                                y: rect.top + window.pageYOffset,
                                width: rect.width,
                                height: rect.height,
                                center_x: rect.left + rect.width/2 + window.pageXOffset,
                                center_y: rect.top + rect.height/2 + window.pageYOffset,
                                inViewport: rect.top >= 0 && rect.left >= 0 &&
                                        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                                        rect.right <= (window.innerWidth || document.documentElement.clientWidth),
                                // Enhanced element identification
                                attributes: getElementAttributes(el),
                                cssSelector: generateSelector(el),
                                xpath: getXPath(el),
                                parentInfo: getParentInfo(el),
                                innerHTML: el.innerHTML.substring(0, 200), // Limited for size
                                childElementCount: el.childElementCount,
                                isDisabled: el.disabled || el.hasAttribute('disabled') || el.getAttribute('aria-disabled') === 'true',
                                zIndex: parseInt(window.getComputedStyle(el).zIndex) || 0
                            });
                        }
                    });

                    // Sort candidates by score (highest first)
                    candidates.sort((a, b) => b.score - a.score);

                    // Include top candidates for debugging
                    const alternatives = candidates.slice(1, 4).map(c => ({
                        text: c.text,
                        type: c.type,
                        score: c.score,
                        cssSelector: c.cssSelector
                    }));

                    // Return best match with debug info
                    return candidates.length > 0 ? {...candidates[0], alternatives} : null;
                }
            """

            free_text = None if is_structured else (target_text or target_description or "")
            return self.page.evaluate(js_code, {
                "targetType": target_type,
                "targetText": target_text if is_structured else free_text,
                "isStructured": is_structured,
                "relaxed": relaxed
            })

    def _scroll_to_element(self, element):
        """
        Scroll element into the center of viewport and return updated coordinates.

        Args:
            element (dict): Element information with at least center_x, center_y,
                        tagName, and text properties

        Returns:
            tuple: Updated (x, y) coordinates of the element after scrolling
        """
        print(f"Scrolling element into viewport: {element.get('type', 'unknown')} - '{element.get('text', '')}'")

        # Get initial coordinates
        x, y = element['center_x'], element['center_y']

        # Check if element is already in viewport
        in_viewport = self.page.evaluate("""
            ({x, y}) => {
                const viewport = {
                    top: window.pageYOffset,
                    left: window.pageXOffset,
                    bottom: window.pageYOffset + window.innerHeight,
                    right: window.pageXOffset + window.innerWidth
                };
                return (
                    x >= viewport.left &&
                    x <= viewport.right &&
                    y >= viewport.top &&
                    y <= viewport.bottom
                );
            }
        """, {"x": x, "y": y})

        if in_viewport:
            print("Element is already in viewport")
            return x, y

        print(f"Element is not in viewport, scrolling to it...")

        # Store element identification for finding it after scrolling
        element_id = {
            'tagName': element['tagName'],
            'text': element.get('text', ''),
            'cssSelector': element.get('cssSelector', '')
        }

        try:
            # Scroll element into view - center it in the viewport
            self.page.evaluate("""
                ({x, y}) => {
                    window.scrollTo({
                        left: x - (window.innerWidth / 2),
                        top: y - (window.innerHeight / 2),
                        behavior: 'smooth'
                    });
                }
            """, {"x": x, "y": y})

            # Wait for scroll to complete
            time.sleep(1.0)

            # Re-check element position after scrolling to get accurate coordinates
            element_coords = self.page.evaluate("""
                ({x, y, tagName, text, cssSelector}) => {
                    // Try to find element at the original point
                    let el = null;

                    // First try by point
                    const viewX = x - window.pageXOffset;
                    const viewY = y - window.pageYOffset;

                    if (viewX >= 0 && viewX <= window.innerWidth &&
                        viewY >= 0 && viewY <= window.innerHeight) {
                        el = document.elementFromPoint(viewX, viewY);
                    }

                    // If element not found by point, try CSS selector
                    if (!el && cssSelector) {
                        try {
                            el = document.querySelector(cssSelector);
                        } catch (e) {}
                    }

                    // If still not found, try finding by tag and text
                    if (!el && tagName && text) {
                        const elements = document.querySelectorAll(tagName);
                        const lowerText = text.toLowerCase();

                        for (const element of elements) {
                            const content = (element.innerText || element.textContent ||
                                        element.getAttribute('value') ||
                                        element.getAttribute('placeholder') || '').toLowerCase();

                            if (content.includes(lowerText)) {
                                el = element;
                                break;
                            }
                        }
                    }

                    // If element found, return its actual coordinates
                    if (el) {
                        const rect = el.getBoundingClientRect();
                        return {
                            x: rect.left + rect.width/2 + window.pageXOffset,
                            y: rect.top + rect.height/2 + window.pageYOffset,
                            found: true,
                            inViewport: (
                                rect.top >= 0 &&
                                rect.left >= 0 &&
                                rect.bottom <= window.innerHeight &&
                                rect.right <= window.innerWidth
                            )
                        };
                    }

                    return {
                        x: x,
                        y: y,
                        found: false
                    };
                }
            """, {"x": x, "y": y, "tagName": element['tagName'], "text": element.get('text', ''), "cssSelector": element.get('cssSelector', '')})

            if element_coords.get('found', False):
                x = element_coords['x']
                y = element_coords['y']
                print(f"Updated element coordinates to ({x}, {y}) after scrolling")

                # If element is still not fully in viewport, make additional adjustment
                if not element_coords.get('inViewport', False):
                    print("Element not fully in viewport, making additional adjustment...")

                    self.page.evaluate("""
                        ({x, y}) => {
                            // Calculate adjustment to center element
                            const viewX = x - window.pageXOffset;
                            const viewY = y - window.pageYOffset;
                            const offsetX = window.innerWidth/2 - viewX;
                            const offsetY = window.innerHeight/2 - viewY;

                            // Apply adjustment
                            window.scrollBy({
                                left: -offsetX,
                                top: -offsetY,
                                behavior: 'smooth'
                            });
                        }
                    """, {"x": x, "y": y})

                    # Wait for final adjustment
                    time.sleep(0.7)

                    # Get final position
                    final_coords = self.page.evaluate("""
                        ({tagName, text}) => {
                            // Try to find the element by tag and text
                            const elements = document.querySelectorAll(tagName);
                            const lowerText = text.toLowerCase();

                            for (const el of elements) {
                                const content = (el.innerText || el.textContent ||
                                            el.getAttribute('value') ||
                                            el.getAttribute('placeholder') || '').toLowerCase();

                                if (content.includes(lowerText)) {
                                    const rect = el.getBoundingClientRect();
                                    return {
                                        x: rect.left + rect.width/2 + window.pageXOffset,
                                        y: rect.top + rect.height/2 + window.pageYOffset,
                                        found: true
                                    };
                                }
                            }

                            return { found: false };
                        }
                    """, {"tagName": element['tagName'], "text": element.get('text', '')})

                    if final_coords.get('found', False):
                        x = final_coords['x']
                        y = final_coords['y']
                        print(f"Final coordinates after adjustment: ({x}, {y})")
            else:
                print("Element not found after scrolling, using original coordinates")

        except Exception as e:
            print(f"Error during scroll: {e}")
            # Fall back to original coordinates on error

        return x, y


    def _perform_click(self, x, y, element_info):
        """Perform click at coordinates with appropriate handling for element type and navigation."""
        # Move mouse to element
        print(f"Moving mouse to element at ({x}, {y})")
        self._natural_mouse_move(x, y)
        time.sleep(0.3)

        # Get information about the element before clicking
        element_type = element_info['type']
        is_navigation_expected = (element_type == 'link' or
                                element_info.get('tagName', '').lower() == 'a' or
                                'href' in element_info.get('attributes', {}))

        try:
            self._virtual_click(x, y)
                # Return success message
            return f"Clicked on element: {element_type} with text '{element_info['text']}'"
        except Exception as e:
            print(f"Error during click operation: {e}")
            # Still perform the physical click as a last resort
            self._virtual_click(x, y)
            return f"Click attempted with errors: {str(e)}"

    def keyboard_action(self, input_text):
        """Handle keyboard actions including typing text and pressing special keys."""
        try:
            # Check if this is a special key command
            special_keys = {
                # Basic navigation keys
                "enter": "Enter",
                "tab": "Tab",
                "shift+tab": "Shift+Tab",
                "backspace": "Backspace",
                "escape": "Escape", "esc": "Escape",
                "delete": "Delete", "del": "Delete",
                "space": " ",

                # Arrow keys
                "up": "ArrowUp",
                "down": "ArrowDown",
                "left": "ArrowLeft",
                "right": "ArrowRight",

                # Common shortcuts
                "ctrl+a": "Control+a", "cmd+a": "Meta+a",
                "ctrl+c": "Control+c", "cmd+c": "Meta+c",
                "ctrl+v": "Control+v", "cmd+v": "Meta+v",
                "ctrl+x": "Control+x", "cmd+x": "Meta+x",
                "ctrl+z": "Control+z", "cmd+z": "Meta+z",
                "ctrl+y": "Control+y", "cmd+y": "Meta+y",
                "ctrl+f": "Control+f", "cmd+f": "Meta+f",

                # Function keys
                "f1": "F1", "f2": "F2", "f3": "F3", "f4": "F4",
                "f5": "F5", "f6": "F6", "f7": "F7", "f8": "F8",
                "f9": "F9", "f10": "F10", "f11": "F11", "f12": "F12",

                # Navigation shortcuts
                "home": "Home",
                "end": "End",
                "pageup": "PageUp",
                "pagedown": "PageDown",

                # Special combinations
                "alt+tab": "Alt+Tab",
                "ctrl+enter": "Control+Enter", "cmd+enter": "Meta+Enter",
                "ctrl+home": "Control+Home", "cmd+home": "Meta+Home",
                "ctrl+end": "Control+End", "cmd+end": "Meta+End",

                # Web-specific
                "ctrl+t": "Control+t", "cmd+t": "Meta+t",  # New tab
                "ctrl+w": "Control+w", "cmd+w": "Meta+w",  # Close tab
                "ctrl+r": "Control+r", "cmd+r": "Meta+r",  # Reload
            }

            # Clean input
            if isinstance(input_text, str):
                input_text = input_text.strip("'\"").strip()

            # Handle multiple key sequence if separated by commas or semicolons
            if "," in input_text or ";" in input_text:
                key_sequence = re.split(r'[,;]', input_text)
                results = []

                for single_key in key_sequence:
                    single_key = single_key.strip().lower()
                    result = self._execute_single_key_action(single_key, special_keys)
                    results.append(result)
                    time.sleep(0.3)  # Brief pause between keys

                return "Executed key sequence: " + " → ".join(results)
            else:
                # Single key/text handling
                normalized_input = input_text.lower()
                return self._execute_single_key_action(normalized_input, special_keys)

        except Exception as e:
            return f"Error with keyboard action: {str(e)}"

    def _execute_single_key_action(self, key_input, special_keys):
        """Execute a single key action (helper for keyboard_action)."""
        if key_input in special_keys:
            key = special_keys[key_input]
            print(f"Pressing special key: {key}")
            time.sleep(0.2)

            # Handle special case for space
            if key == " ":
                self.page.keyboard.press("Space")
            else:
                self.page.keyboard.press(key)

            time.sleep(0.3)
            return f"Pressed {key_input}"

        # Handle hold-and-press patterns like "hold shift, press tab"
        hold_match = re.match(r'hold\s+(\w+),?\s+(?:press\s+)?(\w+)', key_input)
        if hold_match:
            modifier, key = hold_match.groups()
            modifier_key = special_keys.get(modifier.lower(), modifier.capitalize())
            key_to_press = special_keys.get(key.lower(), key.capitalize())

            print(f"Holding {modifier_key} and pressing {key_to_press}")
            self.page.keyboard.down(modifier_key)
            time.sleep(0.3)
            self.page.keyboard.press(key_to_press)
            time.sleep(0.2)
            self.page.keyboard.up(modifier_key)

            return f"Held {modifier} and pressed {key}"

        # Otherwise treat as text to type
        self._virtual_type(key_input)
        return f"Typed '{key_input}'"


    def go_back(self):
        """Navigate back to the previous page in browser history."""
        try:
            # Store current URL to verify navigation
            current_url = self.page.url

            # Check if we can go back
            can_go_back = self.page.evaluate("() => window.history.length > 1")

            if not can_go_back:
                return "Cannot go back - no previous page in history"

            print("Navigating back to previous page...")

            # Try using browser back button first (most reliable)
            self.page.go_back(wait_until="domcontentloaded", timeout=10000)

            # Wait for navigation to complete
            time.sleep(1.5)

            # Verify we actually navigated to a different page
            new_url = self.page.url
            if new_url == current_url:
                # If URL didn't change, try alternative method
                print("Back navigation didn't change URL, trying alternative method...")
                self.page.evaluate("() => window.history.back()")
                time.sleep(1.5)
                new_url = self.page.url

            # Final verification
            if new_url != current_url:
                print(f"Successfully navigated back to: {new_url}")
                return f"Navigated back to previous page: {new_url}"
            else:
                return "Back navigation attempted but URL remains unchanged"

        except Exception as e:
            print(f"Error navigating back: {str(e)}")
            return f"Error navigating back: {str(e)}"

    def navigate(self, url):
        """
        Navigate to a URL using direct navigation.
        """
        try:
            # Clean the URL - remove backticks and other formatting characters
            url = url.replace('`', '').strip()

            # Handle cases with duplicate protocol prefixes
            if url.count('http') > 1:
                # Find the last occurrence of http:// or https://
                last_http_index = max(url.rfind('http://'), url.rfind('https://'))
                if last_http_index >= 0:
                    url = url[last_http_index:]

            # Ensure URL has a protocol
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url

            print(f"Attempting to navigate to: {url}")

            # STEP 1: Direct navigation attempt
            try:
                print(f"Trying direct navigation to {url}")
                self.page.goto(url, timeout=20000)
                current_url = self.page.url

                # Check if navigation was successful
                if not (current_url.startswith("http") and not "about:blank" in current_url):
                    raise Exception("Direct navigation not successful")

                print(f"Direct navigation successful, now at: {current_url}")
                return f"Navigated to {url} - Current page: {current_url}"

            except Exception as direct_nav_error:
                print(f"Direct navigation failed: {direct_nav_error}")

        except Exception as e:
            print(f"Critical navigation error: {e}")
            return f"Error navigating to {url}: {str(e)}"


    def scroll(self, direction="down"):
        """Scroll the page with visible virtual mouse wheel movement."""
        try:
            # Clean input and handle quoted strings
            if isinstance(direction, str):
                direction = direction.lower().strip("'\"").strip()

            # Get viewport size with fallback
            viewport = self.page.viewport_size

            # Check if viewport is valid before accessing its properties
            if viewport is None:
                # Fallback to direct JavaScript scrolling when viewport size can't be determined
                if direction == "down":
                    self.page.evaluate("window.scrollBy(0, 300)")
                    return "Scrolled down (fallback method)"
                elif direction == "up":
                    self.page.evaluate("window.scrollBy(0, -300)")
                    return "Scrolled up (fallback method)"
                elif direction == "top":
                    self.page.evaluate("window.scrollTo(0, 0)")
                    return "Scrolled to top"
                elif direction == "bottom":
                    self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    return "Scrolled to bottom"
                else:
                    self.page.evaluate("window.scrollBy(0, 300)")
                    return f"Invalid direction '{direction}', defaulted to scrolling down"

            # If viewport is valid, use normal mouse wheel movement
            center_x = viewport["width"] / 2
            center_y = viewport["height"] / 2
            self._natural_mouse_move(center_x, center_y)
            time.sleep(0.3)

            # Determine scroll amount and direction
            if direction == "down":
                # Scroll gradually
                for _ in range(3):
                    self.page.mouse.wheel(0, 100)
                    time.sleep(random.uniform(0.2, 0.4))
                return "Scrolled down"
            elif direction == "up":
                # Scroll gradually
                for _ in range(3):
                    self.page.mouse.wheel(0, -100)
                    time.sleep(random.uniform(0.2, 0.4))
                return "Scrolled up"
            elif direction == "top":
                # Go to top
                self.page.evaluate("window.scrollTo(0, 0)")
                return "Scrolled to top"
            elif direction == "bottom":
                # Go to bottom
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                return "Scrolled to bottom"
            else:
                # Default to scrolling down if invalid input
                for _ in range(3):
                    self.page.mouse.wheel(0, 100)
                    time.sleep(random.uniform(0.2, 0.4))
                return f"Invalid direction '{direction}', defaulted to scrolling down"
        except Exception as e:
            # Add more detailed error information for debugging
            print(f"Scroll error details: {e}")

            # Last resort fallback if any part of the scroll handling fails
            try:
                # Try the simplest possible scrolling method
                self.page.evaluate(f"""
                    () => {{
                        if ('{direction}' === 'top') window.scrollTo(0, 0);
                        else if ('{direction}' === 'bottom') window.scrollTo(0, document.body.scrollHeight);
                        else if ('{direction}' === 'up') window.scrollBy(0, -300);
                        else window.scrollBy(0, 300);
                    }}
                """)
                return f"Emergency scroll fallback used for direction: {direction}"
            except Exception as fallback_error:
                return f"Error scrolling: {str(e)} - Fallback also failed: {str(fallback_error)}"


    def search_for(self, query):
        """Execute a search query using virtual mouse and keyboard."""
        try:
            # First check if we're on a search engine
            current_url = self.page.url.lower()

            if "google" in current_url:
                # On Google, look for the search box
                search_box = self.page.query_selector('input[name="q"], [aria-label="Search"]')
                if search_box:
                    box = search_box.bounding_box()
                    self._natural_mouse_move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                    time.sleep(0.3)
                    self._virtual_click()
                    time.sleep(0.5)

                    # Clear existing text
                    self.page.keyboard.press("Control+A")
                    self.page.keyboard.press("Delete")
                    time.sleep(0.3)

                    # Type query with realistic timing
                    self._virtual_type(query)
                    time.sleep(0.5)
                    self.page.keyboard.press("Enter")
                    time.sleep(2)  # Wait for results to load

                    return f"Searched for '{query}' on Google"
                else:
                    return "Could not find Google search box"

            # If not on Google, navigate there first
            self.navigate("https://www.google.com")
            time.sleep(2)

            # Now search
            search_box = self.page.query_selector('input[name="q"], [aria-label="Search"]')
            if search_box:
                box = search_box.bounding_box()
                self._natural_mouse_move(box["x"] + box["width"]/2, box["y"] + box["height"]/2)
                time.sleep(0.3)
                self._virtual_click()
                time.sleep(0.5)

                # Type query with realistic timing
                self._virtual_type(query)
                time.sleep(0.5)
                self.page.keyboard.press("Enter")
                time.sleep(2)  # Wait for results to load

                return f"Navigated to Google and searched for '{query}'"
            else:
                return "Could not find Google search box after navigation"
        except Exception as e:
            return f"Error during search: {str(e)}"


    def close(self):
        """Close the browser cleanly."""
        try:
            self.page.context.browser.close()
            return "Browser closed successfully"
        except Exception as e:
            return f"Error closing browser: {str(e)}"

    # Helper methods
    def _virtual_click(self, x, y):
        """Click with the virtual cursor."""
        virtual_click(self.page, x, y)

    def _virtual_type(self, text):
        """Type text character by character with realistic timing."""
        virtual_type(self.page, text)

    def _natural_mouse_move(self, target_x, target_y):
        """Move the virtual mouse in a natural way, simulating human movement."""
        # Get starting position
        start_x = self.current_x
        start_y = self.current_y

        # Get path points
        path_points = natural_mouse_move(
            self.page, start_x, start_y, target_x, target_y
        )

        # Execute the movement
        for x, y in path_points:
            self._update_cursor(x, y)

            # Slight delay between movements with variable timing
            time.sleep(0.01 + random.uniform(0, 0.02))

            # Occasionally pause briefly (simulating human hesitation)
            if random.random() < 0.05:  # 5% chance
                time.sleep(random.uniform(0.1, 0.3))

        # Update final position
        self.current_x = target_x
        self.current_y = target_y

    def _update_cursor(self, x, y):
        """Update the virtual cursor position."""
        self.current_x = x
        self.current_y = y
        update_cursor(self.page, x, y)

    def _handle_new_tab(self, popup):
        """Handle new tab popup events by getting URL and navigating in main tab instead."""
        try:
            # Wait briefly for the popup to initialize
            time.sleep(0.5)
            # Get the URL of the popup
            popup_url = popup.url
            if popup_url and popup_url != "about:blank":
                # Close the popup
                popup.close()
                # Navigate the main page to that URL instead
                self.page.goto(popup_url)
                print(f"Redirected popup to main tab: {popup_url}")
        except Exception as e:
            print(f"Error handling popup: {e}")
            # Try to close the popup anyway
            try:
                popup.close()
            except:
                pass

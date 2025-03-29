import random
import time

def natural_mouse_move(page, current_x, current_y, target_x, target_y):
    """Move the virtual mouse in a natural way, simulating human movement."""
    # Calculate distance
    distance = ((target_x - current_x) ** 2 + (target_y - current_y) ** 2) ** 0.5
    
    # More points for longer distances
    steps = min(max(int(distance / 50), 5), 25)
    
    # Create a slightly curved path with bezier curve simulation
    control_x = (current_x + target_x) / 2 + random.uniform(-50, 50)
    control_y = (current_y + target_y) / 2 + random.uniform(-50, 50)
    
    # Calculate and return path points
    path_points = []
    for i in range(steps + 1):
        t = i / steps
        # Quadratic bezier curve
        x = (1-t)**2 * current_x + 2*(1-t)*t * control_x + t**2 * target_x
        y = (1-t)**2 * current_y + 2*(1-t)*t * control_y + t**2 * target_y
        path_points.append((x, y))
    
    return path_points

def update_cursor(page, x, y):
    """Update the virtual cursor position in the browser."""
    # Update cursor visually in browser
    page.evaluate(f"window.updateAICursor({x}, {y})")
    # Also update the actual Playwright mouse position (but not the system cursor)
    page.mouse.move(x, y)

def virtual_click(page, current_x, current_y):
    """Click with the virtual cursor."""
    # Change cursor appearance to indicate clicking
    page.evaluate("""
        () => {
            const cursor = document.getElementById('ai-agent-cursor');
            if (cursor) {
                cursor.style.backgroundColor = 'rgba(255, 0, 0, 0.5)';
                setTimeout(() => {
                    cursor.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
                }, 200);
            }
        }
    """)

    # Execute DOM click via JavaScript with special handling for input fields
    click_result = page.evaluate("""
        ({x, y}) => {
            // Calculate viewport-relative coordinates
            const viewX = x - window.pageXOffset;
            const viewY = y - window.pageYOffset;
            
            // Find the element at those coordinates
            const element = document.elementFromPoint(viewX, viewY);
            
            if (!element) {
                console.log('No element found at coordinates', viewX, viewY);
                return {success: false, reason: 'No element found'};
            }
            
            console.log('Found element to click:', element.tagName, element.id, element.className);
            
            // Special handling for input fields to ensure focus
            if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA' || element.tagName === 'SELECT') {
                // Focus + click sequence for input fields
                try {
                    // Try multiple approaches for maximum compatibility
                    element.focus();
                    element.click();
                    
                    // Force focus with mousedown/mouseup events
                    const mouseDown = new MouseEvent('mousedown', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    element.dispatchEvent(mouseDown);
                    
                    const mouseUp = new MouseEvent('mouseup', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    });
                    element.dispatchEvent(mouseUp);
                    
                    // Force selection of input text if present
                    if (element.value) {
                        element.select();
                    }
                    
                    // Ensure element is focused
                    if (document.activeElement !== element) {
                        element.focus();
                    }
                    
                    return {
                        success: true,
                        tagName: element.tagName,
                        id: element.id || '(no id)',
                        className: element.className || '(no class)',
                        inputFocused: true
                    };
                } catch (e) {
                    console.error('Input focus error:', e);
                }
            }
            
            // Standard click for non-input elements
            element.click();
            
            return {
                success: true,
                tagName: element.tagName,
                id: element.id || '(no id)',
                className: element.className || '(no class)'
            };
        }
    """, {"x": current_x, "y": current_y})
    
    print(f"DOM click result: {click_result}")
    time.sleep(0.3)  # Wait for click to register

def virtual_type(page, text):
    """Type text character by character with realistic timing."""
    for char in text:
        # Different delay based on character type
        if char in ['.', ',', '!', '?']:
            delay = random.uniform(0.1, 0.3)  # Longer pause after punctuation
        elif char == ' ':
            delay = random.uniform(0.05, 0.15)  # Medium pause for spaces
        else:
            delay = random.uniform(0.03, 0.1)  # Normal typing speed
        
        # Type the correct character
        page.keyboard.type(char)
        time.sleep(delay)
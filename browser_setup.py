from playwright.sync_api import sync_playwright

def inject_cursor_script():
    """Returns the script to inject for cursor visualization"""
    return """
    // Create a custom cursor element
    const cursor = document.createElement('div');
    cursor.id = 'ai-agent-cursor';
    cursor.style.position = 'absolute';
    cursor.style.width = '20px';
    cursor.style.height = '20px';
    cursor.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
    cursor.style.border = '2px solid red';
    cursor.style.borderRadius = '50%';
    cursor.style.transform = 'translate(-50%, -50%)';
    cursor.style.pointerEvents = 'none';
    cursor.style.zIndex = '999999';
    cursor.style.transition = 'left 0.1s, top 0.1s';
    
    // Add cursor to the page when it loads
    document.addEventListener('DOMContentLoaded', function() {
        document.body.appendChild(cursor);
    });
    
    // If page already loaded, add cursor now
    if (document.body) {
        document.body.appendChild(cursor);
    }
    
    // Function to update cursor position
    window.updateAICursor = function(x, y) {
        if (cursor && document.body && document.body.contains(cursor)) {
            cursor.style.left = x + 'px';
            cursor.style.top = y + 'px';
        } else if (document.body) {
            document.body.appendChild(cursor);
            cursor.style.left = x + 'px';
            cursor.style.top = y + 'px';
        }
    };
    """

def initialize_browser(options, connection_options=None):
    """Initialize the browser by connecting to existing instance or launching a new one."""
    playwright = sync_playwright().start()
    
    # Default connection options if none provided
    if connection_options is None:
        connection_options = {
            "use_existing": True,
            "cdp_endpoint": "http://localhost:9222",
            "fallback_to_new": True
        }
    
    browser = None
    page = None
    
    # Try connecting to existing browser if requested
    if connection_options.get("use_existing", False):
        try:
            print(f"Attempting to connect to existing browser at {connection_options['cdp_endpoint']}...")
            browser = playwright.chromium.connect_over_cdp(connection_options["cdp_endpoint"])
            print("Successfully connected to existing Chrome browser")
            
            # Get the default context or create a new one
            if (len(browser.contexts) > 0):
                context = browser.contexts[0]
            else:
                context = browser.new_context(viewport=None)
                
            # Create a new page in the existing browser
            page = context.new_page()
            
        except Exception as e:
            print(f"Failed to connect to existing browser: {str(e)}")
            
            # Fall back to launching a new browser if configured to do so
            if not connection_options.get("fallback_to_new", True):
                print("Fallback disabled. Exiting.")
                raise e
                
            print("Falling back to launching a new browser instance...")
            browser = None  # Reset for fallback path
    
    # Launch a new browser if needed
    if browser is None:
        print(f"Launching new browser with options: {options}")
        browser = playwright.chromium.launch(**options)
        page = browser.new_page(viewport=None)
    
    # Shared initialization regardless of connection method
    # Inject cursor visualization CSS and JavaScript
    page.add_init_script(inject_cursor_script())
    
    # Add script to prevent new tabs from opening
    page.add_init_script("""
        window.open = function(url, name, features) {
            console.log('Intercepted window.open call for URL:', url);
            if (url) {
                window.location.href = url;
            }
            return window;
        };
        
        // Override link behavior to prevent target="_blank"
        document.addEventListener('click', function(e) {
            const link = e.target.closest('a');
            if (link && link.target === '_blank') {
                e.preventDefault();
                console.log('Intercepted _blank link click for URL:', link.href);
                window.location.href = link.href;
            }
        }, true);
    """)
    
    # Navigate to a blank page first to ensure script loading
    page.goto('about:blank')
    
    # Ensure cursor is created and function is available
    page.evaluate("""
        () => {
            // Create a custom cursor element if it doesn't exist
            if (!document.getElementById('ai-agent-cursor')) {
                const cursor = document.createElement('div');
                cursor.id = 'ai-agent-cursor';
                cursor.style.position = 'absolute';
                cursor.style.width = '20px';
                cursor.style.height = '20px';
                cursor.style.backgroundColor = 'rgba(255, 0, 0, 0.3)';
                cursor.style.border = '2px solid red';
                cursor.style.borderRadius = '50%';
                cursor.style.transform = 'translate(-50%, -50%)';
                cursor.style.pointerEvents = 'none';
                cursor.style.zIndex = '999999';
                cursor.style.transition = 'left 0.1s, top 0.1s';
                document.body.appendChild(cursor);
            }
            
            // Define the updateAICursor function if it doesn't exist
            if (typeof window.updateAICursor !== 'function') {
                window.updateAICursor = function(x, y) {
                    const cursor = document.getElementById('ai-agent-cursor');
                    if (cursor) {
                        cursor.style.left = x + 'px';
                        cursor.style.top = y + 'px';
                    } else {
                        console.error('Cursor element not found');
                    }
                };
            }
        }
    """)
    
    
    print(f"Browser setup successful. User agent: {page.evaluate('() => navigator.userAgent')}")
    
    return playwright, browser, page

def close_browser(playwright, browser, is_connected=False):
    """Close the browser cleanly."""
    try:
        if is_connected:
            # If connected to existing browser, just disconnect
            print("Disconnecting from browser (browser will remain open)")
            playwright.stop()
            return "Disconnected from browser successfully"
        else:
            # If browser was launched by us, close it
            browser.close()
            playwright.stop()
            return "Browser closed successfully"
    except Exception as e:
        return f"Error closing browser: {str(e)}"
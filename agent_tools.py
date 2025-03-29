from langchain.tools import Tool

def create_browser_tools(controller):
    """Create LangChain tools for browser automation."""

    return [
        Tool(
            name="Navigate",
            func=lambda url: controller.navigate(url.strip("'\"").strip()),
            description="Navigate to a URL with virtual mouse movement to address bar. Input: URL (string)."
        ),
        Tool(
            name="VisualClick",
            func=lambda desc: controller.visual_click(desc.strip("'\"").strip()),
            description=f"Click an element using visual analysis when regular DOM methods fail. Input: JSON object with element id, type and text, e.g. {{\"id\": \"5\", \"type\": \"button\", \"text\": \"add to cart\"}}. This helps target specific elements on the page with higher precision."
        ),
        Tool(
            name="AnalyzePage",
            func=lambda *args: controller.analyze_page(),
            description="Analyze the page's structure and content using DOM traversal. Returns a comprehensive structured report that includes: 1) Page metadata (title, URL), 2) Interactive elements organized by type with IDs and descriptions, and 3) Text content hierarchically organized by headings, paragraphs and other content types. The output is formatted for easy reading and reference. No input needed."
        ),
        Tool(
            name="Keyboard",
            func=lambda input_text: controller.keyboard_action(input_text),
            description="Perform keyboard actions including typing text, pressing special keys, and key combinations. Supports sequences using commas (e.g., 'tab, tab, enter'). Input can be text to type or special keys like 'enter', 'tab', 'backspace', 'escape', 'f1-f12', 'pageup', 'pagedown', 'home', 'end', and combinations like 'ctrl+a', 'shift+tab', 'ctrl+enter', etc. Mac users can use 'cmd+' instead of 'ctrl+'. Also supports 'hold shift, press tab' patterns."
        ),
        Tool(
            name="GoBack",
            func=lambda *args: controller.go_back(),
            description="Navigate back to the previous page in browser history. No input needed. Use this to return to the previous page after navigation."
        ),
        Tool(
            name="Scroll",
            func=lambda direction="down": controller.scroll(direction),
            description="Scroll the page with virtual mouse wheel. Input: direction ('up', 'down', 'top', or 'bottom')."
        ),
        Tool(
            name="GoogleSearch",
            func=lambda query: controller.search_for(query.strip("'\"").strip()),
            description="Execute a Google search query. Input: search query (string). Use this for searching on Google."
        ),
    ]

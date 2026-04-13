"""
ZenLink MCP Server
Exposes ZenLink browser automation as native MCP tools for Claude Desktop and other MCP clients.
Requires the ZenLink bridge (bridge.py) to be running on localhost:8765.

Install: pip install "mcp[cli]" httpx
"""

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ZenLink")
BRIDGE = "http://localhost:8765"


def _get(endpoint: str) -> dict:
    """GET request to bridge."""
    try:
        r = httpx.get(f"{BRIDGE}{endpoint}", timeout=15)
        return r.json()
    except httpx.ConnectError:
        return {"error": "ZenLink bridge not running. Start it with: python native/bridge.py"}
    except Exception as e:
        return {"error": str(e)}


def _post(endpoint: str, data: dict, timeout: float = 15) -> dict:
    """POST request to bridge."""
    try:
        r = httpx.post(f"{BRIDGE}{endpoint}", json=data, timeout=timeout)
        return r.json()
    except httpx.ConnectError:
        return {"error": "ZenLink bridge not running. Start it with: python native/bridge.py"}
    except Exception as e:
        return {"error": str(e)}


# -- Read Operations ----------------------------------------------

@mcp.tool()
def zen_status() -> dict:
    """Check if ZenLink bridge and browser extension are connected."""
    return _get("/api/status")


@mcp.tool()
def zen_tabs() -> dict:
    """List all open browser tabs with their IDs, titles, and URLs."""
    return _get("/api/tabs")


@mcp.tool()
def zen_page_info() -> dict:
    """Get current page URL, title, dimensions, and scroll position."""
    return _get("/api/page-info")


@mcp.tool()
def zen_page_text() -> dict:
    """Extract all readable text from the current page."""
    return _get("/api/page-text")


@mcp.tool()
def zen_page_text_by_tab_id(tab_id: int) -> dict:
    """Get page text from a specific tab by ID without switching to it.
    
    Args:
        tab_id: The tab ID to read from (get IDs from zen_tabs)
    
    Returns the full visible text content of the specified tab.
    """
    return _post("/api/page-text-by-tab-id", {"tabId": tab_id})


@mcp.tool()
def zen_forms() -> dict:
    """Get all form fields on the current page with their labels and values."""
    return _get("/api/forms")


@mcp.tool()
def zen_dom() -> dict:
    """Get the accessibility tree of interactive elements on the page."""
    return _get("/api/dom")


@mcp.tool()
def zen_screenshot() -> dict:
    """Capture a screenshot of the current page. Returns the saved file path."""
    return _get("/api/screenshot")


# -- Navigation ---------------------------------------------------

@mcp.tool()
def zen_navigate(url: str) -> dict:
    """Navigate the active tab to a URL.

    Args:
        url: The URL to navigate to (e.g. "https://example.com")
    """
    return _post("/api/navigate", {"url": url})


@mcp.tool()
def zen_new_tab(url: str = "about:blank") -> dict:
    """Open a new browser tab.

    Args:
        url: URL to open in the new tab (default: blank page)
    """
    return _post("/api/new-tab", {"url": url})


@mcp.tool()
def zen_close_tab(tab_id: int) -> dict:
    """Close a browser tab by its ID.

    Args:
        tab_id: The tab ID to close (get IDs from zen_tabs)
    """
    return _post("/api/close-tab", {"tabId": tab_id})


@mcp.tool()
def zen_switch_tab(tab_id: int) -> dict:
    """Switch focus to a specific browser tab.

    Args:
        tab_id: The tab ID to focus (get IDs from zen_tabs)
    """
    return _post("/api/switch-tab", {"tabId": tab_id})


# -- Interaction --------------------------------------------------

@mcp.tool()
def zen_click(selector: str = "", x: int = 0, y: int = 0) -> dict:
    """Click an element on the page by CSS selector or coordinates.

    Args:
        selector: CSS selector to click (e.g. "#submit", ".btn-primary")
        x: X coordinate (used if selector is empty)
        y: Y coordinate (used if selector is empty)
    """
    if selector:
        return _post("/api/click", {"selector": selector})
    return _post("/api/click", {"coords": {"x": x, "y": y}})


@mcp.tool()
def zen_type(selector: str, text: str, clear: bool = False) -> dict:
    """Type text into an input field.

    Args:
        selector: CSS selector of the input element
        text: Text to type
        clear: Whether to clear existing text first
    """
    return _post("/api/type", {"selector": selector, "text": text, "clear": clear})


@mcp.tool()
def zen_fill(selector: str, value: str) -> dict:
    """Set a form field's value directly (faster than typing).

    Args:
        selector: CSS selector of the input/select element
        value: Value to set
    """
    return _post("/api/fill", {"selector": selector, "value": value})


@mcp.tool()
def zen_scroll(direction: str = "down", amount: int = 500) -> dict:
    """Scroll the page.

    Args:
        direction: Scroll direction - "up", "down", "left", or "right"
        amount: Pixels to scroll
    """
    return _post("/api/scroll", {"direction": direction, "amount": amount})


@mcp.tool()
def zen_hover(selector: str) -> dict:
    """Hover over an element on the page.

    Args:
        selector: CSS selector of the element to hover over
    """
    return _post("/api/hover", {"selector": selector})


# -- Smart Queries ------------------------------------------------

@mcp.tool()
def zen_find(query: str) -> dict:
    """Find elements on the page using natural language description.

    Args:
        query: What to find (e.g. "login button", "search bar", "email input")
    """
    return _post("/api/find", {"query": query})


@mcp.tool()
def zen_js(code: str) -> dict:
    """Execute JavaScript in the current page context.

    Args:
        code: JavaScript code to run (e.g. "document.title" or "document.querySelectorAll('a').length")
    """
    return _post("/api/js", {"code": code})


@mcp.tool()
def zen_highlight(selector: str) -> dict:
    """Highlight an element on the page with a visual overlay.

    Args:
        selector: CSS selector of the element to highlight
    """
    return _post("/api/highlight", {"selector": selector})


# -- Wait ---------------------------------------------------------

@mcp.tool()
def zen_wait_for_element(selector: str, timeout: int = 10000, poll_interval: int = 200) -> dict:
    """Wait for a CSS selector to appear and become visible on the page.
    Returns immediately when the element is found, rather than sleeping a fixed duration.
    Use this instead of sleep when waiting for dynamic/JS-rendered content.

    Args:
        selector: CSS selector to wait for (e.g. ".tracking-events", "#results", "[data-loaded]")
        timeout: Maximum time to wait in milliseconds (default: 10000 = 10s)
        poll_interval: How often to check in milliseconds (default: 200ms)
    """
    timeout_s = (timeout / 1000) + 5  # extra buffer for HTTP round-trip
    return _post(
        "/api/wait-for-element",
        {"selector": selector, "timeout": timeout, "pollInterval": poll_interval},
        timeout=timeout_s,
    )


# -- WordPress / Elementor ----------------------------------------

@mcp.tool()
def zen_wp_html(site_url: str, page_id: int) -> dict:
    """Extract HTML widget content from a WordPress Elementor page.

    Navigates to the Elementor editor for the given page, waits for load,
    then extracts the innerHTML of all HTML widgets from the Elementor
    preview iframe. Returns clean HTML/CSS/JS content.

    The browser must already be logged into WP admin for this to work.

    Args:
        site_url: WordPress site URL (e.g. "https://thankyouexperiences.com")
        page_id: WordPress page/post ID (e.g. 5719 for Team page)
    """
    import time
    import json as _json

    url = f"{site_url.rstrip('/')}/wp-admin/post.php?post={page_id}&action=elementor"

    # Navigate to Elementor editor
    nav_result = _post("/api/navigate", {"url": url})
    if "error" in nav_result:
        return nav_result

    # Wait for Elementor to load
    time.sleep(6)

    # Extract HTML widget content from iframe
    js_code = """
    (function() {
        const iframe = document.querySelector('#elementor-preview-iframe');
        if (!iframe) return JSON.stringify({error: 'No Elementor preview iframe found.'});
        const iframeDoc = iframe.contentDocument || iframe.contentWindow.document;
        if (!iframeDoc) return JSON.stringify({error: 'Cannot access iframe document.'});
        const widgets = iframeDoc.querySelectorAll('[data-widget_type="html.default"]');
        if (widgets.length === 0) return JSON.stringify({error: 'No HTML widgets found on this page.'});
        const results = [];
        for (const widget of widgets) {
            const dataId = widget.getAttribute('data-id');
            const container = widget.querySelector('.elementor-html');
            const content = container ? container.innerHTML : widget.innerHTML;
            results.push({widget_id: dataId, content: content.trim()});
        }
        return JSON.stringify({ok: true, page_id: %PAGE_ID%, widget_count: results.length, widgets: results});
    })();
    """.replace("%PAGE_ID%", str(page_id))

    result = _post("/api/js", {"code": js_code})

    if "result" in result:
        try:
            parsed = _json.loads(result["result"])
            return parsed
        except (_json.JSONDecodeError, TypeError):
            return result
    return result

# -- Batch --------------------------------------------------------

@mcp.tool()
def zen_batch(commands: list[dict]) -> dict:
    """Run multiple commands in a single request for speed.

    Each command is a dict with "action" and parameters.
    Available actions: navigate, newTab, closeTab, switchTab, click, type,
    fill, scroll, hover, find, js, pageInfo, pageText, screenshot, tabs,
    forms, dom, sleep, waitForElement, pageTextByTabId

    Args:
        commands: List of command dicts, e.g. [{"action": "navigate", "url": "..."}, {"action": "waitForElement", "selector": ".results", "timeout": 10000}, {"action": "pageText"}]
    """
    # Use a generous timeout to accommodate waitForElement commands
    max_timeout = 15
    for cmd in commands:
        if cmd.get("action") == "waitForElement":
            ms = cmd.get("timeout", 10000)
            max_timeout = max(max_timeout, (ms / 1000) + 10)
    return _post("/api/batch", {"commands": commands}, timeout=max_timeout)


def main():
    """Entry point for the ZenLink MCP server."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

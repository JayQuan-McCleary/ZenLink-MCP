"""
ZenLink MCP Server
Exposes ZenLink browser automation as native MCP tools for Claude Desktop and other MCP clients.
Requires the ZenLink bridge (bridge.py) to be running on localhost:8765.

Install: pip install "mcp[cli]" httpx
"""

import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("ZenLink")
# Bind explicitly to IPv4 — the bridge listens only on 127.0.0.1, and
# `localhost` resolves to ::1 first on Windows, so any IPv6 process
# squatting on :8765 (e.g. a stray `python -m http.server`) silently
# hijacks every call and httpx parses its 404 HTML as JSON.
BRIDGE = "http://127.0.0.1:8765"


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


def _with_tab(body: dict, tab_id: int | None) -> dict:
    """Add tabId to a body dict when targeting a specific tab."""
    if tab_id is not None:
        body["tabId"] = tab_id
    return body


# ════════════════════════════════════════════════════════════════════
#  Parallel-work primer (read this if you're driving multiple tabs)
# ════════════════════════════════════════════════════════════════════
#
# Every tab-aware tool below accepts an optional `tab_id`. If omitted, it
# targets the active tab. Pass `tab_id` to drive a specific tab without
# stealing focus — that's the foundation for parallel multi-tab work.
#
# Recipe for reliable parallel agentic work:
#
#   1. `zen_new_tab(...)` for each tab you'll drive; collect the IDs.
#   2. `zen_keep_alive([id1, id2, ...])` — prevents Zen's Tab Unloader
#      from discarding inactive tabs mid-batch. Pings each tab every
#      60s (default) which resets the unloader's idle timer.
#   3. Drive each tab by passing `tab_id=` to clicks, types, JS, etc.
#      Use `zen_parallel([[...tab1 steps...], [...tab2 steps...]])` to
#      fan out concurrently.
#   4. If you suspect a tab was unloaded (long pauses between commands),
#      `zen_wake_tab(tab_id)` revives it.
#   5. `zen_keep_alive_stop()` when done.
#
# ════════════════════════════════════════════════════════════════════


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
def zen_page_info(tab_id: int | None = None) -> dict:
    """Get current page URL, title, dimensions, and scroll position.

    Args:
        tab_id: Optional tab to target. Defaults to active tab.
    """
    if tab_id is None:
        return _get("/api/page-info")
    return _post("/api/page-info", {"tabId": tab_id})


@mcp.tool()
def zen_page_text(tab_id: int | None = None) -> dict:
    """Extract all readable text from the current page.

    Args:
        tab_id: Optional tab to target. Defaults to active tab. For non-active
            tabs, prefer this with tab_id over zen_page_text_by_tab_id — they
            do the same thing now.
    """
    if tab_id is None:
        return _get("/api/page-text")
    return _post("/api/page-text", {"tabId": tab_id})


@mcp.tool()
def zen_page_text_by_tab_id(tab_id: int) -> dict:
    """Get page text from a specific tab by ID without switching to it.

    Args:
        tab_id: The tab ID to read from (get IDs from zen_tabs)

    Returns the full visible text content of the specified tab.
    """
    return _post("/api/page-text-by-tab-id", {"tabId": tab_id})


@mcp.tool()
def zen_forms(tab_id: int | None = None) -> dict:
    """Get all form fields on the current page with their labels and values.

    Args:
        tab_id: Optional tab to target. Defaults to active tab.
    """
    if tab_id is None:
        return _get("/api/forms")
    return _post("/api/forms", {"tabId": tab_id})


@mcp.tool()
def zen_dom(tab_id: int | None = None) -> dict:
    """Get the accessibility tree of interactive elements on the page.

    Args:
        tab_id: Optional tab to target. Defaults to active tab.
    """
    if tab_id is None:
        return _get("/api/dom")
    return _post("/api/dom", {"tabId": tab_id})


@mcp.tool()
def zen_screenshot() -> dict:
    """Capture a screenshot of the current page. Returns the saved file path.

    Note: screenshots are inherently visual and capture the active tab of the
    focused window. To screenshot a specific tab, switch to it first with
    zen_switch_tab.
    """
    return _get("/api/screenshot")


# -- Navigation ---------------------------------------------------

@mcp.tool()
def zen_navigate(url: str, tab_id: int | None = None) -> dict:
    """Navigate the active tab to a URL.

    Args:
        url: The URL to navigate to (e.g. "https://example.com")
        tab_id: Optional tab to navigate. Defaults to active tab.
    """
    return _post("/api/navigate", _with_tab({"url": url}, tab_id))


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
def zen_click(selector: str = "", x: int = 0, y: int = 0, tab_id: int | None = None) -> dict:
    """Click an element on the page by CSS selector or coordinates.

    Args:
        selector: CSS selector to click (e.g. "#submit", ".btn-primary")
        x: X coordinate (used if selector is empty)
        y: Y coordinate (used if selector is empty)
        tab_id: Optional tab to target. Defaults to active tab.
    """
    body: dict = {"selector": selector} if selector else {"coords": {"x": x, "y": y}}
    return _post("/api/click", _with_tab(body, tab_id))


@mcp.tool()
def zen_trusted_click(
    selector: str = "",
    x: int = 0,
    y: int = 0,
    coordinate_space: str = "viewport",
    focus: bool = False,
    tab_id: int | None = None,
) -> dict:
    """Click using the real OS mouse pointer for pages that reject synthetic DOM events.

    This is slower and moves the user's cursor, so prefer zen_click unless a page
    specifically ignores synthetic clicks.

    Args:
        selector: CSS selector to click. If provided, ZenLink clicks its center.
        x: X coordinate, used if selector is empty.
        y: Y coordinate, used if selector is empty.
        coordinate_space: "viewport" for browser viewport coords or "screen" for desktop coords.
        focus: Whether to try to foreground the browser first. Defaults to false.
        tab_id: Optional tab to resolve the selector against (viewport coords only).
    """
    if selector:
        body = {"selector": selector, "focus": focus}
    else:
        body = {"coords": {"x": x, "y": y}, "coordinateSpace": coordinate_space, "focus": focus}
    return _post("/api/trusted-click", _with_tab(body, tab_id))


@mcp.tool()
def zen_type(selector: str, text: str, clear: bool = False, tab_id: int | None = None) -> dict:
    """Type text into an input field.

    Args:
        selector: CSS selector of the input element
        text: Text to type
        clear: Whether to clear existing text first
        tab_id: Optional tab to target. Defaults to active tab.
    """
    return _post("/api/type", _with_tab({"selector": selector, "text": text, "clear": clear}, tab_id))


@mcp.tool()
def zen_set_editable_content(
    selector: str,
    value: str,
    format: str = "text",
    clear: bool = True,
    tab_id: int | None = None,
) -> dict:
    """Set text or HTML in a contenteditable editor, input, or textarea in one fast operation.

    Use this for rich editors such as Gmail compose bodies where typing long text is slow.

    Args:
        selector: CSS selector or ZenLink ref for the editable element
        value: Text or HTML to place into the editor
        format: "text" for plain text or "html" for trusted HTML
        clear: Whether to replace existing content instead of appending
        tab_id: Optional tab to target. Defaults to active tab.
    """
    return _post(
        "/api/set-editable-content",
        _with_tab({"selector": selector, "value": value, "format": format, "clear": clear}, tab_id),
    )


@mcp.tool()
def zen_fill(selector: str, value: str, tab_id: int | None = None) -> dict:
    """Set a form field's value directly (faster than typing).

    Args:
        selector: CSS selector of the input/select element
        value: Value to set
        tab_id: Optional tab to target. Defaults to active tab.
    """
    return _post("/api/fill", _with_tab({"selector": selector, "value": value}, tab_id))


@mcp.tool()
def zen_scroll(direction: str = "down", amount: int = 500, tab_id: int | None = None) -> dict:
    """Scroll the page.

    Args:
        direction: Scroll direction - "up", "down", "left", or "right"
        amount: Pixels to scroll
        tab_id: Optional tab to target. Defaults to active tab.
    """
    return _post("/api/scroll", _with_tab({"direction": direction, "amount": amount}, tab_id))


@mcp.tool()
def zen_hover(selector: str, tab_id: int | None = None) -> dict:
    """Hover over an element on the page.

    Args:
        selector: CSS selector of the element to hover over
        tab_id: Optional tab to target. Defaults to active tab.
    """
    return _post("/api/hover", _with_tab({"selector": selector}, tab_id))


# -- Smart Queries ------------------------------------------------

@mcp.tool()
def zen_find(query: str, tab_id: int | None = None) -> dict:
    """Find elements on the page using natural language description.

    Args:
        query: What to find (e.g. "login button", "search bar", "email input")
        tab_id: Optional tab to target. Defaults to active tab.
    """
    return _post("/api/find", _with_tab({"query": query}, tab_id))


@mcp.tool()
def zen_js(code: str, tab_id: int | None = None) -> dict:
    """Execute JavaScript in the current page context.

    Args:
        code: JavaScript code to run (e.g. "document.title" or "document.querySelectorAll('a').length")
        tab_id: Optional tab to target. Defaults to active tab.
    """
    return _post("/api/js", _with_tab({"code": code}, tab_id))


@mcp.tool()
def zen_highlight(selector: str, tab_id: int | None = None) -> dict:
    """Highlight an element on the page with a visual overlay.

    Args:
        selector: CSS selector of the element to highlight
        tab_id: Optional tab to target. Defaults to active tab.
    """
    return _post("/api/highlight", _with_tab({"selector": selector}, tab_id))


# -- Wait ---------------------------------------------------------

@mcp.tool()
def zen_wait_for_element(
    selector: str, timeout: int = 10000, poll_interval: int = 200, tab_id: int | None = None
) -> dict:
    """Wait for a CSS selector to appear and become visible on the page.
    Returns immediately when the element is found, rather than sleeping a fixed duration.
    Use this instead of sleep when waiting for dynamic/JS-rendered content.

    Args:
        selector: CSS selector to wait for (e.g. ".tracking-events", "#results", "[data-loaded]")
        timeout: Maximum time to wait in milliseconds (default: 10000 = 10s)
        poll_interval: How often to check in milliseconds (default: 200ms)
        tab_id: Optional tab to target. Defaults to active tab.
    """
    timeout_s = (timeout / 1000) + 5  # extra buffer for HTTP round-trip
    return _post(
        "/api/wait-for-element",
        _with_tab({"selector": selector, "timeout": timeout, "pollInterval": poll_interval}, tab_id),
        timeout=timeout_s,
    )


@mcp.tool()
def zen_wait_for_result(
    code: str, timeout: int = 15000, poll_interval: int = 500, tab_id: int | None = None
) -> dict:
    """Poll a JavaScript expression until it returns a non-empty result.

    Args:
        code: JavaScript expression to evaluate repeatedly
        timeout: Maximum time to wait in milliseconds
        poll_interval: How often to check in milliseconds
        tab_id: Optional tab to target. Defaults to active tab.
    """
    timeout_s = (timeout / 1000) + 5
    return _post(
        "/api/wait-for-result",
        _with_tab({"code": code, "timeout": timeout, "pollInterval": poll_interval}, tab_id),
        timeout=timeout_s,
    )


@mcp.tool()
def zen_workflows() -> dict:
    """List available named ZenLink workflows from the bridge workflow directory."""
    return _get("/api/workflows")


@mcp.tool()
def zen_workflow(name: str, variables: dict | None = None) -> dict:
    """Execute a named ZenLink workflow from the bridge workflow directory.

    Args:
        name: Workflow file name without .md
        variables: Optional template variables for the workflow
    """
    return _post("/api/workflow", {"name": name, "variables": variables or {}}, timeout=300)


@mcp.tool()
def zen_cache(action: str = "clear", seconds: int | None = None) -> dict:
    """Control the ZenLink bridge response cache.

    Args:
        action: "clear", "status", or "ttl"
        seconds: TTL value when action is "ttl"
    """
    body: dict = {"action": action}
    if seconds is not None:
        body["seconds"] = seconds
    return _post("/api/cache", body)


# -- Parallel Multi-Tab Work --------------------------------------

@mcp.tool()
def zen_wake_tab(tab_id: int) -> dict:
    """Revive a tab that Zen's Tab Unloader may have discarded.

    Zen aggressively unloads inactive tabs to save RAM. An unloaded tab still
    appears in zen_tabs but has no live content script — commands targeting it
    will hang or fail until it's reloaded. zen_wake_tab is idempotent: if the
    tab is already alive it returns immediately; otherwise it reloads the tab
    and waits for the page to finish loading.

    Use before targeting a tab that might have been idle for a while. Prefer
    zen_keep_alive for tabs you'll touch repeatedly.

    Args:
        tab_id: The tab ID to wake (get IDs from zen_tabs)
    """
    return _post("/api/wake-tab", {"tabId": tab_id}, timeout=25)


@mcp.tool()
def zen_keep_alive(tab_ids: list[int], interval_seconds: int = 60) -> dict:
    """Keep tabs warm so Zen's Tab Unloader won't discard them mid-workflow.

    Starts a background pinger in the bridge that fires a no-op JS evaluation
    at each listed tab on the given interval. Any script access resets Zen's
    idle timer, so the tabs stay loaded. Replaces any existing keep-alive for
    the same tabs (use a new interval to change cadence).

    Use this at the start of parallel multi-tab work: open your tabs, call
    zen_keep_alive with their IDs, drive them in parallel via zen_parallel or
    by passing tab_id to individual commands, then zen_keep_alive_stop when
    done. The pinger auto-stops if the bridge restarts.

    Args:
        tab_ids: Tab IDs to keep loaded.
        interval_seconds: How often to ping each tab. Minimum 10s, default 60s.
            Should be well under Zen's unloader timeout (commonly 20+ minutes).
    """
    return _post(
        "/api/keep-alive",
        {"tabIds": tab_ids, "intervalSeconds": interval_seconds},
    )


@mcp.tool()
def zen_keep_alive_stop(tab_ids: list[int] | None = None) -> dict:
    """Stop the keep-alive pinger for some or all tabs.

    Args:
        tab_ids: Tabs to stop pinging. Omit (or pass null) to stop all.
    """
    body: dict = {}
    if tab_ids is not None:
        body["tabIds"] = tab_ids
    return _post("/api/keep-alive-stop", body)


@mcp.tool()
def zen_reload_extension() -> dict:
    """Hot-reload the ZenLink extension in the browser.

    Use this after editing the extension source to pick up changes without
    going through `about:addons` and toggling the extension by hand. The
    extension acks the request, then reloads itself ~100ms later; the
    background script's existing reconnect logic re-establishes the bridge
    WebSocket immediately. Content scripts in open tabs survive — they re-
    inject lazily on the next command (see forwardToContent in background.js).

    Note: only works once you're already on a version of the extension that
    has this action handler. The very first install of that version requires
    the usual about:addons toggle.
    """
    return _post("/api/reload-extension", {}, timeout=10)


@mcp.tool()
def zen_parallel(sequences: list[list[dict]]) -> dict:
    """Run command sequences in parallel — typically one sequence per tab.

    Each inner list is a sequence that runs serially; all sequences run
    concurrently. Commands that target a specific tab (navigate, switchTab,
    or any tab-aware action) MUST include "tabId" inside the parallel batch
    to avoid race conditions over the active tab.

    Returns a list of result lists, one per input sequence.

    Args:
        sequences: List of command sequences. Each command is a dict with
            "action" and parameters — same shape as zen_batch commands.
            Example for driving two tabs at once:
                [
                  [{"action": "navigate", "url": "...", "tabId": 12},
                   {"action": "waitForElement", "selector": "h1", "tabId": 12},
                   {"action": "pageText", "tabId": 12}],
                  [{"action": "navigate", "url": "...", "tabId": 13},
                   {"action": "waitForElement", "selector": "h1", "tabId": 13},
                   {"action": "pageText", "tabId": 13}]
                ]
    """
    return _post(
        "/api/batch",
        {"commands": [{"action": "parallel", "sequences": sequences}]},
        timeout=300,
    )


# ════════════════════════════════════════════════════════════════════
#  1.4.0 — Content extraction
# ════════════════════════════════════════════════════════════════════

@mcp.tool()
def zen_query(
    selector: str,
    fields: list[str] | None = None,
    limit: int = 50,
    tab_id: int | None = None,
) -> dict:
    """Extract multiple fields from every element matching a CSS selector.

    Much faster and cheaper than calling zen_js per element. The default
    fields cover the common ones (text, href, value, src, alt, id, name);
    pass `fields=["text","data-foo","bounds","attrs"]` to get arbitrary
    attributes or `bounds`/`attrs`/`html` extras.

    Args:
        selector: CSS selector.
        fields: Field names to extract per element. Defaults to a useful set.
        limit: Max elements to return (capped at 500).
        tab_id: Optional tab; defaults to active.
    """
    body = {"selector": selector, "limit": limit}
    if fields: body["fields"] = fields
    return _post("/api/query", _with_tab(body, tab_id))


@mcp.tool()
def zen_html(selector: str, tab_id: int | None = None) -> dict:
    """Return the outerHTML of a specific element. Cap 100KB."""
    return _post("/api/html", _with_tab({"selector": selector}, tab_id))


@mcp.tool()
def zen_links(internal_only: bool = False, tab_id: int | None = None) -> dict:
    """Return every anchor with href + text. Useful as a crawler primitive."""
    return _post("/api/links", _with_tab({"internalOnly": internal_only}, tab_id))


@mcp.tool()
def zen_images(tab_id: int | None = None) -> dict:
    """Return every <img> with src, alt, and natural dimensions."""
    return _post("/api/images", _with_tab({}, tab_id))


@mcp.tool()
def zen_meta(tab_id: int | None = None) -> dict:
    """Return all meta tags + link rels (canonical, RSS, icons, etc.)."""
    return _post("/api/meta", _with_tab({}, tab_id))


@mcp.tool()
def zen_structured_data(tab_id: int | None = None) -> dict:
    """Extract JSON-LD blocks, OpenGraph (og:*), and Twitter card meta."""
    return _post("/api/structured-data", _with_tab({}, tab_id))


@mcp.tool()
def zen_bounds(selector: str, tab_id: int | None = None) -> dict:
    """Return getBoundingClientRect + viewport/page sizes for an element."""
    return _post("/api/bounds", _with_tab({"selector": selector}, tab_id))


@mcp.tool()
def zen_computed_style(
    selector: str, properties: list[str] | None = None, tab_id: int | None = None
) -> dict:
    """Return computed CSS for an element. Defaults to the layout-relevant set."""
    body = {"selector": selector}
    if properties: body["properties"] = properties
    return _post("/api/computed-style", _with_tab(body, tab_id))


@mcp.tool()
def zen_readability(tab_id: int | None = None) -> dict:
    """Extract the main article on the page (title, byline, clean text).

    Heuristic: score candidate containers (`article`, `main`, `.post`, etc.)
    by text density × paragraph count × inverse link density, strip nav/aside,
    return the winner. Falls back to densest section/div, then body.
    """
    return _post("/api/readability", _with_tab({}, tab_id))


@mcp.tool()
def zen_markdown(selector: str | None = None, tab_id: int | None = None) -> dict:
    """Convert the page (or a selector subtree) to Markdown. Cap 80KB."""
    body = {}
    if selector: body["selector"] = selector
    return _post("/api/markdown", _with_tab(body, tab_id))


@mcp.tool()
def zen_iframes(tab_id: int | None = None) -> dict:
    """List all iframes with src + same-origin/accessible flags."""
    return _post("/api/iframes", _with_tab({}, tab_id))


@mcp.tool()
def zen_explain_selector(selector: str, tab_id: int | None = None) -> dict:
    """Diagnose a CSS selector: match count, sample matches, suggestions for
    a more-specific selector if you got too many."""
    return _post("/api/explain-selector", _with_tab({"selector": selector}, tab_id))


# ════════════════════════════════════════════════════════════════════
#  1.4.0 — Interaction additions
# ════════════════════════════════════════════════════════════════════

@mcp.tool()
def zen_select_option(
    selector: str, value: str, by_text: bool = False, tab_id: int | None = None
) -> dict:
    """Choose an <option> in a <select>. Default matches by value; pass
    `by_text=True` to match by visible text."""
    return _post("/api/select-option", _with_tab({"selector": selector, "value": value, "byText": by_text}, tab_id))


@mcp.tool()
def zen_check(selector: str, checked: bool = True, tab_id: int | None = None) -> dict:
    """Set a checkbox or radio's checked state."""
    return _post("/api/check", _with_tab({"selector": selector, "checked": checked}, tab_id))


@mcp.tool()
def zen_focus(selector: str, tab_id: int | None = None) -> dict:
    """Move focus to the matched element."""
    return _post("/api/focus", _with_tab({"selector": selector}, tab_id))


@mcp.tool()
def zen_blur(selector: str | None = None, tab_id: int | None = None) -> dict:
    """Blur an element (or document.activeElement if no selector)."""
    body = {}
    if selector: body["selector"] = selector
    return _post("/api/blur", _with_tab(body, tab_id))


@mcp.tool()
def zen_keypress(
    key: str,
    selector: str | None = None,
    modifiers: dict | None = None,
    text: str | None = None,
    tab_id: int | None = None,
) -> dict:
    """Dispatch a synthetic keyboard event. Use modifiers like
    `{"ctrl": True, "shift": True}`. Pass `text` to also insert characters
    into editable targets.

    Args:
        key: Key name, e.g. "Enter", "Tab", "Escape", "ArrowDown", "a".
        selector: Optional element to target. Defaults to document.activeElement.
        modifiers: {"ctrl"|"shift"|"alt"|"meta": True}.
        text: If set, also insert this text into editable targets.
    """
    body = {"key": key}
    if selector: body["selector"] = selector
    if modifiers: body["modifiers"] = modifiers
    if text is not None: body["text"] = text
    return _post("/api/keypress", _with_tab(body, tab_id))


@mcp.tool()
def zen_double_click(selector: str, tab_id: int | None = None) -> dict:
    """Dispatch a synthetic double-click on the matched element."""
    return _post("/api/double-click", _with_tab({"selector": selector}, tab_id))


@mcp.tool()
def zen_submit_form(selector: str | None = None, tab_id: int | None = None) -> dict:
    """Submit a form. If selector is omitted, submits the first <form> found."""
    body = {}
    if selector: body["selector"] = selector
    return _post("/api/submit-form", _with_tab(body, tab_id))


@mcp.tool()
def zen_form_fill(fields: dict, tab_id: int | None = None) -> dict:
    """Fill many fields at once via fuzzy matching.

    Each key in `fields` is matched as: CSS selector → name attribute →
    label text (case-insensitive contains) → placeholder. Each value is
    applied via the appropriate setter (.value for inputs/textareas, .checked
    for checkboxes/radios, value for selects). Returns per-key results.

    Args:
        fields: {"email": "foo@bar", "Password": "...", "#submit-target": true}
    """
    return _post("/api/form-fill", _with_tab({"fields": fields}, tab_id))


@mcp.tool()
def zen_drag(from_selector: str, to_selector: str, tab_id: int | None = None) -> dict:
    """Synthetic drag-and-drop from one element to another (HTML5 drag events)."""
    return _post("/api/drag", _with_tab({"from": from_selector, "to": to_selector}, tab_id))


@mcp.tool()
def zen_click_and_wait_navigation(
    selector: str, timeout: int = 15000, tab_id: int | None = None
) -> dict:
    """Click an element, then wait for the resulting navigation to complete.

    Atomic operation — far more reliable than `zen_click` followed by
    `zen_wait_for_url` for links/submit buttons. Listens for
    tabs.onUpdated(status='complete')."""
    return _post(
        "/api/click-and-wait-navigation",
        _with_tab({"selector": selector, "timeout": timeout}, tab_id),
        timeout=(timeout / 1000) + 10,
    )


# ════════════════════════════════════════════════════════════════════
#  1.4.0 — Visual additions
# ════════════════════════════════════════════════════════════════════

@mcp.tool()
def zen_element_screenshot(selector: str, tab_id: int | None = None) -> dict:
    """Screenshot a single element. Scrolls into view, captures, crops in the
    extension via OffscreenCanvas. Returns a PNG data URL."""
    return _post("/api/element-screenshot", _with_tab({"selector": selector}, tab_id), timeout=30)


@mcp.tool()
def zen_full_page_screenshot(tab_id: int | None = None) -> dict:
    """Scroll-and-stitch screenshot covering the full document height (up to
    30 viewports tall). Returns one PNG data URL of the entire page."""
    return _post("/api/full-page-screenshot", _with_tab({}, tab_id), timeout=120)


@mcp.tool()
def zen_full_page_metrics(tab_id: int | None = None) -> dict:
    """Return document/viewport sizes + scroll position + devicePixelRatio."""
    return _post("/api/full-page-metrics", _with_tab({}, tab_id))


# ════════════════════════════════════════════════════════════════════
#  1.4.0 — Tab and window management
# ════════════════════════════════════════════════════════════════════

@mcp.tool()
def zen_pin_tab(pinned: bool = True, tab_id: int | None = None) -> dict:
    """Pin or unpin a tab."""
    return _post("/api/pin-tab", _with_tab({"pinned": pinned}, tab_id))


@mcp.tool()
def zen_mute_tab(muted: bool = True, tab_id: int | None = None) -> dict:
    """Mute or unmute a tab."""
    return _post("/api/mute-tab", _with_tab({"muted": muted}, tab_id))


@mcp.tool()
def zen_duplicate_tab(tab_id: int | None = None) -> dict:
    """Duplicate a tab. Returns the new tab id."""
    return _post("/api/duplicate-tab", _with_tab({}, tab_id))


@mcp.tool()
def zen_reload_tab(bypass_cache: bool = False, tab_id: int | None = None) -> dict:
    """Reload a tab. Pass `bypass_cache=True` for a hard reload."""
    return _post("/api/reload-tab", _with_tab({"bypassCache": bypass_cache}, tab_id))


@mcp.tool()
def zen_back(tab_id: int | None = None) -> dict:
    """Go back in history (browser back button)."""
    return _post("/api/back", _with_tab({}, tab_id))


@mcp.tool()
def zen_forward(tab_id: int | None = None) -> dict:
    """Go forward in history."""
    return _post("/api/forward", _with_tab({}, tab_id))


@mcp.tool()
def zen_get_zoom(tab_id: int | None = None) -> dict:
    """Return the current zoom factor (1.0 = 100%)."""
    return _post("/api/get-zoom", _with_tab({}, tab_id))


@mcp.tool()
def zen_set_zoom(factor: float, tab_id: int | None = None) -> dict:
    """Set zoom factor. 0.3 to 5.0 typical; 1.0 = 100%."""
    return _post("/api/set-zoom", _with_tab({"factor": factor}, tab_id))


@mcp.tool()
def zen_windows() -> dict:
    """List all open browser windows with their tabs."""
    return _post("/api/windows", {})


@mcp.tool()
def zen_create_window(url: str | None = None, incognito: bool = False) -> dict:
    """Open a new browser window. Pass a URL to load it at start."""
    body = {"incognito": incognito}
    if url: body["url"] = url
    return _post("/api/create-window", body)


@mcp.tool()
def zen_close_window(window_id: int) -> dict:
    """Close a browser window by ID (from zen_windows)."""
    return _post("/api/close-window", {"windowId": window_id})


@mcp.tool()
def zen_focus_window(window_id: int) -> dict:
    """Bring a browser window to the foreground."""
    return _post("/api/focus-window", {"windowId": window_id})


@mcp.tool()
def zen_move_tab(tab_id: int, window_id: int | None = None, index: int = -1) -> dict:
    """Move a tab to a position (and optionally to a different window). -1 = end."""
    body = {"tabId": tab_id, "index": index}
    if window_id is not None: body["windowId"] = window_id
    return _post("/api/move-tab", body)


@mcp.tool()
def zen_detach_tab(tab_id: int) -> dict:
    """Pop a tab out into its own new window."""
    return _post("/api/detach-tab", {"tabId": tab_id})


# ════════════════════════════════════════════════════════════════════
#  1.4.0 — Network, cookies, storage, clipboard, downloads
# ════════════════════════════════════════════════════════════════════

@mcp.tool()
def zen_cookies(
    op: str,
    url: str | None = None,
    name: str | None = None,
    value: str | None = None,
    domain: str | None = None,
    path: str | None = None,
    secure: bool = False,
) -> dict:
    """Cookie operations: "get", "set", "remove", "clear".

    - get: returns matching cookies (use url/domain/name to filter).
    - set: requires url + name + value.
    - remove: requires url + name.
    - clear: clears all cookies for url or domain.
    """
    body = {"op": op}
    for k, v in [("url", url), ("name", name), ("value", value), ("domain", domain), ("path", path), ("secure", secure)]:
        if v is not None: body[k] = v
    return _post("/api/cookies", body)


@mcp.tool()
def zen_storage(
    kind: str,
    op: str,
    key: str | None = None,
    value: str | None = None,
    tab_id: int | None = None,
) -> dict:
    """localStorage / sessionStorage ops.

    Args:
        kind: "local" or "session".
        op: "get" | "set" | "remove" | "clear" | "list" | "snapshot" | "restore".
        key: Required for get/set/remove.
        value: For set, the string value. For restore, a dict of key→value.
        tab_id: Tab to run against. Storage is per-origin, so prefer driving
            it on a tab already at the right origin.
    """
    body = {"kind": kind, "op": op}
    if key is not None: body["key"] = key
    if value is not None: body["value"] = value
    return _post("/api/storage", _with_tab(body, tab_id))


@mcp.tool()
def zen_clipboard(op: str, text: str | None = None) -> dict:
    """Read or write the system clipboard.

    Args:
        op: "read" or "write".
        text: Text to write when op="write".
    """
    body = {"op": op}
    if text is not None: body["text"] = text
    return _post("/api/clipboard", body)


@mcp.tool()
def zen_downloads(
    op: str,
    url: str | None = None,
    filename: str | None = None,
    query: dict | None = None,
) -> dict:
    """Downloads operations.

    Args:
        op: "download" | "list" | "cancel".
        url: For "download", the URL to fetch.
        filename: Optional output filename.
        query: For "list", a downloads.search query dict.
    """
    body = {"op": op}
    if url: body["url"] = url
    if filename: body["filename"] = filename
    if query: body["query"] = query
    return _post("/api/downloads", body)


@mcp.tool()
def zen_clear_browsing_data(
    types: list[str] | None = None, since_ms: int | None = None
) -> dict:
    """Clear browsing data of the given types.

    Args:
        types: Which to clear. Subset of ["cache","cookies","history",
            "localStorage","passwords","downloads"]. Default = all of those.
        since_ms: Only data created since this epoch-ms timestamp.
    """
    body = {}
    if types: body["types"] = types
    if since_ms: body["since"] = since_ms
    return _post("/api/clear-browsing-data", body, timeout=60)


@mcp.tool()
def zen_intercept(
    op: str,
    patterns: list[str] | None = None,
    effect: str = "block",
) -> dict:
    """Block, log, or redirect HTTP requests by URL regex.

    Useful to suppress analytics/ads during agent runs (3–10× page speed-up)
    or to log what an SPA actually fetches.

    Args:
        op: "add" | "clear" | "list" | "log" | "clearLog".
        patterns: For "add", regex patterns to match against request URLs.
        effect: For "add", "block" (cancel request) or "redirect".
    """
    body = {"op": op, "effect": effect}
    if patterns: body["patterns"] = patterns
    return _post("/api/intercept", body)


@mcp.tool()
def zen_capture_network(op: str = "read", since: int = 0, tab_id: int | None = None) -> dict:
    """Capture network requests via the page's PerformanceObserver.

    Args:
        op: "start" begins capturing fresh, "stop" pauses, "read" returns
            the buffer (default), "clear" empties it.
        since: When reading, only return entries with startTime >= since (ms).
        tab_id: Optional tab; defaults to active.
    """
    return _post("/api/capture-network", _with_tab({"op": op, "since": since}, tab_id))


@mcp.tool()
def zen_wait_for_network_idle(
    idle_ms: int = 500, timeout: int = 10000, tab_id: int | None = None
) -> dict:
    """Wait until no new network resources have started for `idle_ms`."""
    return _post(
        "/api/wait-for-network-idle",
        _with_tab({"idleMs": idle_ms, "timeout": timeout}, tab_id),
        timeout=(timeout / 1000) + 10,
    )


@mcp.tool()
def zen_wait_for_url(pattern: str, timeout: int = 10000, tab_id: int | None = None) -> dict:
    """Wait until the tab's URL matches a JS regex pattern."""
    return _post(
        "/api/wait-for-url",
        _with_tab({"pattern": pattern, "timeout": timeout}, tab_id),
        timeout=(timeout / 1000) + 10,
    )


@mcp.tool()
def zen_wait_for_title(pattern: str, timeout: int = 10000, tab_id: int | None = None) -> dict:
    """Wait until document.title matches a JS regex pattern."""
    return _post(
        "/api/wait-for-title",
        _with_tab({"pattern": pattern, "timeout": timeout}, tab_id),
        timeout=(timeout / 1000) + 10,
    )


@mcp.tool()
def zen_watch_console(enabled: bool = True, tab_id: int | None = None) -> dict:
    """Toggle console capture on a tab. Once enabled, browser console
    messages (log/info/warn/error/debug + window errors) are buffered up to
    500 entries; retrieve via zen_console_logs."""
    return _post("/api/watch-console", _with_tab({"enabled": enabled}, tab_id))


@mcp.tool()
def zen_console_logs(
    since: int | None = None, level: str | None = None, tab_id: int | None = None
) -> dict:
    """Return buffered console logs from a tab (requires zen_watch_console first)."""
    body = {}
    if since is not None: body["since"] = since
    if level: body["level"] = level
    return _post("/api/console-logs", _with_tab(body, tab_id))


# ════════════════════════════════════════════════════════════════════
#  1.4.0 — Orchestration
# ════════════════════════════════════════════════════════════════════

@mcp.tool()
def zen_broadcast(tab_ids: list[int], command: dict, timeout: int = 30) -> dict:
    """Fire the same command at every listed tab in parallel.

    Each tab gets the command with its own tabId injected. Returns per-tab
    results keyed by tab id.

    Args:
        tab_ids: Tabs to target.
        command: Command dict, e.g. {"action": "pageInfo"} or
            {"action": "getReadability"}.
        timeout: Per-tab timeout in seconds.
    """
    return _post(
        "/api/broadcast",
        {"tabIds": tab_ids, "command": command, "timeout": timeout},
        timeout=timeout + 10,
    )


@mcp.tool()
def zen_sync_barrier(
    tab_ids: list[int],
    predicate: str,
    timeout: int = 30000,
    poll_interval: int = 300,
) -> dict:
    """Block until a JS predicate returns truthy on every listed tab.

    Replaces hand-rolled "wait for everything to be ready" loops.

    Args:
        tab_ids: Tabs to monitor.
        predicate: JS expression that returns truthy when the tab is ready,
            e.g. "!!document.querySelector('.results')".
        timeout: Overall timeout in ms.
        poll_interval: Per-poll interval in ms.
    """
    return _post(
        "/api/sync-barrier",
        {"tabIds": tab_ids, "predicate": predicate, "timeout": timeout, "pollInterval": poll_interval},
        timeout=(timeout / 1000) + 10,
    )


@mcp.tool()
def zen_tag_tab(name: str, tab_id: int) -> dict:
    """Give a tab a memorable name. Refer to it later via zen_resolve_tag.
    Names survive bridge restarts only if you re-tag — they live in memory."""
    return _post("/api/tag-tab", {"name": name, "tabId": tab_id})


@mcp.tool()
def zen_resolve_tag(name: str) -> dict:
    """Look up the tab id for a tag set via zen_tag_tab."""
    return _post("/api/resolve-tag", {"name": name})


@mcp.tool()
def zen_list_tags() -> dict:
    """List all tag → tab id mappings."""
    return _post("/api/list-tags", {})


@mcp.tool()
def zen_untag_tab(name: str) -> dict:
    """Remove a tag."""
    return _post("/api/untag-tab", {"name": name})


@mcp.tool()
def zen_tab_pool(size: int, url: str = "about:blank") -> dict:
    """Maintain a warm pool of N tabs always ready to be acquired.

    Grows or shrinks to `size`. Acquire/release via zen_pool_acquire and
    zen_pool_release. Auto-grows by one if you acquire from an empty pool.
    """
    return _post("/api/tab-pool", {"size": size, "url": url})


@mcp.tool()
def zen_pool_acquire() -> dict:
    """Check out a warm tab from the pool. Returns its tab_id."""
    return _post("/api/pool-acquire", {})


@mcp.tool()
def zen_pool_release(tab_id: int) -> dict:
    """Return a tab to the pool for reuse."""
    return _post("/api/pool-release", {"tabId": tab_id})


# ════════════════════════════════════════════════════════════════════
#  1.4.0 — Session save/restore (auth-once-use-many)
# ════════════════════════════════════════════════════════════════════

@mcp.tool()
def zen_save_session(name: str, urls: list[str] | None = None) -> dict:
    """Snapshot cookies (and per-origin localStorage if urls given) to disk.

    Use case: log into a service interactively once, save the session,
    then have parallel agents load it for authenticated work.

    Args:
        name: A label for the session (becomes filename under
            ~/claude-zen-sessions/).
        urls: Origins whose cookies + localStorage to snapshot. Each gets
            opened briefly in a temp tab so localStorage can be read.
    """
    return _post("/api/save-session", {"name": name, "urls": urls or []}, timeout=120)


@mcp.tool()
def zen_load_session(name: str) -> dict:
    """Restore cookies + localStorage from a previously saved session."""
    return _post("/api/load-session", {"name": name}, timeout=120)


@mcp.tool()
def zen_list_sessions() -> dict:
    """List saved sessions with their metadata."""
    return _post("/api/list-sessions", {})


@mcp.tool()
def zen_delete_session(name: str) -> dict:
    """Delete a saved session file."""
    return _post("/api/delete-session", {"name": name})


# ════════════════════════════════════════════════════════════════════
#  1.4.0 — Observability and policy
# ════════════════════════════════════════════════════════════════════

@mcp.tool()
def zen_health() -> dict:
    """Extended health/status: bridge version, ports, keep-alive list,
    pool state, tags, policy, sessions dir, audit/log sizes."""
    return _post("/api/health", {})


@mcp.tool()
def zen_logs(limit: int = 200, since: str | None = None) -> dict:
    """Return recent bridge log lines (in-memory ring buffer)."""
    body = {"limit": limit}
    if since: body["since"] = since
    return _post("/api/logs", body)


@mcp.tool()
def zen_audit(limit: int = 100, since_ms: int = 0) -> dict:
    """Return recent command audit entries: action, params (JS code stripped),
    success flag, error, duration. Useful for "what did the agent do?" reviews."""
    return _post("/api/audit", {"limit": limit, "since": since_ms})


@mcp.tool()
def zen_set_policy(
    allow: list[str] | None = None,
    deny: list[str] | None = None,
    readonly: bool | None = None,
) -> dict:
    """Set URL allow/deny regex lists and/or read-only mode.

    Read-only mode blocks write actions (click/type/navigate/cookies set/etc.)
    while still allowing read ops. Useful for "let the agent observe only."
    """
    body = {}
    if allow is not None: body["allow"] = allow
    if deny is not None: body["deny"] = deny
    if readonly is not None: body["readonly"] = readonly
    return _post("/api/set-policy", body)


@mcp.tool()
def zen_get_policy() -> dict:
    """Return the active URL/readonly policy."""
    return _post("/api/get-policy", {})


@mcp.tool()
def zen_retry(
    command: dict,
    max_attempts: int = 3,
    backoff_ms: int = 500,
    on_errors: list[str] | None = None,
) -> dict:
    """Wrap any command in exponential-backoff retry.

    Args:
        command: A command dict (same shape as zen_batch entries).
        max_attempts: Total tries including the first.
        backoff_ms: Initial wait between attempts (doubles each retry).
        on_errors: Only retry if the error string contains one of these substrings.
            Default: retry on any error.
    """
    body = {"command": command, "maxAttempts": max_attempts, "backoffMs": backoff_ms}
    if on_errors: body["onErrors"] = on_errors
    return _post("/api/retry", body, timeout=60)


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

    Each command is a dict with "action" and parameters. Add "tabId" to any
    command to target a specific tab instead of the active one. For true
    concurrency across tabs, prefer zen_parallel.

    Available actions: navigate, newTab, closeTab, switchTab, click, type,
    setEditableContent, fill, scroll, hover, find, js, pageInfo, pageText, screenshot, tabs,
    forms, dom, sleep, waitForElement, pageTextByTabId, wakeTab, parallel

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

# ZenLink MCP

MCP server for browser automation via ZenLink — gives Claude Desktop and other MCP clients native browser control through Zen Browser (Firefox-based).

## Installation

```bash
pip install zenlink-mcp
```

## Requirements

- [ZenLink browser extension](https://github.com/JayQuan-McCleary/ZenLink) installed in Zen Browser
- ZenLink bridge running (`python native/bridge.py`)

## Tools

| Tool | Description |
|------|-------------|
| `zen_status` | Check if ZenLink bridge and extension are connected |
| `zen_navigate` | Navigate to a URL |
| `zen_page_text` | Extract all readable text from the current page |
| `zen_page_info` | Get page URL, title, dimensions, scroll position |
| `zen_tabs` | List all open browser tabs |
| `zen_new_tab` | Open a new tab |
| `zen_close_tab` | Close a tab by ID |
| `zen_switch_tab` | Switch to a tab by ID |
| `zen_click` | Click an element by CSS selector or coordinates |
| `zen_type` | Type text into an input field |
| `zen_fill` | Set a form field value directly (faster than typing) |
| `zen_scroll` | Scroll the page |
| `zen_hover` | Hover over an element |
| `zen_find` | Find elements using natural language |
| `zen_js` | Execute JavaScript in the page context |
| `zen_highlight` | Highlight an element with a visual overlay |
| `zen_screenshot` | Capture a screenshot |
| `zen_dom` | Get the accessibility tree of interactive elements |
| `zen_forms` | Get all form fields with labels and values |
| `zen_wait_for_element` | Wait for a CSS selector to appear (replaces fixed sleep timers) |
| `zen_wp_html` | Extract HTML widget content from a WordPress Elementor page |
| `zen_batch` | Run multiple commands in a single request for speed |

### `zen_wait_for_element`

Waits for a CSS selector to appear and become visible on the page. Returns immediately when found rather than sleeping a fixed duration — use this instead of `sleep` when waiting for dynamic/JS-rendered content.

```json
{"action": "waitForElement", "selector": ".tracking-events", "timeout": 10000}
```

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `selector` | string | required | CSS selector to wait for |
| `timeout` | int | 10000 | Max wait time in milliseconds |
| `poll_interval` | int | 200 | How often to check in milliseconds |

Returns `{ ok: true, found: true, elapsed: 342, ref: "r12", tag: "div" }` on success, or `{ ok: false, found: false, error: "Timed out after 10000ms" }` on timeout.

### `zen_batch`

Run multiple commands in one request. Supports all actions including `waitForElement` and `sleep`:

```json
[
  {"action": "navigate", "url": "https://example.com"},
  {"action": "waitForElement", "selector": ".results", "timeout": 8000},
  {"action": "pageText"}
]
```

## Claude Desktop Setup

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "zenlink": {
      "command": "zenlink-mcp"
    }
  }
}
```

## Changelog

### 1.1.0
- Added `zen_wait_for_element` tool — polls DOM until selector appears instead of fixed sleep timers
- Added `waitForElement` as a batch action
- Bridge: new `/api/wait-for-element` endpoint with auto-extended timeout
- Content script bumped to v6

### 1.0.3
- Initial public release

## Links

- [ZenLink Bridge & Extension](https://github.com/JayQuan-McCleary/ZenLink)
- [MCP Registry](https://registry.modelcontextprotocol.io)

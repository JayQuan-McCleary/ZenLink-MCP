# ZenLink-MCP

MCP server that gives Claude Desktop (and other MCP clients) native browser control through [ZenLink](https://github.com/JayQuan-McCleary/ZenLink).

Instead of Claude running shell commands to talk to ZenLink, this makes every ZenLink action a **native tool** — faster, cleaner, no shell overhead.

## Prerequisites

- [ZenLink](https://github.com/JayQuan-McCleary/ZenLink) installed and bridge running (`python native/bridge.py`)
- Python 3.10+

## Install

```bash
pip install "mcp[cli]" httpx
```

## Setup for Claude Desktop

Add to your Claude Desktop config:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "zenlink": {
      "command": "python",
      "args": ["D:\\ZenLink-MCP\\server.py"]
    }
  }
}
```

Replace the path with wherever you cloned this repo. Restart Claude Desktop.

## How It Works

```
Claude Desktop
    ¦
    ¦  MCP (stdio) — native tool calls
    ?
ZenLink-MCP (this server)
    ¦
    ¦  HTTP to localhost:8765
    ?
ZenLink Bridge ? Browser Extension ? Web Page
```

Claude sees `zen_navigate`, `zen_click`, `zen_fill`, etc. as first-class tools — same as file creation or web search. No PowerShell, no curl, no shell spawning.

## Available Tools

### Reading
| Tool | Description |
|------|-------------|
| `zen_status` | Check bridge + extension connection |
| `zen_tabs` | List all open tabs with IDs |
| `zen_page_info` | URL, title, dimensions, scroll position |
| `zen_page_text` | Extract readable text from page |
| `zen_forms` | All form fields with labels and values |
| `zen_dom` | Accessibility tree |
| `zen_screenshot` | Capture viewport as PNG |

### Navigation
| Tool | Description |
|------|-------------|
| `zen_navigate(url)` | Load URL in active tab |
| `zen_new_tab(url)` | Open new tab |
| `zen_close_tab(tab_id)` | Close tab by ID |
| `zen_switch_tab(tab_id)` | Focus a tab |

### Interaction
| Tool | Description |
|------|-------------|
| `zen_click(selector, x, y)` | Click by selector or coordinates |
| `zen_type(selector, text, clear)` | Type into input |
| `zen_fill(selector, value)` | Set form field value |
| `zen_scroll(direction, amount)` | Scroll page |
| `zen_hover(selector)` | Hover over element |

### Smart Queries
| Tool | Description |
|------|-------------|
| `zen_find(query)` | Find elements by natural language |
| `zen_js(code)` | Execute JavaScript in page context |
| `zen_highlight(selector)` | Visual overlay on element |
| `zen_batch(commands)` | Multiple commands in one call |

## Example Conversation

**You:** "Open Wikipedia and find the article about ducks"

**Claude uses:**
1. `zen_navigate("https://en.wikipedia.org")` 
2. `zen_fill("#searchInput", "Duck")`
3. `zen_click("#searchButton")`
4. `zen_page_text()` ? reads the article

No shell commands visible. Just native tool calls.

## Why separate from ZenLink?

**ZenLink** is the universal HTTP bridge — works with any language, any tool, any AI.

**ZenLink-MCP** is the Claude-specific wrapper. Keeping them separate means:
- ZenLink stays clean and universal
- MCP users get a focused, easy setup
- Updates to either don't break the other

## License

MIT
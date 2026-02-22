# ZenLink-MCP

MCP server that gives Claude Desktop (and any MCP client) native browser control through [ZenLink](https://github.com/JayQuan-McCleary/ZenLink).

Instead of shell commands and HTTP calls, every ZenLink action becomes a **native tool** - faster, cleaner, no overhead.

## Prerequisites

- [ZenLink](https://github.com/JayQuan-McCleary/ZenLink) installed and bridge running (`python native/bridge.py`)
- Zen Browser or Firefox with the ZenLink extension loaded
- Python 3.10+

## Install

```bash
pip install zenlink-mcp
```

## Setup for Claude Desktop

Add to your config file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "zenlink": {
      "command": "zenlink-mcp"
    }
  }
}
```

Restart Claude Desktop. ZenLink tools will appear in the tools menu.

### Alternative (run from source)

```json
{
  "mcpServers": {
    "zenlink": {
      "command": "python",
      "args": ["/path/to/ZenLink-MCP/src/zenlink_mcp/server.py"]
    }
  }
}
```

## How It Works

```
Claude Desktop / Any MCP Client
    -
    -  MCP (stdio) - native tool calls
    ?
ZenLink-MCP (this server)
    -
    -  HTTP to localhost:8765
    ?
ZenLink Bridge ? Browser Extension ? Web Page
```

No shell spawning. No curl. Just direct tool calls returning clean JSON.

## Available Tools (22)

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

## Example

**You:** "Open Wikipedia and search for ducks"

**Claude calls:**
1. `zen_navigate("https://en.wikipedia.org")`
2. `zen_fill("#searchInput", "Duck")`
3. `zen_click("#searchButton")`
4. `zen_page_text()` ? reads the article

No shell commands. Just native tool calls.

## Why separate from ZenLink?

**[ZenLink](https://github.com/JayQuan-McCleary/ZenLink)** is the universal HTTP bridge - works with any language, any tool, any AI.

**ZenLink-MCP** is the MCP wrapper. Keeping them separate means:
- ZenLink stays clean and universal
- MCP users get a focused, easy setup
- Updates to either don't break the other

## License

MIT
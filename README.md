# ZenLink MCP

MCP server for browser automation via ZenLink — gives Claude Desktop and other MCP clients native browser control through Zen Browser (Firefox-based).

**v2.0.0** ships ~50 new tools for parallel agentic work: real multi-tab parallelism, tab unloader defense, session save/restore, Readability + Markdown extraction, request interception, cookies/storage, and orchestration primitives (broadcast, sync barriers, tab pools, named tags). See [CHANGELOG.md](CHANGELOG.md) for the full list.

## Installation

```bash
pip install zenlink-mcp
```

## Requirements

- [ZenLink browser extension](https://github.com/JayQuan-McCleary/ZenLink) **v2.0.0+** installed in Zen Browser
- ZenLink bridge running (`python native/bridge.py`)

## Tool surface (75+ tools)

Every tab-aware tool below accepts an optional `tab_id` parameter — pass it to drive a specific tab without stealing focus, the foundation for parallel multi-tab work.

### Core
`zen_status`, `zen_health`, `zen_tabs`, `zen_new_tab`, `zen_close_tab`, `zen_switch_tab`, `zen_navigate`, `zen_screenshot`

### Content extraction (read once, work cheaply)
`zen_page_text`, `zen_page_info`, `zen_readability`, `zen_markdown`, `zen_query`, `zen_html`, `zen_links`, `zen_images`, `zen_meta`, `zen_structured_data`, `zen_bounds`, `zen_computed_style`, `zen_dom`, `zen_forms`, `zen_iframes`, `zen_explain_selector`, `zen_full_page_metrics`

### Interaction
`zen_click`, `zen_trusted_click`, `zen_double_click`, `zen_type`, `zen_fill`, `zen_form_fill`, `zen_set_editable_content`, `zen_select_option`, `zen_check`, `zen_focus`, `zen_blur`, `zen_keypress`, `zen_submit_form`, `zen_drag`, `zen_hover`, `zen_scroll`, `zen_find`, `zen_highlight`, `zen_click_and_wait_navigation`

### Visual
`zen_screenshot`, `zen_element_screenshot`, `zen_full_page_screenshot`

### Tab and window management
`zen_pin_tab`, `zen_mute_tab`, `zen_duplicate_tab`, `zen_reload_tab`, `zen_back`, `zen_forward`, `zen_get_zoom`, `zen_set_zoom`, `zen_windows`, `zen_create_window`, `zen_close_window`, `zen_focus_window`, `zen_move_tab`, `zen_detach_tab`

### Network, cookies, state
`zen_cookies`, `zen_storage` (local/session), `zen_clipboard`, `zen_downloads`, `zen_clear_browsing_data`, `zen_intercept`, `zen_capture_network`, `zen_wait_for_network_idle`, `zen_wait_for_url`, `zen_wait_for_title`, `zen_watch_console`, `zen_console_logs`

### Sessions (auth-once-use-many)
`zen_save_session`, `zen_load_session`, `zen_list_sessions`, `zen_delete_session`

### Orchestration (parallel multi-tab)
`zen_keep_alive`, `zen_keep_alive_stop`, `zen_wake_tab`, `zen_broadcast`, `zen_sync_barrier`, `zen_tag_tab`, `zen_resolve_tag`, `zen_list_tags`, `zen_untag_tab`, `zen_tab_pool`, `zen_pool_acquire`, `zen_pool_release`, `zen_parallel`

### Batch / scripting
`zen_batch` (with `parallel`, `if`, `while`, `try`, `sequence`, `retry`, `${$N.field}` variable substitution)

### Observability / policy
`zen_logs`, `zen_audit`, `zen_set_policy`, `zen_get_policy`, `zen_retry`, `zen_reload_extension`

### Wait primitives
`zen_wait_for_element`, `zen_wait_for_result`, `zen_wait_for_url`, `zen_wait_for_title`, `zen_wait_for_network_idle`

### Workflow
`zen_workflows`, `zen_workflow`, `zen_cache`, `zen_wp_html`

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

Run multiple commands in one request. Supports all actions including `waitForElement`, `trustedClick`, and `sleep`:

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

See [CHANGELOG.md](CHANGELOG.md) for the full history. Highlights of v2.0.0:

- ~50 new MCP tools across content extraction, interaction, network, sessions, orchestration
- Real parallel multi-tab work via `zen_parallel` + `zen_keep_alive`
- Session save/restore for auth-once-use-many flows
- `zen_intercept` to block analytics/ads (3–10× page speedup in agent runs)
- `zen_readability` + `zen_markdown` for token-efficient page extraction
- Hot reload via `zen_reload_extension`

## Links

- [ZenLink Bridge & Extension](https://github.com/JayQuan-McCleary/ZenLink)
- [MCP Registry](https://registry.modelcontextprotocol.io)

<sub>mcp-name: io.github.JayQuan-McCleary/zenlink-mcp</sub>

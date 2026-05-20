# Changelog

## 2.0.1

- Added `mcp-name` ownership marker in README for MCP Registry validation.
- No functional code changes from 2.0.0.

## 2.0.0 — Parallel agentic work

Major release. ~50 new MCP tools focused on parallel multi-tab work,
content extraction, network control, sessions, and orchestration.
Requires the [ZenLink browser extension](https://github.com/JayQuan-McCleary/ZenLink) v2.0.0+.

### New tools by category

**Parallel multi-tab work**
- `zen_keep_alive`, `zen_keep_alive_stop` — pin tabs against Zen's Tab Unloader
- `zen_wake_tab` — revive a discarded tab
- `zen_parallel` — fan out commands across many tabs concurrently
- `zen_broadcast` — send the same command to many tabs
- `zen_sync_barrier` — wait until a JS predicate is truthy on every listed tab
- `zen_tag_tab` / `zen_resolve_tag` / `zen_list_tags` / `zen_untag_tab` — semantic tab names
- `zen_tab_pool` / `zen_pool_acquire` / `zen_pool_release` — warm tab pool

**Content extraction**
- `zen_readability` — extract the main article (title, byline, clean text)
- `zen_markdown` — convert page or subtree to Markdown
- `zen_query` — multi-field extract from elements (text/href/value/attrs/bounds/…)
- `zen_html` — outerHTML of a selector
- `zen_links` — every anchor with href + text + internal/external flag
- `zen_images` — every `<img>` with src, alt, natural dimensions
- `zen_meta` — meta tags + link rels (canonical, RSS, icons)
- `zen_structured_data` — JSON-LD + OpenGraph + Twitter card meta
- `zen_bounds`, `zen_computed_style`, `zen_full_page_metrics`
- `zen_iframes` — list iframes with same-origin/accessible flags
- `zen_explain_selector` — match count + samples + a more-specific selector suggestion

**Interaction additions**
- `zen_form_fill` — fuzzy multi-field fill by selector/name/label/placeholder
- `zen_select_option`, `zen_check`, `zen_focus`, `zen_blur`
- `zen_keypress` (with modifiers), `zen_double_click`, `zen_submit_form`, `zen_drag`
- `zen_click_and_wait_navigation` — atomic click + wait-for-navigation

**Visual**
- `zen_element_screenshot` — scroll-into-view + crop via OffscreenCanvas
- `zen_full_page_screenshot` — scroll-and-stitch full document height

**Tab and window management**
- `zen_pin_tab`, `zen_mute_tab`, `zen_duplicate_tab`, `zen_reload_tab`
- `zen_back`, `zen_forward`, `zen_get_zoom`, `zen_set_zoom`
- `zen_windows`, `zen_create_window`, `zen_close_window`, `zen_focus_window`
- `zen_move_tab`, `zen_detach_tab`

**Network, state, auth**
- `zen_cookies` — get/set/remove/clear
- `zen_storage` — localStorage / sessionStorage with snapshot/restore
- `zen_clipboard` — read/write
- `zen_downloads` — download/list/cancel
- `zen_clear_browsing_data`
- `zen_intercept` — block/redirect HTTP requests by URL regex
- `zen_capture_network` — PerformanceObserver-based capture
- `zen_wait_for_network_idle`, `zen_wait_for_url`, `zen_wait_for_title`
- `zen_watch_console`, `zen_console_logs`

**Sessions (auth-once-use-many)**
- `zen_save_session` — snapshot cookies + per-origin localStorage to disk
- `zen_load_session`, `zen_list_sessions`, `zen_delete_session`

**Observability & policy**
- `zen_health`, `zen_logs`, `zen_audit`
- `zen_set_policy`, `zen_get_policy` — URL allowlist/denylist + read-only mode
- `zen_retry` — exponential-backoff wrapper for any command
- `zen_reload_extension` — hot reload after edits

### Tool changes

- All tab-aware tools accept an optional `tab_id` parameter. Defaults
  to active tab if omitted.
- `zen_intercept` parameter rename: `action` → `effect` (avoids
  wire-level collision).
- `zen_capture_network` parameter rename: `action` → `op`.

### Breaking

- Requires ZenLink browser extension v2.0.0+ with new permissions
  (`cookies`, `webRequest`, `webRequestBlocking`, `downloads`,
  `clipboardRead`, `clipboardWrite`, `browsingData`). Users updating
  from 1.x will see a permission re-prompt.

### Fixed

- Bridge URL pinned to `http://127.0.0.1:8765` instead of `localhost`
  — prevents stray IPv6 listeners from hijacking calls on Windows
  where `localhost` resolves to `::1` first.

## 1.1.0

- `zen_wait_for_element` — polls DOM until selector appears.
- `zen_wp_html`, `zen_page_text_by_tab_id`, batch improvements.

## 1.0.3

- Initial public release.

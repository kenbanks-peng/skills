---
name: terminal-browser
description: Open websites or local HTML in Rex terminal blocks and control browser tabs with terminal-browser.
---

## Open

Rex only. Create a new block; never replace the conversation block.

1. Use the user's target or `REX_SESSION` and `REX_BLOCK`. If missing or stale,
   run `rex whoami --json`. Use full IDs; never guess an ambiguous target.
2. List browsers with `terminal-browser ls --all --json`, then launch:

   ```sh
   rex split -s "$session_id" -b "$anchor_block" \
     --split=right --ratio 50 --focus=false -c "$PWD" \
     --label Browser --json -- terminal-browser open "$url" --no-merge
   ```

   Use a URL or absolute HTML path. Save `.block_ids[0]` as `browser_block`.
   Do not use `--wait` or pass `--split` to terminal-browser.
3. List browsers again after startup. Identify the new browser `key` and tab
   `id` by comparing lists and checking the URL. Block IDs are not browser keys.
4. Verify page content with `snapshot` or `eval` before reporting success.

## Control

Always specify both browser and tab:

```sh
terminal-browser action --browser "$browser_key" --tab "$tab_id" -- snapshot
terminal-browser action --browser "$browser_key" --tab "$tab_id" -- click @e14
terminal-browser action --browser "$browser_key" --tab "$tab_id" -- fill @e3 "hello"
terminal-browser action --browser "$browser_key" --tab "$tab_id" -- eval "document.title"
```

Prefer page-provided `webmcp` tools when available. Confirm before invoking
`consequential: true` tools; `readOnly: false` tools change user data.

After the final action, even on failure, clear the activity indicator:

```sh
terminal-browser action --browser "$browser_key" --tab "$tab_id" done
```

## Recovery and cleanup

After a timeout, inspect before retrying:

```sh
rex capture -s "$session_id" -b "$browser_block" --trim
rex block call -s "$session_id" -b "$browser_block" process
```

Leave the browser visible unless asked to close it. Close only this task's block
with `rex block close -s "$session_id" "$browser_block"`.
Never use `terminal-browser shutdown`; it closes all browsers.

For other commands, use `terminal-browser <command> --help`.

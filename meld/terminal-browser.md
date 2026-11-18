## Open and verify

1. Use the user's target or `REX_SESSION` and `REX_BLOCK` for `session_id` and `anchor_block`. If missing or stale, run `rex whoami --json`. Use full IDs; never guess an ambiguous target.
2. Allow only one terminal-browser instance per Rex tab (window). Inspect `rex session inspect "$session_id" --json` to find the window containing `anchor_block`, then run `terminal-browser ls --all --json` and match existing browsers to blocks in that window (inspect block processes if needed). Never reuse a browser from another Rex tab. If a browser already exists in the target window, save its block ID as `browser_block`, its browser `key` as `browser_key`, and its active browser tab `id` as `tab_id`; navigate that tab to the absolute HTML path and skip creation:

   ```sh
   terminal-browser action --browser "$browser_key" --tab "$tab_id" -- open "$html_path"
   ```

   Only if no browser exists in that Rex tab, record the browser list and open the report in a new block:

   ```sh
   rex split -s "$session_id" -b "$anchor_block" \
     --split=right --ratio 50 --focus=false -c "$PWD" \
     --label Browser --json -- terminal-browser open "$html_path" --no-merge
   ```

   Set `html_path` to the absolute HTML path. Save `.block_ids[0]` as `browser_block`. Do not use `--wait` or pass `--split` to the browser command.
3. If you created a browser, list browsers again after startup. Identify the new browser `key` and tab `id` by comparing lists and checking the report URL. Block IDs are not browser keys.
4. Inspect the rendered content:

   ```sh
   terminal-browser action --browser "$browser_key" --tab "$tab_id" -- snapshot
   ```

   Use `-- eval "document.body.innerText"` instead of `-- snapshot` if needed. Always specify both browser and tab.
5. After the final action, even on failure, clear the activity indicator:

   ```sh
   terminal-browser action --browser "$browser_key" --tab "$tab_id" done
   ```

After a timeout, inspect before retrying with `rex capture -s "$session_id" -b "$browser_block" --trim` and `rex block call -s "$session_id" -b "$browser_block" process`. Leave the report visible unless asked to close it; close only a block created by this task with `rex block close -s "$session_id" "$browser_block"`. Never use `terminal-browser shutdown`, which closes all browsers.

If the renderer or Rex browser is unavailable, report the limitation and any files created.

---
name: terminal-browser
description: A real browser running inside Rex terminal blocks. Use it to show websites or local HTML beside the conversation and drive open browser tabs — snapshot, click, fill, eval — with the `terminal-browser action` subcommand.
---

Run `terminal-browser open <url>` in a new Rex terminal block using the workflow
below. A local HTML path works like a URL. Never take over the block running
the conversation.

Use `terminal-browser ls --all --json` to discover browsers and tabs. Always pass
`--browser` and `--tab` when using the agent-browser compatible
`terminal-browser action` CLI from the agent's block.

When you use the terminal-browser action sub command, the user will visually
see in the browser tab an indication that you are acting on the browser tab. This
will automatically hide after a preset duration, where the countdown resets
everytime terminal-browser action is used. But its a much better experience
for the user if after the last time you plan to use terminal-browser action you
run `terminal-browser action --browser "$browser_key" --tab "$tab_id" done`,
which immediately clears the indication
that you are using the browser tab

Some pages publish WebMCP tools: named actions with a JSON schema that the
page runs itself. agent-browser announces them when a page has them, and
`terminal-browser action --browser "$browser_key" --tab "$tab_id" -- webmcp list --json` shows the full schemas. Prefer
`terminal-browser action --browser "$browser_key" --tab "$tab_id" -- webmcp invoke <tool> --params '<json>'` over
snapshot, click and fill when a tool covers what you need; it is faster and
does not break when the layout changes. Tools can carry annotations. Treat
`readOnly: false` as a change to the user's data and `consequential: true` as
something to confirm with the user before invoking.

## Rex terminal blocks

This skill targets Rex only. Run
`rex __internal skill --feature-session-naming=false` for the installed CLI's
guide; if unavailable, use `rex --help` and `rex split --help`.

1. Resolve the anchor. For “here” or no specified location, use `REX_SESSION`
   and `REX_BLOCK`. If either is absent or stale, run `rex whoami --json` and
   use its `session_id` and `block_id`. If the location remains unknown, inspect
   `rex ls --json` and `rex block ls -s SESSION --json`; do not guess between
   ambiguous targets. Explicit user targets take precedence over inherited IDs.
2. Record `terminal-browser ls --all --json` before launching.
3. Create a Rex terminal block and run the browser **without** its own
   `--split` option. Set `session_id` and `anchor_block` to the resolved full IDs,
   and `url` to the requested URL or absolute HTML path:

   ```sh
   created=$(rex split -s "$session_id" -b "$anchor_block" \
     --split=right --ratio 50 --focus=false -c "$PWD" \
     --label Browser --json -- terminal-browser open "$url" --no-merge) || exit
   browser_block=$(printf '%s' "$created" | jq -er '.block_ids[0]') || exit
   ```

   Rex directions are `right`, `left`, `above`, and `below`.
   `--ratio 50` gives the new block 50 percent of the split.
   `--focus=false` preserves conversation focus; `--no-merge` keeps the new
   browser from merging into a neighboring browser. Do not use `--wait`:
   the browser is long-lived. After a timeout, inspect the layout before retrying
   to avoid duplicate blocks.
4. Run `terminal-browser ls --all --json` again. Identify the new browser by
   comparing keys with the earlier listing, then verify its tab URL. Startup
   may take a moment. Rex blocks may have null pane metadata and
   `inCurrentTab: false`, so do not rely on the default terminal-tab filter or
   assume a Rex block ID is a browser key. If concurrent launches make the
   result ambiguous, inspect further rather than choosing an arbitrary browser.
5. Save the browser `key` and tab `id` as `browser_key` and `tab_id`.
   Explicitly target them for every action from the agent's block:

   ```sh
   terminal-browser action --browser "$browser_key" --tab "$tab_id" -- snapshot
   terminal-browser action --browser "$browser_key" --tab "$tab_id" -- eval "document.title"
   # After the final action, including when an action fails:
   terminal-browser action --browser "$browser_key" --tab "$tab_id" done
   ```

   Use these selectors for WebMCP commands too. To add a browser tab, use
   `terminal-browser new-tab --browser "$browser_key" "$url"`; list tabs again
   to obtain the new tab ID.
6. Verify page content with a snapshot or eval before reporting it loaded.
   For startup failures, inspect
   `rex capture -s "$session_id" -b "$browser_block" --trim` and
   `rex block call -s "$session_id" -b "$browser_block" process`.
   Leave the browser visible unless asked to close it. To close only the block
   created for this task, use
   `rex block close -s "$session_id" "$browser_block"`, not
   `terminal-browser shutdown`, which closes all browsers.

## Command reference

The following notes cover Rex usage, not verbatim CLI help. Use
`terminal-browser <command> --help` for additional options.

```
$ terminal-browser help
Usage: terminal-browser [url] [options]
       terminal-browser <command> [args]

  open                 Open the browser in a terminal pane
  ls                   List running browsers and their tabs
  setup                Install terminal-browser agent skills
  upgrade              Upgrade to the latest release
  new-tab              Open a tab here, and a browser too if there is none
  clear-browsing-data  Clear cookies, site data and cache, like a browser's Clear browsing data
  apps                 Lists registered terminal-browser apps
  register-app         Register a terminal-browser application
  unregister-app       Unregister a terminal-browser application
  shutdown             Stop the daemon
  config               Get and set settings and shortcuts
  action               Use the open browser through the agent-browser CLI

terminal-browser <command> --help for one command's options
terminal-browser --version prints the installed version
```

```
$ terminal-browser open --help
Usage: terminal-browser open [url] [options]

Run this inside the new Rex block created by rex split, as shown above.

The url can be a normal url, a localhost port, or a path to an html file.

Options:
  --ssh <user@host>     Perform all network requests through a remote server, then
                        proxy the result back to the local terminal-browser instance
  --allow-clipboard-read
                        Lets websites read from clipboard.
  --transparent         [placeholder copy: Let the terminal show through pages that do not paint
                        a background. Persist it with terminal-browser config set window.transparent on]
  --no-merge            Do not open the terminal-browser instance as a tab in a neighbor terminal-browser


Examples:
  # Commands to run inside the new Rex block:
  terminal-browser open localhost:3000 --no-merge
  terminal-browser open /absolute/path/report.html --no-merge
  terminal-browser open --ssh dev@build-box localhost:8080 --no-merge
```

```
$ terminal-browser ls --help
Usage: terminal-browser ls --all --json

Lists every browser with its tabs. Use the browser key and tab id for actions.

Options:
  --all               Include browsers in other Rex blocks
  --json              Machine readable, including cdp ports and pane ids
```

```
$ terminal-browser setup --help
Usage: terminal-browser setup

Sets up configuration to make terminal-browser work best, this includes:
- installing agent skills
```

```
$ terminal-browser upgrade --help
Usage: terminal-browser upgrade

Checks this install's release channel and installs the latest version. Does
nothing when already up to date.
```

```
$ terminal-browser new-tab --help
Usage: terminal-browser new-tab --browser <key> [url]

Opens a tab in the explicitly selected browser. Discover the key with
terminal-browser ls --all --json. If no browser exists, create a Rex block
using the workflow above first.

Examples:
  terminal-browser new-tab --browser 90107-1 localhost:3000
```

```
$ terminal-browser clear-browsing-data --help
Usage: terminal-browser clear-browsing-data [options]

Clears cookies and site data, and cached images and files, for every site in
every terminal-browser window, signing you out. Asks first when run in a
terminal; otherwise needs --yes. Reload open pages to see the change.

Options:
  -y, --yes           Clear without asking
  --cookies           Only clear cookies and site data
  --cache             Only clear cached images and files
  --browser <key>     A browser key from terminal-browser ls

Examples:
  terminal-browser clear-browsing-data
  terminal-browser clear-browsing-data --yes --cookies
```

```
$ terminal-browser apps --help
Usage: terminal-browser apps [--json]

Lists the id, name, and binary path of registered terminal-browser apps. Apps can be registered
using terminal-browser register-app. If an app is registered it can be opened through the terminal-browser
new tab command palette after searching for its name.
```

```
$ terminal-browser register-app --help
Usage: terminal-browser register-app --name <name> --bin <path> [--id <id>] [--args "…"]

Registers metadata for a terminal-browser application to ~/.local/share/terminal-browser-interop/apps/<id>.json. This enables functionality
when a user is using terminal-browser, and lets other applications discover terminal-browser apps.
```

```
$ terminal-browser unregister-app --help
Usage: terminal-browser unregister-app <id>

Remove application metadata from ~/.local/share/terminal-browser-interop/apps/<id>.json.
```

```
$ terminal-browser shutdown --help
Usage: terminal-browser shutdown

Every browser in a terminal pane shares one browser process as an optimization. To
fully quit terminal-browser operations, you can use this shutdown command. This will
close all open browsers.
```

```
$ terminal-browser config --help
Usage: terminal-browser config <list|get|set|unset|path> [key] [value]

Reads and writes the settings.json and shortcuts.json files.

Settings are addressed by their settings.json key. Shortcuts are addressed as
shortcuts.<command> and take a comma separated list of key chords, or none to
unbind. unset restores the default.

Commands:
  list                 List every setting and shortcut with its current value
  get <key>            Print the value of one key
  set <key> <value>    Set a key
  unset <key>          Restore a key to its default
  path                 Print the paths of the config files

Examples:
  terminal-browser config list
  terminal-browser config get search.engine
  terminal-browser config set telemetry.usage off
  terminal-browser config set updates.check off
  terminal-browser config set shortcuts.tab.new "cmd+t,ctrl+t"
  terminal-browser config set shortcuts.record.toggle none
  terminal-browser config unset render.fps
  terminal-browser config path
```

```
$ terminal-browser action --help
Usage: terminal-browser action --browser <key> --tab <id> -- <command>

An agent-browser compatible CLI for the browser you already have open.
Everything after -- is an agent-browser command. Always select the browser
and tab explicitly when acting from a different Rex block.

Selectors:
  --browser <key>     A browser key from terminal-browser ls
  --tab <id>          A tab id from terminal-browser ls
  --target <id>       A CDP target id
  --follow            Bring the tab to the front before running the command

Examples:
  terminal-browser action --browser 90107-1 --tab 2 -- snapshot
  terminal-browser action --browser 90107-1 --tab 2 -- click @e14
  terminal-browser action --browser 90107-1 --tab 2 -- eval "document.title"
  terminal-browser action --browser 90107-1 --tab 2 -- fill @e3 "hello"
  terminal-browser action --browser 90107-1 --tab 2 done
```

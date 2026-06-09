---
name: invisible-playwright
description: "Use when an agent needs browser automation through invisible_playwright: a Playwright-compatible patched Firefox wrapper with coherent stealth fingerprints, proxy support, reproducible seeds, and humanized mouse movement."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [browser, playwright, firefox, stealth, automation, proxy, fingerprint]
    homepage: https://github.com/feder-cr/invisible_playwright
    related_skills: [dogfood, systematic-debugging, software-tool-discovery]
required_commands:
  - invisible-playwright
---

# Invisible Playwright

## What this skill is for

Use this skill when the task needs web automation through `invisible_playwright`, the Python package from https://github.com/feder-cr/invisible_playwright.

`invisible_playwright` is a drop-in Playwright-compatible wrapper around a patched Firefox build. It returns normal Playwright `Browser` / `BrowserContext` objects while adding:

- C++-level Firefox fingerprint spoofing, not JavaScript shims.
- Random coherent fingerprint per session, or reproducible fingerprint via `seed=`.
- Proxy support including authenticated SOCKS5.
- Timezone/locale alignment with proxy egress.
- Humanized Bezier mouse movement from the patched browser.
- Optional pinned fingerprint fields for specific test scenarios.
- Optional persistent profile directories for cookies/localStorage/session reuse.

Do not use this as a bypass for unlawful access, abuse, spam, account takeover, or violation of a site’s terms. Use it for legitimate testing, QA, research on properties you may access, and automation the user is authorized to run.

## Preflight checklist

Always do these before writing automation:

```bash
command -v invisible-playwright
invisible-playwright version
invisible-playwright path
```

If the binary is missing or corrupt:

```bash
invisible-playwright fetch
# or, using the module form in the Python environment that has the package:
python -m invisible_playwright fetch
```

If `python -c 'import invisible_playwright'` fails but the CLI works, the package may be installed in a tool-specific venv. Discover the interpreter from the console script:

```bash
IPW_BIN="$(command -v invisible-playwright)"
IPW_PY="$(head -1 "$IPW_BIN" | sed 's/^#!//')"
"$IPW_PY" -c 'import invisible_playwright; print(invisible_playwright.__file__)'
```

Then run your automation with `"$IPW_PY" script.py`, or install the package into the active project environment.

## Installation / setup

Preferred upstream install:

```bash
pip install 'git+https://github.com/feder-cr/invisible_playwright.git'
python -m invisible_playwright fetch
```

CLI commands:

```bash
invisible-playwright fetch          # download patched Firefox if missing
invisible-playwright fetch --force  # re-download current cached version
invisible-playwright path           # absolute path to cached Firefox binary
invisible-playwright version        # wrapper + binary/Firefox versions
invisible-playwright clear-cache    # remove cached binaries
```

Notes:

- Upstream README states Windows x86_64 and Linux x86_64 support. Current installed builds may also provide macOS binaries, but `headless=True` is not supported on macOS by the package’s virtual-display helper.
- On macOS, use headed mode (`headless=False`, the default). A direct local smoke test with headed mode succeeded; `headless=True` failed with `RuntimeError: invisible_playwright supports Windows and Linux only (got 'darwin')`.
- On Linux, `headless=True` uses a hidden virtual display while keeping Firefox’s real headed rendering path. Ensure Xvfb/display dependencies are available if launch fails.

## Basic synchronous usage

Prefer small scripts over long one-liners for browser work. Always close with the context manager.

```python
from invisible_playwright import InvisiblePlaywright

sf = InvisiblePlaywright(seed=12345)  # omit seed for fresh random fingerprint
print('seed =', sf.seed)              # log this for reproducibility

with sf as browser:
    page = browser.new_page()
    page.goto('https://example.com', wait_until='domcontentloaded')
    print(page.title())
```

The object yielded by the context manager is normally a Playwright `Browser`, so existing Playwright code works with `browser.new_page()`, `browser.new_context()`, locators, selectors, route interception, downloads, screenshots, etc.

## Basic async usage

```python
import asyncio
from invisible_playwright.async_api import InvisiblePlaywright

async def main():
    sf = InvisiblePlaywright(seed=12345)
    print('seed =', sf.seed)
    async with sf as browser:
        page = await browser.new_page()
        await page.goto('https://example.com', wait_until='domcontentloaded')
        print(await page.title())

asyncio.run(main())
```

## Proxies and timezone

Proxy dictionary format matches Playwright:

```python
proxy = {
    'server': 'socks5://gate.example.com:1080',
    'username': 'user',
    'password': 'REDACTED',
}

with InvisiblePlaywright(proxy=proxy) as browser:
    page = browser.new_page()
    page.goto('https://httpbin.org/ip')
    print(page.content())
```

Supported schemes: `socks5`, `socks4`, `http`, `https`.

Timezone behavior:

- Default `timezone=''` and `timezone='auto'` resolve timezone from egress IP.
- With a proxy, egress is the proxy IP. If proxy timezone cannot be resolved, launch raises instead of silently using the host timezone.
- Without a proxy, a failed lookup falls back to host timezone.
- Use explicit IANA zone to force a value: `timezone='America/New_York'`.
- Use `locale='en-US'` or another BCP-47 tag to align language headers and navigator language.

For WebRTC public IP alignment, set this in the process environment before launch if needed:

```bash
export STEALTHFOX_WEBRTC_PUBLIC_IP='203.0.113.10'
```

The launcher propagates it into Firefox for synthetic server-reflexive candidate injection.

## Persistent profiles

Use `profile_dir=` when cookies, cache, localStorage, extensions, or session state must persist.

Important: when `profile_dir` is set, the context manager returns a Playwright `BrowserContext`, not a `Browser`. Use the returned object directly.

```python
from pathlib import Path
from invisible_playwright import InvisiblePlaywright

profile_dir = Path('.profiles/example-account')

with InvisiblePlaywright(seed=4242, profile_dir=profile_dir) as ctx:
    page = ctx.new_page()
    page.goto('https://example.com')
```

Best practice:

- Pair persistent profiles with a stable `seed=` so browser identity and storage identity stay coherent.
- Keep one profile directory per logical browser identity/account.
- Do not commit profile directories to git.

## Fingerprint seeds and pinning

Default behavior: every `InvisiblePlaywright()` call gets a new coherent sampled profile.

Use `seed=` for reproducibility:

```python
with InvisiblePlaywright(seed=42) as browser:
    ...
```

Use `pin=` only when you know why you need specific fields. Pin correlated fields together; otherwise you can create implausible combinations.

Safer high-level steering:

```python
pin = {'gpu.class_tier': 'mid_range'}
with InvisiblePlaywright(seed=42, pin=pin) as browser:
    ...
```

Specific device-like tuple:

```python
pin = {
    'gpu.vendor': 'Google Inc. (Intel)',
    'gpu.renderer': 'ANGLE (Intel, Intel(R) Iris(R) Xe Graphics Direct3D11)',
    'gpu.class_tier': 'mid_range',
    'screen.width': 1920,
    'screen.height': 1080,
    'screen.dpr': 1.0,
    'hardware.concurrency': 8,
    'audio.sample_rate': 48000,
}
with InvisiblePlaywright(seed=42, pin=pin) as browser:
    ...
```

Common pinnable keys include:

- `gpu.class_tier`, `gpu.vendor`, `gpu.renderer`
- `screen.width`, `screen.height`, `screen.avail_width`, `screen.avail_height`, `screen.dpr`, `screen.tier`
- `hardware.concurrency`, `hardware.storage_quota_mb`
- `audio.sample_rate`, `audio.output_latency_ms`, `audio.max_channel_count`
- `codec.av1_enabled`, `codec.webm_encoder_enabled`, `codec.mediasource_webm`, `codec.mediasource_mp4`, `codec.webspeech_synth`
- `webgl.msaa_samples`
- `fonts`, `dark_theme`

See upstream `docs/pinning.md` for the full rationale.

## Humanized mouse movement

Default: `humanize=True`, which expands mouse moves/clicks into Bezier trajectories with a default max of about 1.5 seconds.

```python
InvisiblePlaywright(humanize=True)     # default
InvisiblePlaywright(humanize=False)    # disable
InvisiblePlaywright(humanize=0.75)     # cap movement duration in seconds
```

Use Playwright actions normally:

```python
page.click('#submit')
page.locator('text=Continue').click()
```

## Extra browser configuration

Forward extra Firefox args:

```python
InvisiblePlaywright(extra_args=['--width=1280', '--height=900'])
```

Overlay extra Firefox prefs on top of the generated stealth prefs:

```python
InvisiblePlaywright(extra_prefs={'media.navigator.enabled': False})
```

Use an explicit binary path only when diagnosing cache issues:

```python
InvisiblePlaywright(binary_path='/absolute/path/to/firefox')
```

## Recommended automation workflow for agents

1. Run preflight (`command -v`, `version`, `path`).
2. Decide whether the task needs fresh identity, reproducible identity, or persistent profile:
   - Fresh: omit `seed` and `profile_dir`; log `sf.seed`.
   - Reproducible test: set `seed` and log it.
   - Stateful account/session: set both stable `seed` and `profile_dir`.
3. If using a proxy, pass the full proxy dict at launch and let timezone auto-resolve unless the user explicitly gives an IANA zone.
4. Avoid `headless=True` on macOS. On Linux/Windows, use it only if the user wants hidden browser execution.
5. Use Playwright’s robust locator/wait patterns:
   - `page.goto(url, wait_until='domcontentloaded')`
   - `locator = page.get_by_role(...)` or `page.locator(...)`
   - `locator.wait_for()` before interaction when the page is dynamic.
6. Save useful artifacts when debugging:
   - screenshots: `page.screenshot(path='artifact.png', full_page=True)`
   - HTML: `Path('artifact.html').write_text(page.content())`
   - seed/profile/proxy zone in a plain log, without secrets.
7. Always close via context manager or explicit `browser.close()`/`ctx.close()`.

## Smoke tests

Minimal import/CLI check:

```bash
invisible-playwright version
invisible-playwright path
python - <<'PY'
from invisible_playwright import InvisiblePlaywright
sf = InvisiblePlaywright(seed=123)
print(sf.seed)
PY
```

Headed launch smoke test:

```python
from invisible_playwright import InvisiblePlaywright

sf = InvisiblePlaywright(seed=123)
with sf as browser:
    page = browser.new_page()
    page.goto('data:text/html,<title>ok</title><h1>ok</h1>', wait_until='load')
    assert page.title() == 'ok'
print('ok')
```

Linux/Windows hidden launch smoke test:

```python
from invisible_playwright import InvisiblePlaywright

with InvisiblePlaywright(seed=123, headless=True) as browser:
    page = browser.new_page()
    page.goto('data:text/html,<title>ok</title>', wait_until='load')
    assert page.title() == 'ok'
print('ok')
```

## Troubleshooting

### `ModuleNotFoundError: invisible_playwright`

The CLI may be installed via `uv tool` or another venv, while `python` points elsewhere. Use the CLI shebang-discovered interpreter:

```bash
IPW_PY="$(head -1 "$(command -v invisible-playwright)" | sed 's/^#!//')"
"$IPW_PY" your_script.py
```

Or install into the active environment:

```bash
python -m pip install 'git+https://github.com/feder-cr/invisible_playwright.git'
python -m invisible_playwright fetch
```

### Binary missing / checksum / corrupt cache

```bash
invisible-playwright fetch --force
invisible-playwright path
```

If still broken:

```bash
invisible-playwright clear-cache
invisible-playwright fetch
```

### macOS `headless=True` failure

Use default headed mode on macOS:

```python
InvisiblePlaywright(seed=123)  # no headless=True
```

The package’s headless virtual-display helper currently raises on `darwin`.

### Navigation interrupted by `about:newtab`

The package patches `new_page()` to sleep briefly after tab creation. If you still see navigation races, add an explicit short wait before first `goto()` or create a context first:

```python
ctx = browser.new_context()
page = ctx.new_page()
page.wait_for_timeout(500)
page.goto(url, wait_until='domcontentloaded')
```

### Proxy timezone mismatch

If launch fails while a proxy is set and timezone is automatic, either fix the proxy/egress lookup or pass an explicit IANA zone that matches the proxy location:

```python
InvisiblePlaywright(proxy=proxy, timezone='America/New_York')
```

### Persistent profile returns the wrong object type

Without `profile_dir`: context manager returns `Browser`.

With `profile_dir`: context manager returns `BrowserContext`.

Use this pattern:

```python
if profile_dir:
    with InvisiblePlaywright(seed=seed, profile_dir=profile_dir) as ctx:
        page = ctx.new_page()
else:
    with InvisiblePlaywright(seed=seed) as browser:
        page = browser.new_page()
```

## Verification performed for this project-local skill

At creation time in this repository:

- `invisible-playwright version` returned `invisible_playwright 0.2.0`, `BINARY_VERSION=firefox-9 (Firefox 150.0.1)`.
- `invisible-playwright path` resolved to a cached Firefox binary under `~/.cache/invisible-playwright/firefox-9/`.
- A headed smoke test on macOS loaded a data URL and returned title `ok`.
- A macOS `headless=True` smoke test failed as documented above, so this skill explicitly warns agents not to use `headless=True` on macOS.

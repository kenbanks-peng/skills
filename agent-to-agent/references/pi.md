# Pi

Use the **pi-a2a** extension (`@bacnh85/pi-a2a`):
<https://github.com/bacnh85/pi-extensions/tree/main/pi-a2a>.

1. Check whether the extension is installed. Missing tools alone do not prove that it is absent; they can be deferred or need a session reload.
2. If the extension is missing, install it:

   ```bash
   pi install npm:@bacnh85/pi-a2a
   ```

   Perform the installation yourself. If permissions or network access block it, report the specific blocker.
3. After installation, reload the Pi session with `/reload`. This is a Pi session command, not a shell command. Use a supported session interface if available; otherwise ask the user to run `/reload`.
4. Confirm that the extension's A2A tools are available. Activate deferred tools through the host's tool-discovery mechanism when needed.
5. Find and read the extension's **a2a** skill. Use it as the source of truth for discovery, calls, follow-ups, and inbound configuration. If that skill is unavailable, read the installed README and live tool schemas, or the upstream documentation linked above.

Installing the extension does not authorize starting an inbound server. Apply the inbound-access rules in `SKILL.md`.

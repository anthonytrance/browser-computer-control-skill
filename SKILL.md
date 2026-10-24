---
name: browser-computer-control
description: Use Hermes Browser or Browser Use for web pages, and CUA Driver for Windows applications, existing browser windows, and native dialogs. Use for browser interaction, rendered-page testing, screenshots, accessibility, and troubleshooting Chrome attachment or consent.
---

# Browser and Computer Control

If `LOCAL.md` exists beside this file, read it first. It holds this installation's paths and preferences, and where it differs from this file, it wins.

The user's normal Chrome profile, with its saved logins and existing sessions, is the required default for their browser tasks. Verify that Hermes is attached to that profile before using it for ordinary browsing; an unbound `browser_exec` may launch packaged Chromium with no logins. Use CUA for exact attachment and native UI, then Hermes or the Browser Use wrapper on the verified normal-Chrome connection. Choose the context once and reuse it. Packaged Chromium is reserved for explicitly isolated work or project tests. A Chrome debugging consent prompt is a pending permission decision, not evidence that another CDP client will work better.

## Choose the route

1. Prefer a purpose-built API, connector, or site CLI when it can perform and verify the task. For public research, load `web-research`: use callable host-native search/fetch tools or configured Hermes web tools, with the shared CLI as fallback. Search and page extraction can use keyless services without attaching a browser. See [Hermes web and browser changes](references/hermes-web-browser.md) before changing backend settings.
2. For page interaction, prefer exposed Hermes browser tools only when they are bound to the intended normal-Chrome context. Discover deferred Hermes/CUA tools once if needed. If Hermes has no verified connection, use CUA and the [normal-Chrome wrapper](references/browser-use.md) to attach; do not invoke an unbound browser tool as a setup shortcut. Hermes `browser_exec` uses Browser Harness / Browser Use, whose packaged-Chromium default does not carry the user's logins. Discover the actual backend and helpers before using version-specific features. Switching clients on the same normal-Chrome endpoint does not bypass Chrome consent.
3. Use CUA Driver for exact browser attachment, browser toolbars, native dialogs, Firefox UI, and Windows applications. For Chrome page work, hand off to Hermes/Browser Use once the intended connection is ready. CUA's native UI Automation and screenshot actions work without a CDP endpoint. **Do not call `browser_prepare` just to inspect or click a browser window.**
4. If Hermes is unavailable, use the installed Browser Use CLI with the wrapper in [Browser Use](references/browser-use.md), normally with `--normal-chrome`. Use an isolated browser for explicitly separate work or a project's tests that do not need personal sessions. Repository Playwright is appropriate for a project's own browser tests.
5. Use standalone raw CDP only for a demonstrated limitation of the higher-level tool on an explicitly selected isolated browser. Prefer Browser Use's `cdp(...)` helper when that connection works. A pending prompt, unavailable MCP tool, or stopped CUA daemon is not such a limitation.

In TeleCode, do not probe the bundled in-app Browser plugin unless the user explicitly asks to test it. Missing MCP tools do not mean the installed CLIs are unavailable. If TeleCode explicitly reports MCP disabled, mention `/mcp on` and continue through an applicable CLI when possible.

## Choose the context before connecting

- **Ordinary browser work, saved logins, or an existing signed-in tab:** prefer normal Chrome. Reuse a verified Hermes/Browser Use connection. Otherwise use CUA to identify the exact window and handle the setup described in [Chrome attachment and consent](references/chrome-consent.md), then retain one persistent page connection. Do not silently switch profiles or ask the user to sign in again. For one simple native action, CUA alone may finish faster than attachment setup.
- **Explicitly separate browsing or localhost tests:** reuse the task's isolated browser, or prepare one through CUA as described in [CUA Driver](references/cua-driver.md). Pin Browser Use to its verified user-data directory. A named tool session or daemon alone does not create an isolated browser.
- **An existing isolated session:** preserve it, including any login the user completed there. Do not create another profile for each call or because its CUA session expired.

Verify profile ownership when attaching or recovering, not before every page action. A URL, title, cookie, or successful login is not proof of which browser profile owns the connection. Keep the PID, window/tab identity, profile path, and daemon/session name available for subsequent calls.

## Work efficiently

Batch a short sequence of related page actions with its readback. Use targeted DOM or accessibility queries for text and controls; use screenshots for layout, visual state, or when the tree is insufficient. Refresh CUA element indices before acting and after the window changes. Inspect only the target window unless its capture cannot cover the dialog.

For CUA startup, exact tool calls, and keeping its daemon alive across TeleCode turns, read [CUA Driver](references/cua-driver.md). Use the detached launcher for long-lived processes. Do not infer that CUA is unreliable merely because a previous shell-owned process disappeared.

## Recover by failure type

| Observed problem | Next action |
| --- | --- |
| Chrome asks to allow debugging, or handshake stalls with that prompt | Keep one attachment attempt pending; inspect the native prompt with CUA. Follow the consent reference. Do not cycle through clients. |
| CUA reports daemon unavailable | Check `cua-driver status` for the correct socket. Start a detached daemon if needed, then retry the affected read. |
| Stale or wrong browser endpoint | Check the browser process and its own endpoint file. Rebind only to the intended context. |
| Action timed out | Inspect the result before retrying. It may already have executed. |
| A selector or element is stale | Refresh relevant page/window state and target again. Reconnecting will not fix a stale selector. |
| One backend cannot perform the operation | Use the next applicable route while preserving browser context and authorization. |

Make one targeted recovery for the observed cause, then reassess from new evidence. Do not loop through equivalent clients or repeat an unchanged failed setup. If a grant is denied, another interface must not be used to bypass that denial.

Site-specific skills and the user's existing authorization govern account actions. Do not invent another approval gate for routine authorized work. Use credentials only for the authorized login, without logging or saving them. When user participation is needed for sign-in or MFA, describe the state and bring the intended browser window forward so the user, or their screen reader, lands on it.

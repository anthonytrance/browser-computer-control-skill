# CUA Driver on Windows

Prefer exposed CUA tools. If only the CLI is available, discover individual schemas with `cua-driver describe TOOL`; use `list-tools` only when the tool name is unknown. `describe` does not require a running daemon. `call` does.

## Daemon lifecycle in TeleCode

Check `cua-driver status` for the endpoint you intend to use. An embedded host can own a private socket even when the default CLI socket is unavailable. Do not infer from a process name alone that a usable default daemon exists.

If no suitable daemon is running, start one through the required detached launcher (`$python` and `$launcher` as in [Browser Use](browser-use.md)):

```powershell
& $python $launcher --log 'LOG_FOLDER\cua-driver.log' "$env:LOCALAPPDATA\Programs\Cua\cua-driver\bin\cua-driver.exe" serve
```

Capture the PID, then check status in a subsequent tool call. The launcher must exit and leave no visible console. Keep this daemon across related actions. If creating a task-owned private daemon, use `serve --socket ENDPOINT` and repeat `--socket ENDPOINT` on `call`, `status`, and `stop`. Do not stop or replace a shared or host-owned daemon.

A vanished process is not always a launch problem. Local checks on 2026-09-07 recorded access violations in Windows `uiautomationcore.dll` with both CUA 0.22.0 and 0.24.0. On 0.24.0 a bounded tree read succeeded, but the driver crashed during a later click/capture sequence. Check status and the relevant Windows Application Error event when a connection closes without a response. One restart and a narrower observation is a reasonable recovery; success once does not prove the crash is fixed. Preserve any working Hermes connection and report a repeated driver crash rather than changing profiles or retrying indefinitely. Check `cua-driver check-update --json` for a reproducible driver failure, not before every task.

Do not add `--grant existing-profile` for ordinary UI work. Add it only for already-authorized existing-profile CDP preparation. Runtime grants are fixed at startup; neither a named session nor broad shell permissions substitutes for them. Do not use unrestricted/bypass modes to recover from a refusal.

## Native UI workflow

Start with `list_windows`, optionally filtered by PID. It already returns app identity, PID, window ID, bounds, and visibility, so a preceding `list_apps` call is unnecessary unless process-level discovery is needed.

```powershell
'{}' | cua-driver call list_windows
```

Pass JSON on stdin because Windows PowerShell can strip quotes from positional JSON. For the exact target:

```powershell
'{"pid":1234,"window_id":5678,"session":"task-ui","max_elements":150,"max_depth":10,"include_screenshot":false}' | cua-driver call get_window_state
```

Replace the example IDs with observed values. `query` filters the returned tree but does not necessarily reduce the walk; `max_elements` and `max_depth` bound it. Request a screenshot for visual grounding, layout, or a dialog the tree cannot explain. Use `screenshot_out_file` or the CLI's `--screenshot-out-file` to avoid printing base64, then inspect the actual image with the host's image viewer tool.

The installed 0.24.0 also accepts `include_accessibility_tree:false` with `include_screenshot:true` to request pixels and window metadata without the full tree. `max_dimension` limits screenshot size. Do not set both include flags false. Use this when only pixels are needed; it has not been established as a workaround for the local crash. See the [0.24.0 release notes](https://github.com/trycua/cua/releases/tag/cua-driver-rs-v0.24.0).

Repeat the session label on calls accepting `session`. Refresh the same window's state once per turn before element actions, and whenever the UI changes. Prefer the returned `element_token`; on 0.24.0 an `element_index` needs its matching `snapshot_id`. The `actions` array identifies supported native actions. Use `describe click`, `describe type_text`, or the relevant action before unfamiliar parameters. Prefer UI Automation actions when the element is reliable; use observed screenshot coordinates when needed. Keep the default background delivery first, escalating only after the driver's explicit failure or a verified no-op. Read back the result, since an `effect: unverifiable` response is not proof the click worked. End only your named session with `end_session` when finished.

Chrome permission bubbles can extend outside a window snapshot. Follow `capture_coverage` and the consent reference for desktop escalation; do not repeatedly click the same ineffective index.

## Isolated browser for public or local work

First reuse the task's existing isolated browser if it is still alive. Otherwise inspect `describe browser_prepare`, then:

```powershell
'{"allow_launch":true,"profile":{"mode":"isolated_named","name":"task-browser"},"session":"task-ui"}' | cua-driver call browser_prepare
```

Use a meaningful unique task name. Check `prepared_pid`, `endpoint_ownership`, and `side_effects.copied_profile_data: false`. For a fresh launch, also expect `side_effects.launched_browser: true`. If the report omits the user-data directory, read the exact `prepared_pid` process command line and its `--user-data-dir`, for example with `Get-CimInstance Win32_Process -Filter 'ProcessId=OBSERVED_PID'`. Pass that directory to Browser Use's `--user-data-dir`; do not guess the profile path or bypass Browser Use merely because CUA performed the launch.

An isolated browser is suitable when a personal session is unnecessary or the user selected that context. Once a user signs in there, preserve that session. Firefox native UI can use CUA without Chromium CDP. Clean up only task-owned browsers and temporary sessions when they are no longer needed.

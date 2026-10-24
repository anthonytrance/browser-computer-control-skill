# Browser Use on this Windows host

Hermes `browser_exec` and the installed `browser-use` CLI share the Browser Use harness. Prefer the exposed tool when its connection is already suitable. Do not start a second client merely because an operation can also be expressed as raw CDP.

## Exact CLI connection

The examples use three PowerShell variables: `$python`, an interpreter with this skill's `requirements.txt` installed; `$skill`, this skill's folder; and `$launcher`, a detached launcher script (see below). `LOCAL.md` gives this installation's values. Resolve script paths from this skill directory.

The wrapper requires `--user-data-dir PATH`, `--normal-chrome`, or explicit `--discover`. Use `--normal-chrome` for the user's everyday browser work and saved sessions; use `--user-data-dir` for an explicitly selected separate context. It checks the endpoint's listener process, rejects the wrong user-data directory, and derives a stable daemon name from the endpoint. For normal Chrome it then uses Browser Harness's patient local-Chrome handshake, so the exact pending connection remains alive while Chrome's consent prompt is handled. `--check` returns connection metadata without a WebSocket handshake or a Chrome permission prompt. It does not prove that attachment has been approved.

```powershell
& $python "$skill\scripts\run_browser_use.py" --user-data-dir 'EXACT_PATH_FROM_BROWSER_PREPARE' --check
```

On an established connection:

```powershell
$OutputEncoding = [Text.UTF8Encoding]::new($false)
@'
new_tab("https://example.com")
wait_for_load()
print(page_info())
'@ | & $python "$skill\scripts\run_browser_use.py" --user-data-dir 'EXACT_PATH_FROM_BROWSER_PREPARE'
```

The wrapper strips PowerShell's stdin BOM, uses UTF-8, and removes inherited Python and conflicting browser endpoint overrides. Set `$OutputEncoding` as above before piping non-ASCII text: PowerShell 5.1 can replace characters before Python receives them. Alternatively use a UTF-8 `--code-file`. Keep the same arguments across calls. `--discover` is only for a deliberately unconstrained browser context; it can select another profile and trigger normal-Chrome setup. Never use it to recover from failure of an exact connection.

## First attachment and process lifetime

The CLI can auto-start a persistent harness daemon. In TeleCode, launch the first attachment through the detached launcher, so its child survives the tool call without inheriting TeleCode handles. The launcher must start the command as a detached process with no console window, with standard input, output and error redirected (output to the `--log` file), and print the child PID. Save a **read-only** bootstrap such as `print(page_info())` in a task-local Python file, then:

```powershell
& $python $launcher --log 'TASK_PATH\attach.log' $python "$skill\scripts\run_browser_use.py" --user-data-dir 'EXACT_PATH_FROM_BROWSER_PREPARE' --code-file 'TASK_PATH\attach.py'
```

Capture the launcher PID, inspect the log, and verify the bootstrap process exits and leaves no console window. A successful launcher exit only confirms scheduling. For normal Chrome, use `--normal-chrome` and follow the consent reference while that attempt is pending. Do not put passwords or consequential actions in a bootstrap file.

After attachment succeeds, subsequent bounded calls can use stdin directly. If the browser or daemon exits, return to first attachment rather than repeatedly invoking a dead connection. A timeout does not establish whether code ran. Read back the result before repeating an action. The wrapper bounds the foreground client only; an already-started daemon can remain alive. Keep Browser Harness current, because versions before 0.1.13 do not preserve the Windows normal-Chrome approval attempt correctly.

## Page helpers

Use `new_tab(url)` for the first navigation, `goto_url(url)` for the task's current tab, `wait_for_load()`, `page_info()`, `js(expression)`, and `fill_input(selector, text)`. Read `list_tabs()` and explicitly select the intended tab for existing-tab work. Session names separate daemons; they do not prove tab or profile identity. Browser connection/tab state persists; ordinary Python variables do not.

Use `browser-use skill` for unfamiliar helpers. Use `browser-use --doctor` only when diagnosis calls for it, with the same daemon and endpoint environment from `--check`. An unqualified doctor can diagnose a different daemon. Do not dump full accessibility trees when a filtered result will do.

### Verify application transitions

`wait_for_load()` does not prove that a single-page application's route or data request has finished. After a click, wait for the expected heading, URL, dialog, or changed control state before continuing. A later read can reveal that the original click succeeded; inspect before retrying.

On Wise, an accessibility button's box can cover only the small chevron inside a larger associated label. After a verified ineffective coordinate click, inspect the visible label and its `for` control. A targeted DOM `click()` on that observed label or control worked for statement navigation and currency selection on 2026-10-01. Recheck the exact page and resulting state; this is a fallback for an observed UI control, not permission to invoke hidden application operations.

For React multi-selects, change one selection, allow its state to commit, then inspect the selection again. Clicking several "Select all" controls in one JavaScript evaluation can overwrite earlier selections. Verify the final selected set, including removed or closed balances when historical coverage requires them.

Keep a temporary `Browser.setDownloadBehavior` override active until the requested file finishes or an authentication gate is observed, then restore `behavior='default'` in `finally`. Generating a document and downloading it can be separate steps. A click acknowledgement or empty download directory is not a completed export.

With `behavior='allow'`, a later download can overwrite an existing file with the same name. Use a unique empty directory for each export run, then validate the completed file. Watching only for new filenames in a shared destination can miss a successful download.

## Standalone CDP, limited fallback

Keep [../scripts/cdp_direct.py](../scripts/cdp_direct.py) for existing callers and isolated-browser operations a working higher-level connection cannot support. It requires an explicit `--base` and refuses missing or ambiguous targets. Use `--list` followed by `--target-id`, or a unique `--match`. Never silently use another tab when a match fails.

This helper opens a fresh WebSocket per call. It cannot bypass Chrome consent and is inefficient as the default action loop. It is not for the normal Chrome profile. A `/json/list` or `/json/version` failure on normal Chrome does not prove its Chrome-written WebSocket endpoint is dead.

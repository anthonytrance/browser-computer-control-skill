# Existing Chrome attachment and consent

Use this only when page-level CDP access to an existing personal browser is needed. Native CUA window inspection and actions do not require `browser_prepare` or remote debugging.

The user's normal Chrome user-data directory is `%LOCALAPPDATA%\Google\Chrome\User Data`, normally with profile directory `Default`. Inspect the root Chrome command line and exact window. A different `--user-data-dir` means a different browser context, even if it contains the same account login. Reuse the signed-in session and authorized ordinary browser autofill instead of requesting credentials unnecessarily. Do not extract saved passwords or copy cookies/profile files to manufacture an attachment.

## Three different states

1. **CUA runtime authorization:** preparing an existing profile requires the runtime's existing-profile grant (or supported host authorization). `cua-driver describe browser_prepare` documents the installed contract. A generic tool execution approval does not supply this grant.
2. **Chrome instance setup:** with authorized preparation, CUA can enable the instance's remote-debugging option. This exposes an endpoint; it does not authorize every later client.
3. **Chrome client consent:** each new CDP connection may show Chrome's own Allow prompt. Switching from CUA's browser tools to Hermes, Browser Use, Playwright, or raw CDP can cause another prompt.

Check the conversation for existing authorization before asking again. If the user already authorized this profile attachment and its Chrome Allow action, handle the exact prompt through CUA. Otherwise, if attachment is necessary, explain the specific permission Chrome or CUA requires and ask once. Routine native browser work can proceed without setting up debugging, provided this does not bypass an explicit denial.

## Attach once

1. Reuse a verified existing page connection when available. Otherwise obtain exact `pid` and `window_id` through native CUA. Do not generically discover another endpoint.
2. If setup is needed and authorized, call `browser_prepare` with that `pid`, `window_id`, and `strategy: {"kind": "existing_profile"}`. The daemon must already have the authorized grant. Do not restart another task's daemon to change its grants.
3. Check preparation for exact binding and ownership. For the installed driver, the relevant successful fields are `binding_quality: exact`, `endpoint_access_class: existing_profile_approved`, matching owner/listener PIDs, and false `copied_profile_data`, `created_profile`, and `reused_driver_profile`. If the schema changes, inspect the report instead of assuming success.
4. Start the intended persistent Browser Use connection with `--normal-chrome`, or retain the already-working CUA browser connection. Do not connect several clients to test the endpoint. The wrapper verifies the normal profile's Chrome-written `DevToolsActivePort`, then enters Browser Harness's patient local-Chrome handshake so the consent prompt remains tied to one live attempt.
5. While attachment is pending, inspect Chrome's native prompt through CUA. Use fresh `get_window_state` indices and its screenshot. If a browser-owned bubble lies outside window capture, consult `capture_coverage`; after an ineffective window action, use the driver's documented `escalate_session` and fresh desktop observation. Do not use DOM selectors or a page-JavaScript-dialog tool for this native prompt.
6. After the authorized Allow action, verify the **same pending connection** completes, then reuse its daemon/session and target. Do not restart it after a successful approval.

## When the attempt expires

Do not invoke Browser Harness directly with `BU_CDP_WS` for normal Chrome. That marks the connection as remote and bypasses its patient local-Chrome consent handling. Use the skill wrapper with `--normal-chrome`; explicit WebSocket mode remains appropriate for a selected isolated profile that does not require the normal-profile consent flow.

Do not click a stale prompt and assume it approved a future client. If the initiating attempt has ended, establish that fact, then make one coordinated fresh attempt only when the required approval can be handled. Never keep several pending attempts. If this remains impractical, use authorized native CUA actions and report the attachment limitation. Avoid disabling Chrome protections, copying profiles, or silently changing the account context.

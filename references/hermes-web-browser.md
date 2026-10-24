# Hermes web and browser changes

Verified 2026-10-22 against Hermes v0.22.4. Read this reference when choosing a web backend or adapting browser instructions after an update.

## Public research

Load the shared `web-research` skill. Prefer callable Hermes `web_search` and `web_extract` with a verified backend. These are search/extraction tools, separate from browser automation. Keep the existing research CLI as fallback for other hosts, unavailable native tools, or unsuccessful extraction; it uses the research skill's own Python environment, not Hermes's managed Python.

Hermes supports keyless Firecrawl, Exa, Parallel and Keenable, with rate-limit failover and a keyless rescue path. Existing configured backends take priority. An installation may route its per-capability web backends through a `research-bridge` plugin; switching them to keyless `firecrawl` for search and extraction is reasonable after a successful native-provider probe. Keep the research bridge plugin and shared CLI available for fallback and rollback. Inspect live settings rather than assuming an update changes a backend selection.

For an approved switch to Firecrawl, inspect current credentials and settings first. With no Firecrawl API key or self-hosted URL present, selecting `firecrawl` for the per-capability search/extract backends uses the anonymous cloud endpoint. An existing key selects a keyed route instead. Preserve the existing bridge and its CLI for rollback and fallback. Test search and extraction before reporting the route usable.

Firecrawl's public pricing lists 1,000 free credits per month, not 1,000 arbitrary requests: basic scraping costs one credit per page and search costs two credits per ten results. Keyless `/v2/search` and `/v2/scrape` succeeded without an Authorization header on this host on 2026-10-22. That probe does not establish the anonymous quota remaining. Hermes's web docs still list the older 500-credit allowance; use Firecrawl's current pricing for the plan figure and inspect live failures for actual availability.

Firecrawl cloud *browser automation* is a separate configured provider requiring a key. Do not infer that a keyless search or scrape allowance includes an interactive cloud browser.

## Browser compatibility

The user's normal Chrome is the required default for browser tasks. Use a verified connection to `%LOCALAPPDATA%\Google\Chrome\User Data`, normally profile `Default`. If Hermes is not already bound to it, use the existing CUA consent workflow and `run_browser_use.py --normal-chrome`. An unbound Hermes call is not an acceptable fallback: it can open a clean browser. Packaged Chromium is limited to explicitly isolated work or project tests. Public Firecrawl search/extraction is separate from this browser-profile choice.

Hermes's `browser.use_real_profile: true` is a snapshot/copy feature, not attachment to the browser the user normally uses. Do not enable it to satisfy this preference. Keep the existing live-profile attachment workflow; do not copy cookies/profile files or close Chrome to manufacture a snapshot. A failed or consent-pending normal-Chrome attachment must be handled through the existing skill, not by silently substituting an empty profile.

In v0.22.4, Browser Use / Browser Harness is the default driver when available. With no selected cloud browser or explicit endpoint, it drives Hermes's packaged Chromium. This is separate from the user's normal Chrome and has none of their saved sessions by default. Keep normal Chrome as the primary context for their ordinary signed-in browsing and existing tabs, using the existing CUA attachment and consent workflow. Never silently substitute an empty profile for an authenticated task.

Modern Hermes `browser_exec(session=...)` isolates its harness and browser per session on supported backends. A standalone CLI daemon/session name by itself is still not proof of a separate browser profile. Verify endpoint, PID and user-data-directory ownership when attaching or recovering. Reuse the chosen connection.

Older Hermes or other hosts may expose built-in `browser_navigate` / `browser_snapshot` tools instead, or no Hermes tools. Use the callable surface actually present and retain Browser Use CLI, CUA Driver and project Playwright routes. Keep the TeleCode restriction on probing the bundled OpenAI Browser runtime.

Do not install or upgrade packages merely because a newer workflow names them. If the Hermes config disables lazy installs, preserve that choice and any separate Python environments.

Sources:
- https://github.com/NousResearch/hermes-agent/releases/tag/v0.22.4
- https://hermes-agent.nousresearch.com/docs/user-guide/features/browser
- https://hermes-agent.nousresearch.com/docs/user-guide/features/web-search
- https://www.firecrawl.dev/pricing

# Browser and computer control skill

Instructions and helper scripts that let an AI agent work in your own Chrome, with your saved logins, and in ordinary Windows programs and dialogs. Its rules cover which tool to use for which job, attaching to the right browser profile instead of an empty one, handling Chrome's "allow remote debugging" prompt once, and recovering from failures without looping. It was written with screen reader users in mind: it brings the right window forward when you need to sign in yourself.

It routes work to three tools you install separately: Hermes Agent's browser tools when present, the Browser Use command line program, and CUA Driver for Windows interface automation.

## What you need

1. Windows 10 or 11, Python 3.10 or newer, and Google Chrome.
2. Browser Use 0.13.8: `uv tool install browser-use==0.13.8` (uv is at https://docs.astral.sh/uv/).
3. CUA Driver, from https://github.com/trycua/cua, for Windows windows, dialogs and the Chrome consent prompt.
4. A detached launcher script: something that starts a command as a detached process with no console window, redirects its input and output to a log file, and prints the child's process ID. The references call it `$launcher`.

## Setup

1. Clone this repository into your agent's skills folder, for example `%USERPROFILE%\.claude\skills\browser-computer-control`.
2. Install the packages: `python -m pip install -r requirements.txt`.
3. Create a `LOCAL.md` beside `SKILL.md` that sets the three PowerShell variables the references use: `$python` (your interpreter), `$skill` (this folder) and `$launcher` (your launcher script). git ignores this file.
4. Check a connection without triggering any prompt: `& $python "$skill\scripts\run_browser_use.py" --normal-chrome --check`.

## Tests

Run `python -m pytest scripts/tests`. The tests are offline.

## Licence

MIT; see `LICENSE`.

## Privacy

The skill never copies browser profiles, cookies or saved passwords. The pre-commit hook in `.githooks` runs `tools/check_secrets.py` to block tokens and words from your private word list.

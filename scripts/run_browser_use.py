#!/usr/bin/env python3
"""Run Browser Use with explicit browser selection and bounded foreground work."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys


def normal_chrome_dir() -> Path:
    local = os.environ.get("LOCALAPPDATA")
    if not local:
        raise RuntimeError("LOCALAPPDATA is unavailable")
    return Path(local) / "Google" / "Chrome" / "User Data"


def path_key(path) -> str:
    value = str(Path(path).expanduser().resolve())
    if value.startswith("\\\\?\\"):
        value = value[4:]
    return os.path.normcase(value)


def profile_from_process(name: str, argv: list[str]) -> Path:
    if name.lower() not in {"chrome.exe", "chromium.exe", "msedge.exe"}:
        raise RuntimeError("endpoint listener is not a supported Chromium process")
    if any(arg == "--type" or arg.startswith("--type=") for arg in argv):
        raise RuntimeError("endpoint listener is not the root browser process")
    for i, arg in enumerate(argv):
        if arg.startswith("--user-data-dir="):
            value = arg.split("=", 1)[1]
            if value:
                return Path(value)
        if arg == "--user-data-dir" and i + 1 < len(argv) and argv[i + 1]:
            return Path(argv[i + 1])
    if name.lower() == "chrome.exe" and "--user-data-dir" not in argv and not any(
        arg.startswith("--user-data-dir=") for arg in argv
    ):
        return normal_chrome_dir()
    raise RuntimeError("cannot determine the listener's user-data directory")


def listener_pid(port: int, profile: Path) -> int:
    try:
        import psutil
    except ImportError as exc:
        raise RuntimeError("use a Python with this skill's requirements.txt installed (psutil)") from exc
    try:
        owners = {
            row.pid
            for row in psutil.net_connections(kind="tcp")
            if row.status == psutil.CONN_LISTEN and row.laddr.port == port
            and row.laddr.ip in {"127.0.0.1", "::1"} and row.pid
        }
        if len(owners) != 1:
            raise RuntimeError("endpoint has no unique live loopback listener")
        pid = owners.pop()
        proc = psutil.Process(pid)
        actual = profile_from_process(proc.name(), proc.cmdline())
        if path_key(actual) != path_key(profile):
            raise RuntimeError("endpoint listener belongs to a different browser profile")
        return pid
    except psutil.Error as exc:
        raise RuntimeError("cannot verify endpoint listener ownership") from exc


def endpoint_for_profile(profile: Path) -> dict:
    profile = profile.expanduser().resolve()
    active_port = profile / "DevToolsActivePort"
    try:
        lines = active_port.read_text(encoding="utf-8-sig").splitlines()
        port = int(lines[0].strip())
        ws_path = lines[1].strip()
    except (OSError, ValueError, IndexError) as exc:
        raise RuntimeError(
            "selected browser has no readable endpoint file; use native CUA, "
            "or prepare this exact profile if CDP is needed and authorized. "
            "Do not retry with automatic discovery."
        ) from exc
    if not 1 <= port <= 65535 or not re.fullmatch(r"/devtools/browser/[A-Za-z0-9-]+", ws_path):
        raise RuntimeError("invalid Chrome-written endpoint file")
    pid = listener_pid(port, profile)
    ws = f"ws://127.0.0.1:{port}{ws_path}"
    digest = hashlib.sha256((path_key(profile) + "|" + ws).encode()).hexdigest()[:16]
    return {"user_data_dir": str(profile), "browser_pid": pid, "port": port,
            "websocket": ws, "daemon": "bcc-" + digest}


def normal_chrome_ws() -> str:
    """Compatibility helper, with listener ownership verification."""
    return endpoint_for_profile(normal_chrome_dir())["websocket"]


def browser_env(endpoint: dict | None, *, normal_chrome: bool = False) -> dict:
    env = os.environ.copy()
    for key in ("PYTHONHOME", "PYTHONPATH", "BU_CDP_WS", "BU_CDP_URL",
                "BU_NAME", "BU_BROWSER_ID", "BU_AUTOSPAWN", "BROWSER_CDP_URL"):
        env.pop(key, None)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONUTF8"] = "1"
    # Custom IPC dirs otherwise use bare 'bu' filenames, ignoring BU_NAME.
    env["BH_RUNTIME_DIR_SHARED"] = "1"
    env["BH_TMP_DIR_SHARED"] = "1"
    if normal_chrome and endpoint is None:
        raise RuntimeError("normal Chrome requires a verified endpoint")
    if endpoint:
        # Chrome 144+ asks for consent per CDP connection. Browser Harness keeps
        # that handshake alive only in its local-Chrome mode, which is selected
        # by leaving BU_CDP_WS/BU_CDP_URL unset. Normal Chrome is its first
        # Windows profile, and endpoint_for_profile() already proved that exact
        # profile owns a live listener before we allow this mode.
        if not normal_chrome:
            env["BU_CDP_WS"] = endpoint["websocket"]
        env["BU_NAME"] = endpoint["daemon"]
    else:
        env["BU_NAME"] = "bcc-discovery"
    return env


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--normal-chrome", action="store_true")
    mode.add_argument("--user-data-dir", type=Path, help="exact directory of the intended browser")
    mode.add_argument("--discover", action="store_true", help="explicitly allow unconstrained local discovery")
    parser.add_argument("--check", action="store_true", help="verify endpoint without attaching")
    parser.add_argument("--code-file", type=Path, help="read a task-local bootstrap instead of stdin")
    parser.add_argument("--timeout", type=float, default=60, help="foreground client limit in seconds")
    args = parser.parse_args()
    if not 0 < args.timeout <= 1800:
        parser.error("--timeout must be greater than zero and at most 1800 seconds")
    try:
        endpoint = None if args.discover else endpoint_for_profile(
            normal_chrome_dir() if args.normal_chrome else args.user_data_dir
        )
        if args.check:
            print(json.dumps(endpoint or {"daemon": "bcc-discovery", "profile_verified": False}, indent=2))
            return 0
        code = (args.code_file.read_text(encoding="utf-8-sig") if args.code_file
                else sys.stdin.buffer.read().decode("utf-8-sig")).lstrip("\ufeff")
        if not code.strip():
            raise RuntimeError("expected Browser Use Python on stdin or in --code-file")
        executable = shutil.which("browser-use")
        if not executable:
            raise RuntimeError("browser-use is not installed or is absent from PATH")
        extra = {"creationflags": subprocess.CREATE_NO_WINDOW} if os.name == "nt" else {}
        return subprocess.run(
            [executable], input=code, text=True, encoding="utf-8", check=False,
            env=browser_env(endpoint, normal_chrome=args.normal_chrome),
        ).returncode
    except subprocess.TimeoutExpired:
        print("run_browser_use.py: client timed out; attachment or actions may still be pending. "
              "Inspect the existing daemon, Chrome prompt, and page result before retrying.",
              file=sys.stderr)
        return 124
    except (RuntimeError, OSError, UnicodeError) as exc:
        print(f"run_browser_use.py: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())

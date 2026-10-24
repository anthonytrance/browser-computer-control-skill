"""Limited standalone CDP helper for an explicitly selected isolated browser.

Prefer Browser Use's existing connection. This helper opens a new WebSocket
per call and cannot bypass Chrome consent. Targets must be unambiguous.
"""
import argparse
import json
import sys
import time
import urllib.request

import websocket


def targets(base):
    with urllib.request.urlopen(base.rstrip("/") + "/json/list", timeout=15) as response:
        return [target for target in json.loads(response.read()) if target.get("type") == "page"]


def pick(base, match=None, target_id=None):
    candidates = targets(base)
    if target_id is not None:
        candidates = [t for t in candidates if t.get("id") == target_id]
    elif match is not None:
        if not match:
            raise RuntimeError("--match must not be empty")
        candidates = [t for t in candidates if match in (t.get("url") or "")]
    if not candidates:
        raise RuntimeError("no page matches the requested target; use --list")
    if len(candidates) != 1:
        raise RuntimeError("ambiguous page target; use --list and an exact --target-id")
    return candidates[0]


def evaluate(base, expr, match=None, timeout=25, target_id=None):
    target = pick(base, match, target_id)
    ws = websocket.create_connection(
        target["webSocketDebuggerUrl"], timeout=timeout, suppress_origin=True
    )
    deadline = time.monotonic() + timeout
    try:
        ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate", "params": {
            "expression": expr, "returnByValue": True, "awaitPromise": True}}))
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("CDP evaluation timed out; read back state before retrying")
            ws.settimeout(remaining)
            message = json.loads(ws.recv())
            if message.get("id") != 1:
                continue
            if "error" in message:
                raise RuntimeError("CDP protocol error: " + json.dumps(message["error"]))
            result = message.get("result", {})
            if "exceptionDetails" in result:
                detail = (result.get("result") or {}).get("description")
                raise RuntimeError(detail or result["exceptionDetails"].get("text", "JavaScript exception"))
            return result.get("result", {}).get("value")
    finally:
        ws.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", required=True, help="explicit isolated-browser CDP HTTP base")
    selection = parser.add_mutually_exclusive_group()
    selection.add_argument("--match", help="unique URL substring")
    selection.add_argument("--target-id", help="exact page target ID from --list")
    parser.add_argument("--timeout", type=float, default=25)
    parser.add_argument("--list", action="store_true")
    args = parser.parse_args()
    if not 0 < args.timeout <= 1800:
        parser.error("--timeout must be greater than zero and at most 1800 seconds")
    try:
        if args.list:
            result = [{key: t.get(key) for key in ("id", "url", "title")} for t in targets(args.base)]
        else:
            expr = sys.stdin.buffer.read().decode("utf-8-sig")
            if not expr.strip():
                raise RuntimeError("expected JavaScript on stdin")
            result = evaluate(args.base, expr, args.match, args.timeout, args.target_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return 0
    except (RuntimeError, OSError, ValueError, websocket.WebSocketException) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    raise SystemExit(main())

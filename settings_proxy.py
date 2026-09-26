"""Loopback-only sampling proxy with local request and response captures."""
import json
import os
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
UPSTREAM = os.environ.get("BONSAI_UPSTREAM", "http://127.0.0.1:62737").rstrip("/")
if urlparse(UPSTREAM).hostname not in ("127.0.0.1", "localhost", "::1"):
    raise ValueError("The demo upstream must be loopback.")
SETTINGS = json.loads((ROOT / "sampling.json").read_text())


def configure(payload):
    payload = dict(payload)
    cap = payload.get("max_tokens") or payload.get("max_completion_tokens") or 1536
    payload.update(SETTINGS)
    payload["max_tokens"] = min(int(cap), 1536)
    payload["stream"] = False
    payload.pop("max_completion_tokens", None)
    payload.pop("reasoning_effort", None)
    return payload


class Handler(BaseHTTPRequestHandler):
    def reply(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path != "/v1/models":
            return self.reply(404, {"error": "Unknown route"})
        try:
            with urllib.request.urlopen(UPSTREAM + self.path, timeout=10) as response:
                self.reply(response.status, json.load(response))
        except Exception as exc:
            self.reply(502, {"error": str(exc)})

    def do_POST(self):
        if self.path != "/v1/chat/completions":
            return self.reply(404, {"error": "Unknown route"})
        try:
            payload = configure(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
        except (ValueError, KeyError, TypeError) as exc:
            return self.reply(400, {"error": str(exc)})
        started = time.monotonic()
        try:
            request = urllib.request.Request(UPSTREAM + self.path, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(request, timeout=180) as response:
                status, body = response.status, json.load(response)
        except urllib.error.HTTPError as exc:
            status, body = exc.code, {"error": exc.read().decode(errors="replace")}
        except Exception as exc:
            status, body = 502, {"error": str(exc)}
        records = ROOT / "exchanges"
        records.mkdir(exist_ok=True)
        (records / (uuid.uuid4().hex + ".json")).write_text(json.dumps({"request": payload, "response": body, "http_status": status, "seconds": time.monotonic() - started}, indent=2))
        self.reply(status, body)


if __name__ == "__main__":
    port = int(os.environ.get("AMBIENT_PROXY_PORT", "5262"))
    print(f"Sampling proxy http://127.0.0.1:{port}/v1 -> {UPSTREAM}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()

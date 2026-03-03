import json
import os
import urllib.parse
import webbrowser
import http.server
import socketserver
import threading
import time

import requests


AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
DEFAULT_SCOPE = "https://www.googleapis.com/auth/drive.readonly"


class CodeHandler(http.server.BaseHTTPRequestHandler):
    code: str | None = None

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        code = params.get("code", [None])[0]
        if code:
            CodeHandler.code = code
            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Authorization complete. You can close this tab.")
        else:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(b"Missing code parameter.")

    def log_message(self, format: str, *args: object) -> None:
        return


def run_local_server(port: int) -> socketserver.TCPServer:
    server = socketserver.TCPServer(("127.0.0.1", port), CodeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


def main() -> None:
    client_id = os.getenv("GPHOTOS_CLIENT_ID")
    client_secret = os.getenv("GPHOTOS_CLIENT_SECRET")
    if not client_id or not client_secret:
        raise SystemExit("Set GPHOTOS_CLIENT_ID and GPHOTOS_CLIENT_SECRET")

    port = int(os.getenv("GPHOTOS_REDIRECT_PORT", "8123"))
    redirect_uri = f"http://127.0.0.1:{port}/oauth2callback"
    state = "gphotos-view-assist"

    server = run_local_server(port)

    scope = os.getenv("OAUTH_SCOPE", DEFAULT_SCOPE)
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
        "access_type": "offline",
        "prompt": "consent",
        "state": state,
    }
    url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    print("Open this URL in your browser if it does not open automatically:")
    print(url)
    webbrowser.open(url)

    timeout_seconds = 180
    start = time.time()
    while CodeHandler.code is None and time.time() - start < timeout_seconds:
        time.sleep(0.5)
    server.shutdown()

    if CodeHandler.code is None:
        raise SystemExit("Timed out waiting for authorization code")

    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": CodeHandler.code,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code",
    }
    response = requests.post(TOKEN_URL, data=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    refresh_token = data.get("refresh_token")
    if not refresh_token:
        raise SystemExit(
            "No refresh_token returned. Make sure you used prompt=consent and access_type=offline."
        )

    output = {
        "refresh_token": refresh_token,
    }
    print("\nRefresh token:")
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()

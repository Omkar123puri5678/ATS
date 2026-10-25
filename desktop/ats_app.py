"""Desktop launcher: runs the FastAPI backend in a background thread and shows
the React app in a native window (WebView2 on Windows), so the whole project
works as a normal double-click application with no browser or terminal.

Dev run (after `npm run build` in frontend/):  python desktop/ats_app.py
Packaged build:                               see desktop/build.ps1
"""
import os
import socket
import sys
import threading
import time
from pathlib import Path

APP_NAME = "ATS Resume Maker"
# A fixed port keeps the page origin the same between launches, so the
# resume the builder autosaves to localStorage is still there next time.
PREFERRED_PORT = 47615

if getattr(sys, "frozen", False):  # running from the PyInstaller bundle
    BUNDLE = Path(sys._MEIPASS)
    STATIC = BUNDLE / "static"
else:
    ROOT = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(ROOT / "backend"))
    STATIC = ROOT / "frontend" / "dist"

os.environ.setdefault("STATIC_DIR", str(STATIC))

# A windowed exe has no console, so stdout/stderr are None and uvicorn's
# logging would crash on startup.
for stream in ("stdout", "stderr"):
    if getattr(sys, stream) is None:
        setattr(sys, stream, open(os.devnull, "w"))

import uvicorn  # noqa: E402
import webview  # noqa: E402

from app.main import app  # noqa: E402


def pick_port() -> int:
    for port in (PREFERRED_PORT, 0):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return s.getsockname()[1]
            except OSError:
                continue
    raise RuntimeError("No free port")


def start_server(port: int) -> uvicorn.Server:
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_config=None))
    threading.Thread(target=server.run, daemon=True).start()
    deadline = time.time() + 30
    while not server.started:
        if time.time() > deadline:
            raise RuntimeError("Backend did not start within 30 seconds")
        time.sleep(0.05)
    return server


def main():
    if not STATIC.is_dir():
        sys.exit(f"Frontend build not found at {STATIC}. Run `npm run build` in frontend/ first.")
    port = pick_port()
    server = start_server(port)

    data_dir = Path(os.getenv("LOCALAPPDATA", Path.home())) / APP_NAME
    data_dir.mkdir(parents=True, exist_ok=True)
    webview.settings["ALLOW_DOWNLOADS"] = True  # "Download PDF" in the builder

    webview.create_window(APP_NAME, f"http://127.0.0.1:{port}/", width=1280, height=860, min_size=(900, 600))
    # private_mode=False + storage_path keeps localStorage (the autosaved resume) between runs.
    webview.start(private_mode=False, storage_path=str(data_dir))
    server.should_exit = True


if __name__ == "__main__":
    main()

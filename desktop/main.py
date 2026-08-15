"""FeiCai entry point. Starts backend + opens PyWebView window."""

import os
import sys
import socket
import threading
import time
from pathlib import Path

import uvicorn
import webview

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from desktop.logger import logger, try_with_log

PORT = int(os.environ.get("FEICAI_PORT", "8765"))


def start_server():
    """Start FastAPI backend in background thread."""
    from desktop.server import app
    try:
        uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
    except Exception as e:
        logger.error(f"Server start failed: {e}")


def ensure_hermes():
    """Auto-download Hermes on first run."""
    marker = ROOT / "data" / ".hermes_ready"
    if marker.exists():
        logger.info("Hermes already downloaded")
        return

    logger.info("First launch — downloading Hermes Agent...")
    from desktop.downloader import ensure_hermes_sync
    ok = try_with_log(ensure_hermes_sync, fallback=False, msg="Download Hermes")
    if ok:
        marker.parent.mkdir(parents=True, exist_ok=True)
        marker.write_text("done")
        logger.info("Hermes downloaded successfully")
    else:
        logger.warning(
            "Download failed. Manual download:\n"
            "  https://github.com/monikalnbo/hermes-agent\n"
            "  Extract into: data/hermes/"
        )


def pick_url():
    """Pick URL: Vite dev server if running, else built frontend."""
    s = socket.socket()
    try:
        s.settimeout(0.5)
        s.connect(("127.0.0.1", 5173))
        logger.info("Dev mode → Vite at http://127.0.0.1:5173")
        return "http://127.0.0.1:5173"
    except (ConnectionRefusedError, OSError):
        pass
    finally:
        s.close()
    return f"http://127.0.0.1:{PORT}"


def main():
    os.chdir(ROOT)
    v = try_with_log(lambda: (ROOT / 'VERSION').read_text().strip(), fallback='?')
    logger.info(f"FeiCai v{v} — starting")

    # Start backend server first
    t = threading.Thread(target=start_server, daemon=True)
    t.start()
    time.sleep(1.5)

    # Determine initial URL — if Hermes not ready, show loading page
    ready = (ROOT / "data" / ".hermes_ready").exists()
    if ready:
        url = pick_url()
    else:
        # Start download, show loading page
        from desktop.loader import start_download
        start_download()
        url = f"http://127.0.0.1:{PORT}/loading"

    logger.info(f"Loading URL: {url}")

    webview.create_window(
        title="FeiCai",
        url=url,
        width=1280, height=800,
        min_size=(960, 600),
        resizable=True,
        text_select=True,
        confirm_close=True,
    )
    webview.start(debug=False, http_server=False, private_mode=False)


if __name__ == "__main__":
    main()
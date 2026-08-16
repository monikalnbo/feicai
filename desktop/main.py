"""FeiCai entry point. Starts backend + Hermes subprocess + opens PyWebView window."""

import os
import sys
import socket
import subprocess
import threading
import time
import signal
from pathlib import Path

import uvicorn
import webview

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from desktop.logger import logger, try_with_log

PORT = int(os.environ.get("FEICAI_PORT", "8765"))
HERMES_PORT = int(os.environ.get("HERMES_PORT", "8642"))
HERMES_DIR = ROOT / "data" / "hermes"

_hermes_process = None


def start_server():
    """Start FastAPI backend in background thread."""
    from desktop.server import app
    try:
        uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
    except Exception as e:
        logger.error(f"Server start failed: {e}")


def _start_hermes_backend():
    """Start Hermes gateway as subprocess (non-blocking)."""
    global _hermes_process

    # Check if Hermes is already running on the target port
    s = socket.socket()
    try:
        s.settimeout(0.5)
        s.connect(("127.0.0.1", HERMES_PORT))
        s.close()
        logger.info(f"Hermes already running on port {HERMES_PORT}")
        return
    except (ConnectionRefusedError, OSError):
        pass
    finally:
        s.close()

    # Check if Hermes was downloaded
    cli_path = HERMES_DIR / "cli.py"
    if not cli_path.exists():
        logger.warning("Hermes not downloaded yet, skip backend start")
        return

    logger.info(f"Starting Hermes backend from {HERMES_DIR}...")

    try:
        env = os.environ.copy()
        env["HERMES_HOME"] = str(HERMES_DIR)
        env["HERMES_PORT"] = str(HERMES_PORT)

        _hermes_process = subprocess.Popen(
            [sys.executable, "-m", "gateway.run"],
            cwd=str(HERMES_DIR),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        logger.info(f"Hermes backend started (PID {_hermes_process.pid})")
    except Exception as e:
        logger.error(f"Failed to start Hermes backend: {e}")


def _wait_for_port(host, port, timeout=10, interval=0.3):
    """Poll until a TCP port is open. Returns True if ready, False on timeout."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        s = socket.socket()
        try:
            s.settimeout(interval)
            s.connect((host, port))
            s.close()
            return True
        except (ConnectionRefusedError, OSError):
            pass
        finally:
            s.close()
        time.sleep(interval)
    return False


def pick_url():
    """Pick URL: Vite dev server if running, else built frontend."""
    if _wait_for_port("127.0.0.1", 5173, timeout=0.5):
        logger.info("Dev mode → Vite at http://127.0.0.1:5173")
        return "http://127.0.0.1:5173"
    return f"http://127.0.0.1:{PORT}"


def main():
    os.chdir(ROOT)
    v = try_with_log(lambda: (ROOT / 'VERSION').read_text().strip(), fallback='?')
    logger.info(f"FeiCai v{v} — starting")

    # Start backend server first
    t = threading.Thread(target=start_server, daemon=True)
    t.start()

    # Wait for our own server to be ready
    if not _wait_for_port("127.0.0.1", PORT, timeout=10):
        logger.error(f"FeiCai server failed to start on port {PORT}")

    # Start Hermes backend if already downloaded
    _start_hermes_backend()

    # Determine initial URL
    ready = (ROOT / "data" / ".hermes_ready").exists()
    if ready:
        url = pick_url()
        # Wait briefly for Hermes backend to be ready
        _wait_for_port("127.0.0.1", HERMES_PORT, timeout=8)
    else:
        from desktop.loader import start_download
        start_download()
        url = f"http://127.0.0.1:{PORT}/loading"

    logger.info(f"Loading URL: {url}")

    window = webview.create_window(
        title="FeiCai",
        url=url,
        width=1280, height=800,
        min_size=(960, 600),
        resizable=True,
        text_select=True,
        confirm_close=True,
    )

    webview.start(debug=False, http_server=False, private_mode=False)

    # Cleanup Hermes subprocess on exit
    global _hermes_process
    if _hermes_process and _hermes_process.poll() is None:
        logger.info("Stopping Hermes backend...")
        _hermes_process.terminate()
        try:
            _hermes_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            _hermes_process.kill()


if __name__ == "__main__":
    main()
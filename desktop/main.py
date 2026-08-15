"""
肥财 FeiCai — Hermes Agent Desktop Shell
Main entry: starts the backend server and opens a PyWebView window.
"""

import os
import sys
import threading
import uvicorn
import webview

from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Default port
SERVER_PORT = int(os.environ.get("FEICAI_PORT", "8765"))


def start_server():
    """Start the FastAPI backend server in a background thread."""
    from desktop.server import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=SERVER_PORT,
        log_level="info",
        reload=False,
    )


def main():
    """Launch the FeiCai desktop application."""
    print("🐱 肥财 FeiCai — Hermes Agent Desktop Shell")
    print(f"   Server: http://127.0.0.1:{SERVER_PORT}")

    # Start backend server in background thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # Determine the URL to load
    # Production: use the backend's static file server
    # If the web frontend is built, it's served at /
    url = f"http://127.0.0.1:{SERVER_PORT}"

    # Check if Vite dev server is running (prefer it for development)
    import socket

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect(("127.0.0.1", 5173))
        url = "http://127.0.0.1:5173"
        print("   🔄 Dev mode: using Vite dev server at http://127.0.0.1:5173")
    except (ConnectionRefusedError, OSError):
        pass
    finally:
        s.close()

    # Create PyWebView window
    window = webview.create_window(
        title="肥财 FeiCai",
        url=url,
        width=1280,
        height=800,
        min_size=(960, 600),
        resizable=True,
        fullscreen=False,
        text_select=False,
        confirm_close=True,
    )

    # Start the GUI event loop
    webview.start(
        debug=True,
        http_server=False,  # We use our own server
        private_mode=False,
    )


if __name__ == "__main__":
    main()
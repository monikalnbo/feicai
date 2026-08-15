"""
肥财 FeiCai — Hermes Agent Desktop Workbench
Main entry: starts the backend server and opens a PyWebView window.
"""

import os
import sys
import threading
import socket
import time
import uvicorn
import webview

from pathlib import Path

# Add project root to Python path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

# Default port
SERVER_PORT = int(os.environ.get("FEICAI_PORT", "8765"))


# ── Banner ──────────────────────────────────────────────────────────
BANNER = r"""
  ______   _   ______   _
 |  ____| (_) |  ____| (_)
 | |__     _  | |__     _   __ _   ___   ___
 |  __|   | | |  __|   | | / _` | / __| / __|
 | |      | | | |      | || (_| || (__  \__ \
 |_|      |_| |_|      |_| \__,_| \___| |___/

  Hermes Agent Desktop Workbench
"""


def start_server():
    """Start the FastAPI backend server in a background thread."""
    from desktop.server import app

    uvicorn.run(
        app,
        host="127.0.0.1",
        port=SERVER_PORT,
        log_level="warning",
        reload=False,
        access_log=False,
    )


def check_for_updates():
    """Check for updates in a background thread and print result."""
    try:
        from desktop.update_checker import check_for_update_sync

        info = check_for_update_sync()
        if info.has_update:
            print(f"\n  📦 发现新版本: v{info.current_version} → v{info.latest_version}")
            print(f"  🔗  {info.release_url}")
        else:
            print(f"  ✅ 当前已是最新版本 (v{info.current_version})")
    except Exception as e:
        print(f"  ⚠️  更新检查失败: {e}")


def main():
    """Launch the FeiCai desktop workbench."""
    print(BANNER)
    print(f"  🚀 启动服务...")
    print(f"  📡 后端地址: http://127.0.0.1:{SERVER_PORT}")

    # ── 启动后端服务 ──
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 等待服务器就绪
    time.sleep(1.5)

    # ── 检查更新（后台线程） ──
    update_thread = threading.Thread(target=check_for_updates, daemon=True)
    update_thread.start()

    # ── 确定加载哪个 URL ──
    url = f"http://127.0.0.1:{SERVER_PORT}"

    # 检查 Vite 开发服务器是否在运行
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.settimeout(1)
        s.connect(("127.0.0.1", 5173))
        url = "http://127.0.0.1:5173"
        print(f"  🔄 开发模式: 连接 Vite 服务器 http://127.0.0.1:5173")
    except (ConnectionRefusedError, OSError):
        print(f"  🌐 生产模式: 加载构建版前端")
    finally:
        s.close()

    # ── 检查 Hermes 后端 ──
    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s2.settimeout(2)
        s2.connect(("127.0.0.1", 8642))
        print(f"  ✅ Hermes Agent 后端已连接 (http://127.0.0.1:8642)")
    except (ConnectionRefusedError, OSError):
        print(f"  ⚠️  Hermes Agent 后端未检测到，请确保 'hermes gateway start' 已运行")
    finally:
        s2.close()

    print(f"\n  🐱 肥财 FeiCai 启动完成！")
    print(f"  ─────────────────────────────────────────")

    # ── 创建 PyWebView 窗口 ──
    window = webview.create_window(
        title="肥财 FeiCai — Hermes Agent Workbench",
        url=url,
        width=1280,
        height=800,
        min_size=(960, 600),
        resizable=True,
        fullscreen=False,
        text_select=True,
        confirm_close=True,
    )

    # 启动 GUI 事件循环
    webview.start(
        debug=False,
        http_server=False,
        private_mode=False,
    )


if __name__ == "__main__":
    main()
\"\"\"Manages Hermes download lifecycle with progress tracking.\"\"\"

import os
import sys
import time
import httpx
import zipfile
import threading
from pathlib import Path

from desktop.logger import logger, try_with_log

ROOT = Path(__file__).resolve().parent.parent
HERMES_DIR = ROOT / "data" / "hermes"
MARKER = ROOT / "data" / ".hermes_ready"

HERMES_REPO = os.environ.get("HERMES_REPO", "monikalnbo/hermes-agent")
ZIP_URL = f"https://github.com/{HERMES_REPO}/archive/refs/heads/main.zip"

# Shared progress state
_progress = {"percent": 0, "status": "idle", "error": ""}


def get_progress():
    \"\"\"Return current download progress.\"\"\"
    return dict(_progress)


def _update(pct, status, error=""):
    _progress["percent"] = pct
    _progress["status"] = status
    _progress["error"] = error


def _download_and_extract():
    \"\"\"Download Hermes ZIP and extract to data/hermes/. Runs in thread.\"\"\"
    try:
        _update(0, "connecting", "")
        logger.info("Downloading Hermes Agent...")

        with httpx.Client(follow_redirects=True, timeout=600.0) as client:
            resp = client.get(ZIP_URL)
            if resp.status_code != 200:
                raise Exception(f"HTTP {resp.status_code} — {resp.text[:200]}")

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            chunks = []

            _update(1, "downloading", "")
            for chunk in resp.iter_bytes(64 * 1024):
                chunks.append(chunk)
                downloaded += len(chunk)
                pct = int(downloaded / total * 100) if total else 0
                _update(pct, "downloading", "")

        _update(99, "extracting", "")
        logger.info("Extracting...")

        zip_path = HERMES_DIR.parent / "_temp_hermes.zip"
        try:
            with open(zip_path, "wb") as f:
                for c in chunks:
                    f.write(c)

            # ZIP root is "hermes-agent-main/"
            with zipfile.ZipFile(zip_path, "r") as zf:
                HERMES_DIR.mkdir(parents=True, exist_ok=True)
                for member in zf.namelist():
                    if member.endswith("/"):
                        continue
                    parts = member.split("/", 1)
                    if len(parts) < 2:
                        continue
                    target = HERMES_DIR / parts[1]
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as src, open(target, "wb") as dst:
                        dst.write(src.read())
        finally:
            if zip_path.exists():
                zip_path.unlink()

        MARKER.parent.mkdir(parents=True, exist_ok=True)
        MARKER.write_text("done")
        _update(100, "done", "")
        logger.info("Hermes downloaded and extracted successfully")

    except Exception as e:
        logger.error(f"Download failed: {e}")
        _update(0, "error", str(e))


def start_download():
    \"\"\"Start download in background thread. Returns immediately.\"\"\"
    if MARKER.exists():
        _update(100, "done", "")
        return

    _update(0, "connecting", "")
    t = threading.Thread(target=_download_and_extract, daemon=True)
    t.start()


# Minimal loading HTML with progress bar (served inline by server.py)
LOADING_HTML = \"\"\"<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>FeiCai — loading</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0f0f13;color:#e0e0e0;font-family:system-ui,-apple-system,sans-serif;
     display:flex;align-items:center;justify-content:center;height:100vh;
     flex-direction:column;gap:1.5rem}
.container{text-align:center;max-width:400px}
h1{font-size:1.5rem;font-weight:600;letter-spacing:0.05em;margin-bottom:0.5rem}
p{color:#888;font-size:0.875rem}
.bar-wrap{background:#1a1a2e;border-radius:99px;height:8px;overflow:hidden;margin-top:1rem}
.bar{height:100%;width:0%;background:linear-gradient(90deg,#6366f1,#a855f7);
     border-radius:99px;transition:width 0.3s}
#status{margin-top:0.75rem;font-size:0.75rem;color:#666}
.hidden{display:none}
.error{color:#ef4444}
</style>
</head>
<body>
<div class="container">
<h1>FeiCai</h1>
<p>Preparing Hermes Agent...</p>
<div class="bar-wrap"><div class="bar" id="bar"></div></div>
<p id="status">Connecting...</p>
</div>
<script>
async function poll(){try{
const r=await fetch('/api/feicai/download-progress');
const d=await r.json();
document.getElementById('bar').style.width=d.percent+'%';
document.getElementById('status').textContent=
  d.status==='downloading'?('Downloading... '+d.percent+'%'):
  d.status==='extracting'?'Extracting...':
  d.status==='error'?('Error: '+d.error):
  d.status==='done'?'Done! Redirecting...':'';
if(d.status==='error')document.getElementById('status').className='error';
if(d.status==='done'){setTimeout(()=>{window.location.href='/'},500);return}
}catch(e){document.getElementById('status').textContent='Waiting for server...'}
setTimeout(poll,800)}
poll();
</script>
</body>
</html>
\"\"\""
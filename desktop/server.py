"""FeiCai backend server. Proxies API, serves web UI, provides custom endpoints."""

import os
import sys
import httpx
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from desktop.logger import logger, try_with_log

ROOT = Path(__file__).resolve().parent.parent
BASE = Path(sys._MEIPASS) if hasattr(sys, '_MEIPASS') else ROOT

DATA_DIR = ROOT / "data"
HERMES_HOME = DATA_DIR / "hermes"
WEB_DIST = BASE / "web_dist"

HERMES_API = os.environ.get("HERMES_API_URL", "http://127.0.0.1:8642")

app = FastAPI(title="FeiCai")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = httpx.AsyncClient(base_url=HERMES_API, timeout=30.0)


@app.on_event("shutdown")
async def shutdown():
    await client.aclose()


# ---------------------------------------------------------------------------
# Download progress (for loading page)
# ---------------------------------------------------------------------------
@app.get("/api/feicai/download-progress")
async def download_progress():
    from desktop.loader import get_progress
    return JSONResponse(content=get_progress())


# ---------------------------------------------------------------------------
# Loading page (shown while Hermes is being downloaded)
# ---------------------------------------------------------------------------
@app.get("/loading")
async def loading_page():
    from desktop.loader import LOADING_HTML
    return HTMLResponse(content=LOADING_HTML)


# ---------------------------------------------------------------------------
# Serve web frontend (if built)
# ---------------------------------------------------------------------------
index = WEB_DIST / "index.html"
if index.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIST), html=True), name="webui")
else:
    @app.get("/")
    async def dev_mode():
        return JSONResponse({"status": "dev", "message": "FeiCai dev mode — run 'npm run dev' in web/"})


# ---------------------------------------------------------------------------
# API proxy: /api/* -> Hermes backend
# ---------------------------------------------------------------------------
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy(path: str, request: Request):
    try:
        body = await request.body()
        headers = {k: v for k, v in request.headers.items()
                   if k.lower() not in ("host", "content-length", "transfer-encoding")}

        resp = await client.request(
            method=request.method,
            url=f"/api/{path}",
            headers=headers,
            content=body,
            params=dict(request.query_params),
        )

        ct = resp.headers.get("content-type", "")
        if "application/json" in ct:
            return JSONResponse(content=resp.json(), status_code=resp.status_code,
                                headers=dict(resp.headers))
        return JSONResponse(content={"text": resp.text}, status_code=resp.status_code,
                            headers=dict(resp.headers))
    except Exception as e:
        logger.error(f"Proxy /api/{path}: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=502)


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------
@app.get("/api/feicai/version")
async def get_version():
    v = try_with_log(lambda: (ROOT / "VERSION").read_text().strip(), fallback="0.0.0", msg="Read version")
    return JSONResponse(content={"version": v})


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------
@app.get("/api/feicai/status")
async def get_status():
    connected = False
    try:
        r = await client.get("/api/health", timeout=2.0)
        connected = r.status_code == 200
    except Exception as e:
        logger.debug(f"Hermes health check: {e}")

    v = try_with_log(lambda: (ROOT / "VERSION").read_text().strip(), fallback="?")
    return JSONResponse(content={
        "version": v,
        "hermes_connected": connected,
        "data_dir": str(HERMES_HOME),
    })


# ---------------------------------------------------------------------------
# SOUL.md editor
# ---------------------------------------------------------------------------
SOUL_PATH = HERMES_HOME / "SOUL.md"


@app.get("/api/soul")
async def get_soul():
    if SOUL_PATH.exists():
        try:
            content = SOUL_PATH.read_text("utf-8")
            return JSONResponse(content={"content": content})
        except Exception as e:
            logger.error(f"Read SOUL.md: {e}")
            return JSONResponse(content={"error": str(e)}, status_code=500)
    return JSONResponse(content={"content": "", "note": "SOUL.md not found"}, status_code=404)


@app.put("/api/soul")
async def save_soul(request: Request):
    try:
        data = await request.json()
        SOUL_PATH.parent.mkdir(parents=True, exist_ok=True)
        SOUL_PATH.write_text(data.get("content", ""), "utf-8")
        logger.info("SOUL.md saved")
        return JSONResponse(content={"message": "saved"})
    except Exception as e:
        logger.error(f"Save SOUL.md: {e}")
        return JSONResponse(content={"error": str(e)}, status_code=500)


# ---------------------------------------------------------------------------
# Widget system (dashboard cards, extensible)
# ---------------------------------------------------------------------------
WIDGETS = {}


def register_widget(name, label, desc, icon="activity", interval=30, handler=None, api_url=""):
    WIDGETS[name] = {
        "name": name, "label": label, "description": desc, "icon": icon,
        "refresh_interval": interval, "api_url": api_url,
        "__handler": handler,
    }


# Built-in widgets
register_widget("hermes-status", "Hermes Status", "Backend connection", "activity", 15)
register_widget("system-info", "System Info", "Local system", "monitor", 60)
register_widget("feicai-version", "FeiCai Version", "Version & updates", "package", 3600)


@app.get("/api/feicai/widgets")
async def list_widgets():
    items = [{k: v for k, v in w.items() if not k.startswith("__")} for w in WIDGETS.values()]
    return JSONResponse(content={"widgets": items})


@app.get("/api/feicai/widgets/{name}/data")
async def widget_data(name: str):
    w = WIDGETS.get(name)
    if not w:
        return JSONResponse(content={"error": f"widget '{name}' not found"}, status_code=404)

    # Custom handler
    if w["__handler"]:
        try:
            return JSONResponse(content=await w["__handler"]())
        except Exception as e:
            logger.error(f"Widget {name}: {e}")
            return JSONResponse(content={"status": "error", "error": str(e)})

    # External API widget
    if w["api_url"]:
        return await _fetch_external(w["api_url"])

    # Default handlers
    if name == "hermes-status":
        return await _hermes_status()
    if name == "system-info":
        return _system_info()
    if name == "feicai-version":
        return await _feicai_version()

    return JSONResponse(content={"status": "unknown"})


async def _hermes_status():
    ok = False
    try:
        r = await client.get("/api/health", timeout=2.0)
        ok = r.status_code == 200
    except:
        pass
    return {"status": "ok" if ok else "disconnected", "connected": ok}


def _system_info():
    import platform
    return {"status": "ok", "data": {
        "platform": f"{platform.system()} {platform.release()}",
        "python": platform.python_version(),
        "hostname": platform.node(),
    }}


async def _feicai_version():
    from .update_checker import check_for_update
    try:
        info = await check_for_update()
        return {"status": "ok", "data": {
            "current": info.current_version,
            "latest": info.latest_version,
            "has_update": info.has_update,
            "release_url": info.release_url,
        }}
    except Exception as e:
        logger.error(f"Version check: {e}")
        return {"status": "ok", "data": {"current": "?", "has_update": False}}


async def _fetch_external(url: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as c:
            resp = await c.get(url)
            data = resp.json() if "application/json" in resp.headers.get("content-type", "") else {"body": resp.text}
        return {"status": "ok", "source": url, "data": data}
    except Exception as e:
        logger.error(f"External API {url}: {e}")
        return {"status": "error", "error": str(e)}
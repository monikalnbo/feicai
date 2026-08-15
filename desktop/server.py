"""
肥财 - Hermes Agent Desktop Shell
FastAPI backend: proxies API requests and serves WebUI static files.
"""

import os
import sys
import json
import httpx
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# Hermes backend API base URL
HERMES_API_BASE = os.environ.get("HERMES_API_URL", "http://127.0.0.1:8642")

# Paths
ROOT_DIR = Path(__file__).resolve().parent.parent
HERMES_AGENT_DIR = ROOT_DIR / "hermes-agent"
WEB_DIST_DIR = HERMES_AGENT_DIR / "hermes_cli" / "web_dist"
WEB_SRC_DIR = HERMES_AGENT_DIR / "web"

app = FastAPI(title="肥财 FeiCai")

# HTTP client for proxying API requests
client = httpx.AsyncClient(base_url=HERMES_API_BASE, timeout=30.0)


@app.on_event("shutdown")
async def shutdown():
    await client.aclose()


# ---------------------------------------------------------------------------
# API Proxy — forwards /api/* requests to the Hermes backend
# ---------------------------------------------------------------------------
@app.api_route("/api/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"])
async def proxy_api(path: str, request: Request):
    """Proxy API requests to the running Hermes agent backend."""
    try:
        body = await request.body()
        headers = {
            k: v for k, v in request.headers.items()
            if k.lower() not in ("host", "content-length")
        }

        resp = await client.request(
            method=request.method,
            url=f"/api/{path}",
            headers=headers,
            content=body,
            params=dict(request.query_params),
        )

        return JSONResponse(
            content=resp.json() if resp.headers.get("content-type", "").startswith("application/json") else resp.text,
            status_code=resp.status_code,
            headers=dict(resp.headers),
        )
    except Exception as e:
        return JSONResponse(
            content={"error": f"Proxy error: {str(e)}"},
            status_code=502,
        )


# ---------------------------------------------------------------------------
# Serve built WebUI (production mode)
# ---------------------------------------------------------------------------
def _find_index_html() -> Path | None:
    """Look for built index.html in various locations."""
    candidates = [
        WEB_DIST_DIR / "index.html",
        WEB_SRC_DIR / "dist" / "index.html",
        ROOT_DIR / "web" / "dist" / "index.html",
    ]
    for p in candidates:
        if p.exists():
            return p
    return None


if _find_index_html():
    dist_dir = _find_index_html().parent
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="webui")
else:
    # Fallback: redirect to Vite dev server
    @app.get("/")
    async def dev_redirect():
        return JSONResponse({
            "message": "肥财 FeiCai - Development mode",
            "info": "Run 'cd hermes-agent/web && npm run dev' for the live UI, then load http://localhost:5173 in the desktop app.",
        })


# ---------------------------------------------------------------------------
# Hermes SOUL file API (custom endpoint for editing SOUL.md)
# ---------------------------------------------------------------------------
SOUL_PATH = Path(os.environ.get("HERMES_SOUL_PATH", Path.home() / ".hermes" / "SOUL.md"))


@app.get("/api/soul")
async def get_soul():
    """Read the Hermes SOUL.md file."""
    if SOUL_PATH.exists():
        return JSONResponse(content={"content": SOUL_PATH.read_text(encoding="utf-8")})
    return JSONResponse(content={"content": "", "error": "SOUL.md not found"}, status_code=404)


@app.put("/api/soul")
async def update_soul(request: Request):
    """Write to the Hermes SOUL.md file."""
    data = await request.json()
    content = data.get("content", "")
    SOUL_PATH.parent.mkdir(parents=True, exist_ok=True)
    SOUL_PATH.write_text(content, encoding="utf-8")
    return JSONResponse(content={"message": "SOUL.md updated", "path": str(SOUL_PATH)})
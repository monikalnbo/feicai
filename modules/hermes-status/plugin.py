"""Hermes 状态模块"""

import httpx


def init():
    """模块初始化：注册 widget"""
    register_widget(
        name="connection",
        label="Hermes 连接",
        description="Hermes Agent 后端连接状态",
        icon="activity",
        refresh_interval=15,
        handler=get_hermes_status,
    )


async def get_hermes_status():
    """获取 Hermes 后端状态"""
    hermes_api = "http://127.0.0.1:8642"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{hermes_api}/api/status")
            if resp.status_code == 200:
                data = resp.json()
                return {
                    "status": "connected",
                    "label": "Hermes Agent",
                    "connected": True,
                    "data": data,
                }
            return {"status": "error", "label": "Hermes Agent", "connected": False}
    except Exception as e:
        return {
            "status": "disconnected",
            "label": "Hermes Agent",
            "connected": False,
            "error": str(e),
        }
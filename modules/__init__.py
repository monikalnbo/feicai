"""
肥财 FeiCai — 模块系统
自动扫描 modules/ 下的所有模块，加载并注册。
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Callable

# 模块目录
MODULES_DIR = Path(__file__).parent

# 已加载的模块
_loaded_modules: dict[str, dict] = {}
_widget_registry: dict[str, dict] = {}
_api_routes: list[dict] = []


class Module:
    """单个模块"""
    def __init__(self, name: str, dir_path: Path, meta: dict):
        self.name = name
        self.dir_path = dir_path
        self.meta = meta
        self.plugin = None

    def load_plugin(self):
        """加载模块的 plugin.py"""
        plugin_path = self.dir_path / "plugin.py"
        if not plugin_path.exists():
            return

        spec = importlib.util.spec_from_file_location(
            f"modules.{self.name}.plugin", plugin_path
        )
        mod = importlib.util.module_from_spec(spec)
        # 注入注册函数
        mod.register_widget = self._register_widget
        mod.register_api = self._register_api
        sys.modules[spec.name] = mod
        spec.loader.exec_module(mod)

        # 如果模块有 init() 函数，调用它
        if hasattr(mod, "init"):
            mod.init()

        self.plugin = mod

    def _register_widget(self, name: str, label: str, description: str = "",
                          icon: str = "activity", refresh_interval: int = 30,
                          api_url: str = "", handler: Callable = None):
        """注册一个 widget"""
        widget_id = f"{self.name}.{name}"
        _widget_registry[widget_id] = {
            "name": widget_id,
            "label": label,
            "description": description,
            "icon": icon,
            "refresh_interval": refresh_interval,
            "api_url": api_url,
            "handler": handler,
            "module": self.name,
        }

    def _register_api(self, path: str, method: str = "GET", handler: Callable = None):
        """注册一个 API 路由"""
        _api_routes.append({
            "path": f"/api/feicai/modules/{self.name}{path}",
            "method": method,
            "handler": handler,
            "module": self.name,
        })


def discover_modules():
    """扫描 modules/ 目录，发现所有模块"""
    _loaded_modules.clear()
    _widget_registry.clear()
    _api_routes.clear()

    for item in sorted(MODULES_DIR.iterdir()):
        if not item.is_dir() or item.name.startswith("_") or item.name.startswith("."):
            continue

        meta_file = item / "module.json"
        if not meta_file.exists():
            continue

        try:
            meta = json.loads(meta_file.read_text(encoding="utf-8"))
        except Exception:
            meta = {"name": item.name, "label": item.name, "version": "0.1.0"}

        mod = Module(item.name, item, meta)
        mod.load_plugin()
        _loaded_modules[item.name] = mod


def get_widgets() -> list[dict]:
    """获取所有已注册的 widget（不含 handler，用于前端展示）"""
    result = []
    for wid, w in _widget_registry.items():
        result.append({
            "name": w["name"],
            "label": w["label"],
            "description": w["description"],
            "icon": w["icon"],
            "refresh_interval": w["refresh_interval"],
            "api_url": w["api_url"],
            "module": w["module"],
        })
    return result


def get_widget_handler(widget_name: str) -> Callable | None:
    """根据 widget name 获取其数据处理器"""
    w = _widget_registry.get(widget_name)
    if w:
        return w.get("handler")
    return None


def get_api_routes() -> list[dict]:
    """获取所有模块注册的 API 路由"""
    return _api_routes


def get_modules() -> list[dict]:
    """获取所有已加载模块的信息"""
    return [
        {
            "name": m.name,
            "label": m.meta.get("label", m.name),
            "description": m.meta.get("description", ""),
            "version": m.meta.get("version", "0.1.0"),
        }
        for m in _loaded_modules.values()
    ]
"""
肥财 FeiCai — 更新检测模块
从 GitHub Releases API 检查新版本。
"""

import os
import json
import httpx
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Optional

# 项目根目录
ROOT_DIR = Path(__file__).resolve().parent.parent

# 当前版本（从 VERSION 文件读取）
def get_current_version(base_dir: Path | None = None) -> str:
    version_file = (base_dir or ROOT_DIR) / "VERSION"
    if version_file.exists():
        return version_file.read_text(encoding="utf-8").strip()
    return "0.0.0"

# GitHub 信息
GITHUB_REPO = os.environ.get("FEICAI_GITHUB_REPO", "monikalnbo/feicai")
GITHUB_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"


@dataclass
class UpdateInfo:
    """更新信息"""
    current_version: str
    latest_version: str
    release_url: str
    release_notes: str
    has_update: bool
    published_at: str = ""


async def check_for_update() -> UpdateInfo:
    """
    检查 GitHub 上是否有新版本。
    返回 UpdateInfo 对象。
    """
    current = get_current_version()

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(GITHUB_API)
            if resp.status_code != 200:
                return UpdateInfo(
                    current_version=current,
                    latest_version=current,
                    release_url="",
                    release_notes=f"检查更新失败: HTTP {resp.status_code}",
                    has_update=False,
                )

            data = resp.json()
            latest = data.get("tag_name", "").lstrip("v")
            release_url = data.get("html_url", "")
            release_notes = data.get("body", "")[:500]  # 只取前500字符
            published_at = data.get("published_at", "")

            has_update = _compare_versions(latest, current) > 0

            return UpdateInfo(
                current_version=current,
                latest_version=latest,
                release_url=release_url,
                release_notes=release_notes or "无详细发布说明",
                has_update=has_update,
                published_at=published_at,
            )

    except Exception as e:
        return UpdateInfo(
            current_version=current,
            latest_version=current,
            release_url="",
            release_notes=f"检查更新时出错: {str(e)}",
            has_update=False,
        )


def _compare_versions(v1: str, v2: str) -> int:
    """
    比较两个版本号。
    返回 >0 表示 v1 > v2, <0 表示 v1 < v2, =0 表示相等。
    """
    try:
        parts1 = [int(x) for x in v1.split(".")]
        parts2 = [int(x) for x in v2.split(".")]
        # 补齐长度
        max_len = max(len(parts1), len(parts2))
        parts1 += [0] * (max_len - len(parts1))
        parts2 += [0] * (max_len - len(parts2))

        for a, b in zip(parts1, parts2):
            if a != b:
                return a - b
        return 0
    except (ValueError, AttributeError):
        return 0


# 同步版本（用于启动时检查）
def check_for_update_sync() -> UpdateInfo:
    """同步版本的更新检查"""
    import asyncio
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(check_for_update())
    finally:
        loop.close()
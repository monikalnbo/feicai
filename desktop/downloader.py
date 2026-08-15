"""
肥财 FeiCai — Hermes Agent 下载器
首次启动时自动从 GitHub 下载 Hermes Agent。
"""

import os
import sys
import zipfile
import httpx
import asyncio
from pathlib import Path
from typing import Optional

# 下载源
HERMES_REPO = os.environ.get("HERMES_REPO", "monikalnbo/hermes-agent")
HERMES_ZIP_URL = f"https://github.com/{HERMES_REPO}/archive/refs/heads/main.zip"
HERMES_TAR_URL = f"https://github.com/{HERMES_REPO}/archive/refs/heads/main.tar.gz"

# 项目路径
ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT_DIR / "data"
HERMES_DIR = ROOT_DIR / "hermes-agent"
WEB_DIST_TARGET = HERMES_DIR / "hermes_cli" / "web_dist"


async def download_and_extract(url: str, target_dir: Path, progress_callback=None) -> bool:
    """下载 ZIP 并解压到目标目录"""
    target_dir.mkdir(parents=True, exist_ok=True)

    async with httpx.AsyncClient(follow_redirects=True, timeout=300.0) as client:
        async with client.stream("GET", url) as resp:
            if resp.status_code != 200:
                raise Exception(f"下载失败: HTTP {resp.status_code}")

            total = int(resp.headers.get("content-length", 0))
            downloaded = 0
            chunks = []

            async for chunk in resp.aiter_bytes():
                chunks.append(chunk)
                downloaded += len(chunk)
                if progress_callback and total:
                    progress_callback(downloaded / total * 100)

    # 写入临时文件
    zip_path = target_dir / "hermes.zip"
    with open(zip_path, "wb") as f:
        for chunk in chunks:
            f.write(chunk)

    # 解压
    with zipfile.ZipFile(zip_path, "r") as zf:
        # ZIP 里所有文件都在 hermes-agent-main/ 目录下，去掉前缀
        for member in zf.namelist():
            # 跳过目录
            if member.endswith("/"):
                continue
            # 去掉顶层目录前缀
            parts = member.split("/", 1)
            if len(parts) < 2:
                continue
            rel_path = parts[1]
            if not rel_path:
                continue
            target = target_dir / rel_path
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, open(target, "wb") as dst:
                dst.write(src.read())

    zip_path.unlink()
    return True


async def ensure_hermes(progress_callback=None) -> bool:
    """确保 Hermes Agent 已下载到本地"""
    # 判断是否已存在
    marker = HERMES_DIR / ".hermes_installed"
    if marker.exists():
        return True

    print("  📥 正在下载 Hermes Agent...")
    try:
        await download_and_extract(HERMES_ZIP_URL, HERMES_DIR, progress_callback)
        # 创建标记
        marker.write_text("installed")
        print("  ✅ Hermes Agent 下载完成")
        return True
    except Exception as e:
        print(f"  ❌ 下载失败: {e}")
        print("  💡 你可以手动从 https://github.com/monikalnbo/hermes-agent 下载")
        return False


def ensure_hermes_sync() -> bool:
    """同步版本的安装检查"""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(ensure_hermes())
    finally:
        loop.close()


if __name__ == "__main__":
    # 测试下载
    async def main():
        ok = await ensure_hermes(lambda p: print(f"  进度: {p:.1f}%"))
        print("成功" if ok else "失败")

    asyncio.run(main())
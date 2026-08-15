#!/bin/bash
# ─────────────────────────────────────────────
# 肥财 FeiCai — 构建脚本
# 用法：
#   ./scripts/build.sh mac     → 构建 macOS .app
#   ./scripts/build.sh win     → 构建 Windows .exe
#   ./scripts/build.sh linux   → 构建 Linux 可执行文件
# ─────────────────────────────────────────────

set -e
cd "$(dirname "$0")/.."
ROOT=$(pwd)

echo "🐱 肥财 FeiCai — 构建"
echo "────────────────────────"

# 1. 确保前端已构建
if [ ! -d "hermes-agent/hermes_cli/web_dist" ]; then
  echo "📦 构建前端..."
  cd hermes-agent/web
  npm install
  npm run build
  cd "$ROOT"
else
  echo "✅ 前端已构建 (hermes-agent/hermes_cli/web_dist)"
fi

# 2. 确保虚拟环境
if [ ! -d "venv" ]; then
  echo "🐍 创建虚拟环境..."
  python3 -m venv venv
fi

source venv/bin/activate

# 3. 安装依赖
pip install -q -r requirements.txt pyinstaller

# 4. 版本号
VERSION=$(cat VERSION)

# 5. 平台特定构建
case "${1:-mac}" in
  mac|macos|darwin)
    echo "🍎 构建 macOS .app..."
    echo "   版本: v${VERSION}"
    echo ""
    pyinstaller \
      --onefile \
      --windowed \
      --name "肥财" \
      --add-data "VERSION:." \
      --add-data "hermes-agent/hermes_cli/web_dist:web_dist" \
      --hidden-import "desktop.server" \
      --hidden-import "desktop.update_checker" \
      --hidden-import "webview.platforms.cocoa" \
      --hidden-import "uvicorn.logging" \
      --hidden-import "uvicorn.loops.auto" \
      --hidden-import "uvicorn.protocols.http.auto" \
      --hidden-import "uvicorn.protocols.websockets.auto" \
      --collect-all "webview" \
      --icon "assets/icon.icns" \
      desktop/main.py
    echo ""
    echo "✅ 输出: dist/肥财.app"
    echo "   (直接双击即可运行)"
    ;;

  win|windows)
    echo "🪟 构建 Windows .exe..."
    echo "   版本: v${VERSION}"
    echo ""
    pyinstaller \
      --onefile \
      --windowed \
      --name "FeiCai" \
      --add-data "VERSION;." \
      --add-data "hermes-agent/hermes_cli/web_dist;web_dist" \
      --hidden-import "desktop.server" \
      --hidden-import "desktop.update_checker" \
      --hidden-import "webview.platforms.win32" \
      --hidden-import "uvicorn.logging" \
      --hidden-import "uvicorn.loops.auto" \
      --hidden-import "uvicorn.protocols.http.auto" \
      --hidden-import "uvicorn.protocols.websockets.auto" \
      --collect-all "webview" \
      --icon "assets/icon.ico" \
      desktop/main.py
    echo ""
    echo "✅ 输出: dist/FeiCai.exe"
    ;;

  linux)
    echo "🐧 构建 Linux 可执行文件..."
    echo "   版本: v${VERSION}"
    echo ""
    pyinstaller \
      --onefile \
      --name "feicai" \
      --add-data "VERSION:." \
      --add-data "hermes-agent/hermes_cli/web_dist:web_dist" \
      --hidden-import "desktop.server" \
      --hidden-import "desktop.update_checker" \
      --hidden-import "webview.platforms.gtk" \
      --hidden-import "uvicorn.logging" \
      --hidden-import "uvicorn.loops.auto" \
      --hidden-import "uvicorn.protocols.http.auto" \
      --hidden-import "uvicorn.protocols.websockets.auto" \
      --collect-all "webview" \
      desktop/main.py
    echo ""
    echo "✅ 输出: dist/feicai"
    ;;

  spec)
    echo "📄 使用 spec 文件构建..."
    pyinstaller feicai.spec
    echo "✅ 输出: dist/ 目录"
    ;;

  *)
    echo "用法: $0 {mac|win|linux|spec}"
    echo "  默认: mac"
    exit 1
    ;;
esac

deactivate
echo ""
echo "🎉 构建完成！输出在 dist/ 目录"
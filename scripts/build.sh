#!/bin/bash
# ─────────────────────────────────────────────
# 肥财 FeiCai — build script
# Usage:
#   ./scripts/build.sh mac     → macOS .app
#   ./scripts/build.sh win     → Windows .exe
#   ./scripts/build.sh linux   → Linux executable
# ─────────────────────────────────────────────

set -e
cd "$(dirname "$0")/.."
ROOT=$(pwd)

echo "肥财 FeiCai — Build"
echo "────────────────────────"

# 1. Ensure frontend is built
if [ ! -d "web_dist" ]; then
  echo "Building frontend..."
  cd hermes-agent/web
  npm install
  npm run build
  cd "$ROOT"
  # Move web_dist to root
  mv hermes-agent/hermes_cli/web_dist web_dist
else
  echo "Frontend ready (web_dist)"
fi

# 2. Ensure venv
if [ ! -d "venv" ]; then
  echo "Creating venv..."
  python3 -m venv venv
fi

source venv/bin/activate

# 3. Install deps
pip install -q -r requirements.txt pyinstaller

# 4. Version
VERSION=$(cat VERSION)

# 5. Platform-specific build
case "${1:-mac}" in
  mac|macos|darwin)
    echo "macOS .app..."
    echo "  Version: v${VERSION}"
    echo ""
    pyinstaller \
      --onedir \
      --windowed \
      --name "FeiCai" \
      --add-data "VERSION:." \
      --add-data "web_dist:web_dist" \
      --add-data "modules:modules" \
      --hidden-import "desktop.server" \
      --hidden-import "desktop.logger" \
      --hidden-import "desktop.loader" \
      --hidden-import "desktop.update_checker" \
      --hidden-import "webview.platforms.cocoa" \
      --hidden-import "uvicorn.logging" \
      --hidden-import "uvicorn.loops.auto" \
      --hidden-import "uvicorn.protocols.http.auto" \
      --hidden-import "uvicorn.protocols.websockets.auto" \
      --collect-all "webview" \
      desktop/main.py
    echo ""
    echo "Output: dist/FeiCai.app/"
    echo "Package: cd dist && zip -r FeiCai-mac.zip FeiCai.app/"
    ;;

  win|windows)
    echo "Windows .exe..."
    echo "  Version: v${VERSION}"
    echo ""
    pyinstaller \
      --onedir \
      --windowed \
      --name "FeiCai" \
      --add-data "VERSION;." \
      --add-data "web_dist;web_dist" \
      --add-data "modules;modules" \
      --hidden-import "desktop.server" \
      --hidden-import "desktop.logger" \
      --hidden-import "desktop.loader" \
      --hidden-import "desktop.update_checker" \
      --hidden-import "webview.platforms.win32" \
      --hidden-import "uvicorn.logging" \
      --hidden-import "uvicorn.loops.auto" \
      --hidden-import "uvicorn.protocols.http.auto" \
      --hidden-import "uvicorn.protocols.websockets.auto" \
      --collect-all "webview" \
      desktop/main.py
    echo ""
    echo "Output: dist/FeiCai/"
    echo "Package: cd dist && Compress-Archive -Path FeiCai\* -DestinationPath FeiCai-win.zip"
    ;;

  linux)
    echo "Linux executable..."
    echo "  Version: v${VERSION}"
    echo ""
    pyinstaller \
      --onedir \
      --name "FeiCai" \
      --add-data "VERSION:." \
      --add-data "web_dist:web_dist" \
      --add-data "modules:modules" \
      --hidden-import "desktop.server" \
      --hidden-import "desktop.logger" \
      --hidden-import "desktop.loader" \
      --hidden-import "desktop.update_checker" \
      --hidden-import "webview.platforms.gtk" \
      --hidden-import "uvicorn.logging" \
      --hidden-import "uvicorn.loops.auto" \
      --hidden-import "uvicorn.protocols.http.auto" \
      --hidden-import "uvicorn.protocols.websockets.auto" \
      --collect-all "webview" \
      desktop/main.py
    echo ""
    echo "Output: dist/FeiCai/"
    echo "Package: cd dist && zip -r FeiCai-linux.zip FeiCai/"
    ;;

  spec)
    echo "Using spec file..."
    pyinstaller feicai.spec
    echo "Output: dist/"
    ;;

  *)
    echo "Usage: $0 {mac|win|linux|spec}"
    echo "  Default: mac"
    exit 1
    ;;
esac

deactivate
echo ""
echo "Build complete! Output in dist/"
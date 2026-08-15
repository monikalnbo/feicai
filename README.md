# 🐱 肥财 FeiCai

**Hermes Agent Desktop Shell** — 一个轻量级的跨平台桌面应用，使用系统原生 WebView 承载 Hermes Agent WebUI。

## 特点

- 🪶 **轻量** — 基于 Python + PyWebView，使用系统原生 WebView（macOS: WKWebView, Windows: WebView2）
- 🎨 **美观界面** — 基于 Hermes Agent WebUI，优化主题
- 📝 **SOUL 编辑** — 内置 SOUL.md 编辑器，随时调整 Agent 人格
- 🔌 **完整功能** — 保留 Hermes Agent 所有原生功能页面
- 🍎 **跨平台** — 支持 macOS 和 Windows

## 项目结构

```
feicai/
├── hermes-agent/       # 内置 Hermes Agent 完整代码
├── desktop/            # Python 桌面壳
│   ├── main.py        # 入口文件
│   └── server.py      # FastAPI 后端服务
├── web/               # 前端 WebUI (位于 hermes-agent/web/)
├── requirements.txt   # Python 依赖
└── README.md
```

## 快速开始

### 1. 安装依赖

```bash
cd feicai
python3 -m venv venv
source venv/bin/activate  # Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

### 2. 构建前端

```bash
cd hermes-agent/web
npm install
npm run build
cd ../..
```

### 3. 启动 Hermes 后端

确保 Hermes Agent 正在运行：
```bash
hermes gateway start
# 或者
cd hermes-agent && python -m hermes_cli.main web
```

### 4. 启动桌面应用

```bash
cd feicai
source venv/bin/activate
python desktop/main.py
```

### 开发模式（热重载）

```bash
# 终端 1：启动 Vite 开发服务器
cd hermes-agent/web
npm run dev

# 终端 2：启动桌面应用（会自动连到 Vite 服务器）
cd feicai
source venv/bin/activate
python desktop/main.py
```

## 打包

### macOS (.app)

```bash
pip install py2app
python setup.py py2app
```

### Windows (.exe)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed desktop/main.py
```

## 许可证

本项目基于 Hermes Agent 构建，遵循其原始许可证。
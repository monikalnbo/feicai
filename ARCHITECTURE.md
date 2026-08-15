# 🐱 肥财 FeiCai — 架构文档

## 概述

肥财是一款轻量级跨平台桌面应用，使用系统原生 WebView 承载 **Hermes Agent** 的 WebUI，提供一个整洁的工作台界面来管理 AI Agent。

```
┌─────────────────────────────────────────────────────────┐
│                    肥财 FeiCai                          │
│  ┌───────────────────────────────────────────────────┐  │
│  │              PyWebView (原生 WebView)              │  │
│  │  ┌─────────────────────────────────────────────┐  │  │
│  │  │         WebUI (React + TypeScript)          │  │  │
│  │  │  ┌───────────┐ ┌──────────┐ ┌──────────┐   │  │  │
│  │  │  │ Chat      │ │ Sessions │ │ Config   │   │  │  │
│  │  │  ├───────────┤ ├──────────┤ ├──────────┤   │  │  │
│  │  │  │ Skills    │ │ Models   │ │ Soul     │   │  │  │
│  │  │  │ ...       │ │ ...      │ │ Editor   │   │  │  │
│  │  │  └───────────┘ └──────────┘ └──────────┘   │  │  │
│  │  └─────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────┘  │
│                          │ HTTP API                      │
│  ┌───────────────────────▼───────────────────────────┐  │
│  │         FastAPI 后端 (desktop/server.py)           │  │
│  │  ┌─────────────────┐  ┌────────────────────────┐  │  │
│  │  │ API 代理         │  │ 更新检测 / SOUL 管理   │  │  │
│  │  └────────┬────────┘  └────────────────────────┘  │  │
│  └───────────┬────────────────────────────────────────┘  │
│              │ proxy                                    │
│  ┌───────────▼────────────────────────────────────────┐  │
│  │      Hermes Agent 后端 (localhost:8642)             │  │
│  └────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **桌面壳** | Python 3 + PyWebView 6 | 系统原生 WebView（macOS: WKWebView, Windows: WebView2） |
| **后端** | FastAPI + Uvicorn | 轻量异步 HTTP 服务 |
| **前端** | React 19 + TypeScript + Vite | Hermes Agent 原生 WebUI |
| **UI 库** | @nous-research/ui | Hermes 内置 UI 组件库 |
| **更新源** | GitHub Releases API | 从 monikalnbo/feicai 检查更新 |

## 项目结构

```
feicai/
├── desktop/                      # 🖥️ Python 桌面壳
│   ├── main.py                  # 入口：启动后端 + WebView 窗口
│   └── server.py                # FastAPI 后端（代理 + 扩展 API）
│
├── hermes-agent/                 # 📦 内置 Hermes Agent（完整代码）
│   ├── agent/                   # Agent 核心逻辑
│   ├── hermes_cli/              # CLI 和 API 服务
│   ├── web/                     # 🎨 前端 WebUI（React 18 + Vite）
│   │   └── src/
│   │       ├── pages/           # 所有功能页面
│   │       │   ├── ChatPage     # 对话
│   │       │   ├── SessionsPage # 会话管理
│   │       │   ├── ConfigPage   # 配置
│   │       │   ├── EnvPage      # API Keys
│   │       │   ├── SkillsPage   # 技能
│   │       │   ├── ModelsPage   # 模型
│   │       │   ├── SoulEditorPage  # ✨ SOUL 编辑（新增）
│   │       │   └── ...          # 其他 20+ 页面
│   │       └── App.tsx          # 路由和布局
│   └── ...
│
├── ARCHITECTURE.md               # 📖 本文档
├── README.md                    # 快速开始
├── requirements.txt             # Python 依赖
└── .gitignore
```

## 核心功能

### 1. Hermes Agent 原生能力（全部保留）

肥财完整保留了 Hermes Agent 的所有功能页面，无需任何修改即可使用：

| 页面 | 路径 | 功能 |
|------|------|------|
| 💬 对话 | `/chat` | 与 AI Agent 实时对话 |
| 📋 会话 | `/sessions` | 管理对话历史 |
| 📁 文件 | `/files` | 文件管理 |
| 📊 分析 | `/analytics` | 使用量分析 |
| 🤖 模型 | `/models` | 模型切换与管理 |
| 📝 日志 | `/logs` | 系统日志 |
| ⏰ 定时 | `/cron` | 定时任务 |
| 🧩 技能 | `/skills` | 技能管理与安装 |
| 🔌 插件 | `/plugins` | 插件系统 |
| 🔗 MCP | `/mcp` | MCP 服务器管理 |
| 📡 频道 | `/channels` | 消息频道 |
| 🪝 Webhooks | `/webhooks` | Webhook 管理 |
| 🔐 配对 | `/pairing` | 设备配对 |
| 👤 配置 | `/profiles` | 多配置管理 |
| ⚙️ 设置 | `/config` | 系统配置 |
| 🔑 密钥 | `/env` | API Key 管理 |
| 🛠️ 系统 | `/system` | 系统管理 |
| 📖 文档 | `/docs` | 本地文档 |

### 2. ✨ SOUL 编辑器（新增）

在 WebUI 中新增 `/soul` 页面，提供对 Hermes Agent `SOUL.md` 文件的在线编辑功能：
- 读取/保存 Agent 人格定义
- 实时修改，即时生效
- 语法高亮的文本编辑区

### 3. 🚀 更新检测（新增）

启动时自动检查 GitHub 上的新版本：
- 通过 `monikalnbo/feicai` 仓库的 Releases API 检测
- 在控制台和 WebUI 中提示更新
- 方便用户获取最新功能

## 开发指南

### 快速启动

```bash
# 1. 创建虚拟环境
cd feicai
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 构建前端（首次或修改前端后）
cd hermes-agent/web
npm install
npm run build
cd ../..

# 4. 确保 Hermes 后端运行中
hermes gateway start

# 5. 启动肥财
python desktop/main.py
```

### 开发模式（热重载）

```bash
# 终端 1：Vite 开发服务器
cd hermes-agent/web
npm run dev

# 终端 2：肥财桌面应用（自动检测并连接 Vite）
source venv/bin/activate
python desktop/main.py
```

### 添加新页面

1. 在 `hermes-agent/web/src/pages/` 下创建页面组件
2. 在 `hermes-agent/web/src/App.tsx` 中：
   - 添加 `lazy import`
   - 在 `BUILTIN_ROUTES_CORE` 中添加路由
   - 在 `BUILTIN_NAV_REST` 中添加导航项
3. 重新构建前端：`cd hermes-agent/web && npm run build`

### 添加后端 API

在 `desktop/server.py` 中添加新的路由即可，所有 `/api/*` 请求默认代理到 Hermes 后端，自定义路由会优先匹配。

## 打包部署

### macOS (.app)

```bash
pip install py2app
python setup.py py2app
# 输出在 dist/ 目录
```

### Windows (.exe)

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "肥财" desktop/main.py
# 输出在 dist/ 目录
```

## 更新机制

肥财的更新检测工作流程：

```
启动 → 调用 GitHub Releases API → 获取最新版本号
       ↓
  比较本地版本 ← feicai/VERSION 文件
       ↓
  有新版本？ → 是 → 控制台提示 + WebUI 通知
       ↓ 否
  正常启动
```

版本号存储在项目根目录的 `VERSION` 文件中，更新发布通过 GitHub Releases 进行。

## 设计原则

- 🪶 **轻量** — 最小依赖，系统原生 WebView
- 🧩 **可扩展** — 新增页面和 API 只需少量代码
- 🔌 **非侵入** — 不改动 Hermes Agent 核心代码
- 🍎 **跨平台** — 一套代码，Mac + Windows

---

> 肥财 FeiCai — 让 Hermes Agent 拥有一个漂亮的家。
# 🔧 Skills Hub

> OpenClaw Skills 导航站 — 搜索、浏览、一键复制安装命令

**在线地址：** https://skills-hub.pages.dev

---

## 功能

- 🔍 **模糊搜索** — 实时过滤，支持 `⌘K` / `Ctrl+K` 快捷键
- 🗂 **分类筛选** — 18 个语义分类，侧边栏一键切换
- 📦 **多数据源** — ClawHub / skills.sh / GitHub / 本地已安装
- 📋 **一键复制** — 支持镜像加速安装命令（国内可用）
- 🎨 **彩色分类 Badge** — 每个 skill 卡片标注所属类别颜色
- 📱 **响应式** — 桌面三列 / 平板双列 / 手机单列

## 技术栈

- 纯 HTML + CSS + Vanilla JS，零依赖，零构建
- 数据由 `build.py` 离线生成，注入 `<script type="application/json">` 标签
- 部署：[Cloudflare Pages](https://pages.cloudflare.com)，push 自动部署

## 本地开发

```bash
# 重新生成数据（需要在 OpenClaw workspace 环境下运行）
cd /home/void/文档/project/skills-hub
python3 build.py

# 直接用浏览器打开即可，无需 dev server
open index.html
```

## 数据更新

`build.py` 会读取本机已安装的 clawhub + skills.sh skills，生成嵌入到 `index.html` 的静态 JSON。

分类规则在 `build.py` 的 `CATEGORY_RULES` 中维护，当前覆盖 18 个分类：

| 分类 | 示例 |
|---|---|
| 🤖 AI/ML | OpenAI, RAG, embedding, LLM |
| 🧩 Agent模式 | planning, memory, multi-agent |
| 🎨 前端 | React, Vue, Next.js, Tailwind |
| 🐍 Python | FastAPI, uv, asyncio |
| ⚙️ 后端/数据库 | PostgreSQL, Redis, Prisma |
| 🚀 DevOps | K8s, Terraform, GitHub Actions |
| 🔒 安全 | JWT, GDPR, auth |
| ⛓ 区块链/Web3 | Solidity, NFT, DeFi |
| 📝 内容创作 | SEO, 小红书, TikTok |
| 🛠 工具 | Obsidian, Spotify, tmux |
| 🐾 OpenClaw | gateway, cron, sessions |
| … | … |

## 项目结构

```
skills-hub/
├── index.html      # 主页面（含所有 CSS/JS + 嵌入数据）
├── build.py        # 数据构建脚本
└── README.md
```

## 维护

由 [小新 🔧](https://github.com/Quantum505Void) 维护，数据来源于 [clawhub.ai](https://clawhub.ai) 和 [skills.sh](https://skills.sh)。

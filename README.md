# NexTest Platform · 下一代测试平台

**技能驱动的测试智能体 Web 平台：用户 LLM 配置、对话（含 SSE），API 统一在 `/api`。**  
*A web platform for test-oriented agents: Vue 3 + FastAPI + MySQL.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Vue](https://img.shields.io/badge/Vue-3-4FC08D?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.13+-3776AB?logo=python&logoColor=white)](https://www.python.org/)

---

## 用例生成演示

[![用例生成演示](imgs/testcase_gen.gif)](imgs/testcase_gen.gif)

## 功能一览（当前实现）

| 模块 | 说明 |
|------|------|
| **认证** | 注册、登录、刷新令牌、`/api/auth/me`；请求头 `Authorization: Bearer <access_token>` |
| **测试助手** | 非流式 `/api/agent/chat`、SSE `/api/agent/chat/stream`；会话列表、重命名、历史消息； |
| **用户 LLM 配置** | 多配置 CRUD、保存前连通性测试、启用项；对话中可选 `llm_profile_id` 与 `temperature` |
| **技能（运行时）** | 启动时从 `skills` 目录加载注册（每个技能目录需同时包含 `config.json` + `skill.py`）；`/api/skills` 元数据列表与独立 `invoke` |
| **系统管理（admin）** | 用户列表与启用状态，`/api/admin/users` |
| **前端控制台** | 首页、智能体页、模型配置；侧栏按 `user_type === admin` 显示系统管理 |

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 界面 | Vue 3、TypeScript、Vue Router、Pinia、Ant Design Vue、Vite 7 |
| HTTP 客户端 | Axios（默认 `baseURL` `/api`；开发态 Vite 代理至后端） |
| API | Python ≥ 3.13、FastAPI、Uvicorn、Pydantic Settings、JWT（PyJWT）、Loguru |
| 数据 | MySQL（SQLAlchemy 2 异步 + `asyncmy`）、Alembic 迁移 |
| 技能 | 文件系统技能包 + 启动注册（`SKILLS_DIR` 可覆盖路径） |

---

## 快速开始（开发）

### 环境要求

- **Node.js** 18+（推荐 LTS），包管理使用 **pnpm**（与仓库 `pnpm-lock.yaml` 一致）  
- **Python** 3.13+；推荐 [uv](https://github.com/astral-sh/uv)（仓库含 `uv.lock`）  
- **MySQL** 8.x（连接串见 `.env`）  
- Windows 下可使用 **PowerShell** 或 **Git Bash** 执行下列命令  

### 1. 准备数据库

创建空库（名称与 `DATABASE_URL` 一致即可），例如库名 `nextest`。

### 2. 后端

```bash
cd backend
cp .env.example .env
# 编辑 .env：DATABASE_URL、JWT_SECRET 等
```

安装依赖并迁移、启动（任选其一：本示例用 `uv`）：

```bash
cd backend
uv sync
alembic upgrade head
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端

```bash
cd frontend
pnpm install
pnpm dev
```

默认：<http://localhost:5173>；`/api` 与 `/uploads` 代理到 `http://localhost:8000`。生产构建可设置 `VITE_API_BASE_URL` 指向实际 API 根路径。

### 配置要点

- 智能体上下文轮数、用户输入长度上限、技能目录等见 [`backend/.env.example`](backend/.env.example)，与 [`backend/app/core/config.py`](backend/app/core/config.py) 对应。  
- **新增配置项须同步更新 `.env.example`**（与仓库后端架构规则一致）。  

---

## 仓库结构（节选）

```text
nextest-platform/
  frontend/                 # Vue 3 + Vite
  backend/
    app/                    # FastAPI 应用（api / services / repositories / models）
    skills/                 # 技能包目录（启动注册）
    alembic/                # 数据库迁移
  docs/                     # SSE 协议、技能广场、路线图等
  README.md
```

---

## 参与贡献

Issue / PR 欢迎。后端改动请遵守 `api → services → repositories → models` 分层；列表分页请复用 `Paging`（`page` / `size`），详见 [`backend/README.md`](backend/README.md) 与 `.cursor/rules/backend-architecture.mdc`。

---

## 许可证

[MIT](LICENSE) · Copyright (c) 2026 SeaZhusp


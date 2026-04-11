# NexTest 后端说明（服务端注意事项）

本文档面向在本仓库 `backend/` 下开发与部署 FastAPI 服务的同学，汇总约定与易踩坑点。

## 1. 目录与分层

- 业务代码根目录：`app/`。
- 严格分层：**`api` → `services` → `repositories` → `models`**。
  - `api`：路由、入参校验、依赖注入（`Depends`），不写复杂业务与 SQL。
  - `services`：业务编排、事务边界、权限与状态机。
  - `repositories`：数据访问（查询/写入），避免在 endpoint 里直接拼 SQL。
  - `models`：ORM 定义；通用字段见 `app/models/base.py`（含软删除 `deleted_at`）。
- 横切能力放在 `app/core/`（配置、日志、中间件、异常、响应、Token、密码等）。
- 常量与错误码：`app/constants/`（`enums.py`、`error_codes.py`），避免魔法字符串。

## 2. 配置与环境变量

- 统一从 `app/core/config.py` 的 `Settings` 读取；新增配置项必须同步更新 **`backend/.env.example`**。
- 本地复制：将 `.env.example` 复制为 `backend/.env`（或项目约定的路径），勿把生产密钥提交进仓库。
- 数据库连接串：`DATABASE_URL`（默认按 MySQL 异步驱动示例配置），以环境为准覆盖默认值。

## 3. 数据库与会话

- 异步会话入口：`app/db/session.py` 中的 `get_db()`，业务通过 `Depends(get_db)` 注入。
- **不要在业务代码里随手 `create_engine` / 自建 Session**，避免连接泄漏与测试困难。
- 软删除：以 `deleted_at` 为准；查询默认应过滤已删除记录（仓储基类已按此思路封装时，业务仍要注意原生 SQL）。
- 迁移：表结构变更通过 **Alembic** 管理；操作步骤与命令见 **[docs/database-migrations.md](docs/database-migrations.md)**。

## 4. API 版本与路由

- 对外路由挂载在 **`/api/v1`、`/api/v2`**；破坏性变更走新版本，旧版本保留兼容窗口。
- 新增模块时在对应版本的 `router` 中聚合子路由，保持 `endpoints` 文件小而专。

## 5. 鉴权与安全

- 推荐请求头：**`Authorization: Bearer <access_token>`**。
- Token 签发与校验：`app/core/token.py`；密码哈希：`app/core/password.py`（勿把哈希逻辑塞进 `models`）。
- 鉴权依赖：`app/api/deps/auth.py`；与具体用户查询结合时通过 `get_db` + repository/service 完成。

## 6. 异常与响应

- 业务/权限类错误：抛 `app/core/exceptions.py` 中定义的异常类型，并尽量使用 **`app/constants/error_codes.py`** 中的业务码（与 HTTP 状态区分）。
- 全局处理：`app/core/exception_handlers.py` 注册；统一响应形态与 `app/core/responses.py` 保持一致，避免 endpoint 里各写一套 JSON。

## 7. 日志与生命周期

- 日志初始化在 **`lifespan`** 中执行（见 `app/main.py`），避免模块 import 副作用。
- 关闭阶段应释放资源（例如数据库 `dispose`），新增长连接（Redis、MQ）时同样在 lifespan 里配对创建/关闭。

## 8. 中间件

- 集中注册：`app/core/middleware.py` 的 `setup_middleware`（CORS、可信 Host、请求上下文等）。
- 新增中间件时注意顺序（尤其 CORS 与异常响应头），改动后应用真实浏览器与跨域场景验证。

## 9. 分页与列表接口

- 列表分页参数优先复用 **`app/api/deps/query.py` 的 `Paging`**；排序字段需白名单或校验，禁止把前端字符串直接拼进 ORDER BY。
- 错误码、枚举：**按需扩展**，预留号段比一次性写满更重要；与前端/客户端约定好同一套语义。

## 10. 开发与提交前自检

- 本地至少能：`import` 应用、启动服务、跑通关键路径（登录、受保护接口）。
- 提交前：无敏感信息进仓库；`.env` 已在 `.gitignore`；新增依赖写入依赖清单（如 `requirements.txt` / `pyproject.toml`，以项目实际为准）。

---

若有与本文冲突的旧代码路径或命名，以 **`backend/app` 当前目录与 `.cursor/rules/backend-architecture.mdc`** 为准，并逐步收敛。

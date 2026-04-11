# 数据库迁移（Alembic）

本文说明在本仓库 **`backend/`** 目录下如何使用 Alembic 管理 MySQL 表结构，与运行时 **异步** `DATABASE_URL`（如 `mysql+asyncmy://...`）配合使用。

## 要点速览

| 项目 | 说明 |
|------|------|
| 迁移执行方式 | **同步**（`mysql+pymysql`），由 `alembic/env.py` 从 `app.core.config.settings` 读取 `database_url` 并自动替换驱动 |
| 元数据来源 | `app.db.base.Base.metadata`，所有继承 `ModelBase` 的模型需被 **import** 后才会进入 autogenerate |
| 工作目录 | 命令均在 **`backend`** 根目录执行（与 `pyproject.toml`、`alembic.ini` 同级） |
| 环境变量 | 使用 **`backend/.env`** 中的 `DATABASE_URL`（或 `Settings` 对应字段），与 FastAPI 运行时一致 |

## 前置条件

1. 已安装依赖：`uv sync`（需包含 `alembic`、`pymysql`）。
2. MySQL 中已创建数据库，账号对目标库有 DDL 权限。
3. `backend/.env`（或环境变量）中 `DATABASE_URL` 正确。

## 常用命令

在 **`backend`** 目录下执行：

```bash
# 根据模型变更自动生成迁移脚本（生成后必须人工检查）
uv run alembic revision --autogenerate -m "描述本次变更"

# 将数据库升级到最新版本
uv run alembic upgrade head

# 回退一个版本（需 migration 里 downgrade 写得正确）
uv run alembic downgrade -1

# 查看当前数据库版本
uv run alembic current

# 查看迁移历史
uv run alembic history
```

## 首次接入流程

1. 确认 `alembic/env.py` 已配置 `target_metadata = Base.metadata`，并已 `import app.models`（或等价导入所有表模型）。
2. 执行：

   ```bash
   uv run alembic revision --autogenerate -m "init"
   ```

3. 打开 `alembic/versions/` 下新生成的脚本，**核对** `upgrade()` / `downgrade()`：索引、默认值、字符集、外键等 autogenerate 常有偏差。
4. 确认无误后：

   ```bash
   uv run alembic upgrade head
   ```

## 新增模型后的流程

1. 在 `app/models/` 增加模型类（继承 `ModelBase`）。
2. 在 **`app/models/__init__.py`** 中导出该模型（或确保 `alembic/env.py` 能 import 到它），否则 autogenerate **不会**发现新表。
3. `uv run alembic revision --autogenerate -m "add_xxx_table"`
4. 人工审查 revision 文件 → `uv run alembic upgrade head`

## 注意事项

- **不要**在 `alembic.ini` 里写真实数据库密码；连接串以 `.env` / 环境变量为准，由 `env.py` 注入。
- **生产环境**部署应在发布流程中执行 `alembic upgrade head`（或等价自动化），避免只在开发机改库。
- 若数据库已手工建表且与模型一致，可用 `alembic stamp head` 将版本标为最新（**慎用**，需确认结构真的一致）。
- `--autogenerate` 不能检测所有变更（如部分重命名、复杂约束），复杂变更应手写 `op` 或拆多步迁移。

## 相关文件

- `backend/alembic.ini` — 脚本目录等全局配置
- `backend/alembic/env.py` — 数据库 URL、metadata、online/offline 迁移入口
- `backend/alembic/versions/` — 各版本迁移脚本（应纳入 Git）
- `backend/app/db/session.py` — 运行时异步引擎；`get_sync_engine()` 与迁移使用相同 URL 转换规则

## 故障排查

| 现象 | 处理 |
|------|------|
| `No module named 'app'` | 在 `backend` 目录执行 `uv run alembic ...`；检查 `env.py` 中 `sys.path` 是否包含 backend 根目录 |
| autogenerate 无新表 | 确认新模型已在 `app.models` 中被 import |
| 连接失败 | 检查同步 URL 是否为 `mysql+pymysql://...`，防火墙与账号权限 |
| 与线上一致 | CI/CD 中固定执行 `uv sync` + `alembic upgrade head`，并使用同一套 `DATABASE_URL` 策略 |

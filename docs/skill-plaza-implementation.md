# 技能广场与技能管理 — 完整实现方案

本文描述「一步到位」落地的目标范围、数据模型、API、前后端模块及与现有**技能注册表**（`backend/skills/` + `SkillRegistry`）的关系。实现时不拆多期里程碑，但开发可按模块并行。

---

## 1. 目标与边界

### 1.1 业务目标

| 模块 | 受众 | 能力 |
|------|------|------|
| **技能管理**（系统管理下） | `admin` | 维护「广场可见的技能目录」：增删改、上下架、分类标签、详情文案、**可见性**（全员 / 登录 / 指定用户）、**是否在广场展示**。与运行时是否已注册技能对齐校验。 |
| **技能广场**（独立菜单，全员可进） | 所有登录用户 | **只读**：列表、搜索、分类 Tab、卡片展示；**技能详情**（抽屉或独立页）；**不**在此编辑数据。 |
| **执行能力** | 编排层 / 调试接口 | 仍通过已有 `SkillRegistry` + `POST /skills/{skill_id}/invoke`；广场仅引导，不替代执行链。 |

### 1.2 原则

- **手动维护目录**：广场展示字段以 **数据库为准**；`skill_id` 与磁盘技能包一致，用于关联「能跑的技能」。
- **部分开放**：未在目录中上架、或 `visible=false`、或不在用户可见范围内的技能，广场不展示；列表接口过滤。
- **执行真相仍在注册表**：若 DB 有一条但进程未加载该 `skill_id`，详情页可标「暂不可用」并在调用前由后端二次校验（与 `execute_skill` 行为一致）。

---

## 2. 与现有系统的关系

```
backend/skills/<skill_id>/          # 技能包：config.json + skill.py（现有）
        ↓ 启动时 SkillRegistry.reload()
内存 dict: skill_id → BaseSkill      # 唯一执行入口

        ↓ 新增：DB 表 skill_catalog（示例名）
skill_id（PK/FK 语义）+ 展示字段 + visibility + allowlist + published
        ↓
GET /skill-plaza/...                 # 只读，过滤后返回
GET /admin/skill-catalog/...         # CRUD，仅 admin
```

- **不**用 DB 替代 `skill.py` 执行逻辑。
- **可选**同步策略：管理端保存时校验 `skill_id` 是否在 `get_skill_registry().list_skill_ids()` 中；不在则仅允许「草稿/仅文案」状态或强提示（产品规则二选一，实现时写死一种）。

---

## 3. 数据模型（建议）

单表即可满足「一步到位」（后续再拆标签关联表）。

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | UUID / 自增 | 主键 |
| `skill_id` | `str`，唯一 | 与 `backend/skills/<skill_id>` 一致 |
| `name` | `str` | 展示名（可覆盖 config 内 name） |
| `subtitle` | `str`，可选 | 卡片副标题 |
| `description` | `text` | 短描述（列表） |
| `detail_markdown` | `text`，可选 | 详情页长文（可与 Claude SKILL.md 转换内容一致） |
| `category` | `str` | 分类 key，与前端 Tab 对齐（枚举或配置表） |
| `capability_tags` | JSON 数组 | 核心能力标签 |
| `icon_key` | `str`，可选 | 前端图标或 OSS key |
| `visibility` | enum | `public`（所有登录用户） / `authenticated` / `restricted` |
| `allowed_user_ids` | JSON，可选 | `restricted` 时生效用户 ID 列表 |
| `listed_in_plaza` | `bool` | 是否在广场列表出现（false 则仅管理端可见或仅 URL 直达，按产品定） |
| `sort_order` | `int` | 排序 |
| `view_count` | `int` | 可选统计 |
| `like_count` | `int` | 可选统计 |
| `created_at` / `updated_at` | datetime | 审计 |

索引：`(listed_in_plaza, visibility, category)`、`skill_id` 唯一。

---

## 4. 后端（FastAPI）

### 4.1 分层

- `app/models/skill_catalog.py`（或命名 `skill_listing`）：SQLAlchemy 模型，继承 `ModelBase`。
- `app/repositories/skill_catalog_repository.py`：CRUD、列表过滤、分页。
- `app/services/skill_catalog_service.py`：业务规则（可见性解析、与 registry 校验、详情阅读量 +1）。
- `app/api/endpoints/skill_plaza.py`：`prefix="/skill-plaza"`，登录用户可访问列表/详情。
- `app/api/endpoints/admin_skill_catalog.py`：`prefix="/admin/skill-catalog"`，`Depends` 管理员（与 `users` 管理一致）。
- `app/schemas/skill_catalog.py`：Pydantic 入参/出参。

### 4.2 API 草案

**广场（只读）**

- `GET /skill-plaza`：分页列表；`q`、`category`、`visibility` 由服务端根据当前用户解析过滤。
- `GET /skill-plaza/{skill_id}`：详情；若不可见返回 404。

**管理端**

- `GET /admin/skill-catalog`：全量或分页（含未上架）。
- `POST /admin/skill-catalog`
- `PUT /admin/skill-catalog/{id}` 或 `PATCH`
- `DELETE /admin/skill-catalog/{id}`（软删除或硬删，与现有软删规范一致）

**权限**

- 广场接口：`get_current_user`。
- 管理接口：`user_type == admin`（与路由 `meta.role: 'admin'` 对齐）。

### 4.3 迁移

- Alembic revision 新建表；在 `backend/.env.example` 无需新增项除非有 feature flag。

---

## 5. 前端（Vue 3 + Ant Design Vue）

### 5.1 路由与菜单

- **技能广场**：`/skill-plaza`（或 `/skills`），`meta.showInMenu: true`，与「测试智能体」同级，所有登录用户可见。
- **技能管理**：挂在 `system` 下，例如 `/system/skill-catalog`，`meta.role: 'admin'`，与「用户管理」并列。

需在 `frontend/src/router/index.ts` 与 `layouts` 菜单生成逻辑中增加上述项（与现有 `SettingOutlined` / 子菜单模式一致）。

### 5.2 页面

| 页面 | 内容 |
|------|------|
| `views/skill-plaza/index.vue` | 搜索框、状态下拉（若需要）、分类 Tabs、卡片网格；卡片数据来自 `GET /skill-plaza`；点击「查看详情」/「开始对话」跳转详情或带 `skill_id` 进智能体页。 |
| `views/skill-plaza/detail.vue`（或抽屉） | Markdown 详情、`skill_id`、说明是否可调用；按钮跳转 `/agent?skill=xxx`（若路由支持 query）。 |
| `views/system/skill-catalog/index.vue` | Table + 表单 Modal/Drawer：编辑所有 DB 字段；`skill_id` 下拉或远程搜索（建议从 `GET /skills` 元数据拉取已注册 id 供选择）。 |

### 5.3 API 封装

- `frontend/src/api/skillPlaza.ts`、`adminSkillCatalog.ts` 与 `request.ts` 基类一致。

---

## 6. 与智能体页联动（建议）

- 广场「开始对话」：`router.push({ path: '/agent', query: { skill: skill_id } })`。
- `views/agent/index.vue`：读取 `route.query.skill`，若存在则默认选中会话技能或预填 prompt 模板（与现有 agent 编排对齐；若尚无编排，可先仅 message 提示「将使用技能 xxx」）。

（若第一版不做 query 联动，文档仍保留接口约定，前端可只展示「请到智能体中手动选择」——实现时择一。）

---

## 7. 安全与一致性

- **禁止**在广场详情中返回密钥、内部 URL。
- **restricted**：列表与详情均在服务端按 `user.id` 过滤。
- **调用**：用户从前端发起技能调用时仍走已有鉴权；**不信任**前端传的可见性，仅信后端。

---

## 8. 测试与验收

- 单测：可见性过滤（public / restricted）、未登录 401、非 admin 访问管理 403。
- 集成：管理端创建一条 → 广场可见 → 详情 → 与 `invoke` 联调（`skill_id` 存在时）。

---

## 9. 文档与运维

- 本文件与 `docs/claude-skill-zip-integration.md` 配套：运营/开发者如何上架 Claude SKILL 包与维护目录字段。

---

## 10. 小结

- **DB**：技能广场/权限/详情**手动维护**。
- **磁盘**：`backend/skills/` 仍为**执行真相**。
- **前端**：广场只读 + 系统管理可编辑；**admin** 与全员菜单分离。

实现时按「模型 → 仓库 → 服务 → 路由 → 前端页面」顺序即可一次性合入主干。

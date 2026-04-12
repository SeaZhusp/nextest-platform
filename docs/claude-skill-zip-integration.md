# Claude 风格 SKILL 压缩包接入本系统 — 操作说明

本文说明：从 **Anthropic / Claude 生态常见的 SKILL 包（ZIP）** 到 **nextest-platform 当前技能体系**（`backend/skills/<skill_id>/config.json` + `skill.py` + 注册表）的对应关系，以及推荐落地步骤。

---

## 1. Claude SKILL 包通常长什么样

解压 ZIP 后，常见结构类似（名称以实际包为准）：

```
MySkill/
├── SKILL.md              # 前端 YAML front matter + Markdown 正文（指令、规范）
├── reference/            # 可选：参考文档、示例
├── scripts/              # 可选：脚本（多为 Python/Shell，面向 Claude Code 运行时）
└── ...
```

- **SKILL.md**：给模型看的**系统/指令文本**，不是本仓库里的「可执行 Python 技能」本身。
- **scripts/**：若在 Claude 桌面/Code 里运行，可能直接调；在 **本后端** 里是否执行，取决于你是否在 `skill.py` 里显式 `subprocess` 或导入调用（默认不推荐盲目执行 ZIP 内任意脚本，需安全审查）。

本系统当前约定：**可执行入口**是 `skill.py` 里的 `BaseSkill.run()`，由 `SkillRegistry` 加载。

---

## 2. 是否必须「转成 .py」？

**不必须「把 SKILL.md 手工改写成大量 Python 逻辑」**，但**必须**有一个 **`skill.py`** 提供：

- `build_skill() -> BaseSkill`
- `BaseSkill.run()` 的实现

推荐两种接入方式（二选一或组合）：

| 方式 | 做法 | 适用 |
|------|------|------|
| **A. 薄封装（推荐先做）** | 将 `SKILL.md`（及 `reference/`）**原样放入**技能目录，在 `run()` 里读文件，把 Markdown **拼进 LLM 的 system 提示**或用户消息，再走现有 `generate_xxx` / 调用链。 | 以**提示词驱动**为主的 QA/测试用例类技能（你贴的长文即此类）。 |
| **B. 逻辑在 Python** | 把规范拆成代码里的常量、校验、模板；SKILL.md 仅作文档备份。 | 强规则、少依赖模型、需单测覆盖时。 |

因此：**ZIP 不是「整体替换 skill.py」**，而是：**资源（SKILL.md）+ 一个适配器 `skill.py`**。

---

## 3. 目录映射（本仓库落点）

建议在本机/仓库中这样组织（`skill_id` 用小写短横线，与目录名一致）：

```
backend/skills/
└── <skill_id>/                    # 例如 test-case-qa（新建或沿用现有 test_case_gen）
    ├── config.json              # 已有格式：skill_id / name / version / description
    ├── skill.py                 # 必须：build_skill() + BaseSkill
    ├── SKILL.md                 # 从 ZIP 拷贝的原文（可选但推荐）
    └── reference/               # 从 ZIP 拷贝（可选）
```

- `config.json` 的 `skill_id` **必须**与目录名一致（与现有 `SkillRegistry` 校验一致）。
- 若 ZIP 里 **front matter**（`---`）与正文分离，可 **整文件保留**；解析时在 `skill.py` 里用简单库切分 front matter 与 body，或只把正文当 prompt。

---

## 4. 详细操作步骤（从 ZIP 到可调用）

### 步骤 1：解压 ZIP

在临时目录解压，确认根目录名称、是否存在 `SKILL.md`、`reference/`、`scripts/`。

### 步骤 2：确定 `skill_id`

- 新建技能：选一个**全局唯一** id，例如 `qa_test_case` 或 `test-case-qa`。
- 与现有技能不冲突：对照 `backend/skills/` 下已有目录。

### 步骤 3：创建技能目录

在仓库中创建：

`backend/skills/<skill_id>/`

### 步骤 4：拷贝静态资源

- 将 ZIP 中的 **`SKILL.md` 复制到** `backend/skills/<skill_id>/SKILL.md`。
- 若有 `reference/`，整体复制到同目录下 `reference/`。

### 步骤 5：编写 `config.json`

参考现有 `backend/skills/test_case_gen/config.json`，填写：

- `skill_id`：与目录名一致  
- `name` / `version` / `description`：可与 SKILL.md front matter 对齐  

### 步骤 6：编写 `skill.py`（薄封装示例逻辑）

实现要点（伪代码级，非复制即运行）：

1. `class MySkill(BaseSkill):` 实现 `skill_id`、`name`、`version`、`description`、`async def run(self, ctx: SkillContext)`.
2. 在 `run()` 中：
   - 用 `Path(__file__).parent / "SKILL.md"` 读取文件内容。
   - 若 `ctx.llm_config` 存在：将 **SKILL 全文或节选** 作为 **system** 或 **首条 user** 附加上下文，再调用项目内已有 LLM 封装（与 `test_case_gen` 类似）。
   - 若不存在 LLM 配置：返回明确错误提示或降级模板（与现有 `BusinessException` 规范一致）。
3. 模块末尾 **`def build_skill() -> BaseSkill: return MySkill()`**。

**安全**：对 `scripts/` 内脚本若需执行，必须白名单、审查参数、禁止任意 shell；默认**不执行** ZIP 内脚本。

### 步骤 7：重启后端或触发注册表 reload

当前注册表在应用启动时 `reload(skills_root)`。开发环境：**重启 FastAPI 进程**；若未来有热加载接口，再改为调用 reload。

### 步骤 8：验证注册成功

- 调用 `GET /api/skills`（或项目前缀下的 `GET /skills`），确认列表中出现新 `skill_id` 与元数据。

### 步骤 9：验证执行

- 使用 `POST /api/skills/{skill_id}/invoke`，body 带 `user_text`，且编排层传入 LLM 配置时（若你的 agent 会传 `llm_config`），确认行为符合 SKILL.md 约束。

### 步骤 10：上架「技能广场」（若已实现 DB 目录）

在 **技能管理** 后台新增一条记录：`skill_id` 与上一步一致，填写分类、标签、详情文案；设置可见性与 `listed_in_plaza`。  
仅 DB **不能**替代 `skill.py`；未部署技能包时勿将「可运行」写死。

---

## 5. 与「技能广场」文档的关系

- **执行**：始终依赖 `backend/skills/` + 注册表（本文档步骤 1–9）。
- **展示**：依赖数据库 **`skills` 表**（管理端上架 `is_published`）与只读广场 API；**SKILL.md 全文可同步到** `detail_markdown` 字段供广场详情展示，或在详情中仅展示摘要 +「以运行时为准」。

---

## 6. 常见问题

**Q：ZIP 里的 scripts 能直接当后端技能跑吗？**  
A：不自动等价。需在 `skill.py` 中显式、安全地调用；否则仅作文档/参考保留在 `reference/` 或 `scripts/` 目录。

**Q：能否不写 Python，只放 SKILL.md？**  
A：当前注册表**必须**加载 `skill.py` 并得到 `BaseSkill`；至少需要一个最小 `skill.py` 读文件并调 LLM 或返回占位。

**Q：多个 SKILL 包会冲突吗？**  
A：每个包一个 `skill_id` 目录即可；彼此独立。

---

## 7. 检查清单（提交前）

- [ ] `config.json.skill_id` == 目录名 == `BaseSkill.skill_id`  
- [ ] `SKILL.md` 编码 UTF-8，路径在 Linux 部署下大小写一致  
- [ ] `invoke` 与（可选）agent 编排联调通过  
- [ ] 未误提交敏感信息  
- [ ] （若已上广场）管理端目录与 `skill_id` 一致  

---

以上为从 Claude SKILL ZIP 到本系统技能包的**完整接入路径**；与「技能广场」人工维护相结合，即可同时满足 **可控开放** 与 **提示词驱动** 类技能。

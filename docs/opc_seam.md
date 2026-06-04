# OPC 接缝（与 bi-dashboard-demo 数字公司的集成点）

`project_smartbrain` 是独立产品，但留有一条干净的 API 接缝，让方法论可作为"策略/上下文"
注入 OPC 数字公司的 Agent——这样数字员工不只是干活，而是**按公司认可的方法论干活**。

## 接缝契约（本仓库已实现）

```
GET /api/methodologies/{id}/export?format=agent_md
→ { "id", "format": "agent_md", "content": "<可注入 agent 的 markdown>" }
```

`content` 由 `principles + steps + gates + anti_patterns` 拼装而成
（见 `server/app/api/methodologies.py::to_agent_markdown`）。

## Phase 3 如何接入（届时才实现，本设计已支持）

在 bi-dashboard-demo 的产品经理 agent 注入：

- 文件：`multi_agent_dev/agents/product_manager.py`
- 函数：`product_manager_node()`
- 插入点：`parts.append(skill_context)` 之后，追加 `export?format=agent_md` 的 `content`

```python
# product_manager.py，skill_context 之后
import httpx
md = httpx.get(f"{SMARTBRAIN_URL}/api/methodologies/{mid}/export",
               params={"format": "agent_md"}).json()["content"]
if md:
    parts.append(md)
```

数据模型已能"导出某方法论为 agent 可注入上下文"，无需改表。Phase 3 仅需在 OPC 侧加
"为某 phase/agent 绑定一个方法论 id"的配置 + 上面这段注入。

## 双模式共用 schema

同一个方法论对象：管理层用它"教"（沉淀 + 传承，本产品 Phase 1），Agent 用它"做"
（自动执行，Phase 3）。教与做共用一个 7 槽位 schema——这是接缝成立的根本原因。

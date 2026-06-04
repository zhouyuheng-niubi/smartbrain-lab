# 方法论 Schema（产品内核）

一个"方法论"是带 **7 个槽位**的结构化对象。内置方法论与员工自定义方法论都是它的实例——
正因为结构同构，它们才可检索、可组合、可对比、可被 Agent 调用。

| 槽位 | 类型 | 作用 | 数据形状 |
|---|---|---|---|
| `trigger` | dict | 适用场景 → 决定自动浮现（语义检索） | `{"scenarios":[...],"keywords":[...]}` |
| `principles` | list | 内核原则 / 意识形态 | `[{"title","detail"}]` |
| `steps` | list | 执行步骤（有序） | `[{"id","name","intent","guidance"}]` |
| `gates` | list | 决策闸门（每步必答的硬问题） | `[{"id","step_id","question","why","pass_criteria"}]` |
| `anti_patterns` | list | 反模式（专门警告别犯的错） | `[{"name","symptom","fix"}]` |
| `artifacts` | list | 产出物（作为合成输出骨架） | `[{"name","format","template"}]` |
| `metrics` | list | 效果度量（闭环的钥匙） | `[{"name","how_to_measure","target"}]` |

## 为什么槽位用 JSON 列而非子表

7 个槽位整体读写、几乎从不单独 query 某个 step/gate；方法论数量级是百，不是百万；
Phase 1 不需要关系查询。`trigger` 文本单独进 VectorStore 做语义浮现即可。
见 `server/app/models/database.py`。

## 治理元数据

`origin`（builtin/custom）、`status`（draft/published/archived）、`owner_user_id`、
`version`（每次编辑生成 `MethodologyVersion` 快照）、`run_count` / `avg_artifact_score`
（闭环回填的使用统计）。

## 一次"试跑"如何使用 schema（Run Engine）

`MethodologyRun` 按 `steps` 顺序推进，每个 step 内逐 `gate` 用 LLM 追问→作答→判定；
全部走完后用 `artifacts[].template` 作骨架合成产出物，再用 `metrics` 对应的打分器评分。
人用 AI 辅助（Phase 1）与 Agent 自动跑（Phase 2）共用同一 schema，区别只在
`GateResponse.answer_source`。

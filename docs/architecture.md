# 架构

```
React 前端 (Vite + Tailwind + Zustand)
    ↕ REST  (/api/methodologies, /api/runs)  vite 代理 → :54322
FastAPI 后端 (SQLModel ORM + SQLite)
    ├─ api/        methodologies.py · runs.py · health.py
    ├─ engine/     run_engine.py (状态机) · methodology_index.py (语义浮现) · prompts.py
    ├─ models/     database.py  (7 槽位 Methodology + Run/Gate/Outcome/LlmUsage)
    └─ seeds/      3 个内置方法论
    ↕
core/  (vendored from bi-dashboard-demo，见 VENDOR.md)
    llm_config (get_llm) · llm_tracking (create_and_invoke + 用量入库)
    embedding (向量库) · quality_metrics (score_decomposition)
    ↕ OpenAI-compatible API
LLM 供应商 (SiliconFlow / DeepSeek / CodingPlan，可切换)
```

## 分层原则

- **基础设施层** (`core/`)：vendored 复用 bi-dashboard 的成熟代码，仅在 VENDOR-PATCH 块改动。
- **领域层** (`server/app/`)：本产品独有的方法论 schema、Run Engine、API。
- 二者解耦：领域层通过 `core.llm_tracking.create_and_invoke` 调 LLM，通过
  `core.quality_metrics.score_artifact` 打分，通过 `core.embedding` 做语义检索。

## Phase 1 杀手级闭环（数据流）

```
suggest(raw_input) ──语义/关键词──▶ 推荐方法论
   └▶ create_run ──▶ in_progress
        └▶ 循环：ask_gate(LLM 追问) → submit_answer(LLM 判定) → 推进 step
             └▶ synthesize(LLM 合成 artifact) → score_decomposition 打分
                  └▶ 回填 methodology.run_count / avg_artifact_score
                       └▶ record_outcome(usefulness/adopted) ── 闭环
```

所有 LLM 调用经 `create_and_invoke(project_id=<run_id>)` 自动记录 token/费用到 `LlmUsage`。

## 测试策略

`tests/conftest.py` 用临时 SQLite + TestClient + 确定性 fake LLM 桩
（按 `[JUDGE]`/`[SYNTHESIZE]` 标记判别），使全部回归**零 token**。
真实 LLM 端到端验证走 `scripts/smoke_run.py`。

## 降级

- 无 `SILICONFLOW_API_KEY`：embedding 返回零向量 → 语义索引为空 → `/suggest` 自动降级关键词匹配。
- seeding / 索引构建失败：lifespan 内 try/except，不阻塞启动。

# Vendored infrastructure

These modules are **copied** (not imported) from `bi-dashboard-demo` to keep this
product an independent repo while reusing proven, self-contained infrastructure.
Importing across repos would drag bi-dashboard's whole `server.app.models.database`
ORM onto this repo's PYTHONPATH (the tracking module transitively depends on it),
which is fragile. Vendoring trades that fragility for a manual sync obligation.

| file | source | status |
|---|---|---|
| `llm_config.py` | `multi_agent_dev/config.py` | unmodified |
| `llm_tracking.py` | `multi_agent_dev/tracking.py` | **VENDOR-PATCH** |
| `embedding.py` | `multi_agent_dev/embedding.py` | unmodified (subset used) |
| `quality_metrics.py` | `multi_agent_dev/quality_metrics.py` | **VENDOR-PATCH** |

- **Source commit**: `bi-dashboard-demo@6dc89a0`
- **Vendored on**: 2026-06-04

## VENDOR-PATCH blocks (the only places that diverge from source)

### `llm_tracking.py`
1. Imports `from multi_agent_dev.config import …` → `from core.llm_config import …` (3 sites).
2. `check_budget()` / `get_budget_status()`: `LlmUsage.project_id` → `LlmUsage.run_id`
   (this product keys usage by run, not by a project FK).
3. Added module-level `_persist_usage(run_id, rec)` and call it from `UsageTracker.record()`.
   bi-dashboard buffered records in memory and flushed them elsewhere against a project
   FK; here we persist each row immediately to the local `LlmUsage` table keyed by `run_id`.
   The public arg name stays `project_id` — callers pass a `run_id` value into it.

### `quality_metrics.py`
1. Added `score_decomposition()` and registered it in `_SCORERS["decomposition"]`.

### `llm_config.py`
1. Added a `dashscope` provider (阿里云 DashScope / 通义千问, OpenAI 兼容模式) to
   `_PROVIDER_SPECS` (env: `REDACTED_CREDENTIAL_NAME` / `DASHSCOPE_BASE_URL` / `DASHSCOPE_MODEL`)
   and per-role defaults in `_ROLE_DEFAULT_MODEL_BY_PROVIDER["dashscope"]`.

### `embedding.py`
1. `_get_api_config()` now prefers `EMBEDDING_API_KEY` / `EMBEDDING_BASE_URL`
   (falls back to `SILICONFLOW_*`), so embeddings can use a different provider than
   chat — e.g. Aliyun `text-embedding-v4`.
2. `embed_text()` no longer caches all-zero vectors — a transient API failure at
   cold start used to poison the disk cache permanently (the index then built 0
   entries forever). Now only non-zero embeddings are cached.

Only `embed_text` / `embed_batch` / `SearchHit` / `VectorStore` /
`_split_chunks` are used. The `build_*_index` / `index_single_*` / `semantic_search`
helpers reference bi-dashboard's `KnowledgeDoc`/`Memory` tables via lazy import and are
**never called** here — this product builds its own index in
`server/app/engine/methodology_index.py`.

## Syncing upstream fixes

If bi-dashboard patches one of these modules, re-copy and re-apply the VENDOR-PATCH
blocks above. Keep this file's source commit hash current.

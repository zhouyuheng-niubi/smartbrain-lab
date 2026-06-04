"""Pytest fixtures: temp DB, seeded methodologies, TestClient, deterministic fake LLM.

Tests run with ZERO tokens — the fake LLM stub replaces core.llm_tracking.create_and_invoke.
"""
from __future__ import annotations

import os
import pathlib
import sys
import tempfile

# repo root on path + temp DB BEFORE importing any server module (engine binds at import)
_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))
_TMPDIR = tempfile.mkdtemp(prefix="smartbrain_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMPDIR}/test.db"
# Hermetic tests: blank all provider keys so embeddings/LLM never hit the network.
# (load_dotenv won't override an already-set var, so set them to "" before import.)
os.environ["SILICONFLOW_API_KEY"] = ""
os.environ["EMBEDDING_API_KEY"] = ""
os.environ["EMBEDDING_BASE_URL"] = ""
os.environ["REDACTED_CREDENTIAL_NAME"] = ""
# isolated cache dir so tests never hit the real .embedding_cache (poisoned/real vectors)
os.environ["EMBEDDING_CACHE_DIR"] = f"{_TMPDIR}/emb_cache"

import pytest  # noqa: E402

from server.app.models.database import create_db  # noqa: E402
from server.app.seeds import seed_builtin  # noqa: E402


# A complete decomposition artifact — exercises every section score_decomposition checks.
FAKE_ARTIFACT = """# 销售业绩看板

## 1. 业务目标与背景 (S1)
- 业务问题：销售团队看不到实时业绩，月底才知道差距。
- 成功指标：销售人均跟进转化率提升、业绩达成率可视化。

## 2. 用户与场景 / 用户故事 (S2)
- 作为销售经理，我希望实时看到团队业绩，以便及时调整策略。

## 3. 分层拆解 (S3)
- 目标：业绩可视化
  - Epic：业绩看板
    - Story：个人业绩视图
      - 功能点：展示本月成单金额

## 4. 功能点 SMART 明细表 (S4)
| 功能点 | 具体描述 | 可衡量 | 优先级 | 待定项 |
|---|---|---|---|---|
| 本月成单金额 | 按销售展示当月已成单总额 | 金额数值 | P0 | 无 |

## 5. 验收标准 (S5)
| 功能点 | 验收标准 (Given-When-Then) |
|---|---|
| 本月成单金额 | 给定登录销售经理，当打开看板，那么显示本月每位销售的成单金额 |

## 6. 范围边界与非目标 (S6)
- 本期做：业绩展示、个人/团队视图。
- 本期不做（非目标）：薪酬计算、提成发放。

## 7. 风险 / 依赖 / 未知 (S7)
| 风险 | 影响 | 应对 | 负责人 |
|---|---|---|---|
| CRM 数据口径不一致 | 业绩数字错误 | 先对齐口径 | 数据组 |
"""


def fake_create_and_invoke(messages, *, project_id, agent_role, **kwargs):
    """Deterministic stub. Discriminates by marker keywords in the prompt."""
    from langchain_core.messages import AIMessage

    text = ""
    for m in messages:
        c = getattr(m, "content", "")
        if isinstance(c, str):
            text += c

    if "[JUDGE]" in text:
        return AIMessage(content='{"resolved": true, "reason": "测试桩：判定通过", "followup": ""}')
    if "[SYNTHESIZE]" in text:
        return AIMessage(content=FAKE_ARTIFACT)
    if "[DISTILL_EXTRACT]" in text or "[DISTILL_SYNTH]" in text:
        return AIMessage(content=FAKE_METHODOLOGY_JSON)
    if "[DISTILL_Q]" in text:
        return AIMessage(content="（测试桩）你拿到这类问题时，第一件事会看什么？为什么？")
    if "[LENS_DIAGNOSE]" in text:
        return AIMessage(content=FAKE_DIAGNOSIS_JSON)
    if "[ADVISOR]" in text:
        return AIMessage(content="（测试桩·顾问）先问你一个关键问题：这件事要解决的真实目标是什么？")
    # default: a gate clarifying question
    return AIMessage(content="（测试桩）请补充更多细节以澄清这一点。")


FAKE_DIAGNOSIS_JSON = """{
  "overall": "整体方向对，但验收与边界偏弱",
  "score": {"total": 7.0},
  "gate_findings": [
    {"gate_id": "G1", "question": "业务目标是否清晰?", "verdict": "pass", "evidence": "材料提到提升达成率", "suggestion": "补一个基线数字"},
    {"gate_id": "G5", "question": "验收标准是否可判定?", "verdict": "concern", "evidence": "未见GWT", "suggestion": "补 Given-When-Then"}
  ],
  "anti_pattern_hits": [{"name": "需求镀金", "evidence": "加了与目标无关的功能"}],
  "strengths": ["目标明确"],
  "top_fixes": ["补验收标准", "划清边界", "去掉镀金功能"]
}"""


# A complete methodology JSON — exercises slot + thick-field parsing in distill.
FAKE_METHODOLOGY_JSON = """{
  "name": "测试蒸馏方法论",
  "summary": "由测试桩蒸馏出的方法论",
  "tags": ["测试"],
  "trigger": {"scenarios": ["测试场景"], "keywords": ["测试"]},
  "principles": [{"title": "信条一", "detail": "为什么"}],
  "steps": [{"id": "S1", "name": "第一步", "intent": "目的", "guidance": "怎么做"}],
  "gates": [{"id": "G1", "step_id": "S1", "question": "硬问题?", "why": "重要", "pass_criteria": "通过标准"}],
  "anti_patterns": [{"name": "反模式", "symptom": "症状", "fix": "纠正"}],
  "artifacts": [{"name": "产出物", "format": "markdown", "template": "# 骨架"}],
  "metrics": [{"name": "度量", "how_to_measure": "怎么量", "target": "目标"}],
  "applicability": {"when_to_use": ["该用"], "when_not_to_use": ["别用"]},
  "examples": [{"kind": "positive", "title": "正例", "content": "内容"}],
  "related": []
}"""


@pytest.fixture(scope="session", autouse=True)
def _seeded_db():
    create_db()
    seed_builtin()
    yield


@pytest.fixture
def fake_llm(monkeypatch):
    """Patch the run engine's LLM call to the deterministic stub."""
    monkeypatch.setattr("core.llm_tracking.create_and_invoke", fake_create_and_invoke)
    yield


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from server.app.main import app

    with TestClient(app) as c:
        yield c

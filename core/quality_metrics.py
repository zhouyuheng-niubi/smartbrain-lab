# ╔══════════════════════════════════════════════════════════════════════════╗
# ║ VENDORED FROM bi-dashboard-demo@6dc89a0 (multi_agent_dev/quality_metrics)  ║
# ║ on 2026-06-04. VENDOR-PATCH: added score_decomposition() for this product's ║
# ║ Phase 1 requirement-decomposition artifact. See core/VENDOR.md.            ║
# ╚══════════════════════════════════════════════════════════════════════════╝
"""Quality metrics — automated scoring for each workflow phase output.

After each agent produces its artifact, this module evaluates quality
across multiple dimensions and persists the scores as WorkflowEvents.

Scoring is deterministic (rule-based) for speed, with an optional LLM
enhancement for subjective dimensions.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def _count_sections(text: str) -> int:
    return len(re.findall(r'^#{1,3}\s+', text, re.MULTILINE))


def _count_code_blocks(text: str) -> int:
    return len(re.findall(r'^```', text, re.MULTILINE)) // 2


def _count_tables(text: str) -> int:
    return len(re.findall(r'^\|.*\|.*\|', text, re.MULTILINE))


def _count_mermaid(text: str) -> int:
    return len(re.findall(r'```mermaid', text, re.IGNORECASE))


def _has_json_api_contract(text: str) -> bool:
    return bool(re.search(r'"api_contract"\s*:', text))


def _word_count(text: str) -> int:
    return len(text.split())


def _clamp(score: float, lo: float = 0, hi: float = 10) -> float:
    return max(lo, min(hi, score))


def score_requirements(content: str) -> dict[str, Any]:
    """Score a PRD artifact."""
    sections = _count_sections(content)
    tables = _count_tables(content)
    words = _word_count(content)
    has_acceptance = bool(re.search(r'验收|acceptance|AC\b', content, re.IGNORECASE))
    has_user_story = bool(re.search(r'用户故事|user story|作为.*我希望', content, re.IGNORECASE))

    completeness = _clamp(min(sections / 6, 1.0) * 10)
    specificity = _clamp(min(words / 800, 1.0) * 7 + (3 if tables > 0 else 0))
    testability = _clamp((5 if has_acceptance else 0) + (5 if has_user_story else 0))
    structure = _clamp(min(sections / 4, 1.0) * 7 + (3 if tables >= 2 else 0))

    total = round((completeness + specificity + testability + structure) / 4, 1)
    return {
        "phase": "requirements",
        "total": total,
        "dimensions": {
            "completeness": round(completeness, 1),
            "specificity": round(specificity, 1),
            "testability": round(testability, 1),
            "structure": round(structure, 1),
        },
        "stats": {"sections": sections, "tables": tables, "words": words},
    }


def score_architecture(content: str) -> dict[str, Any]:
    """Score an architecture artifact."""
    sections = _count_sections(content)
    code_blocks = _count_code_blocks(content)
    mermaid = _count_mermaid(content)
    tables = _count_tables(content)
    has_contract = _has_json_api_contract(content)
    has_er = bool(re.search(r'erDiagram|ER.*图|实体关系', content, re.IGNORECASE))
    has_project_type = bool(re.search(r'^PROJECT_TYPE:', content, re.MULTILINE))

    modularity = _clamp(min(sections / 8, 1.0) * 7 + (3 if mermaid > 0 else 0))
    api_design = _clamp((5 if has_contract else 2) + (3 if tables >= 3 else 1) + (2 if mermaid > 0 else 0))
    data_model = _clamp((5 if has_er else 1) + (5 if tables >= 2 else 2))
    implementability = _clamp(min(code_blocks / 3, 1.0) * 7 + (3 if has_project_type else 0))

    total = round((modularity + api_design + data_model + implementability) / 4, 1)
    return {
        "phase": "architecture",
        "total": total,
        "dimensions": {
            "modularity": round(modularity, 1),
            "api_design": round(api_design, 1),
            "data_model": round(data_model, 1),
            "implementability": round(implementability, 1),
        },
        "stats": {"sections": sections, "code_blocks": code_blocks, "mermaid": mermaid, "has_contract": has_contract},
    }


def score_ui_design(content: str) -> dict[str, Any]:
    """Score a UI design artifact."""
    sections = _count_sections(content)
    code_blocks = _count_code_blocks(content)
    has_responsive = bool(re.search(r'响应式|responsive|breakpoint|断点|mobile', content, re.IGNORECASE))
    has_components = bool(re.search(r'组件|component|widget', content, re.IGNORECASE))
    has_interaction = bool(re.search(r'交互|interaction|flow|流程|动画|animation', content, re.IGNORECASE))
    has_color = bool(re.search(r'配色|color|palette|主题|theme', content, re.IGNORECASE))

    coverage = _clamp(min(sections / 5, 1.0) * 10)
    responsive = _clamp(10 if has_responsive else 3)
    component_spec = _clamp((5 if has_components else 1) + (5 if code_blocks >= 2 else 2))
    interaction = _clamp((5 if has_interaction else 1) + (5 if has_color else 2))

    total = round((coverage + responsive + component_spec + interaction) / 4, 1)
    return {
        "phase": "ui_design",
        "total": total,
        "dimensions": {
            "coverage": round(coverage, 1),
            "responsive": round(responsive, 1),
            "component_spec": round(component_spec, 1),
            "interaction": round(interaction, 1),
        },
        "stats": {"sections": sections, "code_blocks": code_blocks},
    }


def score_development(content: str, validation_error: str = "") -> dict[str, Any]:
    """Score a development artifact (code output)."""
    code_blocks = _count_code_blocks(content)
    words = _word_count(content)
    has_imports = bool(re.search(r'import\s+|from\s+\S+\s+import|require\(', content))
    file_count = len(re.findall(r'^###\s*File:', content, re.MULTILINE))

    build_pass = _clamp(10 if not validation_error else 2)
    code_volume = _clamp(min(code_blocks / 5, 1.0) * 7 + (3 if file_count >= 3 else 1))
    structure = _clamp((5 if file_count >= 3 else 2) + (5 if has_imports else 2))
    completeness = _clamp(min(words / 1000, 1.0) * 10)

    total = round((build_pass * 2 + code_volume + structure + completeness) / 5, 1)
    return {
        "phase": "development",
        "total": total,
        "dimensions": {
            "build_pass": round(build_pass, 1),
            "code_volume": round(code_volume, 1),
            "structure": round(structure, 1),
            "completeness": round(completeness, 1),
        },
        "stats": {"code_blocks": code_blocks, "file_count": file_count, "has_validation_error": bool(validation_error)},
    }


def score_testing(content: str) -> dict[str, Any]:
    """Score a testing/QA artifact."""
    sections = _count_sections(content)
    code_blocks = _count_code_blocks(content)
    has_ci = bool(re.search(r'CI/CD|GitHub Actions|pipeline|gitlab|jenkins', content, re.IGNORECASE))
    has_test_strategy = bool(re.search(r'测试策略|test strategy|单元测试|unit test|集成测试|integration', content, re.IGNORECASE))
    has_monitoring = bool(re.search(r'监控|monitoring|alerting|告警|Prometheus|Grafana', content, re.IGNORECASE))
    has_docker = bool(re.search(r'docker|容器|Dockerfile|docker-compose', content, re.IGNORECASE))

    test_coverage = _clamp((5 if has_test_strategy else 1) + (5 if code_blocks >= 2 else 2))
    ci_cd = _clamp((5 if has_ci else 1) + (5 if has_docker else 2))
    monitoring = _clamp(10 if has_monitoring else 3)
    completeness = _clamp(min(sections / 5, 1.0) * 10)

    total = round((test_coverage + ci_cd + monitoring + completeness) / 4, 1)
    return {
        "phase": "testing",
        "total": total,
        "dimensions": {
            "test_coverage": round(test_coverage, 1),
            "ci_cd": round(ci_cd, 1),
            "monitoring": round(monitoring, 1),
            "completeness": round(completeness, 1),
        },
        "stats": {"sections": sections, "code_blocks": code_blocks},
    }


# VENDOR-PATCH ── added for project_smartbrain Phase 1 ────────────────────────
def score_decomposition(content: str) -> dict[str, Any]:
    """Score a structured requirement-decomposition artifact (Phase 1 主角).

    五个维度对应需求拆解方法论的核心 gate：
      - goal_clarity  : 讲清业务目标 + 可改善指标
      - layering      : 分层拆解（目标→Epic→Story→功能点）
      - smartness     : 功能点 SMART（无"尽量/优化/更好"等模糊词）
      - acceptance    : 每功能点有可判定验收标准（Given-When-Then）
      - boundary_risk : 划定范围边界(非目标) + 风险/依赖识别
    """
    sections = _count_sections(content)
    tables = _count_tables(content)
    words = _word_count(content)

    has_goal = bool(re.search(r'业务目标|目标背景|business goal|为了|以便', content, re.IGNORECASE))
    has_metric = bool(re.search(r'指标|metric|KPI|转化率|提升|下降|留存|增长', content, re.IGNORECASE))
    has_user_story = bool(re.search(r'作为.{0,8}我希望|作为.{0,8}我想|user story|用户故事', content, re.IGNORECASE))
    has_layering = bool(re.search(r'Epic|Story|功能点|分层|层级', content, re.IGNORECASE))
    has_acceptance = bool(re.search(r'验收标准|acceptance|当.{0,30}那么|given.{0,40}then', content, re.IGNORECASE | re.DOTALL))
    has_boundary = bool(re.search(r'非目标|不做|边界|范围|out of scope', content, re.IGNORECASE))
    has_risk = bool(re.search(r'风险|risk|依赖|dependency|未知|假设', content, re.IGNORECASE))
    vague_terms = re.findall(r'尽量|优化|更好|更快|友好|完善|提升体验|易用|灵活', content)
    vague_count = len(vague_terms)

    goal_clarity = _clamp((5 if has_goal else 1) + (5 if has_metric else 1))
    layering = _clamp(min(sections / 6, 1.0) * 6 + (4 if has_layering else 0))
    smartness = _clamp((6 if vague_count == 0 else max(0, 6 - vague_count)) + (4 if tables > 0 else 1))
    acceptance = _clamp((6 if has_acceptance else 0) + (4 if has_user_story else 1))
    boundary_risk = _clamp((5 if has_boundary else 0) + (5 if has_risk else 0))

    total = round((goal_clarity + layering + smartness + acceptance + boundary_risk) / 5, 1)
    return {
        "phase": "decomposition",
        "total": total,
        "dimensions": {
            "goal_clarity": round(goal_clarity, 1),
            "layering": round(layering, 1),
            "smartness": round(smartness, 1),
            "acceptance": round(acceptance, 1),
            "boundary_risk": round(boundary_risk, 1),
        },
        "stats": {"sections": sections, "tables": tables, "words": words, "vague_terms": vague_count},
    }
# ─────────────────────────────────────────────────────────────────────────────


_SCORERS = {
    "requirements": score_requirements,
    "architecture": score_architecture,
    "ui_design": score_ui_design,
    "development": score_development,
    "testing": score_testing,
    "decomposition": score_decomposition,  # VENDOR-PATCH
}


def score_artifact(phase: str, content: str, **kwargs: Any) -> dict[str, Any] | None:
    """Score an artifact for the given phase.

    Returns the score dict or None if no scorer is available.
    """
    scorer = _SCORERS.get(phase)
    if not scorer:
        return None
    try:
        return scorer(content, **kwargs)
    except Exception as e:
        logger.warning("Quality scoring failed for phase %s: %s", phase, e)
        return None

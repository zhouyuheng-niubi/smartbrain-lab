"""Lens engine — use a methodology as a diagnostic lens on an existing material."""
from __future__ import annotations

import json
import re

from core import llm_tracking
from server.app.engine import prompts
from server.app.models.database import LensReview, Methodology

_LENS_ROLE = "lens"
_MAX_CHARS = 12000

_DIAG_DEFAULTS: dict = {
    "overall": "", "score": None, "gate_findings": [],
    "anti_pattern_hits": [], "strengths": [], "top_fixes": [],
}


def _invoke(prompt_text: str, sid: str = "lens") -> str:
    from langchain_core.messages import HumanMessage

    resp = llm_tracking.create_and_invoke(
        [HumanMessage(content=prompt_text)], project_id=sid, agent_role=_LENS_ROLE
    )
    return (getattr(resp, "content", "") or "").strip()


def _parse_diagnosis(raw: str) -> dict:
    data: dict = {}
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, dict):
                data = parsed
        except Exception:
            data = {}
    out: dict = {}
    for key, default in _DIAG_DEFAULTS.items():
        val = data.get(key, default)
        if default is None:
            out[key] = val if isinstance(val, dict) else None
        else:
            out[key] = val if isinstance(val, type(default)) else default
    return out


def _methodology_context(m: Methodology) -> str:
    lines = [f"《{m.name}》：{m.summary or ''}"]
    if m.principles:
        lines.append("信条：" + "；".join(p.get("title", "") for p in m.principles))
    if m.gates:
        lines.append("决策闸门：")
        for g in m.gates:
            lines.append(f"- [{g.get('id', '')}] {g.get('question', '')}"
                         f"（通过标准：{g.get('pass_criteria', '')}）")
    if m.anti_patterns:
        lines.append("反模式：" + "；".join(a.get("name", "") for a in m.anti_patterns))
    appl = m.applicability or {}
    if appl.get("when_not_to_use"):
        lines.append("不适用：" + "；".join(appl["when_not_to_use"]))
    return "\n".join(lines)


def diagnose(session, methodology_id: str, material: str, title: str = "") -> LensReview:
    m = session.get(Methodology, methodology_id)
    if not m:
        raise ValueError("methodology not found")
    raw = _invoke(
        prompts.LENS_DIAGNOSE_TMPL.format(
            methodology_name=m.name,
            methodology_context=_methodology_context(m),
            title=title or "（未命名）",
            material=material[:_MAX_CHARS],
            schema=prompts.LENS_DIAGNOSIS_JSON_SCHEMA,
        ),
        sid="lens",
    )
    diag = _parse_diagnosis(raw)
    review = LensReview(
        methodology_id=m.id, methodology_name=m.name, title=title,
        material=material, diagnosis=diag, score=diag.get("score"),
    )
    session.add(review)
    session.commit()
    session.refresh(review)
    return review

"""Distillation engine — turn tacit expertise into a 7-slot methodology asset.

Two intake modes, both producing a DRAFT methodology (origin="custom",
provenance.source_type="distilled", status="draft") for the human to review/publish:
  A) from real materials  — distill_from_materials()
  B) expert interview     — start_interview() / submit_answer() / synthesize_from_interview()
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from core import llm_tracking
from server.app.engine import prompts
from server.app.models.database import DistillSession, Methodology

_DISTILLER_ROLE = "distiller"
_MAX_QUESTIONS = 8
_MAX_MATERIAL_CHARS = 12000

# default shape for a parsed methodology (dict-typed vs list-typed slots)
_DEFAULTS: dict = {
    "name": "", "summary": "", "tags": [],
    "trigger": {}, "principles": [], "steps": [], "gates": [],
    "anti_patterns": [], "artifacts": [], "metrics": [],
    "applicability": {}, "examples": [], "related": [],
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _invoke(prompt_text: str, sid: str = "distill") -> str:
    from langchain_core.messages import HumanMessage

    resp = llm_tracking.create_and_invoke(
        [HumanMessage(content=prompt_text)], project_id=sid, agent_role=_DISTILLER_ROLE
    )
    return (getattr(resp, "content", "") or "").strip()


def _parse_methodology_json(raw: str) -> dict:
    """Extract the JSON object from an LLM reply, fill safe defaults per slot."""
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
    for key, default in _DEFAULTS.items():
        val = data.get(key, default)
        out[key] = val if isinstance(val, type(default)) else default
    return out


def _make_draft(session, draft: dict, *, topic: str, expert_name: str = "") -> Methodology:
    """Persist a parsed draft as a custom, distilled, draft methodology."""
    slug = "distilled-" + _now().strftime("%Y%m%d%H%M%S%f")
    provenance = {
        "source_type": "distilled",
        "origin": f"内部:{expert_name}" if expert_name else "内部蒸馏",
        "note": f"蒸馏自主题「{topic}」",
        "forked_from": None,
    }
    m = Methodology(
        slug=slug,
        name=draft.get("name") or topic or "未命名（蒸馏草稿）",
        summary=draft.get("summary", ""),
        trigger=draft.get("trigger", {}),
        principles=draft.get("principles", []),
        steps=draft.get("steps", []),
        gates=draft.get("gates", []),
        anti_patterns=draft.get("anti_patterns", []),
        artifacts=draft.get("artifacts", []),
        metrics=draft.get("metrics", []),
        applicability=draft.get("applicability", {}),
        examples=draft.get("examples", []),
        provenance=provenance,
        related=draft.get("related", []),
        tags=draft.get("tags", []),
        origin="custom",
        status="draft",
    )
    session.add(m)
    session.commit()
    session.refresh(m)
    return m


# ── Mode A: from materials ───────────────────────────────────────────────────
def distill_from_materials(session, materials: list[str], hint: str = "", topic: str = "") -> Methodology:
    sess = DistillSession(mode="materials", topic=topic, materials=materials, status="in_progress")
    session.add(sess)
    session.commit()
    session.refresh(sess)

    text = "\n\n---\n\n".join(m for m in materials if m.strip())[:_MAX_MATERIAL_CHARS]
    raw = _invoke(
        prompts.DISTILL_EXTRACT_TMPL.format(
            topic=topic or "（未指定）", hint=hint or "（无）",
            materials=text, schema=prompts.METHODOLOGY_JSON_SCHEMA,
        ),
        sess.id,
    )
    draft = _parse_methodology_json(raw)
    methodology = _make_draft(session, draft, topic=topic)

    sess.draft = draft
    sess.draft_methodology_id = methodology.id
    sess.status = "completed"
    sess.updated_at = _now()
    session.add(sess)
    session.commit()
    session.refresh(methodology)  # re-load: the sess commit above expired it
    return methodology


# ── Mode B: expert interview ─────────────────────────────────────────────────
def _answered(transcript: list[dict]) -> list[dict]:
    return [t for t in transcript if t.get("answer", "").strip()]


def _format_transcript(transcript: list[dict]) -> str:
    rows = [f"问：{t['question']}\n答：{t['answer']}" for t in _answered(transcript)]
    return "\n\n".join(rows) if rows else "（还没开始）"


def _gaps(transcript: list[dict]) -> str:
    return "目标与触发场景、关键步骤、判断依据(决策闸门)、反模式、什么时候不该用、效果如何衡量"


def _next_question(sess: DistillSession) -> str:
    return _invoke(
        prompts.DISTILL_Q_TMPL.format(
            topic=sess.topic,
            transcript=_format_transcript(sess.transcript),
            gaps=_gaps(sess.transcript),
        ),
        sess.id,
    )


def start_interview(session, topic: str, expert_name: str = "") -> tuple[DistillSession, str]:
    sess = DistillSession(mode="interview", topic=topic, expert_name=expert_name, status="in_progress", transcript=[])
    session.add(sess)
    session.commit()
    session.refresh(sess)
    q = _next_question(sess)
    sess.transcript = [{"question": q, "answer": ""}]
    sess.updated_at = _now()
    session.add(sess)
    session.commit()
    session.refresh(sess)
    return sess, q


def submit_answer(session, sess: DistillSession, answer: str) -> dict:
    """Record the answer to the pending question; ask the next one (or signal done)."""
    transcript = list(sess.transcript or [])
    if transcript and not transcript[-1].get("answer", "").strip():
        transcript[-1] = {**transcript[-1], "answer": answer}
    else:
        transcript.append({"question": "(补充)", "answer": answer})

    done = len(_answered(transcript)) >= _MAX_QUESTIONS
    next_q = ""
    if not done:
        sess.transcript = transcript  # so _next_question sees latest answers
        next_q = _next_question(sess)
        transcript.append({"question": next_q, "answer": ""})

    sess.transcript = transcript
    sess.updated_at = _now()
    session.add(sess)
    session.commit()
    return {"done": done, "question": next_q}


def synthesize_from_interview(session, sess: DistillSession) -> Methodology:
    raw = _invoke(
        prompts.DISTILL_SYNTH_TMPL.format(
            topic=sess.topic,
            transcript=_format_transcript(sess.transcript),
            schema=prompts.METHODOLOGY_JSON_SCHEMA,
        ),
        sess.id,
    )
    draft = _parse_methodology_json(raw)
    methodology = _make_draft(session, draft, topic=sess.topic, expert_name=sess.expert_name)

    sess.draft = draft
    sess.draft_methodology_id = methodology.id
    sess.status = "completed"
    sess.updated_at = _now()
    session.add(sess)
    session.commit()
    session.refresh(methodology)  # re-load: the sess commit above expired it
    return methodology

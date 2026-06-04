"""Run engine — the Phase 1 killer loop.

Drive a methodology over a real fuzzy input as a finite state machine:
  created → in_progress (walk steps; per step, ask each gate → answer → judge)
          → synthesize artifact → score → completed → (later) record outcome

All LLM calls go through `llm_tracking.create_and_invoke` (vendored) keyed by run_id,
so usage is auto-tracked and tests can monkeypatch it for zero-token runs.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Session, select

from core import llm_tracking, quality_metrics
from server.app.core.config import DECOMPOSER_ROLE
from server.app.engine import prompts
from server.app.models.database import (
    GateResponse,
    Methodology,
    MethodologyRun,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── data helpers ─────────────────────────────────────────────────────────────
def _get_methodology(session: Session, run: MethodologyRun) -> Methodology:
    m = session.get(Methodology, run.methodology_id)
    if not m:
        raise ValueError("methodology not found for run")
    return m


def _ordered_steps(m: Methodology) -> list[dict]:
    return list(m.steps or [])


def _gates_for_step(m: Methodology, step_id: str) -> list[dict]:
    return [g for g in (m.gates or []) if g.get("step_id") == step_id]


def _responses(session: Session, run_id: str) -> list[GateResponse]:
    return list(session.exec(select(GateResponse).where(GateResponse.run_id == run_id)).all())


def _resolved_gate_ids(session: Session, run_id: str) -> set[str]:
    return {r.gate_id for r in _responses(session, run_id) if r.resolved}


def _get_response(session: Session, run_id: str, gate_id: str) -> Optional[GateResponse]:
    return session.exec(
        select(GateResponse).where(
            GateResponse.run_id == run_id, GateResponse.gate_id == gate_id
        )
    ).first()


def _invoke(prompt_text: str, run_id: str) -> str:
    from langchain_core.messages import HumanMessage

    resp = llm_tracking.create_and_invoke(
        [HumanMessage(content=prompt_text)], project_id=run_id, agent_role=DECOMPOSER_ROLE
    )
    return (getattr(resp, "content", "") or "").strip()


def _prior_context(session: Session, run_id: str, m: Methodology) -> str:
    gate_by_id = {g.get("id"): g for g in (m.gates or [])}
    lines = []
    for r in _responses(session, run_id):
        if r.resolved and r.user_answer:
            q = gate_by_id.get(r.gate_id, {}).get("question", r.gate_id)
            lines.append(f"- {q} → {r.user_answer}")
    return "\n".join(lines) if lines else "（暂无）"


def _parse_judge(raw: str) -> dict:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            obj = json.loads(match.group(0))
            return {
                "resolved": bool(obj.get("resolved", False)),
                "reason": str(obj.get("reason", "")),
                "followup": str(obj.get("followup", "")),
            }
        except Exception:
            pass
    # lenient text fallback — avoid deadlocking the run on a malformed judge reply
    low = raw.lower()
    resolved = ("true" in low or "通过" in raw) and "false" not in low
    return {"resolved": resolved, "reason": "（判定无法解析，按文本推断）", "followup": ""}


# ── state machine ────────────────────────────────────────────────────────────
def start_run(session: Session, methodology_id: str, raw_input: str, title: str = "") -> MethodologyRun:
    m = session.get(Methodology, methodology_id)
    if not m:
        raise ValueError("methodology not found")
    run = MethodologyRun(
        methodology_id=m.id,
        methodology_version=m.version,
        title=title or (raw_input[:40] if raw_input else m.name),
        raw_input=raw_input,
        status="in_progress",
        current_step_index=0,
    )
    session.add(run)
    session.commit()
    session.refresh(run)
    return run


def current_gate(session: Session, run: MethodologyRun) -> Optional[dict]:
    """Return the next unresolved gate (enriched with its step info), or None if all gates done.

    Auto-advances current_step_index past steps that have no remaining unresolved gate.
    """
    m = _get_methodology(session, run)
    steps = _ordered_steps(m)
    resolved = _resolved_gate_ids(session, run.id)
    idx = run.current_step_index
    while idx < len(steps):
        step = steps[idx]
        nxt = next((g for g in _gates_for_step(m, step.get("id")) if g.get("id") not in resolved), None)
        if nxt:
            if idx != run.current_step_index:
                run.current_step_index = idx
                run.updated_at = _now()
                session.add(run)
                session.commit()
            return {**nxt, "step_name": step.get("name", ""), "step_intent": step.get("intent", "")}
        idx += 1
    if run.current_step_index != len(steps):
        run.current_step_index = len(steps)
        run.updated_at = _now()
        session.add(run)
        session.commit()
    return None


def ask_gate(session: Session, run: MethodologyRun) -> dict:
    """Generate (or return the pending) AI clarifying question for the current gate."""
    g = current_gate(session, run)
    if g is None:
        return {"done": True, "gate": None, "ai_question": ""}

    existing = _get_response(session, run.id, g["id"])
    if existing and existing.ai_question and not existing.resolved:
        return {"done": False, "gate": g, "ai_question": existing.ai_question,
                "gate_response_id": existing.id}

    m = _get_methodology(session, run)
    prompt_text = prompts.GATE_QUESTION_TMPL.format(
        methodology_name=m.name,
        step_name=g.get("step_name", ""),
        step_intent=g.get("step_intent", ""),
        gate_question=g.get("question", ""),
        gate_why=g.get("why", ""),
        gate_pass_criteria=g.get("pass_criteria", ""),
        raw_input=run.raw_input,
        prior_context=_prior_context(session, run.id, m),
    )
    question = _invoke(prompt_text, run.id) or g.get("question", "")

    gr = existing or GateResponse(run_id=run.id, gate_id=g["id"], step_id=g.get("step_id", ""))
    gr.ai_question = question
    gr.resolved = False
    gr.updated_at = _now()
    session.add(gr)
    session.commit()
    session.refresh(gr)
    return {"done": False, "gate": g, "ai_question": question, "gate_response_id": gr.id}


def submit_answer(session: Session, run: MethodologyRun, gate_id: str, answer: str) -> dict:
    """Record the answer, judge it, advance if the step is complete."""
    m = _get_methodology(session, run)
    gate = next((g for g in (m.gates or []) if g.get("id") == gate_id), None)
    if gate is None:
        raise ValueError("gate not found in methodology")

    gr = _get_response(session, run.id, gate_id) or GateResponse(
        run_id=run.id, gate_id=gate_id, step_id=gate.get("step_id", "")
    )
    gr.user_answer = answer
    gr.answer_source = "human"

    verdict = _parse_judge(_invoke(
        prompts.GATE_JUDGE_TMPL.format(
            gate_question=gate.get("question", ""),
            gate_pass_criteria=gate.get("pass_criteria", ""),
            user_answer=answer,
        ),
        run.id,
    ))

    gr.resolved = verdict["resolved"]
    if not verdict["resolved"] and verdict["followup"]:
        gr.ai_question = verdict["followup"]
    gr.updated_at = _now()
    session.add(gr)
    session.commit()
    session.refresh(run)

    nxt = current_gate(session, run)
    run_done = nxt is None
    return {
        "resolved": verdict["resolved"],
        "reason": verdict["reason"],
        "followup": verdict["followup"],
        "run_done": run_done,
        "next_gate": nxt,
    }


def _qa_transcript(session: Session, run_id: str, m: Methodology) -> str:
    gate_by_id = {g.get("id"): g for g in (m.gates or [])}
    lines = []
    for r in _responses(session, run_id):
        if r.user_answer:
            q = gate_by_id.get(r.gate_id, {}).get("question", r.gate_id)
            lines.append(f"问：{q}\n答：{r.user_answer}\n")
    return "\n".join(lines) if lines else "（无问答记录）"


def synthesize_artifact(session: Session, run: MethodologyRun) -> MethodologyRun:
    """Compose the final structured artifact, score it, and roll up methodology stats."""
    m = _get_methodology(session, run)
    template = (m.artifacts[0].get("template", "") if m.artifacts else "") or "# 产出物\n"

    artifact_md = _invoke(
        prompts.SYNTHESIZE_TMPL.format(
            methodology_name=m.name,
            raw_input=run.raw_input,
            qa_transcript=_qa_transcript(session, run.id, m),
            artifact_template=template,
        ),
        run.id,
    )

    # Phase 1 scorer is the decomposition scorer; only score the matching methodology.
    score = None
    if m.slug == "requirement-decomposition":
        score = quality_metrics.score_artifact("decomposition", artifact_md)

    run.artifact_md = artifact_md
    run.artifact_score = score
    run.status = "completed"
    run.completed_at = _now()
    run.updated_at = _now()
    session.add(run)

    # roll up usage stats on the methodology
    m.run_count = (m.run_count or 0) + 1
    if score and isinstance(score.get("total"), (int, float)):
        prev_avg = m.avg_artifact_score
        n = m.run_count
        m.avg_artifact_score = round(
            (score["total"] if prev_avg is None else (prev_avg * (n - 1) + score["total"]) / n), 2
        )
    m.updated_at = _now()
    session.add(m)
    session.commit()
    session.refresh(run)
    return run


def record_outcome(
    session: Session,
    run_id: str,
    usefulness: int = 0,
    adopted: bool = False,
    metric_values: dict | None = None,
    note: str = "",
):
    from server.app.models.database import RunOutcome

    existing = session.exec(select(RunOutcome).where(RunOutcome.run_id == run_id)).first()
    if existing:
        existing.usefulness = usefulness
        existing.adopted = adopted
        existing.metric_values = metric_values or {}
        existing.note = note
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    outcome = RunOutcome(
        run_id=run_id,
        usefulness=usefulness,
        adopted=adopted,
        metric_values=metric_values or {},
        note=note,
    )
    session.add(outcome)
    session.commit()
    session.refresh(outcome)
    return outcome

"""Run API — drive a methodology over a real input (Phase 1 killer loop)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from server.app.engine import run_engine
from server.app.models.database import (
    GateResponse,
    Methodology,
    MethodologyRun,
    get_session,
)
from server.app.schemas.schemas import GateAnswerIn, OutcomeIn, RunCreateIn

router = APIRouter(prefix="/api/runs", tags=["runs"])


def _require_run(session: Session, run_id: str) -> MethodologyRun:
    run = session.get(MethodologyRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="run not found")
    return run


def _run_detail(session: Session, run: MethodologyRun) -> dict:
    responses = list(session.exec(
        select(GateResponse).where(GateResponse.run_id == run.id)
    ).all())
    m = session.get(Methodology, run.methodology_id)
    methodology = None
    if m:
        methodology = {
            "id": m.id, "slug": m.slug, "name": m.name,
            "steps": m.steps, "gates": m.gates, "artifacts": m.artifacts,
        }
    return {"run": run, "gate_responses": responses, "methodology": methodology}


@router.post("")
def create_run(payload: RunCreateIn, session: Session = Depends(get_session)) -> dict:
    try:
        run = run_engine.start_run(session, payload.methodology_id, payload.raw_input, payload.title)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _run_detail(session, run)


@router.get("")
def list_runs(
    methodology_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
    session: Session = Depends(get_session),
) -> dict:
    stmt = select(MethodologyRun)
    if methodology_id:
        stmt = stmt.where(MethodologyRun.methodology_id == methodology_id)
    if status:
        stmt = stmt.where(MethodologyRun.status == status)
    rows = list(session.exec(stmt).all())
    rows.sort(key=lambda r: r.created_at, reverse=True)
    return {"runs": rows, "total": len(rows)}


@router.get("/{run_id}")
def get_run(run_id: str, session: Session = Depends(get_session)) -> dict:
    return _run_detail(session, _require_run(session, run_id))


@router.post("/{run_id}/ask")
def ask(run_id: str, session: Session = Depends(get_session)) -> dict:
    run = _require_run(session, run_id)
    return run_engine.ask_gate(session, run)


@router.post("/{run_id}/answer")
def answer(run_id: str, payload: GateAnswerIn, session: Session = Depends(get_session)) -> dict:
    run = _require_run(session, run_id)
    try:
        return run_engine.submit_answer(session, run, payload.gate_id, payload.answer)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{run_id}/synthesize")
def synthesize(run_id: str, session: Session = Depends(get_session)) -> dict:
    run = _require_run(session, run_id)
    final = run_engine.synthesize_artifact(session, run)
    return _run_detail(session, final)


@router.post("/{run_id}/outcome")
def outcome(run_id: str, payload: OutcomeIn, session: Session = Depends(get_session)) -> dict:
    _require_run(session, run_id)
    oc = run_engine.record_outcome(
        session, run_id,
        usefulness=payload.usefulness,
        adopted=payload.adopted,
        metric_values=payload.metric_values,
        note=payload.note,
    )
    return {"outcome": oc}

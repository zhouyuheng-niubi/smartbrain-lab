"""Distillation API — extract methodology assets from materials or expert interviews."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from server.app.engine import distill
from server.app.models.database import DistillSession, get_session
from server.app.schemas.schemas import (
    DistillMaterialsIn,
    InterviewAnswerIn,
    InterviewStartIn,
)

router = APIRouter(prefix="/api/distill", tags=["distill"])


def _require_session(session: Session, sid: str) -> DistillSession:
    s = session.get(DistillSession, sid)
    if not s:
        raise HTTPException(status_code=404, detail="distill session not found")
    return s


@router.post("/materials")
def from_materials(payload: DistillMaterialsIn, session: Session = Depends(get_session)) -> dict:
    if not any(m.strip() for m in payload.materials):
        raise HTTPException(status_code=400, detail="materials 不能为空")
    m = distill.distill_from_materials(session, payload.materials, payload.hint, payload.topic)
    return {"methodology": m}


@router.post("/interview/start")
def interview_start(payload: InterviewStartIn, session: Session = Depends(get_session)) -> dict:
    if not payload.topic.strip():
        raise HTTPException(status_code=400, detail="topic 不能为空")
    sess, question = distill.start_interview(session, payload.topic, payload.expert_name)
    return {"session": sess, "question": question}


@router.get("/interview/{sid}")
def interview_get(sid: str, session: Session = Depends(get_session)) -> dict:
    return {"session": _require_session(session, sid)}


@router.post("/interview/{sid}/answer")
def interview_answer(sid: str, payload: InterviewAnswerIn, session: Session = Depends(get_session)) -> dict:
    sess = _require_session(session, sid)
    return distill.submit_answer(session, sess, payload.answer)


@router.post("/interview/{sid}/synthesize")
def interview_synthesize(sid: str, session: Session = Depends(get_session)) -> dict:
    sess = _require_session(session, sid)
    m = distill.synthesize_from_interview(session, sess)
    return {"methodology": m}

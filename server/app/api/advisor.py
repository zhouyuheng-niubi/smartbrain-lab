"""Advisor API — chat with a methodology as your coach."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from server.app.engine import advisor
from server.app.models.database import AdvisorSession, get_session
from server.app.schemas.schemas import AdvisorMessageIn, AdvisorStartIn

router = APIRouter(prefix="/api/advisor", tags=["advisor"])


def _require(session: Session, sid: str) -> AdvisorSession:
    s = session.get(AdvisorSession, sid)
    if not s:
        raise HTTPException(status_code=404, detail="advisor session not found")
    return s


@router.post("/start")
def advisor_start(payload: AdvisorStartIn, session: Session = Depends(get_session)) -> dict:
    try:
        sess, _ = advisor.start(session, payload.methodology_id, payload.topic)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return {"session": sess}


@router.post("/{sid}/message")
def advisor_message(sid: str, payload: AdvisorMessageIn, session: Session = Depends(get_session)) -> dict:
    sess = _require(session, sid)
    if not payload.content.strip():
        raise HTTPException(status_code=400, detail="content 不能为空")
    advisor.reply(session, sess, payload.content)
    return {"session": sess}


@router.get("/{sid}")
def advisor_get(sid: str, session: Session = Depends(get_session)) -> dict:
    return {"session": _require(session, sid)}


@router.get("")
def advisor_list(session: Session = Depends(get_session)) -> dict:
    rows = list(session.exec(select(AdvisorSession)).all())
    rows.sort(key=lambda s: s.updated_at, reverse=True)
    return {"sessions": rows, "total": len(rows)}

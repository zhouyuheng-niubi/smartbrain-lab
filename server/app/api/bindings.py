"""Agent bindings — bind a methodology to an OPC agent role; export injectable context."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from server.app.api.methodologies import to_agent_markdown
from server.app.models.database import AgentBinding, Methodology, get_session
from server.app.schemas.schemas import BindingIn

router = APIRouter(prefix="/api/bindings", tags=["bindings"])


def _get(session: Session, role: str) -> AgentBinding | None:
    return session.exec(select(AgentBinding).where(AgentBinding.agent_role == role)).first()


@router.get("")
def list_bindings(session: Session = Depends(get_session)) -> dict:
    return {"bindings": list(session.exec(select(AgentBinding)).all())}


@router.put("/{agent_role}")
def set_binding(agent_role: str, payload: BindingIn, session: Session = Depends(get_session)) -> dict:
    if not session.get(Methodology, payload.methodology_id):
        raise HTTPException(status_code=404, detail="methodology not found")
    b = _get(session, agent_role)
    if b:
        b.methodology_id = payload.methodology_id
        b.updated_at = datetime.now(timezone.utc)
    else:
        b = AgentBinding(agent_role=agent_role, methodology_id=payload.methodology_id)
    session.add(b)
    session.commit()
    session.refresh(b)
    return {"agent_role": b.agent_role, "methodology_id": b.methodology_id}


@router.get("/{agent_role}")
def get_binding(agent_role: str, session: Session = Depends(get_session)) -> dict:
    b = _get(session, agent_role)
    return {"agent_role": agent_role, "methodology_id": b.methodology_id if b else None}


@router.delete("/{agent_role}")
def delete_binding(agent_role: str, session: Session = Depends(get_session)) -> dict:
    b = _get(session, agent_role)
    if b:
        session.delete(b)
        session.commit()
    return {"ok": True, "agent_role": agent_role}


@router.get("/{agent_role}/export")
def export_binding(
    agent_role: str,
    format: str = Query(default="agent_md"),
    session: Session = Depends(get_session),
) -> dict:
    """OPC consumes this: the agent_md of the methodology bound to this role (or empty)."""
    b = _get(session, agent_role)
    if not b or not b.methodology_id:
        return {"agent_role": agent_role, "content": ""}
    m = session.get(Methodology, b.methodology_id)
    if not m:
        return {"agent_role": agent_role, "content": ""}
    return {"agent_role": agent_role, "methodology_id": m.id, "content": to_agent_markdown(m)}

"""Advisor engine — multi-turn coaching that wears a methodology's worldview."""
from __future__ import annotations

from datetime import datetime, timezone

from core import llm_tracking
from server.app.engine import prompts
from server.app.engine.lens import _methodology_context  # reuse the context builder
from server.app.models.database import AdvisorSession, Methodology

_ADVISOR_ROLE = "advisor"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _system(m: Methodology, topic: str) -> str:
    return prompts.ADVISOR_SYSTEM_TMPL.format(
        methodology_name=m.name,
        methodology_context=_methodology_context(m),
        topic=topic or "（未指定）",
    )


def _to_messages(system: str, history: list[dict]):
    from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

    msgs = [SystemMessage(content=system)]
    for h in history:
        if h.get("role") == "user":
            msgs.append(HumanMessage(content=h.get("content", "")))
        else:
            msgs.append(AIMessage(content=h.get("content", "")))
    return msgs


def _invoke(messages, sid: str) -> str:
    resp = llm_tracking.create_and_invoke(messages, project_id=sid, agent_role=_ADVISOR_ROLE)
    return (getattr(resp, "content", "") or "").strip()


def start(session, methodology_id: str, topic: str = "") -> tuple[AdvisorSession, str]:
    m = session.get(Methodology, methodology_id)
    if not m:
        raise ValueError("methodology not found")
    sess = AdvisorSession(methodology_id=m.id, methodology_name=m.name, topic=topic, messages=[], status="active")
    session.add(sess)
    session.commit()
    session.refresh(sess)

    opening = _invoke(_to_messages(_system(m, topic), []), sess.id)
    sess.messages = [{"role": "assistant", "content": opening}]
    sess.updated_at = _now()
    session.add(sess)
    session.commit()
    session.refresh(sess)
    return sess, opening


def reply(session, sess: AdvisorSession, user_content: str) -> str:
    m = session.get(Methodology, sess.methodology_id)
    system = _system(m, sess.topic) if m else "[ADVISOR]"
    history = list(sess.messages or []) + [{"role": "user", "content": user_content}]
    assistant = _invoke(_to_messages(system, history), sess.id)
    history.append({"role": "assistant", "content": assistant})
    sess.messages = history
    sess.updated_at = _now()
    session.add(sess)
    session.commit()
    session.refresh(sess)
    return assistant
